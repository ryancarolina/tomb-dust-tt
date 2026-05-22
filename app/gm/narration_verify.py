"""Mechanical-truth verification for creation flavor (APP-083 Phase 1).

APP-059 EQUIPMENT_GOLD: flavor must not mention GP/gold/coin economics or kit
inventory — any mention fails verify (including amounts matching truth). Word-form
English numbers covered: one–twenty, thirty–ninety, hundred.

APP-089: encounter TurnTruth builder + verify rules for pre-combat exploration prose.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

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

# APP-089 encounter verify patterns
_PREMATURE_COMBAT_RE = re.compile(
    r"\b(?:combat\s+begins|roll(?:s)?\s+for\s+initiative|initiative\s+order|"
    r"fight\s+starts|battle\s+begins|the\s+fight\s+is\s+on)\b",
    re.IGNORECASE,
)
_CONTEST_OUTCOME_RE = re.compile(
    r"\b(?:you\s+(?:sneak|snuck|slip(?:ped)?)\s+past(?:\s+unnoticed)?|"
    r"sneak(?:ed|s)?\s+past\s+unnoticed|"
    r"successfully\s+(?:hide|sneak|slip|move\s+quietly)|"
    r"stealth\s+(?:succeeds|passes|fails)|"
    r"fail(?:ed|s|ure)?\s+(?:the\s+)?(?:stealth|perception|listen)\s+(?:check|roll)?|"
    r"perception\s+(?:succeeds|passes|fails)|"
    r"you\s+go\s+unnoticed|remain(?:s|ed)?\s+undetected)\b",
    re.IGNORECASE,
)
_SURPRISE_WITHOUT_AMBUSH_RE = re.compile(
    r"\b(?:you\s+(?:are|were)\s+surprised|surprised\s+by\s+the\s+attack|"
    r"flat[- ]footed|caught\s+off\s+guard|taken\s+unawares)\b",
    re.IGNORECASE,
)
_SPATIAL_ENTRY_RES = (
    re.compile(r"step\s+(?:into|inside|through)", re.IGNORECASE),
    re.compile(r"cross(?:es|ed)?\s+the\s+threshold", re.IGNORECASE),
    re.compile(r"beyond\s+the\s+(?:arch|door|gate)", re.IGNORECASE),
    re.compile(r"torchlit", re.IGNORECASE),
    re.compile(r"corridor", re.IGNORECASE),
    re.compile(r"vault\s+interior", re.IGNORECASE),
    re.compile(r"catacomb", re.IGNORECASE),
    re.compile(r"undercrypt", re.IGNORECASE),
    re.compile(r"dungeon\s+(?:floor|hall)", re.IGNORECASE),
    re.compile(
        r"you\s+(?:are|enter|stand)\s+(?:now\s+)?(?:in|inside)\s+(?:the\s+)?(?:crypt|dungeon|site|undercrypt|vault)",
        re.IGNORECASE,
    ),
    re.compile(r"\[Phase:\s*delve", re.IGNORECASE),
    re.compile(r"\[Location:[^\]]*(?:UG-|undercrypt|crypt|dungeon)", re.IGNORECASE),
    re.compile(r"Phase:\s*delve", re.IGNORECASE),
    re.compile(r"mode:\s*dungeon", re.IGNORECASE),
)
_MONSTER_ID_IN_PROSE_RE = re.compile(
    r"\b([a-z]+(?:-[a-z]+)+)\b",
    re.IGNORECASE,
)


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
    # APP-089 encounter fields
    encounter_phase: str = ""
    threats: list[dict[str, Any]] = field(default_factory=list)
    tools_ok_this_turn: list[str] = field(default_factory=list)
    combat_active: bool = False
    entry_committed: bool = False
    last_roll: dict[str, Any] | None = None
    last_contest: dict[str, Any] | None = None


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


def _parse_feature_data_json(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}
    return {}


def _threats_from_status(status: dict[str, Any]) -> list[dict[str, Any]]:
    threats: list[dict[str, Any]] = []
    dungeon = status.get("dungeon") or {}
    features = dungeon.get("features") or status.get("features") or []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        if str(feature.get("feature_type") or "").lower() != "enemy":
            continue
        data = _parse_feature_data_json(feature.get("data_json"))
        monster_id = str(data.get("monsterId") or data.get("monster_id") or "").strip()
        if not monster_id:
            continue
        threats.append({
            "monster_id": monster_id,
            "count": int(data.get("count") or 1),
            "feature_id": feature.get("id"),
        })
    return threats


def build_encounter_turn_truth(
    status: dict[str, Any],
    encounter_state: dict[str, Any] | None,
    tool_results: list[str],
    gate_flags: dict[str, Any] | None = None,
) -> TurnTruth:
    """Build authoritative facts for pre-combat encounter narration (APP-089)."""
    blob = encounter_state or {}
    phase = str(blob.get("phase") or "").strip()
    threats = list(blob.get("threats") or [])
    if not threats:
        threats = _threats_from_status(status)

    flags = gate_flags or {}
    last_contest = blob.get("last_contest")
    last_roll = blob.get("last_roll")
    if last_roll is None and isinstance(last_contest, dict):
        last_roll = last_contest.get("roll_ref")

    return TurnTruth(
        mode="exploration",
        step=f"encounter_{phase}" if phase else "encounter",
        encounter_phase=phase,
        threats=threats,
        tools_ok_this_turn=list(tool_results or []),
        combat_active=bool(status.get("combat")),
        entry_committed=bool(flags.get("entry_committed")),
        last_roll=last_roll if isinstance(last_roll, dict) else None,
        last_contest=last_contest if isinstance(last_contest, dict) else None,
        code_block_hint=(
            "Encounter phase active — describe threat and choices; "
            "code appends exploration status footer."
        ),
    )


def _format_encounter_turn_truth_for_prompt(truth: TurnTruth) -> str:
    lines = [
        "## Authoritative facts (do not contradict)",
        f"Encounter phase: {truth.encounter_phase or 'unknown'}",
    ]
    if truth.threats:
        threat_bits = []
        for threat in truth.threats:
            mid = threat.get("monster_id") or "unknown"
            count = threat.get("count", 1)
            threat_bits.append(f"{mid} x{count}")
        lines.append(f"Threats present: {', '.join(threat_bits)}")
    else:
        lines.append("Threats present: none recorded")
    if truth.tools_ok_this_turn:
        lines.append(f"Tools ok this turn: {', '.join(truth.tools_ok_this_turn)}")
    lines.append(f"Combat active: {'yes' if truth.combat_active else 'no'}")
    lines.append(f"Entry committed this turn: {'yes' if truth.entry_committed else 'no'}")
    if truth.last_contest:
        contest_type = truth.last_contest.get("contest_type") or "unknown"
        success = truth.last_contest.get("success")
        lines.append(f"Last contest: {contest_type} success={success}")
    elif truth.last_roll:
        skill = truth.last_roll.get("skill") or truth.last_roll.get("reason") or "roll"
        lines.append(f"Last roll: {skill}")
    lines.append(
        "Do not describe combat started unless start_combat ok this turn "
        "and combat_active is true."
    )
    if truth.code_block_hint:
        lines.append(truth.code_block_hint)
    lines.append(
        "Write 1–3 sentences of encounter narration only. "
        "Offer detect, sneak, withdraw, or hostile engage — do not start combat in prose."
    )
    return "\n".join(lines)


def format_turn_truth_for_prompt(truth: TurnTruth, *, creation: "CreationState | None" = None) -> str:
    if truth.mode == "exploration" or truth.encounter_phase:
        return _format_encounter_turn_truth_for_prompt(truth)

    lines = [
        "## Authoritative facts (do not contradict)",
        f"Step: {truth.step}",
    ]
    if creation and creation.name:
        lines.append(f"Character name: {creation.name}")
    if creation and creation.race:
        lines.append(f"Committed race: {race_display_title(creation.race)}")
    if creation and creation.chosen_class:
        lines.append(f"Committed class: {creation.chosen_class}")
    if creation and creation.chosen_skills:
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


def _content_root() -> Path:
    return Path(__file__).resolve().parents[2] / "build"


def _monster_catalog_index() -> dict[str, str]:
    """Map monster id and display name (lower) -> canonical id."""
    index: dict[str, str] = {}
    monsters_dir = _content_root() / "data" / "monsters"
    if not monsters_dir.is_dir():
        return index
    for path in monsters_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(data, dict):
            continue
        mid = str(data.get("id") or path.stem).strip()
        if not mid:
            continue
        index[mid.lower()] = mid
        display = str(data.get("displayName") or "").strip()
        if display:
            index[display.lower()] = mid
    return index


def _allowed_threat_monster_ids(threats: list[dict[str, Any]]) -> set[str]:
    allowed: set[str] = set()
    for threat in threats:
        mid = str(threat.get("monster_id") or "").strip()
        if mid:
            allowed.add(mid.lower())
    return allowed


def _monster_display_tokens(monster_id: str, catalog: dict[str, str]) -> set[str]:
    tokens = {monster_id.lower(), monster_id.replace("-", " ").lower()}
    for name, mid in catalog.items():
        if mid.lower() == monster_id.lower():
            tokens.add(name.lower())
    parts = monster_id.split("-")
    if len(parts) > 1:
        tokens.add(parts[-1].lower())
    return tokens


def _find_wrong_monsters(text: str, truth: TurnTruth) -> list[str]:
    catalog = _monster_catalog_index()
    if not catalog:
        return []

    allowed_ids = _allowed_threat_monster_ids(truth.threats)
    allowed_tokens: set[str] = set()
    for mid in allowed_ids:
        allowed_tokens.update(_monster_display_tokens(mid, catalog))

    lower = text.lower()
    violations: list[str] = []

    for token, mid in catalog.items():
        if " " not in token and "-" not in token and len(token) < 5:
            continue
        if mid.lower() in allowed_ids:
            continue
        if re.search(rf"\b{re.escape(token)}\b", lower):
            violations.append(mid)
            continue

    for match in _MONSTER_ID_IN_PROSE_RE.finditer(text):
        slug = match.group(1).lower()
        if slug in catalog and slug not in allowed_ids:
            violations.append(catalog[slug])

    return sorted(set(violations))


def _has_contest_roll_evidence(truth: TurnTruth) -> bool:
    if "roll_d20" in truth.tools_ok_this_turn:
        return True
    if "process_beat" in truth.tools_ok_this_turn and truth.last_contest:
        return True
    return bool(truth.last_roll or truth.last_contest)


def _spatial_entry_violation(text: str) -> bool:
    return any(pattern.search(text) for pattern in _SPATIAL_ENTRY_RES)


def _verify_encounter_narration(text: str, truth: TurnTruth) -> list[str]:
    violations: list[str] = []

    combat_started_ok = truth.combat_active or "start_combat" in truth.tools_ok_this_turn
    if not combat_started_ok and _PREMATURE_COMBAT_RE.search(text):
        violations.append("premature_combat_start")

    if _CONTEST_OUTCOME_RE.search(text) and not _has_contest_roll_evidence(truth):
        violations.append("outcome_without_roll")

    if not truth.entry_committed and _spatial_entry_violation(text):
        violations.append("spatial_entry")

    violations.extend(f"wrong_monster:{mid}" for mid in _find_wrong_monsters(text, truth))

    ambush_ok = (
        truth.encounter_phase == "ambush"
        and (truth.last_contest or "roll_d20" in truth.tools_ok_this_turn)
    )
    if _SURPRISE_WITHOUT_AMBUSH_RE.search(text) and not ambush_ok:
        violations.append("surprise_without_ambush")

    return violations


def verify_narration(prose: str, truth: TurnTruth) -> VerificationResult:
    """Return pass/fail for flavor prose against TurnTruth."""
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

    if truth.mode == "exploration" or truth.encounter_phase:
        violations.extend(_verify_encounter_narration(text, truth))
        return VerificationResult(passed=not violations, violations=tuple(violations))

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
