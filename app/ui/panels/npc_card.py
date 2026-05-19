"""NPC card — shows current speaker with voice indicator."""

from __future__ import annotations

import pygame
from ui.theme import (
    BG_PANEL, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    BORDER, PANEL_PADDING, FONT_SIZE, FONT_SIZE_SMALL,
    get_voice_color,
)


VOICE_DISPLAY_NAMES = {
    "narrator": "Game Master",
    "gm": "Game Master",
    "marshal-garrick-holt": "Marshal Garrick Holt",
    "postern-clerk": "Postern Clerk",
    "breley-sergeant": "Breley Sergeant",
    "npc": "NPC",
    "player": "You",
}


class NpcCard:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.current_voice = "narrator"
        self.speaking = False
        self._font = None
        self._font_small = None

    def _ensure_fonts(self):
        if not self._font:
            self._font = pygame.font.SysFont("Consolas", FONT_SIZE, bold=True)
            self._font_small = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)

    def set_speaker(self, voice: str, speaking: bool = True):
        self.current_voice = voice
        self.speaking = speaking

    def resize(self, rect: pygame.Rect):
        self.rect = rect

    def draw(self, screen: pygame.Surface):
        self._ensure_fonts()
        pygame.draw.rect(screen, BG_PANEL, self.rect)
        pygame.draw.rect(screen, BORDER, self.rect, 1)

        x = self.rect.left + PANEL_PADDING
        y = self.rect.top + PANEL_PADDING

        label = self._font_small.render("SPEAKING", True, TEXT_MUTED)
        screen.blit(label, (x, y))
        y += label.get_height() + 4

        color = get_voice_color(self.current_voice)
        name = VOICE_DISPLAY_NAMES.get(self.current_voice, self.current_voice)
        name_surf = self._font.render(name, True, color)
        screen.blit(name_surf, (x, y))
        y += name_surf.get_height() + 4

        if self.speaking:
            indicator_color = color
            pulse = (pygame.time.get_ticks() // 300) % 4
            for i in range(3):
                bar_h = 6 + (4 if i == pulse else 0)
                bar_y = y + (10 - bar_h) // 2
                pygame.draw.rect(screen, indicator_color, (x + i * 8, bar_y, 4, bar_h), border_radius=1)
        else:
            idle = self._font_small.render("idle", True, TEXT_MUTED)
            screen.blit(idle, (x, y))
