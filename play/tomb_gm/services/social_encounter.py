"""Non-combat social encounter FSM (distinct from combat encounter APP-089)."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from tomb_gm.services.economy import get_account_state, save_account_state

PHASES = frozenset({"idle", "active", "contested", "resolved"})


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _encounters(state: dict[str, Any]) -> dict[str, Any]:
    state.setdefault("social_encounters", {})
    return state["social_encounters"]


def encounter_id(npc_id: str, quest_id: str | None = None) -> str:
    if quest_id:
        return f"{npc_id}:{quest_id}"
    return npc_id


def get_encounter(
    conn: sqlite3.Connection,
    campaign_slug: str,
    enc_id: str,
) -> dict[str, Any] | None:
    state = get_account_state(conn, campaign_slug)
    return _encounters(state).get(enc_id)


def _save_encounter(
    conn: sqlite3.Connection,
    campaign_slug: str,
    enc_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    state = get_account_state(conn, campaign_slug)
    encounters = _encounters(state)
    encounters[enc_id] = payload
    save_account_state(conn, campaign_slug, state)
    return payload


def _derive_disposition(margins: list[int]) -> str:
    recent = margins[-3:]
    if not recent:
        return "neutral"
    avg = sum(recent) / len(recent)
    if avg >= 3:
        return "favorable"
    if avg <= -2:
        return "wary"
    return "neutral"


def engage(
    conn: sqlite3.Connection,
    campaign_slug: str,
    *,
    npc_id: str,
    quest_id: str | None = None,
) -> dict[str, Any]:
    enc_id = encounter_id(npc_id, quest_id)
    existing = get_encounter(conn, campaign_slug, enc_id) or {}
    payload = {
        "phase": "active",
        "npc_id": npc_id,
        "quest_id": quest_id,
        "disposition": existing.get("disposition", "neutral"),
        "margins": list(existing.get("margins") or []),
        "updated_at": _now_iso(),
    }
    _save_encounter(conn, campaign_slug, enc_id, payload)
    return {"ok": True, "encounter_id": enc_id, **payload}


def set_contested(
    conn: sqlite3.Connection,
    campaign_slug: str,
    enc_id: str,
    *,
    skill_id: str,
) -> dict[str, Any]:
    enc = get_encounter(conn, campaign_slug, enc_id)
    if not enc:
        return {"ok": False, "error": f"No social encounter: {enc_id}"}
    enc["phase"] = "contested"
    enc["pending_skill_id"] = skill_id
    enc["updated_at"] = _now_iso()
    _save_encounter(conn, campaign_slug, enc_id, enc)
    return {"ok": True, "encounter_id": enc_id, **enc}


def resolve_encounter(
    conn: sqlite3.Connection,
    campaign_slug: str,
    enc_id: str,
    *,
    margin: int,
) -> dict[str, Any]:
    enc = get_encounter(conn, campaign_slug, enc_id)
    if not enc:
        return {"ok": False, "error": f"No social encounter: {enc_id}"}
    margins = list(enc.get("margins") or [])
    margins.append(int(margin))
    enc["margins"] = margins
    enc["disposition"] = _derive_disposition(margins)
    enc["phase"] = "resolved"
    enc.pop("pending_skill_id", None)
    enc["updated_at"] = _now_iso()
    _save_encounter(conn, campaign_slug, enc_id, enc)
    return {"ok": True, "encounter_id": enc_id, **enc}


def reset_encounter(
    conn: sqlite3.Connection,
    campaign_slug: str,
    enc_id: str,
) -> dict[str, Any]:
    enc = get_encounter(conn, campaign_slug, enc_id)
    if not enc:
        return {"ok": True, "encounter_id": enc_id, "phase": "idle"}
    enc["phase"] = "idle"
    enc.pop("pending_skill_id", None)
    enc["updated_at"] = _now_iso()
    _save_encounter(conn, campaign_slug, enc_id, enc)
    return {"ok": True, "encounter_id": enc_id, **enc}


def leave_encounter(
    conn: sqlite3.Connection,
    campaign_slug: str,
    enc_id: str,
) -> dict[str, Any]:
    return reset_encounter(conn, campaign_slug, enc_id)


def active_encounter_summary(conn: sqlite3.Connection, campaign_slug: str) -> dict[str, Any]:
    state = get_account_state(conn, campaign_slug)
    encounters = _encounters(state)
    for enc_id, enc in encounters.items():
        phase = enc.get("phase", "idle")
        if phase in ("active", "contested", "resolved"):
            return {
                "encounter_id": enc_id,
                "phase": phase,
                "npc_id": enc.get("npc_id"),
                "quest_id": enc.get("quest_id"),
                "disposition": enc.get("disposition", "neutral"),
            }
    return {"phase": "idle"}


def disposition_dc_modifier(conn: sqlite3.Connection, campaign_slug: str, enc_id: str) -> int:
    enc = get_encounter(conn, campaign_slug, enc_id)
    if not enc:
        return 0
    from tomb_gm.services.simulation.skill_checks import disposition_dc_modifier as _mod

    return _mod(enc.get("disposition"))
