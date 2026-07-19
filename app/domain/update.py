"""Persistence-independent values returned by the update application services."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from app.domain.enums import CrawlStatus, RunTrigger


class UpdateMode(StrEnum):
    """Select ordinary incremental collection or bounded history collection."""

    INCREMENTAL = "incremental"
    HISTORY = "history"


class SourceUpdateStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SourceUpdateResult:
    source_id: int
    source_name: str
    status: SourceUpdateStatus
    discovered: int = 0
    new: int = 0
    updated: int = 0
    skipped: int = 0
    unclassified: int = 0
    error: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateResult:
    crawl_run_id: int
    status: CrawlStatus
    started_at: datetime
    finished_at: datetime
    source_total: int
    source_success: int
    source_failed: int
    discovered_count: int
    new_count: int
    updated_count: int
    skipped_count: int
    unclassified_count: int
    error_summary: str | None
    source_results: tuple[SourceUpdateResult, ...]
    trigger: RunTrigger = RunTrigger.LEGACY_MANUAL
