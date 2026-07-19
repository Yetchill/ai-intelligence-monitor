"""Minimal development CLI for the shared stage-four update pipeline."""

import argparse
import asyncio
import os
import sys
import tempfile
from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

from app.config.settings import PROJECT_ROOT
from app.domain.enums import Category, CrawlStatus, RunTrigger, SourceScope
from app.domain.exports import ExportFormat, ExportQuery
from app.domain.queries import ItemFilter
from app.domain.update import UpdateMode, UpdateResult
from app.services.application_factory import build_export_service, update_pipeline_context
from app.services.error_sanitization import sanitize_error
from app.services.schedule_settings_service import (
    ScheduleSettingsService,
    next_scheduled_run,
    parse_time,
    parse_weekdays,
)
from app.services.scheduler_service import SchedulerService
from app.services.source_seed_service import SourceSeedService
from app.services.update_execution_service import UpdateExecutionService, UpdateLock
from app.services.update_pipeline import UpdatePipeline
from app.storage.database import Database
from app.storage.repositories import RepositoryUnitOfWork
from app.utils.logging import configure_logging


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    database: Database | None = None
    try:
        configure_logging()
        database = Database.from_settings()
        if arguments.command == "runs":
            _print_runs(database, arguments.limit)
            return 0
        if arguments.command == "sources":
            _seed_sources(database)
            return 0
        if arguments.command == "export":
            _run_export(database, arguments)
            return 0
        if arguments.command == "schedule":
            return _run_schedule_command(database, arguments)
        return asyncio.run(_run_update(database, arguments))
    except KeyboardInterrupt:
        print("scheduler stopped")
        return 0
    except Exception as exc:
        print(f"error: {sanitize_error(exc)}", file=sys.stderr)
        return 2
    finally:
        if database is not None:
            database.dispose()


async def _run_update(database: Database, arguments: argparse.Namespace) -> int:
    execution = UpdateExecutionService(
        database,
        lambda target: update_pipeline_context(target, UpdatePipeline),
        UpdateLock(),
    )
    result = await execution.update(
        trigger=RunTrigger.MANUAL_CLI,
        source_id=arguments.source_id,
        allow_disabled=arguments.allow_disabled,
        formal_only=arguments.source_id is None and not arguments.all_enabled,
        mode=UpdateMode(arguments.mode),
        max_pages=arguments.max_pages,
        max_items=arguments.max_items,
        published_from=_parse_datetime(arguments.published_from),
        published_to=_parse_datetime(arguments.published_to),
    )
    _print_result(result)
    return 1 if result.status is CrawlStatus.FAILED else 0


def _seed_sources(database: Database) -> None:
    service = SourceSeedService(lambda: RepositoryUnitOfWork(database))
    result = service.seed()
    print(
        f"formal sources: created={result.created} promoted={result.promoted} "
        f"existing={result.existing} conflicts={result.conflicts} expected={result.expected}"
    )


def _print_result(result: UpdateResult) -> None:
    print(
        f"run={result.crawl_run_id} status={result.status.value} "
        f"sources={result.source_success}/{result.source_total} "
        f"discovered={result.discovered_count} new={result.new_count} "
        f"updated={result.updated_count} skipped={result.skipped_count} "
        f"accepted={result.accepted_count} rejected={result.rejected_count} "
        f"unclassified={result.unclassified_count}"
    )
    if result.source_total == 0:
        print("no enabled sources were selected")
    for source in result.source_results:
        source_name = sanitize_error(source.source_name, limit=255)
        suffix = f" error={sanitize_error(source.error)}" if source.error else ""
        print(
            f"source={source.source_id}:{source_name} status={source.status.value} "
            f"fetched={source.discovered} normalized={source.normalized} "
            f"accepted={source.accepted} rejected={source.rejected} "
            f"classified={source.classified} inserted={source.new} updated={source.updated} "
            f"duplicate={source.duplicate} failed={source.failed} "
            f"rejection_reasons={source.rejection_reason_counts or {}} "
            f"failure_reasons={source.failure_reason_counts or {}}{suffix}"
        )


def _print_runs(database: Database, limit: int) -> None:
    with RepositoryUnitOfWork(database) as uow:
        runs = uow.crawl_runs.list_recent(limit)
    if not runs:
        print("no crawl runs found")
        return
    for run in runs:
        print(
            f"run={run.id} status={run.status.value} trigger={run.trigger.value} "
            f"started={run.started_at.isoformat()} "
            f"finished={run.finished_at.isoformat() if run.finished_at else '-'} "
            f"sources={run.source_success}/{run.source_total} new={run.new_count} "
            f"updated={run.updated_count} skipped={run.skipped_count}"
        )


def _run_schedule_command(database: Database, arguments: argparse.Namespace) -> int:
    service = ScheduleSettingsService(lambda: RepositoryUnitOfWork(database))
    action = arguments.schedule_command
    if action == "show":
        _print_schedule(service)
        return 0
    current = service.get()
    if action == "disable":
        service.save(
            enabled=False,
            hour=current.hour,
            minute=current.minute,
            days=current.days,
            timezone=current.timezone,
        )
        _print_schedule(service)
        return 0
    if action == "enable":
        hour, minute = parse_time(arguments.schedule_time)
        service.save(
            enabled=True,
            hour=hour,
            minute=minute,
            days=parse_weekdays(arguments.days.split(",")),
            timezone=arguments.timezone or current.timezone,
        )
        _print_schedule(service)
        return 0
    if action == "run":
        if not current.enabled:
            raise ValueError(
                "schedule is disabled; enable it before running the foreground scheduler"
            )
        return asyncio.run(_run_foreground_scheduler(database, service))
    raise ValueError(f"unknown schedule command: {action}")


def _print_schedule(service: ScheduleSettingsService) -> None:
    settings = service.get()
    next_run = next_scheduled_run(settings, datetime.now(UTC))
    print(
        f"enabled={'true' if settings.enabled else 'false'} "
        f"time={settings.hour:02d}:{settings.minute:02d} "
        f"days={','.join(day.value for day in settings.days)} timezone={settings.timezone}"
    )
    print(f"next={next_run.isoformat() if next_run else '-'}")
    last_trigger = (
        settings.last_scheduled_trigger_at.isoformat()
        if settings.last_scheduled_trigger_at
        else "-"
    )
    print(f"last_scheduled_trigger={last_trigger}")


async def _run_foreground_scheduler(database: Database, settings: ScheduleSettingsService) -> int:
    updates = UpdateExecutionService(database, update_pipeline_context, UpdateLock())
    scheduler = SchedulerService(settings, updates)
    await scheduler.start()
    print("foreground scheduler running; press Ctrl+C to stop")
    try:
        await asyncio.Event().wait()
    finally:
        await scheduler.stop()
    return 0


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO datetime: {value}") from exc


def _run_export(database: Database, arguments: argparse.Namespace) -> None:
    published_from = _parse_export_date(arguments.published_from)
    published_to = _parse_export_date(arguments.published_to, exclusive_end=True)
    discovered_from = _parse_export_date(arguments.discovered_from)
    discovered_to = _parse_export_date(arguments.discovered_to, exclusive_end=True)
    if published_from and published_to and published_from >= published_to:
        raise ValueError("published-from must not be later than published-to")
    if discovered_from and discovered_to and discovered_from >= discovered_to:
        raise ValueError("discovered-from must not be later than discovered-to")

    export_format = ExportFormat(arguments.export_format)
    result = build_export_service(database).export(
        export_format,
        ExportQuery(
            filters=ItemFilter(
                keyword=arguments.query,
                category=Category(arguments.category) if arguments.category else None,
                source_id=arguments.source_id,
                favorite=arguments.favorite,
                published_from=published_from,
                published_to=published_to,
                discovered_from=discovered_from,
                discovered_to=discovered_to,
                unclassified=arguments.unclassified,
                source_scope=SourceScope.FORMAL_EXPORT,
            ),
            limit=arguments.limit,
        ),
    )
    output = arguments.output or (PROJECT_ROOT / "output" / result.filename)
    expected_suffix = ".xlsx" if export_format is ExportFormat.EXCEL else ".docx"
    if output.suffix.lower() != expected_suffix:
        raise ValueError(f"output path must end with {expected_suffix}")
    _atomic_write(output, result.content, force=arguments.force)
    print(f"exported {result.item_count} items to {output}")


def _parse_export_date(value: str | None, *, exclusive_end: bool = False) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = date.fromisoformat(value)
        if exclusive_end:
            parsed += timedelta(days=1)
    except (ValueError, OverflowError) as exc:
        raise ValueError(f"invalid export date: {value}; expected YYYY-MM-DD") from exc
    return datetime.combine(parsed, time.min, UTC)


def _atomic_write(path: Path, content: bytes, *, force: bool) -> None:
    path = path.expanduser()
    _validate_output_target(path, force=force)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
        _validate_output_target(path, force=force)
        if force:
            os.replace(temporary_path, path)
            temporary_path = None
        else:
            os.link(temporary_path, path)
            temporary_path.unlink()
            temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _validate_output_target(path: Path, *, force: bool) -> None:
    if path.is_symlink():
        raise ValueError("output path must not be a symbolic link")
    if path.exists() and path.is_dir():
        raise ValueError("output path must be a file, not a directory")
    if path.exists() and not force:
        raise FileExistsError(17, "File exists", path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI intelligence update pipeline debug CLI")
    commands = parser.add_subparsers(dest="command", required=True)
    update = commands.add_parser("update", help="update enabled sources")
    update.add_argument("--source-id", type=int)
    update.add_argument("--allow-disabled", action="store_true")
    update.add_argument(
        "--all-enabled",
        action="store_true",
        help="include enabled test/fallback sources; bulk updates select formal sources by default",
    )
    update.add_argument(
        "--mode",
        choices=[mode.value for mode in UpdateMode],
        default="incremental",
    )
    update.add_argument("--max-pages", type=int)
    update.add_argument("--max-items", type=int)
    update.add_argument("--from", dest="published_from")
    update.add_argument("--to", dest="published_to")
    runs = commands.add_parser("runs", help="show recent crawl run summaries")
    runs.add_argument("--limit", type=int, default=5)
    sources = commands.add_parser("sources", help="manage preset source configuration")
    source_commands = sources.add_subparsers(dest="source_command", required=True)
    source_commands.add_parser("seed-formal", help="idempotently initialize formal sources")
    source_commands.add_parser("seed", help=argparse.SUPPRESS)
    export = commands.add_parser("export", help="export filtered intelligence")
    export_formats = export.add_subparsers(dest="export_format", required=True)
    for export_format in ExportFormat:
        command = export_formats.add_parser(export_format.value)
        command.add_argument("--output", type=Path)
        command.add_argument("--category", choices=[category.value for category in Category])
        command.add_argument("--source-id", type=_positive_int)
        command.add_argument("--favorite", action="store_const", const=True, default=None)
        command.add_argument("--published-from")
        command.add_argument("--published-to")
        command.add_argument("--discovered-from")
        command.add_argument("--discovered-to")
        command.add_argument("--query")
        command.add_argument("--unclassified", action="store_const", const=True, default=None)
        command.add_argument("--limit", type=_positive_int)
        command.add_argument("--force", action="store_true")
    schedule = commands.add_parser("schedule", help="view or manage runtime scheduling")
    schedule_commands = schedule.add_subparsers(dest="schedule_command", required=True)
    schedule_commands.add_parser("show", help="show current schedule settings")
    enable = schedule_commands.add_parser("enable", help="enable and configure scheduling")
    enable.add_argument("--time", dest="schedule_time", required=True, metavar="HH:MM")
    enable.add_argument("--days", required=True, help="comma-separated mon,tue,...,sun")
    enable.add_argument("--timezone", help="IANA timezone; preserves current value when omitted")
    schedule_commands.add_parser("disable", help="disable scheduling")
    schedule_commands.add_parser("run", help="run the scheduler in the foreground")
    return parser


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be a positive integer")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
