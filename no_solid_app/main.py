from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Header
from sqlmodel import Session, select
from typing import List

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from database.database import get_session, create_db_and_tables
from database.models import (
    User,
    UserCreate,
    UserResponse,
    LoginRequest,
    LoginResponse,
    AccountCreate,
    AccountResponse,
    TransactionRequest,
    TransactionResponse,
)
from helpers.singleton import auth_manager, user_creator
from helpers.facade import transaction_facade
from helpers.abstract_factory import AccountFactoryProducer


# Define lifespan first before passing it to FastAPI constructor
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up...")
    create_db_and_tables()
    yield
    print("Shutting down...")


# Then create the app with the lifespan
app = FastAPI(lifespan=lifespan, title="NO SOLID Bank API", version="1.5.0")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("static/welcome.html")


# --- User Routes ---
@app.post("/users/", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_session)):
    # Use the Singleton pattern for user creation
    user = user_creator.create_user(user_data.dict(), db)
    return {
        "document_id": user.document_id,
        "username": user.username,
        "email": user.email,
        "user_type": user.user_type,
        "account_id": user.account_id,
    }


@app.post("/login/", response_model=LoginResponse)
async def login(login_data: LoginRequest, db: Session = Depends(get_session)):
    # Use the Singleton pattern for authentication
    auth_result = auth_manager.authenticate_user(
        login_data.username, login_data.password, db
    )
    if not auth_result:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "message": "Login successful",
        "user": auth_result["user"],
        "session_id": auth_result["session_id"],
    }


# --- Account Routes ---
@app.post("/accounts/", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    username: str = Header(...),
    session_id: str = Header(...),
    db: Session = Depends(get_session),
):
    # Verify authentication using Singleton pattern
    if not auth_manager.is_authenticated(username, session_id, db):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get user from username
    statement = select(User).where(User.username == username)
    user = db.exec(statement).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Create account using Abstract Factory pattern
    factory = AccountFactoryProducer.get_factory(account_data.account_type)
    account_object = factory.create_account(account_data.document_id, db)
    account = account_object.create_db_entry(account_data.document_id, db)
    features = account_object.get_features()

    return {
        "account_id": account.account_id,
        "document_id": account.document_id,
        "balance": account.balance,
        "account_type": account.account_type,
        "status": account.status,
        "features": features,
        "created_at": account.created_at,
    }


# --- Transaction Routes (using Facade pattern) ---
@app.post("/accounts/{account_id}/deposit", response_model=TransactionResponse)
async def deposit(
    account_id: str,
    request: TransactionRequest,
    username: str = Header(...),
    session_id: str = Header(...),
    db: Session = Depends(get_session),
):
    # Verify authentication
    if not auth_manager.is_authenticated(username, session_id, db):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Process deposit via Facade pattern
    result = transaction_facade.process_deposit(account_id, request.amount, db)
    return result


@app.post("/accounts/{account_id}/withdraw", response_model=TransactionResponse)
async def withdraw(
    account_id: str,
    request: TransactionRequest,
    username: str = Header(...),
    session_id: str = Header(...),
    db: Session = Depends(get_session),
):
    """
    Withdraw funds from an account using the Facade pattern.

    - Uses singleton pattern for authentication
    - Uses facade pattern for transaction processing
    - Account validation and funds checking are handled by the facade
    """
    # Verify authentication
    if not auth_manager.is_authenticated(username, session_id, db):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Process withdrawal via Facade pattern
    result = transaction_facade.process_withdrawal(account_id, request.amount, db)
    return result


@app.post("/accounts/{account_id}/transfer", response_model=TransactionResponse)
async def transfer(
    account_id: str,
    request: TransactionRequest,
    username: str = Header(...),
    session_id: str = Header(...),
    db: Session = Depends(get_session),
):
    # Verify authentication
    if not auth_manager.is_authenticated(username, session_id, db):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify destination account is provided
    if not request.destination_account_id:
        raise HTTPException(status_code=400, detail="Destination account is required")

    # Process transfer via Facade pattern
    result = transaction_facade.process_transfer(
        account_id, request.destination_account_id, request.amount, db
    )
    return result


@app.get(
    "/accounts/{account_id}/transactions", response_model=List[TransactionResponse]
)
async def get_transactions(
    account_id: str,
    username: str = Header(...),
    session_id: str = Header(...),
    db: Session = Depends(get_session),
):
    # Verify authentication
    if not auth_manager.is_authenticated(username, session_id, db):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get transactions via Facade pattern
    transactions = transaction_facade.get_account_transactions(account_id, db)
    return transactions


@app.get("/accounts/{account_id}/balance")
async def get_balance(
    account_id: str,
    username: str = Header(...),
    session_id: str = Header(...),
    db: Session = Depends(get_session),
):
    # Verify authentication
    if not auth_manager.is_authenticated(username, session_id, db):
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get balance via Facade pattern
    balance = transaction_facade.get_account_balance(account_id, db)
    return balance
