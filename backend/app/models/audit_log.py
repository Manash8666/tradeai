"""
Audit Log Model — Immutable SEBI-Compliant Logging
Every action is logged and cannot be modified or deleted.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.database import Base


class AuditLog(Base):
    """
    Immutable audit log entry for SEBI compliance.
    Records are append-only — no UPDATE or DELETE operations.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,  # Unauthenticated requests have no user_id
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    resource: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    method: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    ip_address: Mapped[str] = mapped_column(
        String(45),  # IPv6 max length
        nullable=False,
    )
    status_code: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    details: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    algo_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action={self.action}, "
            f"user_id={self.user_id}, timestamp={self.timestamp})>"
        )
