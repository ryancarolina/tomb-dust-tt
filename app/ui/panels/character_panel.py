"""Left character panel with Backpack and Spells tabs."""

from __future__ import annotations

import pygame

from ui.theme import (
    BG_SIDEBAR,
    BG_BUTTON,
    BG_BUTTON_HOVER,
    BORDER,
    PANEL_PADDING,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    FONT_SIZE,
    FONT_SIZE_SMALL,
)


class CharacterPanel:
    TAB_BACKPACK = "backpack"
    TAB_SPELLS = "spells"

    def __init__(self, rect: pygame.Rect, on_item_selected=None):
        self.rect = rect
        self.on_item_selected = on_item_selected
        self.active_tab = self.TAB_BACKPACK

        self._backpack_rows: list[dict] = []
        self._spell_rows: list[dict] = []
        self._backpack_empty_message = "No delver yet"
        self._spells_empty_message = "No spells known"
        self._selected_item_instance_id: str | None = None
        self._selected_spell_index: int | None = None

        self._scroll_offset = 0
        self._tab_height = 32
        self._row_height = 24
        self._tab_rects: dict[str, pygame.Rect] = {}
        self._body_rect = pygame.Rect(0, 0, 0, 0)

        self._font = None
        self._font_small = None
        self._layout()

    def _ensure_fonts(self):
        if not self._font:
            self._font = pygame.font.SysFont("Consolas", FONT_SIZE)
            self._font_small = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)

    def resize(self, rect: pygame.Rect):
        self.rect = rect
        self._scroll_offset = 0
        self._layout()

    def _layout(self):
        tab_y = self.rect.top + PANEL_PADDING
        tab_x = self.rect.left + PANEL_PADDING
        tab_w = (self.rect.width - PANEL_PADDING * 2 - 6) // 2
        self._tab_rects = {
            self.TAB_BACKPACK: pygame.Rect(tab_x, tab_y, tab_w, self._tab_height),
            self.TAB_SPELLS: pygame.Rect(tab_x + tab_w + 6, tab_y, tab_w, self._tab_height),
        }
        body_top = tab_y + self._tab_height + 8
        self._body_rect = pygame.Rect(
            self.rect.left + PANEL_PADDING,
            body_top,
            self.rect.width - PANEL_PADDING * 2,
            max(0, self.rect.bottom - PANEL_PADDING - body_top),
        )

    def _rows_for_active_tab(self) -> list[dict]:
        return self._backpack_rows if self.active_tab == self.TAB_BACKPACK else self._spell_rows

    def _active_empty_message(self) -> str:
        return (
            self._backpack_empty_message
            if self.active_tab == self.TAB_BACKPACK
            else self._spells_empty_message
        )

    def _content_height(self) -> int:
        rows = self._rows_for_active_tab()
        if not rows:
            return self._font.get_linesize() if self._font else 0
        return len(rows) * self._row_height

    def _clamp_scroll(self):
        max_scroll = max(0, self._content_height() - self._body_rect.height)
        self._scroll_offset = max(0, min(self._scroll_offset, max_scroll))

    def handle_wheel(self, wheel_y: int):
        self._layout()
        if self._body_rect.height <= 0:
            return
        self._scroll_offset += -wheel_y * 26
        self._clamp_scroll()

    def _emit_item_selected(self, item: dict[str, str] | None):
        if self.on_item_selected:
            self.on_item_selected(item)

    def handle_click(self, pos: tuple[int, int]) -> bool:
        if not self.rect.collidepoint(pos):
            return False
        self._ensure_fonts()
        self._layout()

        for tab_name, tab_rect in self._tab_rects.items():
            if tab_rect.collidepoint(pos):
                if self.active_tab != tab_name:
                    self.active_tab = tab_name
                    self._scroll_offset = 0
                return True

        if not self._body_rect.collidepoint(pos):
            return True

        rows = self._rows_for_active_tab()
        if not rows:
            if self.active_tab == self.TAB_BACKPACK and self._selected_item_instance_id is not None:
                self._selected_item_instance_id = None
                self._emit_item_selected(None)
            return True

        rel_y = pos[1] - self._body_rect.top + self._scroll_offset
        row_index = rel_y // self._row_height

        if row_index < 0 or row_index >= len(rows):
            if self.active_tab == self.TAB_BACKPACK and self._selected_item_instance_id is not None:
                self._selected_item_instance_id = None
                self._emit_item_selected(None)
            return True

        selected = rows[row_index]
        if self.active_tab == self.TAB_BACKPACK:
            next_instance_id = selected.get("instance_id")
            next_catalog_item_id = selected.get("catalog_item_id")
            if next_instance_id != self._selected_item_instance_id:
                self._selected_item_instance_id = next_instance_id
                if next_instance_id and next_catalog_item_id:
                    self._emit_item_selected(
                        {
                            "instance_id": next_instance_id,
                            "item_id": next_catalog_item_id,
                        }
                    )
                else:
                    self._emit_item_selected(None)
        else:
            self._selected_spell_index = row_index
        return True

    def update_inventory(self, payload: dict | None):
        self._layout()
        rows: list[dict] = []
        empty_message = "No delver yet"
        selected_item_still_present = False

        if payload and payload.get("ok"):
            pack = payload.get("pack") or []
            if pack:
                for idx, item in enumerate(pack):
                    instance_id = item.get("instanceId") or f"pack-{idx}"
                    catalog_item_id = item.get("itemId")
                    label = item.get("displayName") or catalog_item_id or "Unknown item"
                    equipped = bool(item.get("equipped")) or bool(item.get("equippedSlots"))
                    quantity = item.get("quantity")
                    uses = item.get("uses")
                    if quantity and int(quantity) > 1:
                        label = f"{label} x{quantity}"
                    elif uses is not None and int(uses) > 0:
                        label = f"{label} ({uses})"
                    if equipped:
                        label = f"{label} [E]"
                    rows.append(
                        {
                            "instance_id": str(instance_id),
                            "catalog_item_id": str(catalog_item_id) if catalog_item_id else None,
                            "label": str(label),
                        }
                    )
                    if self._selected_item_instance_id == str(instance_id):
                        selected_item_still_present = True
                empty_message = "Backpack empty"
            else:
                empty_message = "Backpack empty"
        elif payload and payload.get("error"):
            empty_message = "No delver yet"

        self._backpack_rows = rows
        self._backpack_empty_message = empty_message
        if self._selected_item_instance_id is not None and not selected_item_still_present:
            self._selected_item_instance_id = None
            self._emit_item_selected(None)
        self._clamp_scroll()

    def update_spells(self, payload: dict | None):
        self._layout()
        rows: list[dict] = []
        empty_message = "No spells known"

        if payload and payload.get("ok"):
            spells = payload.get("spells") or []
            if spells:
                for spell in spells:
                    label = spell.get("displayName") or spell.get("id") or "Unknown spell"
                    details: list[str] = []
                    if spell.get("tier") is not None:
                        details.append(f"T{spell['tier']}")
                    if spell.get("mpCost") is not None:
                        details.append(f"MP {spell['mpCost']}")
                    school = spell.get("school")
                    if school:
                        details.append(str(school).replace("-", " ").title())
                    if details:
                        label = f"{label} — {' | '.join(details)}"
                    rows.append({"spell_id": spell.get("id"), "label": str(label)})
            elif payload.get("spell_lines"):
                for line in payload.get("spell_lines") or []:
                    rows.append({"spell_id": None, "label": str(line)})
            if not rows:
                empty_message = "No spells known"
        self._spell_rows = rows
        self._spells_empty_message = empty_message
        if self._selected_spell_index is not None and self._selected_spell_index >= len(rows):
            self._selected_spell_index = None
        self._clamp_scroll()

    def _draw_tab(self, screen: pygame.Surface, tab_name: str, label: str, mouse_pos: tuple[int, int]):
        tab_rect = self._tab_rects[tab_name]
        active = self.active_tab == tab_name
        hovered = tab_rect.collidepoint(mouse_pos)
        bg = BG_BUTTON_HOVER if hovered or active else BG_BUTTON
        fg = TEXT_PRIMARY if active else TEXT_SECONDARY
        pygame.draw.rect(screen, bg, tab_rect, border_radius=4)
        pygame.draw.rect(screen, BORDER, tab_rect, 1, border_radius=4)
        label_surf = self._font_small.render(label, True, fg)
        screen.blit(
            label_surf,
            (
                tab_rect.centerx - label_surf.get_width() // 2,
                tab_rect.centery - label_surf.get_height() // 2,
            ),
        )

    def _truncate_label(self, text: str, max_width: int) -> str:
        if self._font.size(text)[0] <= max_width:
            return text
        trimmed = text
        while trimmed and self._font.size(trimmed + "...")[0] > max_width:
            trimmed = trimmed[:-1]
        return (trimmed + "...") if trimmed else "..."

    def draw(self, screen: pygame.Surface):
        self._ensure_fonts()
        self._layout()
        self._clamp_scroll()

        pygame.draw.rect(screen, BG_SIDEBAR, self.rect)
        pygame.draw.rect(screen, BORDER, self.rect, 1)

        mouse_pos = pygame.mouse.get_pos()
        self._draw_tab(screen, self.TAB_BACKPACK, "Backpack", mouse_pos)
        self._draw_tab(screen, self.TAB_SPELLS, "Spells", mouse_pos)

        rows = self._rows_for_active_tab()

        pygame.draw.rect(screen, BG_SIDEBAR, self._body_rect)
        pygame.draw.rect(screen, BORDER, self._body_rect, 1)
        screen.set_clip(self._body_rect)

        if rows:
            for idx, row in enumerate(rows):
                y = self._body_rect.top + idx * self._row_height - self._scroll_offset
                row_rect = pygame.Rect(
                    self._body_rect.left + 2,
                    y,
                    self._body_rect.width - 4,
                    self._row_height,
                )
                if row_rect.bottom < self._body_rect.top or row_rect.top > self._body_rect.bottom:
                    continue
                is_selected = False
                if self.active_tab == self.TAB_BACKPACK:
                    is_selected = row.get("instance_id") == self._selected_item_instance_id
                elif self._selected_spell_index is not None:
                    is_selected = idx == self._selected_spell_index
                if is_selected:
                    pygame.draw.rect(screen, BG_BUTTON_HOVER, row_rect, border_radius=3)
                label = self._truncate_label(str(row.get("label", "")), row_rect.width - 8)
                text_surf = self._font.render(label, True, TEXT_PRIMARY)
                screen.blit(
                    text_surf,
                    (row_rect.left + 4, row_rect.centery - text_surf.get_height() // 2),
                )
        else:
            empty_surf = self._font.render(self._active_empty_message(), True, TEXT_MUTED)
            screen.blit(
                empty_surf,
                (
                    self._body_rect.left + 6,
                    self._body_rect.top + 8,
                ),
            )

        screen.set_clip(None)
