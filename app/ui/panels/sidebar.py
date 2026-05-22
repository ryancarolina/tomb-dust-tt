"""Sidebar: combines NPC card + stats + map into right column."""

from __future__ import annotations

import pygame
from pathlib import Path
from ui.panels.stats import StatsPanel
from ui.panels.map_view import MapView
from ui.panels.npc_card import NpcCard


class Sidebar:
    def __init__(self, rect: pygame.Rect, content_root: Path | None = None):
        self.rect = rect
        self._content_root = content_root
        self._map_travel_blocked = False
        self._map_travel_blocked_hint = "Finish Registry intake first"
        self._creation_step: str | None = None
        self._creation_step_display: str | None = None
        self._do_layout(rect)

    def _do_layout(self, rect: pygame.Rect):
        npc_h = 70
        stats_h = (rect.height - npc_h) // 2
        map_h = rect.height - npc_h - stats_h

        self.npc_card = NpcCard(pygame.Rect(rect.left, rect.top, rect.width, npc_h))
        self.stats = StatsPanel(pygame.Rect(rect.left, rect.top + npc_h, rect.width, stats_h))
        self.map = MapView(
            pygame.Rect(rect.left, rect.top + npc_h + stats_h, rect.width, map_h),
            content_root=self._content_root,
        )
        self.map.set_travel_blocked(self._map_travel_blocked, self._map_travel_blocked_hint)
        self.stats.update_from_status(
            {
                "creation_step": self._creation_step,
                "creation_step_display": self._creation_step_display,
            }
        )

    def update_from_status(self, status: dict):
        if "creation_step" in status or "creation_step_display" in status:
            self._creation_step = status.get("creation_step")
            self._creation_step_display = status.get("creation_step_display")
        self.stats.update_from_status(status)
        if "map_travel_blocked" in status:
            blocked = bool(status.get("map_travel_blocked"))
            hint = status.get("map_travel_blocked_hint")
            self._map_travel_blocked = blocked
            if hint is not None:
                self._map_travel_blocked_hint = hint
            self.map.set_travel_blocked(blocked, hint)
        party = status.get("party")
        if party and party.get("address"):
            self.map.update_position(party["address"])

    def set_speaker(self, voice: str, speaking: bool = True):
        self.npc_card.set_speaker(voice, speaking)

    def handle_hover(self, pos: tuple[int, int]):
        if self.map.rect.collidepoint(pos):
            self.map.handle_hover(pos)

    def handle_map_click(self, pos: tuple[int, int]) -> str | None:
        if self.map.rect.collidepoint(pos):
            if self.map.travel_blocked:
                return None
            return self.map.handle_click(pos)
        return None

    def resize(self, rect: pygame.Rect):
        self.rect = rect
        self._do_layout(rect)

    def draw(self, screen: pygame.Surface):
        self.npc_card.draw(screen)
        self.stats.draw(screen)
        self.map.draw(screen)
