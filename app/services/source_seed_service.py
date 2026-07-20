"""Explicit, idempotent import of documented example sources."""

from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

from app.config.settings import PROJECT_ROOT
from app.domain.enums import (
    Category,
    SourceAudience,
    SourceKind,
    SourceOrigin,
    SourceTier,
    SourceType,
)
from app.domain.models import Source
from app.storage.repositories import RepositoryUnitOfWork
from app.utils.url import canonicalize_url

UnitOfWorkFactory = Callable[[], RepositoryUnitOfWork]
DEFAULT_PRESET_PATH = PROJECT_ROOT / "app" / "config" / "preset_sources.yaml"
LEGACY_AIIA_URL = "https://www.aiiaorg.cn/"


@dataclass(frozen=True, slots=True)
class SourceSeedResult:
    created: int
    promoted: int
    existing: int
    conflicts: int
    expected: int

    @property
    def initialized(self) -> int:
        return self.created + self.promoted


class SourceSeedService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def seed(self, path: Path = DEFAULT_PRESET_PATH) -> SourceSeedResult:
        presets = _load_presets(path)
        created = 0
        promoted = 0
        existing = 0
        conflicts = 0
        with self._uow_factory() as uow:
            existing_by_url = {
                canonicalize_url(source.start_url) or source.start_url: source
                for source in uow.sources.list()
            }
            for preset in presets:
                current = existing_by_url.get(preset.start_url)
                if current is not None:
                    if _is_legacy_aiia(current, preset):
                        _promote_legacy_source(current, preset)
                        promoted += 1
                    elif current.source_kind is SourceKind.FORMAL:
                        existing += 1
                    else:
                        conflicts += 1
                    continue
                uow.sources.add(preset)
                existing_by_url[preset.start_url] = preset
                created += 1
        return SourceSeedResult(created, promoted, existing, conflicts, len(presets))


def _is_legacy_aiia(current: Source, preset: Source) -> bool:
    if preset.start_url != LEGACY_AIIA_URL or current.start_url != LEGACY_AIIA_URL:
        return False
    return (
        current.name == "AIIA"
        and current.description is None
        and current.source_type is SourceType.HTML_LIST
        and current.collector_name == "html_list"
        and current.default_category is Category.POLICY_INDUSTRY
        and current.origin is SourceOrigin.PRESET
        and current.source_kind is SourceKind.TEST
        and current.source_tier is SourceTier.FALLBACK
        and current.audience is SourceAudience.ALL
        and current.homepage_visible is False
        and current.export_visible is False
        and current.content_scope == []
        and current.include_terms == []
        and current.exclude_terms == []
        and current.minimum_quality_score == 50.0
        and current.accept_title_only is True
        and current.allow_external_links is False
        and current.allow_technical_updates is False
        and current.collector_config == _legacy_aiia_collector_config()
    )


def _promote_legacy_source(current: Source, preset: Source) -> None:
    """Promote only the exact managed stage-seven record and preserve enabled."""

    for name in (
        "name",
        "description",
        "source_type",
        "default_category",
        "collector_name",
        "collector_config",
        "origin",
        "source_kind",
        "source_tier",
        "audience",
        "homepage_visible",
        "export_visible",
        "content_scope",
        "include_terms",
        "exclude_terms",
        "minimum_quality_score",
        "accept_title_only",
        "allow_external_links",
        "allow_technical_updates",
    ):
        setattr(current, name, deepcopy(getattr(preset, name)))


def _legacy_aiia_collector_config() -> dict[str, object]:
    return {
        "allowed_domains": ["www.aiiaorg.cn", "mp.weixin.qq.com"],
        "discovery": {"mode": "selectors", "max_pages": 1, "max_depth": 0, "max_items": 100},
        "extraction": {
            "item_selector": ".news-scroll-area div.cursor-pointer",
            "title_selector": "h3",
            "date_selector": "span",
            "embedded_title_key": "title",
            "embedded_link_key": "external_url",
        },
    }


def _load_presets(path: Path) -> tuple[Source, ...]:
    with path.open(encoding="utf-8") as stream:
        raw = cast(object, yaml.safe_load(stream))
    if not isinstance(raw, Mapping):
        raise ValueError("预设来源文件根节点无效")
    values = cast(Mapping[object, object], raw).get("sources")
    if not isinstance(values, Sequence) or isinstance(values, (str, bytes)):
        raise ValueError("预设来源文件缺少 sources 列表")
    presets: list[Source] = []
    for index, value in enumerate(cast(Sequence[object], values), start=1):
        if not isinstance(value, Mapping):
            raise ValueError(f"第 {index} 个预设来源格式无效")
        item = {str(key): child for key, child in cast(Mapping[object, object], value).items()}
        name = _required_text(item.get("name"), f"第 {index} 个来源名称")
        start_url = _required_text(item.get("start_url"), f"第 {index} 个来源 URL")
        canonical_url = canonicalize_url(start_url)
        if canonical_url is None:
            raise ValueError(f"第 {index} 个来源 URL 必须是 HTTP(S) 地址")
        source_type = SourceType(_required_text(item.get("source_type"), "source_type"))
        collector_name = _required_text(item.get("collector_name"), "collector_name")
        source_kind = SourceKind(_text_or_default(item.get("source_kind"), SourceKind.TEST.value))
        source_tier = SourceTier(
            _text_or_default(item.get("source_tier"), SourceTier.FALLBACK.value)
        )
        audience = SourceAudience(_text_or_default(item.get("audience"), SourceAudience.ALL.value))
        raw_category = item.get("default_category")
        default_category = Category(raw_category) if isinstance(raw_category, str) else None
        raw_config = item.get("collector_config", {})
        if not isinstance(raw_config, Mapping):
            raise ValueError(f"第 {index} 个来源 collector_config 必须是对象")
        config_mapping = cast(Mapping[object, object], raw_config)
        presets.append(
            Source(
                name=name,
                description=_optional_text(item.get("description")),
                source_type=source_type,
                start_url=canonical_url,
                enabled=True,
                default_category=default_category,
                collector_name=collector_name,
                collector_config={str(key): child for key, child in config_mapping.items()},
                origin=SourceOrigin.PRESET,
                source_kind=source_kind,
                source_tier=source_tier,
                audience=audience,
                homepage_visible=_boolean_or_default(item.get("homepage_visible"), False),
                export_visible=_boolean_or_default(item.get("export_visible"), False),
                content_scope=list(_text_list(item.get("content_scope", []), "content_scope")),
                include_terms=list(_text_list(item.get("include_terms", []), "include_terms")),
                exclude_terms=list(_text_list(item.get("exclude_terms", []), "exclude_terms")),
                minimum_quality_score=_score(item.get("minimum_quality_score", 50)),
                accept_title_only=_boolean_or_default(item.get("accept_title_only"), True),
                allow_external_links=_boolean(
                    item.get("allow_external_links", False), "allow_external_links"
                ),
                allow_technical_updates=_boolean(
                    item.get("allow_technical_updates", False), "allow_technical_updates"
                ),
            )
        )
    return tuple(presets)


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} 不能为空")
    return value.strip()


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    return _required_text(value, "description")


def _boolean(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{label} 必须是布尔值")
    return value


def _boolean_or_default(value: object, default: bool) -> bool:
    return default if value is None else _boolean(value, "visibility setting")


def _text_or_default(value: object, default: str) -> str:
    return default if value is None else _required_text(value, "source metadata")


def _score(value: object) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 100:
        raise ValueError("minimum_quality_score 必须在 0 到 100 之间")
    return float(value)


def _text_list(value: object, label: str) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{label} 必须是字符串列表")
    cleaned: list[str] = []
    for entry in cast(Sequence[object], value):
        text = _required_text(entry, label)
        if text not in cleaned:
            cleaned.append(text)
    return tuple(cleaned)
