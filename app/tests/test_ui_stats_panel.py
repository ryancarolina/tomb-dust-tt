"""Unit tests for StatsPanel full stat block (APP-102)."""

from __future__ import annotations

import os

import pygame
import pytest


@pytest.fixture(autouse=True)
def pygame_headless():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    yield
    pygame.quit()


def _sample_roster_status() -> dict:
    return {
        "roster": [
            {
                "display_name": "Kira Flupps",
                "hp": "12/14",
                "mp": "4/10",
                "fortune": "2/3",
                "gold": 45,
                "class_display": "Militia",
                "class_tier": 1,
                "proficiency_bonus": 2,
                "ac": 14,
                "attributes": {
                    "STR": 12,
                    "AGI": 14,
                    "STA": 15,
                    "INT": 8,
                    "SPI": 10,
                    "LUC": 14,
                },
                "attribute_modifiers": {
                    "STR": 1,
                    "AGI": 2,
                    "STA": 2,
                    "INT": -1,
                    "SPI": 0,
                    "LUC": 2,
                },
                "skills": [
                    {"skill_id": "polearm-proficiency", "level": 4, "display_name": "Polearm Proficiency"},
                    {"skill_id": "stealth", "level": 2, "display_name": "Stealth"},
                    {"skill_id": "perception", "level": 1, "display_name": "Perception"},
                ],
                "conditions": ["Wounded"],
                "concentration": "Shield",
            }
        ],
        "party": {"phase": "preparation", "address": "32-C"},
    }


def test_update_from_status_populates_full_stat_block():
    from ui.panels.stats import StatsPanel

    panel = StatsPanel(pygame.Rect(0, 0, 320, 440))
    panel.update_from_status(_sample_roster_status())

    assert panel.has_roster is True
    assert panel.character_name == "Kira Flupps"
    assert panel.class_display == "Militia"
    assert panel.class_tier == 1
    assert panel.proficiency_bonus == 2
    assert panel.ac == 14
    assert panel.attributes["STR"] == 12
    assert panel.attribute_modifiers["INT"] == -1
    assert len(panel.skills) == 3
    assert panel.conditions == ["Wounded"]
    assert panel.concentration == "Shield"
    assert panel.address == "32-C"


def test_update_from_status_clears_stat_block_without_roster():
    from ui.panels.stats import StatsPanel

    panel = StatsPanel(pygame.Rect(0, 0, 320, 440))
    panel.update_from_status(_sample_roster_status())
    panel.update_from_status(
        {
            "creation_step_display": "Skills",
            "roster": [],
            "party": {"phase": "preparation", "address": "23-A"},
        }
    )

    assert panel.has_roster is False
    assert panel.character_name == "—"
    assert panel.attributes == {}
    assert panel.skills == []
    assert panel.ac == 0
    assert panel.creation_step_display == "Skills"


def test_draw_full_stat_block_does_not_raise():
    from ui.panels.stats import StatsPanel

    panel = StatsPanel(pygame.Rect(0, 0, 320, 440))
    panel.update_from_status(_sample_roster_status())
    screen = pygame.Surface((320, 440))
    panel.draw(screen)


def test_sidebar_stats_height_bias_at_960():
    from ui.panels.sidebar import Sidebar

    sidebar = Sidebar(pygame.Rect(0, 0, 384, 960))
    assert sidebar.stats.rect.height >= 420
    assert sidebar.map.rect.height >= 200
    assert sidebar.stats.rect.height + sidebar.map.rect.height + 70 == 960


def test_skills_wrap_limits_visible_lines():
    from ui.panels.stats import StatsPanel

    panel = StatsPanel(pygame.Rect(0, 0, 200, 440))
    panel.update_from_status(
        {
            "roster": [
                {
                    "display_name": "Wide",
                    "hp": "10/10",
                    "fortune": "1/1",
                    "gold": 0,
                    "class_display": "Militia",
                    "class_tier": 1,
                    "proficiency_bonus": 2,
                    "ac": 10,
                    "attributes": {"STR": 10, "AGI": 10, "STA": 10, "INT": 10, "SPI": 10, "LUC": 10},
                    "attribute_modifiers": {
                        "STR": 0,
                        "AGI": 0,
                        "STA": 0,
                        "INT": 0,
                        "SPI": 0,
                        "LUC": 0,
                    },
                    "skills": [
                        {"skill_id": "swordsmanship", "level": 4, "display_name": "Swordsmanship"},
                        {"skill_id": "archery", "level": 3, "display_name": "Archery"},
                        {"skill_id": "perception", "level": 2, "display_name": "Perception"},
                        {"skill_id": "lore", "level": 1, "display_name": "Lore"},
                        {"skill_id": "stealth", "level": 1, "display_name": "Stealth"},
                    ],
                }
            ],
            "party": {"phase": "delve", "address": "32-C"},
        }
    )
    panel._ensure_fonts()
    lines = panel._wrap_skill_lines(panel.rect.width - 24)
    assert len(lines) <= 3
