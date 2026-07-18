"""Explicit, idempotent import of documented example sources."""

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import cast

import yaml

from app.config.settings import PROJECT_ROOT
from app.domain.enums import Category, SourceOrigin, SourceType
from app.domain.models import Source
from app.storage.repositories import RepositoryUnitOfWork
from app.utils.url import canonicalize_url

UnitOfWorkFactory = Callable[[], RepositoryUnitOfWork]
DEFAULT_PRESET_PATH = PROJECT_ROOT / "app" / "config" / "preset_sources.yaml"


class SourceSeedService:
    def __init__(self, uow_factory: UnitOfWorkFactory) -> None:
        self._uow_factory = uow_factory

    def seed(self, path: Path = DEFAULT_PRESET_PATH) -> tuple[int, int]:
        presets = _load_presets(path)
        created = 0
        existing = 0
        with self._uow_factory() as uow:
            for preset in presets:
                if uow.sources.get_by_start_url(preset.start_url) is not None:
                    existing += 1
                    continue
                uow.sources.add(preset)
                created += 1
        return created, existing


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
        raw_category = item.get("default_category")
        default_category = Category(raw_category) if isinstance(raw_category, str) else None
        raw_config = item.get("collector_config", {})
        if not isinstance(raw_config, Mapping):
            raise ValueError(f"第 {index} 个来源 collector_config 必须是对象")
        config_mapping = cast(Mapping[object, object], raw_config)
        presets.append(
            Source(
                name=name,
                source_type=source_type,
                start_url=canonical_url,
                enabled=True,
                default_category=default_category,
                collector_name=collector_name,
                collector_config={str(key): child for key, child in config_mapping.items()},
                origin=SourceOrigin.PRESET,
            )
        )
    return tuple(presets)


def _required_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} 不能为空")
    return value.strip()
