"""Campaign faction reputation — account_state_json.reputation (APP-100)."""

from __future__ import annotations

import json
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any

from tomb_gm.services.economy import get_account_state, save_account_state

FACTIONS_REL = Path("data") / "factions" / "factions.json"

KNOWN_MECHANICAL_KEYS = frozenset({
    "holt_advance_dc_modifier",
    "holt_advance_cap_bonus",
    "registry_stamp_discount",
    "verdant_travel_tier_bump",
})


class FactionError(ValueError):
    pass


@lru_cache(maxsize=4)
def _load_registry_cached(content_root_str: str) -> dict[str, Any]:
    path = Path(content_root_str) / FACTIONS_REL
    if not path.is_file():
        raise FactionError(f"Missing faction registry: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    by_id = {str(f["id"]): f for f in data.get("factions", []) if isinstance(f, dict) and f.get("id")}
    return {"rulesVersion": data.get("rulesVersion"), "by_id": by_id, "factions": list(by_id.values())}


def load_faction_registry(content_root: Path) -> dict[str, Any]:
    return _load_registry_cached(str(content_root.resolve()))


def faction_ids(content_root: Path) -> list[str]:
    return list(load_faction_registry(content_root)["by_id"].keys())


def ensure_reputation_defaults(state: dict[str, Any], content_root: Path) -> dict[str, int]:
    """Ensure account_state_json.reputation has all canon factions defaulting to 0."""
    rep = state.setdefault("reputation", {})
    if not isinstance(rep, dict):
        rep = {}
        state["reputation"] = rep
    for fid in faction_ids(content_root):
        rep.setdefault(fid, 0)
    return rep  # type: ignore[return-value]


def _load_rep_state(
    conn: sqlite3.Connection,
    campaign_slug: str,
    content_root: Path,
    *,
    persist_defaults: bool = True,
) -> dict[str, int]:
    state = get_account_state(conn, campaign_slug)
    needed = set(faction_ids(content_root))
    existing = state.get("reputation") if isinstance(state.get("reputation"), dict) else {}
    if needed - set(existing.keys()):
        rep_map = ensure_reputation_defaults(state, content_root)
        if persist_defaults:
            save_account_state(conn, campaign_slug, state)
        return rep_map
    return ensure_reputation_defaults(state, content_root)


def _faction_def(content_root: Path, faction_id: str) -> dict[str, Any]:
    reg = load_faction_registry(content_root)
    faction = reg["by_id"].get(faction_id)
    if not faction:
        raise FactionError(f"Unknown faction: {faction_id}")
    return faction


def get_rep(conn: sqlite3.Connection, campaign_slug: str, faction_id: str, *, content_root: Path) -> int:
    _faction_def(content_root, faction_id)
    rep_map = _load_rep_state(conn, campaign_slug, content_root)
    return int(rep_map.get(faction_id, 0))


def adjust_rep(
    conn: sqlite3.Connection,
    campaign_slug: str,
    faction_id: str,
    delta: int,
    reason: str,
    *,
    content_root: Path,
    source: str | None = None,
) -> dict[str, Any]:
    faction = _faction_def(content_root, faction_id)
    rep_min = int(faction.get("repMin", -3))
    rep_max = int(faction.get("repMax", 3))
    state = get_account_state(conn, campaign_slug)
    rep_map = ensure_reputation_defaults(state, content_root)
    before = int(rep_map.get(faction_id, 0))
    after = max(rep_min, min(rep_max, before + int(delta)))
    rep_map[faction_id] = after
    save_account_state(conn, campaign_slug, state)
    tier = tier_for(content_root, faction_id, after)
    return {
        "ok": True,
        "faction_id": faction_id,
        "before": before,
        "after": after,
        "delta_applied": after - before,
        "reason": reason,
        "source": source,
        "tier": tier.get("label"),
        "mechanicalKeys": list(tier.get("mechanicalKeys") or []),
    }


def _tier_active(tier: dict[str, Any], rep: int) -> bool:
    op = tier.get("repOp", "eq")
    threshold = int(tier["rep"])
    if op == "lte":
        return rep <= threshold
    if op == "gte":
        return rep >= threshold
    return rep == threshold


def tier_for(content_root: Path, faction_id: str, rep: int) -> dict[str, Any]:
    faction = _faction_def(content_root, faction_id)
    tiers = faction.get("tiers") or []
    threshold_tiers = [t for t in tiers if t.get("repOp") in ("lte", "gte")]
    if threshold_tiers:
        active = [t for t in threshold_tiers if _tier_active(t, rep)]
        if active:
            # Prefer the strongest threshold match (lte: lowest rep; gte: highest rep).
            lte = [t for t in active if t.get("repOp") == "lte"]
            gte = [t for t in active if t.get("repOp") == "gte"]
            if lte:
                return min(lte, key=lambda t: int(t["rep"]))
            if gte:
                return max(gte, key=lambda t: int(t["rep"]))
        for t in tiers:
            if t.get("repOp", "eq") == "eq" and int(t["rep"]) == rep:
                return t
        for t in tiers:
            if t.get("repOp", "eq") == "eq" and int(t["rep"]) == 0:
                return t
        return tiers[0]

    exact = next((t for t in tiers if int(t.get("rep", 0)) == rep), None)
    if exact:
        return exact
    ladder = sorted(tiers, key=lambda t: int(t["rep"]))
    eligible = [t for t in ladder if int(t["rep"]) <= rep]
    return eligible[-1] if eligible else ladder[0]


def resolve_mechanical_key(key: str, rep_state: dict[str, int]) -> int | None:
    """Return numeric modifier when the key is active, else None."""
    if key == "holt_advance_dc_modifier":
        if rep_state.get("knights-of-breley", 0) <= -2:
            return 2
        return None
    if key == "holt_advance_cap_bonus":
        if rep_state.get("knights-of-breley", 0) >= 2:
            return 25
        return None
    if key == "registry_stamp_discount":
        if rep_state.get("delvers-registry", 0) >= 1:
            return 5
        return None
    if key == "verdant_travel_tier_bump":
        if rep_state.get("verdant-vale", 0) <= -2:
            return 1
        return None
    return None


def _surface_root(address: str) -> str:
    for sep in ("-UG-", "-EP", "-BV", "-SK"):
        if sep in address:
            return address.split(sep, 1)[0]
    return address


def _address_matches(address: str | None, hubs: list[str]) -> bool:
    if not address:
        return False
    surface = _surface_root(address)
    for hub in hubs:
        if address == hub or address.startswith(f"{hub}-") or surface == hub or surface.startswith(f"{hub}-"):
            return True
    return False


def effects_at(
    content_root: Path,
    rep_state: dict[str, int],
    *,
    address: str | None = None,
) -> dict[str, int]:
    """Active mechanical keys and resolved numeric values."""
    reg = load_faction_registry(content_root)
    active: dict[str, int] = {}
    for faction in reg["factions"]:
        fid = str(faction["id"])
        hubs = list(faction.get("hubAddresses") or [])
        if address is not None and hubs and not _address_matches(address, hubs):
            continue
        rep = int(rep_state.get(fid, 0))
        tier = tier_for(content_root, fid, rep)
        for key in tier.get("mechanicalKeys") or []:
            value = resolve_mechanical_key(str(key), rep_state)
            if value is not None:
                active[str(key)] = value
    return active


def reputation_status_summary(
    conn: sqlite3.Connection,
    content_root: Path,
    campaign_slug: str,
    *,
    address: str | None = None,
) -> dict[str, Any]:
    rep_map = _load_rep_state(conn, campaign_slug, content_root)
    summary: dict[str, Any] = {}
    for fid, value in rep_map.items():
        tier = tier_for(content_root, fid, int(value))
        summary[fid] = {
            "value": int(value),
            "tier": tier.get("label"),
            "effects": list(tier.get("effects") or []),
            "mechanicalKeys": list(tier.get("mechanicalKeys") or []),
        }
    summary["_active_effects"] = effects_at(content_root, rep_map, address=address)
    return summary


def list_factions_with_rep(
    conn: sqlite3.Connection,
    content_root: Path,
    campaign_slug: str,
) -> list[dict[str, Any]]:
    rep_map = _load_rep_state(conn, campaign_slug, content_root)
    reg = load_faction_registry(content_root)
    rows: list[dict[str, Any]] = []
    for faction in reg["factions"]:
        fid = str(faction["id"])
        rep = int(rep_map.get(fid, 0))
        tier = tier_for(content_root, fid, rep)
        rows.append(
            {
                "id": fid,
                "displayName": faction.get("displayName", fid),
                "repMin": faction.get("repMin", -3),
                "repMax": faction.get("repMax", 3),
                "hubAddresses": list(faction.get("hubAddresses") or []),
                "rep": rep,
                "tier": tier.get("label"),
                "effects": list(tier.get("effects") or []),
                "mechanicalKeys": list(tier.get("mechanicalKeys") or []),
            }
        )
    return rows
