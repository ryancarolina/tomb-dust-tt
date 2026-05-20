#!/usr/bin/env python3
"""One-shot: migrate spells.json to rules 1.1.0 and append tier 3/6 spells."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPELLS_PATH = ROOT / "data" / "spells" / "spells.json"

NEW_SPELLS = [
    {
        "id": "cinder-lance",
        "displayName": "Cinder Lance",
        "school": "pyromancy",
        "tradition": "arcane",
        "tier": 3,
        "mpCost": 3,
        "castingTime": "action",
        "range": "60 ft",
        "effectType": "attack",
        "attack": {"damage": "2d6", "damageType": "fire"},
    },
    {
        "id": "root-snare",
        "displayName": "Root Snare",
        "school": "biomancy",
        "tradition": "arcane",
        "tier": 3,
        "mpCost": 3,
        "castingTime": "action",
        "range": "60 ft",
        "concentration": True,
        "duration": "1 minute",
        "effectType": "save",
        "save": {"ability": "STR"},
        "effect": "10 ft; Restrained on fail",
    },
    {
        "id": "bone-tap",
        "displayName": "Bone Tap",
        "school": "necromancy",
        "tradition": "arcane",
        "tier": 3,
        "mpCost": 3,
        "castingTime": "action",
        "range": "touch",
        "effectType": "utility",
        "save": {"ability": "SPI"},
        "effect": "Ask one dead creature one question; misleading on failed SPI save",
    },
    {
        "id": "phase-step",
        "displayName": "Phase Step",
        "school": "ether",
        "tradition": "arcane",
        "tier": 3,
        "mpCost": 3,
        "castingTime": "bonus action",
        "range": "self",
        "effectType": "utility",
        "effect": "Teleport 15 ft; +1 threat clock on thin-veil sites",
        "tags": ["thin-veil"],
    },
    {
        "id": "ward-of-dawn",
        "displayName": "Ward of Dawn",
        "school": "divine",
        "tradition": "divine",
        "tier": 3,
        "mpCost": 3,
        "castingTime": "action",
        "range": "10 ft",
        "duration": "1 minute",
        "effectType": "buff",
        "effect": "Allies in range +2 on saves vs fear",
    },
    {
        "id": "sunstorm",
        "displayName": "Sunstorm",
        "school": "pyromancy",
        "tradition": "arcane",
        "tier": 6,
        "mpCost": 6,
        "castingTime": "action",
        "range": "60 ft",
        "effectType": "save",
        "save": {"ability": "STA"},
        "damage": {"dice": "4d6", "damageType": "fire", "halfOnSave": True},
        "effect": "60 ft radius fire",
    },
    {
        "id": "adamant-ward",
        "displayName": "Adamant Ward",
        "school": "ward",
        "tradition": "arcane",
        "tier": 6,
        "mpCost": 6,
        "castingTime": "reaction",
        "range": "30 ft",
        "effectType": "buff",
        "effect": "Ally within range negates one spell hit (once per day)",
    },
    {
        "id": "world-tree-shelter",
        "displayName": "World-Tree Shelter",
        "school": "biomancy",
        "tradition": "arcane",
        "tier": 6,
        "mpCost": 6,
        "castingTime": "action",
        "range": "30 ft",
        "effectType": "utility",
        "effect": "Party gains short-rest HP/MP recovery without full hour (once per session)",
    },
    {
        "id": "lich-gate",
        "displayName": "Lich Gate",
        "school": "necromancy",
        "tradition": "arcane",
        "tier": 6,
        "mpCost": 6,
        "castingTime": "action",
        "range": "30 ft",
        "duration": "1 minute",
        "effectType": "summon",
        "summon": {"monsterId": "ash-shade", "count": 1, "tier": "elite"},
        "effect": "Summon 1 elite ash shade",
    },
    {
        "id": "rift-sever",
        "displayName": "Rift Sever",
        "school": "ether",
        "tradition": "arcane",
        "tier": 6,
        "mpCost": 6,
        "castingTime": "action",
        "range": "30 ft",
        "effectType": "attack",
        "attack": {"damage": "3d12", "damageType": "force"},
        "effect": "Closes one veil breach segment on thin-veil sites",
        "tags": ["thin-veil"],
    },
    {
        "id": "avatar-of-aven",
        "displayName": "Avatar of Aven",
        "school": "divine",
        "tradition": "divine",
        "tier": 6,
        "mpCost": 6,
        "castingTime": "action",
        "range": "self",
        "concentration": True,
        "duration": "1 minute",
        "effectType": "buff",
        "effect": "Radiant aura: undead in 10 ft take 2d6 radiant at start of your turn",
    },
]

SAVE_ABILITY_FROM_EFFECT = {
    "ash-veil": "STA",
    "entangle": "STR",
    "fear-gasp": "SPI",
    "disrupt-weave": "INT",
    "turn-ash": "SPI",
    "inferno-wave": "STA",
    "banish-unlife": "SPI",
    "overgrowth": "STR",
}


def infer_effect_type(spell: dict) -> str:
    if spell.get("effectType"):
        return spell["effectType"]
    if spell.get("summon"):
        return "summon"
    if spell.get("heal"):
        return "heal"
    if "attack" in spell:
        return "attack"
    if "save" in spell and spell.get("damage"):
        return "save"
    if "save" in spell:
        return "save"
    eff = (spell.get("effect") or "").lower()
    if "heal" in eff:
        return "heal"
    if "summon" in eff:
        return "summon"
    return "utility"


def migrate_spell(spell: dict) -> dict:
    out = dict(spell)
    out["rulesVersion"] = "1.1.0"
    save = out.get("save")
    if isinstance(save, dict):
        save = dict(save)
        save.pop("dc", None)
        sid = out.get("id", "")
        if "ability" not in save:
            save["ability"] = SAVE_ABILITY_FROM_EFFECT.get(sid, "STA")
        out["save"] = save
    sid = out.get("id", "")
    if sid == "sap-mend":
        out["heal"] = {"dice": "1d4", "addAbility": "INT"}
        out["effectType"] = "heal"
    elif sid == "mend-light":
        out["heal"] = {"dice": "1d6", "addAbility": "SPI"}
        out["effectType"] = "heal"
    elif sid == "inferno-wave":
        out["effectType"] = "save"
        out["damage"] = {"dice": "3d6", "damageType": "fire", "halfOnSave": True}
    elif sid == "overgrowth":
        out["effectType"] = "save"
        out["damage"] = {"dice": "2d6", "damageType": "piercing", "halfOnSave": True}
    elif sid == "army-of-ash":
        out["effectType"] = "summon"
        out["summon"] = {"monsterId": "ash-shade", "count": 2, "tier": "hazard"}
    else:
        out["effectType"] = infer_effect_type(out)
    return out


def main() -> None:
    spells = json.loads(SPELLS_PATH.read_text(encoding="utf-8"))
    migrated = [migrate_spell(s) for s in spells]
    existing_ids = {s["id"] for s in migrated}
    for ns in NEW_SPELLS:
        ns = migrate_spell({**ns, "rulesVersion": "1.1.0"})
        if ns["id"] not in existing_ids:
            migrated.append(ns)
            existing_ids.add(ns["id"])
    SPELLS_PATH.write_text(json.dumps(migrated, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(migrated)} spells to {SPELLS_PATH}")


if __name__ == "__main__":
    main()
