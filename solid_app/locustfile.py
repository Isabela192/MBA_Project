import random
import string
from decimal import Decimal
from locust import HttpUser, task, between


def generate_document_id():
    """Generate a random document ID (11 digits)"""
    return "".join(random.choices(string.digits, k=11))


def generate_username():
    """Generate a random username"""
    return (
        f"user_{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
    )


def generate_email(username):
    """Generate a random email using the username"""
    return f"{username}@example.com"


def generate_name():
    """Generate a random name"""
    first_names = [
        "John",
        "Jane",
        "Mary",
        "James",
        "Robert",
        "Patricia",
        "Michael",
        "Linda",
    ]
    last_names = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
    ]
    return f"{random.choice(first_names)} {random.choice(last_names)}"


class BankUser(HttpUser):
    wait_time = between(1, 5)  # Wait between 1 and 5 seconds between tasks

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = None
        self.account_id = None
        self.document_id = None
        self.second_account_id = None

    def on_start(self):
        """Initialize user with an account"""
        # Create user
        self.document_id = generate_document_id()
        username = generate_username()

        user_data = {
            "document_id": self.document_id,
            "name": generate_name(),
            "email": generate_email(username),
            "username": username,
        }

        response = self.client.post("/users/", json=user_data)
        if response.status_code == 201:
            self.user_id = response.json().get("user_id")

        # Create account
        account_data = {
            "document_id": self.document_id,
            "account_type": random.choice(["checking", "savings"]),
        }

        response = self.client.post("/accounts/", json=account_data)
        if response.status_code == 201:
            self.account_id = response.json().get("account_id")

        # Create second account for transfers
        second_account_data = {
            "document_id": self.document_id,
            "account_type": random.choice(["checking", "savings"]),
        }

        response = self.client.post("/accounts/", json=second_account_data)
        if response.status_code == 201:
            self.second_account_id = response.json().get("account_id")

    @task(1)
    def get_welcome(self):
        """Test the welcome endpoint"""
        self.client.get("/")

    @task(2)
    def get_users(self):
        """Test getting all users"""
        self.client.get("/users/")

    @task(5)
    def deposit_money(self):
        """Test depositing money"""
        if not self.account_id:
            return

        amount = round(random.uniform(10, 1000), 2)
        payload = {"amount": amount}
        self.client.post(f"/accounts/{self.account_id}/deposit", json=payload)

    @task(4)
    def check_balance(self):
        """Test checking account balance"""
        if not self.account_id:
            return

        self.client.get(f"/accounts/{self.account_id}/balance")

    @task(3)
    def withdraw_money(self):
        """Test withdrawing money"""
        if not self.account_id:
            return

        # First check balance to avoid withdrawal failures
        response = self.client.get(f"/accounts/{self.account_id}/balance")
        if response.status_code == 200:
            balance = Decimal(response.json().get("balance", 0))
            if balance > 0:
                # Withdraw a random amount between 1 and half the balance
                max_amount = balance / 2 if balance > 2 else balance
                amount = round(random.uniform(1, float(max_amount)), 2)
                payload = {"amount": amount}
                self.client.post(f"/accounts/{self.account_id}/withdraw", json=payload)

    @task(2)
    def transfer_money(self):
        """Test transferring money between accounts"""
        if not self.account_id or not self.second_account_id:
            return

        # First check balance to avoid transfer failures
        response = self.client.get(f"/accounts/{self.account_id}/balance")
        if response.status_code == 200:
            balance = Decimal(response.json().get("balance", 0))
            if balance > 10:  # Only transfer if balance is reasonable
                # Transfer a random amount between 1 and half the balance
                max_amount = balance / 2 if balance > 2 else balance
                amount = round(random.uniform(1, float(max_amount)), 2)
                payload = {"to_account_id": self.second_account_id, "amount": amount}
                self.client.post(f"/accounts/{self.account_id}/transfer", json=payload)

    @task(1)
    def view_transactions(self):
        """Test viewing transaction history"""
        if not self.account_id:
            return

        self.client.get(f"/accounts/{self.account_id}/transactions")

    @task(1)
    def create_new_user(self):
        """Test creating a new user"""
        document_id = generate_document_id()
        username = generate_username()

        user_data = {
            "document_id": document_id,
            "name": generate_name(),
            "email": generate_email(username),
            "username": username,
        }

        self.client.post("/users/", json=user_data)
