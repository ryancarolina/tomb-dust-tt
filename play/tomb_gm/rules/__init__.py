"""Rules bridge to build/tools/rules_engine."""

from tomb_gm.rules.bridge import (
    ability_modifier,
    apply_condition,
    apply_damage,
    attack_roll,
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
    "is_critical",
    "pb_for_tier",
    "resolve_attack",
    "roll_d20",
    "roll_dice",
    "saving_throw",
    "skill_bonus",
]
