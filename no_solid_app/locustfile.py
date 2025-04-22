import random
from locust import HttpUser, task, between
import factory
from factory import fuzzy
from factory.faker import Faker
from uuid import uuid4
from database.models import (
    User,
    Account,
    Transaction,
    UserType,
    AccountType,
    AccountStatus,
    TransactionType,
    TransactionStatus,
)
from locust import LoadTestShape


# Factory-boy factories for generating test data
class UserFactory(factory.Factory):
    class Meta:
        model = User

    id = factory.Sequence(lambda n: n + 1)
    document_id = factory.Sequence(
        lambda n: f"{random.randint(10000000000, 99999999999)}"
    )
    username = Faker("user_name")
    email = Faker("email")
    user_type = fuzzy.FuzzyChoice([UserType.CLIENT, UserType.MANAGER])
    updated_at = None
    is_staff = factory.LazyAttribute(
        lambda o: True if o.user_type == UserType.MANAGER else False
    )


class AccountFactory(factory.Factory):
    class Meta:
        model = Account

    id = factory.Sequence(lambda n: n + 1)
    account_id = factory.LazyFunction(uuid4)
    balance = fuzzy.FuzzyDecimal(100, 10000, precision=2)
    account_type = fuzzy.FuzzyChoice([AccountType.SAVINGS, AccountType.CHECKING])
    status = AccountStatus.ACTIVE
    updated_at = None
    user_id = factory.LazyAttribute(lambda o: o.owner.id if o.owner else None)

    # Association with a User
    owner = factory.SubFactory(UserFactory)


class TransactionFactory(factory.Factory):
    class Meta:
        model = Transaction

    id = factory.Sequence(lambda n: n + 1)
    transaction_id = factory.LazyFunction(uuid4)
    type = fuzzy.FuzzyChoice(
        [TransactionType.DEPOSIT, TransactionType.WITHDRAW, TransactionType.TRANSFER]
    )
    amount = fuzzy.FuzzyDecimal(10, 1000, precision=2)
    status = TransactionStatus.COMPLETED

    # We'll set these conditionally based on transaction type
    from_account_id = None
    to_account_id = None

    # Associations with Accounts
    @factory.post_generation
    def setup_accounts(self, create, extracted, **kwargs):
        if self.type == TransactionType.DEPOSIT:
            # For deposits, only to_account is used
            account = AccountFactory()
            self.to_account_id = account.id
            self.to_account = account
        elif self.type == TransactionType.WITHDRAW:
            # For withdrawals, only from_account is used
            account = AccountFactory()
            self.from_account_id = account.id
            self.from_account = account
        elif self.type == TransactionType.TRANSFER:
            # For transfers, both accounts are used
            from_account = AccountFactory()
            to_account = AccountFactory()
            self.from_account_id = from_account.id
            self.from_account = from_account
            self.to_account_id = to_account.id
            self.to_account = to_account


class BankUser(HttpUser):
    wait_time = between(1, 5)  # Wait between 1 and 5 seconds between tasks

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.account_id = None
        self.other_account_id = None

    def on_start(self):
        """Create a user and get their account ID when the test starts"""
        # Create a new user
        user_data = {
            "document_id": f"{random.randint(10000000000, 99999999999)}",
            "name": f"Test User {random.randint(1000, 9999)}",
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "username": f"testuser{random.randint(1000, 9999)}",
        }

        response = self.client.post("/users/", json=user_data)
        if response.status_code == 201:
            user_response = response.json()
            self.account_id = user_response.get("account_id")

        # Get another account for transfer operations
        response = self.client.get("/users/")
        if response.status_code == 200:
            users = response.json()
            # Find a different account than our own
            for user in users:
                for account in user.get("accounts", []):
                    if account.get("account_id") != self.account_id:
                        self.other_account_id = account.get("account_id")
                        break
                if self.other_account_id:
                    break

    @task(3)
    def get_users(self):
        """Get all users - weight: 3"""
        self.client.get("/users/")

    @task(2)
    def create_user(self):
        """Create a new user - weight: 2"""
        user_data = {
            "document_id": f"{random.randint(10000000000, 99999999999)}",
            "name": f"Test User {random.randint(1000, 9999)}",
            "email": f"user{random.randint(1000, 9999)}@example.com",
            "username": f"testuser{random.randint(1000, 9999)}",
        }
        self.client.post("/users/", json=user_data)

    @task(5)
    def deposit(self):
        """Deposit money into account - weight: 5"""
        if not self.account_id:
            return

        deposit_amount = round(random.uniform(10, 1000), 2)
        self.client.post(
            f"/accounts/{self.account_id}/deposit", json={"amount": deposit_amount}
        )

    @task(4)
    def withdraw(self):
        """Withdraw money from account - weight: 4"""
        if not self.account_id:
            return

        withdraw_amount = round(random.uniform(5, 200), 2)
        self.client.post(
            f"/accounts/{self.account_id}/withdraw", json={"amount": withdraw_amount}
        )

    @task(3)
    def transfer(self):
        """Transfer money to another account - weight: 3"""
        if not self.account_id or not self.other_account_id:
            return

        transfer_amount = round(random.uniform(10, 150), 2)
        self.client.post(
            f"/accounts/{self.account_id}/transfer",
            json={"to_account_id": self.other_account_id, "amount": transfer_amount},
        )

    @task(6)
    def check_balance(self):
        """Check account balance - weight: 6"""
        if not self.account_id:
            return

        self.client.get(f"/accounts/{self.account_id}/balance")

    @task(2)
    def get_transactions(self):
        """Get account transactions - weight: 2"""
        if not self.account_id:
            return

        self.client.get(f"/accounts/{self.account_id}/transactions")


class StagesShape(LoadTestShape):
    """
    Custom load shape with stages
    """

    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 10},  # Warm up
        {"duration": 120, "users": 50, "spawn_rate": 10},  # Step up
        {"duration": 180, "users": 100, "spawn_rate": 10},  # Normal load
        {"duration": 240, "users": 200, "spawn_rate": 20},  # Higher load
        {"duration": 300, "users": 300, "spawn_rate": 20},  # Heavy load
        {"duration": 360, "users": 500, "spawn_rate": 30},  # Peak load
        {"duration": 600, "users": 500, "spawn_rate": 30},  # Sustained peak
        {"duration": 660, "users": 250, "spawn_rate": 30},  # Scale down
        {"duration": 720, "users": 100, "spawn_rate": 20},  # Further scale down
        {"duration": 780, "users": 0, "spawn_rate": 20},  # Complete cooldown
    ]

    def tick(self):
        run_time = self.get_run_time()

        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]

        return None
