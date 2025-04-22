from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from fastapi import Depends, FastAPI, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlmodel import Session, select
from database.models import Account, User


from database.database import create_db_and_tables, get_session
from helpers.singleton import user_creator


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    create_db_and_tables()
    yield
    print("Shutting down...")


# Then create the app with the lifespan
app = FastAPI(lifespan=lifespan, title="NO SOLID Bank API")

app.mount("/static", StaticFiles(directory="static"), name="static")


class UserCreate(BaseModel):
    document_id: str = Field(json_schema_extra={"example": "12345678901"})
    name: str = Field(json_schema_extra={"example": "John Doe"})
    email: str = Field(json_schema_extra={"example": "jhon@doe.com.br"})
    username: str = Field(json_schema_extra={"example": "johndoe123"})


class AccountCreate(BaseModel):
    account_type: str = Field(json_schema_extra={"example": "checking"})


class DepositRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class WithdrawRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class TransferRequest(BaseModel):
    to_account_id: UUID
    amount: Decimal = Field(gt=0)


class BalanceUpdateRequest(BaseModel):
    amount: Decimal = Field(
        description="Amount to add (positive) or subtract (negative)"
    )
    account_type: str = Field(
        default="standard",
        description="Account type (standard or premium)",
        json_schema_extra={"example": "standard"},
    )


class TransactionResponse(BaseModel):
    transaction_id: UUID
    amount: Decimal
    type: str
    status: str
    timestamp: datetime


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/welcome.html")


# --- User Routes ---
@app.get("/users/")
async def get_users(session: Session = Depends(get_session)):
    statement = select(User)
    users = session.exec(statement).all()
    # Get all users with their accounts
    result = []
    for user in users:
        user_data = {
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type,
            "created_at": user.created_at,
            "accounts": [],
        }

        # Get accounts for each user
        statement = select(Account).where(Account.user_id == user.id)
        accounts = session.exec(statement).all()
        for account in accounts:
            user_data["accounts"].append(
                {
                    "account_id": str(account.account_id),
                    "account_type": account.account_type,
                    "balance": str(account.balance),
                    "status": account.status,
                }
            )

        result.append(user_data)

    return result


@app.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate, db: Session = Depends(get_session)):
    # Use the Singleton pattern for user creation
    user = user_creator.create_user(user_data.model_dump(), db)

    # Get the account associated with this user
    account = user.accounts[0] if user.accounts else None
    account_id = str(account.account_id) if account else None

    return {
        "document_id": user.document_id,
        "username": user.username,
        "email": user.email,
        "user_type": user.user_type,
        "account_id": account_id,
    }


# --- Transaction Routes (using Facade pattern) ---
