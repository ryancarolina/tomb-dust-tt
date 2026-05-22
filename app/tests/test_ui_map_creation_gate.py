"""Unit tests for map travel block during creation (APP-037)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pygame
import pytest

from test_creation_flow import FIXED_ROLL, INPUTS


def test_is_map_travel_blocked_active_creation(orchestrator, monkeypatch):
    orchestrator.creation.active = True
    monkeypatch.setattr(
        orchestrator.bridge,
        "status",
        lambda: {"awaiting": "PLAYER_ACTIONS", "roster": [{"name": "x"}]},
    )
    assert orchestrator.is_map_travel_blocked() is True


def test_is_map_travel_blocked_desync_guard(orchestrator, monkeypatch):
    orchestrator.creation.active = False
    monkeypatch.setattr(
        orchestrator.bridge,
        "status",
        lambda: {"awaiting": "CHARACTER_CREATION", "roster": []},
    )
    assert orchestrator.is_map_travel_blocked() is True


def test_is_map_travel_blocked_resume_edge(orchestrator, monkeypatch):
    orchestrator.creation.active = False
    monkeypatch.setattr(
        orchestrator.bridge,
        "status",
        lambda: {"awaiting": "CHARACTER_CREATION", "roster": [{"name": "Dumpy"}]},
    )
    assert orchestrator.is_map_travel_blocked() is False


def test_is_map_travel_blocked_post_finalize(orchestrator, monkeypatch):
    monkeypatch.setattr(
        orchestrator.bridge,
        "roll_attributes",
        lambda race: {**FIXED_ROLL, "race": race},
    )
    for text, _expected in INPUTS:
        orchestrator.process_turn(text)

    assert orchestrator.creation.active is False
    assert orchestrator.is_map_travel_blocked() is False


def test_map_view_click_blocked_returns_none():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    try:
        from ui.panels.map_view import MapView

        rect = pygame.Rect(0, 0, 200, 200)
        mv = MapView(rect)
        mv.set_travel_blocked(True)
        assert mv.handle_click((100, 100)) is None
    finally:
        pygame.quit()


def test_map_view_default_hint_string():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    try:
        from ui.panels.map_view import MapView

        mv = MapView(pygame.Rect(0, 0, 200, 200))
        assert mv.travel_blocked_hint == "Finish Registry intake first"
    finally:
        pygame.quit()


def test_enrich_status_for_ui_payload(app_config):
    from ui.app import App, MAP_TRAVEL_BLOCKED_HINT

    app = App(app_config)
    mock_orch = MagicMock()
    mock_orch.is_map_travel_blocked.return_value = True
    mock_orch.get_creation_step_badge.return_value = None
    mock_orch.get_status.return_value = {"awaiting": "CHARACTER_CREATION"}
    app._orchestrator = mock_orch

    enriched = app._enrich_status_for_ui({"awaiting": "CHARACTER_CREATION"})

    assert enriched["map_travel_blocked"] is True
    assert enriched["map_travel_blocked_hint"] == MAP_TRAVEL_BLOCKED_HINT


def test_sidebar_update_from_status_forwards_block():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    try:
        from ui.panels.sidebar import Sidebar

        sidebar = Sidebar(pygame.Rect(0, 0, 300, 600))
        sidebar.update_from_status(
            {
                "map_travel_blocked": True,
                "map_travel_blocked_hint": "Finish Registry intake first",
                "party": {"address": "32-C"},
            }
        )
        assert sidebar.map.travel_blocked is True
        assert sidebar.map.current_address == "32-C"
        assert sidebar._map_travel_blocked is True
    finally:
        pygame.quit()


def test_sidebar_resize_preserves_blocked():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    try:
        from ui.panels.sidebar import Sidebar

        sidebar = Sidebar(pygame.Rect(0, 0, 300, 600))
        sidebar.update_from_status(
            {
                "map_travel_blocked": True,
                "map_travel_blocked_hint": "Finish Registry intake first",
            }
        )
        sidebar.resize(pygame.Rect(0, 0, 320, 640))
        assert sidebar.map.travel_blocked is True
        assert sidebar.map.travel_blocked_hint == "Finish Registry intake first"
    finally:
        pygame.quit()


def test_process_turn_exception_queues_enriched_status(app_config):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    try:
        from ui.app import App, MAP_TRAVEL_BLOCKED_HINT

        app = App(app_config)
        app._layout(800, 600)
        turn_id = 7
        app._current_turn_id = turn_id
        mock_orch = MagicMock()
        mock_orch.get_player_suggestions.return_value = []
        mock_orch.is_map_travel_blocked.return_value = True
        mock_orch.get_creation_step_badge.return_value = None
        mock_orch.get_status.return_value = {"awaiting": "CHARACTER_CREATION", "roster": []}
        mock_orch.process_turn.side_effect = RuntimeError("boom")
        app._orchestrator = mock_orch

        app._process_turn("x", turn_id)

        messages = []
        while not app._ui_queue.empty():
            messages.append(app._ui_queue.get_nowait())

        assert ("error", "boom") in messages
        assert ("suggestions", []) in messages
        status_msgs = [m for m in messages if m[0] == "status"]
        assert len(status_msgs) == 1
        status = status_msgs[0][1]
        assert status["map_travel_blocked"] is True
        assert status["map_travel_blocked_hint"] == MAP_TRAVEL_BLOCKED_HINT
    finally:
        pygame.quit()
