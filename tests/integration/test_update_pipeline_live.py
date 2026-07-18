"""Opt-in real-network smoke test for the complete stage-four pipeline."""

from pathlib import Path

import pytest

from app.classifiers.rule_based import RuleBasedClassifier
from app.collectors.registry import default_collector_registry
from app.domain.enums import CrawlStatus, SourceOrigin, SourceType
from app.domain.models import Source
from app.fetchers.http import HttpFetcher
from app.services.classification_service import ClassificationService
from app.services.crawl_service import CrawlService
from app.services.update_pipeline import UpdatePipeline
from app.storage.database import Database
from app.storage.repositories import RepositoryUnitOfWork

pytestmark = pytest.mark.network


@pytest.mark.asyncio
async def test_three_public_sources_complete_pipeline_in_temporary_database(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "live-pipeline.db"
    database = Database(f"sqlite:///{database_path.as_posix()}")
    database.create_schema()

    sources = [
        Source(
            name="Google Blog RSS",
            source_type=SourceType.RSS,
            start_url="https://blog.google/rss/",
            collector_name="rss",
            collector_config={"max_items": 10},
            origin=SourceOrigin.PRESET,
        ),
        Source(
            name="AIIA",
            source_type=SourceType.HTML_LIST,
            start_url="https://www.aiiaorg.cn/",
            collector_name="html_list",
            collector_config={
                "allowed_domains": ["www.aiiaorg.cn", "mp.weixin.qq.com"],
                "discovery": {
                    "mode": "selectors",
                    "max_pages": 1,
                    "max_depth": 0,
                    "max_items": 10,
                },
                "extraction": {
                    "item_selector": ".news-scroll-area div.cursor-pointer",
                    "title_selector": "h3",
                    "date_selector": "span",
                    "embedded_title_key": "title",
                    "embedded_link_key": "external_url",
                },
            },
            origin=SourceOrigin.PRESET,
        ),
        Source(
            name="Qwen-Agent Releases",
            source_type=SourceType.GITHUB_RELEASE,
            start_url="https://github.com/QwenLM/Qwen-Agent/releases",
            collector_name="github_release",
            collector_config={"max_releases": 10, "include_prereleases": False},
            origin=SourceOrigin.PRESET,
        ),
    ]
    try:
        with RepositoryUnitOfWork(database) as uow:
            for source in sources:
                uow.sources.add(source)

        def uow_factory() -> RepositoryUnitOfWork:
            return RepositoryUnitOfWork(database)

        classification = ClassificationService(RuleBasedClassifier.from_yaml(), uow_factory)
        async with HttpFetcher(timeout_seconds=30, request_interval_seconds=0) as fetcher:
            pipeline = UpdatePipeline(
                uow_factory=uow_factory,
                crawl_service=CrawlService(default_collector_registry(), fetcher),
                classification_service=classification,
            )
            first = await pipeline.update()
            with RepositoryUnitOfWork(database) as uow:
                first_items = uow.items.list()
            second = await pipeline.update()
            with RepositoryUnitOfWork(database) as uow:
                second_items = uow.items.list()
                runs = uow.crawl_runs.list()

        assert first.status is not CrawlStatus.RUNNING
        assert first.source_success >= 1
        assert first_items
        assert all(item.title and item.canonical_url and item.source_id for item in first_items)
        assert all(item.category is not None for item in first_items)
        assert len(second_items) == len(first_items)
        assert second.new_count == 0
        assert len(runs) == 2
        assert all(
            run.finished_at is not None and run.status is not CrawlStatus.RUNNING for run in runs
        )
        assert database_path != Path("data/intelligence.db")
    finally:
        database.dispose()
