"""
Auth Service — JWT Token Management & Password Hashing
Secure, HTTPOnly cookie-based authentication.
"""

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.config import get_settings
from backend.app.models.user import User
from backend.app.models.session import UserSession

settings = get_settings()


# =============================================================================
# Password Hashing (bcrypt)
# =============================================================================


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# =============================================================================
# JWT Token Management
# =============================================================================


def create_access_token(user_id: str, role: str) -> str:
    """Create a short-lived JWT access token."""
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.jwt_access_token_expire_minutes),
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return str(jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))


def create_refresh_token(user_id: str) -> str:
    """Create a long-lived JWT refresh token."""
    payload: dict[str, Any] = {
        "sub": user_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days),
        "iat": datetime.now(timezone.utc),
        "jti": str(uuid.uuid4()),
    }
    return str(jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm))


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    return dict(
        jwt.decode(  # type: ignore[no-any-return]
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    )


def hash_token(token: str) -> str:
    """Hash a token for storage (sessions table)."""
    return hashlib.sha256(token.encode()).hexdigest()


# =============================================================================
# User Operations
# =============================================================================


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """Fetch a user by email address."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()  # type: ignore[no-any-return]


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Fetch a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()  # type: ignore[no-any-return]


async def create_user(
    db: AsyncSession,
    email: str,
    password: str,
    full_name: str = "",
    role: str = "user",
) -> User:
    """Create a new user with hashed password."""
    user = User(
        email=email.lower().strip(),
        hashed_password=hash_password(password),
        full_name=full_name,
        role=role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """Authenticate a user by email and password."""
    user = await get_user_by_email(db, email.lower().strip())
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


# =============================================================================
# Session Management
# =============================================================================


async def create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    refresh_token: str,
    ip_address: str,
    user_agent: str | None = None,
) -> UserSession:
    """Create a new user session with hashed refresh token."""
    session = UserSession(
        user_id=user_id,
        refresh_token_hash=hash_token(refresh_token),
        ip_address=ip_address,
        user_agent=user_agent,
        expires_at=datetime.now(timezone.utc)
        + timedelta(days=settings.jwt_refresh_token_expire_days),
    )
    db.add(session)
    await db.flush()
    return session


async def revoke_session(db: AsyncSession, session_id: uuid.UUID) -> None:
    """Revoke a session (logout)."""
    result = await db.execute(select(UserSession).where(UserSession.id == session_id))
    session = result.scalar_one_or_none()
    if session:
        session.is_active = False
        session.revoked_at = datetime.now(timezone.utc)


async def revoke_all_user_sessions(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Revoke all active sessions for a user."""
    result = await db.execute(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.is_active == True,  # noqa: E712
        )
    )
    sessions = result.scalars().all()
    for session in sessions:
        session.is_active = False
        session.revoked_at = datetime.now(timezone.utc)
