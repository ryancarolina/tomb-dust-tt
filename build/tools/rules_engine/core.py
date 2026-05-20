"""Core d20 resolution helpers aligned with systems/core and systems/combat."""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Iterable

DICE_RE = re.compile(r"^(\d+)d(\d+)(?:\s*([+\-])\s*(\d+))?$")


def ability_modifier(score: int) -> int:
    return (score - 10) // 2


def skill_bonus(level: int) -> int:
    if level <= 2:
        return 0
    if level <= 4:
        return 1
    if level <= 6:
        return 2
    if level <= 8:
        return 3
    return 4


def pb_for_tier(class_tier: int) -> int:
    if class_tier <= 2:
        return 2
    if class_tier <= 4:
        return 3
    return 4


def roll_d20(rng: random.Random | None = None) -> int:
    rng = rng or random.Random()
    return rng.randint(1, 20)


def roll_dice(notation: str, rng: random.Random | None = None) -> int:
    rng = rng or random.Random()
    match = DICE_RE.match(notation.strip())
    if not match:
        raise ValueError(f"invalid dice notation: {notation!r}")
    count, sides, sign, flat = match.groups()
    total = sum(rng.randint(1, int(sides)) for _ in range(int(count)))
    if sign and flat:
        total += int(flat) if sign == "+" else -int(flat)
    return total


@dataclass
class AttackResult:
    natural: int
    total: int
    hit: bool
    critical: bool


def attack_roll(
    *,
    natural: int,
    ability_mod: int,
    pb: int,
    skill_bonus_value: int,
    target_ac: int,
    circumstance: int = 0,
) -> AttackResult:
    total = natural + ability_mod + pb + skill_bonus_value + circumstance
    hit = total >= target_ac
    critical = hit and (natural == 20 or total >= target_ac + 5)
    return AttackResult(natural=natural, total=total, hit=hit, critical=critical)


def is_critical(attack_total: int, target_ac: int, natural: int) -> bool:
    return attack_total >= target_ac and (natural == 20 or attack_total >= target_ac + 5)


def resolve_attack(
    *,
    ability_mod: int,
    pb: int,
    skill_bonus_value: int,
    target_ac: int,
    weapon_damage: str,
    ability_damage_mod: int,
    rng: random.Random | None = None,
    natural: int | None = None,
) -> tuple[AttackResult, int]:
    rng = rng or random.Random()
    nat = natural if natural is not None else roll_d20(rng)
    result = attack_roll(
        natural=nat,
        ability_mod=ability_mod,
        pb=pb,
        skill_bonus_value=skill_bonus_value,
        target_ac=target_ac,
    )
    if not result.hit:
        return result, 0
    damage = roll_dice(weapon_damage, rng) + ability_damage_mod + skill_bonus_value
    if result.critical:
        damage += roll_dice(weapon_damage, rng)
    return result, damage


def saving_throw(
    *,
    natural: int,
    ability_mod: int,
    pb: int,
    magical_defense_bonus: int,
    dc: int,
) -> bool:
    total = natural + ability_mod + pb + magical_defense_bonus
    return total >= dc


def apply_damage(current_hp: int, amount: int) -> int:
    return max(0, current_hp - max(0, amount))


@dataclass
class Combatant:
    name: str
    hp: int
    max_hp: int
    ac: int
    conditions: set[str] = field(default_factory=set)


def apply_condition(combatant: Combatant, condition: str) -> None:
    combatant.conditions.add(condition)


def ac_vs_spells(base_ac: int, magical_defense_bonus: int) -> int:
    return base_ac + magical_defense_bonus


def spell_save_dc(
    *,
    casting_mod: int,
    pb: int,
    spellcasting_bonus: int,
    focus_bonus: int = 0,
) -> int:
    return 8 + casting_mod + pb + spellcasting_bonus + focus_bonus


def spell_attack_total_bonus(
    *,
    casting_mod: int,
    pb: int,
    spellcasting_bonus: int,
    focus_bonus: int = 0,
) -> int:
    return casting_mod + pb + spellcasting_bonus + focus_bonus


def initiative_total(*, natural: int, agi_mod: int, bonus: int = 0) -> int:
    return natural + agi_mod + bonus


def sum_damage(dice_rolls: Iterable[int], flat: int = 0) -> int:
    return sum(dice_rolls) + flat
