from __future__ import annotations

import json
import random
import re
import sqlite3
from pathlib import Path
from typing import Any

from tomb_gm.rules.bridge import initiative_total, roll_d20

MONSTER_SPEC_RE = re.compile(r"^([a-z0-9-]+)(?::(\d+))?$", re.IGNORECASE)


def parse_monster_specs(specs: list[str]) -> list[tuple[str, int]]:
    out: list[tuple[str, int]] = []
    for spec in specs:
        match = MONSTER_SPEC_RE.match(spec.strip())
        if not match:
            raise ValueError(f"invalid monster spec: {spec!r} (use id or id:count)")
        monster_id, count_s = match.groups()
        count = int(count_s) if count_s else 1
        if count < 1:
            raise ValueError(f"monster count must be >= 1: {spec!r}")
        out.append((monster_id.lower(), count))
    return out


def load_monster_json(content_root: Path, monster_id: str) -> dict[str, Any]:
    path = content_root / "data" / "monsters" / f"{monster_id}.json"
    if not path.is_file():
        raise FileNotFoundError(f"monster JSON not found: {monster_id} ({path})")
    return json.loads(path.read_text(encoding="utf-8"))


def pick_stat_block(data: dict[str, Any], tier: str | None = None) -> dict[str, Any]:
    blocks = data.get("statBlocks") or []
    if not blocks:
        raise ValueError(f"monster {data.get('id', '?')} has no statBlocks")
    if tier:
        for block in blocks:
            if block.get("tier") == tier or block.get("id") == tier:
                return block
        raise ValueError(f"tier {tier!r} not found for {data.get('id')}")
    return blocks[0]


def _spawn_instances(
    content_root: Path,
    specs: list[str],
    *,
    tier: str | None,
    rng: random.Random,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    combatants: list[dict[str, Any]] = []
    initiative: list[dict[str, Any]] = []
    counts: dict[str, int] = {}

    for monster_id, count in parse_monster_specs(specs):
        data = load_monster_json(content_root, monster_id)
        block = pick_stat_block(data, tier)
        agi = int((block.get("attributes") or {}).get("AGI", 0))

        for _ in range(count):
            counts[monster_id] = counts.get(monster_id, 0) + 1
            instance_id = f"{monster_id}-{counts[monster_id]}"
            display = block.get("displayName") or data.get("displayName", monster_id)
            combatants.append(
                {
                    "id": instance_id,
                    "kind": "monster",
                    "monsterId": monster_id,
                    "tier": block.get("tier") or block.get("id"),
                    "displayName": display,
                    "hp": block["hp"],
                    "maxHp": block["hp"],
                    "ac": block["ac"],
                    "conditions": [],
                }
            )
            nat = roll_d20(rng)
            init = initiative_total(natural=nat, agi_mod=agi)
            initiative.append(
                {
                    "id": instance_id,
                    "name": display,
                    "natural": nat,
                    "initiative": init,
                }
            )

    initiative.sort(key=lambda row: row["initiative"], reverse=True)
    return combatants, initiative


def start_combat(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    content_root: Path,
    monster_specs: list[str],
    tier: str | None = None,
    seed: int | None = None,
    include_party: bool = False,
    campaign_slug: str | None = None,
) -> dict[str, Any]:
    session = conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        raise ValueError(f"unknown session: {session_id}")

    rng = random.Random(seed) if seed is not None else random.Random()
    combatants, initiative = _spawn_instances(content_root, monster_specs, tier=tier, rng=rng)

    if include_party:
        if not campaign_slug:
            raise ValueError("campaign_slug required when include_party is true")
        from tomb_gm.domain.combat_player import spawn_roster_combatants

        pcs, pc_init = spawn_roster_combatants(conn, campaign_slug, rng=rng)
        combatants.extend(pcs)
        initiative.extend(pc_init)
        initiative.sort(key=lambda row: row["initiative"], reverse=True)

    conn.execute(
        """
        INSERT INTO combat_state (session_id, active, round, turn_index, initiative_json, combatants_json)
        VALUES (?, 1, 1, 0, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
          active = 1,
          round = 1,
          turn_index = 0,
          initiative_json = excluded.initiative_json,
          combatants_json = excluded.combatants_json
        """,
        (session_id, json.dumps(initiative), json.dumps(combatants)),
    )
    conn.commit()
    return {
        "ok": True,
        "session_id": session_id,
        "round": 1,
        "turn_index": 0,
        "initiative": initiative,
        "combatants": combatants,
    }


def combat_status(conn: sqlite3.Connection, session_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM combat_state WHERE session_id = ? AND active = 1",
        (session_id,),
    ).fetchone()
    if not row:
        return {"ok": False, "error": "no active combat for session", "session_id": session_id}
    initiative = json.loads(row["initiative_json"] or "[]")
    combatants = json.loads(row["combatants_json"] or "[]")
    turn_id = None
    if initiative and 0 <= row["turn_index"] < len(initiative):
        turn_id = initiative[row["turn_index"]]["id"]
    return {
        "ok": True,
        "session_id": session_id,
        "round": row["round"],
        "turn_index": row["turn_index"],
        "turn_id": turn_id,
        "initiative": initiative,
        "combatants": combatants,
    }


def advance_turn(conn: sqlite3.Connection, session_id: str) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM combat_state WHERE session_id = ? AND active = 1",
        (session_id,),
    ).fetchone()
    if not row:
        return {"ok": False, "error": "no active combat for session", "session_id": session_id}
    initiative = json.loads(row["initiative_json"] or "[]")
    if not initiative:
        return {"ok": False, "error": "empty initiative", "session_id": session_id}
    turn_index = int(row["turn_index"]) + 1
    round_num = int(row["round"])
    if turn_index >= len(initiative):
        turn_index = 0
        round_num += 1
    conn.execute(
        "UPDATE combat_state SET turn_index = ?, round = ? WHERE session_id = ?",
        (turn_index, round_num, session_id),
    )
    conn.commit()
    turn_id = initiative[turn_index]["id"]
    return {
        "ok": True,
        "session_id": session_id,
        "round": round_num,
        "turn_index": turn_index,
        "turn_id": turn_id,
    }


def apply_damage_to_combatant(
    conn: sqlite3.Connection,
    session_id: str,
    combatant_id: str,
    damage: int,
    *,
    campaign_slug: str | None = None,
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT combatants_json FROM combat_state WHERE session_id = ? AND active = 1",
        (session_id,),
    ).fetchone()
    if not row:
        return {"ok": False, "error": "no active combat"}
    combatants = json.loads(row["combatants_json"] or "[]")
    found = False
    target: dict[str, Any] | None = None
    for c in combatants:
        if c["id"] == combatant_id:
            c["hp"] = max(0, int(c.get("hp", 0)) - damage)
            found = True
            target = c
            break
    if not found:
        return {"ok": False, "error": f"combatant not found: {combatant_id}"}
    conn.execute(
        "UPDATE combat_state SET combatants_json = ? WHERE session_id = ?",
        (json.dumps(combatants), session_id),
    )
    conn.commit()
    out: dict[str, Any] = {
        "ok": True,
        "combatant_id": combatant_id,
        "damage": damage,
        "combatants": combatants,
    }
    if target and target.get("kind") == "pc" and campaign_slug:
        from tomb_gm.domain.combat_player import set_character_hp_from_combat

        sheet_result = set_character_hp_from_combat(
            conn,
            campaign_slug=campaign_slug,
            character_id=combatant_id,
            hp=int(target.get("hp", 0)),
            conditions=list(target.get("conditions") or []),
        )
        out["character"] = sheet_result
    return out


def end_combat(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    campaign_slug: str | None = None,
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT active, combatants_json FROM combat_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if not row or not row["active"]:
        return {"ok": False, "error": "no active combat for session", "session_id": session_id}
    if campaign_slug:
        from tomb_gm.domain.combat_player import sync_combatant_to_sheet

        combatants = json.loads(row["combatants_json"] or "[]")
        for c in combatants:
            if c.get("kind") == "pc":
                sync_combatant_to_sheet(
                    conn,
                    campaign_slug=campaign_slug,
                    character_id=c["id"],
                )
    conn.execute(
        "UPDATE combat_state SET active = 0 WHERE session_id = ?",
        (session_id,),
    )
    conn.commit()
    return {"ok": True, "session_id": session_id, "ended": True}
