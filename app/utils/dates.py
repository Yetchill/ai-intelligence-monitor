"""Best-effort date parsing for feed and list metadata."""

from datetime import UTC, datetime

import dateparser


def parse_datetime(value: str | None) -> datetime | None:
    """Parse a human-facing date and normalize aware results to UTC."""

    if not value or not value.strip():
        return None
    parsed = dateparser.parse(
        value,
        settings={
            "RETURN_AS_TIMEZONE_AWARE": True,
            "TIMEZONE": "UTC",
            "TO_TIMEZONE": "UTC",
            "PREFER_DAY_OF_MONTH": "first",
        },
    )
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)
