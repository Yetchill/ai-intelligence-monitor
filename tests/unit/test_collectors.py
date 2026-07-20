"""Offline collector tests backed by fixed RSS, HTML, and JSON samples."""

from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

import pytest

from app.collectors.cls_topic import CLSTopicCollector
from app.collectors.github_release import GitHubReleaseCollector
from app.collectors.html_list import HTMLListCollector
from app.collectors.registry import CollectorRegistry, default_collector_registry
from app.collectors.rss import RSSCollector
from app.collectors.single_page_changelog import SinglePageChangelogCollector
from app.domain.collection import CollectContext, FetchResult
from app.domain.enums import SourceOrigin, SourceType
from app.domain.models import Source
from app.fetchers.errors import ForbiddenFetchError, RateLimitFetchError

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


class FixtureFetcher:
    def __init__(self, responses: Mapping[str, bytes]) -> None:
        self.responses = responses
        self.requests: list[tuple[str, Mapping[str, str] | None]] = []

    async def fetch(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> FetchResult:
        self.requests.append((url, headers))
        return FetchResult(
            requested_url=url,
            url=url,
            status_code=200,
            headers={},
            content=self.responses[url],
        )


class RateLimitedGitHubFetcher(FixtureFetcher):
    async def fetch(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> FetchResult:
        if url.startswith("https://api.github.com/"):
            self.requests.append((url, headers))
            raise RateLimitFetchError(url, "quota exhausted")
        return await super().fetch(url, headers=headers)


class ForbiddenGitHubFetcher(FixtureFetcher):
    async def fetch(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> FetchResult:
        self.requests.append((url, headers))
        raise ForbiddenFetchError(url, "permission denied")


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("fixture_name", "expected_title"),
    [("sample_rss.xml", "Example model"), ("sample_atom.xml", "Atom release")],
)
async def test_rss_collector_supports_rss_and_atom(
    fixture_name: str,
    expected_title: str,
) -> None:
    url = "https://example.com/feed.xml"
    fetcher = FixtureFetcher({url: (FIXTURES / fixture_name).read_bytes()})

    items = await RSSCollector(fetcher).collect(CollectContext(source_url=url))

    assert items
    assert expected_title in items[0].title
    assert items[0].canonical_url.startswith("https://example.com/")
    assert items[0].published_at is not None
    assert items[0].summary
    if fixture_name == "sample_rss.xml":
        assert len(items) == 2
        assert items[0].canonical_url == "https://example.com/news/model-v1"


@pytest.mark.asyncio
async def test_rss_collector_enforces_configured_result_limit() -> None:
    url = "https://example.com/feed.xml"
    fetcher = FixtureFetcher({url: (FIXTURES / "sample_rss.xml").read_bytes()})

    items = await RSSCollector(fetcher).collect(
        CollectContext(source_url=url, config={"max_items": 1})
    )

    assert len(items) == 1


@pytest.mark.asyncio
async def test_qbitai_official_feed_preserves_dates_links_and_deduplicates() -> None:
    url = "https://www.qbitai.com/category/%E8%B5%84%E8%AE%AF/feed"
    fetcher = FixtureFetcher({url: (FIXTURES / "qbitai_feed.xml").read_bytes()})

    items = await RSSCollector(fetcher).collect(
        CollectContext(source_url=url, config={"max_items": 20})
    )

    assert [item.title for item in items] == [
        "国产大模型发布重要能力升级",
        "Agent 平台开放全新 API",
    ]
    assert [
        item.published_at.date().isoformat() if item.published_at else None for item in items
    ] == [
        "2026-07-20",
        "2026-07-19",
    ]
    assert [item.canonical_url for item in items] == [
        "https://www.qbitai.com/2026/07/310001.html",
        "https://www.qbitai.com/2026/07/310002.html",
    ]


@pytest.mark.asyncio
async def test_cls_topic_uses_public_embedded_json_with_dates_and_stable_links() -> None:
    url = "https://www.cls.cn/subject/1321"
    fetcher = FixtureFetcher({url: (FIXTURES / "cls_topic.html").read_bytes()})

    items = await CLSTopicCollector(fetcher).collect(
        CollectContext(source_url=url, config={"max_items": 20})
    )

    assert [item.title for item in items] == [
        "人工智能产业发布重要模型更新",
        "智能体平台进入行业应用阶段",
    ]
    assert [item.canonical_url for item in items] == [
        "https://www.cls.cn/detail/2430001",
        "https://www.cls.cn/detail/2430002",
    ]
    assert all(item.published_at is not None for item in items)
    assert items[0].extra == {
        "public_payload": "__NEXT_DATA__",
        "article_id": "2430001",
    }
    assert items[0].summary == "公开专题摘要。"
    assert items[1].summary == (
        "【智能体平台进入行业应用阶段】财联社7月19日电\uff0c据称该平台将继续升级。"
    )


@pytest.mark.asyncio
async def test_deepseek_changelog_pairs_date_heading_with_update_heading() -> None:
    url = "https://api-docs.deepseek.com/zh-cn/updates/"
    fetcher = FixtureFetcher({url: (FIXTURES / "deepseek_changelog.html").read_bytes()})

    items = await SinglePageChangelogCollector(fetcher).collect(
        CollectContext(
            source_url=url,
            config={
                "content_selector": ".theme-doc-markdown",
                "date_heading_selector": "h2",
                "entry_selector": "h3",
                "append_summary_when_title_lacks_action": True,
            },
        )
    )

    assert [
        item.published_at.date().isoformat() if item.published_at else None for item in items
    ] == [
        "2026-04-24",
        "2025-12-01",
    ]
    assert items[0].title.startswith("DeepSeek-V4\uff1a")
    assert "正式发布" in items[0].title
    assert items[0].canonical_url != items[1].canonical_url


@pytest.mark.asyncio
async def test_kimi_changelog_pairs_each_update_with_section_date_and_filters_noise() -> None:
    url = "https://platform.kimi.com/blog/posts/changelog"
    fetcher = FixtureFetcher({url: (FIXTURES / "kimi_changelog.html").read_bytes()})

    items = await SinglePageChangelogCollector(fetcher).collect(
        CollectContext(
            source_url=url,
            config={
                "content_selector": "article",
                "date_heading_selector": "h2",
                "entry_selector": "li",
                "include_entry_terms": ["模型", "API"],
            },
        )
    )

    assert [item.title for item in items] == [
        "Kimi K2 Think 模型及其 turbo 版本模型正式发布",
        "kimi-k2-0905-preview 模型上线发布",
    ]
    assert items[0].published_at is not None
    assert items[0].published_at.date().isoformat() == "2025-11-06"
    assert items[0].extra["original_time_text"] == "2025年11月6日"


@pytest.mark.asyncio
async def test_qianfan_changelog_builds_stable_model_action_rows_with_inherited_year() -> None:
    url = "https://cloud.baidu.com/doc/qianfan/s/Kmh4stnjp"
    fetcher = FixtureFetcher({url: (FIXTURES / "qianfan_changelog.html").read_bytes()})

    context = CollectContext(
        source_url=url,
        config={
            "content_selector": ".post__body",
            "date_heading_selector": "h2",
            "entry_selector": "tbody tr",
            "entry_title_cells": [2, 5],
            "entry_date_cell": 0,
            "entry_summary_cell": 6,
            "entry_title_replacements": {"上新": "正式发布"},
        },
    )
    first = await SinglePageChangelogCollector(fetcher).collect(context)
    second = await SinglePageChangelogCollector(fetcher).collect(context)

    assert [item.title for item in first] == [
        "Kimi-K2.5 — 退役",
        "Example-Model — 正式发布",
    ]
    assert first[0].published_at is not None
    assert first[0].published_at.date().isoformat() == "2026-07-09"
    assert [item.canonical_url for item in first] == [item.canonical_url for item in second]


@pytest.mark.asyncio
async def test_zhipu_research_uses_public_embedded_ids_for_stable_detail_links() -> None:
    url = "https://www.zhipuai.cn/zh/research"
    fetcher = FixtureFetcher({url: (FIXTURES / "zhipu_research.html").read_bytes()})

    items = await HTMLListCollector(fetcher).collect(
        CollectContext(
            source_url=url,
            config={
                "allowed_domains": ["www.zhipuai.cn"],
                "discovery": {"mode": "selectors", "max_items": 20},
                "extraction": {
                    "item_selector": "main div.border-b",
                    "title_selector": "div.text-xl",
                    "date_selector": "p",
                    "embedded_title_key": "title_zh",
                    "embedded_link_key": "id",
                    "embedded_link_template": "/zh/research/{value}",
                },
            },
        )
    )

    assert [item.canonical_url for item in items] == [
        "https://www.zhipuai.cn/zh/research/161",
        "https://www.zhipuai.cn/zh/research/156",
    ]
    assert all(item.published_at is not None for item in items)


@pytest.mark.asyncio
async def test_media_selector_parses_relative_time_and_filters_financing_stock_and_ipo() -> None:
    url = "https://36kr.com/newsflashes"
    fetcher = FixtureFetcher({url: (FIXTURES / "media_relative_list.html").read_bytes()})
    fixed_now = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)

    items = await HTMLListCollector(fetcher, clock=lambda: fixed_now).collect(
        CollectContext(
            source_url=url,
            config={
                "allowed_domains": ["36kr.com"],
                "filter_selector_items": True,
                "discovery": {
                    "mode": "selectors",
                    "include_text": ["AI", "大模型"],
                    "exclude_text": ["融资", "股票", "IPO", "上市"],
                },
                "extraction": {
                    "item_selector": ".newsflash-item",
                    "title_selector": "a.item-title",
                    "link_selector": "a.item-title",
                    "date_selector": ".time",
                },
            },
        )
    )

    assert [item.title for item in items] == ["某公司发布新一代 AI 大模型"]
    assert items[0].published_at == datetime(2026, 7, 20, 10, 0, tzinfo=UTC)
    assert items[0].extra["original_time_text"] == "2小时前"


@pytest.mark.asyncio
async def test_media_selector_uses_nearest_group_date_when_item_time_is_empty() -> None:
    url = "https://zhidx.com/news"
    fetcher = FixtureFetcher({url: (FIXTURES / "media_relative_list.html").read_bytes()})
    fixed_now = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)

    items = await HTMLListCollector(fetcher, clock=lambda: fixed_now).collect(
        CollectContext(
            source_url=url,
            config={
                "allowed_domains": ["zhidx.com"],
                "discovery": {"mode": "selectors"},
                "extraction": {
                    "item_selector": ".news-item",
                    "title_selector": "a.title",
                    "link_selector": "a.title",
                    "date_selector": ".time",
                    "ancestor_date_selector": ".title-name",
                },
            },
        )
    )

    assert [item.title for item in items] == ["智能体平台发布重要升级"]
    assert items[0].published_at == datetime(2026, 7, 19, 12, 0, tzinfo=UTC)
    assert items[0].extra["original_time_text"] == "昨天"


@pytest.mark.asyncio
async def test_html_selector_mode_extracts_metadata_and_bounded_pagination() -> None:
    first_url = "https://example.com/news"
    second_url = "https://example.com/news?page=2"
    fetcher = FixtureFetcher(
        {
            first_url: (FIXTURES / "sample_list.html").read_bytes(),
            second_url: (FIXTURES / "sample_list_page_2.html").read_bytes(),
        }
    )
    context = CollectContext(
        source_url=first_url,
        config={
            "allowed_domains": ["example.com"],
            "discovery": {
                "mode": "selectors",
                "max_pages": 2,
                "max_depth": 1,
                "pagination_selector": "a.next",
            },
            "extraction": {
                "item_selector": ".news-list li",
                "title_selector": ".title",
                "link_selector": "a",
                "date_selector": "time, .date",
                "summary_selector": ".summary",
            },
        },
    )

    items = await HTMLListCollector(fetcher).collect(context)

    assert [item.title for item in items] == [
        "人工智能行业标准正式发布",
        "优秀应用案例征集通知",
        "第二页行业动态",
    ]
    assert all(item.canonical_url.startswith("https://example.com/") for item in items)
    assert items[0].published_at is not None
    assert items[0].summary == "标准覆盖智能体产品的基础评测要求。"
    assert [request[0] for request in fetcher.requests] == [first_url, second_url]


@pytest.mark.asyncio
async def test_html_selector_mode_can_pair_visible_titles_with_embedded_links() -> None:
    url = "https://example.com/"
    html = b"""
        <div class="news"><h3>Visible server-rendered news title</h3><span>2026-07-17</span></div>
        <script>self.data = {\"title\":\"Visible server-rendered news title\",\"external_url\":\"https://example.com/article/1\"}</script>
    """
    fetcher = FixtureFetcher({url: html})
    context = CollectContext(
        source_url=url,
        config={
            "allowed_domains": ["example.com"],
            "discovery": {"mode": "selectors"},
            "extraction": {
                "item_selector": ".news",
                "title_selector": "h3",
                "date_selector": "span",
                "embedded_title_key": "title",
                "embedded_link_key": "external_url",
            },
        },
    )

    items = await HTMLListCollector(fetcher).collect(context)

    assert len(items) == 1
    assert items[0].canonical_url == "https://example.com/article/1"
    assert items[0].published_at is not None


@pytest.mark.asyncio
async def test_html_link_filter_rejects_navigation_assets_and_external_domains() -> None:
    url = "https://example.com/"
    fetcher = FixtureFetcher({url: (FIXTURES / "sample_home.html").read_bytes()})
    context = CollectContext(
        source_url=url,
        config={
            "allowed_domains": ["example.com"],
            "discovery": {
                "mode": "link_filter",
                "include_text": ["人工智能", "案例", "成果", "通知"],
                "exclude_url_patterns": ["/login", "/contact"],
            },
        },
    )

    items = await HTMLListCollector(fetcher).collect(context)

    assert [item.title for item in items] == [
        "联盟发布人工智能产业最新研究成果",
        "关于开展优秀人工智能案例征集的通知",
    ]
    assert all(item.published_at is not None for item in items)
    assert items[0].summary == "报告总结了产业应用的最新进展。"


@pytest.mark.asyncio
async def test_html_collector_bounds_results_and_isolates_malformed_links() -> None:
    url = "https://example.com/"
    html = b"""
        <a href="https://[malformed">Malformed link should be skipped</a>
        <a href="/article/1">First valid article title</a>
        <a href="/article/2">Second valid article title</a>
        <a href="/article/3">Third valid article title</a>
    """
    fetcher = FixtureFetcher({url: html})

    items = await HTMLListCollector(fetcher).collect(
        CollectContext(
            source_url=url,
            config={
                "allowed_domains": ["example.com"],
                "discovery": {"mode": "link_filter", "max_items": 2},
            },
        )
    )

    assert [item.title for item in items] == [
        "First valid article title",
        "Second valid article title",
    ]


@pytest.mark.asyncio
async def test_html_allowed_domains_accept_root_and_subdomain_but_not_forged_suffix() -> None:
    url = "https://aiiaorg.cn/"
    html = b"""
        <a href="https://aiiaorg.cn/article/1">Root domain article title</a>
        <a href="https://news.aiiaorg.cn/article/2">Subdomain article title</a>
        <a href="https://evil-aiiaorg.cn/article/3">Forged suffix article title</a>
    """
    fetcher = FixtureFetcher({url: html})

    items = await HTMLListCollector(fetcher).collect(
        CollectContext(
            source_url=url,
            config={
                "allowed_domains": ["aiiaorg.cn"],
                "allow_subdomains": True,
                "discovery": {"mode": "link_filter"},
            },
        )
    )

    assert [item.canonical_url for item in items] == [
        "https://aiiaorg.cn/article/1",
        "https://news.aiiaorg.cn/article/2",
    ]


@pytest.mark.asyncio
async def test_html_pagination_deduplicates_cycles_before_queueing() -> None:
    first_url = "https://example.com/news"
    second_url = "https://example.com/news?page=2"
    first_page = b"""
        <div class="item"><a href="/article/1">First page article</a></div>
        <a class="next" href="/news">Current page</a>
        <a class="next" href="/news?page=2">Next page</a>
        <a class="next" href="/news?page=2">Duplicate next page</a>
    """
    second_page = b"""
        <div class="item"><a href="/article/2">Second page article</a></div>
        <a class="next" href="/news">Back to first page</a>
    """
    fetcher = FixtureFetcher({first_url: first_page, second_url: second_page})

    items = await HTMLListCollector(fetcher).collect(
        CollectContext(
            source_url=first_url,
            config={
                "allowed_domains": ["example.com"],
                "discovery": {
                    "mode": "selectors",
                    "max_pages": 10,
                    "max_depth": 3,
                    "pagination_selector": "a.next",
                },
                "extraction": {"item_selector": ".item", "link_selector": "a"},
            },
        )
    )

    assert [item.title for item in items] == ["First page article", "Second page article"]
    assert [request[0] for request in fetcher.requests] == [first_url, second_url]


@pytest.mark.asyncio
async def test_github_collector_uses_public_api_and_ignores_assets_and_prereleases() -> None:
    api_url = "https://api.github.com/repos/QwenLM/Qwen-Agent/releases?per_page=30"
    fetcher = FixtureFetcher({api_url: (FIXTURES / "github_releases.json").read_bytes()})

    items = await GitHubReleaseCollector(fetcher).collect(
        CollectContext(source_url="https://github.com/QwenLM/Qwen-Agent/releases")
    )

    assert len(items) == 1
    assert items[0].title == "Qwen-Agent v0.1.0"
    assert items[0].published_at is not None
    assert items[0].summary == "Highlights Added tool support and fixes."
    assert "assets" not in items[0].extra
    assert fetcher.requests[0][1] is not None
    assert fetcher.requests[0][1]["Accept"] == "application/vnd.github+json"


@pytest.mark.asyncio
async def test_github_collector_falls_back_to_public_atom_when_api_is_rate_limited() -> None:
    feed_url = "https://github.com/QwenLM/Qwen-Agent/releases.atom"
    fetcher = RateLimitedGitHubFetcher({feed_url: (FIXTURES / "sample_atom.xml").read_bytes()})

    items = await GitHubReleaseCollector(fetcher).collect(
        CollectContext(source_url="https://github.com/QwenLM/Qwen-Agent/releases")
    )

    assert len(items) == 1
    assert items[0].extra == {
        "api_fallback": "atom_rate_limit",
        "prerelease": False,
        "tag_name": "Atom release entry",
    }
    assert [request[0] for request in fetcher.requests] == [
        "https://api.github.com/repos/QwenLM/Qwen-Agent/releases?per_page=30",
        feed_url,
    ]


@pytest.mark.asyncio
async def test_github_collector_does_not_fallback_for_ordinary_forbidden_response() -> None:
    fetcher = ForbiddenGitHubFetcher({})

    with pytest.raises(ForbiddenFetchError):
        await GitHubReleaseCollector(fetcher).collect(
            CollectContext(source_url="https://github.com/QwenLM/Qwen-Agent/releases")
        )

    assert [request[0] for request in fetcher.requests] == [
        "https://api.github.com/repos/QwenLM/Qwen-Agent/releases?per_page=30"
    ]


def test_registry_constructs_by_collector_name_and_accepts_extensions() -> None:
    fetcher = FixtureFetcher({})
    source = Source(
        name="Example",
        source_type=SourceType.RSS,
        start_url="https://example.com/feed",
        collector_name="rss",
        collector_config={},
        origin=SourceOrigin.PRESET,
    )
    registry = default_collector_registry()

    assert isinstance(registry.create(source, fetcher), RSSCollector)
    assert registry.names() == (
        "case_hub",
        "cls_topic",
        "document_hub",
        "github_release",
        "html_list",
        "rss",
        "single_page_changelog",
    )

    custom_registry = CollectorRegistry()
    custom_registry.register("rss", RSSCollector)
    assert isinstance(custom_registry.create(source, fetcher), RSSCollector)
