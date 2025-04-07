from fastapi import FastAPI, HTTPException
from uuid import UUID

# Database imports
from database.database import create_db_and_tables
from database.user_creator import UserCreator
from database.account_factory import get_account_factory
from database.models import UserType

# Helper imports
from helpers.transaction_facade import TransactionFacade
from helpers.auth_manager import AuthenticationManager

# API models
from api.models import (
    UserCreateRequest,
    AccountCreateRequest,
    TransactionRequest,
    LoginRequest,
    UserResponse,
    AccountResponse,
    TransactionResponse,
    LoginResponse,
)

# Initialize FastAPI
app = FastAPI(
    title="NO SOLID Bank API",
    description="Banking API for demonstrating design patterns",
    version="1.0.0",
)

# Initialize singletons
auth_manager = AuthenticationManager()
transaction_facade = TransactionFacade()


@app.on_event("startup")
async def on_startup():
    """Initialize database on startup"""
    create_db_and_tables()


@app.get("/")
async def root():
    """Root endpoint"""
    return {"Welcome! This is NO SOLID App"}


# --- User Management ---
@app.post("/users/", response_model=UserResponse)
async def create_user(user_data: UserCreateRequest):
    """Create a new user"""
    user_creator = UserCreator()

    # Convert UserType string to enum
    try:
        user_type = UserType(user_data.user_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid user type: {user_data.user_type}. Must be 'client' or 'manager'",
        )

    # Create the user in the database
    try:
        user_dict = user_data.model_dump()
        user_dict["user_type"] = user_type
        user = user_creator.create_user(user_dict)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")

    # Register with authentication manager
    auth_manager.register_user(user_dict)

    # Return user information
    return UserResponse(
        id=user.id,
        account_id=user.account_id,
        document_id=user.document_id,
        username=user.username,
        email=user.email,
        user_type=user.user_type.value,
        created_at=user.created_at,
    )


@app.post("/login/", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    """Log in a user"""
    user = auth_manager.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    session_id = user.pop("session_id")
    return LoginResponse(message="Login successful", user=user, session_id=session_id)


@app.post("/logout/")
async def logout(username: str):
    """Log out a user"""
    success = auth_manager.logout(username)
    if not success:
        raise HTTPException(status_code=400, detail="User not logged in")

    return {"message": "Logout successful"}


# --- Account Management ---
@app.post("/accounts/", response_model=AccountResponse)
async def create_account(account_data: AccountCreateRequest, user_id: int):
    """Create a new account for a user"""
    # Get the appropriate account factory based on account type
    try:
        factory = get_account_factory(account_data.account_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Create the account
    try:
        account = factory.create_account(
            user_id=user_id,
            document_id=account_data.document_id,
            initial_balance=account_data.initial_balance,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return account information
    return AccountResponse(
        id=account.id,
        account_id=account.account_id,
        document_id=account.document_id,
        balance=float(account.balance),
        account_type=account.account_type.value,
        status=account.status.value,
        user_id=account.user_id,
        created_at=account.created_at,
        features=factory.get_features(),
    )


# --- Transaction Management ---
@app.post("/accounts/{account_id}/deposit", response_model=TransactionResponse)
async def deposit(account_id: UUID, request: TransactionRequest):
    """Deposit money into an account"""
    try:
        return transaction_facade.process_deposit(account_id, request.amount)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing deposit: {str(e)}"
        )


@app.post("/accounts/{account_id}/withdraw", response_model=TransactionResponse)
async def withdraw(account_id: UUID, request: TransactionRequest):
    """Withdraw money from an account"""
    try:
        return transaction_facade.process_withdraw(account_id, request.amount)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing withdrawal: {str(e)}"
        )


@app.post("/accounts/{account_id}/transfer", response_model=TransactionResponse)
async def transfer(account_id: UUID, request: TransactionRequest):
    """Transfer money between accounts"""
    if not request.destination_account_id:
        raise HTTPException(status_code=400, detail="Destination account is required")

    try:
        return transaction_facade.process_transfer(
            account_id, request.destination_account_id, request.amount
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing transfer: {str(e)}"
        )


@app.get("/accounts/{account_id}/transactions")
async def get_transactions(account_id: UUID, limit: int = 10):
    """Get transaction history for an account"""
    try:
        return transaction_facade.get_transaction_history(account_id, limit)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving transaction history: {str(e)}"
        )
