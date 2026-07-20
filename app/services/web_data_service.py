"""Application services for local Web queries and basic manual operations."""

from collections.abc import Callable
from datetime import UTC, datetime

from app.classifiers.manual import ManualCategoryError, ManualClassifier
from app.domain.enums import (
    IndustryTag,
    LifecycleState,
    PrimaryType,
    ReviewStatus,
    SourceKind,
    TopicTag,
    VerificationStatus,
)
from app.domain.models import ItemReviewEvent
from app.domain.queries import (
    CrawlRunListEntry,
    ItemListEntry,
    ItemQuery,
    Page,
    SourceListEntry,
    SourceOption,
)
from app.services.error_sanitization import sanitize_error
from app.storage.repositories import RepositoryUnitOfWork
from app.utils.url import is_http_url

UnitOfWorkFactory = Callable[[], RepositoryUnitOfWork]


class EntityNotFoundError(LookupError):
    """Raised when a Web operation targets a missing record."""


class SourceStateError(ValueError):
    """Raised when a source cannot safely enter the requested state."""


class WebDataService:
    """Keep query and mutation transaction boundaries outside Web routes."""

    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory
        self._manual_classifier = ManualClassifier()

    def list_items(self, query: ItemQuery) -> Page[ItemListEntry]:
        with self._uow_factory() as uow:
            rows, total = uow.items.paginate_with_sources(query)
            entries = tuple(
                ItemListEntry(
                    id=item.id,
                    title=item.title,
                    original_url=item.original_url if is_http_url(item.original_url) else None,
                    summary=item.summary,
                    published_at=item.published_at,
                    discovered_at=item.discovered_at,
                    updated_at=item.updated_at,
                    automatic_category=item.category,
                    manual_category=item.manual_category,
                    is_favorite=item.is_favorite,
                    source_id=item.source_id,
                    source_name=source_name,
                    source_kind=source_kind,
                    primary_type=item.primary_type,
                    manual_primary_type=item.manual_primary_type,
                    topic_tags=tuple(item.manual_topic_tags or item.topic_tags),
                    industry_tags=tuple(item.manual_industry_tags or item.industry_tags),
                    verification_status=item.verification_status,
                    review_status=item.review_status,
                    case_completeness=item.case_completeness,
                    discovery_url=(
                        item.discovery_url if is_http_url(item.discovery_url or "") else None
                    ),
                    official_url=(
                        item.official_url if is_http_url(item.official_url or "") else None
                    ),
                )
                for item, source_name, source_kind, _source_role in rows
            )
        return Page(entries, query.page, query.per_page, total)

    def source_options(self) -> tuple[SourceOption, ...]:
        with self._uow_factory() as uow:
            options = uow.sources.list_options()
        return tuple(
            SourceOption(source_id, name, source_kind, enabled, lifecycle_state)
            for source_id, name, source_kind, enabled, lifecycle_state in options
        )

    def list_sources(
        self, *, page: int, per_page: int, catalog_filter: str = "all"
    ) -> Page[SourceListEntry]:
        with self._uow_factory() as uow:
            sources, total = uow.sources.paginate(
                page=page, per_page=per_page, catalog_filter=catalog_filter
            )
            entries = tuple(
                SourceListEntry(
                    id=source.id,
                    name=source.name,
                    start_url=source.start_url if is_http_url(source.start_url) else None,
                    source_type=source.source_type,
                    collector_name=source.collector_name,
                    enabled=source.enabled,
                    default_category=source.default_category,
                    discovery_status=source.discovery_status,
                    discovery_confidence=source.discovery_confidence,
                    requires_custom_collector=source.requires_custom_collector,
                    last_checked_at=source.last_checked_at,
                    last_success_at=source.last_success_at,
                    last_error=(
                        sanitize_error(source.last_error, limit=240) if source.last_error else None
                    ),
                    source_kind=source.source_kind,
                    source_tier=source.source_tier.value,
                    audience=source.audience.value,
                    homepage_visible=source.homepage_visible,
                    export_visible=source.export_visible,
                    slug=source.slug,
                    lifecycle_state=source.lifecycle_state,
                    source_role=source.source_role,
                    crawl_mode=source.crawl_mode,
                    review_policy=source.review_policy,
                    implementation_status=source.implementation_status,
                    implementation_reason=source.implementation_reason,
                    last_preview_at=source.last_preview_at,
                    preview_item_count=source.preview_item_count,
                    allowed_primary_types=tuple(source.allowed_primary_types),
                )
                for source in sources
            )
        return Page(entries, page, per_page, total)

    def formal_source_count(self) -> int:
        with self._uow_factory() as uow:
            return sum(source.source_kind is SourceKind.FORMAL for source in uow.sources.list())

    def list_crawl_runs(self, *, page: int, per_page: int) -> Page[CrawlRunListEntry]:
        with self._uow_factory() as uow:
            runs, total = uow.crawl_runs.paginate(page=page, per_page=per_page)
            entries = tuple(
                CrawlRunListEntry(
                    id=run.id,
                    status=run.status,
                    trigger=run.trigger,
                    started_at=run.started_at,
                    finished_at=run.finished_at,
                    source_total=run.source_total,
                    source_success=run.source_success,
                    source_failed=run.source_failed,
                    discovered_count=run.discovered_count,
                    new_count=run.new_count,
                    updated_count=run.updated_count,
                    skipped_count=run.skipped_count,
                    unclassified_count=run.unclassified_count,
                    error_summary=(
                        sanitize_error(run.error_summary, limit=300) if run.error_summary else None
                    ),
                    normalized_count=run.normalized_count,
                    accepted_count=run.accepted_count,
                    rejected_count=run.rejected_count,
                    classified_count=run.classified_count,
                    duplicate_count=run.duplicate_count,
                    failed_count=run.failed_count,
                    rejection_reason_counts=dict(run.rejection_reason_counts),
                    failure_reason_counts=dict(run.failure_reason_counts),
                )
                for run in runs
            )
        return Page(entries, page, per_page, total)

    def set_favorite(self, item_id: int, favorite: bool) -> None:
        with self._uow_factory() as uow:
            item = uow.items.get(item_id)
            if item is None:
                raise EntityNotFoundError(f"资讯 {item_id} 不存在")
            item.is_favorite = favorite

    def set_manual_category(self, item_id: int, value: str | None) -> None:
        result = self._manual_classifier.classify(value)
        with self._uow_factory() as uow:
            item = uow.items.get(item_id)
            if item is None:
                raise EntityNotFoundError(f"资讯 {item_id} 不存在")
            category_before = item.manual_category
            old_value = category_before.value if category_before is not None else None
            new_category = result.category if result is not None else None
            item.manual_category = new_category
            new_value = new_category.value if new_category is not None else None
            item.updated_at = datetime.now(UTC)
            uow.review_events.add(
                ItemReviewEvent(
                    item_id=item.id,
                    changed_at=item.updated_at,
                    actor_source="web_manual_category",
                    old_data={"manual_category": old_value},
                    new_data={"manual_category": new_value},
                )
            )

    def set_source_enabled(self, source_id: int, enabled: bool) -> None:
        with self._uow_factory() as uow:
            source = uow.sources.get(source_id)
            if source is None:
                raise EntityNotFoundError(f"来源 {source_id} 不存在")
            if enabled and source.lifecycle_state is LifecycleState.CANDIDATE:
                raise SourceStateError("candidate 必须通过 preview 和 activate, 不能直接启用。")
            if enabled and source.requires_custom_collector:
                raise SourceStateError("该来源尚未通过可用预览, 不能启用。")
            source.enabled = enabled
            source.lifecycle_state = LifecycleState.ACTIVE if enabled else LifecycleState.PAUSED

    def set_taxonomy_review(
        self,
        item_id: int,
        *,
        primary_type: str | None = None,
        topic_tags: tuple[str, ...] | None = None,
        industry_tags: tuple[str, ...] | None = None,
        verification_status: str | None = None,
        review_status: str | None = None,
        official_url: str | None = None,
        origin_publisher: str | None = None,
        actor_source: str = "system_operator",
    ) -> None:
        from app.utils.url import canonicalize_url

        with self._uow_factory() as uow:
            item = uow.items.get(item_id)
            if item is None:
                raise EntityNotFoundError(f"资讯 {item_id} 不存在")
            old = {
                "manual_primary_type": item.manual_primary_type.value
                if item.manual_primary_type
                else None,
                "manual_topic_tags": item.manual_topic_tags,
                "manual_industry_tags": item.manual_industry_tags,
                "verification_status": item.verification_status.value,
                "review_status": item.review_status.value,
                "official_url": item.official_url,
                "origin_publisher": item.origin_publisher,
            }
            if primary_type is not None:
                item.manual_primary_type = PrimaryType(primary_type)
            if topic_tags is not None:
                item.manual_topic_tags = _validated_tags(topic_tags, TopicTag)
            if industry_tags is not None:
                item.manual_industry_tags = _validated_tags(industry_tags, IndustryTag)
            if verification_status is not None:
                item.verification_status = VerificationStatus(verification_status)
                item.verification_manually_set = True
            if review_status is not None:
                item.review_status = ReviewStatus(review_status)
                item.review_manually_set = True
            if official_url is not None:
                normalized = canonicalize_url(official_url)
                if normalized is None:
                    raise ValueError("official_url 必须是有效 HTTP(S) URL")
                item.official_url = normalized
                item.verification_manually_set = True
            if origin_publisher is not None:
                cleaned = " ".join(origin_publisher.split())
                if not cleaned or len(cleaned) > 500:
                    raise ValueError("origin_publisher 无效")
                item.origin_publisher = cleaned
            item.updated_at = datetime.now(UTC)
            new = {
                "manual_primary_type": item.manual_primary_type.value
                if item.manual_primary_type
                else None,
                "manual_topic_tags": item.manual_topic_tags,
                "manual_industry_tags": item.manual_industry_tags,
                "verification_status": item.verification_status.value,
                "review_status": item.review_status.value,
                "official_url": item.official_url,
                "origin_publisher": item.origin_publisher,
            }
            uow.review_events.add(
                ItemReviewEvent(
                    item_id=item.id,
                    changed_at=item.updated_at,
                    actor_source=actor_source[:100],
                    old_data=old,
                    new_data=new,
                )
            )


def _validated_tags[TagT: TopicTag | IndustryTag](
    values: tuple[str, ...], enum_type: type[TagT]
) -> list[str]:
    parsed = {enum_type(value) for value in values}
    return [value.value for value in enum_type if value in parsed]


__all__ = [
    "EntityNotFoundError",
    "ManualCategoryError",
    "SourceStateError",
    "WebDataService",
]
