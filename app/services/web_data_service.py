"""Application services for local Web queries and basic manual operations."""

from collections.abc import Callable
from datetime import UTC, datetime

from app.classifiers.manual import ManualCategoryError, ManualClassifier
from app.domain.queries import (
    CrawlRunListEntry,
    ItemListEntry,
    ItemQuery,
    Page,
    SourceListEntry,
    SourceOption,
)
from app.services.error_sanitization import sanitize_error
from app.storage.repositories import RepositoryUnitOfWork
from app.utils.url import is_http_url

UnitOfWorkFactory = Callable[[], RepositoryUnitOfWork]


class EntityNotFoundError(LookupError):
    """Raised when a Web operation targets a missing record."""


class SourceStateError(ValueError):
    """Raised when a source cannot safely enter the requested state."""


class WebDataService:
    """Keep query and mutation transaction boundaries outside Web routes."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory
        self._manual_classifier = ManualClassifier()

    def list_items(self, query: ItemQuery) -> Page[ItemListEntry]:
        with self._uow_factory() as uow:
            rows, total = uow.items.paginate_with_sources(query)
            entries = tuple(
                ItemListEntry(
                    id=item.id,
                    title=item.title,
                    original_url=item.original_url if is_http_url(item.original_url) else None,
                    summary=item.summary,
                    published_at=item.published_at,
                    discovered_at=item.discovered_at,
                    updated_at=item.updated_at,
                    automatic_category=item.category,
                    manual_category=item.manual_category,
                    is_favorite=item.is_favorite,
                    source_id=item.source_id,
                    source_name=source_name,
                )
                for item, source_name in rows
            )
        return Page(entries, query.page, query.per_page, total)

    def source_options(self) -> tuple[SourceOption, ...]:
        with self._uow_factory() as uow:
            options = uow.sources.list_options()
        return tuple(SourceOption(source_id, name) for source_id, name in options)

    def list_sources(self, *, page: int, per_page: int) -> Page[SourceListEntry]:
        with self._uow_factory() as uow:
            sources, total = uow.sources.paginate(page=page, per_page=per_page)
            entries = tuple(
                SourceListEntry(
                    id=source.id,
                    name=source.name,
                    start_url=source.start_url if is_http_url(source.start_url) else None,
                    source_type=source.source_type,
                    collector_name=source.collector_name,
                    enabled=source.enabled,
                    default_category=source.default_category,
                    discovery_status=source.discovery_status,
                    discovery_confidence=source.discovery_confidence,
                    requires_custom_collector=source.requires_custom_collector,
                    last_checked_at=source.last_checked_at,
                    last_success_at=source.last_success_at,
                    last_error=(
                        sanitize_error(source.last_error, limit=240) if source.last_error else None
                    ),
                )
                for source in sources
            )
        return Page(entries, page, per_page, total)

    def list_crawl_runs(self, *, page: int, per_page: int) -> Page[CrawlRunListEntry]:
        with self._uow_factory() as uow:
            runs, total = uow.crawl_runs.paginate(page=page, per_page=per_page)
            entries = tuple(
                CrawlRunListEntry(
                    id=run.id,
                    status=run.status,
                    started_at=run.started_at,
                    finished_at=run.finished_at,
                    source_total=run.source_total,
                    source_success=run.source_success,
                    source_failed=run.source_failed,
                    discovered_count=run.discovered_count,
                    new_count=run.new_count,
                    updated_count=run.updated_count,
                    skipped_count=run.skipped_count,
                    unclassified_count=run.unclassified_count,
                    error_summary=(
                        sanitize_error(run.error_summary, limit=300) if run.error_summary else None
                    ),
                )
                for run in runs
            )
        return Page(entries, page, per_page, total)

    def set_favorite(self, item_id: int, favorite: bool) -> None:
        with self._uow_factory() as uow:
            item = uow.items.get(item_id)
            if item is None:
                raise EntityNotFoundError(f"资讯 {item_id} 不存在")
            item.is_favorite = favorite

    def set_manual_category(self, item_id: int, value: str | None) -> None:
        result = self._manual_classifier.classify(value)
        with self._uow_factory() as uow:
            item = uow.items.get(item_id)
            if item is None:
                raise EntityNotFoundError(f"资讯 {item_id} 不存在")
            item.manual_category = result.category if result is not None else None
            item.updated_at = datetime.now(UTC)

    def set_source_enabled(self, source_id: int, enabled: bool) -> None:
        with self._uow_factory() as uow:
            source = uow.sources.get(source_id)
            if source is None:
                raise EntityNotFoundError(f"来源 {source_id} 不存在")
            if enabled and (
                source.requires_custom_collector
                or source.discovery_status
                in {"needs_configuration", "needs_custom_collector", "blocked", "unreachable"}
            ):
                raise SourceStateError("该来源尚未通过可用预览, 不能启用。")
            source.enabled = enabled


__all__ = [
    "EntityNotFoundError",
    "ManualCategoryError",
    "SourceStateError",
    "WebDataService",
]
