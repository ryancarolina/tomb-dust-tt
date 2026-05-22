"""Unit tests for narration tail-follow scroll (APP-060)."""

from __future__ import annotations

import os

import pygame
import pytest

from ui.panels.narration import NarrationPanel

TALL_TABLE = """\
| Stat | Roll | Mod |
| --- | --- | --- |
| STR | 14 | +2 |
| DEX | 12 | +1 |
| CON | 16 | +3 |
| INT | 10 | +0 |
| WIS | 8 | -1 |
| CHA | 13 | +1 |
| LUC | 11 | +0 |
| Notes | Long wrapped prose to force extra layout height beyond the viewport. |
"""


def _expected_bottom(panel: NarrationPanel) -> int:
    return max(0, panel._total_height - panel.rect.height + 40)


@pytest.fixture
def panel():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    try:
        yield NarrationPanel(pygame.Rect(0, 0, 400, 120))
    finally:
        pygame.quit()


@pytest.fixture
def screen():
    return pygame.Surface((400, 120))


def test_stale_scroll_before_rebuild_fails(panel: NarrationPanel, screen):
    panel.add_line(TALL_TABLE, "narrator")
    panel.scroll_to_bottom()
    stale_offset = panel._scroll_offset
    panel.draw(screen)
    expected = _expected_bottom(panel)
    assert expected > 0
    assert stale_offset < expected


def test_request_follow_tail_after_draw_pins_bottom(panel: NarrationPanel, screen):
    panel.add_line(TALL_TABLE, "narrator")
    panel.request_follow_tail()
    panel.draw(screen)
    assert panel._scroll_offset == _expected_bottom(panel)
    assert panel._follow_tail is False


def test_player_line_follows_tail(panel: NarrationPanel, screen):
    panel.add_line("hello from the player", "player")
    panel.request_follow_tail()
    panel.draw(screen)
    assert panel._scroll_offset == _expected_bottom(panel)


def test_error_line_follows_tail(panel: NarrationPanel, screen):
    panel.add_line("[Error: boom]", "narrator")
    panel.request_follow_tail()
    panel.draw(screen)
    assert panel._scroll_offset == _expected_bottom(panel)


def test_multiple_follow_requests_coalesce(panel: NarrationPanel, screen):
    panel.add_line(TALL_TABLE, "narrator")
    panel.request_follow_tail()
    panel.request_follow_tail()
    panel.request_follow_tail()
    panel.draw(screen)
    assert panel._scroll_offset == _expected_bottom(panel)
    assert panel._follow_tail is False


def test_clear_clears_follow_flag(panel: NarrationPanel):
    panel.request_follow_tail()
    panel.clear()
    assert panel._follow_tail is False
    assert panel._scroll_offset == 0
