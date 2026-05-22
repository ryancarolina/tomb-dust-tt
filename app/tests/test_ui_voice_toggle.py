"""Unit tests for Voice chip TTS mute toggle (APP-058)."""

from __future__ import annotations

import copy
import json
import os
from unittest.mock import MagicMock, patch

import pygame
import pytest


def _init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()


def _drain_queue(app):
    messages = []
    while not app._ui_queue.empty():
        messages.append(app._ui_queue.get_nowait())
    return messages


def test_voice_chip_hidden_text_only(app_config):
    _init_pygame()
    try:
        from ui.app import App

        config = copy.deepcopy(app_config)
        config.setdefault("tts", {})["mode"] = "text_only"
        app = App(config)
        app._layout(1280, 800)

        assert app.sidebar.npc_card._tts_chip_visible is False
        assert app.sidebar.handle_voice_toggle_click((100, 20)) is False
    finally:
        pygame.quit()


def test_boot_chip_sync(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(1280, 800)

        assert app._tts_enabled is True
        assert app.sidebar.npc_card._tts_chip_visible is True
        assert app.sidebar.npc_card._voice_chip_label() == "Voice: On"
    finally:
        pygame.quit()


def test_npc_card_click_hit():
    _init_pygame()
    try:
        from ui.panels.npc_card import NpcCard

        card = NpcCard(pygame.Rect(0, 0, 300, 70))
        card.set_tts_chip_visible(True)
        card.set_tts_enabled(True)

        inside = card._voice_chip_rect.center
        outside = (card.rect.left + 5, card.rect.top + 5)

        assert card.handle_voice_toggle_click(inside) is True
        assert card.handle_voice_toggle_click(outside) is False
    finally:
        pygame.quit()


def test_npc_card_hover_and_off_label():
    _init_pygame()
    try:
        from ui.panels.npc_card import NpcCard
        from ui.theme import TEXT_MUTED, TEXT_SECONDARY

        card = NpcCard(pygame.Rect(0, 0, 300, 70))
        card.set_tts_chip_visible(True)
        card.set_tts_enabled(False)

        assert card._voice_chip_label() == "Voice: Off"
        card.handle_voice_hover(card._voice_chip_rect.center)
        assert card._voice_chip_hovered is True
        card.handle_voice_hover((0, 0))
        assert card._voice_chip_hovered is False

        card.set_tts_enabled(True)
        assert card._voice_chip_label() == "Voice: On"
        assert TEXT_SECONDARY != TEXT_MUTED
    finally:
        pygame.quit()


def test_toggle_off_skips_speak(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(800, 600)
        app._tts_enabled = False
        app._current_turn_id = 1

        mock_orch = MagicMock()
        mock_orch.process_turn.return_value = "The torch flickers."
        mock_orch.get_player_suggestions.return_value = []
        mock_orch.get_status.return_value = {"ok": True}
        app._orchestrator = mock_orch

        with patch("tomb_gm.services.tts.speak_scene") as speak_scene:
            app._process_turn("look around", 1)
            speak_scene.assert_not_called()

        messages = _drain_queue(app)
        assert any(msg == ("turn_idle", 1) for msg in messages)
    finally:
        pygame.quit()


def test_toggle_on_speaks(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(800, 600)
        app._tts_enabled = True
        app._current_turn_id = 2

        mock_orch = MagicMock()
        mock_orch.process_turn.return_value = "The torch flickers."
        mock_orch.get_player_suggestions.return_value = []
        mock_orch.get_status.return_value = {"ok": True}
        app._orchestrator = mock_orch

        def _run_inline(target=None, args=(), daemon=True):
            class _Thread:
                def start(self):
                    if target:
                        target(*args)

            return _Thread()

        with patch("ui.app.threading.Thread", side_effect=_run_inline):
            with patch("tomb_gm.services.tts.speak_scene") as speak_scene:
                app._process_turn("look around", 2)
                speak_scene.assert_called_once()
    finally:
        pygame.quit()


def test_toggle_off_calls_request_stop(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(800, 600)
        app._tts_enabled = True
        app._turn_state = "speaking"

        with patch("tomb_gm.services.tts.queue.request_stop") as request_stop:
            app._toggle_tts_enabled()
            request_stop.assert_called_once()
    finally:
        pygame.quit()


def test_toggle_off_sets_idle(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(800, 600)
        app._tts_enabled = True
        app._turn_state = "speaking"
        app.sidebar.set_speaker("narrator", True)

        with patch("tomb_gm.services.tts.queue.request_stop"):
            app._toggle_tts_enabled()

        assert app._tts_enabled is False
        assert app._turn_state == "idle"
        assert app.sidebar.npc_card.speaking is False
    finally:
        pygame.quit()


def test_load_session_resets_toggle_default(app_config, tmp_path, monkeypatch):
    _init_pygame()
    try:
        from ui.app import App

        save_file = tmp_path / "session_state.json"
        save_file.write_text(
            json.dumps(
                {
                    "narration_lines": [],
                    "input_history": [],
                    "visited_cells": [],
                    "current_address": "",
                    "orchestrator_history": [],
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr("ui.app.SAVE_PATH", save_file)

        app = App(app_config)
        app._layout(800, 600)
        app._tts_enabled = False
        app._orchestrator = MagicMock()
        app._orchestrator.get_status.return_value = {}

        app._load_session()

        assert app._tts_enabled is True
        assert app.sidebar.npc_card._tts_enabled is True
        assert app.sidebar.npc_card._voice_chip_label() == "Voice: On"
    finally:
        pygame.quit()


def test_resize_preserves_voice_off_label(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(1280, 800)
        app._tts_enabled = False
        app.sidebar.set_tts_enabled(False)

        app._layout(1024, 768)

        assert app.sidebar.npc_card._tts_enabled is False
        assert app.sidebar.npc_card._voice_chip_label() == "Voice: Off"
    finally:
        pygame.quit()


def test_speak_narration_muted_queues_turn_idle(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(800, 600)
        app._tts_enabled = False
        app._current_turn_id = 5

        app._speak_narration("text", [], 5)

        messages = _drain_queue(app)
        assert messages == [("turn_idle", 5)]
    finally:
        pygame.quit()
