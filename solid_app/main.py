from abc import ABC, abstractmethod
from typing import Dict
from decimal import Decimal
from sqlmodel import create_engine
from uuid import UUID, uuid4
from fastapi import FastAPI
from datetime import datetime
import uuid

app = FastAPI()


# --- Models ---
# class UserBase(BaseModel):
#     account_id: UUID = Field(default_factory=uuid4)
#     document_id: str
#     username: str
#     email: str


# class AccountBase(BaseModel):
#     account_id: UUID = Field(default_factory=uuid4)
#     document_id: str
#     balance: Decimal = Decimal("0")
#     account_type: str
#     status: str = "ACTIVE"


# class DepositRequest(BaseModel):
#     amount: Decimal = Field(gt=0)


# --- Factory Method Pattern ---
class UserFactory(ABC):
    @abstractmethod
    def create_user(self, user_data: UserBase) -> dict:
        pass


class ClientFactory(UserFactory):
    def create_user(self, user_data: UserBase) -> dict:
        return {
            **user_data.model_dump(),
            "user_type": "CLIENT",
            "created_at": datetime.now(),
        }


class ManagerFactory(UserFactory):
    def create_user(self, user_data: UserBase) -> dict:
        return {
            **user_data.model_dump(),
            "user_type": "MANAGER",
            "created_at": datetime.now(),
            "is_staff": True,
        }


# --- Command Pattern ---
class Command(ABC):
    @abstractmethod
    def execute(self) -> dict:
        pass


class DepositCommand(Command):
    def __init__(self, account: UUID, amount: Decimal):
        self.account = account
        self.amount = amount

    def execute(self) -> dict:
        return {
            "transaction_id": uuid4(),
            "type": "DEPOSIT",
            "account": str(self.account),
            "amount": self.amount,
            "status": "COMPLETED",
            "timestamp": datetime.now(),
        }


class TransferCommand(Command):
    def __init__(self, from_account: str, to_account: str, amount: Decimal):
        self.from_account = from_account
        self.to_account = to_account
        self.amount = amount

    def execute(self) -> dict:
        return {
            "transaction_id": str(uuid.uuid4()),
            "type": "TRANSFER",
            "from": self.from_account,
            "to": self.to_account,
            "amount": self.amount,
            "status": "COMPLETED",
        }


class WithdrawalCommand(Command):
    def __init__(self, account: str, amount: Decimal):
        self.account = account
        self.amount = amount

    def execute(self) -> dict:
        return {
            "transaction_id": str(uuid.uuid4()),
            "type": "WITHDRAWAL",
            "account": self.account,
            "amount": self.amount,
            "status": "COMPLETED",
        }


# --- Proxy Pattern ---
class AccountInterface(ABC):
    @abstractmethod
    def get_balance(self, account_id: str) -> Decimal:
        pass

    @abstractmethod
    def update_balance(self, account_id: str, amount: Decimal) -> None:
        pass


class RealAccount(AccountInterface):
    def __init__(self):
        self.accounts: Dict[str, AccountBase] = {}

    def get_balance(self, account_id: str) -> Decimal:
        return self.accounts.get(
            account_id,
            AccountBase(account_id=account_id, document_id="", account_type="CHECKING"),
        ).balance

    def update_balance(self, account_id: str, amount: Decimal) -> None:
        if account_id in self.accounts:
            self.accounts[account_id].balance += amount


class AccountProxy(AccountInterface):
    def __init__(self, real_account: RealAccount):
        self.real_account = real_account
        self.access_log = []

    def get_balance(self, account_id: str) -> Decimal:
        self.access_log.append(f"Balance checked for {account_id}")
        return self.real_account.get_balance(account_id)

    def update_balance(self, account_id: str, amount: Decimal) -> None:
        self.access_log.append(f"Balance updated for {account_id}: {amount}")
        self.real_account.update_balance(account_id, amount)


# --- Routes ---
DATABASE_URL = "sqlite:///./database.db"
engine = create_engine(DATABASE_URL)

@app.get("/")
async def root():
    return {"Welcome! This is the SOLID App"}


@app.post("/accounts/{account_id}/deposit")
async def deposit(account_id: UUID, deposit_data: DepositRequest):
    command = DepositCommand(account_id, deposit_data.amount)
    transaction = command.execute()

    real_account = RealAccount()
    proxy = AccountProxy(real_account)
    proxy.update_balance(str(account_id), deposit_data.amount)

    return {
        "message": "Deposit successful",
        "transaction": transaction,
        "new_balance": proxy.get_balance(str(account_id)),
    }


@app.post("/users/")
async def create_user(user_data: UserBase, user_type: str):
    factory = ClientFactory() if user_type == "CLIENT" else ManagerFactory()
    return factory.create_user(user_data)


@app.post("/accounts/{account_id}/transfer")
async def transfer(account_id: str, to_account: str, amount: Decimal):
    command = TransferCommand(account_id, to_account, amount)
    return command.execute()


@app.post("/accounts/{account_id}/withdraw")
async def withdraw(account_id: str, amount: Decimal):
    command = WithdrawalCommand(account_id, amount)
    return command.execute()


@app.get("/accounts/{account_id}/balance")
async def get_balance(account_id: str):
    real_account = RealAccount()
    proxy = AccountProxy(real_account)
    return {"balance": proxy.get_balance(account_id)}
