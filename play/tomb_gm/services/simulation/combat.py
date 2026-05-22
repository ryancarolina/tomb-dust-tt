from __future__ import annotations

import json
import random
import re
import sqlite3
from pathlib import Path
from typing import Any

from tomb_gm.domain.character import ability_modifier
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


def validate_monster_specs(content_root: Path, monster_specs: list[str]) -> str | None:
    """Return an error string when specs are invalid; None when dispatchable."""
    if not monster_specs:
        return "monster_specs required"
    for raw in monster_specs:
        if not isinstance(raw, str) or not raw.strip():
            return f"invalid monster spec: {raw!r} (use id or id:count)"
        try:
            pairs = parse_monster_specs([raw.strip()])
        except ValueError as exc:
            return str(exc)
        monster_id = pairs[0][0]
        path = content_root / "data" / "monsters" / f"{monster_id}.json"
        if not path.is_file():
            return f"monster JSON not found: {monster_id} ({path})"
    return None


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


def is_living(combatant: dict[str, Any]) -> bool:
    if combatant.get("kind") == "pc":
        from tomb_gm.domain.combat_player import is_pc_combat_active

        return is_pc_combat_active(combatant)
    return int(combatant.get("hp", 0)) > 0


def is_party_down(combatants: list[dict[str, Any]]) -> bool:
    from tomb_gm.domain.combat_player import is_pc_party_down

    pcs = [c for c in combatants if c.get("kind") == "pc"]
    if not pcs:
        return True
    return all(is_pc_party_down(c) for c in pcs)


def living_combatants(combatants: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [c for c in combatants if is_living(c)]


def _agi_mod_for_combatant(
    combatant: dict[str, Any],
    *,
    conn: sqlite3.Connection | None = None,
    campaign_slug: str | None = None,
) -> int:
    if combatant.get("kind") == "pc":
        if conn and campaign_slug:
            from tomb_gm.domain.combat_sheet import load_character_sheet

            char_id = combatant.get("characterId") or combatant.get("id")
            sheet = load_character_sheet(conn, campaign_slug, char_id)
            return ability_modifier(int(sheet.get("attributes", {}).get("AGI", 10)))
        return ability_modifier(int(combatant.get("agi", 10)))
    return int((combatant.get("attributes") or {}).get("AGI", 0))


def _initiative_bonus_for_pc(conn: sqlite3.Connection, campaign_slug: str, character_id: str) -> int:
    from tomb_gm.domain.combat_sheet import load_character_sheet

    sheet = load_character_sheet(conn, campaign_slug, character_id)
    skills = {s["skillId"]: int(s["level"]) for s in sheet.get("skills", [])}
    bonus = 0
    if skills.get("dodge", 0) >= 9:
        bonus += 2
    ba = skills.get("battlefield-awareness", 0)
    bonus += ba // 2
    return bonus


def _sort_initiative_entries(
    entries: list[dict[str, Any]],
    combatants_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    def sort_key(entry: dict[str, Any]) -> tuple:
        c = combatants_by_id.get(entry["id"], {})
        agi_mod = int(entry.get("agi_mod", 0))
        kind_rank = 0 if c.get("kind") == "pc" else 1
        return (-entry["initiative"], -agi_mod, -entry["natural"], kind_rank)

    return sorted(entries, key=sort_key)


def _spawn_instances(
    content_root: Path,
    specs: list[str],
    *,
    tier: str | None,
) -> list[dict[str, Any]]:
    combatants: list[dict[str, Any]] = []
    counts: dict[str, int] = {}

    for monster_id, count in parse_monster_specs(specs):
        data = load_monster_json(content_root, monster_id)
        block = pick_stat_block(data, tier)
        attrs = block.get("attributes") or {}

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
                    "attributes": dict(attrs),
                    "downedBehavior": block.get("downedBehavior") or data.get("downedBehavior", "ignore"),
                }
            )
    return combatants


def roll_round_initiative(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    content_root: Path,
    campaign_slug: str | None = None,
    seed: int | None = None,
    increment_round: bool = False,
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT * FROM combat_state WHERE session_id = ? AND active = 1",
        (session_id,),
    ).fetchone()
    if not row:
        return {"ok": False, "error": "no active combat for session", "session_id": session_id}

    combatants = json.loads(row["combatants_json"] or "[]")
    living = living_combatants(combatants)
    if not living:
        return {"ok": False, "error": "no living combatants", "session_id": session_id}

    rng = random.Random(seed) if seed is not None else random.Random()
    by_id = {c["id"]: c for c in combatants}
    entries: list[dict[str, Any]] = []

    for c in living:
        cid = c["id"]
        agi_mod = _agi_mod_for_combatant(c, conn=conn, campaign_slug=campaign_slug)
        bonus = 0
        if c.get("kind") == "pc" and campaign_slug:
            bonus = _initiative_bonus_for_pc(conn, campaign_slug, cid)
        nat = roll_d20(rng)
        total = initiative_total(natural=nat, agi_mod=agi_mod, bonus=bonus)
        entries.append(
            {
                "id": cid,
                "name": c.get("displayName", cid),
                "natural": nat,
                "initiative": total,
                "agi_mod": agi_mod,
            }
        )

    initiative = _sort_initiative_entries(entries, by_id)
    round_num = int(row["round"])
    if increment_round:
        round_num += 1

    conn.execute(
        "UPDATE combat_state SET round = ?, turn_index = 0, initiative_json = ? WHERE session_id = ?",
        (round_num, json.dumps(initiative), session_id),
    )
    conn.commit()

    turn_id = initiative[0]["id"] if initiative else None
    return {
        "ok": True,
        "session_id": session_id,
        "round": round_num,
        "turn_index": 0,
        "turn_id": turn_id,
        "initiative": initiative,
        "action": "initiative_round",
    }


def start_combat(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    content_root: Path,
    monster_specs: list[str],
    tier: str | None = None,
    seed: int | None = None,
    include_party: bool = True,
    campaign_slug: str | None = None,
    surprised_combatant_ids: list[str] | None = None,
) -> dict[str, Any]:
    session = conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not session:
        raise ValueError(f"unknown session: {session_id}")

    existing = conn.execute(
        "SELECT active FROM combat_state WHERE session_id = ? AND active = 1",
        (session_id,),
    ).fetchone()
    if existing:
        return {"ok": False, "error": "combat already active; end combat before starting a new encounter"}

    err = validate_monster_specs(content_root, monster_specs)
    if err:
        return {"ok": False, "error": err}

    combatants = _spawn_instances(content_root, monster_specs, tier=tier)

    if include_party:
        if not campaign_slug:
            raise ValueError("campaign_slug required when include_party is true")
        from tomb_gm.domain.combat_player import spawn_roster_combatants

        pcs, _ = spawn_roster_combatants(
            conn, campaign_slug, rng=random.Random(seed), content_root=content_root
        )
        combatants.extend(pcs)

    if surprised_combatant_ids:
        surprised_set = set(surprised_combatant_ids)
        for combatant in combatants:
            cid = combatant.get("id") or combatant.get("character_id")
            if cid in surprised_set:
                combatant["surprised"] = True

    conn.execute(
        """
        INSERT INTO combat_state (session_id, active, round, turn_index, initiative_json, combatants_json)
        VALUES (?, 1, 1, 0, '[]', ?)
        ON CONFLICT(session_id) DO UPDATE SET
          active = 1,
          round = 1,
          turn_index = 0,
          initiative_json = '[]',
          combatants_json = excluded.combatants_json
        """,
        (session_id, json.dumps(combatants)),
    )
    conn.commit()

    init_result = roll_round_initiative(
        conn,
        session_id,
        content_root=content_root,
        campaign_slug=campaign_slug,
        seed=seed,
        increment_round=False,
    )
    if not init_result.get("ok"):
        return init_result

    return {
        "ok": True,
        "session_id": session_id,
        "round": init_result["round"],
        "turn_index": 0,
        "turn_id": init_result.get("turn_id"),
        "initiative": init_result["initiative"],
        "combatants": combatants,
        "action": "combat_start",
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
    turn_kind = None
    if initiative and 0 <= row["turn_index"] < len(initiative):
        turn_id = initiative[row["turn_index"]]["id"]
        for c in combatants:
            if c.get("id") == turn_id:
                turn_kind = c.get("kind")
                break
    return {
        "ok": True,
        "session_id": session_id,
        "round": row["round"],
        "turn_index": row["turn_index"],
        "turn_id": turn_id,
        "turn_kind": turn_kind,
        "initiative": initiative,
        "combatants": combatants,
    }


def _assert_actor_turn(status: dict[str, Any], actor_id: str) -> dict[str, Any] | None:
    turn_id = status.get("turn_id")
    if not turn_id:
        return {"ok": False, "error": "no active turn"}
    if actor_id != turn_id:
        return {"ok": False, "error": f"not your turn: expected {turn_id}, got {actor_id}"}
    return None


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
        return {
            "ok": True,
            "session_id": session_id,
            "round": round_num,
            "round_complete": True,
            "turn_index": turn_index,
        }
    conn.execute(
        "UPDATE combat_state SET turn_index = ? WHERE session_id = ?",
        (turn_index, session_id),
    )
    conn.commit()
    turn_id = initiative[turn_index]["id"]
    return {
        "ok": True,
        "session_id": session_id,
        "round": round_num,
        "turn_index": turn_index,
        "turn_id": turn_id,
        "round_complete": False,
    }


def check_combat_end(conn: sqlite3.Connection, session_id: str) -> dict[str, Any]:
    status = combat_status(conn, session_id)
    if not status.get("ok"):
        return {"ok": True, "ended": False}
    combatants = status.get("combatants") or []
    living_pcs = [c for c in combatants if c.get("kind") == "pc" and is_living(c)]
    living_monsters = [c for c in combatants if c.get("kind") == "monster" and is_living(c)]
    if not living_monsters:
        return {"ok": True, "ended": True, "outcome": "victory", "reason": "all_enemies_defeated"}
    if is_party_down(combatants):
        return {"ok": True, "ended": True, "outcome": "defeat", "reason": "party_down"}
    return {"ok": True, "ended": False}


def _pick_monster_target(attacker: dict[str, Any], combatants: list[dict[str, Any]]) -> str | None:
    from tomb_gm.domain.combat_player import DOWNED, DYING

    behavior = str(attacker.get("downedBehavior") or "ignore").lower()
    standing = [
        c for c in combatants
        if c.get("kind") == "pc" and int(c.get("hp", 0)) > 0
    ]
    downed = [
        c for c in combatants
        if c.get("kind") == "pc"
        and int(c.get("hp", 0)) <= 0
        and (DOWNED in (c.get("conditions") or []) or DYING in (c.get("conditions") or []))
    ]

    if behavior == "flee" and standing and not downed:
        return standing[0]["id"]
    if behavior == "flee" and not standing and downed:
        return None

    if behavior in ("feast", "execute", "drag") and downed:
        dying = [c for c in downed if DYING in (c.get("conditions") or [])]
        if dying:
            return dying[0]["id"]
        return downed[0]["id"]

    if standing:
        return standing[0]["id"]
    if downed and behavior != "ignore":
        return downed[0]["id"]
    return None


def apply_damage_to_combatant(
    conn: sqlite3.Connection,
    session_id: str,
    combatant_id: str,
    damage: int,
    *,
    campaign_slug: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    row = conn.execute(
        "SELECT combatants_json FROM combat_state WHERE session_id = ? AND active = 1",
        (session_id,),
    ).fetchone()
    if not row:
        return {"ok": False, "error": "no active combat"}
    combatants = json.loads(row["combatants_json"] or "[]")
    target: dict[str, Any] | None = None
    for c in combatants:
        if c["id"] == combatant_id:
            target = c
            break
    if not target:
        return {"ok": False, "error": f"combatant not found: {combatant_id}"}

    if target.get("kind") == "pc" and campaign_slug:
        from tomb_gm.domain.combat_player import resolve_pc_damage

        sheet_result = resolve_pc_damage(
            conn,
            campaign_slug=campaign_slug,
            character_id=combatant_id,
            damage=damage,
            session_id=session_id,
            seed=seed,
        )
        if sheet_result.get("died"):
            target["hp"] = 0
            target["conditions"] = sheet_result.get("conditions") or []
        else:
            target["hp"] = int(sheet_result.get("hp", 0))
            target["conditions"] = list(sheet_result.get("conditions") or [])
        conn.execute(
            "UPDATE combat_state SET combatants_json = ? WHERE session_id = ?",
            (json.dumps(combatants), session_id),
        )
        conn.commit()
        return {
            "ok": True,
            "combatant_id": combatant_id,
            "damage": damage,
            "combatants": combatants,
            "character": sheet_result,
        }

    target["hp"] = max(0, int(target.get("hp", 0)) - damage)
    conn.execute(
        "UPDATE combat_state SET combatants_json = ? WHERE session_id = ?",
        (json.dumps(combatants), session_id),
    )
    conn.commit()
    return {
        "ok": True,
        "combatant_id": combatant_id,
        "damage": damage,
        "combatants": combatants,
    }


def _resolve_combatant_id(combatants: list[dict[str, Any]], ref: str) -> str | None:
    ref_lower = ref.lower().strip()
    for c in combatants:
        cid = str(c.get("id", ""))
        if cid == ref or cid.lower() == ref_lower:
            return cid
        display = str(c.get("displayName", "")).lower()
        if display == ref_lower or ref_lower in display:
            return cid
    return None


def _pick_monster_attack(block: dict[str, Any]) -> dict[str, Any] | None:
    for action in block.get("actions") or []:
        if action.get("attack"):
            return action
    return None


def monster_attack(
    conn: sqlite3.Connection,
    session_id: str,
    attacker_id: str,
    *,
    content_root: Path,
    campaign_slug: str | None = None,
    target_id: str | None = None,
    seed: int | None = None,
) -> dict[str, Any]:
    from tomb_gm.cli.cmd_core import log_event
    from tomb_gm.services.simulation.spell_service import roll_spell_damage

    status = combat_status(conn, session_id)
    if not status.get("ok"):
        return status

    turn_err = _assert_actor_turn(status, attacker_id)
    if turn_err:
        return turn_err

    combatants = status.get("combatants") or []
    attacker = next((c for c in combatants if c.get("id") == attacker_id), None)
    if not attacker or attacker.get("kind") != "monster":
        return {"ok": False, "error": f"monster attacker not found: {attacker_id}"}
    if not is_living(attacker):
        return {"ok": False, "error": "attacker is defeated"}

    if target_id:
        resolved_target = _resolve_combatant_id(combatants, target_id) or target_id
    else:
        picked = _pick_monster_target(attacker, combatants)
        if not picked:
            return {"ok": False, "error": "no valid PC targets", "downed_behavior": attacker.get("downedBehavior")}
        resolved_target = picked

    target = next((c for c in combatants if c.get("id") == resolved_target), None)
    if not target:
        return {"ok": False, "error": f"target not available: {resolved_target}"}
    if target.get("kind") == "pc":
        from tomb_gm.domain.combat_player import DOWNED, DYING

        conds = target.get("conditions") or []
        if int(target.get("hp", 0)) <= 0 and DOWNED not in conds and DYING not in conds:
            return {"ok": False, "error": f"target not available: {resolved_target}"}
    elif not is_living(target):
        return {"ok": False, "error": f"target not available: {resolved_target}"}

    data = load_monster_json(content_root, attacker["monsterId"])
    block = pick_stat_block(data, attacker.get("tier"))
    action = _pick_monster_attack(block)
    if not action:
        return {"ok": False, "error": f"no attack action for {attacker_id}"}

    attack_spec = action["attack"]
    to_hit = int(attack_spec.get("toHit", 0))
    target_ac = int(target.get("ac", 10))
    rng = random.Random(seed) if seed is not None else random.Random()
    natural = roll_d20(rng)
    total = natural + to_hit
    hit = total >= target_ac
    crit = hit and (natural == 20 or total >= target_ac + 5)

    result: dict[str, Any] = {
        "ok": True,
        "action": "monster_attack",
        "attacker": attacker_id,
        "target": resolved_target,
        "natural": natural,
        "to_hit": to_hit,
        "total": total,
        "target_ac": target_ac,
        "hit": hit,
        "critical": crit,
        "attack_name": action.get("name", "Attack"),
    }

    if hit:
        dice = str(attack_spec.get("damage", "1d6"))
        damage = roll_spell_damage(dice, rng)
        if crit:
            damage *= 2
        result["damage"] = damage
        dmg_result = apply_damage_to_combatant(
            conn,
            session_id,
            resolved_target,
            damage,
            campaign_slug=campaign_slug,
            seed=seed,
        )
        result["damage_applied"] = dmg_result
        char = (dmg_result.get("character") or {})
        if char.get("died"):
            result["target_defeated"] = True
            result["target_dead"] = True
        elif char.get("downed") or char.get("dying"):
            result["target_down"] = True

    log_event(
        conn,
        session_id,
        "combat_monster_attack",
        {k: result[k] for k in result if k != "damage_applied"},
    )
    return result


def combat_attack(
    conn: sqlite3.Connection,
    session_id: str,
    attacker_id: str,
    target_id: str,
    *,
    content_root: Path,
    campaign_slug: str | None = None,
    weapon_id: str | None = None,
    seed: int | None = None,
    enforce_turn: bool = True,
) -> dict[str, Any]:
    from tomb_gm.cli.cmd_core import log_event
    from tomb_gm.domain.combat_sheet import (
        attack_modifiers_from_sheet,
        find_combatant,
        load_character_sheet,
        target_ac_from_monster,
    )
    from tomb_gm.services.content import ContentService
    from tomb_gm.services.simulation.rolls import perform_attack_roll

    status = combat_status(conn, session_id)
    if not status.get("ok"):
        return status

    combatants = status.get("combatants") or []
    resolved_attacker = _resolve_combatant_id(combatants, attacker_id) or attacker_id
    resolved_target = _resolve_combatant_id(combatants, target_id) or target_id

    if enforce_turn:
        turn_err = _assert_actor_turn(status, resolved_attacker)
        if turn_err:
            return turn_err

    attacker = find_combatant(conn, session_id, resolved_attacker)
    if not attacker:
        return {"ok": False, "error": f"attacker not in combat: {attacker_id}"}
    if attacker.get("kind") != "pc":
        return {"ok": False, "error": "only PC attacks are supported via combat_attack"}
    if not is_living(attacker):
        return {"ok": False, "error": "attacker is defeated"}

    target = find_combatant(conn, session_id, resolved_target)
    if not target:
        return {"ok": False, "error": f"target not in combat: {target_id}"}
    if not is_living(target):
        return {"ok": False, "error": f"target already defeated: {target_id}"}

    if not campaign_slug:
        return {"ok": False, "error": "campaign_slug required for PC attacks"}

    char_id = attacker.get("characterId") or attacker.get("id")
    sheet = load_character_sheet(conn, campaign_slug, char_id)
    mods = attack_modifiers_from_sheet(sheet, weapon_id=weapon_id, content_root=content_root)
    resolved_weapon = mods.get("weapon_id") or weapon_id
    content = ContentService(content_root)
    ac = target_ac_from_monster(content, target)

    result = perform_attack_roll(
        conn,
        log_event,
        session_id=session_id,
        ability_mod=mods["ability_mod"],
        pb=mods["pb"],
        skill_level=mods["skill_level"],
        target_ac=ac,
        weapon_damage=mods["weapon_damage"],
        ability_damage_mod=mods["ability_damage_mod"],
        reason=f"{char_id} vs {resolved_target}",
        seed=seed,
        character_id=char_id,
        campaign_slug=campaign_slug,
    )
    result["attacker"] = resolved_attacker
    result["target"] = resolved_target
    result["target_ac"] = ac
    result["action"] = "combat_attack"

    if result.get("hit"):
        dmg_total = int(result.get("damage") or 0)
        if dmg_total:
            damage_result = apply_damage_to_combatant(
                conn,
                session_id,
                resolved_target,
                dmg_total,
                campaign_slug=campaign_slug,
                seed=seed,
            )
            result["damage_applied"] = damage_result
            char = (damage_result.get("character") or {})
            if char.get("died"):
                result["target_defeated"] = True
                result["target_dead"] = True

    return result


def execute_combat_action(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    action: str,
    actor_id: str,
    content_root: Path,
    campaign_slug: str | None = None,
    target_id: str | None = None,
    weapon_id: str | None = None,
    spell_id: str | None = None,
    log_event=None,
    seed: int | None = None,
) -> dict[str, Any]:
    action_upper = action.upper().strip()
    if action_upper == "ATTACK":
        if not target_id:
            return {"ok": False, "error": "target_id required for ATTACK"}
        return combat_attack(
            conn,
            session_id,
            actor_id,
            target_id,
            content_root=content_root,
            campaign_slug=campaign_slug,
            weapon_id=weapon_id,
            seed=seed,
        )
    if action_upper == "CAST":
        if not spell_id:
            return {"ok": False, "error": "spell_id required for CAST"}
        from tomb_gm.domain.spell_cast import cast_spell

        status = combat_status(conn, session_id)
        if status.get("ok"):
            turn_err = _assert_actor_turn(status, actor_id)
            if turn_err:
                return turn_err
        return cast_spell(
            conn,
            log_event,
            content_root=content_root,
            campaign_slug=campaign_slug or "",
            character_id=actor_id,
            spell_id=spell_id,
            session_id=session_id,
            target_id=target_id,
            seed=seed,
        )
    if action_upper == "END_TURN":
        status = combat_status(conn, session_id)
        if status.get("ok"):
            turn_err = _assert_actor_turn(status, actor_id)
            if turn_err:
                return turn_err
        if campaign_slug:
            from tomb_gm.domain.combat_player import clear_pending_fortune_advantage
            from tomb_gm.domain.combat_sheet import find_combatant

            actor = find_combatant(conn, session_id, actor_id)
            char_id = (actor or {}).get("characterId") or actor_id
            clear_pending_fortune_advantage(conn, campaign_slug, char_id)
        return {"ok": True, "action": "end_turn", "actor_id": actor_id}
    return {"ok": False, "error": f"unknown combat action: {action}"}


def finalize_combat_if_ended(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    campaign_slug: str | None = None,
    content_root: Path | None = None,
) -> dict[str, Any]:
    end_check = check_combat_end(conn, session_id)
    if end_check.get("ended"):
        ended = end_combat(conn, session_id, campaign_slug=campaign_slug)
        result = {**end_check, **ended, "action": "combat_finalize"}
        if end_check.get("outcome") == "victory" and campaign_slug and content_root:
            from tomb_gm.services.content import ContentService
            from tomb_gm.services.loot_resolver import LootResolver, grant_loot

            ps = conn.execute(
                "SELECT address, mode, site_id FROM party_state WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            content = ContentService(content_root)
            tier = "skirmisher"
            if ps and ps["site_id"]:
                cell = content.get_cell(ps["site_id"])
                tier = (cell or {}).get("dangerRating") or tier
            elif ps:
                cell = content.get_cell(ps["address"])
                tier = (cell or {}).get("dangerRating") or tier
            resolver = LootResolver(content_root)
            rolled = resolver.roll(tier=tier or "skirmisher")
            if rolled.get("ok"):
                result["loot"] = rolled
                result["loot_granted"] = grant_loot(
                    conn,
                    content,
                    campaign_slug=campaign_slug,
                    loot_result=rolled,
                )
        if end_check.get("outcome") == "defeat" and campaign_slug:
            from tomb_gm.services.death import process_defeat_deaths

            death_results = process_defeat_deaths(
                conn,
                campaign_slug=campaign_slug,
                session_id=session_id,
                cause="slain in the delve",
            )
            if death_results:
                result["death_results"] = death_results
                result["run_ended"] = any(d.get("ok") for d in death_results)
        return result
    return end_check


def run_monster_turns_until_pc_or_end(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    content_root: Path,
    campaign_slug: str | None = None,
    seed: int | None = None,
    max_steps: int = 20,
) -> list[dict[str, Any]]:
    """Auto-resolve monster turns; re-roll initiative when a round completes."""
    results: list[dict[str, Any]] = []
    rng_seed = seed

    for step in range(max_steps):
        end_check = check_combat_end(conn, session_id)
        if end_check.get("ended"):
            results.append({**end_check, "action": "combat_end_check"})
            finalize = finalize_combat_if_ended(
                conn, session_id, campaign_slug=campaign_slug, content_root=content_root
            )
            results.append(finalize)
            break

        status = combat_status(conn, session_id)
        if not status.get("ok"):
            break

        turn_id = status.get("turn_id")
        turn_kind = status.get("turn_kind")
        if turn_kind == "pc":
            break

        if turn_kind == "monster" and turn_id:
            m_result = monster_attack(
                conn,
                session_id,
                turn_id,
                content_root=content_root,
                campaign_slug=campaign_slug,
                seed=rng_seed,
            )
            results.append(m_result)
            if rng_seed is not None:
                rng_seed += 1
            adv = advance_turn(conn, session_id)
            results.append({**adv, "action": "turn_advance"})
            if adv.get("round_complete"):
                init = roll_round_initiative(
                    conn,
                    session_id,
                    content_root=content_root,
                    campaign_slug=campaign_slug,
                    seed=rng_seed,
                    increment_round=True,
                )
                results.append(init)
                if rng_seed is not None:
                    rng_seed += 1
            continue

        break

    return results


def resolve_pc_action_and_advance(
    conn: sqlite3.Connection,
    session_id: str,
    *,
    action: str,
    actor_id: str,
    content_root: Path,
    campaign_slug: str | None = None,
    target_id: str | None = None,
    weapon_id: str | None = None,
    spell_id: str | None = None,
    log_event=None,
    seed: int | None = None,
) -> dict[str, Any]:
    from tomb_gm.cli.cmd_core import log_event as default_log

    log_fn = log_event or default_log
    action_result = execute_combat_action(
        conn,
        session_id,
        action=action,
        actor_id=actor_id,
        content_root=content_root,
        campaign_slug=campaign_slug,
        target_id=target_id,
        weapon_id=weapon_id,
        spell_id=spell_id,
        log_event=log_fn,
        seed=seed,
    )
    mechanical: list[dict[str, Any]] = [action_result]
    if not action_result.get("ok"):
        return {"ok": False, "error": action_result.get("error"), "mechanical": mechanical}

    adv = advance_turn(conn, session_id)
    mechanical.append({**adv, "action": "turn_advance"})
    if adv.get("round_complete"):
        init = roll_round_initiative(
            conn,
            session_id,
            content_root=content_root,
            campaign_slug=campaign_slug,
            seed=seed,
            increment_round=True,
        )
        mechanical.append(init)

    monster_results = run_monster_turns_until_pc_or_end(
        conn,
        session_id,
        content_root=content_root,
        campaign_slug=campaign_slug,
        seed=seed,
    )
    mechanical.extend(monster_results)

    end_check = finalize_combat_if_ended(
        conn, session_id, campaign_slug=campaign_slug, content_root=content_root
    )
    mechanical.append({**end_check, "action": "combat_end_check"})
    return {
        "ok": True,
        "mechanical": mechanical,
        "ended": end_check.get("ended"),
        "outcome": end_check.get("outcome"),
    }


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
    return {"ok": True, "session_id": session_id, "ended": True, "action": "combat_end"}
