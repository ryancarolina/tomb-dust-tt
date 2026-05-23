"""Sheet-backed social skill checks (canon d20)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Callable

from tomb_gm.domain.character import ability_modifier
from tomb_gm.rules.bridge import pb_for_tier, skill_bonus
from tomb_gm.services.simulation.rolls import perform_d20_roll

CANON_SOCIAL_SKILL_IDS = frozenset(
    {"persuasion", "intimidation", "deception", "etiquette", "leadership", "insight"}
)

_SOCIAL_ABILITY: dict[str, str] = {
    "persuasion": "SPI",
    "deception": "INT",
    "etiquette": "INT",
    "leadership": "SPI",
    "insight": "SPI",
}

_PLACEHOLDER_NPC_SPI_MOD = 2
_DEFAULT_PASSIVE_DC = 15


def _skill_level(sheet: dict[str, Any], skill_id: str) -> int:
    for entry in sheet.get("skills", []):
        if entry.get("skillId") == skill_id:
            return int(entry.get("level", 1))
    return 0


def _ability_mod_for_skill(sheet: dict[str, Any], skill_id: str) -> tuple[int, str]:
    attrs = sheet.get("attributes", {})
    if skill_id == "intimidation":
        str_mod = ability_modifier(int(attrs.get("STR", 10)))
        spi_mod = ability_modifier(int(attrs.get("SPI", 10)))
        if str_mod >= spi_mod:
            return str_mod, "STR"
        return spi_mod, "SPI"
    ability_key = _SOCIAL_ABILITY.get(skill_id, "SPI")
    return ability_modifier(int(attrs.get(ability_key, 10))), ability_key


def assemble_skill_modifiers(sheet: dict[str, Any], skill_id: str) -> tuple[int, list[dict[str, Any]]]:
    """Return total modifier and labeled breakdown from character sheet."""
    ability_mod, ability_label = _ability_mod_for_skill(sheet, skill_id)
    pb = pb_for_tier(int(sheet.get("classTier", 1)))
    sk_level = _skill_level(sheet, skill_id)
    sk_bonus = skill_bonus(sk_level)
    modifiers: list[dict[str, Any]] = [
        {"label": ability_label, "value": ability_mod},
        {"label": "PB", "value": pb},
        {"label": "skill", "value": sk_bonus},
    ]
    total = ability_mod + pb + sk_bonus
    return total, modifiers


def _load_npc_from_registry(content_root: Path | str, npc_id: str) -> dict[str, Any] | None:
    path = Path(content_root) / "data" / "npcs" / "key_npcs.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    for entry in data.get("npcs", data if isinstance(data, list) else []):
        if isinstance(entry, dict) and entry.get("id") == npc_id:
            return entry
    return None


def opposed_dc(
    *,
    content_root: Path | str | None = None,
    opposed_npc_id: str | None = None,
    explicit_dc: int | None = None,
) -> int:
    """Resolve DC for a social check; opposed NPC uses registry or placeholder."""
    if explicit_dc is not None:
        return int(explicit_dc)
    if opposed_npc_id and content_root:
        npc = _load_npc_from_registry(content_root, opposed_npc_id)
        if npc:
            attrs = npc.get("attributes") or {}
            spi = int(attrs.get("SPI", 10))
            tier = int(npc.get("classTier", npc.get("tier", 2)))
            return 10 + ability_modifier(spi) + pb_for_tier(tier)
        return 10 + _PLACEHOLDER_NPC_SPI_MOD
    return _DEFAULT_PASSIVE_DC


def faction_rep_dc_modifier(
    conn: sqlite3.Connection,
    campaign_slug: str,
    *,
    npc_id: str | None = None,
    faction_id: str | None = None,
) -> int:
    """Circumstance modifier from faction rep (APP-100); 0 when unavailable."""
    try:
        from tomb_gm.services.factions import rep_dc_modifier  # type: ignore[import-not-found]

        return int(
            rep_dc_modifier(
                conn,
                campaign_slug,
                npc_id=npc_id,
                faction_id=faction_id,
            )
        )
    except ImportError:
        return 0
    except Exception:
        return 0


def disposition_dc_modifier(disposition: str | None) -> int:
    if disposition == "favorable":
        return -1
    if disposition == "wary":
        return 1
    return 0


def skill_check(
    conn: sqlite3.Connection,
    campaign: str,
    character_id: str,
    skill_id: str,
    dc: int | None,
    *,
    opposed_npc_id: str | None = None,
    content_root: Path | str | None = None,
    log_event: Callable[..., Any],
    session_id: str | None = None,
    reason: str = "",
    advantage: bool = False,
    disadvantage: bool = False,
    circumstance_mod: int = 0,
    skip_faction_rep: bool = False,
    seed: int | None = None,
) -> dict[str, Any]:
    """Roll a sheet-backed d20 skill check; returns full breakdown."""
    skill_key = skill_id.strip().lower()
    if skill_key not in CANON_SOCIAL_SKILL_IDS:
        return {"ok": False, "error": f"Unknown social skill: {skill_id}"}

    row = conn.execute(
        "SELECT sheet_json FROM characters WHERE id = ? AND campaign_slug = ?",
        (character_id, campaign),
    ).fetchone()
    if not row:
        return {"ok": False, "error": f"Character not found: {character_id}"}

    sheet = json.loads(row["sheet_json"])
    mod, breakdown = assemble_skill_modifiers(sheet, skill_key)
    rep_mod = 0 if skip_faction_rep else faction_rep_dc_modifier(conn, campaign, npc_id=opposed_npc_id)
    total_mod = mod + circumstance_mod + rep_mod
    final_modifiers = list(breakdown)
    if circumstance_mod:
        final_modifiers.append({"label": "circumstance", "value": circumstance_mod})
    if rep_mod:
        final_modifiers.append({"label": "faction_rep", "value": rep_mod})

    resolved_dc = opposed_dc(
        content_root=content_root,
        opposed_npc_id=opposed_npc_id,
        explicit_dc=dc,
    )

    roll = perform_d20_roll(
        conn,
        log_event,
        session_id=session_id,
        mod=total_mod,
        dc=resolved_dc,
        reason=reason or f"{skill_key} check",
        character_id=character_id,
        seed=seed,
        advantage=advantage,
        disadvantage=disadvantage,
    )
    if not roll.get("ok"):
        return roll

    total = int(roll["total"])
    resolved_dc = int(roll["dc"] or resolved_dc)
    success = bool(roll.get("success"))
    margin = total - resolved_dc

    return {
        **roll,
        "ok": True,
        "skill_id": skill_key,
        "modifiers": final_modifiers,
        "mod": total_mod,
        "dc": resolved_dc,
        "success": success,
        "margin": margin,
        "critical": roll.get("critical", False),
    }
