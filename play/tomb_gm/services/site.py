from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tomb_gm.cli.cmd_core import log_event
from tomb_gm.cli.context import CommandContext
from tomb_gm.domain.stamp import RegistryStamp, stamp_matches_site


class SiteError(Exception):
    pass


@dataclass(frozen=True)
class SiteNode:
    id: str
    address: str
    display_name: str
    tags: tuple[str, ...]
    encounters: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class SiteEdge:
    from_id: str
    to_id: str
    edge_type: str
    locked: bool
    hazard: str | None


@dataclass(frozen=True)
class SiteGraph:
    id: str
    display_name: str
    primary_address: str
    danger_rating: str
    nodes: dict[str, SiteNode]
    edges: tuple[SiteEdge, ...]

    def entry_node_id(self) -> str:
        for node in self.nodes.values():
            if "entry" in node.tags:
                return node.id
        if self.nodes:
            return next(iter(self.nodes))
        raise SiteError("Site has no nodes")

    def edges_from(self, node_id: str) -> list[SiteEdge]:
        return [e for e in self.edges if e.from_id == node_id]


def _sites_dir(content_root: Path) -> Path:
    return content_root / "data" / "sites"


def load_site(content_root: Path, site_id: str) -> SiteGraph:
    path = _sites_dir(content_root) / f"{site_id}.json"
    if not path.is_file():
        raise SiteError(f"Unknown site: {site_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    nodes: dict[str, SiteNode] = {}
    for raw in data.get("nodes", []):
        node = SiteNode(
            id=str(raw["id"]),
            address=str(raw.get("address", data.get("primaryAddress", ""))),
            display_name=str(raw.get("displayName", raw["id"])),
            tags=tuple(raw.get("tags", [])),
            encounters=tuple(raw.get("encounters", [])),
        )
        nodes[node.id] = node
    edges: list[SiteEdge] = []
    for raw in data.get("edges", []):
        edges.append(
            SiteEdge(
                from_id=str(raw["from"]),
                to_id=str(raw["to"]),
                edge_type=str(raw.get("type", "passage")),
                locked=bool(raw.get("locked", False)),
                hazard=raw.get("hazard"),
            )
        )
    return SiteGraph(
        id=str(data["id"]),
        display_name=str(data.get("displayName", site_id)),
        primary_address=str(data.get("primaryAddress", "")),
        danger_rating=str(data.get("dangerRating", "skirmisher")),
        nodes=nodes,
        edges=tuple(edges),
    )


def _read_active(config) -> dict[str, Any]:
    if not config.active_path.is_file():
        raise SiteError("No active session (missing active.json)")
    return json.loads(config.active_path.read_text(encoding="utf-8"))


def _party_row(ctx: CommandContext, session_id: str) -> Any:
    row = ctx.conn.execute(
        "SELECT * FROM party_state WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    if row is None:
        raise SiteError("Party state missing for active session")
    return row


def _flags(row) -> dict[str, Any]:
    return json.loads(row["flags_json"] or "{}")


def _save_party(
    ctx: CommandContext,
    session_id: str,
    *,
    address: str | None = None,
    mode: str | None = None,
    site_id: str | None = None,
    site_node_id: str | None = None,
    flags_json: str | None = None,
) -> None:
    row = _party_row(ctx, session_id)
    ctx.conn.execute(
        """
        UPDATE party_state SET
          address = COALESCE(?, address),
          mode = COALESCE(?, mode),
          site_id = COALESCE(?, site_id),
          site_node_id = COALESCE(?, site_node_id),
          flags_json = COALESCE(?, flags_json)
        WHERE session_id = ?
        """,
        (address, mode, site_id, site_node_id, flags_json, session_id),
    )
    ctx.conn.commit()


def _edge_key(edge: SiteEdge) -> str:
    return f"{edge.from_id}->{edge.to_id}"


def _is_edge_unlocked(flags: dict[str, Any], edge: SiteEdge) -> bool:
    if not edge.locked:
        return True
    unlocks: list[str] = flags.get("site_unlocks", [])
    return _edge_key(edge) in unlocks or edge.to_id in unlocks


def enter_site(ctx: CommandContext, site_id: str) -> dict[str, Any]:
    active = _read_active(ctx.config)
    session_id = active["session_id"]
    party = _party_row(ctx, session_id)
    graph = load_site(ctx.config.content_root, site_id)
    phase = party["phase"]
    stamp = RegistryStamp.from_json(json.loads(party["stamp_json"]) if party["stamp_json"] else None)
    if phase in ("delve", "extract"):
        if not stamp_matches_site(stamp, graph.primary_address, party["address"]):
            raise SiteError(
                f"Valid Registry stamp required for {graph.primary_address} during {phase}"
            )
    entry_id = graph.entry_node_id()
    entry = graph.nodes[entry_id]
    _save_party(
        ctx,
        session_id,
        address=entry.address,
        mode="site",
        site_id=site_id,
        site_node_id=entry_id,
    )
    log_event(
        ctx.conn,
        session_id,
        "site.enter",
        {"site_id": site_id, "node_id": entry_id, "address": entry.address},
    )
    return {
        "ok": True,
        "site_id": site_id,
        "mode": "site",
        "node_id": entry_id,
        "node": _node_payload(entry),
        "address": entry.address,
    }


def where_site(ctx: CommandContext) -> dict[str, Any]:
    active = _read_active(ctx.config)
    party = _party_row(ctx, active["session_id"])
    if party["mode"] != "site" or not party["site_id"] or not party["site_node_id"]:
        raise SiteError("Not inside a site (mode is not site)")
    graph = load_site(ctx.config.content_root, party["site_id"])
    node = graph.nodes[party["site_node_id"]]
    return {
        "ok": True,
        "site_id": party["site_id"],
        "node_id": node.id,
        "node": _node_payload(node),
        "address": node.address,
        "phase": party["phase"],
    }


def exits_site(ctx: CommandContext) -> dict[str, Any]:
    active = _read_active(ctx.config)
    party = _party_row(ctx, active["session_id"])
    if party["mode"] != "site" or not party["site_id"] or not party["site_node_id"]:
        raise SiteError("Not inside a site (mode is not site)")
    graph = load_site(ctx.config.content_root, party["site_id"])
    flags = _flags(party)
    out: list[dict[str, Any]] = []
    for edge in graph.edges_from(party["site_node_id"]):
        target = graph.nodes.get(edge.to_id)
        if target is None:
            continue
        unlocked = _is_edge_unlocked(flags, edge)
        out.append(
            {
                "to": edge.to_id,
                "displayName": target.display_name,
                "type": edge.edge_type,
                "locked": edge.locked,
                "passable": unlocked,
                "hazard": edge.hazard,
            }
        )
    return {"ok": True, "site_id": party["site_id"], "from": party["site_node_id"], "exits": out}


def move_site(ctx: CommandContext, to_node_id: str) -> dict[str, Any]:
    active = _read_active(ctx.config)
    session_id = active["session_id"]
    party = _party_row(ctx, session_id)
    if party["mode"] != "site" or not party["site_id"] or not party["site_node_id"]:
        raise SiteError("Not inside a site (mode is not site)")
    graph = load_site(ctx.config.content_root, party["site_id"])
    if to_node_id not in graph.nodes:
        raise SiteError(f"Unknown node: {to_node_id}")
    flags = _flags(party)
    edge_used: SiteEdge | None = None
    for edge in graph.edges_from(party["site_node_id"]):
        if edge.to_id == to_node_id:
            edge_used = edge
            break
    if edge_used is None:
        raise SiteError(f"No edge from {party['site_node_id']} to {to_node_id}")
    if not _is_edge_unlocked(flags, edge_used):
        raise SiteError(f"Edge to {to_node_id} is locked")
    target = graph.nodes[to_node_id]
    _save_party(
        ctx,
        session_id,
        address=target.address,
        site_node_id=to_node_id,
    )
    payload: dict[str, Any] = {
        "from": party["site_node_id"],
        "to": to_node_id,
        "edge_type": edge_used.edge_type,
    }
    if edge_used.hazard:
        payload["hazard"] = edge_used.hazard
    log_event(ctx.conn, session_id, "site.move", payload)
    result: dict[str, Any] = {
        "ok": True,
        "site_id": party["site_id"],
        "from": party["site_node_id"],
        "to": to_node_id,
        "node": _node_payload(target),
        "address": target.address,
    }
    if edge_used.hazard:
        result["hazard"] = edge_used.hazard
    if target.encounters:
        result["encounters"] = list(target.encounters)
    return result


def search_site(
    ctx: CommandContext,
    *,
    dc: int = 13,
    skill_mod: int = 0,
    seed: int | None = None,
) -> dict[str, Any]:
    """Investigation roll at current site node (d20 + mod vs DC)."""
    import random

    from tomb_gm.rules.bridge import roll_d20
    from tomb_gm.services.loot import roll_loot_table

    active = _read_active(ctx.config)
    party = _party_row(ctx, active["session_id"])
    if party["mode"] != "site" or not party["site_id"] or not party["site_node_id"]:
        raise SiteError("Not inside a site (mode is not site)")
    graph = load_site(ctx.config.content_root, party["site_id"])
    node = graph.nodes[party["site_node_id"]]
    rng = random.Random(seed) if seed is not None else random.Random()
    natural = roll_d20(rng)
    total = natural + skill_mod
    success = total >= dc

    payload: dict[str, Any] = {
        "ok": True,
        "action": "site_search",
        "site_id": party["site_id"],
        "node_id": node.id,
        "node": _node_payload(node),
        "dc": dc,
        "natural": natural,
        "modifier": skill_mod,
        "total": total,
        "success": success,
    }
    if success:
        clues: list[str] = []
        if "boss-adjacent" in node.tags:
            clues.append("Registry seal marks and fresh claw-scoring on the stone.")
        if "thin-veil" in node.tags:
            clues.append("Veil bleed: sound carries wrong; shadows lag a heartbeat.")
        if "burial" in node.tags:
            clues.append("Disturbed ossuary niches; something was dragged toward the marshal tomb.")
        if "hazard" in node.tags:
            clues.append("Structural stress: a collapse clock may advance on loud fights.")
        if clues:
            payload["clues"] = clues
        if "loot" in node.tags:
            loot = roll_loot_table(
                ctx.config.content_root,
                graph.danger_rating,
                rng=rng,
            )
            payload["loot"] = loot
    else:
        payload["message"] = "Nothing useful turns up this pass."

    log_event(
        ctx.conn,
        active["session_id"],
        "site.search",
        {
            "node_id": node.id,
            "dc": dc,
            "natural": natural,
            "success": success,
        },
    )
    return payload


def _node_payload(node: SiteNode) -> dict[str, Any]:
    return {
        "id": node.id,
        "displayName": node.display_name,
        "tags": list(node.tags),
        "address": node.address,
    }
