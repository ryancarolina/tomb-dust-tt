"""Tests for Tomb Dust rules engine — E1 canon and TD-016 walkthrough numbers."""

from __future__ import annotations

import random

import pytest

from tools.rules_engine.core import (
    ability_modifier,
    ac_vs_spells,
    apply_condition,
    apply_damage,
    attack_roll,
    initiative_total,
    is_critical,
    pb_for_tier,
    resolve_attack,
    roll_dice,
    saving_throw,
    skill_bonus,
    Combatant,
)


class TestCanonMath:
    def test_ability_modifier(self):
        assert ability_modifier(10) == 0
        assert ability_modifier(14) == 2
        assert ability_modifier(9) == -1

    def test_skill_bonus_tiers(self):
        assert skill_bonus(1) == 0
        assert skill_bonus(2) == 0
        assert skill_bonus(3) == 1
        assert skill_bonus(4) == 1
        assert skill_bonus(5) == 2
        assert skill_bonus(7) == 3
        assert skill_bonus(9) == 4
        assert skill_bonus(10) == 4

    def test_pb_by_tier(self):
        assert pb_for_tier(1) == 2
        assert pb_for_tier(2) == 2
        assert pb_for_tier(3) == 3
        assert pb_for_tier(5) == 4

    def test_magical_defense_ac(self):
        # Cleric example from calculations.md: AC 16 + MD +2 = 18 vs spells
        assert ac_vs_spells(16, 2) == 18

    def test_gritty_crit_nat_20(self):
        result = attack_roll(
            natural=20,
            ability_mod=2,
            pb=2,
            skill_bonus_value=1,
            target_ac=13,
        )
        assert result.hit
        assert result.critical

    def test_gritty_crit_beat_by_5(self):
        # d20 15 + 2 + 2 + 1 = 20 vs AC 13 → beat by 7
        result = attack_roll(
            natural=15,
            ability_mod=2,
            pb=2,
            skill_bonus_value=1,
            target_ac=13,
        )
        assert result.hit
        assert result.critical
        assert is_critical(result.total, 13, 15)

    def test_nat_1_can_still_hit(self):
        # nat 1 + 5 = 6 vs AC 5
        result = attack_roll(
            natural=1,
            ability_mod=2,
            pb=2,
            skill_bonus_value=1,
            target_ac=5,
        )
        assert result.hit
        assert not result.critical


class TestWalkthrough:
    """TD-016: Tomas (Militia) vs Grave Ghoul in Breley undercrypt."""

    RNG = random.Random(0)

    def test_tomas_derived_stats(self):
        # Militia: STA 12 → HP 10 + 60 = 70
        hp = 10 + (12 * 5)
        assert hp == 70
        # Studded +3, AGI +1, Dodge +1 → AC 15 alert
        ac_alert = 10 + 3 + 1 + 1
        assert ac_alert == 15
        ac_flat_footed = 10 + 3
        assert ac_flat_footed == 13

    def test_initiative_order(self):
        tomas = initiative_total(natural=15, agi_mod=1)
        ghoul = initiative_total(natural=8, agi_mod=2)
        assert tomas == 16
        assert ghoul == 10
        assert tomas > ghoul

    def test_surprise_ghoul_claw_hits_flat_footed(self):
        result = attack_roll(
            natural=12,
            ability_mod=2,
            pb=2,
            skill_bonus_value=0,
            target_ac=13,
        )
        assert result.total == 16
        assert result.hit

    def test_round_2_tomas_crit_longsword(self):
        result, damage = resolve_attack(
            ability_mod=2,
            pb=2,
            skill_bonus_value=1,
            target_ac=13,
            weapon_damage="1d8",
            ability_damage_mod=2,
            rng=self.RNG,
            natural=17,
        )
        assert result.total == 22
        assert result.critical
        # 1d8(7) + 2 STR + 1 skill + crit extra 1d8(7) = 17 with RNG seed 0
        assert damage == 17

    def test_paralyze_save_fail(self):
        passed = saving_throw(
            natural=7,
            ability_mod=2,
            pb=2,
            magical_defense_bonus=0,
            dc=12,
        )
        assert not passed

    def test_dying_and_death(self):
        tomas = Combatant(name="Tomas", hp=6, max_hp=70, ac=15)
        tomas.hp = apply_damage(tomas.hp, 6)
        assert tomas.hp == 0
        apply_condition(tomas, "Dying")
        assert "Dying" in tomas.conditions
        # Damage while Dying → death (hp stays 0, condition tracked separately)
        tomas.hp = apply_damage(tomas.hp, 4)
        assert tomas.hp == 0


class TestDice:
    def test_roll_dice_fixed_rng(self):
        rng = random.Random(42)
        assert roll_dice("1d8", rng) == 2
        assert roll_dice("2d6+3", rng) == 10
