"""Shared update pipeline used by CLI and future UI or scheduling adapters."""

import asyncio
import logging
import traceback
from collections.abc import Callable
from datetime import UTC, datetime
from typing import cast

from app.domain.classification import ClassificationResult
from app.domain.collection import CollectedItem
from app.domain.enums import Category, RunTrigger
from app.domain.models import Source
from app.domain.update import (
    SourceUpdateResult,
    SourceUpdateStatus,
    UpdateMode,
    UpdateResult,
)
from app.services.classification_service import ClassificationService
from app.services.crawl_run_service import CrawlRunService
from app.services.crawl_service import CrawlService
from app.services.error_sanitization import sanitize_error
from app.services.item_normalization import ItemNormalizationError, normalize_collected_item
from app.services.item_persistence_service import ClassifiedItem, ItemPersistenceService
from app.storage.repositories import RepositoryUnitOfWork

LOGGER = logging.getLogger("app.crawler.pipeline")
UnitOfWorkFactory = Callable[[], RepositoryUnitOfWork]


class SourceNotFoundError(LookupError):
    """Raised when a requested source id does not exist."""


class SourceDisabledError(ValueError):
    """Raised when a disabled source is explicitly requested without permission."""


class UpdatePipeline:
    """Coordinate source selection, collection, normalization, classification, and persistence."""

    def __init__(
        self,
        *,
        uow_factory: UnitOfWorkFactory,
        crawl_service: CrawlService,
        classification_service: ClassificationService,
        persistence_service: ItemPersistenceService | None = None,
        crawl_run_service: CrawlRunService | None = None,
    ) -> None:
        self._uow_factory = uow_factory
        self._crawl_service = crawl_service
        self._classification_service = classification_service
        self._persistence_service = persistence_service or ItemPersistenceService(uow_factory)
        self._crawl_run_service = crawl_run_service or CrawlRunService(uow_factory)

    async def update(
        self,
        *,
        source_id: int | None = None,
        allow_disabled: bool = False,
        mode: UpdateMode = UpdateMode.INCREMENTAL,
        max_pages: int | None = None,
        max_items: int | None = None,
        published_from: datetime | None = None,
        published_to: datetime | None = None,
        trigger: RunTrigger = RunTrigger.MANUAL_CLI,
    ) -> UpdateResult:
        sources = self._select_sources(source_id=source_id, allow_disabled=allow_disabled)
        crawl_run_id = self._crawl_run_service.start(source_total=len(sources), trigger=trigger)
        source_results: list[SourceUpdateResult] = []
        try:
            for source in sources:
                result = await self._update_source(
                    source,
                    crawl_run_id=crawl_run_id,
                    mode=mode,
                    max_pages=max_pages,
                    max_items=max_items,
                    published_from=published_from,
                    published_to=published_to,
                )
                source_results.append(result)
            return self._crawl_run_service.finish(crawl_run_id, source_results)
        except asyncio.CancelledError as exc:
            _log_exception("Update pipeline cancelled", exc)
            try:
                self._crawl_run_service.finish(
                    crawl_run_id,
                    source_results,
                    fatal_error="update cancelled during application shutdown",
                )
            except Exception as finish_error:
                _log_exception(
                    "Failed to move cancelled CrawlRun out of running state", finish_error
                )
            raise
        except Exception as exc:
            _log_exception("Uncaught update pipeline failure", exc)
            try:
                self._crawl_run_service.finish(
                    crawl_run_id,
                    source_results,
                    fatal_error=exc,
                )
            except Exception as finish_error:
                _log_exception("Failed to move CrawlRun out of running state", finish_error)
            raise

    def _select_sources(self, *, source_id: int | None, allow_disabled: bool) -> list[Source]:
        with self._uow_factory() as uow:
            if source_id is None:
                return uow.sources.list() if allow_disabled else uow.sources.list_enabled()
            source = uow.sources.get(source_id)
            if source is None:
                raise SourceNotFoundError(f"source {source_id} does not exist")
            if not source.enabled and not allow_disabled:
                raise SourceDisabledError(
                    f"source {source_id} is disabled; pass allow_disabled=True to update it"
                )
            return [source]

    async def _update_source(
        self,
        source: Source,
        *,
        crawl_run_id: int,
        mode: UpdateMode,
        max_pages: int | None,
        max_items: int | None,
        published_from: datetime | None,
        published_to: datetime | None,
    ) -> SourceUpdateResult:
        discovered = 0
        invalid_skipped = 0
        try:
            collected = await self._crawl_service.collect(
                source,
                mode=mode,
                max_pages=max_pages,
                max_items=max_items,
                published_from=published_from,
                published_to=published_to,
            )
            discovered = len(collected)
            normalized_items: list[CollectedItem] = []
            keep_query_params = _keep_query_params(source)
            for item in collected:
                try:
                    normalized_items.append(
                        normalize_collected_item(item, keep_query_params=keep_query_params)
                    )
                except ItemNormalizationError as exc:
                    invalid_skipped += 1
                    LOGGER.warning(
                        "Skipped invalid item from source_id=%s: %s",
                        source.id,
                        sanitize_error(exc),
                    )

            if collected and not normalized_items:
                error = "all collected records failed normalization"
                self._mark_source_failed(source.id, error)
                return SourceUpdateResult(
                    source_id=source.id,
                    source_name=source.name,
                    status=SourceUpdateStatus.FAILED,
                    discovered=discovered,
                    skipped=invalid_skipped,
                    error=error,
                )

            classified_items: list[ClassifiedItem] = []
            for item in normalized_items:
                try:
                    classification = await self._classification_service.classify(
                        item,
                        source_default=source.default_category,
                    )
                except Exception as exc:
                    _log_exception(
                        f"Classification failed for source_id={source.id}; using unclassified",
                        exc,
                    )
                    classification = ClassificationResult(
                        category=Category.UNCLASSIFIED,
                        score=0.0,
                        reason=f"classification failed: {sanitize_error(exc)}",
                        provider="classification_error",
                    )
                classified_items.append(ClassifiedItem(item, classification))

            stats = self._persistence_service.persist_source(
                source_id=source.id,
                source_name=source.name,
                crawl_run_id=crawl_run_id,
                items=classified_items,
                invalid_skipped=invalid_skipped,
                checked_at=datetime.now(UTC),
            )
            return SourceUpdateResult(
                source_id=source.id,
                source_name=source.name,
                status=SourceUpdateStatus.SUCCESS,
                discovered=discovered,
                new=stats.new,
                updated=stats.updated,
                skipped=stats.skipped,
                unclassified=stats.unclassified,
            )
        except Exception as exc:
            safe_error = sanitize_error(exc)
            _log_exception(f"Source update failed for source_id={source.id}", exc)
            self._mark_source_failed(source.id, safe_error)
            return SourceUpdateResult(
                source_id=source.id,
                source_name=source.name,
                status=SourceUpdateStatus.FAILED,
                discovered=discovered,
                skipped=invalid_skipped,
                error=safe_error,
            )

    def _mark_source_failed(self, source_id: int, error: str) -> None:
        try:
            with self._uow_factory() as uow:
                source = uow.sources.get(source_id)
                if source is None:
                    raise LookupError(f"source {source_id} no longer exists")
                source.last_checked_at = datetime.now(UTC)
                source.last_error = sanitize_error(error)
        except Exception as state_error:
            _log_exception(
                f"Failed to persist failure state for source_id={source_id}",
                state_error,
            )


def _log_exception(context: str, error: BaseException) -> None:
    stack = " | ".join(
        f"{frame.filename}:{frame.lineno} in {frame.name}"
        for frame in traceback.extract_tb(error.__traceback__)
    )
    LOGGER.error("%s: %s; traceback=%s", context, sanitize_error(error), stack or "unavailable")


def _keep_query_params(source: Source) -> tuple[str, ...] | None:
    value = source.collector_config.get("keep_query_params")
    if not isinstance(value, list):
        return None
    values = cast(list[object], value)
    return tuple(item for item in values if isinstance(item, str))
