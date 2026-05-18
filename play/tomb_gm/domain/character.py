from __future__ import annotations

import json
import random
import re
import sqlite3
from datetime import datetime, timezone
from typing import Any

RULES_VERSION = "1.0.0"

TIER1_CLASSES = frozenset({"peasant", "laborer", "urchin", "apprentice", "militia", "novice"})

BASE_MP_BY_CLASS: dict[str, int] = {
    "peasant": 5,
    "laborer": 4,
    "urchin": 6,
    "apprentice": 12,
    "militia": 5,
    "novice": 10,
}

CLASS_MATCHING_SKILLS: dict[str, frozenset[str]] = {
    "peasant": frozenset({"nature", "athletics", "endurance", "engineering"}),
    "laborer": frozenset({"athletics", "endurance", "engineering"}),
    "urchin": frozenset(
        {"stealth", "sleight-of-hand", "acrobatics", "deception", "perception", "investigation"}
    ),
    "apprentice": frozenset({"lore", "spellcasting", "arcana", "engineering", "magical-knowledge"}),
    "militia": frozenset(
        {
            "swordsmanship",
            "archery",
            "shield-use",
            "unarmed-combat",
            "perception",
            "lore",
            "battlefield-awareness",
        }
    ),
    "novice": frozenset(
        {"medicine", "spellcasting", "magical-knowledge", "lore", "persuasion", "etiquette"}
    ),
}

DEFAULT_SKILLS_BY_CLASS: dict[str, list[str]] = {
    "peasant": ["nature", "athletics", "endurance"],
    "laborer": ["athletics", "endurance", "engineering"],
    "urchin": ["stealth", "sleight-of-hand", "acrobatics"],
    "apprentice": ["lore", "spellcasting", "arcana"],
    "militia": ["swordsmanship", "perception", "lore"],
    "novice": ["medicine", "spellcasting", "lore"],
}

DEFAULT_ATTRIBUTES: dict[str, int] = {
    "STR": 10,
    "AGI": 10,
    "STA": 10,
    "INT": 10,
    "SPI": 10,
    "LUC": 10,
}

ATTRIBUTE_ORDER: tuple[str, ...] = ("STR", "AGI", "STA", "INT", "SPI", "LUC")
STANDARD_ATTRIBUTE_ARRAY: list[int] = [15, 14, 13, 12, 10, 8]


class CharacterError(ValueError):
    pass


def slugify(display_name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", display_name.lower().strip())
    slug = slug.strip("-")
    if not slug or not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", slug):
        raise CharacterError(f"Invalid character name for id slug: {display_name!r}")
    return slug


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def roll_attribute_scores(rng: random.Random | None = None) -> tuple[dict[str, int], list[dict[str, Any]]]:
    """Roll 1d10 per attribute (creation.md base roll step — GM executes via CLI)."""
    roller = rng if rng is not None else random.Random()
    scores: dict[str, int] = {}
    detail: list[dict[str, Any]] = []
    for attr in ATTRIBUTE_ORDER:
        natural = roller.randint(1, 10)
        scores[attr] = natural
        detail.append({"attribute": attr, "die": "1d10", "natural": natural})
    return scores, detail


def standard_attribute_pool() -> tuple[dict[str, Any], list[int]]:
    """Fixed array; player assigns scores via character create --str etc."""
    return (
        {
            "method": "standard-array",
            "pool": list(STANDARD_ATTRIBUTE_ARRAY),
            "assign_via": "character create --str/--agi/... flags",
        },
        list(STANDARD_ATTRIBUTE_ARRAY),
    )


def compute_hp(sta: int, *, base_hp: int = 10) -> dict[str, int]:
    maximum = base_hp + sta * 5
    return {"current": maximum, "max": maximum, "base": base_hp}


def compute_mp(int_score: int, base_mp_class: str) -> dict[str, int]:
    base_mp = BASE_MP_BY_CLASS[base_mp_class]
    maximum = base_mp + int_score * 3
    return {"current": maximum, "max": maximum, "base": base_mp}


def compute_fortune_max(luc: int) -> int:
    return max(1, 1 + ability_modifier(luc))


def eligible_tier1_classes(attributes: dict[str, int]) -> list[str]:
    eligible = ["peasant"]
    if attributes["STR"] >= 8:
        eligible.append("laborer")
    if attributes["AGI"] >= 8:
        eligible.append("urchin")
    if attributes["INT"] >= 8:
        eligible.append("apprentice")
    if attributes["STR"] >= 8 or attributes["AGI"] >= 8:
        eligible.append("militia")
    if attributes["SPI"] >= 8:
        eligible.append("novice")
    return eligible


def validate_skills(base_class: str, skill_ids: list[str]) -> None:
    if len(skill_ids) != 3:
        raise CharacterError("Exactly 3 starting skills are required")
    if len(set(skill_ids)) != 3:
        raise CharacterError("Starting skills must be distinct")
    matching = CLASS_MATCHING_SKILLS[base_class]
    if not any(skill_id in matching for skill_id in skill_ids):
        raise CharacterError(
            f"At least one starting skill must match {base_class} key abilities"
        )


def build_sheet(
    *,
    character_id: str,
    display_name: str,
    base_class: str,
    attributes: dict[str, int],
    skill_ids: list[str],
    race_id: str | None = None,
    gold_gp: int = 0,
    inventory: dict[str, Any] | None = None,
    armor: dict[str, Any] | None = None,
    creation_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    base_class = base_class.lower()
    if base_class not in TIER1_CLASSES:
        raise CharacterError(f"Unknown Tier-1 class: {base_class}")
    eligible = eligible_tier1_classes(attributes)
    if base_class not in eligible:
        raise CharacterError(
            f"Class {base_class} not eligible for attributes: {', '.join(eligible)}"
        )
    validate_skills(base_class, skill_ids)
    luc = attributes.get("LUC", 10)
    fortune_max = compute_fortune_max(luc)
    sheet: dict[str, Any] = {
        "id": character_id,
        "rulesVersion": RULES_VERSION,
        "displayName": display_name,
        "attributes": {key: attributes[key] for key in ("STR", "AGI", "STA", "INT", "SPI", "LUC")},
        "classTier": 1,
        "classId": base_class,
        "baseMpClass": base_class,
        "skills": [{"skillId": skill_id, "level": 1} for skill_id in skill_ids],
        "hp": compute_hp(attributes["STA"]),
        "mp": compute_mp(attributes["INT"], base_class),
        "fortune": {"current": fortune_max, "max": fortune_max},
        "goldGp": gold_gp,
        "inventory": inventory or {"body": [], "pack": []},
        "armor": armor or {"wornId": None, "shieldId": None},
        "conditions": [],
        "deed_counters": {},
        "flags": {},
    }
    if race_id:
        sheet["raceId"] = race_id
    if creation_audit:
        sheet["creationAudit"] = creation_audit
    return sheet


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def campaign_exists(conn: sqlite3.Connection, campaign_slug: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM campaigns WHERE slug = ?",
        (campaign_slug,),
    ).fetchone()
    return row is not None


def create_character(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    display_name: str,
    base_class: str,
    attributes: dict[str, int] | None = None,
    skill_ids: list[str] | None = None,
    character_id: str | None = None,
    race_id: str | None = None,
    gold_gp: int = 0,
    inventory: dict[str, Any] | None = None,
    armor: dict[str, Any] | None = None,
    creation_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not campaign_exists(conn, campaign_slug):
        raise CharacterError(f"Campaign not found: {campaign_slug}")
    attrs = dict(DEFAULT_ATTRIBUTES)
    if attributes:
        attrs.update(attributes)
    skills = list(skill_ids or DEFAULT_SKILLS_BY_CLASS[base_class.lower()])
    char_id = character_id or slugify(display_name)
    existing = conn.execute(
        "SELECT 1 FROM characters WHERE id = ? AND campaign_slug = ?",
        (char_id, campaign_slug),
    ).fetchone()
    if existing:
        raise CharacterError(f"Character already exists: {char_id}")
    sheet = build_sheet(
        character_id=char_id,
        display_name=display_name,
        base_class=base_class,
        attributes=attrs,
        skill_ids=skills,
        race_id=race_id,
        gold_gp=gold_gp,
        inventory=inventory,
        armor=armor,
        creation_audit=creation_audit,
    )
    conn.execute(
        "INSERT INTO characters (id, campaign_slug, slot, sheet_json, alive, created_at) "
        "VALUES (?, ?, NULL, ?, 1, ?)",
        (char_id, campaign_slug, json.dumps(sheet), _now_iso()),
    )
    conn.commit()
    return {"id": char_id, "sheet": sheet}


def get_character(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    character_id: str,
) -> dict[str, Any] | None:
    row = conn.execute(
        "SELECT id, slot, sheet_json, alive, created_at FROM characters "
        "WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        return None
    sheet = json.loads(row["sheet_json"])
    return {
        "id": row["id"],
        "slot": row["slot"],
        "alive": bool(row["alive"]),
        "created_at": row["created_at"],
        "sheet": sheet,
    }


def list_characters(conn: sqlite3.Connection, *, campaign_slug: str) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, slot, sheet_json, alive, created_at FROM characters "
        "WHERE campaign_slug = ? ORDER BY created_at, id",
        (campaign_slug,),
    ).fetchall()
    result: list[dict[str, Any]] = []
    for row in rows:
        sheet = json.loads(row["sheet_json"])
        result.append(
            {
                "id": row["id"],
                "slot": row["slot"],
                "display_name": sheet.get("displayName", row["id"]),
                "class_id": sheet.get("classId"),
                "alive": bool(row["alive"]),
                "created_at": row["created_at"],
            }
        )
    return result


def set_roster_slot(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    slot: int,
    character_id: str,
    max_players: int = 4,
) -> dict[str, Any]:
    if slot < 1 or slot > max_players:
        raise CharacterError(f"Slot must be 1-{max_players}")
    if not campaign_exists(conn, campaign_slug):
        raise CharacterError(f"Campaign not found: {campaign_slug}")
    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign_slug),
    ).fetchone()
    if not row:
        raise CharacterError(f"Character not found: {character_id}")
    conn.execute(
        "UPDATE characters SET slot = NULL WHERE campaign_slug = ? AND slot = ?",
        (campaign_slug, slot),
    )
    conn.execute(
        "UPDATE characters SET slot = NULL WHERE campaign_slug = ? AND id = ?",
        (campaign_slug, character_id),
    )
    sheet = json.loads(row["sheet_json"])
    sheet["slot"] = slot
    conn.execute(
        "UPDATE characters SET slot = ?, sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (slot, json.dumps(sheet), character_id, campaign_slug),
    )
    conn.commit()
    return {"slot": slot, "character_id": character_id, "display_name": sheet.get("displayName")}


def clear_roster_slot(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
    slot: int,
    max_players: int = 4,
) -> dict[str, Any]:
    if slot < 1 or slot > max_players:
        raise CharacterError(f"Slot must be 1-{max_players}")
    row = conn.execute(
        "SELECT id, sheet_json FROM characters WHERE campaign_slug = ? AND slot = ?",
        (campaign_slug, slot),
    ).fetchone()
    if not row:
        return {"slot": slot, "cleared": False}
    sheet = json.loads(row["sheet_json"])
    sheet.pop("slot", None)
    conn.execute(
        "UPDATE characters SET slot = NULL, sheet_json = ? WHERE id = ? AND campaign_slug = ?",
        (json.dumps(sheet), row["id"], campaign_slug),
    )
    conn.commit()
    return {"slot": slot, "cleared": True, "character_id": row["id"]}


def roster_summary(
    conn: sqlite3.Connection,
    *,
    campaign_slug: str,
) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT id, slot, sheet_json FROM characters "
        "WHERE campaign_slug = ? AND slot IS NOT NULL ORDER BY slot",
        (campaign_slug,),
    ).fetchall()
    party: list[dict[str, Any]] = []
    for row in rows:
        sheet = json.loads(row["sheet_json"])
        hp = sheet.get("hp", {})
        party.append(
            {
                "slot": row["slot"],
                "character_id": row["id"],
                "display_name": sheet.get("displayName", row["id"]),
                "class_id": sheet.get("classId"),
                "hp": f"{hp.get('current', '?')}/{hp.get('max', '?')}",
            }
        )
    return party
