"""APP-073: strip LLM status tags and stat tables from creation flavor."""

from __future__ import annotations

from types import SimpleNamespace

from gm.creation import (
    format_roll_stats_table,
    strip_flavor_stats_table,
    strip_llm_status_tags,
)
from test_creation_flow import FIXED_ROLL


def _patch_llm_content(
    monkeypatch,
    content: str,
    *,
    finish_reason: str = "stop",
    orchestrator=None,
) -> None:
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
    if orchestrator is not None:
        orchestrator.client = stub_client


def _flavor_region(narration: str, body_marker: str = "| Attr | Base |") -> str:
    idx = narration.find(body_marker)
    return narration[:idx] if idx >= 0 else narration.rsplit("Awaiting:", 1)[0]


def test_strip_llm_status_tags_inline_awaiting():
    inline = "The clerk nods. Awaiting: SKILL_INPUT"
    out_inline = strip_llm_status_tags(inline)
    assert "Awaiting:" not in out_inline
    assert "The clerk nods" in out_inline

    bracket = "[Location: 32-C | Phase: desk | Awaiting: SKILL_INPUT]"
    out_bracket = strip_llm_status_tags(bracket)
    assert "Location:" not in out_bracket
    assert "Phase:" not in out_bracket
    assert "Awaiting:" not in out_bracket

    whole_line = "Awaiting: MAGIC_SCHOOLS_INPUT\n\nProse."
    out_whole = strip_llm_status_tags(whole_line)
    assert "Awaiting:" not in out_whole
    assert "Prose." in out_whole

    prose_only = "Registry dust hangs in the air."
    assert strip_llm_status_tags(prose_only) == prose_only


def test_strip_flavor_stats_table_unit():
    prose_after = "The ink still smolders on the ledger."

    heading_block = (
        "### Your Attributes\n"
        "| Attr | Base | Genetic | Life Evt | Racial | Final |\n"
        "|:------|-----:|--------:|---------:|-------:|------:|\n"
        "| STR | 14 | 0 | 0 | 0 | 14 |\n\n"
        f"{prose_after}"
    )
    out_heading = strip_flavor_stats_table(heading_block)
    assert "### Your Attributes" not in out_heading
    assert "| Attr |" not in out_heading
    assert prose_after in out_heading

    prose_before = "The dice clatter across the counter."
    full_table = (
        f"{prose_before}\n\n"
        "| Attr | Base | Genetic | Life Evt | Racial | Final |\n"
        "|:------|-----:|--------:|---------:|-------:|------:|\n"
        "| STR | 14 | 0 | 0 | 0 | 14 |\n"
    )
    out_full = strip_flavor_stats_table(full_table)
    assert prose_before in out_full
    assert "| Attr | Base |" not in out_full

    compact = (
        "| STR | AGI | STA | INT | SPI | LUC |\n"
        "|-----|-----|-----|-----|-----|-----|\n"
        "| 14 | 12 | 10 | 11 | 9 | 10 |\n"
    )
    out_compact = strip_flavor_stats_table(compact)
    assert "| STR | AGI |" not in out_compact

    tool_fragment = "The dice clatter. `roll_attributes(race"
    out_tool = strip_flavor_stats_table(tool_fragment)
    assert "`roll_attributes(" not in out_tool

    prose_only = f"{prose_before}\n\n{prose_after}"
    assert strip_flavor_stats_table(prose_only) == prose_only

    assert strip_flavor_stats_table("") == ""
    assert strip_flavor_stats_table("   \n  ") == ""


def test_compose_flavor_sanitize_status_and_stats(orchestrator):
    bad_flavor = (
        "The clerk squints. Awaiting: SKILL_INPUT\n\n"
        "[Phase: creation]\n\n"
        "### Your Attributes\n"
        "| Attr | Base | Genetic | Life Evt | Racial | Final |\n"
        "|:------|-----:|--------:|---------:|-------:|------:|\n"
        "| STR | 14 | 0 | 0 | 0 | 14 |"
    )
    body = format_roll_stats_table(FIXED_ROLL)
    orchestrator.creation.step = "CLASS"

    narration = orchestrator._compose_creation_narration(bad_flavor, body)

    assert narration.count("| Attr | Base |") == 1
    assert narration.count("Awaiting:") == 1
    assert "Awaiting: CLASS_INPUT" in narration
    assert "SKILL_INPUT" not in _flavor_region(narration)
    assert "### Your Attributes" not in _flavor_region(narration)


BAD_STAT_FLAVOR = (
    "The clerk watches the bones settle.\n\n"
    "### Your Attributes\n"
    "| Attr | Base | Genetic | Life Evt | Racial | Final |\n"
    "|:------|-----:|--------:|---------:|-------:|------:|\n"
    "| STR | 14 | 0 | 0 | 0 | 14 |\n"
    "| AGI | 12 | 0 | 0 | 0 | 12 |"
)


def test_roll_stats_narration_single_stats_table(orchestrator, monkeypatch):
    _patch_llm_content(
        monkeypatch, BAD_STAT_FLAVOR, finish_reason="length", orchestrator=orchestrator
    )
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )

    orchestrator.process_turn("new game")
    narration = orchestrator.process_turn("Spluffy")
    narration = orchestrator.process_turn("undead")

    assert orchestrator.creation.step == "CLASS"
    assert narration.count("| Attr | Base |") == 1
    assert "Test narration." not in narration
    assert "Awaiting: CLASS_INPUT" in narration

    flavor = _flavor_region(narration)
    assert "| 14 |" not in flavor

    for attr, final in FIXED_ROLL["final_attributes"].items():
        assert str(final) in narration
