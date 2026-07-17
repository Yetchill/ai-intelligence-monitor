"""Database initialization and constraint tests."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.domain.enums import Category
from app.domain.models import IntelligenceItem, Source
from app.storage.database import Database
from app.storage.repositories import RepositoryUnitOfWork

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_alembic_initializes_database(tmp_path: Path) -> None:
    database_path = tmp_path / "migrated.db"
    config = Config(PROJECT_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")

    command.upgrade(config, "head")

    database = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        inspector = inspect(database.engine)
        assert set(inspector.get_table_names()) == {
            "alembic_version",
            "crawl_runs",
            "intelligence_items",
            "item_revisions",
            "sources",
        }
    finally:
        database.dispose()


def test_canonical_url_is_unique(database: Database, source: Source) -> None:
    with RepositoryUnitOfWork(database) as repositories:
        repositories.sources.add(source)
        repositories.items.add(
            IntelligenceItem(
                source_id=source.id,
                title="First title",
                original_url="https://example.com/articles/1?utm_source=test",
                canonical_url="https://example.com/articles/1",
                category=Category.UNCLASSIFIED,
                fingerprint="a" * 64,
            )
        )

    try:
        with RepositoryUnitOfWork(database) as repositories:
            repositories.items.add(
                IntelligenceItem(
                    source_id=source.id,
                    title="Duplicate URL",
                    original_url="https://example.com/articles/1",
                    canonical_url="https://example.com/articles/1",
                    category=Category.UNCLASSIFIED,
                    fingerprint="b" * 64,
                )
            )
    except IntegrityError:
        pass
    else:
        raise AssertionError("Duplicate canonical URL should violate the database constraint")


def test_source_fingerprint_pair_is_unique(database: Database, source: Source) -> None:
    with RepositoryUnitOfWork(database) as repositories:
        repositories.sources.add(source)
        repositories.items.add(
            IntelligenceItem(
                source_id=source.id,
                title="First title",
                original_url="https://example.com/one",
                canonical_url="https://example.com/one",
                fingerprint="same-fingerprint",
            )
        )

    try:
        with RepositoryUnitOfWork(database) as repositories:
            repositories.items.add(
                IntelligenceItem(
                    source_id=source.id,
                    title="Same content at another URL",
                    original_url="https://example.com/two",
                    canonical_url="https://example.com/two",
                    fingerprint="same-fingerprint",
                )
            )
    except IntegrityError:
        pass
    else:
        raise AssertionError("Duplicate source/fingerprint should violate the database constraint")
