"""File for SQLAlchemy models"""

# Import External Libraries
import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum

# Import SQLAlchey-related Libraries
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class JobStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Contract(Base):

    __tablename__ = "contracts"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(
            uuid.uuid4(),
        ),
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    s3_key: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
    )
    status: Mapped[JobStatus] = mapped_column(
        SqlEnum(JobStatus),
        default=JobStatus.PENDING,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=timezone.utc,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=timezone.utc,
        onupdate=timezone.utc,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    report: Mapped["ComplianceReport | None"] = relationship(
        back_populates="contract",
        uselist=False,
    )


class ComplianceReport(Base):

    __tablename__ = "compliance_reports"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    contract_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("contracts.id"),
        nullable=False,
    )
    total_clauses: Mapped[int] = mapped_column(default=0)
    non_compliant_clauses: Mapped[int] = mapped_column(default=0)
    report_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    report_s3_key: Mapped[str | None] = mapped_column(
        String(512),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=timezone.utc,
        nullable=False,
    )

    contract: Mapped["Contract"] = relationship(back_populates="report")
