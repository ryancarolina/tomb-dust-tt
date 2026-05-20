"""Combat state machine — code-enforced turn flow (mirrors creation FSM)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

COMBAT_STEPS = [
    "COMBAT_IDLE",
    "COMBAT_ENCOUNTER",
    "COMBAT_INITIATIVE_ROUND",
    "COMBAT_NARRATE_ORDER",
    "COMBAT_PC_ACTION",
    "COMBAT_RESOLVE_PC",
    "COMBAT_MONSTER_ACT",
    "COMBAT_TURN_ADVANCE",
    "COMBAT_CHECK_END",
    "COMBAT_END",
    "COMBAT_AFTERMATH",
]


@dataclass
class CombatState:
    active: bool = False
    step: str = "COMBAT_IDLE"
    pending_start: bool = False
    pending_monsters: list[str] = field(default_factory=list)
    order_narrated: bool = False
    last_mechanical: list[dict[str, Any]] = field(default_factory=list)
    round: int = 0
    turn_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "active": self.active,
            "step": self.step,
            "pending_start": self.pending_start,
            "pending_monsters": list(self.pending_monsters),
            "order_narrated": self.order_narrated,
            "last_mechanical": list(self.last_mechanical),
            "round": self.round,
            "turn_id": self.turn_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> CombatState:
        if not data:
            return cls()
        return cls(
            active=bool(data.get("active")),
            step=str(data.get("step") or "COMBAT_IDLE"),
            pending_start=bool(data.get("pending_start")),
            pending_monsters=list(data.get("pending_monsters") or []),
            order_narrated=bool(data.get("order_narrated")),
            last_mechanical=list(data.get("last_mechanical") or []),
            round=int(data.get("round") or 0),
            turn_id=data.get("turn_id"),
        )


def is_pc_turn(status: dict[str, Any]) -> bool:
    combat = status.get("combat") or {}
    turn_id = combat.get("turn_id")
    if not turn_id:
        return False
    for c in combat.get("combatants") or []:
        if c.get("id") == turn_id:
            return c.get("kind") == "pc"
    return False


def combatant_kind(status: dict[str, Any], combatant_id: str) -> str | None:
    for c in (status.get("combat") or {}).get("combatants") or []:
        if c.get("id") == combatant_id:
            return c.get("kind")
    return None


def format_initiative_table(initiative: list[dict[str, Any]]) -> str:
    lines = ["**Initiative this round:**"]
    for i, row in enumerate(initiative, 1):
        lines.append(
            f"{i}. {row.get('name', row.get('id', '?'))} — "
            f"{row.get('initiative', '?')} (d20 {row.get('natural', '?')})"
        )
    return "\n".join(lines)


def get_combat_step_prompt(state: CombatState, status: dict[str, Any]) -> str:
    combat = status.get("combat") or {}
    turn_id = combat.get("turn_id")
    step = state.step

    if step == "COMBAT_PC_ACTION":
        targets = [
            c for c in (combat.get("combatants") or [])
            if c.get("kind") == "monster" and int(c.get("hp", 0)) > 0
        ]
        target_lines = [
            f"  - {c['id']}: {c.get('displayName', '?')} HP {c.get('hp')}/{c.get('maxHp')} AC {c.get('ac')}"
            for c in targets
        ]
        return (
            f"COMBAT — Round {combat.get('round', '?')}. It is **{turn_id}**'s turn (player action required).\n"
            f"Call **combat_action** only. Valid targets:\n" + "\n".join(target_lines) + "\n"
            "Actions: ATTACK (weapon_id if known), CAST (spell_id from knownSpells), END_TURN.\n"
            "Do NOT call process_beat, start_combat, world_travel, or move_room during combat."
        )

    if step == "COMBAT_NARRATE_ORDER":
        return (
            "COMBAT — New round initiative has been rolled. Narrate the turn order briefly.\n"
            + format_initiative_table(combat.get("initiative") or [])
        )

    if step == "COMBAT_AFTERMATH":
        return "COMBAT ENDED. Narrate the outcome briefly. Do not call combat tools."

    return (
        f"COMBAT active — Round {combat.get('round', '?')}, turn {turn_id}. "
        "Follow mechanical results only."
    )
