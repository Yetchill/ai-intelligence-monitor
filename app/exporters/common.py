"""Shared safe text, labels, filenames, and formatting for office documents."""

import re
from datetime import datetime

from app.domain.enums import Category
from app.utils.url import is_http_url

CATEGORY_LABELS = {
    Category.MODEL_TECHNOLOGY: "大模型与技术",
    Category.AGENT_PRODUCT: "智能体与产品",
    Category.ENTERPRISE_CASE: "企业成果与案例",
    Category.AWARD_CASE: "奖项与优秀案例",
    Category.SOLICITATION: "征集与申报",
    Category.POLICY_INDUSTRY: "政策、标准与行业",
    Category.UNCLASSIFIED: "待分类",
}
CATEGORY_ORDER = tuple(CATEGORY_LABELS)

_ILLEGAL_XML = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\ud800-\udfff\ufffe\uffff]")
_FORMULA_PREFIXES = ("=", "+", "-", "@")
_INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_INVALID_SHEET = re.compile(r"[\\/*?:\[\]]")


def clean_text(value: object, *, limit: int = 32_767) -> str:
    """Return XML-safe bounded plain text without interpreting HTML."""

    text = _ILLEGAL_XML.sub("", str(value))
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"


def excel_safe_text(value: object, *, limit: int = 32_767) -> str:
    """Keep untrusted text from being interpreted as an Excel formula."""

    text = clean_text(value, limit=limit)
    if text.startswith(_FORMULA_PREFIXES) or text.startswith(("\t", "\r", "\n")):
        return "'" + text
    return text


def safe_hyperlink(value: str | None) -> str | None:
    if value is None or len(value) > 2_048 or not is_http_url(value):
        return None
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        return None
    return value.strip()


def format_time(value: datetime | None) -> str:
    return value.strftime("%Y-%m-%d %H:%M") if value is not None else ""


def safe_filename(value: str, *, extension: str) -> str:
    stem = _INVALID_FILENAME.sub("-", clean_text(value, limit=120)).strip(" .-")
    if not stem:
        stem = "export"
    normalized_extension = extension.lstrip(".").lower()
    return f"{stem}.{normalized_extension}"


def safe_sheet_name(value: str) -> str:
    name = _INVALID_SHEET.sub("-", clean_text(value, limit=31)).strip("'")
    return name or "导出"
