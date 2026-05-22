"""Stats panel — HP bar, Fortune, Gold, Phase badge."""

from __future__ import annotations

import pygame
from ui.theme import (
    BG_SIDEBAR, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, BORDER,
    HP_GREEN, HP_RED, HP_BG, FORTUNE_GOLD, FORTUNE_EMPTY,
    PHASE_COLORS, COLOR_CLERK, PANEL_PADDING, FONT_SIZE, FONT_SIZE_SMALL, FONT_SIZE_STAT,
)


class StatsPanel:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.character_name = "—"
        self.hp_current = 0
        self.hp_max = 1
        self.mp_current = 0
        self.mp_max = 0
        self.fortune_current = 0
        self.fortune_max = 1
        self.gold = 0
        self.phase = "preparation"
        self.location_name = "—"
        self.address = "—"
        self.conditions: list[str] = []
        self.known_spells: list[str] = []
        self.creation_step_display: str | None = None
        self._font = None
        self._font_small = None
        self._font_stat = None

    def _ensure_fonts(self):
        if not self._font:
            self._font = pygame.font.SysFont("Consolas", FONT_SIZE)
            self._font_small = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)
            self._font_stat = pygame.font.SysFont("Consolas", FONT_SIZE_STAT, bold=True)

    def update_from_status(self, status: dict):
        if "creation_step_display" in status:
            display = status.get("creation_step_display")
            self.creation_step_display = display if display else None

        roster = status.get("roster", [])
        if roster:
            pc = roster[0]
            self.character_name = pc.get("display_name", "—")

            hp_str = pc.get("hp", "0/0")
            parts = hp_str.split("/")
            try:
                self.hp_current = int(parts[0])
                self.hp_max = int(parts[1]) if len(parts) > 1 else self.hp_current
            except (ValueError, IndexError):
                pass

            fortune_str = pc.get("fortune", "0/1")
            fparts = fortune_str.split("/")
            try:
                self.fortune_current = int(fparts[0])
                self.fortune_max = int(fparts[1]) if len(fparts) > 1 else self.fortune_current
            except (ValueError, IndexError):
                pass

            self.gold = pc.get("gold", 0)

            mp_str = pc.get("mp", "0/0")
            mparts = mp_str.split("/")
            try:
                self.mp_current = int(mparts[0])
                self.mp_max = int(mparts[1]) if len(mparts) > 1 else 0
            except (ValueError, IndexError):
                pass

            self.conditions = pc.get("conditions", [])
            self.known_spells = pc.get("known_spells") or []

        party = status.get("party")
        if party:
            self.phase = party.get("phase", "preparation")
            self.address = party.get("address", "—")

    def resize(self, rect: pygame.Rect):
        self.rect = rect

    def draw(self, screen: pygame.Surface):
        self._ensure_fonts()
        pygame.draw.rect(screen, BG_SIDEBAR, self.rect)
        pygame.draw.rect(screen, BORDER, self.rect, 1)

        x = self.rect.left + PANEL_PADDING
        y = self.rect.top + PANEL_PADDING

        if self.creation_step_display:
            registry_surf = self._font_small.render(
                f" Registry: {self.creation_step_display} ", True, (20, 20, 20)
            )
            registry_rect = pygame.Rect(
                x, y, registry_surf.get_width() + 8, registry_surf.get_height() + 4
            )
            pygame.draw.rect(screen, COLOR_CLERK, registry_rect, border_radius=3)
            screen.blit(registry_surf, (registry_rect.x + 4, registry_rect.y + 2))
            y += registry_rect.height + 8

        # Character name
        name_surf = self._font_stat.render(self.character_name, True, TEXT_PRIMARY)
        screen.blit(name_surf, (x, y))
        y += name_surf.get_height() + 8

        # Phase badge
        phase_color = PHASE_COLORS.get(self.phase, (100, 100, 100))
        badge_surf = self._font_small.render(f" {self.phase.upper()} ", True, (20, 20, 20))
        badge_rect = pygame.Rect(x, y, badge_surf.get_width() + 8, badge_surf.get_height() + 4)
        pygame.draw.rect(screen, phase_color, badge_rect, border_radius=3)
        screen.blit(badge_surf, (badge_rect.x + 4, badge_rect.y + 2))
        y += badge_rect.height + 12

        # HP bar
        hp_label = self._font_small.render("HP", True, TEXT_MUTED)
        screen.blit(hp_label, (x, y))
        y += hp_label.get_height() + 4

        bar_w = self.rect.width - PANEL_PADDING * 2
        bar_h = 16
        pygame.draw.rect(screen, HP_BG, (x, y, bar_w, bar_h), border_radius=3)
        if self.hp_max > 0:
            fill_ratio = max(0, min(1, self.hp_current / self.hp_max))
            fill_w = int(bar_w * fill_ratio)
            color = HP_GREEN if fill_ratio > 0.3 else HP_RED
            if fill_w > 0:
                pygame.draw.rect(screen, color, (x, y, fill_w, bar_h), border_radius=3)
        hp_text = self._font_small.render(f"{self.hp_current}/{self.hp_max}", True, TEXT_PRIMARY)
        screen.blit(hp_text, (x + bar_w // 2 - hp_text.get_width() // 2, y + 1))
        y += bar_h + 12

        # MP bar (only show if character has MP)
        if self.mp_max > 0:
            mp_label = self._font_small.render("MP", True, TEXT_MUTED)
            screen.blit(mp_label, (x, y))
            y += mp_label.get_height() + 4

            mp_bar_color = (60, 100, 180)
            pygame.draw.rect(screen, HP_BG, (x, y, bar_w, bar_h), border_radius=3)
            mp_ratio = max(0, min(1, self.mp_current / self.mp_max))
            mp_fill_w = int(bar_w * mp_ratio)
            if mp_fill_w > 0:
                pygame.draw.rect(screen, mp_bar_color, (x, y, mp_fill_w, bar_h), border_radius=3)
            mp_text = self._font_small.render(f"{self.mp_current}/{self.mp_max}", True, TEXT_PRIMARY)
            screen.blit(mp_text, (x + bar_w // 2 - mp_text.get_width() // 2, y + 1))
            y += bar_h + 12

        # Fortune
        fortune_label = self._font_small.render("Fortune", True, TEXT_MUTED)
        screen.blit(fortune_label, (x, y))
        y += fortune_label.get_height() + 4
        for i in range(self.fortune_max):
            dot_color = FORTUNE_GOLD if i < self.fortune_current else FORTUNE_EMPTY
            pygame.draw.circle(screen, dot_color, (x + 8 + i * 20, y + 6), 6)
        y += 20

        # Gold
        gold_label = self._font_small.render("Gold", True, TEXT_MUTED)
        screen.blit(gold_label, (x, y))
        y += gold_label.get_height() + 2
        gold_val = self._font.render(f"{self.gold} GP", True, FORTUNE_GOLD)
        screen.blit(gold_val, (x, y))
        y += gold_val.get_height() + 12

        # Location
        loc_label = self._font_small.render("Location", True, TEXT_MUTED)
        screen.blit(loc_label, (x, y))
        y += loc_label.get_height() + 2
        addr_surf = self._font.render(self.address, True, TEXT_SECONDARY)
        screen.blit(addr_surf, (x, y))
        y += addr_surf.get_height() + 12

        if self.known_spells:
            sp_label = self._font_small.render("Spells", True, TEXT_MUTED)
            screen.blit(sp_label, (x, y))
            y += sp_label.get_height() + 2
            for sp in self.known_spells[:4]:
                sp_surf = self._font_small.render(f"• {sp.replace('-', ' ').title()}", True, TEXT_SECONDARY)
                screen.blit(sp_surf, (x, y))
                y += sp_surf.get_height() + 1
            y += 8

        # Conditions (if any)
        if self.conditions:
            cond_label = self._font_small.render("Conditions", True, TEXT_MUTED)
            screen.blit(cond_label, (x, y))
            y += cond_label.get_height() + 4
            for cond in self.conditions[:4]:
                cond_surf = self._font_small.render(f"• {cond}", True, HP_RED)
                screen.blit(cond_surf, (x, y))
                y += cond_surf.get_height() + 2
