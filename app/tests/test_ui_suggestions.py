"""Unit tests for code-owned player suggestion chips (APP-065)."""

from __future__ import annotations

import os
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from test_creation_flow import FIXED_ROLL, INPUTS

from ui.suggestions import (
    build_player_suggestions,
    filter_player_suggestions,
    is_blocked_chip_token,
)


def test_blocked_internal_tokens():
    assert is_blocked_chip_token("EQUIPMENT_CONFIRMATION") is True
    assert is_blocked_chip_token("SKILLS_INPUT") is True
    assert is_blocked_chip_token("PLAYER_ACTIONS") is True
    assert is_blocked_chip_token("Yes, confirm") is False
    assert is_blocked_chip_token("load game") is False


def test_equipment_gold_active_chips():
    chips = build_player_suggestions(
        creation_step="EQUIPMENT_GOLD",
        creation_active=True,
        engine_awaiting="CHARACTER_CREATION",
        has_save=False,
    )
    assert chips == ["Yes, confirm", "I need different gear"]
    assert not any(is_blocked_chip_token(c) for c in chips)


def test_equipment_confirm_regex_alignment():
    from gm.creation import is_equipment_confirm

    assert is_equipment_confirm("Yes, confirm")
    assert not is_equipment_confirm("I need different gear")


def test_inactive_creation_ignores_step():
    chips = build_player_suggestions(
        creation_step="EQUIPMENT_GOLD",
        creation_active=False,
        engine_awaiting="CHARACTER_CREATION",
        has_save=False,
    )
    assert chips == []


def test_setup_has_save():
    chips = build_player_suggestions(
        creation_step="NAME",
        creation_active=False,
        engine_awaiting="SETUP",
        has_save=True,
    )
    assert chips == ["load game", "new game"]


def test_setup_no_save():
    chips = build_player_suggestions(
        creation_step="NAME",
        creation_active=False,
        engine_awaiting="SETUP",
        has_save=False,
    )
    assert chips == ["new game"]


def test_name_step_no_chips():
    chips = build_player_suggestions(
        creation_step="NAME",
        creation_active=True,
        engine_awaiting="CHARACTER_CREATION",
        has_save=False,
    )
    assert chips == []


@pytest.mark.parametrize(
    "bad",
    [
        "EQUIPMENT_CONFIRMATION",
        "SKILLS_INPUT",
        "PLAYER_ACTIONS",
        "RECEPTION_CHOICE",
        "STATS_REVIEW",
        "NAME_INPUT",
    ],
)
def test_builder_never_returns_blocked(bad: str):
    assert filter_player_suggestions([bad, "Yes, confirm"]) == ["Yes, confirm"]


def test_get_player_suggestions_empty_after_finalize(orchestrator, monkeypatch):
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )
    for text, _expected in INPUTS:
        orchestrator.process_turn(text)

    assert orchestrator.creation.active is False
    assert orchestrator.creation.step == "WORLD_INTRO"
    assert orchestrator.get_player_suggestions() == []


def test_queue_turn_suggestions_empty_list_always_put(app_config):
    from ui.app import App

    app = App(app_config)
    app._current_turn_id = 1
    mock_orch = MagicMock()
    mock_orch.get_player_suggestions.return_value = []
    app._orchestrator = mock_orch

    app._queue_turn_suggestions(1)

    msg = app._ui_queue.get_nowait()
    assert msg == ("suggestions", [])
    mock_orch.get_player_suggestions.assert_called_once()


def test_queue_turn_suggestions_stale_turn_noop(app_config):
    from ui.app import App

    app = App(app_config)
    app._current_turn_id = 2
    mock_orch = MagicMock()
    app._orchestrator = mock_orch

    app._queue_turn_suggestions(1)

    assert app._ui_queue.empty()
    mock_orch.get_player_suggestions.assert_not_called()


def test_process_turn_exception_refreshes_suggestions(app_config):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame
    from ui.app import App

    pygame.init()
    try:
        app = App(app_config)
        app._layout(800, 600)
        turn_id = 7
        app._current_turn_id = turn_id
        mock_orch = MagicMock()
        mock_orch.get_player_suggestions.return_value = []
        mock_orch.process_turn.side_effect = RuntimeError("boom")
        mock_orch.get_status.side_effect = RuntimeError("should not reach")
        app._orchestrator = mock_orch

        app._process_turn("x", turn_id)

        messages = []
        while not app._ui_queue.empty():
            messages.append(app._ui_queue.get_nowait())

        assert ("error", "boom") in messages
        assert ("suggestions", []) in messages
    finally:
        pygame.quit()
