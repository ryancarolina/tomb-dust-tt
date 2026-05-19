"""Build LLM context from game state."""

from __future__ import annotations

from typing import Any


def build_state_context(status: dict) -> str:
    """Turn the status dict into a concise state block for the LLM."""
    parts: list[str] = []

    party = status.get("party")
    if party:
        parts.append(f"Location: {party.get('address', '?')} (mode: {party.get('mode', 'surface')})")
        parts.append(f"Phase: {party.get('phase', '?')}")
        if party.get("site_id"):
            parts.append(f"Site: {party['site_id']} node: {party.get('site_node_id', '?')}")
        clocks = party.get("clocks")
        if clocks:
            parts.append(f"Clocks: {clocks}")

    roster = status.get("roster", [])
    if roster:
        roster_lines = []
        for r in roster:
            roster_lines.append(f"  Slot {r['slot']}: {r['display_name']} HP {r['hp']}")
        parts.append("Party:\n" + "\n".join(roster_lines))

    combat = status.get("combat")
    if combat:
        parts.append(f"COMBAT ACTIVE — Round {combat['round']}, Turn {combat['turn_index']}")
        parts.append(f"Initiative: {combat['initiative']}")

    awaiting = status.get("awaiting", "SETUP")
    parts.append(f"Awaiting: {awaiting}")

    return "\n".join(parts)


def build_messages(
    system_prompt: str,
    state_context: str,
    history: list[dict[str, str]],
    player_input: str,
) -> list[dict[str, Any]]:
    """Assemble the messages array for the LLM."""
    combined_system = f"{system_prompt}\n\n## Current Game State\n{state_context}"
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": combined_system},
    ]

    for msg in history[-20:]:
        messages.append(msg)

    messages.append({"role": "user", "content": player_input})
    return messages
