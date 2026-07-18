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


class CrawlStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"

    # Source compatibility for callers compiled against the stage-one names.
    SUCCEEDED = SUCCESS
    PARTIAL = PARTIAL_SUCCESS
