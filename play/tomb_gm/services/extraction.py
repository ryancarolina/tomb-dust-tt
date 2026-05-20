from __future__ import annotations

import json
from typing import Any

from tomb_gm.cli.cmd_core import log_event
from tomb_gm.cli.context import CommandContext
from tomb_gm.domain.clock import ClockState
from tomb_gm.domain.stamp import RegistryStamp, build_stamp

PHASES = frozenset({"preparation", "ingress", "delve", "extract", "aftermath"})
PHASE_TRANSITIONS: dict[str, frozenset[str]] = {
    "preparation": frozenset({"ingress"}),
    "ingress": frozenset({"delve", "preparation"}),
    "delve": frozenset({"extract"}),
    "extract": frozenset({"aftermath", "delve"}),
    "aftermath": frozenset({"preparation"}),
}


class ExtractionError(Exception):
    pass


def _read_active(config) -> dict[str, Any]:
    if not config.active_path.is_file():
        raise ExtractionError("No active session (missing active.json)")
    return json.loads(config.active_path.read_text(encoding="utf-8"))


def _party_row(ctx: CommandContext, session_id: str):
    row = ctx.conn.execute(
        "SELECT * FROM party_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        raise ExtractionError("Party state missing for active session")
    return row


def set_phase(ctx: CommandContext, phase: str) -> dict[str, Any]:
    phase = phase.lower()
    if phase not in PHASES:
        raise ExtractionError(f"Unknown phase: {phase}")
    active = _read_active(ctx.config)
    session_id = active["session_id"]
    party = _party_row(ctx, session_id)
    current = party["phase"]
    allowed = PHASE_TRANSITIONS.get(current, frozenset())
    if phase != current and phase not in allowed:
        raise ExtractionError(f"Cannot transition from {current} to {phase}")
    ctx.conn.execute(
        "UPDATE party_state SET phase = ? WHERE session_id = ?",
        (phase, session_id),
    )
    ctx.conn.execute(
        "UPDATE sessions SET phase = ? WHERE id = ?",
        (phase, session_id),
    )
    ctx.conn.commit()
    log_event(ctx.conn, session_id, "phase.set", {"from": current, "to": phase})
    return {"ok": True, "phase": phase, "previous": current}


def advance_phase_for_dungeon_entry(ctx: CommandContext) -> dict[str, Any]:
    """Walk preparation→ingress→delve when the party enters an underground site."""
    active = _read_active(ctx.config)
    party = _party_row(ctx, active["session_id"])
    current = party["phase"]

    if current == "delve":
        return {"ok": True, "phase": "delve", "previous": current}
    if current == "preparation":
        ingress = set_phase(ctx, "ingress")
        if not ingress.get("ok"):
            return ingress
        current = "ingress"
    if current == "ingress":
        return set_phase(ctx, "delve")
    return {
        "ok": False,
        "error": f"Cannot enter dungeon from phase {current}",
        "phase": current,
    }


def clock_show(ctx: CommandContext) -> dict[str, Any]:
    active = _read_active(ctx.config)
    party = _party_row(ctx, active["session_id"])
    clocks = ClockState.from_json(json.loads(party["clocks_json"] or "{}"))
    return {"ok": True, "clocks": clocks.to_json(), "phase": party["phase"]}


def clock_tick(
    ctx: CommandContext,
    clock: str,
    *,
    reason: str = "",
    segments: int = 1,
) -> dict[str, Any]:
    active = _read_active(ctx.config)
    session_id = active["session_id"]
    party = _party_row(ctx, session_id)
    clocks = ClockState.from_json(json.loads(party["clocks_json"] or "{}"))
    updated, tick_info = clocks.tick(clock.lower(), segments)
    ctx.conn.execute(
        "UPDATE party_state SET clocks_json = ? WHERE session_id = ?",
        (json.dumps(updated.to_json()), session_id),
    )
    ctx.conn.commit()
    log_event(
        ctx.conn,
        session_id,
        "clock.tick",
        {"reason": reason, **tick_info},
    )
    return {
        "ok": True,
        "clocks": updated.to_json(),
        "tick": tick_info,
        "reason": reason or None,
    }


def registry_stamp_buy(
    ctx: CommandContext,
    address: str,
    *,
    danger: str = "skirmisher",
    surface_entry: str | None = None,
) -> dict[str, Any]:
    active = _read_active(ctx.config)
    session_id = active["session_id"]
    party = _party_row(ctx, session_id)
    stamp_data = build_stamp(address=address, danger=danger, surface_entry=surface_entry)
    cost = int(stamp_data["costGp"])
    gold = int(party["gold_in_transit"])
    if gold < cost:
        raise ExtractionError(f"Insufficient gold: need {cost}, have {gold}")
    new_gold = gold - cost
    ctx.conn.execute(
        "UPDATE party_state SET stamp_json = ?, gold_in_transit = ? WHERE session_id = ?",
        (json.dumps(stamp_data), new_gold, session_id),
    )
    ctx.conn.commit()
    stamp = RegistryStamp.from_json(stamp_data)
    assert stamp is not None
    log_event(
        ctx.conn,
        session_id,
        "registry.stamp.buy",
        {"address": address, "cost_gp": cost, "danger": danger},
    )
    return {
        "ok": True,
        "stamp": stamp.to_json(),
        "gold_in_transit": new_gold,
        "cost_gp": cost,
    }
