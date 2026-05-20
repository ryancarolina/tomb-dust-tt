"""Scrolling narration panel with per-voice styling."""

from __future__ import annotations

import pygame
from ui.theme import (
    BG_PANEL, TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, BORDER, PANEL_PADDING, SCROLLBAR_WIDTH,
    FONT_SIZE, FONT_SIZE_SMALL, get_voice_color,
)
from ui.rich_text import (
    render_wrapped_line, render_table, StyledSpan,
    parse_markdown_spans, is_table_line, is_separator_line,
)


VOICE_LABELS = {
    "narrator": "GM",
    "gm": "GM",
    "marshal-garrick-holt": "Holt",
    "postern-clerk": "Clerk",
    "breley-sergeant": "Sergeant",
    "npc": "NPC",
    "npc-male": "NPC",
    "npc-female": "NPC",
    "player": "You",
}


class NarrationPanel:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.lines: list[dict] = []
        self._rendered: list[pygame.Surface] = []
        self._total_height = 0
        self._scroll_offset = 0
        self._fonts_ready = False
        self._font = None
        self._font_bold = None
        self._font_italic = None
        self._font_small = None
        self._dirty = True

    def _ensure_fonts(self):
        if not self._fonts_ready:
            self._font = pygame.font.SysFont("Consolas", FONT_SIZE)
            self._font_bold = pygame.font.SysFont("Consolas", FONT_SIZE, bold=True)
            self._font_italic = pygame.font.SysFont("Consolas", FONT_SIZE, italic=True)
            self._font_small = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)
            self._fonts_ready = True

    def add_line(self, text: str, voice: str = "narrator"):
        self.lines.append({"text": text, "voice": voice})
        self._dirty = True

    def add_lines(self, lines: list[dict]):
        for line in lines:
            self.lines.append(line)
        self._dirty = True

    def clear(self):
        self.lines.clear()
        self._rendered.clear()
        self._total_height = 0
        self._scroll_offset = 0
        self._dirty = True

    def scroll(self, dy: int):
        self._scroll_offset = max(
            0, min(self._scroll_offset + dy, max(0, self._total_height - self.rect.height + 40))
        )

    def scroll_to_bottom(self):
        self._scroll_offset = max(0, self._total_height - self.rect.height + 40)

    def _rebuild(self):
        self._ensure_fonts()
        self._rendered.clear()
        max_width = self.rect.width - PANEL_PADDING * 2 - SCROLLBAR_WIDTH - 8
        line_height = self._font.get_linesize()

        for entry in self.lines:
            voice = entry.get("voice", "narrator")
            text = entry.get("text", "")
            color = get_voice_color(voice)
            label = VOICE_LABELS.get(voice, voice)

            label_surf = self._font_small.render(f"  {label}", True, TEXT_MUTED)
            self._rendered.append(label_surf)

            if voice == "player":
                spans = parse_markdown_spans(text, color)
                wrapped = render_wrapped_line(
                    spans, self._font, self._font_bold, self._font_italic, max_width
                )
                self._rendered.extend(wrapped)
            else:
                self._render_gm_text(text, color, max_width)

            spacer = pygame.Surface((max_width, 8), pygame.SRCALPHA)
            self._rendered.append(spacer)

        self._total_height = sum(s.get_height() for s in self._rendered)
        self._dirty = False

    def _render_gm_text(self, text: str, color: tuple, max_width: int):
        """Render GM text with markdown support: bold, italic, tables, state lines."""
        import re

        raw_lines = text.split("\n")
        i = 0
        while i < len(raw_lines):
            line = raw_lines[i]

            if is_table_line(line):
                table_block = []
                while i < len(raw_lines) and (is_table_line(raw_lines[i]) or is_separator_line(raw_lines[i])):
                    table_block.append(raw_lines[i])
                    i += 1
                table_surfs = render_table(
                    table_block,
                    self._font_small, self._font_bold,
                    max_width,
                    header_color=(220, 200, 140),
                    cell_color=(200, 200, 210),
                )
                self._rendered.extend(table_surfs)
                spacer = pygame.Surface((max_width, 4), pygame.SRCALPHA)
                self._rendered.append(spacer)
                continue

            if re.match(r"^\[.+\]$", line.strip()):
                state_color = (120, 130, 150)
                state_surf = self._font_small.render(line.strip(), True, state_color)
                self._rendered.append(state_surf)
                i += 1
                continue

            stripped = line.strip()
            if not stripped:
                spacer = pygame.Surface((max_width, 4), pygame.SRCALPHA)
                self._rendered.append(spacer)
                i += 1
                continue

            if stripped.startswith("* ") or stripped.startswith("- "):
                bullet_text = stripped[2:]
                spans = parse_markdown_spans(f"  \u2022 {bullet_text}", color)
            else:
                spans = parse_markdown_spans(stripped, color)

            wrapped = render_wrapped_line(
                spans, self._font, self._font_bold, self._font_italic, max_width
            )
            self._rendered.extend(wrapped)
            i += 1

    def resize(self, rect: pygame.Rect):
        self.rect = rect
        self._dirty = True

    def draw(self, screen: pygame.Surface):
        if self._dirty:
            self._rebuild()

        pygame.draw.rect(screen, BG_PANEL, self.rect)
        pygame.draw.rect(screen, BORDER, self.rect, 1)

        clip = self.rect.inflate(-2, -2)
        screen.set_clip(clip)

        y = self.rect.top + PANEL_PADDING - self._scroll_offset
        for surf in self._rendered:
            if y + surf.get_height() > self.rect.top - 20 and y < self.rect.bottom + 20:
                screen.blit(surf, (self.rect.left + PANEL_PADDING, y))
            y += surf.get_height()

        screen.set_clip(None)

        if self._total_height > self.rect.height:
            sb_rect = pygame.Rect(
                self.rect.right - SCROLLBAR_WIDTH - 2,
                self.rect.top + 2,
                SCROLLBAR_WIDTH,
                self.rect.height - 4,
            )
            pygame.draw.rect(screen, BG_PANEL, sb_rect)
            visible_ratio = self.rect.height / self._total_height
            thumb_h = max(20, int(sb_rect.height * visible_ratio))
            scroll_ratio = self._scroll_offset / max(1, self._total_height - self.rect.height)
            thumb_y = sb_rect.top + int((sb_rect.height - thumb_h) * scroll_ratio)
            thumb_rect = pygame.Rect(sb_rect.left, thumb_y, SCROLLBAR_WIDTH, thumb_h)
            pygame.draw.rect(screen, BORDER, thumb_rect, border_radius=4)
