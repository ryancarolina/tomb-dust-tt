from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from tomb_gm.config import GameplayConfig, REPO_ROOT

_SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def validate_slug(slug: str) -> str | None:
    if not slug or not _SLUG_RE.match(slug):
        return "slug must be lowercase alphanumeric segments separated by hyphens"
    return None


def build_content_pin(content_root: Path) -> dict:
    pin: dict = {"rules_version": "1.0.0"}
    changelog = content_root / "RULESCHANGELOG.md"
    if changelog.exists():
        text = changelog.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("## ") and "—" in line:
                version = line.split("—", 1)[0].replace("##", "").strip()
                if version and version[0].isdigit():
                    pin["rules_version"] = version
                    break
    grid_path = content_root / "data" / "av-grid" / "av-grid.json"
    if grid_path.exists():
        try:
            data = json.loads(grid_path.read_text(encoding="utf-8"))
            if "version" in data:
                pin["av_grid_version"] = str(data["version"])
        except json.JSONDecodeError:
            pass
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            timeout=5,
            check=False,
        )
        if proc.returncode == 0:
            pin["git_commit"] = proc.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass
    return pin


def create_campaign(
    conn: sqlite3.Connection,
    cfg: GameplayConfig,
    slug: str,
    display_name: str,
) -> dict:
    err = validate_slug(slug)
    if err:
        return {"ok": False, "error": err}
    existing = conn.execute("SELECT slug FROM campaigns WHERE slug = ?", (slug,)).fetchone()
    if existing:
        return {"ok": False, "error": f"campaign already exists: {slug}"}

    now = _utc_now()
    content_pin = build_content_pin(cfg.content_root)
    conn.execute(
        "INSERT INTO campaigns (slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (slug, display_name, json.dumps(content_pin), "{}", now, now),
    )
    conn.commit()

    campaign_dir = cfg.campaigns_dir / slug
    campaign_dir.mkdir(parents=True, exist_ok=True)

    return {
        "ok": True,
        "slug": slug,
        "display_name": display_name,
        "content_pin": content_pin,
        "campaign_dir": str(campaign_dir),
        "created_at": now,
    }


def list_campaigns(conn: sqlite3.Connection) -> dict:
    rows = conn.execute(
        "SELECT slug, display_name, created_at, updated_at FROM campaigns ORDER BY created_at"
    ).fetchall()
    campaigns = [
        {
            "slug": row["slug"],
            "display_name": row["display_name"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
        for row in rows
    ]
    return {"ok": True, "campaigns": campaigns}


def show_campaign(conn: sqlite3.Connection, slug: str) -> dict:
    row = conn.execute("SELECT * FROM campaigns WHERE slug = ?", (slug,)).fetchone()
    if not row:
        return {"ok": False, "error": f"campaign not found: {slug}"}

    last_session = conn.execute(
        "SELECT id, started_at, ended_at, phase FROM sessions WHERE campaign_slug = ? "
        "ORDER BY started_at DESC LIMIT 1",
        (slug,),
    ).fetchone()

    last_session_payload = None
    if last_session:
        last_session_payload = {
            "id": last_session["id"],
            "started_at": last_session["started_at"],
            "ended_at": last_session["ended_at"],
            "phase": last_session["phase"],
            "open": last_session["ended_at"] is None,
        }

    return {
        "ok": True,
        "slug": row["slug"],
        "display_name": row["display_name"],
        "content_pin": json.loads(row["content_pin_json"]),
        "account_state": json.loads(row["account_state_json"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "last_session": last_session_payload,
    }
