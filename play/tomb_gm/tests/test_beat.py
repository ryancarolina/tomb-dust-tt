from __future__ import annotations

import json
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
PLAY = REPO / "play"
WORKSPACE = PLAY / "workspace"
def _run(*args: str, expect_ok: bool = True) -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "tomb_gm", "--workspace", str(WORKSPACE), *args],
        capture_output=True,
        text=True,
        cwd=str(PLAY),
        env=__import__("os").environ,
    )
    data = json.loads(proc.stdout or proc.stderr or "{}")
    if expect_ok and proc.returncode != 0:
        raise AssertionError(proc.stderr or proc.stdout)
    return data


def _clear_active_session() -> None:
    active_path = WORKSPACE / ".local" / "active.json"
    if active_path.exists():
        _run("session", "end", expect_ok=False)
    if active_path.exists():
        active_path.unlink()


def _seed_session() -> str:
    slug = f"beat-{uuid.uuid4().hex[:8]}"
    _run("init")
    _clear_active_session()
    _run("campaign", "new", "--slug", slug, "--name", "Beat Test")
    _run("session", "start", "--campaign", slug)
    return slug


def test_beat_travel_and_look():
    _seed_session()
    actions = json.dumps(
        {
            "lines": [
                {"slot": 1, "raw": "We travel to 33-C on the King's Road."},
                {"slot": 2, "raw": "I look around."},
            ]
        }
    )
    beat = _run("beat", "--actions", actions)
    assert beat["ok"] is True
    assert beat["beat_id"]
    assert beat["narration_brief"]
    summary = beat["mechanical_summary"]
    assert any(m.get("action") == "travel" and m.get("ok") for m in summary)
    st = _run("status")
    assert st["party"]["address"] == "33-C"


def test_beat_site_enter_and_move():
    _seed_session()
    travel = json.dumps({"lines": [{"slot": 1, "raw": "We go to 32-C-UG-1"}]})
    _run("beat", "--actions", travel)
    actions = json.dumps(
        {
            "lines": [
                {"slot": 1, "raw": "We enter the breley-undercrypt."},
                {"slot": 2, "raw": "Move to ossuary-hall."},
            ]
        }
    )
    beat = _run("beat", "--actions", actions)
    assert beat["ok"] is True
    assert any(m.get("action") == "site_enter" for m in beat["mechanical_summary"])
    assert any(m.get("action") == "site_move" for m in beat["mechanical_summary"])


def test_beat_requires_session():
    _run("init")
    _clear_active_session()
    actions = json.dumps({"lines": [{"slot": 1, "raw": "hello"}]})
    data = _run("beat", "--actions", actions, expect_ok=False)
    assert data["ok"] is False
    assert data["error"] == "NO_ACTIVE_SESSION"
