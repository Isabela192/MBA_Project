from typing import Optional, List
from datetime import datetime
from uuid import uuid4
from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from decimal import Decimal
from uuid import UUID


class UserType(str, Enum):
    CLIENT = "client"
    MANAGER = "manager"


class AccountType(str, Enum):
    SAVINGS = "savings"
    CHECKING = "checking"


class AccountStatus(str, Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    CLOSED = "closed"


class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER = "transfer"


class TransactionStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class User(SQLModel, table=True):
    __tablename__ = "users"
    id: Optional[int] = Field(default=None, primary_key=True)
    document_id: str = Field(max_length=14, index=True, unique=True)
    username: str = Field(max_length=50, index=True, unique=True)
    email: str = Field(max_length=100, index=True, unique=True)
    user_type: UserType
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)
    is_staff: Optional[bool] = Field(default=False)

    # Relationships
    accounts: List["Account"] = Relationship(back_populates="owner")


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: UUID = Field(default_factory=uuid4, index=True, unique=True)
    balance: Decimal = Field(default=Decimal("0"))
    account_type: AccountType
    status: AccountStatus = Field(default=AccountStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = Field(default=None)

    # foreign key
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    # Relationships
    owner: Optional["User"] = Relationship(back_populates="accounts")
    outgoing_transactions: List["Transaction"] = Relationship(
        back_populates="from_account",
        sa_relationship_kwargs={"foreign_keys": "Transaction.from_account_id"},
    )
    incoming_transactions: List["Transaction"] = Relationship(
        back_populates="to_account",
        sa_relationship_kwargs={"foreign_keys": "Transaction.to_account_id"},
    )


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: UUID = Field(default_factory=uuid4, index=True, unique=True)
    type: TransactionType
    amount: Decimal = Field(gt=0)
    status: TransactionStatus = Field(default=TransactionStatus.PENDING)
    timestamp: datetime = Field(default_factory=datetime.now)

    # foreign keys
    from_account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")
    to_account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")

    # Relationships
    from_account: Optional["Account"] = Relationship(
        back_populates="outgoing_transactions",
        sa_relationship_kwargs={"foreign_keys": "Transaction.from_account_id"},
    )
    to_account: Optional["Account"] = Relationship(
        back_populates="incoming_transactions",
        sa_relationship_kwargs={"foreign_keys": "Transaction.to_account_id"},
    )
