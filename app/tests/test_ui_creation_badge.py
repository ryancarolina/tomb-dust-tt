"""Unit tests for creation step badge in stats panel (APP-036)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pygame
import pytest

from gm.creation import (
    CREATION_STEPS,
    CREATION_STATUS_LABELS,
    CREATION_STEP_DISPLAY,
    format_creation_step_display,
)


def test_creation_step_display_covers_all_steps():
    for step in CREATION_STEPS:
        assert step in CREATION_STEP_DISPLAY
    footer_tokens = set(CREATION_STATUS_LABELS.values())
    for label in CREATION_STEP_DISPLAY.values():
        assert label not in footer_tokens


def test_format_creation_step_display_fallback():
    assert format_creation_step_display("UNKNOWN_STEP") == "Unknown Step"
    assert format_creation_step_display("SKILLS") == "Skills"


def test_get_creation_step_badge_active(orchestrator):
    orchestrator.creation.active = True
    orchestrator.creation.step = "SKILLS"
    assert orchestrator.get_creation_step_badge() == {
        "step": "SKILLS",
        "display_label": "Skills",
    }


def test_get_creation_step_badge_inactive(orchestrator, monkeypatch):
    orchestrator.creation.active = False
    orchestrator.creation.step = "WORLD_INTRO"
    monkeypatch.setattr(
        orchestrator.bridge,
        "status",
        lambda: {"awaiting": "CHARACTER_CREATION", "roster": []},
    )
    assert orchestrator.get_creation_step_badge() is None


def test_enrich_status_for_ui_creation_fields(app_config):
    from ui.app import App

    app = App(app_config)
    mock_orch = MagicMock()
    mock_orch.is_map_travel_blocked.return_value = False
    mock_orch.get_creation_step_badge.return_value = {
        "step": "RACE",
        "display_label": "Race",
    }
    app._orchestrator = mock_orch

    enriched = app._enrich_status_for_ui({"awaiting": "CHARACTER_CREATION"})
    assert enriched["creation_step"] == "RACE"
    assert enriched["creation_step_display"] == "Race"

    mock_orch.get_creation_step_badge.return_value = None
    enriched = app._enrich_status_for_ui({"awaiting": "PLAYER_ACTIONS"})
    assert enriched["creation_step"] is None
    assert enriched["creation_step_display"] is None


def test_stats_panel_shows_badge_from_status():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    try:
        from ui.panels.stats import StatsPanel

        panel = StatsPanel(pygame.Rect(0, 0, 200, 300))
        panel.update_from_status({"creation_step_display": "Race"})
        assert panel.creation_step_display == "Race"
    finally:
        pygame.quit()


def test_stats_panel_clears_badge_when_none():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    try:
        from ui.panels.stats import StatsPanel

        panel = StatsPanel(pygame.Rect(0, 0, 200, 300))
        panel.update_from_status({"creation_step_display": "Race"})
        panel.update_from_status({"creation_step_display": None})
        assert panel.creation_step_display is None
    finally:
        pygame.quit()


def test_sidebar_resize_preserves_creation_badge():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    try:
        from ui.panels.sidebar import Sidebar

        sidebar = Sidebar(pygame.Rect(0, 0, 300, 600))
        sidebar.update_from_status(
            {
                "creation_step": "SKILLS",
                "creation_step_display": "Skills",
            }
        )
        assert sidebar.stats.creation_step_display == "Skills"
        sidebar.resize(pygame.Rect(0, 0, 320, 640))
        assert sidebar.stats.creation_step_display == "Skills"
    finally:
        pygame.quit()


def test_process_turn_exception_queues_creation_badge(app_config):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(800, 600)
        turn_id = 7
        app._current_turn_id = turn_id
        mock_orch = MagicMock()
        mock_orch.get_player_suggestions.return_value = []
        mock_orch.is_map_travel_blocked.return_value = True
        mock_orch.get_creation_step_badge.return_value = {
            "step": "NAME",
            "display_label": "Name",
        }
        mock_orch.get_status.return_value = {"awaiting": "CHARACTER_CREATION", "roster": []}
        mock_orch.process_turn.side_effect = RuntimeError("boom")
        app._orchestrator = mock_orch

        app._process_turn("x", turn_id)

        messages = []
        while not app._ui_queue.empty():
            messages.append(app._ui_queue.get_nowait())

        status_msgs = [m for m in messages if m[0] == "status"]
        assert len(status_msgs) == 1
        status = status_msgs[0][1]
        assert status["creation_step"] == "NAME"
        assert status["creation_step_display"] == "Name"
    finally:
        pygame.quit()
