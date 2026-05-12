"""Event API endpoint tests."""

from __future__ import annotations

from httpx import AsyncClient

from app import storage


async def test_list_events_returns_all(client: AsyncClient, clean_db) -> None:
    await storage.add_event(
        storage.NewEvent(
            title="Mission Night Market",
            location="Mission District",
            date="April 15, 2026",
        ),
        pool=clean_db,
    )
    resp = await client.get("/api/events")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["title"] == "Mission Night Market"


async def test_get_event_by_id(client: AsyncClient, clean_db) -> None:
    e = await storage.add_event(
        storage.NewEvent(
            title="Bay to Breakers",
            location="Howard & Main to Great Highway",
            date="May 17, 2026",
        ),
        pool=clean_db,
    )
    resp = await client.get(f"/api/events/{e.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == e.id

    miss = await client.get("/api/events/99999")
    assert miss.status_code == 404


async def test_delete_event_requires_cron_secret(
    client: AsyncClient, clean_db, cron_headers
) -> None:
    e = await storage.add_event(
        storage.NewEvent(
            title="César Chávez Day Parade",
            location="Mission District",
            date="April 11, 2026",
        ),
        pool=clean_db,
    )
    no_secret = await client.delete(f"/api/events/{e.id}")
    assert no_secret.status_code == 401

    with_secret = await client.delete(f"/api/events/{e.id}", headers=cron_headers)
    assert with_secret.status_code == 200
    assert with_secret.json() == {"ok": True}
    assert await storage.get_event_by_id(e.id, pool=clean_db) is None
