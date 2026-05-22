"""Center-column IllustrationPanel with Images runtime toggle."""

from __future__ import annotations

from pathlib import Path

import pygame

from ui.theme import (
    BG_DARK,
    BG_PANEL,
    BG_BUTTON,
    BG_BUTTON_HOVER,
    BORDER,
    FONT_SIZE,
    FONT_SIZE_SMALL,
    PANEL_PADDING,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class IllustrationPanel:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self._font = None
        self._font_small = None
        self._images_chip_visible = True
        self._images_enabled = False
        self._images_chip_rect = pygame.Rect(0, 0, 0, 0)
        self._images_chip_hovered = False
        self._header_h = 0
        self._caption_h = 0
        self._image_rect = pygame.Rect(0, 0, 0, 0)
        self._caption_rect = pygame.Rect(0, 0, 0, 0)

        self._illustration_path: str | None = None
        self._illustration_title = ""
        self._loading = False
        self._image_surface: pygame.Surface | None = None

        self._layout()

    def _ensure_fonts(self) -> None:
        if not self._font:
            self._font = pygame.font.SysFont("Consolas", FONT_SIZE)
            self._font_small = pygame.font.SysFont("Consolas", FONT_SIZE_SMALL)

    def _chip_label(self) -> str:
        return "Images: On" if self._images_enabled else "Images: Off"

    def _layout(self) -> None:
        self._ensure_fonts()
        self._header_h = self._font_small.get_linesize() + 8
        self._caption_h = self._font_small.get_linesize() + 8
        top = self.rect.top + PANEL_PADDING
        left = self.rect.left + PANEL_PADDING
        width = max(1, self.rect.width - PANEL_PADDING * 2)
        max_bottom = self.rect.bottom - PANEL_PADDING
        image_top = top + self._header_h + 6
        image_bottom = max(image_top + 20, max_bottom - self._caption_h - 6)
        self._image_rect = pygame.Rect(left, image_top, width, max(20, image_bottom - image_top))
        self._caption_rect = pygame.Rect(
            left,
            min(max_bottom - self._caption_h, self._image_rect.bottom + 6),
            width,
            self._caption_h,
        )
        self._layout_images_chip()

    def _layout_images_chip(self) -> None:
        if not self._images_chip_visible:
            self._images_chip_rect = pygame.Rect(0, 0, 0, 0)
            return
        label = self._chip_label()
        text_w = self._font_small.size(label)[0]
        chip_w = text_w + 16
        chip_h = self._font_small.get_linesize() + 6
        chip_x = self.rect.right - PANEL_PADDING - chip_w
        chip_y = self.rect.top + PANEL_PADDING
        self._images_chip_rect = pygame.Rect(chip_x, chip_y, chip_w, chip_h)

    def resize(self, rect: pygame.Rect) -> None:
        self.rect = rect
        self._layout()

    def set_illustration(self, path: str | None = None, title: str = "", loading: bool = False) -> None:
        prev_loading = self._loading
        self._illustration_title = title or ""
        next_loading = bool(loading)
        next_path = str(path) if path else None
        if next_path == self._illustration_path and prev_loading == next_loading:
            return
        self._loading = next_loading
        self._illustration_path = next_path
        self._image_surface = None
        if next_path and not self._loading:
            try:
                self._image_surface = pygame.image.load(str(Path(next_path)))
            except Exception:
                self._illustration_path = None
                self._image_surface = None

    def set_images_enabled(self, enabled: bool) -> None:
        self._images_enabled = bool(enabled)
        self._layout_images_chip()

    def set_images_chip_visible(self, visible: bool) -> None:
        self._images_chip_visible = bool(visible)
        if not self._images_chip_visible:
            self._images_chip_hovered = False
        self._layout_images_chip()

    def handle_images_toggle_click(self, pos: tuple[int, int]) -> bool:
        if not self._images_chip_visible:
            return False
        return self._images_chip_rect.collidepoint(pos)

    def handle_images_hover(self, pos: tuple[int, int]) -> None:
        if not self._images_chip_visible:
            self._images_chip_hovered = False
            return
        self._images_chip_hovered = self._images_chip_rect.collidepoint(pos)

    def _draw_letterboxed_image(self, screen: pygame.Surface) -> None:
        if not self._image_surface:
            return
        src_w, src_h = self._image_surface.get_size()
        if src_w <= 0 or src_h <= 0:
            return
        scale = min(self._image_rect.width / src_w, self._image_rect.height / src_h)
        draw_w = max(1, int(src_w * scale))
        draw_h = max(1, int(src_h * scale))
        scaled = pygame.transform.smoothscale(self._image_surface, (draw_w, draw_h))
        draw_x = self._image_rect.centerx - draw_w // 2
        draw_y = self._image_rect.centery - draw_h // 2
        screen.blit(scaled, (draw_x, draw_y))

    def draw(self, screen: pygame.Surface) -> None:
        self._ensure_fonts()
        self._layout()

        pygame.draw.rect(screen, BG_PANEL, self.rect)
        pygame.draw.rect(screen, BORDER, self.rect, 1)

        title = self._font_small.render("Illustration", True, TEXT_MUTED)
        screen.blit(title, (self.rect.left + PANEL_PADDING, self.rect.top + PANEL_PADDING))

        pygame.draw.rect(screen, BG_DARK, self._image_rect)
        pygame.draw.rect(screen, BORDER, self._image_rect, 1)
        screen.set_clip(self._image_rect)
        self._draw_letterboxed_image(screen)
        screen.set_clip(None)

        if self._loading:
            loading = self._font.render("Generating…", True, TEXT_MUTED)
            screen.blit(
                loading,
                (
                    self._image_rect.centerx - loading.get_width() // 2,
                    self._image_rect.centery - loading.get_height() // 2,
                ),
            )
        elif not self._image_surface:
            empty = self._font_small.render("No illustration yet", True, TEXT_MUTED)
            screen.blit(
                empty,
                (
                    self._image_rect.centerx - empty.get_width() // 2,
                    self._image_rect.centery - empty.get_height() // 2,
                ),
            )

        pygame.draw.rect(screen, BG_PANEL, self._caption_rect)
        pygame.draw.rect(screen, BORDER, self._caption_rect, 1)
        caption_text = self._illustration_title or ("Generating…" if self._loading else "")
        if caption_text:
            cap = self._font_small.render(caption_text, True, TEXT_PRIMARY)
            max_w = max(1, self._caption_rect.width - 10)
            if cap.get_width() > max_w:
                trimmed = caption_text
                while trimmed and self._font_small.size(trimmed + "…")[0] > max_w:
                    trimmed = trimmed[:-1]
                cap = self._font_small.render((trimmed + "…") if trimmed else "…", True, TEXT_PRIMARY)
            screen.blit(
                cap,
                (
                    self._caption_rect.left + 6,
                    self._caption_rect.centery - cap.get_height() // 2,
                ),
            )

        if self._images_chip_visible and self._images_chip_rect.width:
            chip_bg = BG_BUTTON_HOVER if self._images_chip_hovered else BG_BUTTON
            pygame.draw.rect(screen, chip_bg, self._images_chip_rect, border_radius=4)
            pygame.draw.rect(screen, BORDER, self._images_chip_rect, 1, border_radius=4)
            chip_color = TEXT_SECONDARY if self._images_enabled else TEXT_MUTED
            chip = self._font_small.render(self._chip_label(), True, chip_color)
            screen.blit(
                chip,
                (
                    self._images_chip_rect.centerx - chip.get_width() // 2,
                    self._images_chip_rect.centery - chip.get_height() // 2,
                ),
            )
