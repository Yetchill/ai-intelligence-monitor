# pyright: reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false
"""Stage-seven scheduling tests using controlled clocks and temporary databases."""

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import cast
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient

from app import cli
from app.domain.enums import CrawlStatus, RunTrigger, Weekday
from app.domain.scheduling import SchedulerStatus
from app.domain.update import UpdateResult
from app.services.crawl_run_service import CrawlRunService
from app.services.schedule_settings_service import (
    ScheduleSettingsService,
    ScheduleValidationError,
    next_scheduled_run,
    parse_time,
    parse_weekdays,
)
from app.services.scheduler_service import SchedulerService
from app.services.update_execution_service import (
    UpdateExecutionService,
    UpdateInProgressError,
    UpdateLock,
)
from app.services.update_pipeline import UpdatePipeline
from app.storage.database import Database
from app.storage.repositories import RepositoryUnitOfWork
from app.web.app import create_app
from app.web.dependencies import WebUpdateService


def _service(database: Database) -> ScheduleSettingsService:
    return ScheduleSettingsService(lambda: RepositoryUnitOfWork(database))


def _result(trigger: RunTrigger = RunTrigger.SCHEDULED) -> UpdateResult:
    now = datetime(2026, 7, 20, 1, 0, tzinfo=UTC)
    return UpdateResult(
        crawl_run_id=1,
        status=CrawlStatus.SUCCESS,
        started_at=now,
        finished_at=now,
        source_total=0,
        source_success=0,
        source_failed=0,
        discovered_count=0,
        new_count=0,
        updated_count=0,
        skipped_count=0,
        unclassified_count=0,
        error_summary=None,
        source_results=(),
        trigger=trigger,
    )


def test_default_is_disabled_and_uses_system_iana_timezone(database: Database) -> None:
    settings = _service(database).get()

    assert settings.enabled is False
    assert settings.days == tuple(Weekday)
    assert settings.timezone
    assert ZoneInfo(settings.timezone)
    assert next_scheduled_run(settings, datetime.now(UTC)) is None


def test_settings_enable_disable_and_restart_recovery(database: Database) -> None:
    first = _service(database)
    saved = first.save(
        enabled=True,
        hour=9,
        minute=25,
        days=(Weekday.MON, Weekday.WED, Weekday.FRI),
        timezone="Asia/Shanghai",
    )
    recovered = _service(database).get()

    assert recovered == saved
    assert recovered.days == (Weekday.MON, Weekday.WED, Weekday.FRI)
    disabled = first.save(
        enabled=False,
        hour=recovered.hour,
        minute=recovered.minute,
        days=recovered.days,
        timezone=recovered.timezone,
    )
    assert disabled.enabled is False


@pytest.mark.parametrize("value", ["9:00", "24:00", "09:60", "aa:bb", "09:000"])
def test_invalid_time_is_rejected(value: str) -> None:
    with pytest.raises(ScheduleValidationError):
        parse_time(value)


def test_invalid_days_timezone_and_failed_save_preserve_settings(database: Database) -> None:
    service = _service(database)
    original = service.get()

    with pytest.raises(ScheduleValidationError):
        parse_weekdays(())
    with pytest.raises(ScheduleValidationError):
        service.save(
            enabled=True,
            hour=8,
            minute=0,
            days=(Weekday.MON,),
            timezone="Not/A-Timezone",
        )
    assert service.get() == original


def test_next_run_handles_same_day_midnight_and_week_boundary(database: Database) -> None:
    service = _service(database)
    monday = service.save(
        enabled=True,
        hour=9,
        minute=0,
        days=(Weekday.MON,),
        timezone="UTC",
    )

    assert next_scheduled_run(monday, datetime(2026, 7, 20, 8, 59, tzinfo=UTC)) == datetime(
        2026, 7, 20, 9, 0, tzinfo=UTC
    )
    assert next_scheduled_run(monday, datetime(2026, 7, 20, 9, 0, tzinfo=UTC)) == datetime(
        2026, 7, 27, 9, 0, tzinfo=UTC
    )

    midnight = service.save(
        enabled=True,
        hour=0,
        minute=5,
        days=(Weekday.TUE,),
        timezone="Asia/Shanghai",
    )
    assert next_scheduled_run(midnight, datetime(2026, 7, 20, 16, 4, tzinfo=UTC)) == datetime(
        2026, 7, 20, 16, 5, tzinfo=UTC
    )


def test_dst_nonexistent_time_is_skipped_and_ambiguous_time_uses_later_fold(
    database: Database,
) -> None:
    service = _service(database)
    spring = service.save(
        enabled=True,
        hour=2,
        minute=30,
        days=(Weekday.SUN,),
        timezone="America/New_York",
    )
    assert next_scheduled_run(spring, datetime(2026, 3, 8, 0, 0, tzinfo=UTC)) == datetime(
        2026, 3, 15, 6, 30, tzinfo=UTC
    )

    autumn = service.save(
        enabled=True,
        hour=1,
        minute=30,
        days=(Weekday.SUN,),
        timezone="America/New_York",
    )
    assert next_scheduled_run(autumn, datetime(2026, 11, 1, 0, 0, tzinfo=UTC)) == datetime(
        2026, 11, 1, 6, 30, tzinfo=UTC
    )


class ControlledClock:
    def __init__(self, now: datetime) -> None:
        self.current = now
        self.targets: list[datetime] = []
        self.waiting = asyncio.Event()
        self._fire = asyncio.Event()

    def now(self) -> datetime:
        return self.current

    async def wait_until(self, target: datetime, wake_event: asyncio.Event) -> bool:
        self.targets.append(target)
        self._fire.clear()
        self.waiting.set()
        fire_task = asyncio.create_task(self._fire.wait())
        wake_task = asyncio.create_task(wake_event.wait())
        done, pending = await asyncio.wait(
            (fire_task, wake_task), return_when=asyncio.FIRST_COMPLETED
        )
        for task in pending:
            task.cancel()
        if wake_task in done:
            return True
        self.current = target
        return False

    async def advance_to_target(self) -> datetime:
        await asyncio.wait_for(self.waiting.wait(), timeout=1)
        self.waiting.clear()
        target = self.targets[-1]
        self._fire.set()
        return target


class RecordingRunner:
    def __init__(self, *, fail_first: bool = False) -> None:
        self.calls = 0
        self.fail_first = fail_first
        self.called = asyncio.Event()

    async def try_scheduled_update(self) -> UpdateResult | None:
        self.calls += 1
        self.called.set()
        if self.fail_first and self.calls == 1:
            raise RuntimeError("pipeline failed")
        return _result()


@pytest.mark.asyncio
async def test_scheduler_triggers_without_catchup_or_same_minute_duplicate(
    database: Database,
) -> None:
    service = _service(database)
    service.save(
        enabled=True,
        hour=9,
        minute=0,
        days=(Weekday.MON,),
        timezone="UTC",
    )
    clock = ControlledClock(datetime(2026, 7, 20, 8, 0, tzinfo=UTC))
    runner = RecordingRunner()
    scheduler = SchedulerService(service, runner, clock=clock)

    await scheduler.start()
    first_target = await clock.advance_to_target()
    await asyncio.wait_for(runner.called.wait(), timeout=1)
    runner.called.clear()
    await asyncio.wait_for(clock.waiting.wait(), timeout=1)

    assert first_target == datetime(2026, 7, 20, 9, 0, tzinfo=UTC)
    assert runner.calls == 1
    assert clock.targets[-1] == datetime(2026, 7, 27, 9, 0, tzinfo=UTC)
    assert service.get().last_scheduled_trigger_at == first_target
    await scheduler.stop()


@pytest.mark.asyncio
async def test_scheduler_continues_after_pipeline_error_and_reload_cancels_old_plan(
    database: Database,
) -> None:
    service = _service(database)
    service.save(
        enabled=True,
        hour=9,
        minute=0,
        days=(Weekday.MON, Weekday.TUE),
        timezone="UTC",
    )
    clock = ControlledClock(datetime(2026, 7, 20, 8, 0, tzinfo=UTC))
    runner = RecordingRunner(fail_first=True)
    scheduler = SchedulerService(service, runner, clock=clock)
    await scheduler.start()

    await clock.advance_to_target()
    await asyncio.wait_for(runner.called.wait(), timeout=1)
    runner.called.clear()
    await asyncio.wait_for(clock.waiting.wait(), timeout=1)
    assert runner.calls == 1
    clock.waiting.clear()

    service.save(
        enabled=True,
        hour=10,
        minute=0,
        days=(Weekday.TUE,),
        timezone="UTC",
    )
    await scheduler.reload()
    await asyncio.wait_for(clock.waiting.wait(), timeout=1)
    assert clock.targets[-1] == datetime(2026, 7, 21, 10, 0, tzinfo=UTC)

    service.save(
        enabled=False,
        hour=10,
        minute=0,
        days=(Weekday.TUE,),
        timezone="UTC",
    )
    await scheduler.reload()
    await asyncio.sleep(0)
    assert scheduler.view().status is SchedulerStatus.DISABLED
    await scheduler.stop()


class BlockingPipeline(UpdatePipeline):
    def __init__(self) -> None:
        self.started = asyncio.Event()
        self.release = asyncio.Event()
        self.triggers: list[RunTrigger] = []
        self.fail = False

    async def update(self, **kwargs: object) -> UpdateResult:
        trigger = cast(RunTrigger, kwargs["trigger"])
        self.triggers.append(trigger)
        self.started.set()
        if self.fail:
            self.fail = False
            raise RuntimeError("boom")
        await self.release.wait()
        return _result(trigger)


@pytest.mark.asyncio
async def test_manual_and_scheduled_updates_share_lock_and_release_after_errors(
    database: Database,
) -> None:
    pipeline = BlockingPipeline()

    @asynccontextmanager
    async def context(_database: Database) -> AsyncGenerator[UpdatePipeline]:
        yield pipeline

    lock = UpdateLock()
    manual = WebUpdateService(database, context, lock)
    scheduled = UpdateExecutionService(database, context, lock)
    manual_task = asyncio.create_task(manual.update())
    await pipeline.started.wait()
    assert await scheduled.try_scheduled_update() is None
    pipeline.release.set()
    await manual_task

    pipeline.started.clear()
    pipeline.release.clear()
    scheduled_task = asyncio.create_task(scheduled.try_scheduled_update())
    await pipeline.started.wait()
    with pytest.raises(UpdateInProgressError):
        await manual.update()
    pipeline.release.set()
    await scheduled_task
    assert pipeline.triggers == [RunTrigger.MANUAL_WEB, RunTrigger.SCHEDULED]

    pipeline.started.clear()
    pipeline.release.clear()
    pipeline.fail = True
    with pytest.raises(RuntimeError):
        await manual.update()
    pipeline.release.set()
    assert (await manual.update()).status is CrawlStatus.SUCCESS


def test_scheduled_crawl_run_records_trigger(database: Database) -> None:
    run_id = CrawlRunService(lambda: RepositoryUnitOfWork(database)).start(
        source_total=0, trigger=RunTrigger.SCHEDULED
    )
    with RepositoryUnitOfWork(database) as uow:
        assert uow.crawl_runs.get(run_id).trigger is RunTrigger.SCHEDULED  # type: ignore[union-attr]


@pytest.mark.asyncio
async def test_fastapi_lifespan_starts_and_stops_enabled_scheduler_with_controlled_time(
    database: Database,
) -> None:
    _service(database).save(
        enabled=True,
        hour=9,
        minute=0,
        days=(Weekday.MON,),
        timezone="UTC",
    )
    clock = ControlledClock(datetime(2026, 7, 20, 8, 0, tzinfo=UTC))
    pipeline = BlockingPipeline()
    pipeline.release.set()

    @asynccontextmanager
    async def context(_database: Database) -> AsyncGenerator[UpdatePipeline]:
        yield pipeline

    application = create_app(
        database=database,
        enforce_migrations=False,
        pipeline_context_factory=context,
        scheduler_clock=clock,
    )
    async with application.router.lifespan_context(application):
        await clock.advance_to_target()
        await asyncio.wait_for(pipeline.started.wait(), timeout=1)
        assert pipeline.triggers == [RunTrigger.SCHEDULED]

    assert application.state.services.scheduler.view().status is SchedulerStatus.STOPPED


def test_web_settings_page_save_validation_and_immediate_display(database: Database) -> None:
    application = create_app(database=database, enforce_migrations=False)
    with TestClient(application, raise_server_exceptions=False) as client:
        page = client.get("/settings")
        assert page.status_code == 200
        assert "应用必须保持运行" in page.text
        assert "设置" in client.get("/").text

        invalid = client.post(
            "/settings",
            data={
                "enabled": "true",
                "schedule_time": "09:00",
                "days": "mon",
                "timezone": "Invalid/Zone",
            },
        )
        assert invalid.status_code == 400
        assert application.state.services.schedule_settings.get().enabled is False

        saved = client.post(
            "/settings",
            data={
                "enabled": "true",
                "schedule_time": "09:30",
                "days": ["mon", "fri"],
                "timezone": "Asia/Shanghai",
            },
            follow_redirects=True,
        )
        assert saved.status_code == 200
        assert "设置已保存并立即生效" in saved.text
        assert "Asia/Shanghai" in saved.text
        assert "下一次计划运行" in saved.text


def test_cli_schedule_show_enable_disable_and_invalid_input(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(cli, "configure_logging", lambda: None)

    def fake_from_settings(_cls: type[Database]) -> Database:
        return database

    monkeypatch.setattr(cli.Database, "from_settings", classmethod(fake_from_settings))

    assert cli.main(["schedule", "show"]) == 0
    assert "enabled=false" in capsys.readouterr().out
    assert (
        cli.main(
            [
                "schedule",
                "enable",
                "--time",
                "08:15",
                "--days",
                "mon,tue,wed,thu,fri",
                "--timezone",
                "Asia/Shanghai",
            ]
        )
        == 0
    )
    assert "enabled=true" in capsys.readouterr().out
    assert cli.main(["schedule", "disable"]) == 0
    assert "enabled=false" in capsys.readouterr().out
    assert cli.main(["schedule", "enable", "--time", "25:00", "--days", "mon"]) == 2
    assert "error:" in capsys.readouterr().err
