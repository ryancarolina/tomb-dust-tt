from __future__ import annotations

import json
from typing import Any

from tomb_gm.services.content import ContentService
from tomb_gm.services.site_resolve import _slug

_APOSTROPHE_FOLDS = str.maketrans("", "", "'\u2019")


def _fold_apostrophes(text: str) -> str:
    return text.translate(_APOSTROPHE_FOLDS)


def _display_match_score(
    query_norm: str, query_slug: str, *, address: str, display_name: str
) -> int:
    folded_query = _fold_apostrophes(query_norm)
    folded_name = _fold_apostrophes(display_name.lower())
    name_slug = _slug(_fold_apostrophes(display_name))
    addr_lower = address.lower()
    if query_norm == addr_lower or query_slug == _slug(address):
        return 100
    if folded_query == folded_name or query_slug == name_slug:
        return 90
    if query_slug and (query_slug in name_slug or name_slug in query_slug):
        return 70
    if folded_query and folded_query in folded_name:
        return 60
    return 0


def _score_surface_candidate(
    query_norm: str,
    query_slug: str,
    *,
    address: str,
    display_name: str,
    trade_route: str | None,
) -> int:
    display_score = _display_match_score(
        query_norm, query_slug, address=address, display_name=display_name
    )
    route_score = 0
    if trade_route and display_score > 0:
        route_slug = _slug(trade_route)
        if (
            query_slug == route_slug
            or query_slug in route_slug
            or route_slug in query_slug
        ):
            route_score = 80
    return max(display_score, route_score)


def _surface_exit_hints(content: ContentService, exits: list[str]) -> str:
    surface_exits = [
        addr
        for addr in exits
        if not (content.get_cell(addr) or {}).get("layerStack")
    ]
    if not surface_exits:
        return "No legal surface exits from here."
    parts: list[str] = []
    for addr in surface_exits:
        cell = content.get_cell(addr) or {}
        display = str(cell.get("displayName") or addr)
        parts.append(f"{addr} ({display})")
    return "Legal surface exits: " + "; ".join(parts)


def _candidate_pool(
    content: ContentService,
    exits: list[str],
    *,
    from_address: str,
    query_norm: str,
    query_slug: str,
    surface_only: bool,
) -> list[tuple[int, str, str]]:
    exact_current = query_norm == from_address.lower() or query_slug == _slug(from_address)
    pool: list[tuple[int, str, str]] = []
    for addr in exits:
        cell = content.get_cell(addr)
        if not cell:
            continue
        layered = bool(cell.get("layerStack"))
        if surface_only and layered:
            continue
        if not surface_only and not layered:
            continue
        if addr == from_address and not exact_current:
            continue
        display = str(cell.get("displayName") or addr)
        trade_route = cell.get("tradeRoute")
        route = str(trade_route) if trade_route else None
        score = _score_surface_candidate(
            query_norm,
            query_slug,
            address=addr,
            display_name=display,
            trade_route=route,
        )
        if score > 0:
            pool.append((score, addr, display))
    return pool


def _pick_best(
    candidates: list[tuple[int, str, str]],
) -> tuple[dict[str, Any] | None, list[tuple[int, str, str]]]:
    if not candidates:
        return None, []
    candidates.sort(key=lambda item: (-item[0], item[1]))
    best_score = candidates[0][0]
    best = [c for c in candidates if c[0] == best_score]
    if len(best) > 1:
        options = [{"address": addr, "displayName": name} for _, addr, name in best]
        return {
            "ambiguous": True,
            "options": options,
        }, best
    _, address, display = best[0]
    return {
        "ok": True,
        "address": address,
        "displayName": display,
    }, best


def resolve_surface_address(
    content: ContentService,
    query: str,
    *,
    from_address: str,
) -> dict[str, Any]:
    """Resolve a friendly surface place name to a legal exit AV-GRID id."""
    raw = query.strip()
    if not raw:
        return {"ok": False, "error": "EMPTY_QUERY", "query": raw}

    query_norm = raw.lower()
    query_slug = _slug(_fold_apostrophes(raw))
    world = WorldService(content)
    exits = world.legal_exits(from_address)
    if exits is None:
        return {
            "ok": False,
            "error": "UNKNOWN_FROM_ADDRESS",
            "query": raw,
            "message": f"Unknown AV-GRID address: {from_address}",
        }

    exit_set = {e.lower() for e in exits}
    if query_norm in exit_set:
        address = next(e for e in exits if e.lower() == query_norm)
        cell = content.get_cell(address) or {}
        return {
            "ok": True,
            "address": address,
            "displayName": str(cell.get("displayName") or address),
            "resolved_from": raw,
        }

    surface_candidates = _candidate_pool(
        content,
        exits,
        from_address=from_address,
        query_norm=query_norm,
        query_slug=query_slug,
        surface_only=True,
    )
    result, _ = _pick_best(surface_candidates)
    if result and result.get("ambiguous"):
        options = result["options"]
        return {
            "ok": False,
            "error": "AMBIGUOUS_ADDRESS",
            "query": raw,
            "options": options,
            "message": f"'{raw}' matches multiple exits — pick one by AV-GRID address.",
        }
    if result and result.get("ok"):
        return {**result, "resolved_from": raw}

    layered_candidates = _candidate_pool(
        content,
        exits,
        from_address=from_address,
        query_norm=query_norm,
        query_slug=query_slug,
        surface_only=False,
    )
    layered_result, _ = _pick_best(layered_candidates)
    if layered_result and layered_result.get("ambiguous"):
        options = layered_result["options"]
        return {
            "ok": False,
            "error": "AMBIGUOUS_ADDRESS",
            "query": raw,
            "options": options,
            "message": f"'{raw}' matches multiple layered sites — pick one by AV-GRID address.",
        }
    if layered_result and layered_result.get("ok"):
        display = layered_result.get("displayName") or layered_result["address"]
        return {
            "ok": False,
            "error": "USE_ENTER_DUNGEON",
            "query": raw,
            "message": (
                f"'{raw}' matches layered site {layered_result['address']} ({display}). "
                "Use enter_dungeon(site_address) or compass_exits — not world_travel."
            ),
        }

    hints = _surface_exit_hints(content, exits)
    return {
        "ok": False,
        "error": "UNKNOWN_ADDRESS",
        "query": raw,
        "message": f"No surface exit matches '{raw}'. {hints}",
    }


def _format_surface_id(column: int, row: str) -> str:
    return f"{column}-{row}"


def _adjacent_surface_ids(content: ContentService, address: str) -> list[str]:
    entry = content.get_cell(address)
    if not entry or entry.get("layerStack"):
        return []
    col = int(entry["column"])
    row = str(entry["row"])
    row_ord = ord(row)
    candidates = [
        _format_surface_id(col - 1, row),
        _format_surface_id(col + 1, row),
    ]
    if row_ord > ord("A"):
        candidates.append(_format_surface_id(col, chr(row_ord - 1)))
    if row_ord < ord("Z"):
        candidates.append(_format_surface_id(col, chr(row_ord + 1)))
    addresses = content.load_av_grid()["addresses"]
    out: list[str] = []
    for cid in candidates:
        cell = addresses.get(cid)
        if cell and not cell.get("layerStack"):
            out.append(cid)
    return sorted(out)


class WorldService:
    def __init__(self, content: ContentService) -> None:
        self.content = content

    def unknown_address_error(self, address: str) -> dict[str, Any]:
        return {
            "ok": False,
            "error": "UNKNOWN_ADDRESS",
            "address": address,
            "message": f"Unknown AV-GRID address: {address}",
        }

    def legal_exits(self, address: str) -> list[str] | None:
        entry = self.content.get_cell(address)
        if not entry:
            return None
        targets: set[str] = set()
        parent = entry.get("parent")
        if parent:
            targets.add(parent)
        for child in entry.get("childAddresses", []):
            targets.add(child)
        if not entry.get("layerStack"):
            targets.update(_adjacent_surface_ids(self.content, address))
        return sorted(targets)

    def can_travel(self, from_address: str, to_address: str) -> tuple[bool, str | None]:
        if not self.content.get_cell(from_address):
            return False, "UNKNOWN_FROM_ADDRESS"
        if not self.content.get_cell(to_address):
            return False, "UNKNOWN_ADDRESS"
        if from_address == to_address:
            return True, None
        exits = self.legal_exits(from_address)
        if exits is None:
            return False, "UNKNOWN_FROM_ADDRESS"
        if to_address not in exits:
            return False, "INVALID_TRAVEL"
        return True, None

    def stamp_validity(
        self, address: str, stamp_json: str | None
    ) -> dict[str, Any]:
        entry = self.content.get_cell(address)
        if not entry:
            return {"valid": False, "reason": "unknown_address"}
        registry = entry.get("registry") or {}
        stamped_site = bool(registry.get("stamped"))
        party_stamp = json.loads(stamp_json) if stamp_json else None
        if not stamped_site:
            return {
                "valid": True,
                "required": False,
                "registryStamped": False,
                "partyStamp": party_stamp,
            }
        if party_stamp and party_stamp.get("address") == address:
            return {
                "valid": True,
                "required": True,
                "registryStamped": True,
                "partyStamp": party_stamp,
            }
        return {
            "valid": False,
            "required": True,
            "registryStamped": True,
            "partyStamp": party_stamp,
            "reason": "stamp_required_for_stamped_site",
        }

    def where_payload(
        self, address: str, *, mode: str, stamp_json: str | None
    ) -> dict[str, Any] | None:
        cell = self.content.cell_payload(address)
        if not cell:
            return None
        return {
            "address": address,
            "mode": mode,
            "cell": cell,
            "stamp": self.stamp_validity(address, stamp_json),
        }

    def wilderness_travel_needed(self, to_address: str, stamp_json: str | None) -> bool:
        entry = self.content.get_cell(to_address)
        if not entry:
            return False
        registry = entry.get("registry") or {}
        if registry.get("stamped"):
            validity = self.stamp_validity(to_address, stamp_json)
            return not validity.get("valid", True)
        return True
