"""Text input panel with history and suggestion buttons."""

from __future__ import annotations

import pygame
from ui.theme import (
    BG_INPUT, BG_BUTTON, BG_BUTTON_HOVER, TEXT_PRIMARY, TEXT_SECONDARY,
    TEXT_MUTED, BORDER, BORDER_FOCUS, PANEL_PADDING, FONT_SIZE, FONT_SIZE_SMALL,
)


class InputBox:
    def __init__(self, rect: pygame.Rect, on_submit=None):
        self.rect = rect
        self.on_submit = on_submit
        self.text = ""
        self.cursor_pos = 0
        self.history: list[str] = []
        self.history_index = -1
        self.focused = True
        self.suggestions: list[str] = []
        self._font = None
        self._font_small = None
        self._cursor_blink = 0
        self._cursor_visible = True

    def _ensure_fonts(self):
        if not self._font:
            self._font = pygame.font.SysFont("Consolas", FONT_SIZE)
            self._font_small = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)

    def set_suggestions(self, suggestions: list[str]):
        self.suggestions = suggestions[:4]

    def resize(self, rect: pygame.Rect):
        self.rect = rect

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and self.focused:
            if event.key == pygame.K_RETURN:
                if self.text.strip():
                    submitted = self.text.strip()
                    self.history.append(submitted)
                    self.history_index = -1
                    self.text = ""
                    self.cursor_pos = 0
                    if self.on_submit:
                        self.on_submit(submitted)
                    return submitted
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_pos > 0:
                    self.text = self.text[: self.cursor_pos - 1] + self.text[self.cursor_pos:]
                    self.cursor_pos -= 1
            elif event.key == pygame.K_DELETE:
                if self.cursor_pos < len(self.text):
                    self.text = self.text[: self.cursor_pos] + self.text[self.cursor_pos + 1:]
            elif event.key == pygame.K_LEFT:
                self.cursor_pos = max(0, self.cursor_pos - 1)
            elif event.key == pygame.K_RIGHT:
                self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
            elif event.key == pygame.K_HOME:
                self.cursor_pos = 0
            elif event.key == pygame.K_END:
                self.cursor_pos = len(self.text)
            elif event.key == pygame.K_UP:
                if self.history:
                    if self.history_index == -1:
                        self.history_index = len(self.history) - 1
                    elif self.history_index > 0:
                        self.history_index -= 1
                    self.text = self.history[self.history_index]
                    self.cursor_pos = len(self.text)
            elif event.key == pygame.K_DOWN:
                if self.history_index >= 0:
                    self.history_index += 1
                    if self.history_index >= len(self.history):
                        self.history_index = -1
                        self.text = ""
                    else:
                        self.text = self.history[self.history_index]
                    self.cursor_pos = len(self.text)
            elif event.unicode and event.unicode.isprintable():
                self.text = self.text[: self.cursor_pos] + event.unicode + self.text[self.cursor_pos:]
                self.cursor_pos += 1
        return None

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        """Check if a suggestion button was clicked."""
        btn_rects = self._get_suggestion_rects()
        for i, br in enumerate(btn_rects):
            if br.collidepoint(pos):
                text = self.suggestions[i]
                if self.on_submit:
                    self.on_submit(text)
                self.history.append(text)
                return text
        return None

    def _get_suggestion_rects(self) -> list[pygame.Rect]:
        self._ensure_fonts()
        rects = []
        x = self.rect.right - PANEL_PADDING
        y = self.rect.top + PANEL_PADDING
        for s in self.suggestions:
            w = self._font_small.size(s)[0] + 16
            h = 24
            x -= w + 6
            rects.append(pygame.Rect(x, y, w, h))
        return rects

    def draw(self, screen: pygame.Surface):
        self._ensure_fonts()

        pygame.draw.rect(screen, BG_INPUT, self.rect)
        border_color = BORDER_FOCUS if self.focused else BORDER
        pygame.draw.rect(screen, border_color, self.rect, 1)

        # Input text
        text_area = self.rect.inflate(-PANEL_PADDING * 2, -PANEL_PADDING * 2)
        prompt_surf = self._font.render("> ", True, TEXT_MUTED)
        screen.blit(prompt_surf, (text_area.left, text_area.centery - prompt_surf.get_height() // 2))

        prompt_w = prompt_surf.get_width()
        display_text = self.text if self.text else ""
        text_surf = self._font.render(display_text, True, TEXT_PRIMARY)
        screen.blit(text_surf, (text_area.left + prompt_w, text_area.centery - text_surf.get_height() // 2))

        # Cursor
        self._cursor_blink += 1
        if self._cursor_blink % 60 < 30:
            cursor_x = text_area.left + prompt_w + self._font.size(self.text[: self.cursor_pos])[0]
            cursor_y = text_area.centery - self._font.get_linesize() // 2
            pygame.draw.line(screen, TEXT_PRIMARY, (cursor_x, cursor_y), (cursor_x, cursor_y + self._font.get_linesize()), 1)

        # Placeholder
        if not self.text:
            ph = self._font.render("Type your action...", True, TEXT_MUTED)
            screen.blit(ph, (text_area.left + prompt_w, text_area.centery - ph.get_height() // 2))

        # Suggestion buttons
        mouse_pos = pygame.mouse.get_pos()
        btn_rects = self._get_suggestion_rects()
        for i, br in enumerate(btn_rects):
            hovered = br.collidepoint(mouse_pos)
            bg = BG_BUTTON_HOVER if hovered else BG_BUTTON
            pygame.draw.rect(screen, bg, br, border_radius=4)
            label = self._font_small.render(self.suggestions[i], True, TEXT_SECONDARY)
            screen.blit(label, (br.centerx - label.get_width() // 2, br.centery - label.get_height() // 2))
