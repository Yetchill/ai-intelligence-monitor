"""HttpFetcher status categories and retry behavior."""

from collections.abc import Callable

import httpx
import pytest

from app.fetchers.errors import (
    FetchTimeoutError,
    ForbiddenFetchError,
    NotFoundFetchError,
    RateLimitFetchError,
)
from app.fetchers.http import HttpFetcher


@pytest.mark.asyncio
async def test_fetcher_sets_user_agent_and_returns_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["User-Agent"].startswith("AIIntelligenceMonitor/")
        return httpx.Response(200, text="ok", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        fetcher = HttpFetcher(client=client, request_interval_seconds=0)
        result = await fetcher.fetch("https://example.com/feed")

    assert result.text == "ok"
    assert result.status_code == 200


@pytest.mark.asyncio
async def test_fetcher_retries_5xx_with_exponential_policy() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503 if attempts < 3 else 200, text="ready", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        fetcher = HttpFetcher(client=client, request_interval_seconds=0, max_retries=2)
        result = await fetcher.fetch("https://example.com/api")

    assert attempts == 3
    assert result.text == "ready"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "headers", "expected_error"),
    [
        (403, {}, ForbiddenFetchError),
        (404, {}, NotFoundFetchError),
        (429, {"Retry-After": "60"}, RateLimitFetchError),
        (403, {"X-RateLimit-Remaining": "0"}, RateLimitFetchError),
    ],
)
async def test_fetcher_distinguishes_status_failures(
    status: int,
    headers: dict[str, str],
    expected_error: type[Exception],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, headers=headers, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        fetcher = HttpFetcher(client=client, request_interval_seconds=0, max_retries=0)
        with pytest.raises(expected_error):
            await fetcher.fetch("https://example.com/resource")


@pytest.mark.asyncio
async def test_fetcher_distinguishes_timeout() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    transport_handler: Callable[[httpx.Request], httpx.Response] = handler
    async with httpx.AsyncClient(transport=httpx.MockTransport(transport_handler)) as client:
        fetcher = HttpFetcher(client=client, request_interval_seconds=0, max_retries=0)
        with pytest.raises(FetchTimeoutError):
            await fetcher.fetch("https://example.com/slow")
