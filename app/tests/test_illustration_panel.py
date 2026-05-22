from __future__ import annotations

import os
from pathlib import Path

import pygame


def _init_pygame():
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    pygame.init()
    pygame.display.set_mode((1, 1))


def test_images_chip_click_and_label_state():
    _init_pygame()
    try:
        from ui.panels.illustration import IllustrationPanel

        panel = IllustrationPanel(pygame.Rect(0, 0, 500, 260))
        panel.set_images_chip_visible(True)
        panel.set_images_enabled(True)

        assert panel.handle_images_toggle_click(panel._images_chip_rect.center) is True
        assert panel._chip_label() == "Images: On"

        panel.set_images_enabled(False)
        assert panel._chip_label() == "Images: Off"
    finally:
        pygame.quit()


def test_set_illustration_loads_surface_and_draws(tmp_path: Path):
    _init_pygame()
    try:
        from ui.panels.illustration import IllustrationPanel

        image_path = tmp_path / "sample.png"
        source = pygame.Surface((240, 120))
        source.fill((120, 80, 40))
        pygame.image.save(source, str(image_path))

        panel = IllustrationPanel(pygame.Rect(0, 0, 480, 260))
        panel.set_illustration(path=str(image_path), title="Marshal Garrick Holt", loading=False)

        assert panel._image_surface is not None
        assert panel._illustration_path == str(image_path)

        screen = pygame.Surface((480, 260))
        panel.draw(screen)
    finally:
        pygame.quit()


def test_default_title_shows_when_no_active_illustration(tmp_path: Path):
    _init_pygame()
    try:
        from ui.panels.illustration import IllustrationPanel

        image_path = tmp_path / "title.png"
        source = pygame.Surface((320, 240))
        source.fill((90, 70, 50))
        pygame.image.save(source, str(image_path))

        panel = IllustrationPanel(
            pygame.Rect(0, 0, 480, 260),
            default_image_path=image_path,
            default_title="Tomb Dust",
        )
        assert panel._showing_default is True
        assert panel._display_surface() is not None
        assert panel._illustration_title == "Tomb Dust"

        panel.clear_to_default()
        assert panel._showing_default is True
        assert panel._illustration_title == "Tomb Dust"
    finally:
        pygame.quit()


def test_entity_illustration_replaces_default(tmp_path: Path):
    _init_pygame()
    try:
        from ui.panels.illustration import IllustrationPanel

        default_path = tmp_path / "title.png"
        entity_path = tmp_path / "npc.png"
        for path, color in ((default_path, (40, 40, 80)), (entity_path, (180, 120, 60))):
            surf = pygame.Surface((200, 200))
            surf.fill(color)
            pygame.image.save(surf, str(path))

        panel = IllustrationPanel(
            pygame.Rect(0, 0, 480, 260),
            default_image_path=default_path,
        )
        panel.set_illustration(path=str(entity_path), title="Marshal Garrick Holt", loading=False)
        assert panel._showing_default is False
        assert panel._illustration_path == str(entity_path)

        panel.clear_to_default()
        assert panel._showing_default is True
        assert panel._illustration_title == "Tomb Dust"
    finally:
        pygame.quit()


def test_loading_state_uses_generating_placeholder():
    _init_pygame()
    try:
        from ui.panels.illustration import IllustrationPanel

        panel = IllustrationPanel(pygame.Rect(0, 0, 420, 240))
        panel.set_illustration(path=None, title="Isla Brack", loading=True)

        assert panel._loading is True
        assert panel._image_surface is None

        screen = pygame.Surface((420, 240))
        panel.draw(screen)
    finally:
        pygame.quit()
