"""
KYC (Know Your Customer) Information Model
SEBI and PMLA Compliance
"""

import uuid
from datetime import date
from typing import Optional

from sqlalchemy import Date, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.database import Base
from backend.app.models.user import User

"""
KYC information linked to a User account.
One-to-one relationship with User.
"""

__tablename__ = "kyc_info"

id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    primary_key=True,
    default=uuid.uuid4,
)

user_id: Mapped[uuid.UUID] = mapped_column(
    UUID(as_uuid=True),
    nullable=False,
    unique=True,
    index=True,
)

# Personal Information
pan: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
date_of_birth: Mapped[date] = mapped_column(Date, nullable=False)
address: Mapped[str] = mapped_column(Text, nullable=False)
phone_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

# KYC Status
is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
verification_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, index=True)
verified_on: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
verification_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

# Relationship
user: Mapped["User"] = relationship("User", back_populates="kyc_info")

"""
def __repr__(self) -> str:
    return f"<KycInfo(id={self.id}, user_id={self.user_id}, pan={self.pan}, status={self.verification_status})>"
"""
