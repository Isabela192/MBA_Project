from contextlib import asynccontextmanager
from decimal import Decimal
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from database.database import create_db_and_tables, get_session
from database.models import Account, User
from helpers.commands import (
    DepositCommand,
    GetTransactionsCommand,
    TransferCommand,
    WithdrawCommand,
)
from helpers.factories import ClientFactory, ManagerFactory
from helpers.proxies import AccountProxy, RealAccount


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    create_db_and_tables()
    yield
    print("Shutting down...")


app = FastAPI(lifespan=lifespan, title="SOLID Bank API")

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


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/welcome.html")


# --- User Routes (using Factory pattern) ---
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
async def create_user(
    user_data: UserCreate,
    user_type: str = "client",
    session: Session = Depends(get_session),
    account_data: AccountCreate = None,
):
    if user_type not in ["client", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user type"
        )

    factory = ClientFactory() if user_type == "client" else ManagerFactory()
    user = factory.create_user(user_data.model_dump(), session)

    # Create a default checking account if none provided
    if account_data is None:
        account_data = AccountCreate(account_type="checking")

    account = factory.create_user_account(
        user=user, account_data=account_data.model_dump(), session=session
    )

    return {
        "user_id": user.id,
        "username": user.username,
        "account": {
            "account_id": str(account.account_id),
            "account_type": account.account_type,
            "balance": str(account.balance),
        },
    }


# --- Transaction Routes (using command pattern) ---
@app.post("/accounts/{account_id}/deposit")
async def deposit(
    account_id: UUID,
    deposit_request: DepositRequest,
    session: Session = Depends(get_session),
):
    command = DepositCommand(account_id=account_id, amount=deposit_request.amount)
    transaction = command.execute(session)

    if transaction.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=transaction.get("message", "Deposit failed"),
        )

    real_account = RealAccount()
    account_proxy = AccountProxy(real_account)
    balance = account_proxy.get_balance(account_id, session)
    return {"message": "Deposit successful", "balance": balance}


@app.post("/accounts/{account_id}/withdraw")
async def withdraw(
    account_id: UUID,
    withdraw_request: WithdrawRequest,
    session: Session = Depends(get_session),
):
    command = WithdrawCommand(account_id=account_id, amount=withdraw_request.amount)
    transaction = command.execute(session)

    if transaction.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=transaction.get("message", "Withdraw failed"),
        )

    real_account = RealAccount()
    account_proxy = AccountProxy(real_account)
    balance = account_proxy.get_balance(account_id, session)
    return {"message": "Withdraw successful", "balance": balance}


@app.post("/accounts/{account_id}/transfer")
async def transfer(
    account_id: UUID,
    transfer_request: TransferRequest,
    session: Session = Depends(get_session),
):
    command = TransferCommand(
        from_account_id=account_id,
        to_account_id=transfer_request.to_account_id,
        amount=transfer_request.amount,
    )
    transaction = command.execute(session)

    if transaction.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=transaction.get("message", "Transfer failed"),
        )

    real_account = RealAccount()
    proxy = AccountProxy(real_account)
    balance = proxy.get_balance(str(account_id), session)

    return {
        "message": "Transfer successful",
        "transaction": transaction,
        "new_balance": balance,
    }


@app.get("/accounts/{account_id}/balance")
async def get_balance(account_id: UUID, session: Session = Depends(get_session)):
    real_account = RealAccount()
    proxy = AccountProxy(real_account)
    balance = proxy.get_balance(account_id, session)

    if balance is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found",
        )

    return {"balance": balance}


class BalanceUpdateRequest(BaseModel):
    amount: Decimal


@app.put("/accounts/{account_id}/balance")
async def update_balance(
    account_id: UUID,
    update_request: BalanceUpdateRequest,
    session: Session = Depends(get_session),
):
    real_account = RealAccount()
    account_proxy = AccountProxy(real_account)

    result = account_proxy.update_balance(account_id, update_request.amount, session)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Account {account_id} not found",
        )

    new_balance = account_proxy.get_balance(account_id, session)
    return {"message": "Balance updated successfully", "balance": new_balance}


@app.get("/accounts/{account_id}/transactions")
async def get_transactions(account_id: UUID, session: Session = Depends(get_session)):
    command = GetTransactionsCommand(account_id=str(account_id))
    result = command.execute(session)

    if result.get("status") == "failed":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", f"Account {account_id} not found"),
        )

    return {"account_id": result["account_id"], "transactions": result["transactions"]}


@app.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
):
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )

    session.delete(user)
    session.commit()
    return {"message": "User deleted successfully"}
