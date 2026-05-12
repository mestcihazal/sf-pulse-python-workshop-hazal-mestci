"""California Academy of Sciences event scraper."""

from __future__ import annotations

from app.sources.famsf import parse_museum_events
from app.sources.http import fetch_url
from app.storage import NewEvent

_CAL_ACADEMY_URL = "https://www.calacademy.org/events"


async def fetch_cal_academy_events() -> list[NewEvent]:
    html = await fetch_url(_CAL_ACADEMY_URL)
    return parse_museum_events(html, _CAL_ACADEMY_URL, "California Academy of Sciences")
