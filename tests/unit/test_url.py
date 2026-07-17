"""URL resolution and canonicalization tests."""

import pytest

from app.utils.url import canonicalize_url, is_http_url, resolve_url


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "HTTPS://Example.COM:443/news/item/?b=2&utm_source=test&a=1#section",
            "https://example.com/news/item?a=1&b=2",
        ),
        ("http://example.com:80/", "http://example.com/"),
        ("https://example.com/path///", "https://example.com/path"),
        ("https://例子.测试/新闻", "https://xn--fsqu00a.xn--0zwm56d/新闻"),
    ],
)
def test_canonicalize_url(raw: str, expected: str) -> None:
    assert canonicalize_url(raw) == expected


def test_resolve_relative_url_and_remove_fragment() -> None:
    assert (
        resolve_url("https://example.com/news/index.html", "../article/1#intro")
        == "https://example.com/article/1"
    )


def test_configured_query_parameter_allowlist() -> None:
    assert (
        canonicalize_url(
            "https://example.com/search?page=2&category=ai&session=secret&utm_medium=email",
            keep_query_params={"page", "category"},
        )
        == "https://example.com/search?category=ai&page=2"
    )


@pytest.mark.parametrize(
    "raw",
    ["javascript:alert(1)", "mailto:user@example.com", "ftp://example.com/file", "/relative"],
)
def test_non_http_urls_are_rejected(raw: str) -> None:
    assert canonicalize_url(raw) is None
    assert is_http_url(raw) is False
