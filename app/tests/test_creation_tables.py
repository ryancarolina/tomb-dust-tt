"""APP-072 / APP-059: code-owned creation tables + cell-length contract."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from gm.creation import (
    CLASS_INFO,
    RACES,
    assert_table_contract,
    format_classes_table,
    format_races_table,
    format_schools_table,
    format_skills_table,
    format_spells_table,
    strip_flavor_race_table,
    validate_table_cell_lengths,
)

BAD_FLAVOR = (
    "The clerk scratches the ledger and asks which bloodline you claim.\n\n"
    "| Race | Adjustments |\n"
    "|------|-------------|\n"
    "| Human | +1 STR, +1 INT | A common"
)


def _patch_llm_content(monkeypatch, content: str, *, finish_reason: str = "stop") -> None:
    class _StubCompletions:
        @staticmethod
        def create(**kwargs):
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content=content,
                            tool_calls=None,
                        ),
                        finish_reason=finish_reason,
                    )
                ]
            )

    stub_client = SimpleNamespace(
        chat=SimpleNamespace(completions=_StubCompletions())
    )

    monkeypatch.setattr(
        "gm.orchestrator.create_client",
        lambda *args, **kwargs: stub_client,
    )


def test_strip_flavor_race_table_unit():
    prose_before = "The clerk leans over the counter."
    prose_after = "Which lineage shall I record?"

    truncated = (
        f"{prose_before}\n\n"
        "| Race | Adjustments |\n"
        "| Human | +1 STR"
    )
    out_trunc = strip_flavor_race_table(truncated)
    assert prose_before in out_trunc
    assert "| Race |" not in out_trunc

    full_table = (
        f"{prose_before}\n\n"
        "| Race | Adjustments |\n"
        "|------|-------------|\n"
        "| Human | +1 STR, +1 INT | Common folk |\n"
        "| Elf | +1 AGI | Tall and keen |\n\n"
        f"{prose_after}"
    )
    out_full = strip_flavor_race_table(full_table)
    assert prose_before in out_full
    assert prose_after in out_full
    assert "| Race |" not in out_full

    prose_only = f"{prose_before}\n\n{prose_after}"
    assert strip_flavor_race_table(prose_only) == prose_only

    assert strip_flavor_race_table("") == ""
    assert strip_flavor_race_table("   \n  ") == ""


def test_race_narration_single_table_header(orchestrator, monkeypatch):
    _patch_llm_content(monkeypatch, BAD_FLAVOR, finish_reason="length")

    orchestrator.process_turn("new game")
    narration = orchestrator.process_turn("Dumpy")

    assert orchestrator.creation.step == "RACE"
    assert orchestrator.creation.races_table_shown is True
    assert "Pick **one race**" in narration
    assert narration.count("| Race | Adjustments |") == 1
    assert "Description |" not in narration
    assert "Awaiting: RACE_INPUT" in narration

    narration_reprompt = orchestrator.process_turn("not-a-race")
    assert narration_reprompt.count("| Race | Adjustments |") == 1


def test_format_races_table_two_columns():
    md = format_races_table()
    assert "| Race | Adjustments |" in md
    assert "Description |" not in md
    assert md.count("| ") >= len(RACES) + 2  # header + separator + rows
    data_rows = [ln for ln in md.splitlines() if ln.startswith("| ") and "Race" not in ln and ":-" not in ln]
    assert len(data_rows) == len(RACES)
    assert_table_contract("RACE", md)


def test_format_classes_table_three_columns():
    eligible = ["peasant", "urchin", "militia", "novice", "apprentice"]
    md = format_classes_table(eligible)
    assert "| Class | Requirement | Key skills |" in md
    assert "Starting GP" not in md
    assert md.count(" gp |") == 0
    assert_table_contract("CLASS", md)


def test_format_classes_table_key_skills_all_class_info():
    for class_key in CLASS_INFO:
        md = format_classes_table([class_key])
        assert_table_contract("CLASS", md)


def test_format_skills_table_contract():
    md = format_skills_table("apprentice")
    assert "| Skill |" in md
    assert_table_contract("SKILLS", md)


def test_format_schools_table_contract():
    md = format_schools_table("apprentice")
    assert "| Themes |" in md
    assert_table_contract("SPELL_SCHOOLS", md)


def test_format_spells_table_effect_cap():
    md = format_spells_table("apprentice", ["evocation", "enchantment"])
    assert "| Effect |" in md
    assert_table_contract("SPELLS", md)
    for line in md.splitlines():
        if not line.startswith("|") or "Effect" in line or ":-" in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 4:
            effect = cells[3]
            assert len(effect) <= 40
            if len(effect) == 40 and effect.endswith("…"):
                assert effect == effect[:37] + "…"


def test_validate_table_cell_lengths_violation():
    bad = (
        "| Race | Adjustments |\n"
        "|:------|:-------------|\n"
        "| OverlongRaceName | +1 STR |"
    )
    violations = validate_table_cell_lengths(bad, "RACE")
    assert any("RACE.Race:" in v and ">14" in v for v in violations)


def test_assert_table_contract_fails():
    bad = (
        "| Class | Requirement | Key skills |\n"
        "|:------|:-------------|:-----------|\n"
        "| Peasant | None | " + "x" * 41 + " |"
    )
    with pytest.raises(pytest.fail.Exception):
        assert_table_contract("CLASS", bad)


def test_truncate_cell_helper():
    from gm.creation import _truncate_cell

    assert _truncate_cell("short") == "short"
    assert _truncate_cell("x" * 40) == "x" * 40
    assert _truncate_cell("x" * 41) == "x" * 37 + "…"
    assert len(_truncate_cell("x" * 100, 40)) == 38
