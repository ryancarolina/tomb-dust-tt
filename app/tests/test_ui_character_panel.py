"""Unit tests for left CharacterPanel and three-column layout (APP-062)."""

from __future__ import annotations

import os
from unittest.mock import MagicMock

import pygame


def _init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()


def _drain_queue(app):
    out = []
    while not app._ui_queue.empty():
        out.append(app._ui_queue.get_nowait())
    return out


def test_layout_uses_three_columns(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(1280, 800)

        assert app.character_panel.rect.width == int(1280 * 0.22)
        assert app.sidebar.rect.width == int(1280 * 0.30)
        assert app.narration.rect.width == 1280 - app.character_panel.rect.width - app.sidebar.rect.width
        assert app.narration.rect.left == app.character_panel.rect.right
    finally:
        pygame.quit()


def test_status_refresh_populates_inventory_and_spells(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(900, 600)

        bridge = MagicMock()
        bridge.list_inventory.return_value = {
            "ok": True,
            "character_id": "pc-1",
            "pack": [{"instanceId": "it-1", "itemId": "rations", "displayName": "Rations", "equipped": True}],
        }
        bridge.list_known_spells.return_value = {
            "ok": True,
            "spells": [{"id": "spark", "displayName": "Spark", "tier": 1, "mpCost": 1, "school": "evocation"}],
        }
        bridge.list_quests_for_ui.return_value = {
            "ok": True,
            "quests": [
                {
                    "quest_id": "holt-brothers-signet",
                    "displayName": "Brother's Signet",
                    "giverDisplayName": "Marshal Garrick Holt",
                    "state": "accepted",
                    "activeObjectiveLabel": "Recover the signet ring",
                }
            ],
        }
        app._orchestrator = MagicMock(bridge=bridge)

        app._ui_queue.put(("status", {"roster": [{"character_id": "pc-1"}], "party": {"address": "32-C"}}))
        app._process_ui_queue()

        bridge.list_inventory.assert_called_once_with(character_id="pc-1")
        bridge.list_known_spells.assert_called_once_with("pc-1")
        bridge.list_quests_for_ui.assert_called_once_with(active_only=True)
        assert app.character_panel._backpack_rows[0]["label"].endswith("[E]")
        assert "Spark" in app.character_panel._spell_rows[0]["label"]
        assert app.character_panel._quest_rows[0]["title"] == "Brother's Signet"
    finally:
        pygame.quit()


def test_backpack_selection_emits_queue_message(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(900, 600)
        app.character_panel.update_inventory(
            {
                "ok": True,
                "pack": [{"instanceId": "it-1", "itemId": "rations", "displayName": "Rations"}],
            }
        )

        body = app.character_panel._body_rect
        app.character_panel.handle_click((body.left + 8, body.top + 8))

        messages = _drain_queue(app)
        assert ("character_item_selected", {"instance_id": "it-1", "item_id": "rations"}) in messages
    finally:
        pygame.quit()


def test_backpack_click_empty_clears_selection(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(900, 600)
        app.character_panel.update_inventory(
            {
                "ok": True,
                "pack": [{"instanceId": "it-1", "itemId": "rations", "displayName": "Rations"}],
            }
        )
        body = app.character_panel._body_rect
        app.character_panel.handle_click((body.left + 8, body.top + 8))
        _drain_queue(app)

        app.character_panel.handle_click((body.left + 8, body.bottom - 8))
        messages = _drain_queue(app)
        assert ("character_item_selected", {"instance_id": None, "item_id": None}) in messages
    finally:
        pygame.quit()


def test_character_panel_scroll_changes_offset():
    _init_pygame()
    try:
        from ui.panels.character_panel import CharacterPanel

        panel = CharacterPanel(pygame.Rect(0, 0, 280, 260))
        panel.update_inventory(
            {
                "ok": True,
                "pack": [
                    {"instanceId": f"it-{idx}", "itemId": "rations", "displayName": f"Rations {idx}"}
                    for idx in range(20)
                ],
            }
        )

        start = panel._scroll_offset
        panel.handle_wheel(-2)

        assert panel._scroll_offset > start
    finally:
        pygame.quit()


def test_empty_states_during_creation(app_config):
    _init_pygame()
    try:
        from ui.app import App

        app = App(app_config)
        app._layout(900, 600)
        app.character_panel.update_inventory({"ok": False, "error": "no living character found"})
        app.character_panel.update_spells(None)
        app.character_panel.update_quests(None)

        assert app.character_panel._backpack_empty_message == "No delver yet"
        assert app.character_panel._spells_empty_message == "No spells known"
        assert app.character_panel._quests_empty_message == "No active quests."
    finally:
        pygame.quit()


def test_quests_tab_switch_and_empty_state(app_config):
    _init_pygame()
    try:
        from ui.panels.character_panel import CharacterPanel

        panel = CharacterPanel(pygame.Rect(0, 0, 280, 260))
        panel.update_quests({"ok": True, "quests": []})
        quests_tab = panel._tab_rects[CharacterPanel.TAB_QUESTS]
        panel.handle_click((quests_tab.centerx, quests_tab.centery))

        assert panel.active_tab == CharacterPanel.TAB_QUESTS
        assert panel._quest_rows == []
        assert panel._active_empty_message() == "No active quests."
    finally:
        pygame.quit()


def test_three_tab_layout_widths(app_config):
    _init_pygame()
    try:
        from ui.panels.character_panel import CharacterPanel

        panel = CharacterPanel(pygame.Rect(0, 0, 300, 240))
        tabs = list(panel._tab_rects.values())
        assert len(tabs) == 3
        assert tabs[0].width == tabs[1].width == tabs[2].width
    finally:
        pygame.quit()
