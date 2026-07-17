"""RSS and Atom list collector."""

from collections.abc import Mapping, Sequence
from typing import cast

import feedparser  # pyright: ignore[reportMissingTypeStubs]
from bs4 import BeautifulSoup

from app.domain.collection import CollectContext, CollectedItem, Fetcher
from app.utils.dates import parse_datetime
from app.utils.url import canonicalize_url


class RSSCollector:
    """Collect feed metadata without visiting entry detail pages."""

    name = "rss"

    def __init__(self, fetcher: Fetcher) -> None:
        self._fetcher = fetcher

    async def collect(self, context: CollectContext) -> list[CollectedItem]:
        response = await self._fetcher.fetch(context.source_url)
        parsed = _parse_feed(response.content)
        entries_value = parsed.get("entries", [])
        if not isinstance(entries_value, Sequence) or isinstance(entries_value, (str, bytes)):
            return []

        items: list[CollectedItem] = []
        entries = cast(Sequence[object], entries_value)
        for raw_entry in entries:
            try:
                if not isinstance(raw_entry, Mapping):
                    continue
                entry = cast(Mapping[str, object], raw_entry)
                title = _string(entry.get("title"))
                link = _string(entry.get("link"))
                if not title or not link:
                    continue
                canonical_url = canonicalize_url(link, base_url=response.url)
                if canonical_url is None:
                    continue
                summary_value = _string(entry.get("summary")) or _string(entry.get("description"))
                summary = _plain_text(summary_value)
                published = (
                    _string(entry.get("published"))
                    or _string(entry.get("updated"))
                    or _string(entry.get("created"))
                )
                items.append(
                    CollectedItem(
                        title=_plain_text(title) or title.strip(),
                        original_url=canonical_url,
                        canonical_url=canonical_url,
                        published_at=parse_datetime(published),
                        summary=summary,
                    )
                )
            except Exception:
                # Feeds in the wild often contain one malformed entry. Keep the rest usable.
                continue
        return items


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _parse_feed(content: bytes) -> Mapping[str, object]:
    return cast(
        Mapping[str, object],
        feedparser.parse(content),  # pyright: ignore[reportUnknownMemberType]
    )


def _plain_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = BeautifulSoup(value, "lxml").get_text(" ", strip=True)
    return " ".join(text.split()) or None
