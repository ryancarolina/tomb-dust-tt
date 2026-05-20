"""Save snapshot tests: engine_status on _save_session (APP-016 T4a-d).

Never writes dev ``app/session_state.json`` — SAVE_PATH is monkeypatched per test.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from test_creation_flow import FIXED_ROLL, INPUTS


def read_save(save_path: Path) -> dict:
    return json.loads(save_path.read_text(encoding="utf-8"))


@pytest.fixture
def save_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "session_state.json"
    monkeypatch.setattr("ui.app.SAVE_PATH", path)
    return path


@pytest.fixture
def headless_app(app_config: dict, orchestrator, save_path: Path):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame
    from ui.app import App

    pygame.init()
    app = App(app_config)
    app._layout(800, 600)
    app._orchestrator = orchestrator
    yield app
    pygame.quit()


def _roll_attributes_patch(monkeypatch: pytest.MonkeyPatch, orchestrator) -> None:
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )


def test_save_includes_engine_status_mid_creation(
    headless_app, orchestrator, save_path, monkeypatch
):
    """T4a: mid-creation save includes engine_status with empty roster."""
    orchestrator.process_turn("new game")
    orchestrator.process_turn("Dumpy")

    headless_app._save_session()
    assert save_path.exists()

    data = read_save(save_path)
    assert "engine_status" in data
    es = data["engine_status"]
    status = orchestrator.get_status()
    assert es["awaiting"] == "CHARACTER_CREATION"
    assert es["roster"] == []
    assert es["awaiting"] == status["awaiting"]
    assert es["roster"] == status["roster"]


def test_save_includes_engine_status_after_finalize(
    headless_app, orchestrator, save_path, monkeypatch
):
    """T4b: post-finalize save includes engine_status with roster and delver awaiting."""
    _roll_attributes_patch(monkeypatch, orchestrator)
    for text, _expected in INPUTS:
        orchestrator.process_turn(text)

    headless_app._save_session()
    data = read_save(save_path)
    assert "engine_status" in data
    es = data["engine_status"]
    assert len(es["roster"]) >= 1
    assert es["awaiting"] != "CHARACTER_CREATION"


def test_load_session_legacy_without_engine_status(
    headless_app, orchestrator, save_path
):
    """T4c: legacy save without engine_status loads without error."""
    legacy = {
        "session_id": None,
        "campaign_slug": None,
        "narration_lines": [{"text": "Ledger line.", "voice": "narrator"}],
        "input_history": ["Dumpy"],
        "visited_cells": [],
        "current_address": None,
        "orchestrator_history": [],
        "creation_state": {
            "active": True,
            "step": "RACE",
            "name": "Dumpy",
            "race": None,
            "chosen_class": None,
            "chosen_skills": [],
            "chosen_schools": [],
            "chosen_spells": [],
            "starting_gold": None,
            "skills_table_shown": False,
            "schools_table_shown": False,
            "spells_table_shown": False,
            "races_table_shown": True,
            "classes_table_shown": False,
            "roll_result": None,
            "equipment_kit": None,
            "gold_roll": None,
        },
        "combat_state": None,
    }
    save_path.write_text(json.dumps(legacy, indent=2), encoding="utf-8")

    pre_active = orchestrator.creation.active
    headless_app._load_session()

    assert len(headless_app.narration.lines) == 1
    assert headless_app.narration.lines[0]["text"] == "Ledger line."
    assert orchestrator.creation.active == pre_active
    assert "engine_status" not in read_save(save_path)


def test_save_omits_engine_status_on_get_status_failure(
    headless_app, orchestrator, save_path, monkeypatch
):
    """T4d: get_status failure still writes save but omits engine_status key."""
    orchestrator.process_turn("new game")
    orchestrator.process_turn("Dumpy")

    def _raise() -> dict:
        raise RuntimeError("simulated")

    monkeypatch.setattr(orchestrator, "get_status", _raise)
    headless_app._save_session()

    assert save_path.exists()
    data = read_save(save_path)
    assert "engine_status" not in data
    assert data.get("creation_state") is not None
    assert data["creation_state"].get("active") is True
