"""Test helpers shared by conftest and individual test modules."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
PLAY = REPO / "play"
BUILD = REPO / "build"
PLAY_WORKSPACE = PLAY / "workspace"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_isolated_workspace(base: Path) -> Path:
    ws = base / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "campaigns").mkdir(exist_ok=True)
    import os

    rel_build = Path(os.path.relpath(BUILD, ws))
    (ws / "config.yaml").write_text(
        f"content_root: {rel_build.as_posix()}\nlocal_dir: .local\nmax_players: 4\n",
        encoding="utf-8",
    )
    return ws.resolve()


def seed_campaign(conn, slug: str, display_name: str | None = None) -> None:
    now = utc_now()
    conn.execute(
        "INSERT OR REPLACE INTO campaigns "
        "(slug, display_name, content_pin_json, account_state_json, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (slug, display_name or slug, "{}", "{}", now, now),
    )
    conn.commit()
