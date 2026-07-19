"""Shared process-local exclusion for manual and scheduled updates."""

from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from threading import Lock

from app.domain.enums import RunTrigger
from app.domain.update import UpdateResult
from app.services.update_pipeline import UpdatePipeline
from app.storage.database import Database

PipelineContextFactory = Callable[[Database], AbstractAsyncContextManager[UpdatePipeline]]


class UpdateInProgressError(RuntimeError):
    """Raised when another update already owns the process-local lock."""


class UpdateLock:
    def __init__(self) -> None:
        self._lock = Lock()

    def acquire(self) -> bool:
        return self._lock.acquire(blocking=False)

    def release(self) -> None:
        self._lock.release()

    @property
    def locked(self) -> bool:
        return self._lock.locked()


class UpdateExecutionService:
    def __init__(
        self,
        database: Database,
        pipeline_context_factory: PipelineContextFactory,
        update_lock: UpdateLock,
    ) -> None:
        self._database = database
        self._pipeline_context_factory = pipeline_context_factory
        self._lock = update_lock

    async def update(
        self,
        *,
        trigger: RunTrigger,
        source_id: int | None = None,
    ) -> UpdateResult:
        return await self._execute(trigger=trigger, source_id=source_id)

    async def _execute(
        self,
        *,
        trigger: RunTrigger,
        source_id: int | None = None,
    ) -> UpdateResult:
        if not self._lock.acquire():
            raise UpdateInProgressError("已有更新正在运行, 请等待完成后再试。")
        try:
            async with self._pipeline_context_factory(self._database) as pipeline:
                return await pipeline.update(source_id=source_id, trigger=trigger)
        finally:
            self._lock.release()

    async def try_scheduled_update(self) -> UpdateResult | None:
        try:
            return await self._execute(trigger=RunTrigger.SCHEDULED)
        except UpdateInProgressError:
            return None
