"""Enumerated values persisted by the stage-one data model."""

from enum import StrEnum


class SourceType(StrEnum):
    RSS = "rss"
    HTML_LIST = "html_list"
    GITHUB_RELEASE = "github_release"
    JSON_API = "json_api"
    CUSTOM = "custom"


class Category(StrEnum):
    MODEL_TECHNOLOGY = "model_technology"
    AGENT_PRODUCT = "agent_product"
    ENTERPRISE_CASE = "enterprise_case"
    AWARD_CASE = "award_case"
    SOLICITATION = "solicitation"
    POLICY_INDUSTRY = "policy_industry"
    UNCLASSIFIED = "unclassified"


class SourceOrigin(StrEnum):
    PRESET = "preset"
    USER_ADDED = "user_added"
    IMPORTED = "imported"


class SourceKind(StrEnum):
    """Business standing of a configured source."""

    FORMAL = "formal"
    TEST = "test"
    FALLBACK = "fallback"


class SourceTier(StrEnum):
    """Editorial authority tier used by the admission policy."""

    GOVERNMENT = "government"
    OFFICIAL_COMPANY = "official_company"
    ASSOCIATION = "association"
    AUTHORITATIVE_MEDIA = "authoritative_media"
    FALLBACK = "fallback"


class SourceAudience(StrEnum):
    LEADERSHIP = "leadership"
    ALL = "all"


class SourceScope(StrEnum):
    """Stable item-list visibility scopes exposed by Web and export adapters."""

    LEADERSHIP = "leadership"
    FORMAL_EXPORT = "formal_export"
    ALL = "all"
    NON_FORMAL = "non_formal"
    DISABLED = "disabled"
    FALLBACK = "fallback"


class DiscoveryStatus(StrEnum):
    READY = "ready"
    PARTIAL = "partial"
    NEEDS_CONFIGURATION = "needs_configuration"
    NEEDS_CUSTOM_COLLECTOR = "needs_custom_collector"
    BLOCKED = "blocked"
    UNREACHABLE = "unreachable"


class CrawlStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"

    # Source compatibility for callers compiled against the stage-one names.
    SUCCEEDED = SUCCESS
    PARTIAL = PARTIAL_SUCCESS


class RunTrigger(StrEnum):
    LEGACY_MANUAL = "legacy_manual"
    MANUAL_WEB = "manual_web"
    MANUAL_CLI = "manual_cli"
    SCHEDULED = "scheduled"


class Weekday(StrEnum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"
