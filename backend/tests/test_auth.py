"""
Auth Tests — Registration, Login, Logout, Token Refresh, Edge Cases
Target: >90% coverage on auth module.
"""

import pytest
from httpx import AsyncClient


# =============================================================================
# Registration Tests
# =============================================================================


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """Test successful user registration."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePass123!",
            "full_name": "New User",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "Registration successful"
    assert data["user"]["email"] == "newuser@example.com"
    assert data["user"]["full_name"] == "New User"
    assert data["user"]["role"] == "user"
    assert "access_token" in response.cookies
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Test registration with an email that's already taken."""
    user_data = {
        "email": "duplicate@example.com",
        "password": "SecurePass123!",
        "full_name": "First User",
    }
    # First registration
    response1 = await client.post("/auth/register", json=user_data)
    assert response1.status_code == 201

    # Duplicate registration
    response2 = await client.post("/auth/register", json=user_data)
    assert response2.status_code == 409
    assert "already registered" in response2.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email(client: AsyncClient) -> None:
    """Test registration with invalid email format."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "not-an-email",
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient) -> None:
    """Test registration with password that's too short."""
    response = await client.post(
        "/auth/register",
        json={
            "email": "user@example.com",
            "password": "short",
        },
    )
    assert response.status_code == 422


# =============================================================================
# Login Tests
# =============================================================================


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Test successful login."""
    # Register first
    await client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "password": "SecurePass123!",
            "full_name": "Login User",
        },
    )

    # Login
    response = await client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "SecurePass123!",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert data["user"]["email"] == "login@example.com"
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """Test login with wrong password."""
    await client.post(
        "/auth/register",
        json={
            "email": "wrong_pass@example.com",
            "password": "SecurePass123!",
        },
    )

    response = await client.post(
        "/auth/login",
        json={
            "email": "wrong_pass@example.com",
            "password": "WrongPassword!",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient) -> None:
    """Test login with email that doesn't exist."""
    response = await client.post(
        "/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123!",
        },
    )
    assert response.status_code == 401


# =============================================================================
# Protected Route Tests
# =============================================================================


@pytest.mark.asyncio
async def test_get_me_authenticated(authenticated_client: AsyncClient) -> None:
    """Test /auth/me with valid authentication."""
    response = await authenticated_client.get("/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient) -> None:
    """Test /auth/me without authentication."""
    response = await client.get("/auth/me")
    assert response.status_code == 401


# =============================================================================
# Logout Tests
# =============================================================================


@pytest.mark.asyncio
async def test_logout_success(authenticated_client: AsyncClient) -> None:
    """Test successful logout clears cookies."""
    response = await authenticated_client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json()["message"] == "Logged out successfully"


# =============================================================================
# Token Refresh Tests
# =============================================================================


@pytest.mark.asyncio
async def test_refresh_without_token(client: AsyncClient) -> None:
    """Test token refresh without refresh token cookie."""
    response = await client.post("/auth/refresh")
    assert response.status_code == 401
    assert "Refresh token missing" in response.json()["detail"]
