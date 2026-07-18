"""Database initialization and constraint tests."""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from app.domain.enums import Category
from app.domain.models import IntelligenceItem, Source
from app.storage.database import Database
from app.storage.repositories import RepositoryUnitOfWork
from app.web.app import require_current_migration

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_sqlite_foreign_keys_are_enabled_in_modern_transaction_mode(database: Database) -> None:
    with database.engine.connect() as connection:
        assert connection.exec_driver_sql("PRAGMA foreign_keys").scalar() == 1


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


def test_web_startup_migration_check_does_not_upgrade_database(tmp_path: Path) -> None:
    database_path = tmp_path / "behind-head.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    config = Config(PROJECT_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "8df43a9b1c2e")
    database = Database(database_url)
    try:
        with pytest.raises(RuntimeError, match="数据库结构未升级"):
            require_current_migration(database)
        with database.engine.connect() as connection:
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        assert revision == "8df43a9b1c2e"
        assert "updated_at" not in {
            column["name"] for column in inspect(database.engine).get_columns("intelligence_items")
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
                    "('2026-07-17 01:00:00', 'partial', 2, 1, 1, 1, 1, 0, 0, 0), "
                    "('2026-07-17 02:00:00', 'running', 3, 0, 0, 0, 0, 0, 0, 0), "
                    "('2026-07-17 03:00:00', 'failed', 4, 0, 4, 4, 0, 0, 4, 4)"
                )
            )
    finally:
        database.dispose()

    command.upgrade(config, "head")
    migrated = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        with migrated.engine.connect() as connection:
            statuses = list(connection.scalars(text("SELECT status FROM crawl_runs ORDER BY id")))
        assert statuses == ["success", "partial_success", "running", "failed"]
    finally:
        migrated.dispose()

    command.downgrade(config, "db0caa03a995")
    downgraded = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        with downgraded.engine.connect() as connection:
            statuses = list(connection.scalars(text("SELECT status FROM crawl_runs ORDER BY id")))
            source_totals = list(
                connection.scalars(text("SELECT source_total FROM crawl_runs ORDER BY id"))
            )
        assert statuses == ["succeeded", "partial", "running", "failed"]
        assert source_totals == [1, 2, 3, 4]
    finally:
        downgraded.dispose()

    command.upgrade(config, "head")
    repeated = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        with repeated.engine.connect() as connection:
            statuses = list(connection.scalars(text("SELECT status FROM crawl_runs ORDER BY id")))
        assert statuses == ["success", "partial_success", "running", "failed"]
    finally:
        repeated.dispose()


def test_item_updated_at_migration_preserves_existing_rows(tmp_path: Path) -> None:
    database_path = tmp_path / "item-updated-at-migration.db"
    config = Config(PROJECT_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    command.upgrade(config, "8df43a9b1c2e")
    database = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        with database.engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO sources "
                    "(name, source_type, start_url, enabled, collector_name, collector_config, "
                    "requires_custom_collector, origin, created_at, updated_at) VALUES "
                    "('Feed', 'rss', 'https://example.com/feed', 1, 'rss', '{}', 0, "
                    "'preset', '2026-07-18 00:00:00', '2026-07-18 00:00:00')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO intelligence_items "
                    "(source_id, title, original_url, canonical_url, discovered_at, last_seen_at, "
                    "category, fingerprint, is_favorite, is_active, extra) VALUES "
                    "(1, 'Existing item', 'https://example.com/item', 'https://example.com/item', "
                    "'2026-07-18 01:00:00', '2026-07-18 02:00:00', 'unclassified', "
                    f"'{('a' * 64)}', 0, 1, '{{}}')"
                )
            )
            connection.execute(
                text(
                    "INSERT INTO item_revisions "
                    "(item_id, changed_at, old_data, new_data) VALUES "
                    "(1, '2026-07-18 02:00:00', '{\"title\": \"Old\"}', "
                    '\'{"title": "Existing item"}\')'
                )
            )
    finally:
        database.dispose()

    command.upgrade(config, "head")
    migrated = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        with migrated.engine.connect() as connection:
            row = connection.execute(
                text("SELECT title, last_seen_at, updated_at FROM intelligence_items")
            ).one()
            revision = connection.execute(
                text("SELECT item_id, old_data, new_data FROM item_revisions")
            ).one()
            foreign_key_violations = list(connection.execute(text("PRAGMA foreign_key_check")))
        assert row.title == "Existing item"
        assert row.updated_at == row.last_seen_at
        assert revision.item_id == 1
        assert '"Old"' in revision.old_data
        assert foreign_key_violations == []
    finally:
        migrated.dispose()

    command.downgrade(config, "8df43a9b1c2e")
    downgraded = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        inspector = inspect(downgraded.engine)
        assert "updated_at" not in {
            column["name"] for column in inspector.get_columns("intelligence_items")
        }
        with downgraded.engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM intelligence_items")) == 1
            assert connection.scalar(text("SELECT count(*) FROM item_revisions")) == 1
            assert list(connection.execute(text("PRAGMA foreign_key_check"))) == []
    finally:
        downgraded.dispose()

    command.upgrade(config, "head")
    repeated = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        with repeated.engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM intelligence_items")) == 1
            assert connection.scalar(text("SELECT count(*) FROM item_revisions")) == 1
            assert connection.scalar(text("SELECT updated_at FROM intelligence_items")) == (
                "2026-07-18 02:00:00"
            )
            assert list(connection.execute(text("PRAGMA foreign_key_check"))) == []
    finally:
        repeated.dispose()


def test_status_migration_rejects_unknown_history_before_schema_changes(tmp_path: Path) -> None:
    database_path = tmp_path / "unknown-status-migration.db"
    config = Config(PROJECT_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    command.upgrade(config, "db0caa03a995")
    database = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        with database.engine.begin() as connection:
            connection.exec_driver_sql("PRAGMA ignore_check_constraints=ON")
            connection.execute(
                text(
                    "INSERT INTO crawl_runs "
                    "(started_at, status, source_total, source_success, source_failed, "
                    "discovered_count, new_count, updated_count, skipped_count, "
                    "unclassified_count) VALUES "
                    "('2026-07-17 00:00:00', 'mystery', 1, 0, 1, 0, 0, 0, 0, 0)"
                )
            )
            connection.exec_driver_sql("PRAGMA ignore_check_constraints=OFF")
    finally:
        database.dispose()

    with pytest.raises(RuntimeError, match=r"unknown status.*mystery"):
        command.upgrade(config, "head")

    preserved = Database(f"sqlite:///{database_path.as_posix()}")
    try:
        with preserved.engine.connect() as connection:
            status = connection.scalar(text("SELECT status FROM crawl_runs"))
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        assert status == "mystery"
        assert revision == "db0caa03a995"
    finally:
        preserved.dispose()


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
