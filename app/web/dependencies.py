"""Application dependencies and process-local update exclusion."""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from threading import Lock

from app.domain.update import UpdateResult
from app.services.application_factory import update_pipeline_context
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
    updates: WebUpdateService

    @classmethod
    def build(
        cls,
        database: Database,
        *,
        pipeline_context_factory: PipelineContextFactory = update_pipeline_context,
    ) -> "WebServices":
        def uow_factory() -> RepositoryUnitOfWork:
            return RepositoryUnitOfWork(database)

        return cls(
            database=database,
            data=WebDataService(uow_factory),
            updates=WebUpdateService(database, pipeline_context_factory),
        )
