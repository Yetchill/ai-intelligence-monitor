"""Stage-four update pipeline behavior with no public-network dependency."""

from collections.abc import Mapping
from datetime import UTC, datetime
from typing import cast

import pytest

from app.classifiers.rule_based import RuleBasedClassifier
from app.collectors.registry import CollectorRegistry
from app.domain.collection import CollectContext, CollectedItem, Fetcher, FetchResult
from app.domain.enums import Category, CrawlStatus, SourceOrigin, SourceType
from app.domain.models import IntelligenceItem, Source
from app.domain.update import SourceUpdateStatus, UpdateMode
from app.services.classification_service import ClassificationService
from app.services.crawl_run_service import CrawlRunService
from app.services.crawl_service import CrawlService
from app.services.item_persistence_service import ItemPersistenceService
from app.services.update_pipeline import SourceDisabledError, SourceNotFoundError, UpdatePipeline
from app.storage.database import Database
from app.storage.repositories import RepositoryUnitOfWork
from app.utils.fingerprint import generate_item_fingerprint


class ScenarioFetcher:
    """Collector test backend carried through the registry's Fetcher slot."""

    def __init__(self) -> None:
        self.responses: dict[str, list[list[CollectedItem] | Exception]] = {}
        self.contexts: list[CollectContext] = []
        self.active_uow_count = 0

    async def fetch(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> FetchResult:
        del url, headers
        raise AssertionError("ScenarioCollector does not perform transport fetches")


class ScenarioCollector:
    name = "scenario"

    def __init__(self, fetcher: Fetcher) -> None:
        self.backend = cast(ScenarioFetcher, fetcher)

    async def collect(self, context: CollectContext) -> list[CollectedItem]:
        assert self.backend.active_uow_count == 0, "network collection held a database UoW"
        self.backend.contexts.append(context)
        response = self.backend.responses[context.source_url].pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class TrackingUnitOfWork(RepositoryUnitOfWork):
    def __init__(self, database: Database, tracker: ScenarioFetcher) -> None:
        super().__init__(database)
        self._tracker = tracker

    def __enter__(self) -> "TrackingUnitOfWork":
        self._tracker.active_uow_count += 1
        try:
            super().__enter__()
        except Exception:
            self._tracker.active_uow_count -= 1
            raise
        return self

    def __exit__(self, *args: object) -> None:
        try:
            super().__exit__(*args)  # pyright: ignore[reportArgumentType]
        finally:
            self._tracker.active_uow_count -= 1


def _source(name: str, url: str, *, enabled: bool = True) -> Source:
    return Source(
        name=name,
        source_type=SourceType.CUSTOM,
        start_url=url,
        enabled=enabled,
        collector_name="scenario",
        collector_config={},
        origin=SourceOrigin.PRESET,
    )


def _item(
    url: str,
    *,
    title: str = "关于开展优秀人工智能案例征集的通知",
    summary: str | None = "欢迎企业提交材料",
    published_at: datetime | None = None,
    extra: Mapping[str, object] | None = None,
) -> CollectedItem:
    return CollectedItem(
        title=title,
        original_url=url,
        canonical_url=url,
        summary=summary,
        published_at=published_at,
        extra=extra or {},
    )


def _pipeline(
    database: Database,
    backend: ScenarioFetcher,
    *,
    crawl_run_service: CrawlRunService | None = None,
) -> UpdatePipeline:
    def uow_factory() -> RepositoryUnitOfWork:
        return TrackingUnitOfWork(database, backend)

    registry = CollectorRegistry()
    registry.register("scenario", ScenarioCollector)
    classification = ClassificationService(RuleBasedClassifier.from_yaml(), uow_factory)
    return UpdatePipeline(
        uow_factory=uow_factory,
        crawl_service=CrawlService(registry, backend),
        classification_service=classification,
        persistence_service=ItemPersistenceService(uow_factory),
        crawl_run_service=crawl_run_service,
    )


def _add_sources(database: Database, *sources: Source) -> None:
    with RepositoryUnitOfWork(database) as uow:
        for source in sources:
            uow.sources.add(source)


@pytest.mark.asyncio
async def test_first_run_persists_classification_and_second_run_is_skipped(
    database: Database,
) -> None:
    source = _source("Feed", "https://example.com/feed")
    source.last_error = "previous transient failure"
    _add_sources(database, source)
    collected = _item("https://example.com/article/1?utm_source=test")
    backend = ScenarioFetcher()
    backend.responses[source.start_url] = [[collected], [collected]]
    pipeline = _pipeline(database, backend)

    first = await pipeline.update()
    second = await pipeline.update()

    assert first.status is CrawlStatus.SUCCESS
    assert (first.discovered_count, first.new_count, first.updated_count) == (1, 1, 0)
    assert (second.new_count, second.updated_count, second.skipped_count) == (0, 0, 1)
    with RepositoryUnitOfWork(database) as uow:
        items = uow.items.list()
        revisions = uow.revisions.list()
        stored_source = uow.sources.get(source.id)
    assert len(items) == 1
    assert items[0].canonical_url == "https://example.com/article/1"
    assert items[0].category is Category.SOLICITATION
    assert items[0].classification_score is not None
    assert items[0].classification_reason
    assert items[0].automatic_category_provider == "rule_based"
    assert revisions == []
    assert stored_source is not None
    assert stored_source.last_checked_at is not None
    assert stored_source.last_success_at is not None
    assert stored_source.last_error is None


@pytest.mark.asyncio
async def test_content_change_creates_revision_with_only_changed_fields(
    database: Database,
) -> None:
    source = _source("Feed", "https://example.com/feed")
    _add_sources(database, source)
    published = datetime(2026, 7, 1, tzinfo=UTC)
    backend = ScenarioFetcher()
    backend.responses[source.start_url] = [
        [_item("https://example.com/1", published_at=published, extra={"attachment": "a.pdf"})],
        [
            _item(
                "https://example.com/1",
                summary="更新后的申报材料说明",
                published_at=datetime(2026, 7, 2),
                extra={"attachment": "b.pdf"},
            )
        ],
    ]
    pipeline = _pipeline(database, backend)

    await pipeline.update()
    result = await pipeline.update()

    assert result.updated_count == 1
    with RepositoryUnitOfWork(database) as uow:
        revisions = uow.revisions.list()
    assert len(revisions) == 1
    assert set(revisions[0].old_data) == {"summary", "published_at", "extra"}
    assert set(revisions[0].new_data) == {"summary", "published_at", "extra"}
    assert revisions[0].old_data["extra"] == {"attachment": "a.pdf"}
    assert revisions[0].new_data["extra"] == {"attachment": "b.pdf"}


@pytest.mark.asyncio
async def test_last_seen_only_change_does_not_create_revision(database: Database) -> None:
    source = _source("Feed", "https://example.com/feed")
    _add_sources(database, source)
    collected = _item("https://example.com/1")
    backend = ScenarioFetcher()
    backend.responses[source.start_url] = [[collected], [collected]]
    pipeline = _pipeline(database, backend)

    await pipeline.update()
    with RepositoryUnitOfWork(database) as uow:
        before = uow.items.list()[0].last_seen_at
    result = await pipeline.update()
    with RepositoryUnitOfWork(database) as uow:
        after = uow.items.list()[0].last_seen_at
        revisions = uow.revisions.list()

    assert result.skipped_count == 1
    assert after >= before
    assert revisions == []


@pytest.mark.asyncio
async def test_manual_category_is_preserved_while_automatic_fields_refresh(
    database: Database,
) -> None:
    source = _source("Feed", "https://example.com/feed")
    _add_sources(database, source)
    backend = ScenarioFetcher()
    backend.responses[source.start_url] = [
        [_item("https://example.com/1")],
        [_item("https://example.com/1", title="Qwen Agent 产品版本正式发布")],
    ]
    pipeline = _pipeline(database, backend)
    await pipeline.update()
    with RepositoryUnitOfWork(database) as uow:
        item = uow.items.list()[0]
        item.manual_category = Category.AWARD_CASE

    await pipeline.update()

    with RepositoryUnitOfWork(database) as uow:
        item = uow.items.list()[0]
    assert item.manual_category is Category.AWARD_CASE
    assert item.category is Category.AGENT_PRODUCT
    assert (item.manual_category or item.category) is Category.AWARD_CASE


@pytest.mark.asyncio
async def test_unclassified_count_is_aggregated(database: Database) -> None:
    source = _source("Feed", "https://example.com/feed")
    _add_sources(database, source)
    backend = ScenarioFetcher()
    backend.responses[source.start_url] = [
        [_item("https://example.com/1", title="Weekly notes", summary=None)]
    ]

    result = await _pipeline(database, backend).update()

    assert result.unclassified_count == 1
    with RepositoryUnitOfWork(database) as uow:
        assert uow.items.list()[0].category is Category.UNCLASSIFIED


@pytest.mark.asyncio
async def test_source_failure_is_isolated_and_produces_partial_success(database: Database) -> None:
    failing = _source("Failing", "https://example.com/fail")
    working = _source("Working", "https://example.com/work")
    _add_sources(database, failing, working)
    backend = ScenarioFetcher()
    backend.responses[failing.start_url] = [
        RuntimeError("<html>huge body</html> token=super-secret https://x.test/a?token=secret")
    ]
    backend.responses[working.start_url] = [[_item("https://example.com/ok")]]

    result = await _pipeline(database, backend).update()

    assert result.status is CrawlStatus.PARTIAL_SUCCESS
    assert (result.source_success, result.source_failed, result.new_count) == (1, 1, 1)
    assert [entry.status for entry in result.source_results] == [
        SourceUpdateStatus.FAILED,
        SourceUpdateStatus.SUCCESS,
    ]
    failed_error = result.source_results[0].error or ""
    assert "super-secret" not in failed_error
    assert "<html>" not in failed_error
    assert "?token=" not in failed_error
    with RepositoryUnitOfWork(database) as uow:
        failed_source = uow.sources.get(failing.id)
        working_source = uow.sources.get(working.id)
    assert failed_source is not None and failed_source.last_checked_at is not None
    assert failed_source.last_success_at is None
    assert failed_source.last_error == failed_error
    assert working_source is not None and working_source.last_success_at is not None


@pytest.mark.asyncio
async def test_all_sources_failed_marks_run_failed_and_finished(database: Database) -> None:
    first = _source("First", "https://example.com/1")
    second = _source("Second", "https://example.com/2")
    _add_sources(database, first, second)
    backend = ScenarioFetcher()
    backend.responses[first.start_url] = [RuntimeError("first failed")]
    backend.responses[second.start_url] = [RuntimeError("second failed")]

    result = await _pipeline(database, backend).update()

    assert result.status is CrawlStatus.FAILED
    assert (result.source_success, result.source_failed) == (0, 2)
    assert result.finished_at is not None
    with RepositoryUnitOfWork(database) as uow:
        runs = uow.crawl_runs.list()
    assert len(runs) == 1
    assert runs[0].status is CrawlStatus.FAILED
    assert runs[0].finished_at is not None


@pytest.mark.asyncio
async def test_disabled_sources_are_skipped_by_default_and_can_be_explicitly_run(
    database: Database,
) -> None:
    enabled = _source("Enabled", "https://example.com/enabled")
    disabled = _source("Disabled", "https://example.com/disabled", enabled=False)
    _add_sources(database, enabled, disabled)
    backend = ScenarioFetcher()
    backend.responses[enabled.start_url] = [[]]
    backend.responses[disabled.start_url] = [[]]
    pipeline = _pipeline(database, backend)

    default_result = await pipeline.update()
    assert default_result.source_total == 1
    assert [context.source_url for context in backend.contexts] == [enabled.start_url]
    with pytest.raises(SourceDisabledError, match="allow_disabled=True"):
        await pipeline.update(source_id=disabled.id)
    explicit_result = await pipeline.update(source_id=disabled.id, allow_disabled=True)
    assert explicit_result.source_total == 1
    assert backend.contexts[-1].source_url == disabled.start_url


@pytest.mark.asyncio
async def test_source_id_selection_and_missing_source_error(database: Database) -> None:
    first = _source("First", "https://example.com/1")
    second = _source("Second", "https://example.com/2")
    _add_sources(database, first, second)
    backend = ScenarioFetcher()
    backend.responses[second.start_url] = [[]]
    pipeline = _pipeline(database, backend)

    result = await pipeline.update(source_id=second.id)

    assert result.source_total == 1
    assert result.source_results[0].source_id == second.id
    with pytest.raises(SourceNotFoundError, match="999999"):
        await pipeline.update(source_id=999_999)


@pytest.mark.asyncio
async def test_invalid_items_are_isolated_but_all_invalid_fails_source(database: Database) -> None:
    source = _source("Feed", "https://example.com/feed")
    _add_sources(database, source)
    invalid_title = _item("https://example.com/empty", title="   ")
    invalid_url = _item("javascript:alert(1)")
    invalid_extra = _item("https://example.com/bad-extra", extra={"value": object()})
    valid = _item("https://example.com/valid")
    backend = ScenarioFetcher()
    backend.responses[source.start_url] = [
        [invalid_title, invalid_url, invalid_extra, valid],
        [invalid_title, invalid_url],
    ]
    pipeline = _pipeline(database, backend)

    first = await pipeline.update()
    second = await pipeline.update()

    assert first.status is CrawlStatus.SUCCESS
    assert (first.discovered_count, first.new_count, first.skipped_count) == (4, 1, 3)
    assert second.status is CrawlStatus.FAILED
    assert (second.discovered_count, second.skipped_count) == (2, 2)
    with RepositoryUnitOfWork(database) as uow:
        assert len(uow.items.list()) == 1


@pytest.mark.asyncio
async def test_cross_source_url_keeps_first_item_and_records_discovery(database: Database) -> None:
    first = _source("First", "https://example.com/feed-1")
    second = _source("Second", "https://example.com/feed-2")
    _add_sources(database, first, second)
    shared_url = "https://shared.example.com/article"
    backend = ScenarioFetcher()
    backend.responses[first.start_url] = [[_item(shared_url)]]
    backend.responses[second.start_url] = [
        [_item(shared_url, title="Qwen Agent 产品版本正式发布", extra={"other": True})]
    ]
    pipeline = _pipeline(database, backend)
    await pipeline.update(source_id=first.id)
    with RepositoryUnitOfWork(database) as uow:
        stored = uow.items.list()[0]
        stored.manual_category = Category.ENTERPRISE_CASE
        stored.is_favorite = True

    result = await pipeline.update(source_id=second.id)

    assert (result.new_count, result.updated_count, result.skipped_count) == (0, 0, 1)
    with RepositoryUnitOfWork(database) as uow:
        items = uow.items.list()
        revisions = uow.revisions.list()
    assert len(items) == 1
    stored = items[0]
    assert stored.source_id == first.id
    assert stored.title == "关于开展优秀人工智能案例征集的通知"
    assert stored.category is Category.SOLICITATION
    assert stored.manual_category is Category.ENTERPRISE_CASE
    assert stored.is_favorite is True
    discoveries = stored.extra["_source_discoveries"]
    assert isinstance(discoveries, list)
    assert discoveries[0]["source_id"] == second.id
    assert revisions == []


@pytest.mark.asyncio
async def test_same_source_fingerprint_deduplicates_a_changed_url(database: Database) -> None:
    source = _source("Feed", "https://example.com/feed")
    _add_sources(database, source)
    backend = ScenarioFetcher()
    backend.responses[source.start_url] = [
        [_item("https://example.com/old-url")],
        [_item("https://example.com/new-url")],
    ]
    pipeline = _pipeline(database, backend)

    await pipeline.update()
    result = await pipeline.update()

    assert (result.new_count, result.updated_count, result.skipped_count) == (0, 0, 1)
    with RepositoryUnitOfWork(database) as uow:
        items = uow.items.list()
    assert len(items) == 1
    assert items[0].canonical_url == "https://example.com/old-url"


@pytest.mark.asyncio
async def test_history_mode_options_reach_collector_config(database: Database) -> None:
    source = _source("Feed", "https://example.com/feed")
    _add_sources(database, source)
    backend = ScenarioFetcher()
    backend.responses[source.start_url] = [[]]

    await _pipeline(database, backend).update(
        mode=UpdateMode.HISTORY,
        max_pages=999,
        max_items=999_999,
        published_from=datetime(2025, 1, 1),
        published_to=datetime(2026, 1, 1, tzinfo=UTC),
    )

    config = backend.contexts[0].config
    assert config["update_mode"] == "history"
    assert config["max_items"] == 999_999
    assert config["published_from"] == "2025-01-01T00:00:00+00:00"
    discovery = config["discovery"]
    assert isinstance(discovery, dict)
    assert discovery["max_pages"] == 999
    assert discovery["max_items"] == 999_999


class FailFirstFinishService(CrawlRunService):
    def __init__(self, database: Database) -> None:
        super().__init__(lambda: RepositoryUnitOfWork(database))
        self.failed_once = False

    def finish(self, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        if not self.failed_once:
            self.failed_once = True
            raise RuntimeError("unexpected finalization failure")
        return super().finish(*args, **kwargs)  # pyright: ignore[reportArgumentType]


@pytest.mark.asyncio
async def test_uncaught_exception_still_moves_run_out_of_running(database: Database) -> None:
    source = _source("Feed", "https://example.com/feed")
    _add_sources(database, source)
    backend = ScenarioFetcher()
    backend.responses[source.start_url] = [[]]
    service = FailFirstFinishService(database)

    with pytest.raises(RuntimeError, match="unexpected finalization"):
        await _pipeline(database, backend, crawl_run_service=service).update()

    with RepositoryUnitOfWork(database) as uow:
        run = uow.crawl_runs.list()[0]
    assert run.status is CrawlStatus.FAILED
    assert run.finished_at is not None


def test_unique_constraint_conflict_recovers_inside_savepoint(database: Database) -> None:
    source = _source("Feed", "https://example.com/feed")
    _add_sources(database, source)
    with RepositoryUnitOfWork(database) as uow:
        existing = uow.items.add(
            IntelligenceItem(
                source_id=source.id,
                title="Existing",
                original_url="https://example.com/item",
                canonical_url="https://example.com/item",
                fingerprint="a" * 64,
            )
        )

    with RepositoryUnitOfWork(database) as uow:
        recovered, inserted = uow.items.add_or_get_existing(
            IntelligenceItem(
                source_id=source.id,
                title="Racing duplicate",
                original_url="https://example.com/item",
                canonical_url="https://example.com/item",
                fingerprint="b" * 64,
            )
        )
        source_in_same_transaction = uow.sources.get(source.id)
        assert source_in_same_transaction is not None
        source_in_same_transaction.last_error = "transaction remains usable"

    assert inserted is False
    assert recovered.id == existing.id
    with RepositoryUnitOfWork(database) as uow:
        assert len(uow.items.list()) == 1
        assert uow.sources.get(source.id).last_error == "transaction remains usable"  # type: ignore[union-attr]


def test_application_services_do_not_expose_sqlalchemy_session(database: Database) -> None:
    backend = ScenarioFetcher()
    pipeline = _pipeline(database, backend)
    persistence = ItemPersistenceService(lambda: RepositoryUnitOfWork(database))

    assert not hasattr(pipeline, "session")
    assert not hasattr(persistence, "session")
    with RepositoryUnitOfWork(database) as uow:
        assert not hasattr(uow, "session")


def test_fingerprint_is_stable_for_equivalent_titles_and_source_scoped() -> None:
    first = generate_item_fingerprint("  Qwen\tAgent Ｖ2.0  ")  # noqa: RUF001
    second = generate_item_fingerprint("qwen agent V2.0")

    assert first == second
    assert len(first) == 64
    assert generate_item_fingerprint("Qwen Agent V2.1") != first


@pytest.mark.asyncio
async def test_reclassify_item_and_all_are_independent_service_interfaces(
    database: Database,
) -> None:
    source = _source("Feed", "https://example.com/feed")
    _add_sources(database, source)
    with RepositoryUnitOfWork(database) as uow:
        item = uow.items.add(
            IntelligenceItem(
                source_id=source.id,
                title="人工智能行业标准正式发布",
                original_url="https://example.com/item",
                canonical_url="https://example.com/item",
                category=Category.UNCLASSIFIED,
                fingerprint="f" * 64,
            )
        )
    service = ClassificationService(
        RuleBasedClassifier.from_yaml(),
        lambda: RepositoryUnitOfWork(database),
    )

    result = await service.reclassify_item(item.id)
    count = await service.reclassify_all(source_id=source.id)

    assert result.category is Category.POLICY_INDUSTRY
    assert count == 1
    with RepositoryUnitOfWork(database) as uow:
        stored = uow.items.get(item.id)
    assert stored is not None
    assert stored.category is Category.POLICY_INDUSTRY
    assert stored.classification_reason
