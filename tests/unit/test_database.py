"""Database initialization and constraint tests."""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
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


def test_status_migration_preserves_existing_crawl_runs(tmp_path: Path) -> None:
    database_path = tmp_path / "status-migration.db"
    config = Config(PROJECT_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    command.upgrade(config, "db0caa03a995")
    database = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        with database.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO crawl_runs "
                    "(started_at, status, source_total, source_success, source_failed, "
                    "discovered_count, new_count, updated_count, skipped_count, "
                    "unclassified_count) VALUES "
                    "('2026-07-17 00:00:00', 'succeeded', 1, 1, 0, 1, 1, 0, 0, 0), "
                    "('2026-07-17 01:00:00', 'partial', 2, 1, 1, 1, 1, 0, 0, 0)"
                )
            )
    finally:
        database.dispose()

    command.upgrade(config, "head")
    migrated = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        with migrated.engine.connect() as connection:
            statuses = list(connection.scalars(text("SELECT status FROM crawl_runs ORDER BY id")))
        assert statuses == ["success", "partial_success"]
    finally:
        migrated.dispose()


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
