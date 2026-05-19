"""AV-GRID map — node-based view of known locations with connections."""

from __future__ import annotations

import json
import pygame
from pathlib import Path
from ui.theme import (
    BG_SIDEBAR, TEXT_MUTED, TEXT_SECONDARY, TEXT_PRIMARY, BORDER,
    MAP_CELL, MAP_CELL_ACTIVE, MAP_CELL_VISITED, MAP_BORDER,
    PANEL_PADDING, FONT_SIZE_SMALL,
)


class MapView:
    def __init__(self, rect: pygame.Rect, content_root: Path | None = None):
        self.rect = rect
        self.current_address = "32-C"
        self.visited: set[str] = set()
        self._addresses: dict[str, dict] = {}
        self._surface_cells: list[dict] = []
        self._font = None
        self._node_rects: list[tuple[pygame.Rect, str, str]] = []
        self._hover_addr: str | None = None
        if content_root:
            self._load_grid(content_root)

    def _load_grid(self, content_root: Path):
        grid_path = content_root / "data" / "av-grid" / "av-grid.json"
        if grid_path.is_file():
            data = json.loads(grid_path.read_text(encoding="utf-8"))
            self._addresses = data.get("addresses", {})
            self._surface_cells = [
                v for v in self._addresses.values()
                if isinstance(v, dict) and not v.get("layerStack")
            ]
            self._surface_cells.sort(key=lambda c: (c.get("column", 0), c.get("row", "A")))

    def _ensure_fonts(self):
        if not self._font:
            self._font = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)

    def update_position(self, address: str):
        if address:
            self.visited.add(self.current_address)
            self.current_address = address

    def resize(self, rect: pygame.Rect):
        self.rect = rect

    def handle_hover(self, pos: tuple[int, int]):
        self._hover_addr = None
        for node_rect, addr, _ in self._node_rects:
            if node_rect.collidepoint(pos):
                self._hover_addr = addr
                break

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        for node_rect, addr, _ in self._node_rects:
            if node_rect.collidepoint(pos) and addr != self.current_address:
                return addr
        return None

    def draw(self, screen: pygame.Surface):
        self._ensure_fonts()
        pygame.draw.rect(screen, BG_SIDEBAR, self.rect)
        pygame.draw.rect(screen, BORDER, self.rect, 1)

        x = self.rect.left + PANEL_PADDING
        y = self.rect.top + PANEL_PADDING

        label = self._font.render("WORLD MAP", True, TEXT_MUTED)
        screen.blit(label, (x, y))
        y += label.get_height() + 6

        self._node_rects.clear()

        current_data = self._addresses.get(self.current_address, {})
        children = current_data.get("childAddresses", [])

        nodes_to_show = self._get_nearby_nodes()

        available_h = self.rect.bottom - y - PANEL_PADDING
        node_h = 22
        max_visible = available_h // node_h

        for i, node in enumerate(nodes_to_show[:max_visible]):
            addr = node["id"]
            name = node.get("displayName", addr)
            is_current = addr == self.current_address
            is_child = addr in children
            is_hover = addr == self._hover_addr
            is_visited = addr in self.visited

            node_rect = pygame.Rect(x, y + i * node_h, self.rect.width - PANEL_PADDING * 2, node_h - 2)
            self._node_rects.append((node_rect, addr, name))

            if is_current:
                bg_color = MAP_CELL_ACTIVE
                text_color = TEXT_PRIMARY
            elif is_hover:
                bg_color = (60, 80, 100)
                text_color = TEXT_PRIMARY
            elif is_visited:
                bg_color = MAP_CELL_VISITED
                text_color = TEXT_SECONDARY
            else:
                bg_color = MAP_CELL
                text_color = TEXT_SECONDARY

            pygame.draw.rect(screen, bg_color, node_rect, border_radius=3)

            prefix = ""
            if is_current:
                prefix = "> "
            elif is_child:
                prefix = "  v "
            elif is_visited:
                prefix = "  . "
            else:
                prefix = "  - "

            display = f"{prefix}{name}"
            addr_tag = f" [{addr}]"
            name_w = self._font.size(display)[0]
            if name_w + self._font.size(addr_tag)[0] < node_rect.width - 4:
                display += addr_tag

            text_surf = self._font.render(display, True, text_color)
            screen.blit(text_surf, (node_rect.left + 4, node_rect.top + 2))

    def _get_nearby_nodes(self) -> list[dict]:
        """Get current location + its children + adjacent surface cells."""
        current_data = self._addresses.get(self.current_address)
        if not current_data or not isinstance(current_data, dict):
            return [{"id": self.current_address, "displayName": self.current_address}]

        result = [current_data]
        children = current_data.get("childAddresses", [])
        for child_addr in children:
            child = self._addresses.get(child_addr)
            if child and isinstance(child, dict):
                result.append(child)

        current_col = current_data.get("column", 0)
        current_row = current_data.get("row", "A")

        for cell in self._surface_cells:
            addr = cell.get("id", "")
            if addr == self.current_address:
                continue
            col = cell.get("column", 0)
            row = cell.get("row", "A")
            if abs(col - current_col) <= 2 and abs(ord(row) - ord(current_row)) <= 2:
                result.append(cell)

        seen = set()
        deduped = []
        for node in result:
            nid = node.get("id", "")
            if nid not in seen:
                seen.add(nid)
                deduped.append(node)
        return deduped

    def _parse_address(self, address: str) -> tuple[int, str]:
        parts = address.split("-")
        try:
            col = int(parts[0])
            row = parts[1] if len(parts) > 1 else "A"
            return col, row
        except (ValueError, IndexError):
            return 32, "C"
