from typing import Optional
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime


# --- Request Models ---
class UserCreateRequest(BaseModel):
    """Request model for creating a user"""

    document_id: str = Field(..., description="User's document ID")
    username: str = Field(..., description="Username")
    email: EmailStr = Field(..., description="Email address")
    user_type: str = Field(..., description="User type: client or manager")
    is_staff: bool = Field(False, description="Is user a staff member?")


class AccountCreateRequest(BaseModel):
    """Request model for creating an account"""

    document_id: str = Field(..., description="Account document ID")
    account_type: str = Field(..., description="Account type: checking or savings")
    initial_balance: Decimal = Field(Decimal("0"), description="Initial balance")


class TransactionRequest(BaseModel):
    """Request model for transactions"""

    amount: Decimal = Field(gt=0, description="Transaction amount")
    destination_account_id: Optional[UUID] = Field(
        None, description="Destination account ID for transfers"
    )


class LoginRequest(BaseModel):
    """Request model for login"""

    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


# --- Response Models ---
class UserResponse(BaseModel):
    """Response model for user data"""

    id: int = Field(..., description="User ID")
    account_id: UUID = Field(..., description="User account ID")
    document_id: str = Field(..., description="User document ID")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email")
    user_type: str = Field(..., description="User type")
    created_at: datetime = Field(..., description="Creation timestamp")


class AccountResponse(BaseModel):
    """Response model for account data"""

    id: int = Field(..., description="Account ID")
    account_id: UUID = Field(..., description="Account UUID")
    document_id: str = Field(..., description="Account document ID")
    balance: float = Field(..., description="Account balance")
    account_type: str = Field(..., description="Account type")
    status: str = Field(..., description="Account status")
    user_id: int = Field(..., description="Owner user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    features: dict = Field(..., description="Account features")


class TransactionResponse(BaseModel):
    """Response model for transaction data"""

    transaction_id: UUID = Field(..., description="Transaction ID")
    type: str = Field(..., description="Transaction type")
    amount: float = Field(..., description="Transaction amount")
    status: str = Field(..., description="Transaction status")
    timestamp: datetime = Field(..., description="Transaction timestamp")

    # Optional fields based on transaction type
    account_id: Optional[UUID] = Field(
        None, description="Account ID (for deposits/withdrawals)"
    )
    from_account_id: Optional[int] = Field(
        None, description="Source account ID (for transfers)"
    )
    to_account_id: Optional[int] = Field(
        None, description="Destination account ID (for transfers)"
    )
    source_account: Optional[UUID] = Field(
        None, description="Source account UUID (for transfers)"
    )
    destination_account: Optional[UUID] = Field(
        None, description="Destination account UUID (for transfers)"
    )
    new_balance: Optional[float] = Field(
        None, description="New account balance after transaction"
    )
    source_balance: Optional[float] = Field(
        None, description="Source account balance after transfer"
    )
    destination_balance: Optional[float] = Field(
        None, description="Destination account balance after transfer"
    )


class LoginResponse(BaseModel):
    """Response model for login"""

    message: str = Field(..., description="Login status message")
    user: dict = Field(..., description="User information")
    session_id: str = Field(..., description="Session ID")
