"""APP-017: reconcile empty roster on load (T-017a–f, T-017c2).

Never writes dev ``app/session_state.json`` — patch ``_session_state_path`` per test.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from test_creation_flow import FIXED_ROLL, INPUTS

from test_engine_status_on_save import headless_app, read_save, save_path  # noqa: F401


def _patch_session_state_path(orchestrator, save_path: Path) -> None:
    orchestrator._session_state_path = lambda: save_path  # type: ignore[method-assign]


def _write_session_state(save_path: Path, **overrides) -> dict:
    data = {
        "session_id": None,
        "campaign_slug": None,
        "narration_lines": [],
        "input_history": [],
        "visited_cells": [],
        "current_address": None,
        "orchestrator_history": [],
        "creation_state": None,
        "combat_state": None,
        "engine_status": None,
    }
    data.update(overrides)
    save_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def _patch_live_status(
    monkeypatch: pytest.MonkeyPatch,
    orchestrator,
    *,
    awaiting: str,
    roster: list,
    characters: list | None = None,
) -> None:
    try:
        base = orchestrator.bridge.status()
    except Exception:
        base = {}

    def _status() -> dict:
        out = dict(base)
        out["awaiting"] = awaiting
        out["roster"] = roster
        if characters is not None:
            out["characters"] = characters
        return out

    monkeypatch.setattr(orchestrator.bridge, "status", _status)


def _roll_attributes_patch(monkeypatch: pytest.MonkeyPatch, orchestrator) -> None:
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )


def test_t017a_force_active_when_inactive_and_disk_mid_creation(
    headless_app, orchestrator, save_path, monkeypatch
):
    """T-017a: inactive memory + disk mid-creation → force active on sync."""
    orchestrator.process_turn("new game")
    orchestrator.process_turn("Dumpy")
    headless_app._save_session()
    assert save_path.exists()
    assert read_save(save_path).get("engine_status") is not None

    _patch_session_state_path(orchestrator, save_path)
    orchestrator.creation.active = False

    orchestrator._sync_creation_from_status()

    assert orchestrator.creation.active is True


def test_t017b_force_active_from_disk_when_live_setup(
    orchestrator, save_path, monkeypatch
):
    """T-017b: live SETUP + saved CHARACTER_CREATION → force active; step not clobbered."""
    live = orchestrator.bridge.status()
    assert (live.get("awaiting") or "") in ("", "SETUP")

    _write_session_state(
        save_path,
        creation_state=None,
        engine_status={"awaiting": "CHARACTER_CREATION", "roster": []},
    )
    _patch_session_state_path(orchestrator, save_path)
    orchestrator.import_creation_state(None)
    pre_step = orchestrator.creation.step

    orchestrator._sync_creation_from_status()

    assert orchestrator.creation.active is True
    assert orchestrator.creation.step == pre_step


def test_t017c_post_finalize_non_empty_roster_no_reactivate(
    headless_app, orchestrator, save_path, monkeypatch
):
    """T-017c: post-finalize roster → sync does not reactivate creation."""
    _roll_attributes_patch(monkeypatch, orchestrator)
    for text, _expected in INPUTS:
        orchestrator.process_turn(text)

    headless_app._save_session()
    _patch_session_state_path(orchestrator, save_path)
    orchestrator.creation.active = False

    orchestrator._sync_creation_from_status()

    assert orchestrator.creation.active is False


def test_t017c2_live_empty_roster_wins_over_stale_saved_roster(
    orchestrator, save_path, monkeypatch
):
    """T-017c2: live empty roster wins over stale saved roster snapshot."""
    _write_session_state(
        save_path,
        engine_status={
            "awaiting": "CHARACTER_CREATION",
            "roster": [{"display_name": "Ghost"}],
        },
    )
    _patch_session_state_path(orchestrator, save_path)
    _patch_live_status(
        monkeypatch,
        orchestrator,
        awaiting="CHARACTER_CREATION",
        roster=[],
    )
    orchestrator.creation.active = False

    orchestrator._sync_creation_from_status()

    assert orchestrator.creation.active is True


def test_t017d_legacy_without_engine_status_unchanged(
    headless_app, orchestrator, save_path
):
    """T-017d: legacy save without engine_status — load unchanged (T4c baseline)."""
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
    _patch_session_state_path(orchestrator, save_path)

    pre_active = orchestrator.creation.active
    headless_app._load_session()

    assert len(headless_app.narration.lines) == 1
    assert headless_app.narration.lines[0]["text"] == "Ledger line."
    assert orchestrator.creation.active == pre_active
    assert "engine_status" not in read_save(save_path)


def test_t017e_suggestions_nonempty_after_reconcile(
    orchestrator, save_path, monkeypatch
):
    """T-017e: reconcile at EQUIPMENT_GOLD → equipment suggestion chips."""
    _roll_attributes_patch(monkeypatch, orchestrator)
    for text, expected in INPUTS:
        if expected == "WORLD_INTRO":
            break
        orchestrator.process_turn(text)
    assert orchestrator.creation.step == "EQUIPMENT_GOLD"

    _write_session_state(
        save_path,
        creation_state=None,
        engine_status={"awaiting": "CHARACTER_CREATION", "roster": []},
    )
    _patch_session_state_path(orchestrator, save_path)
    _patch_live_status(
        monkeypatch,
        orchestrator,
        awaiting="CHARACTER_CREATION",
        roster=[],
    )
    orchestrator.creation.active = False

    orchestrator._sync_creation_from_status()

    assert orchestrator.get_player_suggestions() == [
        "Yes, confirm",
        "I need different gear",
    ]


def test_t017f_roster_setup_orphan_rows_no_force_active(
    orchestrator, save_path, monkeypatch
):
    """T-017f: ROSTER_SETUP with orphan characters → no force-active."""
    _patch_live_status(
        monkeypatch,
        orchestrator,
        awaiting="ROSTER_SETUP",
        roster=[],
        characters=[{"id": "x"}],
    )
    orchestrator.creation.active = False

    orchestrator._sync_creation_from_status()

    assert orchestrator.creation.active is False
