"""Repositories and a unit-of-work transaction boundary."""

from collections.abc import Mapping
from types import TracebackType
from typing import Any

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.domain.enums import SourceAudience, SourceKind, SourceScope
from app.domain.models import (
    Base,
    CrawlRun,
    IntelligenceItem,
    ItemRevision,
    ScheduleSettings,
    Source,
)
from app.domain.queries import ItemFilter, ItemQuery
from app.storage.database import Database


class RepositoryError(ValueError):
    """Raised when a repository operation is invalid."""


class BaseRepository[ModelT: Base]:
    """Small, typed CRUD surface shared by model-specific repositories."""

    model: type[ModelT]

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: ModelT) -> ModelT:
        self._session.add(entity)
        self._session.flush()
        return entity

    def get(self, entity_id: int) -> ModelT | None:
        return self._session.get(self.model, entity_id)

    def list(self) -> list[ModelT]:
        statement = select(self.model).order_by(self.model.id)  # type: ignore[attr-defined]
        return list(self._session.scalars(statement))

    def update(self, entity_id: int, changes: Mapping[str, Any]) -> ModelT | None:
        entity = self.get(entity_id)
        if entity is None:
            return None
        valid_fields = set(self.model.__table__.columns.keys()) - {"id"}
        unknown_fields = set(changes) - valid_fields
        if unknown_fields:
            fields = ", ".join(sorted(unknown_fields))
            raise RepositoryError(f"Unknown or immutable fields: {fields}")
        for field, value in changes.items():
            setattr(entity, field, value)
        self._session.flush()
        return entity

    def delete(self, entity_id: int) -> bool:
        entity = self.get(entity_id)
        if entity is None:
            return False
        self._session.delete(entity)
        self._session.flush()
        return True


class SourceRepository(BaseRepository[Source]):
    model = Source

    def get_by_start_url(self, start_url: str) -> Source | None:
        return self._session.scalar(select(Source).where(Source.start_url == start_url))

    def list_enabled(self) -> list[Source]:
        statement = select(Source).where(Source.enabled.is_(True)).order_by(Source.id)
        return list(self._session.scalars(statement))

    def list_enabled_formal(self) -> list[Source]:
        statement = (
            select(Source)
            .where(Source.enabled.is_(True), Source.source_kind == SourceKind.FORMAL)
            .order_by(Source.id)
        )
        return list(self._session.scalars(statement))

    def list_options(self) -> list[tuple[int, str, SourceKind, bool]]:
        statement = select(Source.id, Source.name, Source.source_kind, Source.enabled).order_by(
            Source.name, Source.id
        )
        return [
            (source_id, name, source_kind, enabled)
            for source_id, name, source_kind, enabled in self._session.execute(statement)
        ]

    def paginate(self, *, page: int, per_page: int) -> tuple[list[Source], int]:
        total = self._session.scalar(select(func.count(Source.id))) or 0
        statement = (
            select(Source)
            .order_by(Source.name, Source.id)
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(self._session.scalars(statement)), total


class IntelligenceItemRepository(BaseRepository[IntelligenceItem]):
    model = IntelligenceItem

    def get_by_canonical_url(self, canonical_url: str) -> IntelligenceItem | None:
        return self._session.scalar(
            select(IntelligenceItem).where(IntelligenceItem.canonical_url == canonical_url)
        )

    def list_by_source(self, source_id: int) -> list[IntelligenceItem]:
        statement = (
            select(IntelligenceItem)
            .where(IntelligenceItem.source_id == source_id)
            .order_by(IntelligenceItem.id)
        )
        return list(self._session.scalars(statement))

    def get_by_source_fingerprint(
        self,
        source_id: int,
        fingerprint: str,
    ) -> IntelligenceItem | None:
        return self._session.scalar(
            select(IntelligenceItem).where(
                IntelligenceItem.source_id == source_id,
                IntelligenceItem.fingerprint == fingerprint,
            )
        )

    def add_or_get_existing(
        self,
        entity: IntelligenceItem,
    ) -> tuple[IntelligenceItem, bool]:
        """Insert under a savepoint and recover a concurrently inserted duplicate."""

        try:
            with self._session.begin_nested():
                self._session.add(entity)
                self._session.flush()
            return entity, True
        except IntegrityError:
            existing = self.get_by_canonical_url(entity.canonical_url)
            if existing is None:
                existing = self.get_by_source_fingerprint(entity.source_id, entity.fingerprint)
            if existing is None:
                raise
            return existing, False

    def paginate_with_sources(
        self, query: ItemQuery
    ) -> tuple[list[tuple[IntelligenceItem, str, SourceKind]], int]:
        total = self.count_filtered(query)
        rows = self.list_filtered_with_sources(
            query,
            limit=query.per_page,
            offset=(query.page - 1) * query.per_page,
        )
        return rows, total

    def count_filtered(self, item_filter: ItemFilter) -> int:
        filters = _item_filters(item_filter)
        total_statement = (
            select(func.count(IntelligenceItem.id))
            .join(Source, IntelligenceItem.source_id == Source.id)
            .where(*filters)
        )
        return self._session.scalar(total_statement) or 0

    def list_filtered_with_sources(
        self,
        item_filter: ItemFilter,
        *,
        limit: int,
        offset: int = 0,
    ) -> list[tuple[IntelligenceItem, str, SourceKind]]:
        filters = _item_filters(item_filter)
        statement = (
            select(IntelligenceItem, Source.name, Source.source_kind)
            .join(Source, IntelligenceItem.source_id == Source.id)
            .where(*filters)
            .order_by(*_item_order())
            .offset(offset)
            .limit(limit)
        )
        return [
            (item, source_name, source_kind)
            for item, source_name, source_kind in self._session.execute(statement)
        ]


class CrawlRunRepository(BaseRepository[CrawlRun]):
    model = CrawlRun

    def list_recent(self, limit: int = 5) -> list[CrawlRun]:
        statement = (
            select(CrawlRun)
            .order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc())
            .limit(max(1, min(limit, 100)))
        )
        return list(self._session.scalars(statement))

    def paginate(self, *, page: int, per_page: int) -> tuple[list[CrawlRun], int]:
        total = self._session.scalar(select(func.count(CrawlRun.id))) or 0
        statement = (
            select(CrawlRun)
            .order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        return list(self._session.scalars(statement)), total


class ItemRevisionRepository(BaseRepository[ItemRevision]):
    model = ItemRevision

    def list_by_item(self, item_id: int) -> list[ItemRevision]:
        statement = (
            select(ItemRevision)
            .where(ItemRevision.item_id == item_id)
            .order_by(ItemRevision.changed_at, ItemRevision.id)
        )
        return list(self._session.scalars(statement))


class ScheduleSettingsRepository(BaseRepository[ScheduleSettings]):
    model = ScheduleSettings

    def get_singleton(self) -> ScheduleSettings | None:
        return self._session.get(ScheduleSettings, 1)

    def add_singleton_if_missing(self, entity: ScheduleSettings) -> ScheduleSettings:
        """Create the singleton without racing another first writer."""

        statement = (
            sqlite_insert(ScheduleSettings)
            .values(
                id=1,
                schedule_enabled=entity.schedule_enabled,
                schedule_hour=entity.schedule_hour,
                schedule_minute=entity.schedule_minute,
                schedule_days_mask=entity.schedule_days_mask,
                timezone=entity.timezone,
                updated_at=entity.updated_at,
                last_scheduled_trigger_at=entity.last_scheduled_trigger_at,
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )
        self._session.execute(statement)
        row = self.get_singleton()
        if row is None:
            raise RuntimeError("could not create schedule settings singleton")
        return row


class RepositoryUnitOfWork:
    """Expose repositories while keeping SQLAlchemy sessions out of callers."""

    def __init__(self, database: Database) -> None:
        self._database = database
        self._session: Session | None = None
        self.sources: SourceRepository
        self.items: IntelligenceItemRepository
        self.crawl_runs: CrawlRunRepository
        self.revisions: ItemRevisionRepository
        self.schedule_settings: ScheduleSettingsRepository

    def __enter__(self) -> "RepositoryUnitOfWork":
        session = self._database.session_factory()
        self._session = session
        self.sources = SourceRepository(session)
        self.items = IntelligenceItemRepository(session)
        self.crawl_runs = CrawlRunRepository(session)
        self.revisions = ItemRevisionRepository(session)
        self.schedule_settings = ScheduleSettingsRepository(session)
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is None:
            return
        try:
            if exception_type is None:
                self._session.commit()
            else:
                self._session.rollback()
        finally:
            self._session.close()
            self._session = None

    def commit(self) -> None:
        """Commit current changes and immediately begin the next transaction."""

        if self._session is None:
            raise RuntimeError("Unit of work is not active")
        self._session.commit()

    def rollback(self) -> None:
        """Roll back current changes."""

        if self._session is None:
            raise RuntimeError("Unit of work is not active")
        self._session.rollback()


def _item_filters(query: ItemFilter) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = [IntelligenceItem.is_active.is_(True)]
    if query.source_scope is SourceScope.LEADERSHIP:
        filters.extend(
            (
                Source.enabled.is_(True),
                Source.source_kind == SourceKind.FORMAL,
                Source.homepage_visible.is_(True),
                Source.audience.in_((SourceAudience.LEADERSHIP, SourceAudience.ALL)),
                IntelligenceItem.admission_accepted.is_(True),
            )
        )
    elif query.source_scope is SourceScope.FORMAL_EXPORT:
        filters.extend(
            (
                Source.enabled.is_(True),
                Source.source_kind == SourceKind.FORMAL,
                Source.export_visible.is_(True),
                IntelligenceItem.admission_accepted.is_(True),
            )
        )
    elif query.source_scope is SourceScope.NON_FORMAL:
        filters.append(Source.source_kind != SourceKind.FORMAL)
    elif query.source_scope is SourceScope.DISABLED:
        filters.append(Source.enabled.is_(False))
    elif query.source_scope is SourceScope.FALLBACK:
        filters.append(Source.source_kind == SourceKind.FALLBACK)
    if query.keyword:
        escaped = _escape_like(query.keyword)
        pattern = f"%{escaped}%"
        filters.append(
            or_(
                IntelligenceItem.title.ilike(pattern, escape="\\"),
                IntelligenceItem.summary.ilike(pattern, escape="\\"),
            )
        )
    if query.category is not None:
        filters.append(
            or_(
                IntelligenceItem.manual_category == query.category,
                and_(
                    IntelligenceItem.manual_category.is_(None),
                    IntelligenceItem.category == query.category,
                ),
            )
        )
    if query.source_id is not None:
        filters.append(IntelligenceItem.source_id == query.source_id)
    if query.favorite is not None:
        filters.append(IntelligenceItem.is_favorite.is_(query.favorite))
    if query.published_from is not None:
        filters.append(IntelligenceItem.published_at >= query.published_from)
    if query.published_to is not None:
        filters.append(IntelligenceItem.published_at < query.published_to)
    if query.discovered_from is not None:
        filters.append(IntelligenceItem.discovered_at >= query.discovered_from)
    if query.discovered_to is not None:
        filters.append(IntelligenceItem.discovered_at < query.discovered_to)
    if query.unclassified is not None:
        is_unclassified = or_(
            IntelligenceItem.manual_category == "unclassified",
            and_(
                IntelligenceItem.manual_category.is_(None),
                IntelligenceItem.category == "unclassified",
            ),
        )
        filters.append(is_unclassified if query.unclassified else ~is_unclassified)
    return filters


def _item_order() -> tuple[ColumnElement[Any], ...]:
    effective_date = func.coalesce(
        IntelligenceItem.published_at,
        IntelligenceItem.discovered_at,
        IntelligenceItem.updated_at,
    )
    return effective_date.desc(), IntelligenceItem.id.desc()


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
