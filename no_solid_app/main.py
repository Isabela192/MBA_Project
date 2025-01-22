from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field
from fastapi import FastAPI, HTTPException
from uuid import UUID, uuid4
from datetime import datetime
from abc import ABC, abstractmethod

app = FastAPI()


# --- Models ---
class UserBase(BaseModel):
    account_id: UUID = Field(default_factory=uuid4)
    document_id: str
    username: str
    email: str
    user_type: str


class AccountBase(BaseModel):
    account_id: UUID = Field(default_factory=uuid4)
    document_id: str
    balance: Decimal = Decimal("0")
    account_type: str
    status: str = "ACTIVE"


class TransactionRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    destination_account_id: Optional[UUID] = None


# --- Singleton Pattern ---
class AuthenticationManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AuthenticationManager, cls).__new__(cls)
            # Initialize user store
            cls._instance.users = {}
            cls._instance.active_sessions = {}
        return cls._instance

    def register_user(self, user_data: UserBase) -> dict:
        if user_data.username in self.users:
            raise HTTPException(status_code=400, detail="Username already exists")

        user_dict = user_data.model_dump()
        self.users[user_data.username] = user_dict
        return user_dict

    def authenticate_user(self, username: str, password: str) -> Optional[dict]:
        user = self.users.get(username)
        if user:
            self.active_sessions[username] = str(uuid4())
            return user
        return None

    def is_authenticated(self, username: str, session_id: str) -> bool:
        return self.active_sessions.get(username) == session_id


# --- Facade Pattern ---
class TransactionFacade:
    def __init__(self):
        self.accounts_db = {}
        self.transactions_db = []

    def process_deposit(self, account_id: UUID, amount: Decimal) -> dict:
        if str(account_id) not in self.accounts_db:
            self.accounts_db[str(account_id)] = AccountBase(
                account_id=account_id, document_id="", account_type="CHECKING"
            )

        account = self.accounts_db[str(account_id)]
        account.balance += amount

        transaction = {
            "transaction_id": uuid4(),
            "type": "DEPOSIT",
            "account_id": account_id,
            "amount": amount,
            "timestamp": datetime.now(),
        }
        self.transactions_db.append(transaction)
        return transaction

    def process_transfer(
        self, source_account: UUID, dest_account: UUID, amount: Decimal
    ) -> dict:
        if str(source_account) not in self.accounts_db:
            raise HTTPException(status_code=404, detail="Source account not found")

        source = self.accounts_db[str(source_account)]
        if source.balance < amount:
            raise HTTPException(status_code=400, detail="Insufficient funds")

        source.balance -= amount
        if str(dest_account) in self.accounts_db:
            self.accounts_db[str(dest_account)].balance += amount

        transaction = {
            "transaction_id": uuid4(),
            "type": "TRANSFER",
            "source_account": source_account,
            "destination_account": dest_account,
            "amount": amount,
            "timestamp": datetime.now(),
        }
        self.transactions_db.append(transaction)
        return transaction


# --- Abstract Factory Pattern ---
class Account(ABC):
    @abstractmethod
    def get_type(self) -> str:
        pass

    @abstractmethod
    def get_features(self) -> dict:
        pass


class AccountFactory(ABC):
    @abstractmethod
    def create_account(self, document_id: str) -> Account:
        pass


class CheckingAccount(Account):
    def get_type(self) -> str:
        return "CHECKING"

    def get_features(self) -> dict:
        return {
            "overdraft_allowed": True,
            "minimum_balance": Decimal("0"),
            "maintenance_fee": Decimal("10"),
        }


class SavingsAccount(Account):
    def get_type(self) -> str:
        return "SAVINGS"

    def get_features(self) -> dict:
        return {
            "interest_rate": Decimal("0.025"),
            "minimum_balance": Decimal("100"),
            "withdrawal_limit": 6,
        }


class CheckingAccountFactory(AccountFactory):
    def create_account(self, document_id: str) -> Account:
        return CheckingAccount()


class SavingsAccountFactory(AccountFactory):
    def create_account(self, document_id: str) -> Account:
        return SavingsAccount()


# --- Routes ---
auth_manager = AuthenticationManager()
transaction_facade = TransactionFacade()


@app.post("/users/")
async def create_user(user_data: UserBase):
    return auth_manager.register_user(user_data)


@app.post("/login/")
async def login(username: str, password: str):
    user = auth_manager.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"message": "Login successful", "user": user}


@app.post("/accounts/")
async def create_account(document_id: str, account_type: str):
    factory = (
        CheckingAccountFactory()
        if account_type == "CHECKING"
        else SavingsAccountFactory()
    )
    account = factory.create_account(document_id)
    return {
        "account_id": uuid4(),
        "type": account.get_type(),
        "features": account.get_features(),
        "document_id": document_id,
    }


@app.post("/accounts/{account_id}/deposit")
async def deposit(account_id: UUID, request: TransactionRequest):
    return transaction_facade.process_deposit(account_id, request.amount)


@app.post("/accounts/{account_id}/transfer")
async def transfer(account_id: UUID, request: TransactionRequest):
    if not request.destination_account_id:
        raise HTTPException(status_code=400, detail="Destination account is required")
    return transaction_facade.process_transfer(
        account_id, request.destination_account_id, request.amount
    )
