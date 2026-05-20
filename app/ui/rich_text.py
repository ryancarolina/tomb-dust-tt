"""Rich text rendering for narration — handles word wrap, italic, bold, colors, tables."""

from __future__ import annotations

import re
import pygame
from typing import NamedTuple


class StyledSpan(NamedTuple):
    text: str
    color: tuple[int, int, int]
    bold: bool = False
    italic: bool = False


def parse_markdown_spans(text: str, base_color: tuple[int, int, int]) -> list[StyledSpan]:
    """Parse inline markdown (bold, italic) into styled spans."""
    spans: list[StyledSpan] = []
    pattern = re.compile(r"\*\*(.+?)\*\*|\*(.+?)\*|_(.+?)_")
    last_end = 0

    for m in pattern.finditer(text):
        if m.start() > last_end:
            spans.append(StyledSpan(text[last_end:m.start()], base_color))
        if m.group(1):
            spans.append(StyledSpan(m.group(1), base_color, bold=True))
        elif m.group(2):
            spans.append(StyledSpan(m.group(2), base_color, italic=True))
        elif m.group(3):
            spans.append(StyledSpan(m.group(3), base_color, italic=True))
        last_end = m.end()

    if last_end < len(text):
        spans.append(StyledSpan(text[last_end:], base_color))

    return spans if spans else [StyledSpan(text, base_color)]


def is_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and stripped.count("|") >= 3


def is_separator_line(line: str) -> bool:
    stripped = line.strip()
    return bool(re.match(r"^\|[\s:|-]+\|$", stripped))


def _truncate_to_width(text: str, font: pygame.font.Font, max_px: int) -> str:
    """Truncate text to fit within max_px pixels, adding ellipsis if needed."""
    if font.size(text)[0] <= max_px:
        return text
    for end in range(len(text), 0, -1):
        candidate = text[:end] + ".."
        if font.size(candidate)[0] <= max_px:
            return candidate
    return text[:3] + ".."


def render_table(
    table_lines: list[str],
    font: pygame.font.Font,
    font_bold: pygame.font.Font,
    max_width: int,
    header_color: tuple[int, int, int],
    cell_color: tuple[int, int, int],
    bg_color: tuple[int, int, int] = (30, 32, 38),
) -> list[pygame.Surface]:
    """Render a markdown table as formatted surfaces."""
    rows: list[list[str]] = []
    for line in table_lines:
        if is_separator_line(line):
            continue
        cells = [c.strip().strip("*") for c in line.strip().strip("|").split("|")]
        rows.append(cells)

    if not rows:
        return []

    line_height = font.get_linesize() + 4
    col_count = max(len(r) for r in rows)

    # Calculate widths from DATA rows (skip header for sizing to avoid bloat from long headers)
    col_widths = [0] * col_count
    data_rows = rows[1:] if len(rows) > 1 else rows
    for row in data_rows:
        for i, cell in enumerate(row):
            if i < col_count:
                w = font.size(cell)[0] + 16
                col_widths[i] = max(col_widths[i], w)

    # Ensure minimum width from header (but capped)
    if rows:
        for i, cell in enumerate(rows[0]):
            if i < col_count:
                header_w = min(font_bold.size(cell)[0] + 16, 140)
                col_widths[i] = max(col_widths[i], header_w)

    total_w = sum(col_widths)
    if total_w > max_width:
        scale = max_width / total_w
        col_widths = [max(40, int(w * scale)) for w in col_widths]
        total_w = sum(col_widths)

    surfaces: list[pygame.Surface] = []
    for row_idx, row in enumerate(rows):
        is_header = row_idx == 0
        surf = pygame.Surface((max_width, line_height), pygame.SRCALPHA)
        if is_header:
            surf.fill((40, 44, 52))
        elif row_idx % 2 == 0:
            surf.fill((28, 30, 36))

        x = 4
        for col_idx, cell in enumerate(row):
            if col_idx >= col_count:
                break
            use_font = font_bold if is_header else font
            color = header_color if is_header else cell_color
            available_px = (col_widths[col_idx] - 12) if col_idx < len(col_widths) else 48
            display_text = _truncate_to_width(cell, use_font, available_px)
            cell_surf = use_font.render(display_text, True, color)
            surf.blit(cell_surf, (x + 4, 2))
            x += col_widths[col_idx] if col_idx < len(col_widths) else 60

        surfaces.append(surf)

    return surfaces


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
