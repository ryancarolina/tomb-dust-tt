"""Bridge: direct Python API into the tomb_gm engine (no subprocess)."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from tomb_gm.config import resolve_workspace, load_config
from tomb_gm.db.connection import run_migrations
from tomb_gm.cli.context import CommandContext
from tomb_gm.cli.cmd_core import handle_init, handle_status, handle_check, handle_suggest, log_event


def _connect_threadsafe(db_path: Path) -> sqlite3.Connection:
    """Connect with check_same_thread=False for use from background threads."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


class GameBridge:
    """Provides direct access to tomb_gm mechanics without subprocess calls."""

    def __init__(self, workspace: str | Path | None = None):
        ws = resolve_workspace(str(workspace) if workspace else None)
        cfg = load_config(ws)
        conn = _connect_threadsafe(cfg.db_path)
        run_migrations(conn)
        self.ctx = CommandContext(config=cfg, conn=conn)
        self._ns = _FakeNamespace(str(ws))

    def status(self) -> dict:
        return handle_status(self._ns, None)

    def check(self) -> dict:
        return handle_check(self._ns, None)

    def suggest(self) -> dict:
        return handle_suggest(self._ns, None)

    def init(self) -> dict:
        return handle_init(self._ns, None)

    def roll_d20(self, mod: int = 0, dc: int = 10, reason: str = "") -> dict:
        from tomb_gm.services.simulation.rolls import roll_d20
        result = roll_d20(self.ctx.conn, self._active_session_id(), mod=mod, dc=dc, reason=reason)
        return result

    def process_beat(self, lines: list[dict], **flags) -> dict:
        from tomb_gm.services.beat import process_beat
        actions = {"lines": lines, **flags}
        return process_beat(self.ctx, actions)

    def world_travel(self, to_address: str) -> dict:
        from tomb_gm.services.world import WorldService
        from tomb_gm.services.content import ContentService

        content = ContentService(self.ctx.config.content_root)
        world = WorldService(content)
        session_id = self._active_session_id()
        row = self.ctx.conn.execute(
            "SELECT address, stamp_json FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return {"ok": False, "error": "no active party state"}
        from_addr = row["address"]
        ok, code = world.can_travel(from_addr, to_address)
        if not ok:
            return {"ok": False, "error": code, "from": from_addr, "to": to_address}
        self.ctx.conn.execute(
            "UPDATE party_state SET address = ?, mode = 'surface', site_id = NULL, site_node_id = NULL WHERE session_id = ?",
            (to_address, session_id),
        )
        self.ctx.conn.commit()
        log_event(self.ctx.conn, session_id, "world_travel", {"from": from_addr, "to": to_address})
        cell = content.cell_payload(to_address)
        return {"ok": True, "action": "travel", "from": from_addr, "to": to_address, "cell": cell}

    def site_enter(self, site_id: str) -> dict:
        from tomb_gm.services.site import enter_site, SiteError
        try:
            return {**enter_site(self.ctx, site_id), "action": "site_enter"}
        except SiteError as exc:
            return {"ok": False, "error": str(exc)}

    def site_move(self, node_id: str) -> dict:
        from tomb_gm.services.site import move_site, SiteError
        try:
            return {**move_site(self.ctx, node_id), "action": "site_move"}
        except SiteError as exc:
            return {"ok": False, "error": str(exc)}

    def start_combat(self, monster_specs: list[str], include_party: bool = True) -> dict:
        from tomb_gm.services.simulation.combat import start_combat
        session_id = self._active_session_id()
        campaign_slug = self._campaign_slug()
        try:
            result = start_combat(
                self.ctx.conn,
                session_id=session_id,
                content_root=self.ctx.config.content_root,
                monster_specs=monster_specs,
                include_party=include_party,
                campaign_slug=campaign_slug,
            )
            return {**result, "action": "combat_start"}
        except (ValueError, FileNotFoundError) as exc:
            return {"ok": False, "error": str(exc)}

    def combat_attack(self, attacker_id: str, target_id: str) -> dict:
        from tomb_gm.services.simulation.combat import combat_attack
        session_id = self._active_session_id()
        try:
            return combat_attack(self.ctx.conn, session_id, attacker_id, target_id,
                                 content_root=self.ctx.config.content_root,
                                 campaign_slug=self._campaign_slug())
        except (ValueError, KeyError) as exc:
            return {"ok": False, "error": str(exc)}

    def combat_end(self) -> dict:
        from tomb_gm.services.simulation.combat import end_combat
        session_id = self._active_session_id()
        return end_combat(self.ctx.conn, session_id)

    def world_where(self) -> dict:
        from tomb_gm.services.world import WorldService
        from tomb_gm.services.content import ContentService

        content = ContentService(self.ctx.config.content_root)
        world = WorldService(content)
        session_id = self._active_session_id()
        row = self.ctx.conn.execute(
            "SELECT address, mode, stamp_json FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return {"ok": False, "error": "no party state"}
        payload = world.where_payload(row["address"], mode=row["mode"], stamp_json=row["stamp_json"])
        return {"ok": True, **(payload or {})}

    def world_exits(self) -> dict:
        from tomb_gm.services.world import WorldService
        from tomb_gm.services.content import ContentService

        content = ContentService(self.ctx.config.content_root)
        world = WorldService(content)
        session_id = self._active_session_id()
        row = self.ctx.conn.execute(
            "SELECT address FROM party_state WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        if not row:
            return {"ok": False, "error": "no party state"}
        exits = world.legal_exits(row["address"])
        return {"ok": True, "address": row["address"], "exits": exits}

    def campaign_new(self, slug: str, display_name: str = "") -> dict:
        from tomb_gm.domain.campaign import create_campaign
        return create_campaign(self.ctx.conn, self.ctx.config, slug, display_name or slug)

    def session_start(self, campaign_slug: str) -> dict:
        from tomb_gm.domain.session import start_session
        return start_session(self.ctx.conn, self.ctx.config, campaign_slug)

    def session_resume(self) -> dict:
        from tomb_gm.domain.session import resume_session
        return resume_session(self.ctx.conn, self.ctx.config)

    def character_create(self, **kwargs) -> dict:
        from tomb_gm.domain.character import create_character
        campaign_slug = self._campaign_slug()
        name = kwargs.pop("name", "Unnamed")
        background = kwargs.pop("background", "soldier")
        attributes = {}
        for attr in ("str", "agi", "end", "wil", "int", "luc"):
            key = f"{attr}_score"
            if key in kwargs:
                attributes[attr.upper()] = kwargs.pop(key)
        try:
            result = create_character(
                self.ctx.conn,
                campaign_slug=campaign_slug,
                display_name=name,
                base_class=background,
                attributes=attributes or None,
            )
            return {"ok": True, **result}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def roster_set(self, campaign_slug: str, slot: int, character_id: str) -> dict:
        from tomb_gm.domain.character import roster_set
        return roster_set(self.ctx.conn, campaign_slug, slot, character_id)

    def memory_recall(self, query: str, top_k: int = 5) -> dict:
        from tomb_gm.services.memory import recall_facts
        campaign_slug = self._campaign_slug()
        facts = recall_facts(self.ctx.conn, campaign_slug, query, top_k=top_k)
        return {"ok": True, "facts": facts}

    def _active_session_id(self) -> str:
        active_path = self.ctx.config.active_path
        if not active_path.exists():
            raise ValueError("NO_ACTIVE_SESSION")
        data = json.loads(active_path.read_text(encoding="utf-8"))
        sid = data.get("session_id")
        if not sid:
            raise ValueError("NO_ACTIVE_SESSION")
        return sid

    def _campaign_slug(self) -> str:
        session_id = self._active_session_id()
        row = self.ctx.conn.execute(
            "SELECT campaign_slug FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            raise ValueError("NO_CAMPAIGN")
        return row["campaign_slug"]


class _FakeNamespace:
    """Mimics argparse.Namespace for handlers that expect args.workspace."""

    def __init__(self, workspace: str):
        self.workspace = workspace
        self.seed = None
