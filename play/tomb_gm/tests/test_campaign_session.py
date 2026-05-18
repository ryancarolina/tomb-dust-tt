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
    import os

    proc = subprocess.run(
        [sys.executable, "-m", "tomb_gm", "--workspace", str(WORKSPACE), *args],
        capture_output=True,
        text=True,
        cwd=str(PLAY),
        env=os.environ,
    )
    payload = json.loads(proc.stdout or proc.stderr or "{}")
    if expect_ok and proc.returncode != 0:
        raise AssertionError(proc.stderr or proc.stdout)
    return payload


def _clear_active_session() -> None:
    active_path = WORKSPACE / ".local" / "active.json"
    if active_path.exists():
        _run("session", "end", expect_ok=False)
    if active_path.exists():
        active_path.unlink()


@pytest.fixture()
def campaign_slug() -> str:
    return f"test-{uuid.uuid4().hex[:8]}"


def test_campaign_new_session_lifecycle(campaign_slug: str):
    _run("init")
    _clear_active_session()

    created = _run("campaign", "new", "--slug", campaign_slug, "--name", "Test Campaign")
    assert created["ok"] is True
    assert created["slug"] == campaign_slug
    assert "content_pin" in created
    assert (WORKSPACE / "campaigns" / campaign_slug).is_dir()

    listed = _run("campaign", "list")
    assert listed["ok"] is True
    assert any(c["slug"] == campaign_slug for c in listed["campaigns"])

    shown = _run("campaign", "show", "--slug", campaign_slug)
    assert shown["ok"] is True
    assert shown["last_session"] is None

    started = _run("session", "start", "--campaign", campaign_slug)
    assert started["ok"] is True
    assert started["phase"] == "preparation"
    assert started["address"] == "32-C"
    uuid.UUID(started["session_id"])

    active_path = WORKSPACE / ".local" / "active.json"
    assert active_path.exists()
    active = json.loads(active_path.read_text(encoding="utf-8"))
    assert active["campaign_slug"] == campaign_slug
    assert active["session_id"] == started["session_id"]

    status = _run("status")
    assert status["ok"] is True
    assert status["active"] is not None
    assert status["active"]["campaign_slug"] == campaign_slug
    assert status["active"]["session_id"] == started["session_id"]
    assert status["party"]["address"] == "32-C"
    assert status["party"]["phase"] == "preparation"
    assert status["awaiting"] == "CHARACTER_CREATION"

    ended = _run("session", "end")
    assert ended["ok"] is True
    assert ended["session_id"] == started["session_id"]
    assert not active_path.exists()

    after = _run("status")
    assert after["active"] is None
    assert after["awaiting"] == "SETUP"
