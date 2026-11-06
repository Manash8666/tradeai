"""
Auth Schemas — Pydantic models for request/response validation.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=255)
    pan: str = Field(default="ABCDE1234F", max_length=12)
    date_of_birth: str = Field(default="1990-01-01")
    address: str = Field(default="Mumbai, Maharashtra, India")
    phone_number: str = Field(default="+919876543210", max_length=20)

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public user data (no password)."""

    id: UUID
    email: str
    full_name: str
    role: str
    is_verified: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuthResponse(BaseModel):
    """Auth response — tokens are in HTTPOnly cookies, not body."""

    message: str
    user: UserResponse


class TokenRefreshResponse(BaseModel):
    """Token refresh response."""

    message: str

