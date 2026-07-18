"""Minimal development CLI for the shared stage-four update pipeline."""

import argparse
import asyncio
import sys
from collections.abc import Sequence
from datetime import datetime

from app.domain.enums import CrawlStatus
from app.domain.update import UpdateMode, UpdateResult
from app.services.application_factory import update_pipeline_context
from app.services.error_sanitization import sanitize_error
from app.services.source_seed_service import SourceSeedService
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
        return asyncio.run(_run_update(database, arguments))
    except Exception as exc:
        print(f"error: {sanitize_error(exc)}", file=sys.stderr)
        return 2
    finally:
        if database is not None:
            database.dispose()


async def _run_update(database: Database, arguments: argparse.Namespace) -> int:
    async with update_pipeline_context(database, UpdatePipeline) as pipeline:
        result = await pipeline.update(
            source_id=arguments.source_id,
            allow_disabled=arguments.allow_disabled,
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
    created, existing = service.seed()
    print(f"preset sources: created={created} existing={existing}")


def _print_result(result: UpdateResult) -> None:
    print(
        f"run={result.crawl_run_id} status={result.status.value} "
        f"sources={result.source_success}/{result.source_total} "
        f"discovered={result.discovered_count} new={result.new_count} "
        f"updated={result.updated_count} skipped={result.skipped_count} "
        f"unclassified={result.unclassified_count}"
    )
    if result.source_total == 0:
        print("no enabled sources were selected")
    for source in result.source_results:
        source_name = sanitize_error(source.source_name, limit=255)
        suffix = f" error={sanitize_error(source.error)}" if source.error else ""
        print(
            f"source={source.source_id}:{source_name} status={source.status.value} "
            f"discovered={source.discovered} new={source.new} updated={source.updated} "
            f"skipped={source.skipped} unclassified={source.unclassified}{suffix}"
        )


def _print_runs(database: Database, limit: int) -> None:
    with RepositoryUnitOfWork(database) as uow:
        runs = uow.crawl_runs.list_recent(limit)
    if not runs:
        print("no crawl runs found")
        return
    for run in runs:
        print(
            f"run={run.id} status={run.status.value} started={run.started_at.isoformat()} "
            f"finished={run.finished_at.isoformat() if run.finished_at else '-'} "
            f"sources={run.source_success}/{run.source_total} new={run.new_count} "
            f"updated={run.updated_count} skipped={run.skipped_count}"
        )


def _parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"invalid ISO datetime: {value}") from exc


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI intelligence update pipeline debug CLI")
    commands = parser.add_subparsers(dest="command", required=True)
    update = commands.add_parser("update", help="update enabled sources")
    update.add_argument("--source-id", type=int)
    update.add_argument("--allow-disabled", action="store_true")
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
    source_commands.add_parser("seed", help="idempotently import documented example sources")
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
