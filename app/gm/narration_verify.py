"""Mechanical-truth verification for creation flavor (APP-083 Phase 1).

APP-059 EQUIPMENT_GOLD: flavor must not mention GP/gold/coin economics or kit
inventory — any mention fails verify (including amounts matching truth). Word-form
English numbers covered: one–twenty, thirty–ninety, hundred.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from gm.creation import (
    RACES,
    race_display_title,
    school_catalog,
    eligible_schools_for_class,
    tier1_spells_for_schools,
    starting_spell_profile,
    ensure_equipment_gold,
)

if TYPE_CHECKING:
    from gm.creation import CreationState

CREATION_CATALOG_DENYLIST = frozenset({
    "restoration", "transmutation", "divination", "evocation", "abjuration",
    "conjuration", "enchantment", "communion", "warding",
})

_MD_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|")
_ENUMERATION_RE = re.compile(
    r"(eight known schools|here are your options|listing the \d+ known)",
    re.IGNORECASE,
)
_GP_CLAIM_RE = re.compile(
    r"(\d+)\s*(?:gp|\bgold\b|gold\s+pieces?|gold\s+coins?|\bcoins?\b)",
    re.IGNORECASE,
)
# APP-059: any economics prose in EQUIPMENT_GOLD flavor (not only mismatch).
_EQUIPMENT_WORD_NUMBERS = (
    r"one|two|three|four|five|six|seven|eight|nine|ten|"
    r"eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
    r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred"
)
_EQUIPMENT_GP_DIGIT_RE = re.compile(
    r"\d+\s*(?:gp|\bgold\b|gold\s+pieces?|gold\s+coins?|\bcoins?\b)",
    re.IGNORECASE,
)
_EQUIPMENT_GP_WORD_RE = re.compile(
    rf"\b(?:{_EQUIPMENT_WORD_NUMBERS})\s+"
    r"(?:gp|\bgold\b|gold\s+pieces?|gold\s+coins?|\bcoins?\b)",
    re.IGNORECASE,
)
_EQUIPMENT_GP_PHRASE_RE = re.compile(
    r"\b(?:coin pouch|starting gold|gold pieces?|gold coins?)\b",
    re.IGNORECASE,
)
_EQUIPMENT_KIT_RE = re.compile(
    r"\b(?:Registry kit|bedroll|rations|waterskin|pouch)\b",
    re.IGNORECASE,
)
_AWAITING_RE = re.compile(r"\bAwaiting:\s*\S+", re.IGNORECASE)
_LOCATION_TAG_RE = re.compile(r"\[Location:", re.IGNORECASE)
_PHASE_TAG_RE = re.compile(r"\bPhase:\s*\S+", re.IGNORECASE)


@dataclass
class TurnTruth:
    mode: str = "creation"
    step: str = ""
    allowed_school_ids: set[str] = field(default_factory=set)
    allowed_school_names: set[str] = field(default_factory=set)
    allowed_spell_ids: set[str] = field(default_factory=set)
    allowed_spell_names: set[str] = field(default_factory=set)
    allowed_race_titles: set[str] = field(default_factory=set)
    committed_race: str | None = None
    starting_gold_gp: int | None = None
    kit_text: str = ""
    denylist_tokens: frozenset[str] = CREATION_CATALOG_DENYLIST
    code_block_hint: str = ""


@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    violations: tuple[str, ...] = ()


def build_creation_turn_truth(creation) -> TurnTruth:
    """Build authoritative facts for the current creation step."""
    step = creation.step or ""
    truth = TurnTruth(mode="creation", step=step)
    truth.allowed_race_titles = {name.replace("-", " ").title() for name in RACES}
    truth.allowed_race_titles.update(name for name in RACES)

    if creation.race:
        truth.committed_race = creation.race

    if step == "SPELL_SCHOOLS" and creation.chosen_class:
        schools = eligible_schools_for_class(creation.chosen_class)
        truth.allowed_school_ids = {s["id"] for s in schools}
        truth.allowed_school_names = {
            s["displayName"].lower() for s in schools
        } | truth.allowed_school_ids
        profile = starting_spell_profile(creation.chosen_class) or {}
        if creation.chosen_class == "novice":
            truth.code_block_hint = "Choose Divine plus 1 other school — code appends school table."
        else:
            n = profile.get("schoolPickCount", 2)
            truth.code_block_hint = f"Choose {n} arcane schools — code appends school table."

    elif step == "SPELLS" and creation.chosen_class:
        school_ids = list(creation.chosen_schools or [])
        spells = tier1_spells_for_schools(school_ids)
        truth.allowed_spell_ids = {s["id"] for s in spells}
        truth.allowed_spell_names = {
            s["displayName"].lower() for s in spells
        } | truth.allowed_spell_ids
        truth.allowed_school_ids = set(school_ids)
        truth.code_block_hint = "Pick tier-1 spells — code appends spell table."

    elif step == "EQUIPMENT_GOLD" and creation.chosen_class:
        ensure_equipment_gold(creation)
        truth.starting_gold_gp = int(creation.starting_gold)
        truth.kit_text = str(creation.equipment_kit or "")
        truth.code_block_hint = "Kit and starting gold — code appends Registry summary."

    elif step in ("RACE",):
        truth.code_block_hint = "Race pick table appended by code — do not list races."

    elif step in ("CLASS", "ROLL_STATS"):
        truth.code_block_hint = "Class/stats tables appended by code."

    elif step == "SKILLS":
        truth.code_block_hint = "Skills table appended by code."

    elif step in ("FINALIZE", "WORLD_INTRO"):
        truth.code_block_hint = "Registration summary appended by code."

    return truth


def format_turn_truth_for_prompt(truth: TurnTruth, *, creation: "CreationState") -> str:
    lines = [
        "## Authoritative facts (do not contradict)",
        f"Step: {truth.step}",
    ]
    if creation.name:
        lines.append(f"Character name: {creation.name}")
    if creation.race:
        lines.append(f"Committed race: {race_display_title(creation.race)}")
    if creation.chosen_class:
        lines.append(f"Committed class: {creation.chosen_class}")
    if creation.chosen_skills:
        lines.append(f"Committed skills: {', '.join(creation.chosen_skills)}")
    if truth.allowed_school_names:
        schools = sorted(truth.allowed_school_names)
        lines.append(f"Allowed schools only: {', '.join(schools)}")
    if truth.allowed_spell_names:
        spells = sorted(truth.allowed_spell_names)
        lines.append(f"Allowed tier-1 spells only: {', '.join(spells)}")
    if truth.starting_gold_gp is not None:
        lines.append(f"Starting gold: {truth.starting_gold_gp} gp")
    if truth.kit_text:
        lines.append(f"Registry kit: {truth.kit_text}")
    if truth.code_block_hint:
        lines.append(truth.code_block_hint)
    lines.append(
        "Write 1–2 sentences of clerk banter only. "
        "Do not list picks, stats, kit items, gold amounts, schools, spells, or markdown tables — code appends those."
    )
    return "\n".join(lines)


def _contains_markdown_table(text: str) -> bool:
    rows = [ln for ln in (text or "").splitlines() if _MD_TABLE_ROW_RE.match(ln)]
    return len(rows) >= 2


def _find_denylist_tokens(text: str, denylist: frozenset[str]) -> list[str]:
    lower = (text or "").lower()
    hits: list[str] = []
    for token in denylist:
        if re.search(rf"\b{re.escape(token)}\b", lower):
            hits.append(token)
    return hits


def _find_off_catalog_schools(text: str, allowed: set[str]) -> list[str]:
    if not allowed:
        return []
    hits: list[str] = []
    for school in school_catalog():
        sid = school["id"]
        display = school["displayName"].lower()
        if sid in allowed or display in allowed:
            continue
        if re.search(rf"\b{re.escape(display)}\b", text, re.IGNORECASE):
            hits.append(display)
        elif re.search(rf"\b{re.escape(sid)}\b", text, re.IGNORECASE):
            hits.append(sid)
    return hits


def verify_narration(prose: str, truth: TurnTruth) -> VerificationResult:
    """Return pass/fail for creation flavor prose against TurnTruth."""
    text = (prose or "").strip()
    if not text:
        return VerificationResult(passed=True)

    violations: list[str] = []

    if _contains_markdown_table(text):
        violations.append("markdown_table")
    if _AWAITING_RE.search(text):
        violations.append("awaiting_tag")
    if _LOCATION_TAG_RE.search(text):
        violations.append("location_tag")
    if _PHASE_TAG_RE.search(text):
        violations.append("phase_tag")
    if _ENUMERATION_RE.search(text):
        violations.append("pick_enumeration")

    violations.extend(f"denylist:{t}" for t in _find_denylist_tokens(text, truth.denylist_tokens))

    if truth.step == "SPELL_SCHOOLS":
        violations.extend(
            f"off_catalog_school:{s}"
            for s in _find_off_catalog_schools(text, truth.allowed_school_names | truth.allowed_school_ids)
        )

    if truth.step == "SPELLS" and truth.allowed_spell_ids:
        for spell in tier1_spells_for_schools(list(truth.allowed_school_ids)):
            sid = spell["id"]
            display = spell["displayName"].lower()
            if sid in truth.allowed_spell_ids:
                continue
            if re.search(rf"\b{re.escape(display)}\b", text, re.IGNORECASE):
                violations.append(f"off_catalog_spell:{display}")

    if truth.step == "EQUIPMENT_GOLD" and truth.starting_gold_gp is not None:
        if (
            _EQUIPMENT_GP_DIGIT_RE.search(text)
            or _EQUIPMENT_GP_WORD_RE.search(text)
            or _EQUIPMENT_GP_PHRASE_RE.search(text)
        ):
            violations.append("equipment_gp_mention")
        if _EQUIPMENT_KIT_RE.search(text):
            violations.append("equipment_kit_mention")
        for m in _GP_CLAIM_RE.finditer(text):
            claimed = int(m.group(1))
            if claimed != truth.starting_gold_gp:
                violations.append(f"gold_mismatch:{claimed}vs{truth.starting_gold_gp}")

    if truth.committed_race:
        committed_title = race_display_title(truth.committed_race)
        for key in RACES:
            if key == truth.committed_race:
                continue
            title = race_display_title(key)
            if re.search(rf"\b{re.escape(title)}\b", text, re.IGNORECASE):
                violations.append(f"wrong_race:{title}")
                break

    return VerificationResult(passed=not violations, violations=tuple(violations))
