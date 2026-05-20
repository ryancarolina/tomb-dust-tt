"""Hub location gates for stash, vendors, and fence services."""

from __future__ import annotations

import sqlite3
from typing import Any

from tomb_gm.services.content import ContentService


class HubError(ValueError):
    pass


def active_delver_id(conn: sqlite3.Connection, campaign_slug: str) -> str | None:
    row = conn.execute(
        "SELECT id FROM characters "
        "WHERE campaign_slug = ? AND slot IS NOT NULL AND alive = 1 "
        "ORDER BY slot ASC LIMIT 1",
        (campaign_slug,),
    ).fetchone()
    return str(row["id"]) if row else None


def party_surface_state(conn: sqlite3.Connection, session_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT address, mode FROM party_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if not row:
        raise HubError("no party state for session")
    return {"address": row["address"], "mode": row["mode"]}


def cell_services(content: ContentService, address: str) -> dict[str, Any]:
    cell = content.get_cell(address)
    if not cell:
        return {}
    services = cell.get("services")
    return dict(services) if isinstance(services, dict) else {}


def hub_services_available(
    conn: sqlite3.Connection,
    content: ContentService,
    session_id: str,
    *,
    require_stash: bool = False,
    require_vendor: str | None = None,
    require_fence: bool = False,
) -> dict[str, Any]:
    """Return service flags when party is on surface at a hub cell; else raise HubError."""
    ps = party_surface_state(conn, session_id)
    if ps["mode"] != "surface":
        raise HubError(f"hub services blocked: party mode is {ps['mode']!r} (need surface)")

    services = cell_services(content, str(ps["address"]))
    if require_stash and not services.get("stash"):
        raise HubError(f"stash unavailable at {ps['address']}")
    if require_vendor:
        vendor_ids = list(services.get("vendorIds") or [])
        if require_vendor not in vendor_ids:
            raise HubError(f"vendor {require_vendor!r} unavailable at {ps['address']}")
    if require_fence and not services.get("fence"):
        raise HubError(f"fence unavailable at {ps['address']}")

    return {
        "ok": True,
        "address": ps["address"],
        "mode": ps["mode"],
        "services": services,
    }
