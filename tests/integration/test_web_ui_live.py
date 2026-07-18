"""Opt-in real-network smoke test for the local Web workflow."""

# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from app.services.application_factory import update_pipeline_context
from app.services.source_seed_service import SourceSeedService
from app.storage.database import Database
from app.storage.repositories import RepositoryUnitOfWork
from app.web.app import create_app

pytestmark = pytest.mark.network
PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.asyncio
async def test_seed_update_and_web_actions_use_temporary_database(tmp_path: Path) -> None:
    database_path = tmp_path / "stage-five-live.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    config = Config(PROJECT_ROOT / "alembic.ini")
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")
    database = Database(database_url)
    try:
        seed = SourceSeedService(lambda: RepositoryUnitOfWork(database))
        assert seed.seed() == (3, 0)

        async with update_pipeline_context(database) as pipeline:
            first = await pipeline.update()
        with RepositoryUnitOfWork(database) as uow:
            items = uow.items.list()
        assert first.source_success >= 1
        assert items

        application = create_app(database=database, enforce_migrations=True)
        with TestClient(application) as client:
            home = client.get("/")
            assert home.status_code == 200
            assert items[0].title in home.text
            assert client.get("/", params={"source_id": items[0].source_id}).status_code == 200
            client.post(
                f"/items/{items[0].id}/favorite",
                data={"favorite": "true"},
            )
            client.post(
                f"/items/{items[0].id}/category",
                data={"category": "enterprise_case"},
            )

        async with update_pipeline_context(database) as pipeline:
            second = await pipeline.update()
        with RepositoryUnitOfWork(database) as uow:
            stored = uow.items.get(items[0].id)
            final_items = uow.items.list()
        assert stored is not None
        assert stored.is_favorite is True
        assert stored.manual_category is not None
        assert len(final_items) == len(items)
        assert second.new_count == 0
        assert database_path.resolve() != (PROJECT_ROOT / "data" / "intelligence.db").resolve()
    finally:
        database.dispose()
