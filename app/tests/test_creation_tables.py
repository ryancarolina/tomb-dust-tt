"""APP-072: race table strip + single code-owned table in RACE narration."""

from __future__ import annotations

from types import SimpleNamespace

from gm.creation import strip_flavor_race_table

BAD_FLAVOR = (
    "The clerk scratches the ledger and asks which bloodline you claim.\n\n"
    "| Race | Adjustments | Description |\n"
    "|------|-------------|-------------|\n"
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
        "| Race | Adjustments | Description |\n"
        "| Human | +1 STR"
    )
    out_trunc = strip_flavor_race_table(truncated)
    assert prose_before in out_trunc
    assert "| Race |" not in out_trunc

    full_table = (
        f"{prose_before}\n\n"
        "| Race | Adjustments | Description |\n"
        "|------|-------------|-------------|\n"
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
    assert "Awaiting: RACE_INPUT" in narration

    narration_reprompt = orchestrator.process_turn("not-a-race")
    assert narration_reprompt.count("| Race | Adjustments |") == 1
