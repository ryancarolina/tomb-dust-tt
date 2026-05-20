"""Shared pytest fixtures — tests must never mutate play/workspace (player saves)."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

from helpers import PLAY, make_isolated_workspace


@pytest.fixture
def isolated_workspace(tmp_path: Path) -> Path:
    return make_isolated_workspace(tmp_path)


@pytest.fixture
def run_tomb_gm(isolated_workspace: Path) -> Callable[..., dict[str, Any]]:
    def _run(
        *args: str,
        expect_ok: bool = True,
        seed: int | None = None,
    ) -> dict[str, Any]:
        cmd = [sys.executable, "-m", "tomb_gm", "--workspace", str(isolated_workspace)]
        if seed is not None:
            cmd.extend(["--seed", str(seed)])
        cmd.extend(args)
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(PLAY),
            env=os.environ,
        )
        raw = proc.stdout or proc.stderr or "{}"
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"Non-JSON CLI output for {args}: {raw}") from exc
        if expect_ok and proc.returncode != 0:
            raise AssertionError(proc.stderr or proc.stdout)
        if not expect_ok and proc.returncode == 0 and payload.get("ok"):
            raise AssertionError(f"Expected CLI failure for {args}: {payload}")
        return payload

    return _run


@pytest.fixture
def clear_active_session(isolated_workspace: Path, run_tomb_gm) -> Callable[[], None]:
    def _clear() -> None:
        active_path = isolated_workspace / ".local" / "active.json"
        if active_path.exists():
            run_tomb_gm("session", "end", expect_ok=False)
        if active_path.exists():
            active_path.unlink()

    return _clear


@pytest.fixture
def test_config(isolated_workspace: Path):
    from tomb_gm.config import load_config

    return load_config(isolated_workspace)


@pytest.fixture
def test_db(test_config):
    import sqlite3

    conn = sqlite3.connect(test_config.db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def command_ctx(isolated_workspace: Path):
    from tomb_gm.cli.context import CommandContext
    from tomb_gm.config import load_config
    from tomb_gm.db.connection import connect, run_migrations

    cfg = load_config(isolated_workspace)
    conn = connect(cfg.db_path)
    run_migrations(conn)
    yield CommandContext(config=cfg, conn=conn)
    conn.close()


@pytest.fixture
def args_ns(isolated_workspace: Path) -> Callable[..., argparse.Namespace]:
    def _ns(**kwargs: Any) -> argparse.Namespace:
        base: dict[str, Any] = {"workspace": str(isolated_workspace)}
        base.update(kwargs)
        return argparse.Namespace(**base)

    return _ns
