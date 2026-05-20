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

SKILL_CATEGORIES: dict[str, list[str]] = {
    "Combat": ["swordsmanship", "archery", "shield-use", "unarmed-combat", "crossbow"],
    "Physical": ["athletics", "acrobatics", "climbing", "swimming", "endurance"],
    "Subterfuge": ["stealth", "sleight-of-hand", "lockpicking", "disguise"],
    "Mental": ["lore", "investigation", "perception", "nature", "engineering"],
    "Magic": ["spellcasting", "arcana", "magical-knowledge", "mana-control"],
    "Social": ["persuasion", "deception", "etiquette", "intimidation"],
    "Other": ["medicine", "battlefield-awareness"],
}

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
    gold_roll: int = 0

    def advance(self):
        idx = CREATION_STEPS.index(self.step)
        if idx < len(CREATION_STEPS) - 1:
            self.step = CREATION_STEPS[idx + 1]
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


def get_step_prompt(state: CreationState) -> str:
    """Return the LLM instruction for the current creation step."""

    if state.step == "NAME":
        return (
            "CHARACTER CREATION STEP 1: ASK NAME.\n"
            "Narrate the player arriving at the Registry desk in Breley Keep. "
            "A clerk asks them for their name. Keep it to 2-3 sentences of scene-setting, "
            "then ask: \"What name shall I put down?\"\n"
            "You MUST call set_creation_choice(step='NAME', value='<the name>') with whatever name the player gives. "
            "Do NOT ask about race yet."
        )

    if state.step == "RACE":
        race_table = "| Race | Adjustments | Description |\n|------|-------------|-------------|\n"
        race_table += "\n".join(
            f"| {name.replace('-', ' ').title()} | {_format_mods(info['mods'])} | {info['description']} |"
            for name, info in RACES.items()
        )
        return (
            f"CHARACTER CREATION STEP 2: CHOOSE RACE.\n"
            f"The clerk nods and writes down '{state.name}'. Now they ask about lineage.\n"
            f"Present this EXACT markdown table of all 16 races (the clerk reads from a Registry form):\n\n"
            f"{race_table}\n\n"
            f"Write 1-2 sentences of in-character narration, then output the table above EXACTLY.\n"
            f"Ask the player to pick one.\n"
            f"You MUST call set_creation_choice(step='RACE', value='<race_id>') with the player's choice. "
            f"Valid race_ids: human, high-elf, dark-elf, wood-elf, dwarf, halfling, centaur, aquarid, demonkin, orc, gnome, dragonkin, faerie, minotaur, undead, troll."
        )

    if state.step == "ROLL_STATS":
        return ""

    if state.step == "CLASS":
        attrs = state.roll_result.get("final_attributes", {})
        eligible = state.roll_result.get("eligible_classes", ["peasant"])
        class_details = "\n".join(
            f"  - **{cls.title()}** ({CLASS_INFO[cls]['requirement']}): "
            f"{CLASS_INFO[cls]['description']} Key skills: {', '.join(CLASS_INFO[cls]['key_skills'])}. "
            f"Kit: {CLASS_INFO[cls]['kit']}."
            for cls in eligible
            if cls in CLASS_INFO
        )
        return (
            f"CHARACTER CREATION STEP 4: CHOOSE CLASS.\n"
            f"Final stats: STR {attrs.get('STR', '?')}, AGI {attrs.get('AGI', '?')}, "
            f"STA {attrs.get('STA', '?')}, INT {attrs.get('INT', '?')}, "
            f"SPI {attrs.get('SPI', '?')}, LUC {attrs.get('LUC', '?')}\n\n"
            f"Eligible Tier-1 classes:\n{class_details}\n\n"
            f"Present these in character (the clerk explains what each path means at the Registry). "
            f"Ask the player to choose one.\n"
            f"You MUST call set_creation_choice(step='CLASS', value='<class_id>') with the player's choice. "
            f"Valid class_ids: {', '.join(eligible)}."
        )

    if state.step == "SKILLS":
        return (
            "CHARACTER CREATION STEP 5: SKILLS — handled by code. "
            "The skills table is injected separately. Do NOT call tools."
        )

    if state.step == "SPELL_SCHOOLS":
        return (
            "CHARACTER CREATION STEP 6: SPELL SCHOOLS — handled by code. "
            "The schools table is injected separately. Do NOT call tools."
        )

    if state.step == "SPELLS":
        return (
            "CHARACTER CREATION STEP 7: STARTING SPELLS — handled by code. "
            "The spells table is injected separately. Do NOT call tools."
        )

    if state.step == "EQUIPMENT_GOLD":
        ensure_equipment_gold(state)
        return (
            f"CHARACTER CREATION STEP 8: EQUIPMENT & GOLD.\n"
            f"Class kit: {state.equipment_kit}\n"
            f"Starting gold: **{state.starting_gold} gp** (1d6 roll already applied).\n\n"
            f"Narrate the clerk handing {state.name} their kit and coin pouch. "
            f"Ask if they accept and are ready to begin.\n"
            f"Only call set_creation_choice(step='EQUIPMENT_GOLD', value='confirmed') when the player "
            f"explicitly confirms (yes/ready/confirm)."
        )

    if state.step == "FINALIZE":
        return ""

    if state.step == "WORLD_INTRO":
        return ""

    return ""


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


def _format_mods(mods: dict) -> str:
    if not mods:
        return "+1 to any two (player's choice)"
    parts = []
    for attr, val in mods.items():
        sign = "+" if val > 0 else ""
        parts.append(f"{sign}{val} {attr}")
    return ", ".join(parts)
