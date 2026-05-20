"""APP-015: creation block cleared on new game (T-015a–d)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


def _patch_session_state_path(orchestrator, save_path: Path) -> None:
    orchestrator._session_state_path = lambda: save_path  # type: ignore[method-assign]


def seed_stale_creation(
    save_path: Path,
    *,
    with_engine_status: bool = True,
) -> dict:
    """Write stale SKILLS block + optional mismatched engine_status."""
    data = {
        "creation_state": {
            "active": True,
            "step": "SKILLS",
            "name": "Flupps",
            "race": "human",
            "roll_result": {"ok": True, "race": "human", "final_attributes": {"STR": 10}},
            "chosen_skills": ["lore", "spellcasting", "arcana"],
            "chosen_class": "apprentice",
        },
        "narration_lines": ["Stale narration line"],
        "input_history": ["new game", "Flupps", "human"],
    }
    if with_engine_status:
        data["engine_status"] = {
            "awaiting": "IN_DELVE",
            "roster": [{"display_name": "Flupps", "character_id": "pc-1"}],
        }
    save_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


@pytest.fixture
def session_state_file(tmp_path: Path) -> Path:
    return tmp_path / "session_state.json"


def test_t015a_setup_new_game_clears_stale_creation_on_disk(
    orchestrator, session_state_file, monkeypatch
):
    """T-015a: success path — disk NAME-fresh; non-creation keys preserved."""
    seed = seed_stale_creation(session_state_file)
    _patch_session_state_path(orchestrator, session_state_file)
    orchestrator.import_creation_state(seed["creation_state"])

    monkeypatch.setattr(orchestrator, "_delete_save_file", lambda: None)

    result = orchestrator.setup_new_game()
    assert result.get("ok") is True

    assert session_state_file.exists()
    data = json.loads(session_state_file.read_text(encoding="utf-8"))
    cs = data["creation_state"]
    assert cs["step"] == "NAME"
    assert cs["name"] == ""
    assert cs["roll_result"] == {}
    assert data["narration_lines"] == seed["narration_lines"]
    assert data["input_history"] == seed["input_history"]
    assert orchestrator.creation.step == "NAME"
    assert orchestrator.creation.name == ""


def test_t015b_campaign_new_failure_still_clears_creation(
    orchestrator, session_state_file, monkeypatch
):
    """T-015b: early return — memory and disk stay NAME-fresh."""
    seed = seed_stale_creation(session_state_file)
    _patch_session_state_path(orchestrator, session_state_file)
    orchestrator.import_creation_state(seed["creation_state"])

    monkeypatch.setattr(
        orchestrator.bridge,
        "campaign_new",
        lambda slug, title: {"ok": False, "error": "simulated failure"},
    )

    result = orchestrator.setup_new_game()
    assert result.get("ok") is False
    assert "simulated failure" in result.get("error", "")

    data = json.loads(session_state_file.read_text(encoding="utf-8"))
    cs = data["creation_state"]
    assert cs["step"] == "NAME"
    assert cs["name"] == ""
    assert cs["roll_result"] == {}
    assert orchestrator.creation.step == "NAME"
    assert orchestrator.creation.name == ""


def test_t015c_load_game_after_new_game_uses_name_not_stale_disk(
    orchestrator, session_state_file, monkeypatch
):
    """T-015c: recovery copy reflects NAME memory, not pre-wipe SKILLS disk."""
    seed = seed_stale_creation(session_state_file)
    _patch_session_state_path(orchestrator, session_state_file)
    orchestrator.import_creation_state(seed["creation_state"])

    monkeypatch.setattr(orchestrator, "_delete_save_file", lambda: None)
    assert orchestrator.setup_new_game().get("ok") is True

    result = orchestrator.process_turn("load game")

    assert "skills" not in result.lower()
    assert "Flupps" not in result
    assert "[Awaiting: NAME_INPUT]" in result
    assert "unsaved" in result.lower() or "finished save" in result.lower()


def test_t015d_engine_status_cleared_on_new_game_success(
    orchestrator, session_state_file, monkeypatch
):
    """T-015d: surgical clear removes stale engine_status; preserves narration."""
    seed = seed_stale_creation(session_state_file, with_engine_status=True)
    _patch_session_state_path(orchestrator, session_state_file)
    orchestrator.import_creation_state(seed["creation_state"])

    monkeypatch.setattr(orchestrator, "_delete_save_file", lambda: None)
    assert orchestrator.setup_new_game().get("ok") is True

    data = json.loads(session_state_file.read_text(encoding="utf-8"))
    assert "engine_status" not in data
    assert data["creation_state"]["step"] == "NAME"
    assert data["narration_lines"] == seed["narration_lines"]


def test_t015d_engine_status_cleared_on_new_game_early_return(
    orchestrator, session_state_file, monkeypatch
):
    """T-015d: engine_status cleared even when campaign_new fails."""
    seed = seed_stale_creation(session_state_file, with_engine_status=True)
    _patch_session_state_path(orchestrator, session_state_file)
    orchestrator.import_creation_state(seed["creation_state"])

    monkeypatch.setattr(
        orchestrator.bridge,
        "campaign_new",
        lambda slug, title: {"ok": False, "error": "simulated failure"},
    )

    orchestrator.setup_new_game()

    data = json.loads(session_state_file.read_text(encoding="utf-8"))
    assert data.get("engine_status") is None or "engine_status" not in data
    assert data["creation_state"]["step"] == "NAME"
    assert data["narration_lines"] == seed["narration_lines"]
