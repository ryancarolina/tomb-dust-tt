"""Test helpers shared by conftest and individual test modules."""

from __future__ import annotations

import os
from pathlib import Path

# app/tests/helpers.py — one level shallower than play/tomb_gm/tests/helpers.py (parents[3]).
REPO = Path(__file__).resolve().parents[2]
APP = REPO / "app"
PLAY = REPO / "play"
BUILD = REPO / "build"


def make_isolated_workspace(base: Path) -> Path:
    ws = base / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    (ws / "campaigns").mkdir(exist_ok=True)
    rel_build = Path(os.path.relpath(BUILD, ws))
    (ws / "config.yaml").write_text(
        f"content_root: {rel_build.as_posix()}\nlocal_dir: .local\nmax_players: 4\n",
        encoding="utf-8",
    )
    return ws.resolve()
