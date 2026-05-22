"""Tests for mechanical-truth narration verification (APP-083)."""

from __future__ import annotations

from gm.creation import CreationState, ensure_equipment_gold
from gm.narration_verify import (
    TurnTruth,
    build_creation_turn_truth,
    format_turn_truth_for_prompt,
    verify_narration,
)
from gm.orchestrator import handle_finish_reason_length


SUMPTY_SCHOOLS_DRIFT = (
    "The clerk slides a fresh form across the counter. "
    "Restoration, Evocation, Abjuration, and the other schools are all on record — "
    "pick two that suit your calling."
)

SUMPTY_SPELLS_DRIFT = (
    "| School | Spells |\n"
    "|:-------|:-------|\n"
    "| Restoration | Mend Light, Consecrate Ground |\n"
    "| Communion | Aegis Spark |"
)

SUMPTY_EQUIPMENT_DRIFT = (
    "The clerk counts out 50 gold and a bedroll kit into your hands."
)

VALID_BANTER = "The clerk taps the ledger and waits for your answer."


def _novice_creation(*, step: str = "SPELL_SCHOOLS") -> CreationState:
    state = CreationState(active=True, step=step)
    state.name = "Sumpty"
    state.race = "undead"
    state.chosen_class = "novice"
    state.chosen_skills = ["spellcasting", "medicine", "lore"]
    state.chosen_schools = ["divine", "ward"]
    return state


def test_verify_rejects_sumpty_school_drift():
    creation = _novice_creation(step="SPELL_SCHOOLS")
    truth = build_creation_turn_truth(creation)
    result = verify_narration(SUMPTY_SCHOOLS_DRIFT, truth)
    assert not result.passed
    assert any("restoration" in v or "denylist" in v for v in result.violations)


def test_verify_rejects_sumpty_spells_table():
    creation = _novice_creation(step="SPELLS")
    truth = build_creation_turn_truth(creation)
    result = verify_narration(SUMPTY_SPELLS_DRIFT, truth)
    assert not result.passed
    assert "markdown_table" in result.violations


def test_verify_rejects_wrong_gold_on_equipment_step():
    creation = _novice_creation(step="EQUIPMENT_GOLD")
    creation.gold_roll = 1
    ensure_equipment_gold(creation)
    assert creation.starting_gold != 50
    truth = build_creation_turn_truth(creation)
    result = verify_narration(SUMPTY_EQUIPMENT_DRIFT, truth)
    assert not result.passed
    assert any(v.startswith("gold_mismatch") for v in result.violations)


def test_verify_equipment_word_form_gold_fails():
    creation = _novice_creation(step="EQUIPMENT_GOLD")
    ensure_equipment_gold(creation)
    truth = build_creation_turn_truth(creation)
    prose = "The clerk slides fifty gold pieces across the counter."
    result = verify_narration(prose, truth)
    assert not result.passed
    assert "equipment_gp_mention" in result.violations


def test_verify_equipment_matching_gp_fails():
    creation = _novice_creation(step="EQUIPMENT_GOLD")
    ensure_equipment_gold(creation)
    truth = build_creation_turn_truth(creation)
    assert truth.starting_gold_gp is not None
    prose = f"The clerk notes {truth.starting_gold_gp} gp on the form."
    result = verify_narration(prose, truth)
    assert not result.passed
    assert "equipment_gp_mention" in result.violations
    assert not any(v.startswith("gold_mismatch") for v in result.violations)


def test_verify_equipment_kit_mention_fails():
    creation = _novice_creation(step="EQUIPMENT_GOLD")
    ensure_equipment_gold(creation)
    truth = build_creation_turn_truth(creation)
    prose = "Registry kit with bedroll and rations awaits on the counter."
    result = verify_narration(prose, truth)
    assert not result.passed
    assert "equipment_kit_mention" in result.violations


def test_verify_accepts_clean_banter():
    creation = _novice_creation(step="SPELL_SCHOOLS")
    truth = build_creation_turn_truth(creation)
    result = verify_narration(VALID_BANTER, truth)
    assert result.passed


def test_format_turn_truth_includes_allowed_schools():
    creation = _novice_creation(step="SPELL_SCHOOLS")
    truth = build_creation_turn_truth(creation)
    block = format_turn_truth_for_prompt(truth, creation=creation)
    assert "Allowed schools only" in block
    assert "divine" in block.lower() or "pyromancy" in block.lower()


def test_handle_finish_reason_length_discards_when_body_pending():
    recovery = handle_finish_reason_length(
        "length",
        "partial prose",
        body_pending=True,
        flavor_only=False,
        length_retries_left=1,
    )
    assert recovery.action == "discard"
    assert recovery.next_prose == ""


def test_handle_finish_reason_length_retries_name_flavor():
    recovery = handle_finish_reason_length(
        "length",
        "partial",
        body_pending=False,
        flavor_only=True,
        length_retries_left=1,
    )
    assert recovery.action == "retry"


def test_handle_finish_reason_length_fallback_when_exhausted():
    recovery = handle_finish_reason_length(
        "length",
        "partial",
        body_pending=False,
        flavor_only=True,
        length_retries_left=0,
    )
    assert recovery.action == "fallback"
