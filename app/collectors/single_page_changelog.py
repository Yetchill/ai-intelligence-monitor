"""Bounded section collector for official single-page changelogs."""

import re
from collections.abc import Mapping
from hashlib import sha256
from typing import cast
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup, Tag

from app.domain.collection import CollectContext, CollectedItem, Fetcher
from app.utils.dates import parse_datetime
from app.utils.url import canonicalize_url

_DATE = re.compile(r"(?:19|20)\d{2}[年./-]\d{1,2}[月./-]\d{1,2}日?")


class SinglePageChangelogCollector:
    name = "single_page_changelog"

    def __init__(self, fetcher: Fetcher) -> None:
        self._fetcher = fetcher

    async def collect(self, context: CollectContext) -> list[CollectedItem]:
        response = await self._fetcher.fetch(context.source_url)
        soup = BeautifulSoup(response.content, "lxml")
        config = _mapping(context.config)
        selector = (
            _text(config.get("section_selector")) or "article h2, article h3, main h2, main h3"
        )
        max_items = min(200, max(1, _integer(config.get("max_items"), 20)))
        items: list[CollectedItem] = []
        seen_keys: set[str] = set()
        for heading in soup.select(selector):
            if len(items) >= max_items:
                break
            title = " ".join(heading.get_text(" ", strip=True).split())
            if len(title) < 4:
                continue
            summary = _section_summary(heading)
            date_match = _DATE.search(f"{title} {summary or ''}")
            stable_text = f"{date_match.group(0) if date_match else ''}\n{title}".casefold()
            key = sha256(stable_text.encode("utf-8")).hexdigest()[:20]
            if key in seen_keys:
                continue
            seen_keys.add(key)
            url = _entry_url(response.url, key)
            items.append(
                CollectedItem(
                    title=title,
                    original_url=url,
                    canonical_url=url,
                    published_at=parse_datetime(date_match.group(0) if date_match else None),
                    summary=summary,
                    extra={"changelog_entry_key": key, "detail_fetched": True},
                )
            )
        return items


def _section_summary(heading: Tag) -> str | None:
    parts: list[str] = []
    sibling = heading.next_sibling
    while sibling is not None and len(" ".join(parts)) < 2_000:
        if isinstance(sibling, Tag) and sibling.name in {"h1", "h2", "h3"}:
            break
        if isinstance(sibling, Tag):
            text = " ".join(sibling.get_text(" ", strip=True).split())
            if text:
                parts.append(text)
        sibling = sibling.next_sibling
    value = " ".join(parts).strip()
    return value[:2_000] or None


def _entry_url(page_url: str, key: str) -> str:
    split = urlsplit(page_url)
    query = dict(parse_qsl(split.query, keep_blank_values=True))
    query["entry"] = key
    value = urlunsplit(
        (split.scheme, split.netloc, split.path, urlencode(sorted(query.items())), "")
    )
    return canonicalize_url(value, keep_query_params=tuple(query)) or value


def _mapping(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        return {}
    return {str(key): child for key, child in cast(Mapping[object, object], value).items()}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _integer(value: object, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default
