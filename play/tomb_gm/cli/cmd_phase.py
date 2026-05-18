from __future__ import annotations

import argparse

from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.registry import add_command_module
from tomb_gm.config import load_config, resolve_workspace
from tomb_gm.db.connection import connect
from tomb_gm.services import extraction as extraction_svc


def register(sub: argparse._SubParsersAction) -> None:
    phase = sub.add_parser("phase", help="Extraction phase")
    phase_sub = phase.add_subparsers(dest="phase_cmd", required=True)
    set_p = phase_sub.add_parser("set", help="Set extraction phase")
    set_p.add_argument(
        "--phase",
        required=True,
        choices=sorted(extraction_svc.PHASES),
        help="Target phase",
    )
    set_p.set_defaults(handler=handle_phase_set)

    clock = sub.add_parser("clock", help="Threat clocks")
    clock_sub = clock.add_subparsers(dest="clock_cmd", required=True)
    tick_p = clock_sub.add_parser("tick", help="Advance a threat clock")
    tick_p.add_argument("--clock", required=True, choices=["ingress", "delve", "extract"])
    tick_p.add_argument("--reason", default="", help="Why the clock advanced")
    tick_p.add_argument("--segments", type=int, default=1)
    tick_p.set_defaults(handler=handle_clock_tick)
    clock_sub.add_parser("show", help="Show all clocks").set_defaults(handler=handle_clock_show)

    registry = sub.add_parser("registry", help="Registry services")
    reg_sub = registry.add_subparsers(dest="registry_cmd", required=True)
    stamp = reg_sub.add_parser("stamp", help="Map stamps")
    stamp_sub = stamp.add_subparsers(dest="stamp_cmd", required=True)
    buy_p = stamp_sub.add_parser("buy", help="Purchase a map stamp (stub)")
    buy_p.add_argument("--address", required=True, help="Primary AV-GRID address")
    buy_p.add_argument("--danger", default="skirmisher", help="Danger tier")
    buy_p.add_argument("--surface-entry", dest="surface_entry", default=None)
    buy_p.set_defaults(handler=handle_registry_stamp_buy)


def _ctx(args: argparse.Namespace) -> CommandContext:
    ws = resolve_workspace(args.workspace)
    cfg = load_config(ws)
    return CommandContext(config=cfg, conn=connect(cfg.db_path))


def handle_phase_set(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    return extraction_svc.set_phase(_ctx(args), args.phase)


def handle_clock_tick(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    return extraction_svc.clock_tick(
        _ctx(args),
        args.clock,
        reason=args.reason,
        segments=args.segments,
    )


def handle_clock_show(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    return extraction_svc.clock_show(_ctx(args))


def handle_registry_stamp_buy(args: argparse.Namespace, _ctx_unused: CommandContext | None = None) -> dict:
    return extraction_svc.registry_stamp_buy(
        _ctx(args),
        args.address,
        danger=args.danger,
        surface_entry=args.surface_entry,
    )


add_command_module(register)
