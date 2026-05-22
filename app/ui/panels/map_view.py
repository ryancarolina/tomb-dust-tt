"""AV-GRID map — top-down 3x3 grid showing immediate surroundings."""

from __future__ import annotations

import json
import pygame
from pathlib import Path
from ui.theme import (
    BG_SIDEBAR, TEXT_MUTED, TEXT_SECONDARY, TEXT_PRIMARY, BORDER,
    PANEL_PADDING, FONT_SIZE_SMALL,
)

TERRAIN_COLORS = {
    "forest": (34, 80, 34),
    "marsh": (50, 60, 40),
    "farmland": (90, 100, 50),
    "road": (100, 90, 70),
    "cliff": (90, 85, 80),
    "tundra": (180, 200, 220),
    "coast": (50, 90, 130),
    "ruins": (70, 50, 50),
    "settlement": (110, 90, 60),
    "plains": (80, 100, 50),
    "hills": (70, 85, 55),
    "mountains": (100, 100, 110),
    "cavern-mouth": (40, 35, 45),
    "lake": (40, 70, 120),
    "river": (50, 80, 130),
    "desert": (140, 120, 70),
    "steppe": (110, 100, 60),
}

DANGER_BORDER_COLORS = {
    None: (60, 65, 70),
    "hazard": (60, 100, 60),
    "skirmisher": (130, 130, 50),
    "elite": (160, 60, 40),
    "boss": (130, 30, 30),
}

FOG_COLOR = (30, 32, 38)
PLAYER_COLOR = (220, 200, 80)
COMPASS_COLOR = (140, 150, 160)


class MapView:
    def __init__(self, rect: pygame.Rect, content_root: Path | None = None):
        self.rect = rect
        self.current_address = "32-C"
        self.visited: set[str] = set()
        self.scene_index = 1
        self.scene_max = 3
        self.heading = "N"
        self.mode = "surface"
        self.dungeon_room: str | None = None
        self.dungeon_exits: list[str] = []
        self.travel_blocked = False
        self.travel_blocked_hint = "Finish Registry intake first"
        self._hovering = False
        self._addresses: dict[str, dict] = {}
        self._font = None
        self._font_small = None
        if content_root:
            self._load_grid(content_root)

    def set_travel_blocked(self, blocked: bool, hint: str | None = None):
        self.travel_blocked = blocked
        if hint is not None:
            self.travel_blocked_hint = hint

    def _load_grid(self, content_root: Path):
        grid_path = content_root / "data" / "av-grid" / "av-grid.json"
        if grid_path.is_file():
            data = json.loads(grid_path.read_text(encoding="utf-8"))
            self._addresses = data.get("addresses", {})

    def _ensure_fonts(self):
        if not self._font:
            self._font = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)
            self._font_small = pygame.font.SysFont("Consolas", max(9, FONT_SIZE_SMALL - 2))

    def update_position(self, address: str, scene_index: int = 1, scene_max: int = 3,
                        heading: str = "N", mode: str = "surface",
                        dungeon_room: str | None = None, dungeon_exits: list[str] | None = None):
        if address:
            self.visited.add(self.current_address)
            self.current_address = address
            self.visited.add(address)
        self.scene_index = scene_index
        self.scene_max = scene_max
        self.heading = heading
        self.mode = mode
        self.dungeon_room = dungeon_room
        self.dungeon_exits = dungeon_exits or []

    def resize(self, rect: pygame.Rect):
        self.rect = rect

    def handle_hover(self, pos: tuple[int, int]):
        self._hovering = self.rect.collidepoint(pos)

    def handle_click(self, pos: tuple[int, int]) -> str | None:
        if self.travel_blocked:
            return None
        return None

    def draw(self, screen: pygame.Surface):
        self._ensure_fonts()
        pygame.draw.rect(screen, BG_SIDEBAR, self.rect)
        pygame.draw.rect(screen, BORDER, self.rect, 1)

        if self.mode == "dungeon":
            self._draw_dungeon(screen)
        else:
            self._draw_surface(screen)

    def _draw_surface(self, screen: pygame.Surface):
        """Draw 3x3 top-down grid centered on current cell."""
        x = self.rect.left + PANEL_PADDING
        y = self.rect.top + PANEL_PADDING

        # Title
        title = self._font.render("MAP", True, TEXT_MUTED)
        screen.blit(title, (x, y))
        y += title.get_height() + 4

        # Get current cell data
        current = self._addresses.get(self.current_address, {})
        col = current.get("column", 32)
        row = current.get("row", "C")
        row_ord = ord(row)

        # Compute available space for the 3x3 grid
        available_w = self.rect.width - PANEL_PADDING * 2
        available_h = self.rect.height - (y - self.rect.top) - PANEL_PADDING - 60

        cell_size = min(available_w // 3, available_h // 3, 60)
        grid_w = cell_size * 3
        grid_h = cell_size * 3
        grid_x = x + (available_w - grid_w) // 2
        grid_y = y + 14

        # Compass labels
        compass_n = self._font_small.render("N", True, COMPASS_COLOR)
        compass_s = self._font_small.render("S", True, COMPASS_COLOR)
        compass_e = self._font_small.render("E", True, COMPASS_COLOR)
        compass_w = self._font_small.render("W", True, COMPASS_COLOR)

        screen.blit(compass_n, (grid_x + grid_w // 2 - compass_n.get_width() // 2, grid_y - 12))
        screen.blit(compass_s, (grid_x + grid_w // 2 - compass_s.get_width() // 2, grid_y + grid_h + 2))
        screen.blit(compass_w, (grid_x - 12, grid_y + grid_h // 2 - compass_w.get_height() // 2))
        screen.blit(compass_e, (grid_x + grid_w + 3, grid_y + grid_h // 2 - compass_e.get_height() // 2))

        # Draw 3x3 grid (row A = north, so row_ord-1 = north)
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                cell_col = col + dx
                cell_row_ord = row_ord + dy
                if cell_row_ord < ord("A") or cell_row_ord > ord("Z"):
                    continue
                if cell_col < 1 or cell_col > 60:
                    continue

                cell_id = f"{cell_col}-{chr(cell_row_ord)}"
                cell_data = self._addresses.get(cell_id)

                gx = grid_x + (dx + 1) * cell_size
                gy = grid_y + (dy + 1) * cell_size
                cell_rect = pygame.Rect(gx, gy, cell_size - 2, cell_size - 2)

                is_current = (dx == 0 and dy == 0)
                is_visited = cell_id in self.visited

                if cell_data and (is_visited or is_current):
                    terrain = cell_data.get("terrain", "plains")
                    bg = TERRAIN_COLORS.get(terrain, (50, 55, 60))
                    danger = cell_data.get("dangerRating")
                    border_color = DANGER_BORDER_COLORS.get(danger, (60, 65, 70))
                else:
                    bg = FOG_COLOR
                    border_color = (45, 48, 52)

                pygame.draw.rect(screen, bg, cell_rect)
                border_w = 2 if is_current else 1
                pygame.draw.rect(screen, border_color, cell_rect, border_w)

                if is_current:
                    # Draw player marker
                    center = cell_rect.center
                    pygame.draw.circle(screen, PLAYER_COLOR, center, cell_size // 6)
                    # Heading arrow
                    arrow_len = cell_size // 4
                    arrow_offsets = {"N": (0, -arrow_len), "S": (0, arrow_len),
                                     "E": (arrow_len, 0), "W": (-arrow_len, 0)}
                    off = arrow_offsets.get(self.heading, (0, -arrow_len))
                    pygame.draw.line(screen, PLAYER_COLOR, center,
                                     (center[0] + off[0], center[1] + off[1]), 2)
                elif is_visited and cell_data:
                    # Small visited dot
                    pygame.draw.circle(screen, (100, 110, 90), cell_rect.center, 3)

                # Settlement/landmark indicator
                if cell_data and cell_data.get("population") in ("town", "fortress", "city"):
                    # Small square indicator
                    ind_size = 5
                    ind_rect = pygame.Rect(cell_rect.right - ind_size - 3, cell_rect.top + 3, ind_size, ind_size)
                    pygame.draw.rect(screen, (180, 160, 80), ind_rect)

        # Location name and scene progress below grid
        info_y = grid_y + grid_h + 16
        display_name = current.get("displayName", self.current_address)
        name_surf = self._font.render(display_name, True, TEXT_PRIMARY)
        screen.blit(name_surf, (x, info_y))
        info_y += name_surf.get_height() + 3

        # Scene progress dots
        scene_text = f"Scene {self.scene_index}/{self.scene_max}"
        dots = ""
        for i in range(self.scene_max):
            dots += "●" if i < self.scene_index else "○"
        scene_surf = self._font_small.render(f"{scene_text}  {dots}  [{self.heading}]", True, TEXT_SECONDARY)
        screen.blit(scene_surf, (x, info_y))

        if self.travel_blocked:
            grid_rect = pygame.Rect(grid_x, grid_y, grid_w, grid_h)
            self._draw_travel_block_overlay(screen, grid_rect, x, grid_y + grid_h + 16)

    def _draw_dungeon(self, screen: pygame.Surface):
        """Draw dungeon room view with exits."""
        x = self.rect.left + PANEL_PADDING
        y = self.rect.top + PANEL_PADDING

        title = self._font.render("DUNGEON", True, TEXT_MUTED)
        screen.blit(title, (x, y))
        y += title.get_height() + 8

        # Current room
        room_name = self.dungeon_room or "Unknown Room"
        room_surf = self._font.render(room_name, True, TEXT_PRIMARY)
        screen.blit(room_surf, (x, y))
        y += room_surf.get_height() + 6

        # Room box
        box_size = min(self.rect.width - PANEL_PADDING * 2, 80)
        box_x = x + (self.rect.width - PANEL_PADDING * 2 - box_size) // 2
        box_rect = pygame.Rect(box_x, y, box_size, box_size)
        pygame.draw.rect(screen, (50, 45, 55), box_rect)
        pygame.draw.rect(screen, (100, 80, 60), box_rect, 2)

        # Player dot in center
        pygame.draw.circle(screen, PLAYER_COLOR, box_rect.center, 5)
        y += box_size + 8

        # Exits
        if self.dungeon_exits:
            exits_label = self._font_small.render("Exits:", True, TEXT_MUTED)
            screen.blit(exits_label, (x, y))
            y += exits_label.get_height() + 3
            for exit_name in self.dungeon_exits[:6]:
                exit_surf = self._font_small.render(f"  > {exit_name}", True, TEXT_SECONDARY)
                screen.blit(exit_surf, (x, y))
                y += exit_surf.get_height() + 2

        # Address
        y += 4
        addr_surf = self._font_small.render(f"[{self.current_address}]", True, TEXT_MUTED)
        screen.blit(addr_surf, (x, y))

        if self.travel_blocked:
            content_rect = pygame.Rect(
                self.rect.left + PANEL_PADDING,
                self.rect.top + PANEL_PADDING + 20,
                self.rect.width - PANEL_PADDING * 2,
                y - (self.rect.top + PANEL_PADDING + 20),
            )
            self._draw_travel_block_overlay(screen, content_rect, x, y + 4)

    def _draw_travel_block_overlay(
        self,
        screen: pygame.Surface,
        overlay_rect: pygame.Rect,
        hint_x: int,
        hint_y: int,
    ):
        overlay = pygame.Surface((overlay_rect.width, overlay_rect.height), pygame.SRCALPHA)
        muted = TEXT_MUTED
        overlay.fill((muted[0], muted[1], muted[2], 102))
        screen.blit(overlay, overlay_rect.topleft)
        if self.travel_blocked and self._hovering:
            hint_surf = self._font_small.render(self.travel_blocked_hint, True, TEXT_MUTED)
            screen.blit(hint_surf, (hint_x, hint_y))

    def _parse_address(self, address: str) -> tuple[int, str]:
        parts = address.split("-")
        try:
            col = int(parts[0])
            row = parts[1] if len(parts) > 1 else "A"
            return col, row
        except (ValueError, IndexError):
            return 32, "C"
