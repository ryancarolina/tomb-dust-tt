from __future__ import annotations

import argparse
import json

from tomb_gm.cli.cmd_core import log_event
from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.services.simulation.rolls import perform_attack_roll, perform_d20_roll


def register(sub: argparse._SubParsersAction) -> None:
    roll = sub.add_parser("roll", help="Dice and checks")
    roll_sub = roll.add_subparsers(dest="roll_cmd", required=True)

    d20 = roll_sub.add_parser("d20", help="d20 test vs DC")
    d20.add_argument("--mod", type=int, default=0)
    d20.add_argument("--dc", type=int, default=None)
    d20.add_argument("--reason", default="")
    d20.add_argument("--character", dest="character_id", default=None)
    d20.add_argument("--advantage", action="store_true")
    d20.add_argument("--disadvantage", action="store_true")
    d20.set_defaults(handler=handle_d20)

    save = roll_sub.add_parser("save", help="Saving throw vs DC")
    save.add_argument("--mod", type=int, default=0)
    save.add_argument("--dc", type=int, required=True)
    save.add_argument("--reason", default="")
    save.set_defaults(handler=handle_save)

    init = roll_sub.add_parser("initiative", help="Roll initiative for active combat")
    init.set_defaults(handler=handle_initiative)

    table = roll_sub.add_parser("table", help="Roll on a simple table")
    table.add_argument("--die", default="d6", help="Die notation e.g. d6")
    table.set_defaults(handler=handle_table)

    attack = roll_sub.add_parser("attack", help="Attack vs AC (rules_engine)")
    attack.add_argument("--ability-mod", type=int, required=True)
    attack.add_argument("--pb", type=int, required=True)
    attack.add_argument("--skill-level", type=int, default=1)
    attack.add_argument("--target-ac", type=int, required=True)
    attack.add_argument("--weapon", default="1d8", help="Damage dice notation")
    attack.add_argument("--ability-damage-mod", type=int, default=0)
    attack.add_argument("--natural", type=int, default=None)
    attack.add_argument("--reason", default="")
    attack.set_defaults(handler=handle_attack)

    attrs = roll_sub.add_parser("attributes", help="Roll 1d10 per attribute (character creation)")
    attrs.add_argument(
        "--method",
        choices=("roll", "standard-array"),
        default="roll",
        help="roll = six 1d10; standard-array = return fixed pool [15,14,13,12,10,8]",
    )
    attrs.set_defaults(handler=handle_attributes)

    genetics = roll_sub.add_parser("genetics", help="Roll 1d4 genetics per attribute (creation)")
    genetics.set_defaults(handler=handle_genetics)

    life = roll_sub.add_parser("life-event", help="Roll 2d20 life event (creation)")
    life.set_defaults(handler=handle_life_event)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    conn = connect(cfg.db_path)
    return CommandContext(config=cfg, conn=conn)


def _session_id(ctx: CommandContext) -> str | None:
    path = ctx.config.active_path
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("session_id")


def handle_d20(args: argparse.Namespace, _ctx_unused: CommandContext | None) -> dict:
    ctx = _ctx(args)
    return perform_d20_roll(
        ctx.conn,
        log_event,
        session_id=_session_id(ctx),
        mod=args.mod,
        dc=args.dc,
        reason=args.reason or None,
        character_id=args.character_id,
        seed=args.seed,
        advantage=args.advantage,
        disadvantage=args.disadvantage,
    )


def handle_save(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    import random

    from tomb_gm.rules.bridge import roll_d20, saving_throw

    ctx = _ctx(args)
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    natural = roll_d20(rng)
    success = saving_throw(
        natural=natural,
        ability_mod=args.mod,
        pb=0,
        magical_defense_bonus=0,
        dc=args.dc,
    )
    total = natural + args.mod
    payload = {
        "kind": "save",
        "natural": natural,
        "total": total,
        "dc": args.dc,
        "success": success,
        "reason": args.reason or "",
    }
    log_event(ctx.conn, _session_id(ctx), "roll", payload)
    return {"ok": True, **payload}


def handle_initiative(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    from tomb_gm.services.simulation.combat import roll_round_initiative

    ctx = _ctx(args)
    session_id = _session_id(ctx)
    if not session_id:
        return {"ok": False, "error": "NO_ACTIVE_SESSION"}
    campaign = None
    row = ctx.conn.execute(
        "SELECT campaign_slug FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()
    if row:
        campaign = row["campaign_slug"]
    return roll_round_initiative(
        ctx.conn,
        session_id,
        content_root=ctx.config.content_root,
        campaign_slug=campaign,
        seed=args.seed,
        increment_round=bool(getattr(args, "new_round", False)),
    )


def handle_table(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    import random

    from tomb_gm.rules.bridge import roll_dice

    ctx = _ctx(args)
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    total = roll_dice(args.die, rng=rng)
    payload = {"kind": "table", "die": args.die, "total": total}
    log_event(ctx.conn, _session_id(ctx), "roll", payload)
    return {"ok": True, **payload}


def handle_attributes(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    import random

    from tomb_gm.domain.character import roll_attribute_scores, standard_attribute_pool

    ctx = _ctx(args)
    if args.method == "standard-array":
        meta, pool = standard_attribute_pool()
        payload = {**meta, "pool": pool}
        log_event(ctx.conn, _session_id(ctx), "roll", payload)
        return {"ok": True, **meta}

    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    scores, detail = roll_attribute_scores(rng)
    payload = {
        "kind": "attributes",
        "method": "roll",
        "attributes": scores,
        "detail": detail,
        "seed": args.seed,
    }
    log_event(ctx.conn, _session_id(ctx), "roll", payload)
    return {"ok": True, "method": "roll", "attributes": scores, "detail": detail}


def handle_genetics(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    import random

    from tomb_gm.domain.creation import roll_genetics

    ctx = _ctx(args)
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    mods, detail = roll_genetics(rng)
    payload = {"kind": "genetics", "modifiers": mods, "detail": detail}
    log_event(ctx.conn, _session_id(ctx), "roll", payload)
    return {"ok": True, **payload}


def handle_life_event(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    import random

    from tomb_gm.domain.creation import roll_life_event

    ctx = _ctx(args)
    rng = random.Random(args.seed) if args.seed is not None else random.Random()
    event, dice = roll_life_event(rng, ctx.config.content_root)
    payload = {"kind": "life_event", "dice": dice, "event": event}
    log_event(ctx.conn, _session_id(ctx), "roll", payload)
    return {"ok": True, **payload}


def handle_attack(args: argparse.Namespace, _ctx_unused: CommandContext | None) -> dict:
    ctx = _ctx(args)
    return perform_attack_roll(
        ctx.conn,
        log_event,
        session_id=_session_id(ctx),
        ability_mod=args.ability_mod,
        pb=args.pb,
        skill_level=args.skill_level,
        target_ac=args.target_ac,
        weapon_damage=args.weapon,
        ability_damage_mod=args.ability_damage_mod,
        reason=args.reason or None,
        seed=args.seed,
        natural=args.natural,
    )


add_command_module(register)
