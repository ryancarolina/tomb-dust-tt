"""Resolve player/LLM site references to AV-GRID addresses."""

from __future__ import annotations

import re
from typing import Any

from tomb_gm.services.content import ContentService

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(text: str) -> str:
    return _SLUG_RE.sub("-", text.lower()).strip("-")


def _normalize_query(query: str) -> str:
    return query.strip()


def _match_score(query_norm: str, query_slug: str, display_name: str, address: str) -> int:
    name_lower = display_name.lower()
    name_slug = _slug(display_name)
    addr_lower = address.lower()
    if query_norm == addr_lower or query_slug == _slug(address):
        return 100
    if query_norm == name_lower or query_slug == name_slug:
        return 90
    if query_slug and (query_slug in name_slug or name_slug in query_slug):
        return 70
    if query_norm in name_lower:
        return 60
    return 0


def resolve_site_address(
    content: ContentService,
    query: str,
    *,
    current_surface_address: str | None = None,
) -> dict[str, Any]:
    """Resolve a site slug, display name, or AV-GRID id to a canonical address."""
    raw = _normalize_query(query)
    if not raw:
        return {"ok": False, "error": "EMPTY_SITE_QUERY"}

    query_norm = raw.lower()
    query_slug = _slug(raw)
    grid = content.load_av_grid().get("addresses", {})

    if raw in grid:
        return {"ok": True, "site_address": raw, "resolved_from": raw}

    site_data = content.load_site(raw)
    if site_data and site_data.get("primaryAddress"):
        address = str(site_data["primaryAddress"])
        if address in grid:
            return {"ok": True, "site_address": address, "resolved_from": raw}

    site_data = content.load_site(query_slug)
    if site_data and site_data.get("primaryAddress"):
        address = str(site_data["primaryAddress"])
        if address in grid:
            return {"ok": True, "site_address": address, "resolved_from": raw}

    candidates: list[tuple[int, str, str]] = []

    def _consider(address: str) -> None:
        cell = grid.get(address)
        if not cell:
            return
        display = str(cell.get("displayName") or address)
        score = _match_score(query_norm, query_slug, display, address)
        if score > 0:
            candidates.append((score, address, display))

    if current_surface_address:
        surface = grid.get(current_surface_address) or {}
        for child_id in surface.get("childAddresses", []):
            _consider(str(child_id))

    if not candidates:
        for address, cell in grid.items():
            layers = cell.get("layerStack") or []
            if not layers:
                continue
            display = str(cell.get("displayName") or address)
            score = _match_score(query_norm, query_slug, display, address)
            if score > 0:
                candidates.append((score, address, display))

    if not candidates:
        return {
            "ok": False,
            "error": "UNKNOWN_SITE",
            "message": f"No site matches '{raw}'. Use an AV-GRID address (e.g. 32-C-UG-1) or call compass_exits.",
            "query": raw,
        }

    candidates.sort(key=lambda item: (-item[0], item[1]))
    best_score = candidates[0][0]
    best = [c for c in candidates if c[0] == best_score]

    if len(best) > 1:
        options = [{"address": addr, "displayName": name} for _, addr, name in best]
        return {
            "ok": False,
            "error": "AMBIGUOUS_SITE",
            "message": f"'{raw}' matches multiple sites — pick one by AV-GRID address.",
            "query": raw,
            "options": options,
        }

    _, address, display = best[0]
    return {
        "ok": True,
        "site_address": address,
        "displayName": display,
        "resolved_from": raw,
    }
