"""Short-transaction source creation, editing, and confirmed rediscovery."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from threading import Lock

from sqlalchemy.exc import IntegrityError, OperationalError

from app.domain.enums import (
    Category,
    DiscoveryStatus,
    SourceAudience,
    SourceKind,
    SourceOrigin,
    SourceTier,
    SourceType,
)
from app.domain.models import Source
from app.domain.onboarding import DiscoverySession
from app.services.source_discovery import (
    DiscoveryTokenStore,
    SourceDiscoveryService,
    SourcePreviewService,
)
from app.storage.repositories import RepositoryUnitOfWork
from app.utils.url import is_http_url

UnitOfWorkFactory = Callable[[], RepositoryUnitOfWork]


class SourceManagementError(ValueError):
    """A safe validation or conflict message for source management."""


class SourceAlreadyExistsError(SourceManagementError):
    def __init__(self, source_id: int) -> None:
        self.source_id = source_id
        super().__init__(f"该规范化网址已存在, 请查看来源 {source_id}。")


class ManagedSourceNotFoundError(LookupError):
    """The requested source does not exist."""


@dataclass(frozen=True, slots=True)
class SourceDetails:
    id: int
    name: str
    description: str | None
    start_url: str | None
    source_type: SourceType
    collector_name: str
    enabled: bool
    default_category: Category | None
    discovery_status: str | None
    discovery_confidence: float | None
    requires_custom_collector: bool
    origin: SourceOrigin
    last_tested_at: datetime | None
    last_checked_at: datetime | None
    last_success_at: datetime | None
    last_error: str | None


class SourceOnboardingService:
    def __init__(
        self,
        discovery: SourceDiscoveryService,
        preview: SourcePreviewService,
        store: DiscoveryTokenStore,
    ) -> None:
        self._discovery = discovery
        self._preview = preview
        self._store = store

    async def start(self, url: str, *, rediscover_source_id: int | None = None) -> str:
        result = await self._discovery.discover(url)
        preview = await self._preview.preview(result)
        return self._store.put(
            DiscoverySession(
                discovery=result,
                preview=preview,
                rediscover_source_id=rediscover_source_id,
            )
        )


class SourceManagementService:
    def __init__(self, uow_factory: UnitOfWorkFactory, store: DiscoveryTokenStore) -> None:
        self._uow_factory = uow_factory
        self._store = store
        self._write_lock = Lock()

    def get_discovery(self, token: str) -> DiscoverySession:
        return self._store.get(token)

    def get_source(self, source_id: int) -> SourceDetails:
        with self._uow_factory() as uow:
            source = uow.sources.get(source_id)
            if source is None:
                raise ManagedSourceNotFoundError(f"来源 {source_id} 不存在。")
            return _details(source)

    def create_from_token(
        self,
        token: str,
        *,
        name: str,
        default_category: str | None,
        enabled: bool,
        description: str | None,
    ) -> SourceDetails:
        session = self._store.claim(token)
        try:
            if session.rediscover_source_id is not None:
                raise SourceManagementError("该检测结果只用于重新检测, 不能创建新来源。")
            if enabled and not session.can_enable:
                raise SourceManagementError("当前预览不可用; 只能保存为停用的待处理来源。")
            cleaned_name = _name(name)
            cleaned_description = _description(description)
            category = _category(default_category)
            discovery = session.discovery
            persisted_status = (
                DiscoveryStatus.NEEDS_CONFIGURATION.value
                if discovery.usable and not session.preview.can_enable
                else discovery.discovery_status.value
            )
            try:
                with self._write_lock, self._uow_factory() as uow:
                    existing = uow.sources.get_by_start_url(discovery.normalized_url)
                    if existing is not None:
                        raise SourceAlreadyExistsError(existing.id)
                    source = uow.sources.add(
                        Source(
                            name=cleaned_name,
                            description=cleaned_description,
                            source_type=discovery.source_type,
                            start_url=discovery.normalized_url,
                            enabled=enabled,
                            default_category=category,
                            collector_name=discovery.collector_name,
                            collector_config=dict(discovery.collector_config),
                            discovery_status=persisted_status,
                            discovery_confidence=discovery.discovery_confidence,
                            requires_custom_collector=discovery.requires_custom_collector,
                            origin=SourceOrigin.USER_ADDED,
                            source_kind=(
                                SourceKind.FALLBACK
                                if discovery.source_type is SourceType.GITHUB_RELEASE
                                else SourceKind.TEST
                            ),
                            source_tier=SourceTier.FALLBACK,
                            audience=SourceAudience.ALL,
                            homepage_visible=False,
                            export_visible=False,
                            content_scope=[],
                            include_terms=[],
                            exclude_terms=[],
                            minimum_quality_score=15,
                            accept_title_only=True,
                            allow_external_links=False,
                            allow_technical_updates=False,
                            last_tested_at=discovery.tested_at,
                        )
                    )
                    source_id = source.id
            except (IntegrityError, OperationalError) as exc:
                with self._write_lock, self._uow_factory() as uow:
                    existing = uow.sources.get_by_start_url(discovery.normalized_url)
                    if existing is not None:
                        raise SourceAlreadyExistsError(existing.id) from exc
                raise
        except Exception:
            self._store.release(token)
            raise
        self._store.discard(token)
        return self.get_source(source_id)

    def edit(
        self,
        source_id: int,
        *,
        name: str,
        default_category: str | None,
        enabled: bool,
        description: str | None,
    ) -> SourceDetails:
        cleaned_name = _name(name)
        cleaned_description = _description(description)
        category = _category(default_category)
        with self._write_lock, self._uow_factory() as uow:
            source = uow.sources.get(source_id)
            if source is None:
                raise ManagedSourceNotFoundError(f"来源 {source_id} 不存在。")
            if enabled and (
                source.requires_custom_collector
                or source.discovery_status
                in {"needs_configuration", "needs_custom_collector", "blocked", "unreachable"}
            ):
                raise SourceManagementError("该来源尚未通过可用预览, 不能启用。")
            source.name = cleaned_name
            source.description = cleaned_description
            source.default_category = category
            source.enabled = enabled
        return self.get_source(source_id)

    def confirm_rediscovery(self, source_id: int, token: str) -> SourceDetails:
        session = self._store.claim(token)
        try:
            if session.rediscover_source_id != source_id:
                raise SourceManagementError("重新检测结果与当前来源不匹配。")
            discovery = session.discovery
            try:
                with self._write_lock, self._uow_factory() as uow:
                    source = uow.sources.get(source_id)
                    if source is None:
                        raise ManagedSourceNotFoundError(f"来源 {source_id} 不存在。")
                    source.discovery_status = discovery.discovery_status.value
                    source.discovery_confidence = discovery.discovery_confidence
                    source.last_tested_at = discovery.tested_at
                    if session.can_enable:
                        duplicate = uow.sources.get_by_start_url(discovery.normalized_url)
                        if duplicate is not None and duplicate.id != source_id:
                            raise SourceAlreadyExistsError(duplicate.id)
                        source.start_url = discovery.normalized_url
                        source.source_type = discovery.source_type
                        source.collector_name = discovery.collector_name
                        source.collector_config = dict(discovery.collector_config)
                        source.requires_custom_collector = False
            except IntegrityError as exc:
                raise SourceManagementError("新检测网址与已有来源冲突, 原配置保持不变。") from exc
        except Exception:
            self._store.release(token)
            raise
        self._store.discard(token)
        return self.get_source(source_id)


def _details(source: Source) -> SourceDetails:
    return SourceDetails(
        id=source.id,
        name=source.name,
        description=source.description,
        start_url=source.start_url if is_http_url(source.start_url) else None,
        source_type=source.source_type,
        collector_name=source.collector_name,
        enabled=source.enabled,
        default_category=source.default_category,
        discovery_status=source.discovery_status,
        discovery_confidence=source.discovery_confidence,
        requires_custom_collector=source.requires_custom_collector,
        origin=source.origin,
        last_tested_at=source.last_tested_at,
        last_checked_at=source.last_checked_at,
        last_success_at=source.last_success_at,
        last_error=source.last_error,
    )


def _name(value: str) -> str:
    cleaned = " ".join(value.split())
    if not cleaned:
        raise SourceManagementError("来源名称不能为空。")
    if len(cleaned) > 255:
        raise SourceManagementError("来源名称不能超过 255 个字符。")
    return cleaned


def _description(value: str | None) -> str | None:
    cleaned = value.strip() if value else ""
    if len(cleaned) > 2000:
        raise SourceManagementError("来源说明不能超过 2000 个字符。")
    return cleaned or None


def _category(value: str | None) -> Category | None:
    if not value:
        return None
    try:
        return Category(value)
    except ValueError as exc:
        raise SourceManagementError("默认分类无效。") from exc


__all__ = [
    "ManagedSourceNotFoundError",
    "SourceAlreadyExistsError",
    "SourceDetails",
    "SourceManagementError",
    "SourceManagementService",
    "SourceOnboardingService",
]
