"""Structured character creation state machine.

Tracks which step the player is on and provides per-step context
to the LLM so it doesn't hallucinate, truncate, or double-call tools.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tomb_gm.domain.character import CharacterError, validate_skills

_DATA_ROOT = Path(__file__).resolve().parents[2] / "build" / "data"

CREATION_STEPS = [
    "NAME",
    "RACE",
    "ROLL_STATS",
    "CLASS",
    "SKILLS",
    "SPELL_SCHOOLS",
    "SPELLS",
    "EQUIPMENT_GOLD",
    "FINALIZE",
    "WORLD_INTRO",
]

# Canonical skill slugs (match play/tomb_gm/domain/character.py)
ALL_SKILL_SLUGS: tuple[str, ...] = (
    "swordsmanship", "archery", "shield-use", "unarmed-combat",
    "dual-wielding", "heavy-weapons", "thrown-weapons", "crossbow",
    "athletics", "acrobatics", "climbing", "swimming", "endurance",
    "stealth", "sleight-of-hand", "lockpicking", "disguise",
    "lore", "investigation", "perception", "nature", "engineering",
    "spellcasting", "arcana", "magical-knowledge", "mana-control",
    "persuasion", "deception", "etiquette", "intimidation",
    "medicine", "battlefield-awareness",
)

SKILL_DISPLAY: dict[str, str] = {slug: slug.replace("-", " ").title() for slug in ALL_SKILL_SLUGS}

SKILL_PARSE_ALIASES: dict[str, str] = {
    "shield use": "shield-use",
    "sleight of hand": "sleight-of-hand",
    "magical knowledge": "magical-knowledge",
    "battlefield awareness": "battlefield-awareness",
    "unarmed combat": "unarmed-combat",
    "dual wielding": "dual-wielding",
    "heavy weapons": "heavy-weapons",
    "thrown weapons": "thrown-weapons",
    "mana control": "mana-control",
}


def _compact_skill_token(s: str) -> str:
    return s.replace(" ", "").replace("-", "")


def _build_skill_compact_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    for slug in ALL_SKILL_SLUGS:
        mapping[_compact_skill_token(slug)] = slug
    for alias, target in SKILL_PARSE_ALIASES.items():
        mapping[_compact_skill_token(alias)] = target
    return mapping


_SKILL_COMPACT_MAP: dict[str, str] = _build_skill_compact_map()

SKILL_CATEGORIES: dict[str, list[str]] = {
    "Combat": ["swordsmanship", "archery", "shield-use", "unarmed-combat", "crossbow"],
    "Physical": ["athletics", "acrobatics", "climbing", "swimming", "endurance"],
    "Subterfuge": ["stealth", "sleight-of-hand", "lockpicking", "disguise"],
    "Mental": ["lore", "investigation", "perception", "nature", "engineering"],
    "Magic": ["spellcasting", "arcana", "magical-knowledge", "mana-control"],
    "Social": ["persuasion", "deception", "etiquette", "intimidation"],
    "Other": ["medicine", "battlefield-awareness"],
}

CREATION_STATUS_LABELS: dict[str, str] = {
    "NAME": "NAME_INPUT",
    "RACE": "RACE_INPUT",
    "ROLL_STATS": "STATS_REVIEW",
    "CLASS": "CLASS_INPUT",
    "SKILLS": "SKILLS_INPUT",
    "SPELL_SCHOOLS": "SPELL_SCHOOLS_INPUT",
    "SPELLS": "SPELLS_INPUT",
    "EQUIPMENT_GOLD": "EQUIPMENT_GOLD_CONFIRMATION",
    "FINALIZE": "FINALIZE",
    "WORLD_INTRO": "RECEPTION_CHOICE",
}

CREATION_STEP_DISPLAY: dict[str, str] = {
    "NAME": "Name",
    "RACE": "Race",
    "ROLL_STATS": "Roll Stats",
    "CLASS": "Class",
    "SKILLS": "Skills",
    "SPELL_SCHOOLS": "Spell Schools",
    "SPELLS": "Spells",
    "EQUIPMENT_GOLD": "Equipment & Gold",
    "FINALIZE": "Finalize",
    "WORLD_INTRO": "Reception",
}


def format_creation_step_display(step: str) -> str:
    return CREATION_STEP_DISPLAY.get(step) or step.replace("_", " ").title()

_LLM_STATUS_TAG_RE = re.compile(
    r"\[Location:[^\]]*\]"
    r"|\[Phase:[^\]]*\]"
    r"|\[[^\]]*(?:\bLocation:|\bPhase:|\bHP:|\bFortune:|\bGP:|\bTurn:|\bAwaiting:)[^\]]*\]"
    r"|Awaiting:\s*[A-Z0-9_]+",
    re.I | re.MULTILINE,
)

_MEMORY_BANNER_RE = re.compile(
    r"^\s*\*\*Campaign Memory Updated:?\*\*\s*$",
    re.I | re.MULTILINE,
)
_TRAILING_MEMORY_BLOCK_RE = re.compile(
    r"\n---\s*\n\s*\*\*Campaign Memory Updated:?\*\*\s*",
    re.I,
)

CLARIFICATION_RE = re.compile(
    r"(don't see|dont see|not see|what are|what skills|list|show me|options|"
    r"which skills|help|\?|repeat|display|where are)",
    re.I,
)

EQUIPMENT_CONFIRM_RE = re.compile(
    r"\b(yes|yeah|yep|confirm|confirmed|ready|accept|ok|okay|"
    r"let'?s go|lets go|begin|start|good|fine|proceed|continue)\b",
    re.I,
)

EQUIPMENT_OBJECTION_RE = re.compile(
    r"(didn't pick|didnt pick|wrong|wait|hold on|not yet|go back|"
    r"change|didn't get|didnt get|not my|fix|redo)",
    re.I,
)

RACES = {
    "human": {"description": "Adaptable and versatile. +1 to any two attributes.", "mods": {}},
    "high-elf": {"description": "Graceful and wise, excelling in arcane arts.", "mods": {"INT": 2, "AGI": 1}},
    "dark-elf": {"description": "Masters of the underworld's depths and dark magic.", "mods": {"AGI": 2, "INT": 1, "SPI": -1}},
    "wood-elf": {"description": "Agile forest masters, connected to nature.", "mods": {"AGI": 2, "SPI": 1}},
    "dwarf": {"description": "Resilient masters of craftsmanship and mining.", "mods": {"STA": 2, "STR": 1, "AGI": -1}},
    "halfling": {"description": "Small but resilient, nimble and spirited.", "mods": {"AGI": 2, "SPI": 1}},
    "centaur": {"description": "Powerful plains-roaming protectors of nature.", "mods": {"STR": 2, "AGI": 1, "INT": -1}},
    "aquarid": {"description": "Deep-sea humanoids who excel in water manipulation.", "mods": {"AGI": 2, "SPI": 1, "STA": -1}},
    "demonkin": {"description": "Born from Thar's essence, adept in dark magic.", "mods": {"SPI": 2, "STR": 1, "AGI": -1}},
    "orc": {"description": "Fierce warriors of brute strength and resilience.", "mods": {"STR": 2, "STA": 1, "INT": -1}},
    "gnome": {"description": "Inventive and quick-witted tinkers and arcanists.", "mods": {"INT": 2, "AGI": 1, "STR": -1}},
    "dragonkin": {"description": "Powerful beings with dragon blood and elemental affinity.", "mods": {"STR": 2, "SPI": 1, "AGI": -1}},
    "faerie": {"description": "Tiny magical tricksters, agile and cunning.", "mods": {"AGI": 2, "INT": 1, "STR": -1}},
    "minotaur": {"description": "Imposing warriors of great strength and endurance.", "mods": {"STR": 2, "STA": 1, "INT": -1}},
    "undead": {"description": "Raised from death, resilient with strong will and necromantic talent.", "mods": {"SPI": 2, "STA": 1, "AGI": -1}},
    "troll": {"description": "Tall regenerators and fierce hunters.", "mods": {"STR": 2, "AGI": 1, "INT": -1}},
}


def race_display_title(race_key: str) -> str:
    return race_key.replace("-", " ").title()


CLASS_INFO = {
    "peasant": {
        "requirement": "None",
        "description": "Common folk — resourceful survivors with broad practical knowledge.",
        "key_skills": ["Nature", "Athletics", "Endurance", "Engineering"],
        "base_mp": 5,
        "kit": "Club, sling, backpack, bedroll, rations ×5, waterskin, flint and steel, pouch",
        "base_gp": 10,
    },
    "laborer": {
        "requirement": "STR 8+",
        "description": "Hard workers — strong backs and iron determination.",
        "key_skills": ["Athletics", "Endurance", "Engineering"],
        "base_mp": 4,
        "kit": "Quarterstaff, padded armor, backpack, rope (50 ft), rations ×5, healer's kit",
        "base_gp": 15,
    },
    "urchin": {
        "requirement": "AGI 8+",
        "description": "Street rats — quick hands, sharp eyes, and survival instincts.",
        "key_skills": ["Stealth", "Sleight of Hand", "Acrobatics", "Deception", "Perception", "Investigation"],
        "base_mp": 6,
        "kit": "Dagger, leather armor, thieves' tools, backpack, rations ×3, pouch",
        "base_gp": 5,
    },
    "apprentice": {
        "requirement": "INT 8+",
        "description": "Aspiring arcanists — books, spells, and the hunger for knowledge.",
        "key_skills": ["Lore", "Spellcasting", "Arcana", "Engineering", "Magical Knowledge"],
        "base_mp": 12,
        "kit": "Quarterstaff, spellbook, ink and quill, herbalism kit, backpack, rations ×5",
        "base_gp": 20,
    },
    "militia": {
        "requirement": "STR 8+ or AGI 8+",
        "description": "Trained fighters — disciplined, armed, ready for the line.",
        "key_skills": ["Swordsmanship", "Archery", "Shield Use", "Perception", "Lore", "Battlefield Awareness"],
        "base_mp": 5,
        "kit": "Spear, shortsword, studded leather, buckler, backpack, healer's kit, rations ×5, bedroll",
        "base_gp": 25,
    },
    "novice": {
        "requirement": "SPI 8+",
        "description": "Acolytes of the divine — healing, blessings, and spiritual fortitude.",
        "key_skills": ["Medicine", "Spellcasting", "Magical Knowledge", "Lore", "Persuasion", "Etiquette"],
        "base_mp": 10,
        "kit": "Warhammer, leather armor, holy symbol, healer's kit, backpack, rations ×5",
        "base_gp": 15,
    },
}

LIFE_EVENT_GP_MODS = {
    "Severe Illness": -5, "Grueling Labor": 5, "Athletic Training": 0,
    "Intense Study": 10, "Mystical Encounter": 15, "Childhood Trauma": -10,
    "Adventurous Upbringing": 5, "Scholarly Pursuits": 15, "Peaceful Life": 0,
    "Isolated Childhood": -5, "Military Training": 10, "Magical Awakening": 20,
    "Parental Loss": -5, "Orphaned Young": -10, "Hard Labor": 5,
    "Blessed with Health": 5, "Nimble Childhood": 0, "Farm Life": 5,
    "Severe Injury": -10, "Early Mentorship": 10, "Harsh Environment": -5,
    "Frequent Travel": 5, "Sickness Recovery": 0, "Rich Education": 25,
    "Desert Life": -5, "Lonely Upbringing": -5, "Combat Training": 10,
    "Regular Meditation": 5, "Nomadic Life": 0, "Repeated Trauma": -15,
    "Street Smarts": 5, "High Society": 30, "Religious Upbringing": 10,
    "War Survivor": 0, "Jungle Life": -5, "Early Loss of Family": -10,
    "Forest Dweller": 0, "Wealthy Childhood": 35, "Harsh Winters": -5,
    "Unremarkable Youth": 0,
}


@dataclass
class CreationState:
    """Tracks character creation progress."""

    active: bool = False
    step: str = "NAME"
    name: str = ""
    race: str = ""
    roll_result: dict = field(default_factory=dict)
    chosen_class: str = ""
    chosen_skills: list[str] = field(default_factory=list)
    chosen_schools: list[str] = field(default_factory=list)
    chosen_spells: list[str] = field(default_factory=list)
    starting_gold: int = 0
    equipment_kit: str = ""
    skills_table_shown: bool = False
    schools_table_shown: bool = False
    spells_table_shown: bool = False
    races_table_shown: bool = False
    classes_table_shown: bool = False
    gold_roll: int = 0

    def advance(self):
        idx = CREATION_STEPS.index(self.step)
        if idx < len(CREATION_STEPS) - 1:
            self.step = CREATION_STEPS[idx + 1]
        if self.step == "RACE":
            self.races_table_shown = False
        if self.step == "CLASS":
            self.classes_table_shown = False
        if self.step == "SKILLS":
            self.skills_table_shown = False
            self.chosen_skills = []
        if self.step == "SPELL_SCHOOLS":
            self.schools_table_shown = False
            self.chosen_schools = []
        if self.step == "SPELLS":
            self.spells_table_shown = False
            self.chosen_spells = []
        skip_inapplicable_spell_steps(self)

    def is_complete(self) -> bool:
        return self.step == "WORLD_INTRO" or not self.active

    def to_dict(self) -> dict:
        return {
            "active": self.active,
            "step": self.step,
            "name": self.name,
            "race": self.race,
            "chosen_class": self.chosen_class,
            "chosen_skills": list(self.chosen_skills),
            "chosen_schools": list(self.chosen_schools),
            "chosen_spells": list(self.chosen_spells),
            "starting_gold": self.starting_gold,
            "skills_table_shown": self.skills_table_shown,
            "schools_table_shown": self.schools_table_shown,
            "spells_table_shown": self.spells_table_shown,
            "races_table_shown": self.races_table_shown,
            "classes_table_shown": self.classes_table_shown,
            "roll_result": self.roll_result,
            "equipment_kit": self.equipment_kit,
            "gold_roll": self.gold_roll,
        }

    @classmethod
    def from_dict(cls, data: dict) -> CreationState:
        return cls(
            active=bool(data.get("active", False)),
            step=data.get("step", "NAME"),
            name=data.get("name", ""),
            race=data.get("race", ""),
            roll_result=dict(data.get("roll_result") or {}),
            chosen_class=data.get("chosen_class", ""),
            chosen_skills=list(data.get("chosen_skills") or []),
            chosen_schools=list(data.get("chosen_schools") or []),
            chosen_spells=list(data.get("chosen_spells") or []),
            starting_gold=int(data.get("starting_gold") or 0),
            equipment_kit=data.get("equipment_kit", ""),
            skills_table_shown=bool(data.get("skills_table_shown", False)),
            schools_table_shown=bool(data.get("schools_table_shown", False)),
            spells_table_shown=bool(data.get("spells_table_shown", False)),
            races_table_shown=bool(data.get("races_table_shown", False)),
            classes_table_shown=bool(data.get("classes_table_shown", False)),
            gold_roll=int(data.get("gold_roll") or 0),
        )


def normalize_skill_slug(name: str) -> str | None:
    """Map player/LLM skill text to a canonical slug."""
    lower = name.strip().lower()
    if lower in ALL_SKILL_SLUGS:
        return lower
    if lower in SKILL_PARSE_ALIASES:
        return SKILL_PARSE_ALIASES[lower]
    hyphen = lower.replace(" ", "-")
    if hyphen in ALL_SKILL_SLUGS:
        return hyphen
    compact = _SKILL_COMPACT_MAP.get(_compact_skill_token(lower))
    if compact:
        return compact
    return None


def class_key_skill_slugs(class_key: str) -> set[str]:
    info = CLASS_INFO.get(class_key, CLASS_INFO["peasant"])
    slugs: set[str] = set()
    for label in info["key_skills"]:
        slug = normalize_skill_slug(label)
        if slug:
            slugs.add(slug)
    return slugs


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def school_catalog() -> list[dict[str, Any]]:
    return _load_json(_DATA_ROOT / "spells" / "schools.json")


def spell_catalog() -> list[dict[str, Any]]:
    return _load_json(_DATA_ROOT / "spells" / "spells.json")


def starting_spell_profile(class_key: str) -> dict[str, Any] | None:
    data = _load_json(_DATA_ROOT / "character" / "starting-spells.json")
    return data.get("profiles", {}).get(class_key)


def needs_spell_picks(state: CreationState) -> bool:
    return (
        state.chosen_class in ("novice", "apprentice")
        and "spellcasting" in state.chosen_skills
    )


def skip_inapplicable_spell_steps(state: CreationState) -> None:
    if needs_spell_picks(state):
        return
    while state.step in ("SPELL_SCHOOLS", "SPELLS"):
        idx = CREATION_STEPS.index(state.step)
        if idx >= len(CREATION_STEPS) - 1:
            break
        state.step = CREATION_STEPS[idx + 1]


def _school_by_id(school_id: str) -> dict[str, Any] | None:
    for school in school_catalog():
        if school["id"] == school_id:
            return school
    return None


def eligible_schools_for_class(class_key: str) -> list[dict[str, Any]]:
    profile = starting_spell_profile(class_key) or {}
    schools = school_catalog()
    if profile.get("schoolFilter") == "arcane":
        return [s for s in schools if s.get("tradition") == "arcane"]
    return list(schools)


def tier1_spells_for_schools(school_ids: list[str]) -> list[dict[str, Any]]:
    chosen = set(school_ids)
    return [
        sp for sp in spell_catalog()
        if sp.get("school") in chosen and int(sp.get("tier", 99)) == 1
    ]


def format_schools_table(chosen_class: str) -> str:
    profile = starting_spell_profile(chosen_class) or {}
    pick_count = int(profile.get("schoolPickCount", 2))
    schools = eligible_schools_for_class(chosen_class)
    if chosen_class == "novice":
        rule = "Choose **Divine** plus **1 other school** (2 total)."
    else:
        rule = f"Choose **{pick_count} arcane schools**."
    lines = [
        rule,
        "Reply with school names or ids, comma-separated.",
        "",
        "| School | Tradition | Themes |",
        "|:-------|:----------|:-------|",
    ]
    for school in schools:
        themes = ", ".join(school.get("themes", [])[:3])
        lines.append(
            f"| {school['displayName']} (`{school['id']}`) | {school.get('tradition', '?')} | {themes} |"
        )
    return "\n".join(lines)


def format_spells_table(chosen_class: str, school_ids: list[str]) -> str:
    profile = starting_spell_profile(chosen_class) or {}
    pick_count = int(profile.get("spellPickCount", 2))
    spells = tier1_spells_for_schools(school_ids)
    divine_note = ""
    if profile.get("minDivineSpells"):
        divine_note = " At least **1** must be from the **Divine** school."
    lines = [
        f"Pick **{pick_count} tier-1 spells** from your chosen schools.{divine_note}",
        "Reply with spell names or ids, comma-separated.",
        "",
        "| Spell | School | MP | Effect |",
        "|:------|:-------|:---|:-------|",
    ]
    for spell in sorted(spells, key=lambda s: (s.get("school", ""), s.get("displayName", ""))):
        effect = spell.get("effect") or spell.get("effectType", "")
        if spell.get("heal"):
            effect = f"Heal {spell['heal'].get('dice', '?')}"
        elif spell.get("attack"):
            effect = f"Attack {spell['attack'].get('damage', '?')}"
        lines.append(
            f"| {spell['displayName']} (`{spell['id']}`) | {spell.get('school', '?')} | "
            f"{spell.get('mpCost', '?')} | {effect} |"
        )
    return "\n".join(lines)


def normalize_school_id(name: str) -> str | None:
    lower = name.strip().lower().replace(" ", "-")
    for school in school_catalog():
        sid = school["id"]
        display = school["displayName"].lower()
        if lower in (sid, display, display.replace(" ", "-")):
            return sid
        if lower in display or sid in lower:
            return sid
    return None


def normalize_spell_id(name: str, *, school_ids: list[str]) -> str | None:
    lower = name.strip().lower().replace(" ", "-")
    for spell in tier1_spells_for_schools(school_ids):
        sid = spell["id"]
        display = spell["displayName"].lower()
        if lower in (sid, display, display.replace(" ", "-")):
            return sid
        if lower in display or sid in lower:
            return sid
    return None


def validate_school_picks(class_key: str, school_ids: list[str]) -> str | None:
    profile = starting_spell_profile(class_key)
    if not profile:
        return "No spell profile for this class."
    pick_count = int(profile.get("schoolPickCount", 2))
    if len(school_ids) != pick_count:
        return f"Need exactly {pick_count} schools, got {len(school_ids)}."
    if len(set(school_ids)) != len(school_ids):
        return "Schools must be distinct."
    eligible = {s["id"] for s in eligible_schools_for_class(class_key)}
    for sid in school_ids:
        if sid not in eligible:
            return f"School '{sid}' is not eligible for {class_key}."
    if class_key == "novice" and "divine" not in school_ids:
        return "Novice must include the Divine school."
    if profile.get("schoolFilter") == "arcane":
        for sid in school_ids:
            school = _school_by_id(sid)
            if school and school.get("tradition") != "arcane":
                return f"Apprentice may only pick arcane schools (not {sid})."
    return None


def validate_spell_picks(class_key: str, school_ids: list[str], spell_ids: list[str]) -> str | None:
    profile = starting_spell_profile(class_key)
    if not profile:
        return "No spell profile for this class."
    pick_count = int(profile.get("spellPickCount", 2))
    if len(spell_ids) != pick_count:
        return f"Need exactly {pick_count} spells, got {len(spell_ids)}."
    if len(set(spell_ids)) != len(spell_ids):
        return "Spells must be distinct."
    allowed = {sp["id"] for sp in tier1_spells_for_schools(school_ids)}
    for sid in spell_ids:
        if sid not in allowed:
            return f"Spell '{sid}' is not tier-1 from your chosen schools."
    if profile.get("minDivineSpells"):
        divine_ids = {
            sp["id"] for sp in tier1_spells_for_schools(["divine"])
        }
        if not any(sp in divine_ids for sp in spell_ids):
            return "At least one spell must be from the Divine school."
    return None


def parse_player_schools(text: str, class_key: str) -> list[str] | None:
    if is_clarification(text):
        return None
    lower = text.lower()
    if "," in lower:
        parts = [p.strip() for p in lower.split(",") if p.strip()]
        slugs = []
        for part in parts:
            sid = normalize_school_id(part)
            if sid and sid not in slugs:
                slugs.append(sid)
        profile = starting_spell_profile(class_key) or {}
        if len(slugs) == int(profile.get("schoolPickCount", 2)):
            return slugs
    found: list[str] = []
    for school in sorted(eligible_schools_for_class(class_key), key=lambda s: len(s["displayName"]), reverse=True):
        sid = school["id"]
        display = school["displayName"].lower()
        if (display in lower or sid in lower) and sid not in found:
            found.append(sid)
    profile = starting_spell_profile(class_key) or {}
    if len(found) == int(profile.get("schoolPickCount", 2)):
        return found
    return None


def parse_player_spells(text: str, class_key: str, school_ids: list[str]) -> list[str] | None:
    if is_clarification(text):
        return None
    lower = text.lower()
    if "," in lower:
        parts = [p.strip() for p in lower.split(",") if p.strip()]
        slugs = []
        for part in parts:
            sid = normalize_spell_id(part, school_ids=school_ids)
            if sid and sid not in slugs:
                slugs.append(sid)
        profile = starting_spell_profile(class_key) or {}
        if len(slugs) == int(profile.get("spellPickCount", 2)):
            return slugs
    found: list[str] = []
    for spell in sorted(tier1_spells_for_schools(school_ids), key=lambda s: len(s["displayName"]), reverse=True):
        sid = spell["id"]
        display = spell["displayName"].lower()
        if (display in lower or sid in lower) and sid not in found:
            found.append(sid)
    profile = starting_spell_profile(class_key) or {}
    if len(found) == int(profile.get("spellPickCount", 2)):
        return found
    return None


def strip_llm_status_tags(text: str) -> str:
    """Remove LLM-invented status footer blocks; code owns Awaiting/Location lines."""
    cleaned = _LLM_STATUS_TAG_RE.sub("", text or "")
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def strip_llm_meta_narration(text: str) -> str:
    """Remove LLM meta leaks (campaign memory banners) from player-facing prose."""
    if not (text or "").strip():
        return ""
    cleaned = _TRAILING_MEMORY_BLOCK_RE.sub("", text or "")
    cleaned = _MEMORY_BANNER_RE.sub("", cleaned)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


_RACE_TABLE_HEADER_RE = re.compile(r"^\s*\| Race \|", re.MULTILINE)
_MD_TABLE_SEPARATOR_RE = re.compile(r"^\s*\|[-:\s|]+\|\s*$")
_MD_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|")
_STATS_TABLE_HEADER_RE = re.compile(r"^\s*\| Attr \|")
_STATS_HEADING_RE = re.compile(r"^\s*#{1,3}\s+Your Attributes\b", re.IGNORECASE)
_COMPACT_ATTR_HEADER_RE = re.compile(r"^\s*\| STR \|.*\| AGI \|")


def strip_flavor_race_table(text: str) -> str:
    """Remove markdown race tables from LLM flavor; code owns format_races_table() body."""
    if not (text or "").strip():
        return ""
    lines = (text or "").splitlines()
    keep: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if _RACE_TABLE_HEADER_RE.match(line):
            i += 1
            if i < len(lines) and _MD_TABLE_SEPARATOR_RE.match(lines[i]):
                i += 1
            while i < len(lines) and _MD_TABLE_ROW_RE.match(lines[i]):
                i += 1
            continue
        keep.append(line)
        i += 1
    out_lines = [ln for ln in keep if "| Race |" not in ln]
    result = "\n".join(out_lines)
    return re.sub(r"\n{3,}", "\n\n", result).strip()


def strip_flavor_stats_table(text: str) -> str:
    """Remove markdown stat tables from LLM flavor; code owns format_roll_stats_table() body."""
    if not (text or "").strip():
        return ""
    lines = (text or "").splitlines()
    keep: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if (
            _STATS_TABLE_HEADER_RE.match(line)
            or _STATS_HEADING_RE.match(line)
            or _COMPACT_ATTR_HEADER_RE.match(line)
        ):
            i += 1
            if i < len(lines) and _MD_TABLE_SEPARATOR_RE.match(lines[i]):
                i += 1
            while i < len(lines) and _MD_TABLE_ROW_RE.match(lines[i]):
                i += 1
            continue
        keep.append(line)
        i += 1
    out_lines = [
        ln
        for ln in keep
        if "| Attr | Base |" not in ln
        and "`roll_attributes(" not in ln
        and "| STR | AGI |" not in ln
    ]
    result = "\n".join(out_lines)
    return re.sub(r"\n{3,}", "\n\n", result).strip()


_PREMATURE_FLAVOR_MARKERS = (
    re.compile(r"pre[-_]?delve", re.IGNORECASE),
    re.compile(r"awaiting:\s*reception_choice", re.IGNORECASE),
    re.compile(r"registered\s+delver", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a\s+registered", re.IGNORECASE),
    re.compile(r"is\s+now\s+a\s+registered", re.IGNORECASE),
)
_PREMATURE_PREPARATION_PHASE_RE = re.compile(r"phase:\s*preparation", re.IGNORECASE)


def sanitize_premature_completion_flavor(
    flavor: str,
    *,
    active: bool,
    step: str,
    roster_len: int = 0,
) -> str:
    """Blank flavor that invents post-creation completion while desk FSM is active."""
    if not (flavor or "").strip():
        return ""
    for pattern in _PREMATURE_FLAVOR_MARKERS:
        if pattern.search(flavor):
            return ""
    if active and step != "WORLD_INTRO" and _PREMATURE_PREPARATION_PHASE_RE.search(flavor):
        return ""
    return flavor


def format_creation_status(state: CreationState) -> str:
    """Code-owned footer line for creation UI and suggestion parsing."""
    label = CREATION_STATUS_LABELS.get(state.step, f"{state.step}_INPUT")
    return f"Awaiting: {label}"


def _primary_roster_entry(status: dict) -> dict:
    roster = status.get("roster") or []
    if not roster:
        return {}
    return min(roster, key=lambda r: r.get("slot", 999))


def format_exploration_status(status: dict) -> str:
    """Code-owned bracket footer for exploration/combat narration."""
    party = status.get("party") or {}
    location = party.get("display_address") or party.get("address") or "?"
    phase = party.get("phase") or "?"

    primary = _primary_roster_entry(status)
    hp = primary.get("hp") or "?/?"
    fortune = primary.get("fortune") or "?/1"
    gold = primary.get("gold", 0) if primary else 0
    gp = str(gold) if primary else "0"
    transit = int(party.get("gold_in_transit") or 0)
    if transit > 0:
        gp = f"{gold} (+{transit} transit)"

    awaiting = status.get("awaiting") or "?"
    turn_part = ""
    combat = status.get("combat")
    if combat:
        turn_id = combat.get("turn_id") or "?"
        turn_part = f" | Turn: {turn_id}"

    return (
        f"[Location: {location} | Phase: {phase} | HP: {hp} | Fortune: {fortune} | "
        f"GP: {gp}{turn_part} | Awaiting: {awaiting}]"
    )


def format_races_table() -> str:
    lines = [
        "Pick **one race**. Reply with the race name.",
        "",
        "| Race | Adjustments | Description |",
        "|:------|:-------------|:-------------|",
    ]
    for name, info in RACES.items():
        lines.append(
            f"| {name.replace('-', ' ').title()} | {_format_mods(info['mods'])} | {info['description']} |"
        )
    return "\n".join(lines)


def format_roll_stats_table(roll_result: dict) -> str:
    """Code-owned attribute breakdown after roll_attributes."""
    life_event = roll_result.get("life_event", {})
    final_attributes = roll_result.get("final_attributes", {})
    base_rolls = roll_result.get("base_rolls", {})
    genetic_factors = roll_result.get("genetic_factors", {})
    racial_adjustments = roll_result.get("racial_adjustments", {})

    lines = [
        f"Life event: {life_event.get('name', 'Unknown')}",
        "",
        "| Attr | Base | Genetic | Life Evt | Racial | Final |",
        "|:------|-----:|--------:|---------:|-------:|------:|",
    ]
    for attr in ("STR", "AGI", "STA", "INT", "SPI"):
        base = base_rolls.get(attr, 0)
        gf = genetic_factors.get(attr, {})
        genetic = gf.get("mod", 0) if isinstance(gf, dict) else gf
        life_mod = life_event.get("mods", {}).get(attr, 0)
        racial = racial_adjustments.get(attr, 0)
        final = final_attributes.get(attr, 0)
        lines.append(
            f"| {attr} | {base} | {genetic} | {life_mod} | {racial} | {final} |"
        )
    luc = final_attributes.get("LUC", 0)
    lines.append(f"| LUC | — | — | — | — | {luc} |")
    sta = final_attributes.get("STA", 10)
    hp = 10 + sta * 5
    lines.extend(["", f"**HP:** {hp} (10 + STA {sta} × 5)"])
    return "\n".join(lines)


def format_classes_table(eligible: list[str]) -> str:
    lines = [
        "Pick **one tier-1 class** you qualify for.",
        "",
        "| Class | Requirement | Key skills | Starting GP |",
        "|:------|:-------------|:-----------|:------------|",
    ]
    for cls in eligible:
        info = CLASS_INFO.get(cls)
        if not info:
            continue
        keys = ", ".join(info["key_skills"][:4])
        lines.append(
            f"| {cls.title()} | {info['requirement']} | {keys} | {info['base_gp']} gp |"
        )
    return "\n".join(lines)


def format_equipment_summary(state: CreationState) -> str:
    """Kit and gold from ensure_equipment_gold — not LLM prose."""
    ensure_equipment_gold(state)
    skills = ", ".join(SKILL_DISPLAY.get(s, s) for s in state.chosen_skills)
    return (
        f"**Registry kit:** {state.equipment_kit}\n\n"
        f"**Starting gold:** {state.starting_gold} gp\n\n"
        f"**Skills on record:** {skills or '—'}\n\n"
        f"Reply **yes** or **ready** to accept and finalize registration."
    )


def format_skills_table(chosen_class: str) -> str:
    """Build the full skills pick table for character creation."""
    key_slugs = class_key_skill_slugs(chosen_class)
    key_names = ", ".join(SKILL_DISPLAY[s] for s in sorted(key_slugs))
    lines = [
        f"Pick **3 skills** (level 1). At least 1 must be a {chosen_class.title()} key skill "
        f"({key_names}). Reply with three names, comma-separated.",
        "",
        "| Category | Skill | Class key? |",
        "|:---------|:------|:-----------|",
    ]
    for category, slugs in SKILL_CATEGORIES.items():
        for slug in slugs:
            marker = "★" if slug in key_slugs else ""
            lines.append(f"| {category} | {SKILL_DISPLAY[slug]} | {marker} |")
    return "\n".join(lines)


def ensure_equipment_gold(state: CreationState) -> None:
    """Compute kit and starting gold once when entering EQUIPMENT_GOLD."""
    if state.starting_gold > 0 and state.equipment_kit:
        return
    cls = state.chosen_class or "peasant"
    info = CLASS_INFO.get(cls, CLASS_INFO["peasant"])
    life_event_name = state.roll_result.get("life_event", {}).get("name", "Unremarkable Youth")
    gp_mod = LIFE_EVENT_GP_MODS.get(life_event_name, 0)
    base_gp = info["base_gp"]
    if state.gold_roll <= 0:
        state.gold_roll = random.randint(1, 6)
    state.starting_gold = max(0, (base_gp + gp_mod) * state.gold_roll)
    state.equipment_kit = info["kit"]


def is_clarification(text: str) -> bool:
    return bool(CLARIFICATION_RE.search(text.strip()))


def is_equipment_confirm(text: str) -> bool:
    return bool(EQUIPMENT_CONFIRM_RE.search(text.strip()))


def is_equipment_objection(text: str) -> bool:
    return bool(EQUIPMENT_OBJECTION_RE.search(text.strip()))


def validate_skill_picks(class_key: str, skill_ids: list[str]) -> str | None:
    """Return error message if invalid, else None."""
    if len(skill_ids) != 3:
        return f"Need exactly 3 skills, got {len(skill_ids)}."
    if len(set(skill_ids)) != 3:
        return "Skills must be distinct."
    for slug in skill_ids:
        if slug not in ALL_SKILL_SLUGS:
            return f"Unknown skill '{slug}'."
    try:
        validate_skills(class_key, skill_ids)
    except CharacterError as exc:
        return str(exc)
    return None


def parse_player_race(text: str) -> str | None:
    """Try to match player input to a valid race key."""
    lower = text.lower().strip().rstrip(".")
    for key in RACES:
        if key == lower or key.replace("-", " ") == lower:
            return key
    for key in RACES:
        if key.replace("-", " ") in lower or key in lower:
            return key
    aliases = {
        "elf": None, "high elf": "high-elf", "dark elf": "dark-elf",
        "wood elf": "wood-elf", "dragon": "dragonkin", "dragon kin": "dragonkin",
        "demon": "demonkin", "demon kin": "demonkin",
    }
    for alias, race_key in aliases.items():
        if alias in lower:
            return race_key
    return None


def parse_player_class(text: str, eligible: list[str]) -> str | None:
    """Try to match player input to an eligible class."""
    lower = text.lower().strip().rstrip(".")
    for cls in eligible:
        if cls in lower:
            return cls
    _aliases = {
        "thief": "urchin", "rogue": "urchin", "sneak": "urchin",
        "soldier": "militia", "fighter": "militia", "warrior": "militia",
        "mage": "apprentice", "wizard": "apprentice", "scholar": "apprentice",
        "priest": "novice", "cleric": "novice", "healer": "novice",
        "farmer": "peasant", "worker": "laborer", "smith": "laborer",
    }
    for alias, cls in _aliases.items():
        if alias in lower and cls in eligible:
            return cls
    return None


def parse_player_skills(text: str, class_key: str) -> list[str] | None:
    """Extract exactly 3 canonical skill slugs from player input."""
    if is_clarification(text):
        return None
    lower = text.lower()
    # Comma-separated explicit picks first
    if "," in lower:
        parts = [p.strip() for p in lower.split(",") if p.strip()]
        slugs = []
        for part in parts:
            slug = normalize_skill_slug(part)
            if slug and slug not in slugs:
                slugs.append(slug)
        if len(slugs) == 3:
            return slugs

    found: list[str] = []
    searchable = sorted(set(SKILL_PARSE_ALIASES.keys()) | set(ALL_SKILL_SLUGS), key=len, reverse=True)
    for token in searchable:
        slug = normalize_skill_slug(token)
        if not slug:
            continue
        pattern = token.replace("-", " ")
        if pattern in lower and slug not in found:
            found.append(slug)
    if len(found) == 3:
        return found
    return None


def format_skill_parse_error(text: str, class_key: str) -> str:
    """Build SKILLS-step error text for comma-separated input (APP-075)."""
    _ = class_key
    generic = "Name exactly 3 skills from the table, comma-separated."
    if is_clarification(text) or "," not in text.lower():
        return generic
    lower = text.lower()
    parts = [p.strip() for p in lower.split(",") if p.strip()]
    unknown = [part for part in parts if normalize_skill_slug(part) is None]
    if len(unknown) == 1:
        return f"Unrecognized skill: {unknown[0]}. {generic}"
    if len(unknown) > 1:
        return f"Unrecognized skills: {', '.join(unknown)}. {generic}"
    return generic


def _format_mods(mods: dict) -> str:
    if not mods:
        return "+1 to any two (player's choice)"
    parts = []
    for attr, val in mods.items():
        sign = "+" if val > 0 else ""
        parts.append(f"{sign}{val} {attr}")
    return ", ".join(parts)
