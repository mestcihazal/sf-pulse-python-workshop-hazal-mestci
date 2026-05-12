"""Fine Arts Museums of SF calendar scraper."""

from __future__ import annotations

import re

from app.sources.http import fetch_url
from app.storage import NewEvent

_FAMSF_URL = "https://www.famsf.org/visit/calendar"

_RE_TAG = re.compile(r"<[^>]+>")
_RE_WS = re.compile(r"\s+")

_GENERIC_TITLES = re.compile(
    r"^(calendar|events?|visit|menu|navigation|search|skip|home|about|shop|membership|"
    r"education|art|exhibitions?|programs?|contact|donate|buy tickets?|get tickets?|"
    r"learn more|see all|view all|de young|legion of honor|famsf)\s*$",
    re.IGNORECASE,
)

# selectors via regex patterns on raw HTML
_RE_CARD_BLOCK = re.compile(
    r'<(?:article|div)[^>]+class="[^"]*(?:event|card|listing)[^"]*"[^>]*>([\s\S]*?)</(?:article|div)>',
    re.IGNORECASE,
)
_RE_HEADING = re.compile(
    r'<h[1-6][^>]*>([\s\S]*?)</h[1-6]>',
    re.IGNORECASE,
)
_RE_DATE_TEXT = re.compile(
    r'<(?:time|span|div|p)[^>]*(?:date|time)[^>]*>([\s\S]*?)</(?:time|span|div|p)>',
    re.IGNORECASE,
)


def _clean_text(html: str) -> str:
    return _RE_WS.sub(" ", _RE_TAG.sub(" ", html)).strip()


def parse_museum_events(
    html: str,
    source_url: str,
    default_location: str,
) -> list[NewEvent]:
    """Parse event cards from a museum calendar page."""
    if not html:
        return []

    results: list[NewEvent] = []

    # Try to extract from event card blocks
    cards = _RE_CARD_BLOCK.findall(html)
    if not cards:
        # Fallback: find headings with nearby date spans
        headings = _RE_HEADING.findall(html)
        dates = _RE_DATE_TEXT.findall(html)
        for i, heading_html in enumerate(headings):
            title = _clean_text(heading_html)
            if not title or _GENERIC_TITLES.match(title) or len(title) > 120:
                continue
            date_str = _clean_text(dates[i]) if i < len(dates) else ""
            if not date_str:
                continue
            results.append(
                NewEvent(
                    title=title,
                    location=default_location,
                    date=date_str,
                    source_url=source_url,
                )
            )
        return results[:30]

    for card_html in cards[:40]:
        headings = _RE_HEADING.findall(card_html)
        if not headings:
            continue
        title = _clean_text(headings[0])
        if not title or _GENERIC_TITLES.match(title) or len(title) > 120:
            continue

        date_parts = _RE_DATE_TEXT.findall(card_html)
        date_str = _clean_text(date_parts[0]) if date_parts else ""

        # Infer location from title hints
        location = default_location
        title_lower = title.lower()
        if "legion" in title_lower:
            location = "Legion of Honor"
        elif "de young" in title_lower or "deyoung" in title_lower:
            location = "de Young Museum"

        if not date_str:
            continue

        results.append(
            NewEvent(
                title=title,
                location=location,
                date=date_str,
                source_url=source_url,
            )
        )

    return results


async def fetch_famsf_events() -> list[NewEvent]:
    html = await fetch_url(_FAMSF_URL)
    return parse_museum_events(html, _FAMSF_URL, "de Young Museum")
