from __future__ import annotations

import argparse

from tomb_gm.cli.cmd_core import log_event
from tomb_gm.cli.context import CommandContext
from tomb_gm.domain.combat_sheet import (
    attack_modifiers_from_sheet,
    find_combatant,
    load_character_sheet,
    target_ac_from_monster,
)
from tomb_gm.services.content import ContentService
from tomb_gm.services.simulation.combat import advance_turn, apply_damage_to_combatant
from tomb_gm.services.simulation.rolls import perform_attack_roll


def handle_turn(ctx: CommandContext, session_id: str) -> dict:
    return advance_turn(ctx.conn, session_id)


def handle_attack(
    ctx: CommandContext,
    session_id: str,
    args: argparse.Namespace,
) -> dict:
    sheet = load_character_sheet(ctx.conn, args.campaign, args.character_id)
    mods = attack_modifiers_from_sheet(sheet, weapon_id=args.weapon)
    combatant = find_combatant(ctx.conn, session_id, args.target_id)
    if not combatant:
        return {"ok": False, "error": f"target not in combat: {args.target_id}"}
    content = ContentService(ctx.config.content_root)
    ac = target_ac_from_monster(content, combatant)
    result = perform_attack_roll(
        ctx.conn,
        log_event,
        session_id=session_id,
        ability_mod=mods["ability_mod"],
        pb=mods["pb"],
        skill_level=mods["skill_level"],
        target_ac=ac,
        weapon_damage=mods["weapon_damage"],
        ability_damage_mod=mods["ability_damage_mod"],
        reason=f"{args.character_id} vs {args.target_id}",
        seed=args.seed,
    )
    if result.get("hit"):
        dmg_total = int(result.get("damage") or 0)
        if dmg_total:
            apply_damage_to_combatant(
                ctx.conn,
                session_id,
                args.target_id,
                dmg_total,
                campaign_slug=args.campaign,
            )
    result["attacker"] = args.character_id
    result["target"] = args.target_id
    return result
