"""Idempotent item persistence, content revision, and cross-source discovery handling."""

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, cast

from app.domain.classification import ClassificationResult
from app.domain.collection import CollectedItem
from app.domain.enums import Category
from app.domain.models import IntelligenceItem, ItemRevision
from app.services.item_normalization import INTERNAL_DISCOVERIES_KEY
from app.storage.repositories import RepositoryUnitOfWork
from app.utils.fingerprint import generate_item_fingerprint

UnitOfWorkFactory = Callable[[], RepositoryUnitOfWork]


@dataclass(frozen=True, slots=True)
class ClassifiedItem:
    item: CollectedItem
    classification: ClassificationResult


@dataclass(frozen=True, slots=True)
class SourcePersistenceStats:
    new: int
    updated: int
    skipped: int
    unclassified: int


class ItemPersistenceService:
    """Persist one source inside one short transaction owned by this application service."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def persist_source(
        self,
        *,
        source_id: int,
        source_name: str,
        crawl_run_id: int,
        items: Sequence[ClassifiedItem],
        invalid_skipped: int = 0,
        checked_at: datetime | None = None,
    ) -> SourcePersistenceStats:
        now = _utc(checked_at or datetime.now(UTC))
        new_count = 0
        updated_count = 0
        skipped_count = invalid_skipped
        unclassified_count = 0
        processed_item_ids: set[int] = set()

        with self._uow_factory() as uow:
            source = uow.sources.get(source_id)
            if source is None:
                raise LookupError(f"source {source_id} no longer exists")

            for classified in items:
                normalized = classified.item
                fingerprint = generate_item_fingerprint(normalized.title)
                existing = uow.items.get_by_canonical_url(normalized.canonical_url)
                if existing is None:
                    existing = uow.items.get_by_source_fingerprint(source_id, fingerprint)

                if existing is None:
                    candidate = IntelligenceItem(
                        source_id=source_id,
                        title=normalized.title,
                        original_url=normalized.original_url,
                        canonical_url=normalized.canonical_url,
                        summary=normalized.summary,
                        published_at=normalized.published_at,
                        discovered_at=now,
                        last_seen_at=now,
                        category=classified.classification.category,
                        classification_score=classified.classification.score,
                        classification_reason=classified.classification.reason,
                        automatic_category_provider=classified.classification.provider,
                        manual_category=None,
                        fingerprint=fingerprint,
                        extra=dict(normalized.extra),
                    )
                    existing, inserted = uow.items.add_or_get_existing(candidate)
                    if existing.id in processed_item_ids:
                        continue
                    if inserted:
                        new_count += 1
                    else:
                        outcome = self._update_existing(
                            uow,
                            existing,
                            source_id=source_id,
                            source_name=source_name,
                            crawl_run_id=crawl_run_id,
                            classified=classified,
                            now=now,
                        )
                        updated_count += outcome == "updated"
                        skipped_count += outcome == "skipped"
                else:
                    if existing.id in processed_item_ids:
                        continue
                    outcome = self._update_existing(
                        uow,
                        existing,
                        source_id=source_id,
                        source_name=source_name,
                        crawl_run_id=crawl_run_id,
                        classified=classified,
                        now=now,
                    )
                    updated_count += outcome == "updated"
                    skipped_count += outcome == "skipped"

                processed_item_ids.add(existing.id)
                effective_category = existing.manual_category or existing.category
                unclassified_count += effective_category is Category.UNCLASSIFIED

            source.last_checked_at = now
            source.last_success_at = now
            source.last_error = None

        return SourcePersistenceStats(
            new=new_count,
            updated=updated_count,
            skipped=skipped_count,
            unclassified=unclassified_count,
        )

    def _update_existing(
        self,
        uow: RepositoryUnitOfWork,
        existing: IntelligenceItem,
        *,
        source_id: int,
        source_name: str,
        crawl_run_id: int,
        classified: ClassifiedItem,
        now: datetime,
    ) -> str:
        existing.last_seen_at = now
        if existing.source_id != source_id:
            existing.extra = _record_additional_source(
                existing.extra,
                source_id=source_id,
                source_name=source_name,
                seen_at=now,
            )
            return "skipped"

        changes = _content_changes(existing, classified.item)
        if changes:
            old_data = {field: values[0] for field, values in changes.items()}
            new_data = {field: values[1] for field, values in changes.items()}
            uow.revisions.add(
                ItemRevision(
                    item_id=existing.id,
                    crawl_run_id=crawl_run_id,
                    changed_at=now,
                    old_data=old_data,
                    new_data=new_data,
                )
            )
            _apply_content(existing, classified.item, changes)

        _apply_classification(existing, classified.classification)
        return "updated" if changes else "skipped"


def _content_changes(
    existing: IntelligenceItem,
    incoming: CollectedItem,
) -> dict[str, tuple[object, object]]:
    changes: dict[str, tuple[object, object]] = {}
    for field, old, new in (
        ("title", existing.title, incoming.title),
        ("summary", existing.summary, incoming.summary),
        (
            "published_at",
            _json_datetime(existing.published_at),
            _json_datetime(incoming.published_at),
        ),
        ("extra", _business_extra(existing.extra), dict(incoming.extra)),
    ):
        if old != new:
            changes[field] = (old, new)
    return changes


def _apply_content(
    existing: IntelligenceItem,
    incoming: CollectedItem,
    changes: dict[str, tuple[object, object]],
) -> None:
    if "title" in changes:
        existing.title = incoming.title
    if "summary" in changes:
        existing.summary = incoming.summary
    if "published_at" in changes:
        existing.published_at = incoming.published_at
    if "extra" in changes:
        discoveries = _extra_mapping(existing.extra).get(INTERNAL_DISCOVERIES_KEY)
        extra = dict(incoming.extra)
        if discoveries is not None:
            extra[INTERNAL_DISCOVERIES_KEY] = discoveries
        existing.extra = extra


def _apply_classification(
    existing: IntelligenceItem,
    result: ClassificationResult,
) -> None:
    existing.category = result.category
    existing.classification_score = result.score
    existing.classification_reason = result.reason
    existing.automatic_category_provider = result.provider


def _business_extra(extra: object) -> dict[str, object]:
    return {
        key: cast(object, value)
        for key, value in _extra_mapping(extra).items()
        if key != INTERNAL_DISCOVERIES_KEY
    }


def _record_additional_source(
    extra: object,
    *,
    source_id: int,
    source_name: str,
    seen_at: datetime,
) -> dict[str, Any]:
    updated = _extra_mapping(extra)
    raw_discoveries = updated.get(INTERNAL_DISCOVERIES_KEY)
    discoveries_by_source: dict[int, dict[str, object]] = {}
    if isinstance(raw_discoveries, list):
        for value in cast(list[object], raw_discoveries):
            if not isinstance(value, Mapping):
                continue
            mapping = cast(Mapping[object, object], value)
            discovery_source_id = mapping.get("source_id")
            if not isinstance(discovery_source_id, int) or isinstance(discovery_source_id, bool):
                continue
            first_seen = mapping.get("first_seen_at")
            last_seen = mapping.get("last_seen_at")
            name = mapping.get("source_name")
            if not isinstance(first_seen, str) or not isinstance(last_seen, str):
                continue
            previous = discoveries_by_source.get(discovery_source_id)
            if previous is None:
                discoveries_by_source[discovery_source_id] = {
                    "source_id": discovery_source_id,
                    "source_name": name if isinstance(name, str) else "",
                    "first_seen_at": first_seen,
                    "last_seen_at": last_seen,
                }
            else:
                previous["first_seen_at"] = min(cast(str, previous["first_seen_at"]), first_seen)
                previous["last_seen_at"] = max(cast(str, previous["last_seen_at"]), last_seen)
    seen_at_text = seen_at.isoformat()
    discovery = discoveries_by_source.get(source_id)
    if discovery is None:
        discoveries_by_source[source_id] = {
            "source_id": source_id,
            "source_name": source_name,
            "first_seen_at": seen_at_text,
            "last_seen_at": seen_at_text,
        }
    else:
        discovery["source_name"] = source_name
        discovery["last_seen_at"] = seen_at_text
    updated[INTERNAL_DISCOVERIES_KEY] = [
        discoveries_by_source[key] for key in sorted(discoveries_by_source)
    ]
    return updated


def _extra_mapping(extra: object) -> dict[str, Any]:
    if not isinstance(extra, Mapping):
        return {}
    mapping = cast(Mapping[object, object], extra)
    return {key: value for key, value in mapping.items() if isinstance(key, str)}


def _json_datetime(value: datetime | None) -> str | None:
    return _utc(value).isoformat() if value is not None else None


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
