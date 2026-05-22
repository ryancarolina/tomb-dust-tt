"""UI image toggle and APP-095 NPC trigger tests."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pygame


def _init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()


def test_layout_splits_center_with_illustration_ratio(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(1280, 960)

        center_h = app.illustration.rect.height + app.narration.rect.height
        expected = int((960 - 50) * app_config["ui"]["illustration_height_ratio"])
        assert app.illustration.rect.left == app.character_panel.rect.right
        assert abs(app.illustration.rect.height - expected) <= 1
        assert center_h == 960 - 50
    finally:
        pygame.quit()


def test_toggle_images_off_cancels_inflight_generation(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(900, 600)
        app._images_enabled = True
        app.illustration.set_images_enabled(True)
        app._image_service = MagicMock()

        app._toggle_images_enabled()

        assert app._images_enabled is False
        assert app.illustration._images_enabled is False
        app._image_service.cancel_generation.assert_called_once()
    finally:
        pygame.quit()


def test_process_turn_requests_npc_illustration_when_no_item_selected(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(900, 600)
        app._tts_enabled = False
        app._current_turn_id = 1

        mock_orch = MagicMock()
        mock_orch.process_turn.return_value = "A line of narration."
        mock_orch.get_player_suggestions.return_value = []
        mock_orch.get_status.return_value = {"ok": True, "active": {"campaign_slug": "camp-a"}}
        app._orchestrator = mock_orch

        app._request_illustration = MagicMock()

        with patch(
            "tomb_gm.services.tts.scene.parse_scene",
            return_value=[{"voice": "isla-brack", "text": "Welcome, delver."}],
        ):
            app._process_turn("look", 1)

        app._request_illustration.assert_called_once_with("npc", "isla-brack", "Isla Brack")
    finally:
        pygame.quit()


def test_process_turn_skips_npc_trigger_when_item_selected(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(900, 600)
        app._tts_enabled = False
        app._current_turn_id = 2
        app._selected_character_catalog_item_id = "rations"

        mock_orch = MagicMock()
        mock_orch.process_turn.return_value = "A line of narration."
        mock_orch.get_player_suggestions.return_value = []
        mock_orch.get_status.return_value = {"ok": True, "active": {"campaign_slug": "camp-a"}}
        app._orchestrator = mock_orch

        app._request_illustration = MagicMock()

        with patch(
            "tomb_gm.services.tts.scene.parse_scene",
            return_value=[{"voice": "marshal-garrick-holt", "text": "Orders."}],
        ):
            app._process_turn("look", 2)

        app._request_illustration.assert_not_called()
    finally:
        pygame.quit()
