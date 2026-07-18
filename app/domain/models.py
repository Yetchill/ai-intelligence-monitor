"""SQLAlchemy 2.x mappings for the core persistence model."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.domain.enums import Category, CrawlStatus, SourceOrigin, SourceType


def utc_now() -> datetime:
    """Return the current UTC time for model defaults."""

    return datetime.now(UTC)


def enum_values[EnumT: StrEnum](members: type[EnumT]) -> list[str]:
    """Return stable persisted values for a string enum."""

    return [member.value for member in members]


def enum_type[EnumT: StrEnum](enum_class: type[EnumT]) -> Enum:
    """Create a portable string-backed SQLAlchemy enum."""

    return Enum(
        enum_class,
        values_callable=enum_values,
        native_enum=False,
        create_constraint=True,
        validate_strings=True,
    )


class Base(DeclarativeBase):
    """Declarative mapping base."""


class Source(Base):
    """A configured entry point from which intelligence will eventually be collected."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[SourceType] = mapped_column(enum_type(SourceType), nullable=False)
    start_url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    default_category: Mapped[Category | None] = mapped_column(enum_type(Category), nullable=True)
    collector_name: Mapped[str] = mapped_column(String(100), nullable=False)
    collector_config: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    discovery_status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    discovery_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    requires_custom_collector: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    origin: Mapped[SourceOrigin] = mapped_column(
        enum_type(SourceOrigin), nullable=False, default=SourceOrigin.PRESET
    )
    last_tested_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )

    items: Mapped[list["IntelligenceItem"]] = relationship(
        back_populates="source", passive_deletes=True
    )


class IntelligenceItem(Base):
    """A normalized intelligence record discovered from a source."""

    __tablename__ = "intelligence_items"
    __table_args__ = (
        UniqueConstraint("source_id", "fingerprint", name="uq_item_source_fingerprint"),
        Index("ix_items_category_discovered", "category", "discovered_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(
        ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(1000), nullable=False)
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False, unique=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    category: Mapped[Category] = mapped_column(
        enum_type(Category), nullable=False, default=Category.UNCLASSIFIED
    )
    classification_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    classification_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    automatic_category_provider: Mapped[str | None] = mapped_column(String(100), nullable=True)
    manual_category: Mapped[Category | None] = mapped_column(enum_type(Category), nullable=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    extra: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    source: Mapped[Source] = relationship(back_populates="items")
    revisions: Mapped[list["ItemRevision"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", passive_deletes=True
    )


class CrawlRun(Base):
    """Summary and lifecycle state for one complete update run."""

    __tablename__ = "crawl_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[CrawlStatus] = mapped_column(
        enum_type(CrawlStatus), nullable=False, default=CrawlStatus.RUNNING
    )
    source_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_success: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    discovered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    new_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unclassified_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    revisions: Mapped[list["ItemRevision"]] = relationship(back_populates="crawl_run")


class ItemRevision(Base):
    """A before/after snapshot for a material change to an intelligence item."""

    __tablename__ = "item_revisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(
        ForeignKey("intelligence_items.id", ondelete="CASCADE"), nullable=False, index=True
    )
    crawl_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("crawl_runs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    old_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    new_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)

    item: Mapped[IntelligenceItem] = relationship(back_populates="revisions")
    crawl_run: Mapped[CrawlRun | None] = relationship(back_populates="revisions")
