"""Quest definitions and runtime lifecycle (APP-085 / APP-108)."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from collections.abc import Callable
from typing import Any

from tomb_gm.services.economy import get_account_state, save_account_state
from tomb_gm.services.hub import active_delver_id
from tomb_gm.services.simulation import skill_checks as sc
from tomb_gm.services import social_encounter as se

QUEST_STATES = frozenset(
    {"hidden", "offered", "accepted", "ready_to_turn_in", "completed", "abandoned", "failed"}
)


class QuestError(ValueError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _quests_path(content_root: Path | str) -> Path:
    return Path(content_root) / "data" / "quests" / "quests.json"


def load_quest_defs(content_root: Path | str) -> dict[str, dict[str, Any]]:
    path = _quests_path(content_root)
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    quests = data.get("quests", [])
    return {q["id"]: q for q in quests if isinstance(q, dict) and q.get("id")}


def get_quest_def(content_root: Path | str, quest_id: str) -> dict[str, Any] | None:
    return load_quest_defs(content_root).get(quest_id)


def _runtime_quests(state: dict[str, Any]) -> dict[str, Any]:
    state.setdefault("quests", {})
    return state["quests"]


def _objective_states(definition: dict[str, Any]) -> dict[str, str]:
    objectives = definition.get("objectives") or []
    return {obj["id"]: "pending" for obj in objectives if obj.get("id")}


def list_quests(conn: sqlite3.Connection, campaign_slug: str) -> dict[str, Any]:
    state = get_account_state(conn, campaign_slug)
    runtime = _runtime_quests(state)
    return {"ok": True, "quests": dict(runtime)}


def offer_quest(
    conn: sqlite3.Connection,
    campaign_slug: str,
    quest_id: str,
    *,
    content_root: Path | str,
) -> dict[str, Any]:
    definition = get_quest_def(content_root, quest_id)
    if not definition:
        return {"ok": False, "error": f"Unknown quest: {quest_id}"}

    state = get_account_state(conn, campaign_slug)
    runtime = _runtime_quests(state)
    existing = runtime.get(quest_id)
    if existing and existing.get("state") not in ("hidden", "offered"):
        return {
            "ok": False,
            "error": f"Quest already {existing.get('state')}",
            "quest_id": quest_id,
        }

    runtime[quest_id] = {
        "state": "offered",
        "offeredAt": _now_iso(),
        "objectives": _objective_states(definition),
        "advancePaidGp": 0,
    }
    save_account_state(conn, campaign_slug, state)
    return {
        "ok": True,
        "quest_id": quest_id,
        "state": "offered",
        "displayName": definition.get("displayName"),
    }


def accept_quest(
    conn: sqlite3.Connection,
    campaign_slug: str,
    quest_id: str,
    *,
    content_root: Path | str,
) -> dict[str, Any]:
    definition = get_quest_def(content_root, quest_id)
    if not definition:
        return {"ok": False, "error": f"Unknown quest: {quest_id}"}

    state = get_account_state(conn, campaign_slug)
    runtime = _runtime_quests(state)
    entry = runtime.get(quest_id)
    if not entry or entry.get("state") != "offered":
        return {"ok": False, "error": "Quest not offered", "quest_id": quest_id}

    entry["state"] = "accepted"
    entry["acceptedAt"] = _now_iso()
    entry.setdefault("advancePaidGp", 0)
    entry.setdefault("objectives", _objective_states(definition))
    save_account_state(conn, campaign_slug, state)

    giver = definition.get("giverNpcId")
    if giver:
        se.engage(conn, campaign_slug, npc_id=giver, quest_id=quest_id)

    return {"ok": True, "quest_id": quest_id, "state": "accepted"}


def _advance_tier(outcomes: list[dict[str, Any]], margin: int) -> int:
    for tier in outcomes:
        min_m = tier.get("minMargin")
        max_m = tier.get("maxMargin")
        if min_m is not None and margin < int(min_m):
            continue
        if max_m is not None and margin > int(max_m):
            continue
        return int(tier.get("advanceGp", 0))
    return 0


def grant_quest_advance(
    conn: sqlite3.Connection,
    campaign_slug: str,
    quest_id: str,
    gold_gp: int,
    *,
    content_root: Path | str,
    character_id: str | None = None,
) -> dict[str, Any]:
    definition = get_quest_def(content_root, quest_id)
    if not definition:
        return {"ok": False, "error": f"Unknown quest: {quest_id}"}

    state = get_account_state(conn, campaign_slug)
    runtime = _runtime_quests(state)
    entry = runtime.get(quest_id)
    if not entry or entry.get("state") != "accepted":
        return {"ok": False, "error": "Quest not accepted", "quest_id": quest_id}

    advance_def = (definition.get("negotiation") or {}).get("advance") or {}
    max_advance = int(advance_def.get("maxAdvanceGp", gold_gp))
    paid = int(entry.get("advancePaidGp", 0))
    requested = max(0, int(gold_gp))
    allowed = max(0, min(requested, max_advance - paid))
    if allowed <= 0:
        return {
            "ok": True,
            "quest_id": quest_id,
            "granted_gp": 0,
            "advancePaidGp": paid,
            "capped": requested > 0,
        }

    char_id = character_id or active_delver_id(conn, campaign_slug)
    if not char_id:
        return {"ok": False, "error": "no active character"}

    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (char_id, campaign_slug),
    ).fetchone()
    if not row:
        return {"ok": False, "error": f"Character not found: {char_id}"}

    sheet = json.loads(row["sheet_json"])
    before = int(sheet.get("goldGp", 0))
    sheet["goldGp"] = before + allowed
    conn.execute(
        "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), char_id, campaign_slug),
    )

    entry["advancePaidGp"] = paid + allowed
    save_account_state(conn, campaign_slug, state)
    conn.commit()

    return {
        "ok": True,
        "quest_id": quest_id,
        "character_id": char_id,
        "granted_gp": allowed,
        "advancePaidGp": entry["advancePaidGp"],
        "goldGp_before": before,
        "goldGp_after": sheet["goldGp"],
    }


def negotiate_quest_advance(
    conn: sqlite3.Connection,
    campaign_slug: str,
    quest_id: str,
    skill_id: str,
    *,
    content_root: Path | str,
    log_event,
    session_id: str | None = None,
    character_id: str | None = None,
    approach: str | None = None,
    advantage: bool = False,
    seed: int | None = None,
) -> dict[str, Any]:
    definition = get_quest_def(content_root, quest_id)
    if not definition:
        return {"ok": False, "error": f"Unknown quest: {quest_id}"}

    advance_def = (definition.get("negotiation") or {}).get("advance")
    if not advance_def:
        return {"ok": False, "error": "Quest has no advance negotiation", "quest_id": quest_id}

    state = get_account_state(conn, campaign_slug)
    runtime = _runtime_quests(state)
    entry = runtime.get(quest_id)
    if not entry or entry.get("state") != "accepted":
        return {"ok": False, "error": "Quest must be accepted before negotiating advance"}

    skill_key = skill_id.strip().lower()
    allowed_skills = [s.lower() for s in advance_def.get("skillIds", [])]
    if skill_key not in allowed_skills:
        return {
            "ok": False,
            "error": f"Skill {skill_id} not allowed for this negotiation",
            "allowed": allowed_skills,
        }

    npc_id = str(advance_def.get("npcId", definition.get("giverNpcId", "")))
    enc_id = se.encounter_id(npc_id, quest_id)
    se.engage(conn, campaign_slug, npc_id=npc_id, quest_id=quest_id)
    se.set_contested(conn, campaign_slug, enc_id, skill_id=skill_key)

    base_dc = int(advance_def.get("baseDc", 15))
    disp_mod = se.disposition_dc_modifier(conn, campaign_slug, enc_id)
    rep_mod = sc.faction_rep_dc_modifier(conn, campaign_slug, npc_id=npc_id)
    effective_dc = base_dc + disp_mod + rep_mod

    char_id = character_id or active_delver_id(conn, campaign_slug)
    if not char_id:
        return {"ok": False, "error": "no active character"}

    check = sc.skill_check(
        conn,
        campaign_slug,
        char_id,
        skill_key,
        effective_dc,
        opposed_npc_id=npc_id,
        content_root=content_root,
        log_event=log_event,
        session_id=session_id,
        reason=approach or f"negotiate advance for {quest_id}",
        advantage=advantage,
        skip_faction_rep=True,
        seed=seed,
    )
    if not check.get("ok"):
        return check

    margin = int(check.get("margin", 0))
    tier_gp = _advance_tier(advance_def.get("outcomes") or [], margin)
    se.resolve_encounter(conn, campaign_slug, enc_id, margin=margin)

    grant = grant_quest_advance(
        conn,
        campaign_slug,
        quest_id,
        tier_gp,
        content_root=content_root,
        character_id=char_id,
    )
    se.reset_encounter(conn, campaign_slug, enc_id)

    return {
        "ok": True,
        "quest_id": quest_id,
        "skill_id": skill_key,
        "approach": approach,
        "check": check,
        "margin": margin,
        "advance_gp": tier_gp,
        "grant": grant,
    }


def _all_objectives_done(entry: dict[str, Any], definition: dict[str, Any]) -> bool:
    objectives_state = entry.get("objectives") or {}
    for obj in definition.get("objectives") or []:
        obj_id = obj.get("id")
        if not obj_id:
            continue
        if objectives_state.get(obj_id) != "done":
            return False
    return True


def _sync_quest_state_after_objectives(entry: dict[str, Any], definition: dict[str, Any]) -> None:
    if _all_objectives_done(entry, definition) and entry.get("state") == "accepted":
        entry["state"] = "ready_to_turn_in"


def _find_pending_deliver_objective(
    definition: dict[str, Any],
    entry: dict[str, Any],
    item_id: str,
    npc_id: str,
) -> tuple[str | None, dict[str, Any] | None]:
    objectives_state = entry.get("objectives") or {}
    for obj in definition.get("objectives") or []:
        if obj.get("type") != "deliver_item":
            continue
        if obj.get("itemId") != item_id or obj.get("npcId") != npc_id:
            continue
        obj_id = obj.get("id")
        if not obj_id:
            continue
        if objectives_state.get(obj_id) == "done":
            continue
        return str(obj_id), obj
    return None, None


def deliver_quest_item(
    conn: sqlite3.Connection,
    campaign_slug: str,
    quest_id: str,
    item_id: str,
    npc_id: str,
    *,
    content_root: Path | str,
    character_id: str | None = None,
    has_item_fn: Callable[[str], dict[str, Any]] | None = None,
    remove_item_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    definition = get_quest_def(content_root, quest_id)
    if not definition:
        return {"ok": False, "error": f"Unknown quest: {quest_id}"}

    state = get_account_state(conn, campaign_slug)
    runtime = _runtime_quests(state)
    entry = runtime.get(quest_id)
    quest_state = entry.get("state") if entry else None
    if not entry or quest_state not in ("accepted", "ready_to_turn_in"):
        return {"ok": False, "error": f"Quest not accepted: {quest_id}", "quest_id": quest_id}

    objective_id, _objective = _find_pending_deliver_objective(definition, entry, item_id, npc_id)
    if not objective_id:
        return {"ok": False, "error": "No deliver_item objective for item/npc", "quest_id": quest_id}

    if has_item_fn is not None:
        has_result = has_item_fn(item_id)
        if not has_result.get("ok"):
            return has_result
        if not has_result.get("found"):
            return {"ok": False, "error": f"Item not in pack: {item_id}"}

    if remove_item_fn is None:
        return {"ok": False, "error": "remove_item_fn required"}

    remove_kwargs: dict[str, Any] = {"item_id": item_id}
    if character_id:
        remove_kwargs["character_id"] = character_id
    remove_result = remove_item_fn(**remove_kwargs)
    if not remove_result.get("ok"):
        return remove_result

    entry.setdefault("objectives", _objective_states(definition))
    entry["objectives"][objective_id] = "done"
    _sync_quest_state_after_objectives(entry, definition)
    save_account_state(conn, campaign_slug, state)

    return {
        "ok": True,
        "quest_id": quest_id,
        "item_id": item_id,
        "objective_id": objective_id,
        "npc_id": npc_id,
        "state": entry.get("state"),
        "removed": remove_result.get("removed"),
        "character_id": remove_result.get("character_id") or character_id,
    }


def complete_quest(
    conn: sqlite3.Connection,
    campaign_slug: str,
    quest_id: str,
    *,
    content_root: Path | str,
    character_id: str | None = None,
) -> dict[str, Any]:
    definition = get_quest_def(content_root, quest_id)
    if not definition:
        return {"ok": False, "error": f"Unknown quest: {quest_id}"}

    state = get_account_state(conn, campaign_slug)
    runtime = _runtime_quests(state)
    entry = runtime.get(quest_id)
    if not entry or entry.get("state") not in ("accepted", "ready_to_turn_in"):
        return {"ok": False, "error": "Quest not ready to complete", "quest_id": quest_id}

    rewards = definition.get("rewards") or {}
    total_gold = int(rewards.get("goldGp", 0))
    paid = int(entry.get("advancePaidGp", 0))
    payout = max(0, total_gold - paid)

    char_id = character_id or active_delver_id(conn, campaign_slug)
    gold_after = None
    if payout > 0 and char_id:
        row = conn.execute(
            "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
            (char_id, campaign_slug),
        ).fetchone()
        if row:
            sheet = json.loads(row["sheet_json"])
            sheet["goldGp"] = int(sheet.get("goldGp", 0)) + payout
            gold_after = sheet["goldGp"]
            conn.execute(
                "UPDATE characters SET sheet_json = ? WHERE id = ? AND campaign_slug = ?",
                (json.dumps(sheet), char_id, campaign_slug),
            )

    entry["state"] = "completed"
    entry["completedAt"] = _now_iso()
    save_account_state(conn, campaign_slug, state)
    conn.commit()

    return {
        "ok": True,
        "quest_id": quest_id,
        "state": "completed",
        "payout_gp": payout,
        "advancePaidGp": paid,
        "character_id": char_id,
        "goldGp_after": gold_after,
    }
