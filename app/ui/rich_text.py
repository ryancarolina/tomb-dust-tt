"""Rich text rendering for narration — handles word wrap, italic, bold, colors."""

from __future__ import annotations

import pygame
from typing import NamedTuple


class StyledSpan(NamedTuple):
    text: str
    color: tuple[int, int, int]
    bold: bool = False
    italic: bool = False


def render_wrapped_line(
    spans: list[StyledSpan],
    font_normal: pygame.font.Font,
    font_bold: pygame.font.Font,
    font_italic: pygame.font.Font,
    max_width: int,
) -> list[pygame.Surface]:
    """Render styled spans with word wrap. Returns list of line surfaces."""
    lines: list[pygame.Surface] = []
    line_height = font_normal.get_linesize()

    all_words: list[tuple[str, StyledSpan]] = []
    for span in spans:
        words = span.text.split(" ")
        for i, word in enumerate(words):
            token = word if i == 0 else " " + word
            all_words.append((token, span))

    current_x = 0
    current_line_surfs: list[tuple[pygame.Surface, int]] = []

    for token, span in all_words:
        font = font_bold if span.bold else (font_italic if span.italic else font_normal)
        word_surf = font.render(token, True, span.color)
        word_w = word_surf.get_width()

        if current_x + word_w > max_width and current_x > 0:
            line_surf = pygame.Surface((max_width, line_height), pygame.SRCALPHA)
            for surf, x in current_line_surfs:
                line_surf.blit(surf, (x, 0))
            lines.append(line_surf)
            current_line_surfs = []
            current_x = 0
            if token.startswith(" "):
                token = token[1:]
                word_surf = font.render(token, True, span.color)
                word_w = word_surf.get_width()

        current_line_surfs.append((word_surf, current_x))
        current_x += word_w

    if current_line_surfs:
        line_surf = pygame.Surface((max_width, line_height), pygame.SRCALPHA)
        for surf, x in current_line_surfs:
            line_surf.blit(surf, (x, 0))
        lines.append(line_surf)

    return lines
