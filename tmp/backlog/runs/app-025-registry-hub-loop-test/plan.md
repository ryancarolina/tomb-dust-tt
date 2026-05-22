# Implementation Plan: APP-025-registry-hub-loop-test

**Status:** draft  
**backlog_ticket:** APP-025  
**ticket_path:** tmp/backlog/app-025-registry-hub-loop-integration-test.md  
**domain_spec:** tmp/app-exploration-delve-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Add a **bridge-direct** integration test module — **no LLM mocks, no orchestrator** — that walks the canonical Registry hub extraction loop at **Breley Keep (`32-C`)** via the same `GameBridge` APIs the orchestrator dispatches.

**Single new file:** `app/tests/test_registry_hub_loop.py` with local helpers for session bootstrap, party assertions, and **`events` audit (T3)**. No production code changes expected unless pytest reveals a bridge/FSM bug (fix under same ticket + spec changelog note).

**Test strategy:**

| Layer | Choice |
|-------|--------|
| Fixture | `bridge` from `conftest.py` (`isolated_workspace` / `tmp_path`) |
| Bootstrap | `_ensure_salt_road_session(bridge)` — copy pattern from `test_combat_monster_validation.py` |
| Entry site | T1/T3/T4/T5: `32-C-UG-1`; T2: `"undercrypt"` |
| Ingress proof | T3 queries `events` via `bridge.ctx.conn` — not observable mid-call on `status()` |
| Failure isolation | T1 full loop; T2–T5 separate functions (spec preference) |

**Out of scope:** orchestrator mocks, creation bootstrap, registry stamp, surface travel (APP-023), optional R3 sub-test (`set_phase("extract")` while still `mode=dungeon`).

---

## Code-path traces (planned test execution)

### Flow A — Full hub loop (T1: S0→S3)

| Step | File:symbol | Action | Assert |
|------|-------------|--------|--------|
| 1 | `conftest.py:bridge` | `GameBridge(workspace=isolated_workspace).init()` | — |
| 2 | `test_registry_hub_loop.py:_ensure_salt_road_session` | `campaign_new("salt-road", …)` tolerate `already exists`; `session_start("salt-road")` | both `ok` |
| 3 | `bridge.status()` | S0 — preparation | `party.address=="32-C"`, `mode=="surface"`, `phase=="preparation"` |
| 4 | `bridge.enter_dungeon(site_address="32-C-UG-1")` | S1 — ingress + delve inside call | `ok`; `party.phase=="delve"`, `mode=="dungeon"`, `site_id=="32-C-UG-1"` |
| 5 | `bridge.exit_dungeon()` | S2 — exit site | `ok`; `mode=="surface"`, `site_id` null/absent; **`phase=="delve"`** |
| 6 | `bridge.set_phase("extract")` | S3 — extract | `ok`; `party.phase=="extract"`, `mode=="surface"` |

**Engine path under S1** (no direct test calls):

1. `bridge.enter_dungeon` → `resolve_site_address` → `ExplorationService.enter_site` (`mode=dungeon`)
2. `advance_phase_for_dungeon_entry` → `set_phase(ingress)` → `set_phase(delve)` with `log_event(..., "phase.set", {from, to})`

### Flow B — Friendly slug (T2)

Same bootstrap as Flow A; call `enter_dungeon("undercrypt")`. Assert `ok`, `site_id=="32-C-UG-1"`, `mode=="dungeon"`, `phase=="delve"`. Optionally assert `result.get("resolved_from") == "undercrypt"` when bridge returns it.

### Flow C — Events audit (T3)

| Step | Action |
|------|--------|
| 1 | Bootstrap + record `max_event_id = _max_event_id(conn, session_id)` |
| 2 | `enter_dungeon("32-C-UG-1")` |
| 3 | `_phase_set_transitions(conn, session_id, after_id=max_event_id)` |
| 4 | Assert ordered pairs `== [("preparation", "ingress"), ("ingress", "delve")]` |

**Why `after_id` filter:** Later `set_phase("extract")` in T1/T5 also logs `phase.set`; T3 must not depend on full-table scan or test order pollution.

### Flow D — Exit vs extract (T4, T5)

| Test | Setup | Call | Assert |
|------|-------|------|--------|
| T4 | Bootstrap + `enter_dungeon` | `exit_dungeon()` | surface mode; phase still `delve` |
| T5 | Bootstrap + `enter_dungeon` + `exit_dungeon` | `set_phase("extract")` | `ok`; `phase=="extract"` |

Shared fixture helper `_bootstrap_delve_on_surface(bridge)` runs bootstrap → enter → exit and returns `(bridge, party)` for T5 (T4 stops before exit assert reuse).

### Flow E — Paths **not** exercised (guardrails)

| Anti-pattern | Why excluded |
|--------------|--------------|
| `bridge.site_enter` | `mode=site` CLI graph — not app dungeon path |
| `set_phase("delve")` from `preparation` | Illegal FSM (APP-022) |
| `world_travel("32-C-UG-1")` | APP-023 `USE_ENTER_DUNGEON` |

---

## Task breakdown

### 1. Module scaffold — `app/tests/test_registry_hub_loop.py` (new)

```python
"""APP-025: Registry hub loop integration test (T1–T5)."""
from __future__ import annotations

import json

import pytest
```

Docstring cites ticket + bridge-direct policy. No imports from orchestrator or mock LLM helpers.

---

### 2. Session bootstrap — `_ensure_salt_road_session(bridge) -> None`

Copy verbatim pattern from `test_combat_monster_validation.py`:

```python
def _ensure_salt_road_session(bridge) -> None:
    result = bridge.campaign_new("salt-road", "Salt Road")
    assert result.get("ok") or "already exists" in str(result.get("error", ""))
    start = bridge.session_start("salt-road")
    assert start.get("ok")
```

**Optional pytest fixture** (local to module):

```python
@pytest.fixture
def bridge_with_session(bridge):
    _ensure_salt_road_session(bridge)
    return bridge
```

Use `bridge_with_session` in T2–T5; T1 may call helper inline or use same fixture.

**S0 assertion helper:**

```python
def _assert_preparation_at_breley(party: dict) -> None:
    assert party["address"] == "32-C"
    assert party["mode"] == "surface"
    assert party["phase"] == "preparation"
```

Call after bootstrap in every test.

---

### 3. Party / site_id helpers

SQLite may return `None` for cleared `site_id`. Normalize for assertions:

```python
def _normalized_site_id(party: dict) -> str | None:
    raw = party.get("site_id")
    if raw in (None, ""):
        return None
    return str(raw)
```

```python
def _active_session_id(bridge) -> str:
    active = bridge.status().get("active") or {}
    session_id = active.get("session_id")
    assert session_id, "expected active session_id from bridge.status()"
    return str(session_id)
```

---

### 4. T3 events helpers (QA-spec contract)

Pin SQL, session id source, ordering, and scope filter per qa-spec-pass adversarial note 1.

#### 4.1 `_max_event_id(conn, session_id: str) -> int`

```python
def _max_event_id(conn, session_id: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(id), 0) AS m FROM events WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return int(row["m"])
```

Call **after bootstrap, before `enter_dungeon`**, so bootstrap noise (if any) is excluded together with later extract transitions.

#### 4.2 `_phase_set_transitions(conn, session_id: str, *, after_id: int = 0) -> list[tuple[str, str]]`

```python
def _phase_set_transitions(conn, session_id: str, *, after_id: int = 0) -> list[tuple[str, str]]:
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
```

**Contract:**

| Field | Source |
|-------|--------|
| Connection | `bridge.ctx.conn` (same as `test_setup_new_game_lifecycle.py`) |
| Session id | `_active_session_id(bridge)` → typically `"current"` |
| Payload | `json.loads(row["payload_json"])` — keys `from`, `to` per `extraction.py:log_event` |
| Order | `ORDER BY id ASC` on filtered rows |
| Scope | `id > after_id` where `after_id = _max_event_id(...)` captured pre-`enter_dungeon` |

#### 4.3 `_assert_ingress_phase_audit(bridge) -> None`

Convenience wrapper for T3 (and optional inline check in T1):

```python
def _assert_ingress_phase_audit(bridge) -> None:
    conn = bridge.ctx.conn
    session_id = _active_session_id(bridge)
    transitions = _phase_set_transitions(conn, session_id, after_id=0)
    # Caller must pass after_id from snapshot; inline in test:
    # after_id = _max_event_id(conn, session_id)
    # assert _phase_set_transitions(conn, session_id, after_id=after_id) == [
    #     ("preparation", "ingress"),
    #     ("ingress", "delve"),
    # ]
```

**T3 test body (canonical):**

```python
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
```

Do **not** run T3 after `exit_dungeon` or `set_phase("extract")` in the same function.

---

### 5. Composite setup helper (T4/T5)

```python
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
```

T4: bootstrap → enter only → `exit_dungeon` → assert (subset of above).  
T5: `_bootstrap_delve_on_surface` → `set_phase("extract")`.

---

### 6. Test matrix (T1–T5)

| ID | Test name | Setup | Pass criteria |
|----|-----------|-------|---------------|
| **T1** | `test_registry_hub_loop_preparation_through_extract` | `_ensure_salt_road_session`; S0 assert | Full S0→S3 with `enter_dungeon("32-C-UG-1")`; every step `ok`; final `phase=="extract"`, `mode=="surface"`, `site_id` cleared |
| **T2** | `test_enter_dungeon_resolves_undercrypt_from_breley` | `bridge_with_session` | `enter_dungeon("undercrypt")` → `ok`; `site_id=="32-C-UG-1"`, `mode=="dungeon"`, `phase=="delve"`; optional `resolved_from=="undercrypt"` |
| **T3** | `test_enter_dungeon_logs_ingress_phase_transitions` | `bridge_with_session` + `after_id` snapshot | `_phase_set_transitions` == preparation→ingress, ingress→delve (see §4.3) |
| **T4** | `test_exit_dungeon_keeps_delve_phase` | bootstrap + enter | `exit_dungeon` → `mode=="surface"`, `_normalized_site_id(party) is None`, **`phase=="delve"`** |
| **T5** | `test_set_phase_extract_from_delve` | `_bootstrap_delve_on_surface` | `set_phase("extract")` → `ok`, `phase=="extract"` |

**T1 vs T3–T5:** T1 may omit inline events assert (T3 owns R2). Do not merge T4/T5 into T1 only — keep separate functions per spec.

**Optional (non-blocking, not ticket AC):** `test_set_phase_extract_while_still_in_dungeon` — enter only, `set_phase("extract")` without exit; documents R3 optional sub-test. Skip unless impl wants extra coverage; do not replace T1 ordering.

---

### 7. Acceptance criteria checklist (ticket → tests)

| Ticket AC | Test / artifact |
|-----------|-----------------|
| Bridge-direct loop: `32-C` / `preparation` → `enter_dungeon` → `exit_dungeon` → `set_phase("extract")` | **T1** |
| After entry: `mode=dungeon`, `phase=delve` | **T1**, **T2** |
| After exit: `mode=surface`, `phase=delve` | **T1**, **T4** |
| After `set_phase`: `phase=extract` | **T1**, **T5** |
| `events` `phase.set`: preparation→ingress→delve during `enter_dungeon` | **T3** (+ helpers §4) |
| Domain spec § APP-025 synced; changelog on close | Close task — not impl file |

---

### 8. Domain spec sync on close — `tmp/app-exploration-delve-spec.md`

On `release APP-025 --done` (Expected file — close-time only):

1. Mark checklist item `[x]` for APP-025.
2. Add changelog row: APP-025 done — `test_registry_hub_loop.py` T1–T5.
3. Add `app/tests/test_registry_hub_loop.py` to § File map (qa-spec-pass note 2).

No change during impl unless spec drift discovered.

---

## Requirements → implementation map

| ID | Requirement | Locus | Test |
|----|-------------|-------|------|
| **R1** | Bridge-direct S0–S3 loop | `test_registry_hub_loop.py` | T1 |
| **R1** | Friendly `undercrypt` resolution | same | T2 |
| **R2** | Ingress via `events` audit | `_phase_set_transitions`, `_max_event_id` | T3 |
| **R3** | `exit_dungeon` ≠ `extract` | assertions on phase after exit | T1, T4 |
| **R3** | `set_phase("extract")` from `delve` | `set_phase` call | T1, T5 |
| **R4** | Module + fixtures policy | module docstring, `conftest` `bridge` | all |
| **R5** | Test-only; no prod change unless bug | — | green pytest |

---

## Files (must ⊆ ticket Expected files)

| File | Changes |
|------|---------|
| `app/tests/test_registry_hub_loop.py` | **New** — helpers §2–5; tests T1–T5 |

**Close-time only (not impl commit scope unless same release):**

| File | Changes |
|------|---------|
| `tmp/app-exploration-delve-spec.md` | Checklist `[x]`, changelog, file map row |

**Explicitly not touched:**

- `app/gm/bridge.py`, `play/tomb_gm/services/*` (unless bugfix)
- `app/tests/conftest.py` — reuse existing `bridge` fixture; no shared helper extraction to `helpers.py` unless APP-051 later requests it

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| New module | `python -m pytest app/tests/test_registry_hub_loop.py -q` | 5 passed |
| Regression — phase FSM | `python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_advance_phase_for_dungeon_entry -q` | pass |
| Regression — illegal delve | `python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_set_phase_rejects_preparation_to_delve -q` | pass |
| Regression — APP-022 hints | `python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q` | pass |
| Gate | `python -m pytest app/tests -q` | all green |

Run from repo root or `cd app && python -m pytest tests/test_registry_hub_loop.py -q`.

---

## Rollback

Delete `app/tests/test_registry_hub_loop.py`. No feature flags or production rollback.

---

## Open questions

- **None blocking.** Live probe (research-brief) confirms loop works without roster.
- **`impl-check APP-025`:** Run before editing `app/tests/` (`python tmp/backlog/claim_ticket.py impl-check APP-025`).
- **Optional R3 sub-test:** Defer unless impl pass has spare time; must not alter T1 step order (exit before extract).
