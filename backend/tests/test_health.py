"""
Health & System Endpoint Tests
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test /health endpoint returns healthy status."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"
    assert "timestamp" in data
    assert data["service"] == "TradingPlatform"


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Test / root endpoint returns API info."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "AI Trading Platform API"
    assert data["version"] == "0.1.0"
    assert data["docs"] == "/docs"


@pytest.mark.asyncio
async def test_compliance_status_authenticated(
    authenticated_client: AsyncClient,
) -> None:
    """Test /compliance/status requires auth and returns compliance data."""
    response = await authenticated_client.get("/compliance/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "compliant"
    checks = data["checks"]
    assert checks["static_ip_architecture"] is True
    assert checks["audit_logging_active"] is True
    assert checks["ip_rotation_code"] is False  # Must always be False
    assert checks["jwt_httponly_cookies"] is True
    assert checks["algo_id_support"] is True
    assert "NautilusTrader" in checks["engine_attribution"]


@pytest.mark.asyncio
async def test_compliance_status_unauthenticated(client: AsyncClient) -> None:
    """Test /compliance/status rejects unauthenticated requests."""
    response = await client.get("/compliance/status")
    assert response.status_code == 401
