"""Code-owned player suggestion chips — never scrape narration."""

from __future__ import annotations

import re

from gm.creation import CREATION_STATUS_LABELS

PLAYER_SUGGESTIONS_BY_CREATION_STEP: dict[str, list[str]] = {
    "NAME": [],
    "RACE": [],
    "ROLL_STATS": [],
    "CLASS": [],
    "SKILLS": [],
    "SPELL_SCHOOLS": [],
    "SPELLS": [],
    "EQUIPMENT_GOLD": ["Yes, confirm", "I need different gear"],
    "FINALIZE": [],
    "WORLD_INTRO": [],
}

PLAYER_SUGGESTIONS_BY_AWAITING: dict[str, list[str]] = {
    "SETUP": ["new game"],
    "SESSION_ENDED": ["new game"],
    "CHARACTER_CREATION": [],
    "ROSTER_SETUP": [],
    "PLAYER_ACTIONS": [],
    "COMBAT_TURN": [],
    "DYING": [],
    "DOWNED": [],
    "BLOCKED": [],
    "HUMAN_GATE": [],
}

_UPPER_SNAKE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,}$")

_BLOCKED_ENUMS = frozenset(
    {
        *PLAYER_SUGGESTIONS_BY_AWAITING.keys(),
        *CREATION_STATUS_LABELS.values(),
        "RECEPTION_CHOICE",
    }
)


def is_blocked_chip_token(text: str) -> bool:
    """Return True if text must not appear as a player chip."""
    token = text.strip()
    if not token:
        return True
    if _UPPER_SNAKE_RE.match(token):
        return True
    if token.endswith("_INPUT") or token.endswith("_CONFIRMATION"):
        return True
    if token in _BLOCKED_ENUMS:
        return True
    return False


def filter_player_suggestions(candidates: list[str]) -> list[str]:
    """Drop blocked tokens, preserve order, cap at 4."""
    out: list[str] = []
    for item in candidates:
        if is_blocked_chip_token(item):
            continue
        out.append(item)
        if len(out) >= 4:
            break
    return out


def build_player_suggestions(
    *,
    creation_step: str,
    creation_active: bool,
    engine_awaiting: str,
    has_save: bool,
) -> list[str]:
    """Build player-facing chip labels from creation + engine state."""
    if creation_active and creation_step in PLAYER_SUGGESTIONS_BY_CREATION_STEP:
        return filter_player_suggestions(
            PLAYER_SUGGESTIONS_BY_CREATION_STEP[creation_step]
        )

    awaiting = engine_awaiting or ""

    if awaiting == "SETUP":
        if has_save:
            return filter_player_suggestions(["load game", "new game"])
        return filter_player_suggestions(["new game"])

    if awaiting == "SESSION_ENDED":
        return filter_player_suggestions(["new game"])

    if awaiting == "CHARACTER_CREATION" and not creation_active:
        return []

    if awaiting in PLAYER_SUGGESTIONS_BY_AWAITING:
        return filter_player_suggestions(PLAYER_SUGGESTIONS_BY_AWAITING[awaiting])

    return []
