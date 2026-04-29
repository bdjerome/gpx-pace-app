import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TemplateGpxFile(Base):
    """Platform-provided GPX routes available to all users (no owner)."""

    __tablename__ = "template_gpx_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    gcs_path: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    distance_m: Mapped[Optional[Decimal]] = mapped_column(Numeric, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    #one-to-many relationship with RacePlan
    race_plans: Mapped[list["RacePlan"]] = relationship(back_populates="template_gpx_file")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    hashed_pw: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    #one-to-many relationship with GpxFile and RacePlan
    gpx_files: Mapped[list["GpxFile"]] = relationship(back_populates="user")
    race_plans: Mapped[list["RacePlan"]] = relationship(back_populates="user")


class GpxFile(Base):
    __tablename__ = "gpx_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    file_name: Mapped[str] = mapped_column(Text, nullable=False)
    gcs_path: Mapped[str] = mapped_column(Text, nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(server_default=text("now()"))

    #many-to-one relationship with User, one-to-many relationship with RacePlan
    user: Mapped["User"] = relationship(back_populates="gpx_files")
    race_plans: Mapped[list["RacePlan"]] = relationship(back_populates="gpx_file")


class RacePlan(Base):
    __tablename__ = "race_plans"

    #constraint to ensure exactly one of gpx_file_id or template_gpx_file_id is non-null
    __table_args__ = (
        CheckConstraint(
            "(gpx_file_id IS NOT NULL)::int + (template_gpx_file_id IS NOT NULL)::int = 1",
            name="gpx_source_check",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    gpx_file_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("gpx_files.id"), nullable=True
    )
    template_gpx_file_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("template_gpx_files.id"), nullable=True
    )
    nickname: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    updated_at: Mapped[datetime] = mapped_column(
        server_default=text("now()"), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    #many-to-one relationships with User, GpxFile, and TemplateGpxFile
    user: Mapped["User"] = relationship(back_populates="race_plans")
    gpx_file: Mapped[Optional["GpxFile"]] = relationship(back_populates="race_plans")
    template_gpx_file: Mapped[Optional["TemplateGpxFile"]] = relationship(
        back_populates="race_plans"
    )
    notes: Mapped[list["PlanNote"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan"
    )


class PlanNote(Base):
    """Per-km notes attached to a saved race plan."""

    __tablename__ = "plan_notes"

    plan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("race_plans.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    km: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False)

    plan: Mapped["RacePlan"] = relationship(back_populates="notes")
