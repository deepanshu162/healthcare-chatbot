from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for user registration."""
    name: str = Field(..., min_length=2, max_length=60, description="Full name of user.")
    email: EmailStr = Field(..., description="Valid email address.")
    password: str = Field(..., min_length=6, max_length=128, description="Account password (min 6 chars).")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        clean = v.strip()
        if not clean:
            raise ValueError("Name cannot be empty.")
        return clean

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserLoginRequest(BaseModel):
    """Payload for user login."""
    email: EmailStr = Field(..., description="Account email address.")
    password: str = Field(..., min_length=1, description="Account password.")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class UserResponse(BaseModel):
    """Public user profile representation."""
    id: str = Field(..., description="Unique user identifier.")
    name: str = Field(..., description="User's display name.")
    email: str = Field(..., description="User's email.")
    created_at: Optional[str] = Field(default=None, description="ISO timestamp of account creation.")


class TokenResponse(BaseModel):
    """JWT authentication token response."""
    access_token: str = Field(..., description="JWT Bearer token.")
    token_type: str = Field(default="bearer", description="Token type.")
    user: UserResponse = Field(..., description="Authenticated user info.")


class TokenData(BaseModel):
    """Internal decoded JWT token payload."""
    user_id: Optional[str] = None
    email: Optional[str] = None
