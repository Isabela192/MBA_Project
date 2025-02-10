from sqlmodel import SQLModel, create_engine, Session, Field, Column, String, UUID, DateTime, Decimal, Relationship
from uuid import uuid4

class UserBase(SQLModel, table=True):
    account_id: UUID = Field(default_factory=uuid4, primary_key=True)
    document_id: str
    username: str
    email: str

class AccountBase(SQLModel, table=True):
    account_id: UUID = Field(default_factory=uuid4)
    document_id: str
    balance: Decimal = Decimal("0")
    account_type: str
    status: str = "ACTIVE"

class DepositRequest(SQLModel, table=True):
    amount: Decimal = Field(gt=0)