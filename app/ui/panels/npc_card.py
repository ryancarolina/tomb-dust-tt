"""NPC card — shows current speaker with voice indicator."""

from __future__ import annotations

import pygame
from ui.theme import (
    BG_PANEL, BG_BUTTON, BG_BUTTON_HOVER, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
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
        self._tts_chip_visible = False
        self._tts_enabled = True
        self._voice_chip_rect = pygame.Rect(0, 0, 0, 0)
        self._voice_chip_hovered = False
        self._font = None
        self._font_small = None

    def _ensure_fonts(self):
        if not self._font:
            self._font = pygame.font.SysFont("Consolas", FONT_SIZE, bold=True)
            self._font_small = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)

    def set_speaker(self, voice: str, speaking: bool = True):
        self.current_voice = voice
        self.speaking = speaking

    def set_tts_chip_visible(self, visible: bool) -> None:
        self._tts_chip_visible = visible
        self._layout_voice_chip()

    def set_tts_enabled(self, enabled: bool) -> None:
        self._tts_enabled = enabled
        self._layout_voice_chip()

    def handle_voice_toggle_click(self, pos: tuple[int, int]) -> bool:
        if not self._tts_chip_visible:
            return False
        return self._voice_chip_rect.collidepoint(pos)

    def handle_voice_hover(self, pos: tuple[int, int]) -> None:
        if not self._tts_chip_visible:
            self._voice_chip_hovered = False
            return
        self._voice_chip_hovered = self._voice_chip_rect.collidepoint(pos)

    def _voice_chip_label(self) -> str:
        return "Voice: On" if self._tts_enabled else "Voice: Off"

    def _layout_voice_chip(self) -> None:
        self._ensure_fonts()
        if not self._tts_chip_visible:
            self._voice_chip_rect = pygame.Rect(0, 0, 0, 0)
            return
        label = self._voice_chip_label()
        text_w = self._font_small.size(label)[0]
        chip_w = text_w + 16
        chip_h = self._font_small.get_linesize() + 6
        chip_x = self.rect.right - PANEL_PADDING - chip_w
        chip_y = self.rect.top + PANEL_PADDING
        self._voice_chip_rect = pygame.Rect(chip_x, chip_y, chip_w, chip_h)

    def resize(self, rect: pygame.Rect):
        self.rect = rect
        self._layout_voice_chip()

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
        max_name_w = self.rect.width - PANEL_PADDING * 2
        if self._tts_chip_visible and self._voice_chip_rect.width:
            max_name_w = self._voice_chip_rect.left - x - PANEL_PADDING
        if max_name_w > 0 and name_surf.get_width() > max_name_w:
            truncated = name
            while truncated and self._font.size(truncated + "…")[0] > max_name_w:
                truncated = truncated[:-1]
            name_surf = self._font.render(truncated + "…" if truncated else "…", True, color)
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

        if self._tts_chip_visible and self._voice_chip_rect.width:
            chip_bg = BG_BUTTON_HOVER if self._voice_chip_hovered else BG_BUTTON
            pygame.draw.rect(screen, chip_bg, self._voice_chip_rect, border_radius=4)
            pygame.draw.rect(screen, BORDER, self._voice_chip_rect, 1, border_radius=4)
            chip_text_color = TEXT_SECONDARY if self._tts_enabled else TEXT_MUTED
            chip_label = self._font_small.render(self._voice_chip_label(), True, chip_text_color)
            screen.blit(
                chip_label,
                (
                    self._voice_chip_rect.centerx - chip_label.get_width() // 2,
                    self._voice_chip_rect.centery - chip_label.get_height() // 2,
                ),
            )
