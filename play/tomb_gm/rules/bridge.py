"""Import canon rules math from build/tools/rules_engine."""

from __future__ import annotations

import sys
from pathlib import Path

_BUILD_ROOT = Path(__file__).resolve().parents[3] / "build"
if str(_BUILD_ROOT) not in sys.path:
    sys.path.insert(0, str(_BUILD_ROOT))

from tools.rules_engine.core import (  # noqa: E402
    ability_modifier,
    apply_condition,
    apply_damage,
    attack_roll,
    initiative_total,
    is_critical,
    pb_for_tier,
    resolve_attack,
    roll_d20,
    roll_dice,
    saving_throw,
    skill_bonus,
)

__all__ = [
    "ability_modifier",
    "apply_condition",
    "apply_damage",
    "attack_roll",
    "initiative_total",
    "is_critical",
    "pb_for_tier",
    "resolve_attack",
    "roll_d20",
    "roll_dice",
    "saving_throw",
    "skill_bonus",
]
