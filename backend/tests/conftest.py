"""
Test Configuration & Fixtures
Uses in-memory SQLite for fast, isolated tests.
"""

import os
import asyncio
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set test environment BEFORE importing app modules
os.environ["APP_ENV"] = "testing"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only-do-not-use-in-production"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from backend.app.database import Base, get_db  # noqa: E402
from backend.app.main import app  # noqa: E402


# Test database engine (SQLite async)
test_engine = create_async_engine(
    "sqlite+aiosqlite:///./test.db",
    echo=False,
)

test_session_factory = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Override DB dependency with test database."""
    async with test_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Override the database dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create and tear down test database for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Direct database session for test setup."""
    async with test_session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient) -> AsyncClient:
    """Client with auth cookies — registers a test user and logs in."""
    register_data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
    }
    response = await client.post("/auth/register", json=register_data)
    assert response.status_code == 201

    # Cookies are automatically stored on the client
    return client
