import random
from decimal import Decimal
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


# Locust User class
class BankAPIUser(HttpUser):
    wait_time = between(1, 5)  # Wait between 1 and 5 seconds between tasks

    def on_start(self):
        """Setup before tests start running"""
        # Create test user for authentication
        self.test_user = UserFactory(
            username="test_user",
            email="test_user@example.com",
            user_type=UserType.CLIENT,
        )

        # Create test account
        self.test_account = AccountFactory(
            owner=self.test_user, balance=Decimal("1000.00")
        )

        # Authenticate (this is a placeholder - implement actual auth if needed)
        # self.client.post("/login", json={"username": self.test_user.username, "password": "test_password"})

    @task(3)
    def get_user_info(self):
        """Test getting user information"""
        self.client.get(f"/users/{self.test_user.id}")

    @task(4)
    def get_account_info(self):
        """Test getting account information"""
        self.client.get(f"/accounts/{self.test_account.id}")

    @task(2)
    def create_deposit(self):
        """Test creating a deposit transaction"""
        transaction = TransactionFactory(
            type=TransactionType.DEPOSIT,
            amount=Decimal(str(random.randint(50, 500))),
            to_account_id=self.test_account.id,
        )

        self.client.post(
            "/transactions",
            json={
                "type": transaction.type.value,
                "amount": str(transaction.amount),
                "to_account_id": transaction.to_account_id,
            },
        )

    @task(2)
    def create_withdrawal(self):
        """Test creating a withdrawal transaction"""
        transaction = TransactionFactory(
            type=TransactionType.WITHDRAW,
            amount=Decimal(str(random.randint(10, 100))),
            from_account_id=self.test_account.id,
        )

        self.client.post(
            "/transactions",
            json={
                "type": transaction.type.value,
                "amount": str(transaction.amount),
                "from_account_id": transaction.from_account_id,
            },
        )

    @task(1)
    def create_transfer(self):
        """Test creating a transfer transaction"""
        # Create a destination account
        destination_account = AccountFactory()

        transaction = TransactionFactory(
            type=TransactionType.TRANSFER,
            amount=Decimal(str(random.randint(10, 200))),
            from_account_id=self.test_account.id,
            to_account_id=destination_account.id,
        )

        self.client.post(
            "/transactions",
            json={
                "type": transaction.type.value,
                "amount": str(transaction.amount),
                "from_account_id": transaction.from_account_id,
                "to_account_id": transaction.to_account_id,
            },
        )

    @task(3)
    def list_transactions(self):
        """Test listing transactions for an account"""
        self.client.get(f"/accounts/{self.test_account.id}/transactions")
