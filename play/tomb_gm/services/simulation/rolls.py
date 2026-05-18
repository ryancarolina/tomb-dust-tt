from __future__ import annotations

import random
import sqlite3
from typing import Any

from tomb_gm.rules.bridge import resolve_attack, roll_d20, skill_bonus


def _rng(seed: int | None) -> random.Random:
    return random.Random(seed) if seed is not None else random.Random()


def _roll_event_id(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT last_insert_rowid()").fetchone()
    return f"evt-{row[0]}"


def perform_d20_roll(
    conn: sqlite3.Connection,
    log_event,
    *,
    session_id: str | None,
    mod: int = 0,
    dc: int | None = None,
    reason: str | None = None,
    character_id: str | None = None,
    seed: int | None = None,
    advantage: bool = False,
    disadvantage: bool = False,
) -> dict[str, Any]:
    rng = _rng(seed)
    if advantage and not disadvantage:
        natural = max(roll_d20(rng), roll_d20(rng))
    elif disadvantage and not advantage:
        natural = min(roll_d20(rng), roll_d20(rng))
    else:
        natural = roll_d20(rng)
    modifiers: list[dict[str, Any]] = []
    if mod:
        modifiers.append({"label": "mod", "value": mod})
    total = natural + mod
    success = None if dc is None else total >= dc
    critical = natural == 20
    payload = {
        "kind": "d20",
        "natural": natural,
        "modifiers": modifiers,
        "total": total,
        "dc": dc,
        "success": success,
        "critical": critical,
        "reason": reason or "",
        "character_id": character_id,
        "seed": seed,
    }
    log_event(conn, session_id, "roll", payload)
    roll_id = _roll_event_id(conn)
    return {
        "ok": True,
        "roll_id": roll_id,
        "natural": natural,
        "modifiers": modifiers,
        "total": total,
        "dc": dc,
        "success": success,
        "critical": critical,
        "reason": reason or "",
    }


def perform_attack_roll(
    conn: sqlite3.Connection,
    log_event,
    *,
    session_id: str | None,
    ability_mod: int,
    pb: int,
    skill_level: int,
    target_ac: int,
    weapon_damage: str,
    ability_damage_mod: int,
    reason: str | None = None,
    seed: int | None = None,
    natural: int | None = None,
) -> dict[str, Any]:
    rng = _rng(seed)
    skill_bonus_value = skill_bonus(skill_level)
    result, damage = resolve_attack(
        ability_mod=ability_mod,
        pb=pb,
        skill_bonus_value=skill_bonus_value,
        target_ac=target_ac,
        weapon_damage=weapon_damage,
        ability_damage_mod=ability_damage_mod,
        rng=rng,
        natural=natural,
    )
    modifiers = [
        {"label": "ability", "value": ability_mod},
        {"label": "PB", "value": pb},
        {"label": "skill", "value": skill_bonus_value},
    ]
    payload = {
        "kind": "attack",
        "natural": result.natural,
        "modifiers": modifiers,
        "total": result.total,
        "target_ac": target_ac,
        "hit": result.hit,
        "critical": result.critical,
        "damage": damage,
        "skill_level": skill_level,
        "reason": reason or "",
        "seed": seed,
    }
    log_event(conn, session_id, "roll", payload)
    roll_id = _roll_event_id(conn)
    return {
        "ok": True,
        "roll_id": roll_id,
        "natural": result.natural,
        "modifiers": modifiers,
        "total": result.total,
        "target_ac": target_ac,
        "hit": result.hit,
        "critical": result.critical,
        "damage": damage,
        "success": result.hit,
    }
