"""APP-018: creation FSM restore from session_state.json (T-018a–f)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _patch_session_state_path(orchestrator, save_path: Path) -> None:
    orchestrator._session_state_path = lambda: save_path  # type: ignore[method-assign]


def seed_session_state(
    save_path: Path,
    *,
    step: str = "RACE",
    name: str = "Dumpy",
    active: bool = True,
    with_engine_status: bool = True,
    awaiting: str = "CHARACTER_CREATION",
    roster: list | None = None,
    extra_creation: dict | None = None,
) -> dict:
    """Write mid-creation session_state.json for restore tests."""
    creation_state: dict = {
        "active": active,
        "step": step,
        "name": name,
        "race": "",
        "roll_result": {},
        "chosen_skills": [],
        "chosen_class": "",
    }
    if extra_creation:
        creation_state.update(extra_creation)

    data: dict = {"creation_state": creation_state}
    if with_engine_status:
        data["engine_status"] = {
            "awaiting": awaiting,
            "roster": [] if roster is None else roster,
        }
    save_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


@pytest.fixture
def session_state_file(tmp_path: Path) -> Path:
    return tmp_path / "session_state.json"


def _mock_resume_fail(orchestrator, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        orchestrator.bridge,
        "session_resume",
        lambda: {"ok": False, "error": "no save session found"},
    )


def _mock_resume_ok(orchestrator, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        orchestrator.bridge,
        "session_resume",
        lambda: {"ok": True},
    )


def test_t018a_continue_fail_restores_race_from_disk(
    orchestrator, session_state_file, monkeypatch
):
    """T-018a: resume fail + disk seed → step RACE, variant B mentions race."""
    seed_session_state(session_state_file, step="RACE", name="Dumpy")
    _patch_session_state_path(orchestrator, session_state_file)
    _mock_resume_fail(orchestrator, monkeypatch)

    result = orchestrator.process_turn("continue")

    assert orchestrator.creation.step == "RACE"
    assert orchestrator.creation.active is True
    assert orchestrator.creation.name == "Dumpy"
    assert "race" in result.lower()
    assert "[Awaiting: RACE_INPUT]" in result


def test_t018b_relaunch_desk_input_restores_saved_awaiting(
    orchestrator, session_state_file, monkeypatch
):
    """T-018b: saved CHARACTER_CREATION + live SETUP → G3a restores RACE."""
    seed_session_state(session_state_file, step="RACE", name="Dumpy")
    _patch_session_state_path(orchestrator, session_state_file)
    monkeypatch.setattr(
        orchestrator.bridge,
        "status",
        lambda: {"awaiting": "SETUP", "roster": []},
    )

    orchestrator.process_turn("Dwarf")

    assert orchestrator.creation.active is True
    assert orchestrator.creation.step == "RACE"
    assert orchestrator.creation.name == "Dumpy"


def test_t018c_resume_success_preserves_race_not_name(
    orchestrator, session_state_file, monkeypatch
):
    """T-018c: resume ok + CHARACTER_CREATION → disk RACE, not NAME clobber."""
    seed_session_state(session_state_file, step="RACE", name="Dumpy")
    _patch_session_state_path(orchestrator, session_state_file)
    _mock_resume_ok(orchestrator, monkeypatch)
    monkeypatch.setattr(
        orchestrator.bridge,
        "status",
        lambda: {"awaiting": "CHARACTER_CREATION", "roster": []},
    )
    creation_turn_calls: list[str] = []
    monkeypatch.setattr(
        orchestrator,
        "_creation_turn",
        lambda inp: creation_turn_calls.append(inp) or "resume creation",
    )

    orchestrator.process_turn("load game")

    assert orchestrator.creation.step == "RACE"
    assert orchestrator.creation.active is True
    assert creation_turn_calls
    assert orchestrator.creation.step != "NAME" or orchestrator.creation.name == "Dumpy"


def test_t018d_legacy_save_live_awaiting_restores_skills(
    orchestrator, session_state_file, monkeypatch
):
    """T-018d: no engine_status on disk; live CHARACTER_CREATION → SKILLS."""
    seed_session_state(
        session_state_file,
        step="SKILLS",
        name="Flupps",
        with_engine_status=False,
        extra_creation={
            "race": "human",
            "chosen_skills": ["lore", "spellcasting", "arcana"],
            "chosen_class": "apprentice",
        },
    )
    _patch_session_state_path(orchestrator, session_state_file)
    _mock_resume_fail(orchestrator, monkeypatch)
    monkeypatch.setattr(
        orchestrator.bridge,
        "status",
        lambda: {"awaiting": "CHARACTER_CREATION", "roster": []},
    )

    orchestrator.process_turn("continue")

    assert orchestrator.creation.step == "SKILLS"
    assert orchestrator.creation.active is True
    assert orchestrator.creation.name == "Flupps"


@pytest.mark.parametrize(
    "awaiting,roster",
    [
        ("PLAYER_ACTIONS", []),
        ("CHARACTER_CREATION", [{"display_name": "Flupps", "character_id": "pc-1"}]),
    ],
)
def test_t018e_post_finalize_does_not_restore_stale_creation(
    orchestrator,
    session_state_file,
    monkeypatch,
    awaiting: str,
    roster: list,
):
    """T-018e: non–mid-creation gate → default inactive creation unchanged."""
    seed_session_state(
        session_state_file,
        step="SKILLS",
        name="Flupps",
        awaiting=awaiting,
        roster=roster,
        extra_creation={"race": "human", "chosen_class": "apprentice"},
    )
    _patch_session_state_path(orchestrator, session_state_file)
    _mock_resume_fail(orchestrator, monkeypatch)

    orchestrator.process_turn("continue")

    assert orchestrator.creation.active is False
    assert orchestrator.creation.step == "NAME"
    assert orchestrator.creation.name == ""


def test_t018f_new_game_wipe_blocks_skills_restore_on_continue(
    orchestrator, session_state_file, monkeypatch
):
    """T-018f: setup_new_game clears disk; continue does not restore old SKILLS."""
    seed_session_state(
        session_state_file,
        step="SKILLS",
        name="Flupps",
        extra_creation={
            "race": "human",
            "chosen_skills": ["lore", "spellcasting", "arcana"],
            "chosen_class": "apprentice",
        },
    )
    _patch_session_state_path(orchestrator, session_state_file)
    monkeypatch.setattr(orchestrator, "_delete_save_file", lambda: None)
    _mock_resume_fail(orchestrator, monkeypatch)

    assert orchestrator.setup_new_game().get("ok") is True

    data = json.loads(session_state_file.read_text(encoding="utf-8"))
    assert data["creation_state"]["step"] == "NAME"
    assert "engine_status" not in data

    result = orchestrator.process_turn("continue")

    assert orchestrator.creation.step == "NAME"
    assert orchestrator.creation.active is True
    assert "Flupps" not in result
    assert "skills" not in result.lower()
    assert "[Awaiting: NAME_INPUT]" in result
