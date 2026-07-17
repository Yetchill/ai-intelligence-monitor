"""Repositories and a unit-of-work transaction boundary."""

from collections.abc import Mapping
from types import TracebackType
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.models import Base, CrawlRun, IntelligenceItem, ItemRevision, Source
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


class CrawlRunRepository(BaseRepository[CrawlRun]):
    model = CrawlRun


class ItemRevisionRepository(BaseRepository[ItemRevision]):
    model = ItemRevision

    def list_by_item(self, item_id: int) -> list[ItemRevision]:
        statement = (
            select(ItemRevision)
            .where(ItemRevision.item_id == item_id)
            .order_by(ItemRevision.changed_at, ItemRevision.id)
        )
        return list(self._session.scalars(statement))


class RepositoryUnitOfWork:
    """Expose repositories while keeping SQLAlchemy sessions out of callers."""

    def __init__(self, database: Database) -> None:
        self._database = database
        self._session: Session | None = None
        self.sources: SourceRepository
        self.items: IntelligenceItemRepository
        self.crawl_runs: CrawlRunRepository
        self.revisions: ItemRevisionRepository

    def __enter__(self) -> "RepositoryUnitOfWork":
        session = self._database.session_factory()
        self._session = session
        self.sources = SourceRepository(session)
        self.items = IntelligenceItemRepository(session)
        self.crawl_runs = CrawlRunRepository(session)
        self.revisions = ItemRevisionRepository(session)
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
