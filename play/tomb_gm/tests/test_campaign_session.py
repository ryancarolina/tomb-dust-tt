from __future__ import annotations

import json
import uuid

import pytest


@pytest.fixture()
def campaign_slug() -> str:
    return f"test-{uuid.uuid4().hex[:8]}"


def test_campaign_new_session_lifecycle(
    run_tomb_gm,
    clear_active_session,
    isolated_workspace,
    campaign_slug: str,
):
    run_tomb_gm("init")
    clear_active_session()

    created = run_tomb_gm("campaign", "new", "--slug", campaign_slug, "--name", "Test Campaign")
    assert created["ok"] is True
    assert created["slug"] == campaign_slug
    assert "content_pin" in created
    assert (isolated_workspace / "campaigns" / campaign_slug).is_dir()

    listed = run_tomb_gm("campaign", "list")
    assert listed["ok"] is True
    assert any(c["slug"] == campaign_slug for c in listed["campaigns"])

    shown = run_tomb_gm("campaign", "show", "--slug", campaign_slug)
    assert shown["ok"] is True
    assert shown["last_session"] is None

    started = run_tomb_gm("session", "start", "--campaign", campaign_slug)
    assert started["ok"] is True
    assert started["phase"] == "preparation"
    assert started["address"] == "32-C"
    assert started["session_id"] == "current"

    active_path = isolated_workspace / ".local" / "active.json"
    assert active_path.exists()
    active = json.loads(active_path.read_text(encoding="utf-8"))
    assert active["campaign_slug"] == campaign_slug
    assert active["session_id"] == started["session_id"]

    status = run_tomb_gm("status")
    assert status["ok"] is True
    assert status["active"] is not None
    assert status["active"]["campaign_slug"] == campaign_slug
    assert status["active"]["session_id"] == started["session_id"]
    assert status["party"]["address"] == "32-C"
    assert status["party"]["phase"] == "preparation"
    assert status["awaiting"] == "CHARACTER_CREATION"

    ended = run_tomb_gm("session", "end")
    assert ended["ok"] is True
    assert ended["session_id"] == started["session_id"]
    assert not active_path.exists()

    after = run_tomb_gm("status")
    assert after["active"] is None
    assert after["awaiting"] == "SETUP"
