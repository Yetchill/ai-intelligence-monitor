"""Application dependencies and process-local update exclusion."""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from threading import Lock

from app.classifiers.rule_based import RuleBasedClassifier
from app.collectors.registry import default_collector_registry
from app.domain.collection import Fetcher
from app.domain.update import UpdateResult
from app.services.application_factory import build_export_service, update_pipeline_context
from app.services.export_service import ExportService
from app.services.source_discovery import (
    DiscoveryTokenStore,
    SourceDiscoveryService,
    SourcePreviewService,
)
from app.services.source_management import SourceManagementService, SourceOnboardingService
from app.services.source_url_security import SafeHttpFetcher, SourceUrlGuard
from app.services.update_pipeline import UpdatePipeline
from app.services.web_data_service import WebDataService
from app.storage.database import Database
from app.storage.repositories import RepositoryUnitOfWork

PipelineContextFactory = Callable[[Database], AbstractAsyncContextManager[UpdatePipeline]]


class UpdateInProgressError(RuntimeError):
    """Raised when a second update is requested in the same process."""


class WebUpdateService:
    def __init__(
        self,
        database: Database,
        pipeline_context_factory: PipelineContextFactory = update_pipeline_context,
    ) -> None:
        self._database = database
        self._pipeline_context_factory = pipeline_context_factory
        self._lock = Lock()

    async def update(self, *, source_id: int | None = None) -> UpdateResult:
        if not self._lock.acquire(blocking=False):
            raise UpdateInProgressError("已有更新正在运行, 请等待完成后再试。")
        try:
            async with self._pipeline_context_factory(self._database) as pipeline:
                return await pipeline.update(source_id=source_id)
        finally:
            self._lock.release()


@dataclass(slots=True)
class WebServices:
    database: Database
    data: WebDataService
    exports: ExportService
    updates: WebUpdateService
    onboarding: SourceOnboardingService
    sources: SourceManagementService
    token_store: DiscoveryTokenStore
    _owned_source_fetcher: SafeHttpFetcher | None = None

    @classmethod
    def build(
        cls,
        database: Database,
        *,
        pipeline_context_factory: PipelineContextFactory = update_pipeline_context,
        source_fetcher: Fetcher | None = None,
        source_url_guard: SourceUrlGuard | None = None,
        token_store: DiscoveryTokenStore | None = None,
    ) -> "WebServices":
        def uow_factory() -> RepositoryUnitOfWork:
            return RepositoryUnitOfWork(database)

        guard = source_url_guard or SourceUrlGuard()
        owned_fetcher = SafeHttpFetcher(guard) if source_fetcher is None else None
        fetcher: Fetcher = source_fetcher or owned_fetcher  # type: ignore[assignment]
        store = token_store or DiscoveryTokenStore()
        discovery = SourceDiscoveryService(fetcher, guard)
        preview = SourcePreviewService(
            default_collector_registry(), fetcher, RuleBasedClassifier.from_yaml()
        )
        return cls(
            database=database,
            data=WebDataService(uow_factory),
            exports=build_export_service(database),
            updates=WebUpdateService(database, pipeline_context_factory),
            onboarding=SourceOnboardingService(discovery, preview, store),
            sources=SourceManagementService(uow_factory, store),
            token_store=store,
            _owned_source_fetcher=owned_fetcher,
        )

    async def aclose(self) -> None:
        if self._owned_source_fetcher is not None:
            await self._owned_source_fetcher.aclose()
