"""
Audit Log Tests — Immutability & Compliance
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.audit_log import AuditLog


@pytest.mark.asyncio
async def test_audit_log_creation(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test that API requests create audit log entries."""
    # Make a request that should be logged
    await authenticated_client.get("/compliance/status")

    # Check audit logs
    result = await db_session.execute(
        select(AuditLog).where(AuditLog.resource == "/compliance/status")
    )
    logs = result.scalars().all()
    assert len(logs) >= 1

    log = logs[0]
    assert log.method == "GET"
    assert log.resource == "/compliance/status"
    assert log.status_code == 200
    assert log.ip_address is not None
    assert log.details is not None


@pytest.mark.asyncio
async def test_audit_log_captures_user_id(
    authenticated_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test that audit logs capture the authenticated user's ID."""
    await authenticated_client.get("/auth/me")

    result = await db_session.execute(select(AuditLog).where(AuditLog.resource == "/auth/me"))
    logs = result.scalars().all()
    assert len(logs) >= 1
    # User ID should be captured for authenticated requests
    assert logs[0].user_id is not None


@pytest.mark.asyncio
async def test_health_not_audited(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test that /health requests are NOT logged (skip path)."""
    await client.get("/health")

    result = await db_session.execute(select(AuditLog).where(AuditLog.resource == "/health"))
    logs = result.scalars().all()
    assert len(logs) == 0


@pytest.mark.asyncio
async def test_audit_log_has_required_fields(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Test that audit log entries have all SEBI-required fields."""
    await client.get("/")

    result = await db_session.execute(select(AuditLog).where(AuditLog.resource == "/"))
    logs = result.scalars().all()
    assert len(logs) >= 1

    log = logs[0]
    assert log.action is not None
    assert log.resource is not None
    assert log.method is not None
    assert log.ip_address is not None
    assert log.status_code is not None
    assert log.timestamp is not None
