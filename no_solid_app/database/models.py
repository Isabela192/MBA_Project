from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4
from sqlmodel import Field, SQLModel, Relationship
from pydantic import BaseModel


# Database Models


class UserAccountLink(SQLModel, table=True):
    __tablename__ = "user_account_links"

    user_id: Optional[int] = Field(
        default=None, foreign_key="users.id", primary_key=True
    )
    account_id: Optional[int] = Field(
        default=None, foreign_key="accounts.id", primary_key=True
    )


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: str = Field(default_factory=lambda: str(uuid4()), index=True)
    document_id: str = Field(index=True)
    username: str = Field(index=True, unique=True)
    password_hash: str
    email: str = Field(index=True)
    user_type: str
    created_at: datetime = Field(default_factory=datetime.now)

    accounts: List["Account"] = Relationship(
        back_populates="users", link_model=UserAccountLink
    )


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: str = Field(
        default_factory=lambda: str(uuid4()), index=True, unique=True
    )
    document_id: str = Field(index=True)
    balance: float = Field(default=0.0)
    account_type: str
    status: str = Field(default="ACTIVE")
    created_at: datetime = Field(default_factory=datetime.now)

    users: List[User] = Relationship(
        back_populates="accounts", link_model=UserAccountLink
    )
    transactions: List["Transaction"] = Relationship(back_populates="account")


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: str = Field(
        default_factory=lambda: str(uuid4()), index=True, unique=True
    )
    account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")
    destination_account_id: Optional[str] = None
    transaction_type: str
    amount: float
    timestamp: datetime = Field(default_factory=datetime.now)

    account: Optional[Account] = Relationship(back_populates="transactions")


class SessionModel(SQLModel, table=True):
    __tablename__ = "sessions"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    session_id: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)


# API Request/Response Models


class UserCreate(BaseModel):
    document_id: str
    username: str
    password: str
    email: str
    user_type: str = "CLIENT"


class UserResponse(BaseModel):
    document_id: str
    username: str
    email: str
    user_type: str
    account_id: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    message: str
    user: Dict[str, Any]
    session_id: str


class AccountCreate(BaseModel):
    document_id: str
    account_type: str = "CHECKING"


class AccountResponse(BaseModel):
    account_id: str
    document_id: str
    balance: float
    account_type: str
    status: str
    features: Optional[Dict[str, Any]] = None
    created_at: datetime


class TransactionRequest(BaseModel):
    amount: float
    destination_account_id: Optional[str] = None


class TransactionResponse(BaseModel):
    transaction_id: str
    type: str
    account_id: str
    destination_account_id: Optional[str] = None
    amount: float
    timestamp: datetime
