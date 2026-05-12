"""SF Funcheap RSS event scraper."""

from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta

from app.sources.rss import fetch_rss
from app.storage import NewEvent

_FUNCHEAP_RSS_URL = "https://sf.funcheap.com/feed/"

_RE_DATE_IN_PARENS = re.compile(
    r"\(([A-Za-z]+ \d{1,2},\s*\d{4})\)\s*$"
)
_RE_MONTH_DAY_YEAR = re.compile(
    r"([A-Za-z]+ \d{1,2},?\s*\d{4})"
)
_GENERIC_TITLES = re.compile(
    r"^(search|events?|calendar|san francisco|sf events?|bay area)\s*$",
    re.IGNORECASE,
)
_CUTOFF_DAYS = 60


def normalize_funcheap_title_and_date(
    title: str, pub_date_str: str
) -> tuple[str, str]:
    """Strip embedded date from title and return (clean_title, date_str)."""
    match = _RE_DATE_IN_PARENS.search(title)
    if match:
        clean = title[: match.start()].strip()
        return clean, match.group(1)
    return title.strip(), pub_date_str


def _parse_pub_date(pub_date_str: str) -> datetime | None:
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z"):
        try:
            return datetime.strptime(pub_date_str, fmt)
        except ValueError:
            pass
    return None


async def fetch_funcheap_events() -> list[NewEvent]:
    items = await fetch_rss(_FUNCHEAP_RSS_URL)
    cutoff = datetime.now(UTC) - timedelta(days=_CUTOFF_DAYS)
    results: list[NewEvent] = []

    for item in items:
        title = item.title.strip()
        if not title or _GENERIC_TITLES.match(title):
            continue

        parsed_dt = _parse_pub_date(item.pub_date)
        pub_date_str = (
            parsed_dt.strftime("%B %d, %Y").lstrip("0").replace(" 0", " ")
            if parsed_dt
            else item.pub_date
        )

        if parsed_dt and parsed_dt < cutoff:
            continue

        clean_title, date_str = normalize_funcheap_title_and_date(title, pub_date_str)
        if not clean_title or _GENERIC_TITLES.match(clean_title):
            continue

        description = item.description.strip() if item.description else None
        if description and len(description) > 300:
            description = description[:300] + "…"

        results.append(
            NewEvent(
                title=clean_title,
                location="San Francisco",
                date=date_str,
                description=description or None,
                source_url=item.link or None,
            )
        )

    return results
