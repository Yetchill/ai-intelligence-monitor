"""Opt-in live checks for the three stage-two acceptance sources."""

import pytest

from app.collectors.github_release import GitHubReleaseCollector
from app.collectors.html_list import HTMLListCollector
from app.collectors.rss import RSSCollector
from app.domain.collection import CollectContext, CollectedItem
from app.fetchers.http import HttpFetcher

pytestmark = pytest.mark.network


def _assert_valid(items: list[CollectedItem]) -> None:
    assert items
    assert all(item.title.strip() for item in items)
    assert all(item.canonical_url.startswith(("http://", "https://")) for item in items)


@pytest.mark.asyncio
async def test_google_blog_rss_live() -> None:
    async with HttpFetcher(timeout_seconds=30, request_interval_seconds=0) as fetcher:
        items = await RSSCollector(fetcher).collect(
            CollectContext(source_url="https://blog.google/rss/")
        )

    _assert_valid(items)
    assert all(item.published_at is not None or item.summary for item in items)
    print(f"Google Blog RSS collected {len(items)} items")


@pytest.mark.asyncio
async def test_aiia_home_live() -> None:
    context = CollectContext(
        source_url="https://www.aiiaorg.cn/",
        config={
            "allowed_domains": ["www.aiiaorg.cn", "mp.weixin.qq.com"],
            "discovery": {"mode": "selectors", "max_pages": 1, "max_depth": 0},
            "extraction": {
                "item_selector": ".news-scroll-area div.cursor-pointer",
                "title_selector": "h3",
                "date_selector": "span",
                "embedded_title_key": "title",
                "embedded_link_key": "external_url",
            },
        },
    )
    async with HttpFetcher(timeout_seconds=30, request_interval_seconds=0) as fetcher:
        items = await HTMLListCollector(fetcher).collect(context)

    _assert_valid(items)
    assert all(item.published_at is not None for item in items)
    forbidden_titles = {"登录", "联系我们", "活动日历"}
    assert all(item.title not in forbidden_titles and not item.title.isdigit() for item in items)
    print(f"AIIA home collected {len(items)} news items")


@pytest.mark.asyncio
async def test_qwen_agent_releases_live() -> None:
    async with HttpFetcher(timeout_seconds=30, request_interval_seconds=0) as fetcher:
        items = await GitHubReleaseCollector(fetcher).collect(
            CollectContext(
                source_url="https://github.com/QwenLM/Qwen-Agent/releases",
                config={"max_releases": 30, "include_prereleases": False},
            )
        )

    _assert_valid(items)
    assert all(item.published_at is not None for item in items)
    assert all(item.extra.get("prerelease") is False for item in items)
    print(f"Qwen-Agent collected {len(items)} formal releases")
