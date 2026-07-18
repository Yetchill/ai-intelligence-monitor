"""SSRF-resistant URL validation and bounded fetching for source onboarding."""

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable, Mapping, Sequence
from urllib.parse import urljoin, urlsplit

import httpx

from app.domain.collection import FetchResult
from app.fetchers.errors import (
    FetchError,
    FetchTimeoutError,
    ForbiddenFetchError,
    HttpStatusFetchError,
    NotFoundFetchError,
    RateLimitFetchError,
    ServerFetchError,
)
from app.utils.url import canonicalize_url

MAX_SOURCE_URL_LENGTH = 2048
SAFE_PORTS = {"http": {80}, "https": {443}}
MAX_REDIRECTS = 4
MAX_RESPONSE_BYTES = 2 * 1024 * 1024

Resolver = Callable[[str], Awaitable[Sequence[str]]]


class SourceUrlSecurityError(ValueError):
    """A user-facing URL rejection that never includes local addressing details."""


class ResponseTooLargeFetchError(FetchError):
    """The response exceeded the onboarding byte limit."""


async def resolve_public_addresses(hostname: str) -> Sequence[str]:
    """Resolve both IPv4 and IPv6 without blocking the event loop."""

    def resolve() -> Sequence[str]:
        rows = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
        return tuple(dict.fromkeys(str(row[4][0]) for row in rows))

    try:
        return await asyncio.to_thread(resolve)
    except OSError as exc:
        raise SourceUrlSecurityError("无法解析该网址的主机名。") from exc


class SourceUrlGuard:
    """Normalize input and require every resolved target to be globally routable."""

    def __init__(self, resolver: Resolver = resolve_public_addresses) -> None:
        self._resolver = resolver

    def normalize(self, value: str) -> str:
        candidate = value.strip()
        if not candidate:
            raise SourceUrlSecurityError("请输入来源网址。")
        if len(candidate) > MAX_SOURCE_URL_LENGTH:
            raise SourceUrlSecurityError("网址过长, 请使用不超过 2048 个字符的地址。")
        try:
            parts = urlsplit(candidate)
            port = parts.port
        except ValueError as exc:
            raise SourceUrlSecurityError("网址格式无效。") from exc
        scheme = parts.scheme.lower()
        if scheme not in SAFE_PORTS or not parts.hostname:
            raise SourceUrlSecurityError("只允许使用 HTTP 或 HTTPS 网址。")
        if parts.username is not None or parts.password is not None:
            raise SourceUrlSecurityError("网址中不能包含用户名或密码。")
        effective_port = port or (80 if scheme == "http" else 443)
        if effective_port not in SAFE_PORTS[scheme]:
            raise SourceUrlSecurityError("该网址端口不在允许的安全端口范围内。")
        normalized = canonicalize_url(candidate)
        if normalized is None or len(normalized) > MAX_SOURCE_URL_LENGTH:
            raise SourceUrlSecurityError("网址格式无效。")
        return normalized

    async def validate(self, value: str) -> str:
        normalized = self.normalize(value)
        hostname = urlsplit(normalized).hostname or ""
        lowered = hostname.casefold().rstrip(".")
        if lowered == "localhost" or lowered.endswith(".localhost"):
            raise SourceUrlSecurityError("该网址指向不允许访问的本地或内部地址。")
        literal = _parse_address(lowered)
        addresses = (str(literal),) if literal is not None else await self._resolver(lowered)
        if not addresses:
            raise SourceUrlSecurityError("无法解析该网址的主机名。")
        for value in addresses:
            address = _parse_address(value)
            if address is None or not address.is_global:
                raise SourceUrlSecurityError("该网址指向不允许访问的本地或内部地址。")
        return normalized


class SafeHttpFetcher:
    """Fetcher used only by discovery/preview with per-hop validation and body limits."""

    def __init__(
        self,
        guard: SourceUrlGuard,
        *,
        timeout_seconds: float = 10.0,
        max_redirects: int = MAX_REDIRECTS,
        max_response_bytes: int = MAX_RESPONSE_BYTES,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._guard = guard
        self._timeout = httpx.Timeout(timeout_seconds)
        self._max_redirects = max(0, min(max_redirects, 10))
        self._max_response_bytes = max(1024, max_response_bytes)
        self._client = client or httpx.AsyncClient(timeout=self._timeout, follow_redirects=False)
        self._owns_client = client is None

    async def __aenter__(self) -> "SafeHttpFetcher":
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def fetch(
        self,
        url: str,
        *,
        headers: Mapping[str, str] | None = None,
    ) -> FetchResult:
        requested_url = await self._guard.validate(url)
        current_url = requested_url
        for redirect_count in range(self._max_redirects + 1):
            # Validate the exact redirect target but keep its path spelling for the request.
            # Some servers redirect a canonicalized ``/feed`` back to ``/feed/``.
            await self._guard.validate(current_url)
            try:
                async with self._client.stream(
                    "GET",
                    current_url,
                    headers=headers,
                    timeout=self._timeout,
                    follow_redirects=False,
                ) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location or redirect_count >= self._max_redirects:
                            raise FetchError(current_url, "网页重定向次数过多或目标无效。")
                        current_url = urljoin(current_url, location)
                        continue
                    status = response.status_code
                    if status == 403:
                        if response.headers.get("x-ratelimit-remaining") == "0":
                            raise RateLimitFetchError(current_url, "公开接口请求配额暂时耗尽。")
                        raise ForbiddenFetchError(current_url, "网站拒绝公开访问。")
                    if status == 404:
                        raise NotFoundFetchError(current_url, "网页不存在。")
                    if status == 429:
                        raise RateLimitFetchError(current_url, "网站请求频率受限。")
                    if 500 <= status <= 599:
                        raise ServerFetchError(current_url, "网站服务暂时不可用。")
                    if status >= 400:
                        raise HttpStatusFetchError(current_url, status)
                    declared = response.headers.get("content-length")
                    if (
                        declared
                        and declared.isdecimal()
                        and int(declared) > self._max_response_bytes
                    ):
                        raise ResponseTooLargeFetchError(
                            current_url, "网页响应内容超过预览大小限制。"
                        )
                    chunks: list[bytes] = []
                    total = 0
                    async for chunk in response.aiter_bytes():
                        total += len(chunk)
                        if total > self._max_response_bytes:
                            raise ResponseTooLargeFetchError(
                                current_url, "网页响应内容超过预览大小限制。"
                            )
                        chunks.append(chunk)
                    encoding = response.encoding or "utf-8"
                    return FetchResult(
                        requested_url=requested_url,
                        url=str(response.url),
                        status_code=response.status_code,
                        headers=dict(response.headers.items()),
                        content=b"".join(chunks),
                        encoding=encoding,
                    )
            except httpx.TimeoutException as exc:
                raise FetchTimeoutError(current_url, "网页响应超时, 请稍后重试。") from exc
            except httpx.RequestError as exc:
                raise FetchError(current_url, "无法安全访问该网页。") from exc
        raise FetchError(current_url, "网页重定向次数过多。")


def _parse_address(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


__all__ = [
    "MAX_RESPONSE_BYTES",
    "MAX_SOURCE_URL_LENGTH",
    "ResponseTooLargeFetchError",
    "SafeHttpFetcher",
    "SourceUrlGuard",
    "SourceUrlSecurityError",
]
