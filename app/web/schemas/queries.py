"""Strict parsing for local Web list filters."""

from datetime import UTC, date, datetime, time, timedelta
from enum import Enum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from app.domain.enums import Category, PrimaryType, ReviewStatus, SourceScope, VerificationStatus
from app.domain.queries import ItemFilter, ItemQuery

MAX_DATABASE_ID = 9_223_372_036_854_775_807


class WebInputError(ValueError):
    """A concise validation error suitable for an HTML response."""


class PageParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1, le=1_000_000)
    per_page: Literal[20, 50, 100] = 20

    @field_validator("per_page", mode="before")
    @classmethod
    def parse_per_page(cls, value: object) -> object:
        if isinstance(value, str) and value.isdecimal():
            return int(value)
        return value

    @classmethod
    def parse(cls, values: dict[str, str]) -> Self:
        try:
            return cls.model_validate(values)
        except ValidationError as exc:
            raise WebInputError("分页参数无效; 每页只支持 20、50 或 100 条。") from exc


class ItemQueryParams(PageParams):
    keyword: str | None = Field(default=None, max_length=200)
    category: Category | None = None
    primary_type: PrimaryType | None = None
    verification_status: VerificationStatus | None = None
    review_status: ReviewStatus | None = None
    source_id: int | None = Field(default=None, ge=1, le=MAX_DATABASE_ID)
    favorite: Literal["all", "yes", "no"] = "all"
    published_from: date | None = None
    published_to: date | None = None
    discovered_from: date | None = None
    discovered_to: date | None = None
    unclassified: Literal["all", "yes", "no"] = "all"
    is_read: Literal["all", "yes", "no"] = "all"
    source_scope: Literal[
        "leadership", "all", "non_formal", "disabled", "fallback", "industry_leads"
    ] = "all"

    @field_validator("source_scope", mode="before")
    @classmethod
    def safe_source_scope(cls, value: object) -> object:
        allowed = {"leadership", "all", "non_formal", "disabled", "fallback", "industry_leads"}
        return value if value in allowed else "leadership"

    @field_validator("keyword", mode="before")
    @classmethod
    def trim_keyword(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        return stripped or None

    @classmethod
    def parse(cls, values: dict[str, str]) -> Self:
        try:
            parsed = cls.model_validate(
                {key: value for key, value in values.items() if value != ""}
            )
        except ValidationError as exc:
            raise WebInputError(
                "筛选参数无效, 请检查分类、来源、日期和分页设置。日期格式应为 YYYY-MM-DD。"
            ) from exc
        if parsed.published_from and parsed.published_to:
            if parsed.published_from > parsed.published_to:
                raise WebInputError("发布时间开始日期不能晚于结束日期。")
        if parsed.discovered_from and parsed.discovered_to:
            if parsed.discovered_from > parsed.discovered_to:
                raise WebInputError("发现时间开始日期不能晚于结束日期。")
        return parsed

    def to_domain(self) -> ItemQuery:
        item_filter = self.to_filter()
        return ItemQuery(
            keyword=item_filter.keyword,
            category=item_filter.category,
            primary_type=item_filter.primary_type,
            verification_status=item_filter.verification_status,
            review_status=item_filter.review_status,
            source_id=item_filter.source_id,
            favorite=item_filter.favorite,
            published_from=item_filter.published_from,
            published_to=item_filter.published_to,
            discovered_from=item_filter.discovered_from,
            discovered_to=item_filter.discovered_to,
            unclassified=item_filter.unclassified,
            is_read=item_filter.is_read,
            source_scope=item_filter.source_scope,
            page=self.page,
            per_page=self.per_page,
        )

    def to_filter(self, *, for_export: bool = False) -> ItemFilter:
        scope = SourceScope(self.source_scope)
        if for_export and scope is SourceScope.LEADERSHIP:
            scope = SourceScope.FORMAL_EXPORT
        return ItemFilter(
            keyword=self.keyword,
            category=self.category,
            primary_type=self.primary_type,
            verification_status=self.verification_status,
            review_status=self.review_status,
            source_id=self.source_id,
            favorite=_tri_state(self.favorite),
            published_from=_start(self.published_from),
            published_to=_exclusive_end(self.published_to),
            discovered_from=_start(self.discovered_from),
            discovered_to=_exclusive_end(self.discovered_to),
            unclassified=_tri_state(self.unclassified),
            is_read=_tri_state(self.is_read),
            source_scope=scope,
        )

    def query_values(self) -> dict[str, str]:
        values: dict[str, str] = {"per_page": str(self.per_page)}
        for key in (
            "keyword",
            "category",
            "primary_type",
            "verification_status",
            "review_status",
            "source_id",
            "favorite",
            "published_from",
            "published_to",
            "discovered_from",
            "discovered_to",
            "unclassified",
            "is_read",
            "source_scope",
        ):
            value = getattr(self, key)
            if value is None or (value == "all" and key != "source_scope"):
                continue
            values[key] = value.value if isinstance(value, Enum) else str(value)
        return values

    def export_values(self) -> dict[str, str]:
        values = self.query_values()
        values.pop("per_page", None)
        return values


def _tri_state(value: str) -> bool | None:
    return {"all": None, "yes": True, "no": False}[value]


def _start(value: date | None) -> datetime | None:
    return datetime.combine(value, time.min, UTC) if value else None


def _exclusive_end(value: date | None) -> datetime | None:
    if value is None:
        return None
    try:
        next_day = value + timedelta(days=1)
    except OverflowError as exc:
        raise WebInputError("结束日期超出支持范围。") from exc
    return datetime.combine(next_day, time.min, UTC)
