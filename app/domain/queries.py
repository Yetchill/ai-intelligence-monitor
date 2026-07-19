"""Persistence-neutral query values used by application and Web adapters."""

from dataclasses import dataclass
from datetime import datetime

from app.domain.enums import Category, CrawlStatus, RunTrigger, SourceType


@dataclass(frozen=True, slots=True)
class Page[EntryT]:
    entries: tuple[EntryT, ...]
    page: int
    per_page: int
    total: int

    @property
    def total_pages(self) -> int:
        return max(1, (self.total + self.per_page - 1) // self.per_page)


@dataclass(frozen=True, slots=True)
class ItemFilter:
    """Filters shared by paginated lists and complete bounded exports."""

    keyword: str | None = None
    category: Category | None = None
    source_id: int | None = None
    favorite: bool | None = None
    published_from: datetime | None = None
    published_to: datetime | None = None
    discovered_from: datetime | None = None
    discovered_to: datetime | None = None
    unclassified: bool | None = None


@dataclass(frozen=True, slots=True)
class ItemQuery(ItemFilter):
    page: int = 1
    per_page: int = 20


@dataclass(frozen=True, slots=True)
class ItemListEntry:
    id: int
    title: str
    original_url: str | None
    summary: str | None
    published_at: datetime | None
    discovered_at: datetime
    updated_at: datetime
    automatic_category: Category
    manual_category: Category | None
    is_favorite: bool
    source_id: int
    source_name: str

    @property
    def effective_category(self) -> Category:
        return self.manual_category or self.automatic_category

    @property
    def category_origin(self) -> str:
        return "人工" if self.manual_category is not None else "自动"


@dataclass(frozen=True, slots=True)
class SourceOption:
    id: int
    name: str


@dataclass(frozen=True, slots=True)
class SourceListEntry:
    id: int
    name: str
    start_url: str | None
    source_type: SourceType
    collector_name: str
    enabled: bool
    default_category: Category | None
    discovery_status: str | None
    discovery_confidence: float | None
    requires_custom_collector: bool
    last_checked_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None


@dataclass(frozen=True, slots=True)
class CrawlRunListEntry:
    id: int
    status: CrawlStatus
    trigger: RunTrigger
    started_at: datetime
    finished_at: datetime | None
    source_total: int
    source_success: int
    source_failed: int
    discovered_count: int
    new_count: int
    updated_count: int
    skipped_count: int
    unclassified_count: int
    error_summary: str | None
