from __future__ import annotations

import json
import uuid


def _seed_session(run_tomb_gm, clear_active_session) -> str:
    slug = f"beat-{uuid.uuid4().hex[:8]}"
    run_tomb_gm("init")
    clear_active_session()
    run_tomb_gm("campaign", "new", "--slug", slug, "--name", "Beat Test")
    run_tomb_gm("session", "start", "--campaign", slug)
    return slug


def test_beat_travel_and_look(run_tomb_gm, clear_active_session):
    _seed_session(run_tomb_gm, clear_active_session)
    actions = json.dumps(
        {
            "lines": [
                {"slot": 1, "raw": "We travel to 33-C on the King's Road."},
                {"slot": 2, "raw": "I look around."},
            ]
        }
    )
    beat = run_tomb_gm("beat", "--actions", actions)
    assert beat["ok"] is True
    assert beat["beat_id"]
    assert beat["narration_brief"]
    summary = beat["mechanical_summary"]
    assert any(m.get("action") == "travel" and m.get("ok") for m in summary)
    st = run_tomb_gm("status")
    assert st["party"]["address"] == "33-C"


def test_beat_site_enter_and_move(run_tomb_gm, clear_active_session):
    _seed_session(run_tomb_gm, clear_active_session)
    travel = json.dumps({"lines": [{"slot": 1, "raw": "We go to 32-C-UG-1"}]})
    run_tomb_gm("beat", "--actions", travel)
    actions = json.dumps(
        {
            "lines": [
                {"slot": 1, "raw": "We enter the breley-undercrypt."},
                {"slot": 2, "raw": "Move to ossuary-hall."},
            ]
        }
    )
    beat = run_tomb_gm("beat", "--actions", actions)
    assert beat["ok"] is True
    assert any(m.get("action") == "site_enter" for m in beat["mechanical_summary"])
    assert any(m.get("action") == "site_move" for m in beat["mechanical_summary"])


def test_beat_requires_session(run_tomb_gm, clear_active_session):
    run_tomb_gm("init")
    clear_active_session()
    actions = json.dumps({"lines": [{"slot": 1, "raw": "hello"}]})
    data = run_tomb_gm("beat", "--actions", actions, expect_ok=False)
    assert data["ok"] is False
    assert data["error"] == "NO_ACTIVE_SESSION"
