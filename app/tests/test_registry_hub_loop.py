"""APP-025: Registry hub loop integration test (T1–T5).

Bridge-direct integration — no LLM mocks, no orchestrator. Exercises the
canonical Breley Keep (32-C) preparation → ingress → delve → extract loop via
GameBridge APIs the orchestrator dispatches.
"""

from __future__ import annotations

import json

import pytest


def _ensure_salt_road_session(bridge) -> None:
    result = bridge.campaign_new("salt-road", "Salt Road")
    assert result.get("ok") or "already exists" in str(result.get("error", ""))
    start = bridge.session_start("salt-road")
    assert start.get("ok")


@pytest.fixture
def bridge_with_session(bridge):
    _ensure_salt_road_session(bridge)
    return bridge


def _assert_preparation_at_breley(party: dict) -> None:
    assert party["address"] == "32-C"
    assert party["mode"] == "surface"
    assert party["phase"] == "preparation"


def _normalized_site_id(party: dict) -> str | None:
    raw = party.get("site_id")
    if raw in (None, ""):
        return None
    return str(raw)


def _active_session_id(bridge) -> str:
    active = bridge.status().get("active") or {}
    session_id = active.get("session_id")
    assert session_id, "expected active session_id from bridge.status()"
    return str(session_id)


def _max_event_id(conn, session_id: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(id), 0) AS m FROM events WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return int(row["m"])


def _phase_set_transitions(
    conn, session_id: str, *, after_id: int = 0
) -> list[tuple[str, str]]:
    rows = conn.execute(
        "SELECT payload_json FROM events "
        "WHERE session_id = ? AND type = 'phase.set' AND id > ? "
        "ORDER BY id ASC",
        (session_id, after_id),
    ).fetchall()
    out: list[tuple[str, str]] = []
    for row in rows:
        payload = json.loads(row["payload_json"] or "{}")
        out.append((str(payload.get("from", "")), str(payload.get("to", ""))))
    return out


def _bootstrap_delve_on_surface(bridge) -> dict:
    """After enter + exit: surface mode, phase still delve."""
    _ensure_salt_road_session(bridge)
    party = bridge.status()["party"]
    _assert_preparation_at_breley(party)

    enter = bridge.enter_dungeon(site_address="32-C-UG-1")
    assert enter.get("ok") is True
    party = bridge.status()["party"]
    assert party["phase"] == "delve"
    assert party["mode"] == "dungeon"
    assert party["site_id"] == "32-C-UG-1"

    exit_result = bridge.exit_dungeon()
    assert exit_result.get("ok") is True
    party = bridge.status()["party"]
    assert party["mode"] == "surface"
    assert party["phase"] == "delve"
    assert _normalized_site_id(party) is None
    return party


# --- T1: full hub loop S0→S3 ---


def test_registry_hub_loop_preparation_through_extract(bridge):
    _ensure_salt_road_session(bridge)
    party = bridge.status()["party"]
    _assert_preparation_at_breley(party)

    enter = bridge.enter_dungeon(site_address="32-C-UG-1")
    assert enter.get("ok") is True
    party = bridge.status()["party"]
    assert party["phase"] == "delve"
    assert party["mode"] == "dungeon"
    assert party["site_id"] == "32-C-UG-1"

    exit_result = bridge.exit_dungeon()
    assert exit_result.get("ok") is True
    party = bridge.status()["party"]
    assert party["mode"] == "surface"
    assert party["phase"] == "delve"
    assert _normalized_site_id(party) is None

    extract = bridge.set_phase("extract")
    assert extract.get("ok") is True
    party = bridge.status()["party"]
    assert party["phase"] == "extract"
    assert party["mode"] == "surface"
    assert _normalized_site_id(party) is None


# --- T2: friendly undercrypt slug ---


def test_enter_dungeon_resolves_undercrypt_from_breley(bridge_with_session):
    bridge = bridge_with_session
    _assert_preparation_at_breley(bridge.status()["party"])

    result = bridge.enter_dungeon("undercrypt")
    assert result.get("ok") is True
    if "resolved_from" in result:
        assert result["resolved_from"] == "undercrypt"

    party = bridge.status()["party"]
    assert party["site_id"] == "32-C-UG-1"
    assert party["mode"] == "dungeon"
    assert party["phase"] == "delve"


# --- T3: ingress phase.set events audit ---


def test_enter_dungeon_logs_ingress_phase_transitions(bridge_with_session):
    bridge = bridge_with_session
    _assert_preparation_at_breley(bridge.status()["party"])
    conn = bridge.ctx.conn
    session_id = _active_session_id(bridge)
    after_id = _max_event_id(conn, session_id)

    result = bridge.enter_dungeon(site_address="32-C-UG-1")
    assert result.get("ok") is True

    transitions = _phase_set_transitions(conn, session_id, after_id=after_id)
    assert transitions == [("preparation", "ingress"), ("ingress", "delve")]


# --- T4: exit_dungeon keeps delve phase ---


def test_exit_dungeon_keeps_delve_phase(bridge_with_session):
    bridge = bridge_with_session
    _assert_preparation_at_breley(bridge.status()["party"])

    enter = bridge.enter_dungeon(site_address="32-C-UG-1")
    assert enter.get("ok") is True
    party = bridge.status()["party"]
    assert party["phase"] == "delve"
    assert party["mode"] == "dungeon"

    exit_result = bridge.exit_dungeon()
    assert exit_result.get("ok") is True
    party = bridge.status()["party"]
    assert party["mode"] == "surface"
    assert party["phase"] == "delve"
    assert _normalized_site_id(party) is None


# --- T5: set_phase extract from delve on surface ---


def test_set_phase_extract_from_delve(bridge):
    _bootstrap_delve_on_surface(bridge)

    extract = bridge.set_phase("extract")
    assert extract.get("ok") is True
    party = bridge.status()["party"]
    assert party["phase"] == "extract"
    assert party["mode"] == "surface"
