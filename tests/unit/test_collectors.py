"""Offline collector tests backed by fixed RSS, HTML, and JSON samples."""

from collections.abc import Mapping
from pathlib import Path

import pytest

from app.collectors.github_release import GitHubReleaseCollector
from app.collectors.html_list import HTMLListCollector
from app.collectors.registry import CollectorRegistry, default_collector_registry
from app.collectors.rss import RSSCollector
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
        "document_hub",
        "github_release",
        "html_list",
        "rss",
        "single_page_changelog",
    )

    custom_registry = CollectorRegistry()
    custom_registry.register("rss", RSSCollector)
    assert isinstance(custom_registry.create(source, fetcher), RSSCollector)
