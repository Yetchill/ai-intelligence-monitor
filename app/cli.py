"""Minimal development CLI for the shared stage-four update pipeline."""

import argparse
import asyncio
from collections.abc import Sequence
from datetime import datetime

from app.classifiers.rule_based import RuleBasedClassifier
from app.collectors.registry import default_collector_registry
from app.domain.enums import CrawlStatus
from app.domain.update import UpdateMode, UpdateResult
from app.fetchers.http import HttpFetcher
from app.services.classification_service import ClassificationService
from app.services.crawl_service import CrawlService
from app.services.update_pipeline import UpdatePipeline
from app.storage.database import Database
from app.storage.repositories import RepositoryUnitOfWork
from app.utils.logging import configure_logging


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    configure_logging()
    database = Database.from_settings()
    try:
        if arguments.command == "runs":
            _print_runs(database, arguments.limit)
            return 0
        return asyncio.run(_run_update(database, arguments))
    finally:
        database.dispose()


async def _run_update(database: Database, arguments: argparse.Namespace) -> int:
    def uow_factory() -> RepositoryUnitOfWork:
        return RepositoryUnitOfWork(database)

    classifier = RuleBasedClassifier.from_yaml()
    classification_service = ClassificationService(classifier, uow_factory)
    async with HttpFetcher() as fetcher:
        pipeline = UpdatePipeline(
            uow_factory=uow_factory,
            crawl_service=CrawlService(default_collector_registry(), fetcher),
            classification_service=classification_service,
        )
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


def _print_result(result: UpdateResult) -> None:
    print(
        f"run={result.crawl_run_id} status={result.status.value} "
        f"sources={result.source_success}/{result.source_total} "
        f"discovered={result.discovered_count} new={result.new_count} "
        f"updated={result.updated_count} skipped={result.skipped_count} "
        f"unclassified={result.unclassified_count}"
    )
    for source in result.source_results:
        suffix = f" error={source.error}" if source.error else ""
        print(
            f"source={source.source_id}:{source.source_name} status={source.status.value} "
            f"discovered={source.discovered} new={source.new} updated={source.updated} "
            f"skipped={source.skipped} unclassified={source.unclassified}{suffix}"
        )


def _print_runs(database: Database, limit: int) -> None:
    with RepositoryUnitOfWork(database) as uow:
        runs = uow.crawl_runs.list_recent(limit)
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
    return parser


if __name__ == "__main__":
    raise SystemExit(main())
