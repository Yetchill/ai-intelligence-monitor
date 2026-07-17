"""Safe URL resolution and canonicalization helpers."""

from collections.abc import Collection
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

TRACKING_QUERY_KEYS = {
    "dclid",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
    "msclkid",
}


def is_http_url(url: str) -> bool:
    """Return whether a URL is an absolute HTTP(S) URL."""

    parts = urlsplit(url.strip())
    return parts.scheme.lower() in {"http", "https"} and bool(parts.hostname)


def canonicalize_url(
    url: str,
    *,
    base_url: str | None = None,
    keep_query_params: Collection[str] | None = None,
) -> str | None:
    """Resolve and normalize a web URL, returning ``None`` for unsafe schemes.

    When ``keep_query_params`` is omitted, non-tracking parameters are retained. When it is
    supplied, only the named non-tracking parameters are retained.
    """

    candidate = urljoin(base_url, url) if base_url else url
    candidate = candidate.strip()
    parts = urlsplit(candidate)
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"} or not parts.hostname:
        return None

    hostname = parts.hostname.lower().rstrip(".")
    try:
        hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError:
        return None

    port = parts.port
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    netloc = hostname if port is None or default_port else f"{hostname}:{port}"

    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/") or "/"

    allowed = set(keep_query_params) if keep_query_params is not None else None
    query_items: list[tuple[str, str]] = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        normalized_key = key.lower()
        if normalized_key.startswith("utm_") or normalized_key in TRACKING_QUERY_KEYS:
            continue
        if allowed is not None and key not in allowed:
            continue
        query_items.append((key, value))
    query_items.sort()

    return urlunsplit((scheme, netloc, path, urlencode(query_items, doseq=True), ""))


def resolve_url(
    base_url: str,
    link: str,
    *,
    keep_query_params: Collection[str] | None = None,
) -> str | None:
    """Resolve a possibly-relative link and apply canonicalization."""

    return canonicalize_url(link, base_url=base_url, keep_query_params=keep_query_params)
