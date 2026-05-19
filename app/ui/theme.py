"""Visual theme constants for the Tomb Dust UI."""

import pygame

# Colors (dark fantasy palette)
BG_DARK = (18, 18, 24)
BG_PANEL = (24, 26, 32)
BG_INPUT = (32, 34, 42)
BG_SIDEBAR = (20, 22, 28)
BG_BUTTON = (44, 46, 56)
BG_BUTTON_HOVER = (58, 62, 74)

TEXT_PRIMARY = (220, 218, 210)
TEXT_SECONDARY = (160, 158, 150)
TEXT_MUTED = (100, 98, 94)
TEXT_ACCENT = (140, 180, 220)

BORDER = (48, 50, 58)
BORDER_FOCUS = (100, 140, 190)

# Voice colors
COLOR_NARRATOR = (170, 168, 160)
COLOR_NPC_DEFAULT = (200, 180, 120)
COLOR_HOLT = (210, 160, 90)
COLOR_CLERK = (140, 180, 160)
COLOR_SERGEANT = (160, 140, 190)
COLOR_PLAYER = (120, 200, 160)

VOICE_COLORS = {
    "narrator": COLOR_NARRATOR,
    "gm": COLOR_NARRATOR,
    "marshal-garrick-holt": COLOR_HOLT,
    "postern-clerk": COLOR_CLERK,
    "breley-sergeant": COLOR_SERGEANT,
    "npc": COLOR_NPC_DEFAULT,
    "player": COLOR_PLAYER,
}

# HP bar
HP_GREEN = (60, 180, 80)
HP_RED = (200, 60, 60)
HP_BG = (40, 42, 48)

# Fortune
FORTUNE_GOLD = (220, 190, 80)
FORTUNE_EMPTY = (60, 58, 54)

# Map
MAP_CELL = (40, 44, 52)
MAP_CELL_ACTIVE = (80, 140, 200)
MAP_CELL_VISITED = (50, 60, 70)
MAP_BORDER = (60, 64, 72)

# Phase badges
PHASE_COLORS = {
    "preparation": (100, 160, 200),
    "delve": (180, 100, 60),
    "combat": (200, 60, 60),
    "extraction": (140, 180, 80),
    "surface": (100, 160, 200),
}

# Sizing
FONT_SIZE = 16
FONT_SIZE_SMALL = 13
FONT_SIZE_HEADING = 20
FONT_SIZE_STAT = 24
PANEL_PADDING = 12
SCROLLBAR_WIDTH = 8


def get_voice_color(voice: str) -> tuple[int, int, int]:
    return VOICE_COLORS.get(voice, COLOR_NPC_DEFAULT)
