# QA Report: Implementation

**Task:** APP-066-sync-engine-awaiting-with-creation-step  
**backlog_ticket:** APP-066  
**ticket_path:** tmp/backlog/app-066-sync-engine-awaiting-with-creation-step.md  
**Round:** 1  
**Verdict:** FAIL

## Summary

Run artifacts (`reflection-dev-impl-WS1.md`, `reflection-dev-impl-WS2.md`) describe the label-based drift comparator and golden-path `drift_events == []` assert, but the **working tree does not contain those changes**. `_check_creation_drift` still compares narrated `Awaiting:` to engine `CHARACTER_CREATION`, which is the pre-APP-066 bug. Domain specs document the target contract (PM draft); implementation is missing.

**Blocker count:** 2 (WS1 not landed; WS2 not landed)

---

## Tests run

| Command | Result |
|---------|--------|
| `python -m pytest app/tests/test_creation_flow.py -q` (repo root) | **pass** — 2 passed in ~0.8s (does not exercise APP-066 behavior) |
| `python -m pytest play/tomb_gm/tests/test_campaign_session.py -q` | **pass** — 1 passed in ~1.2s |

**Note:** First pytest invocation from repo root briefly hit `ImportError: format_roll_stats_table` (orchestrator import vs `creation.py`); subsequent runs green. No test currently fails on false `creation_drift` because WS2 assert is absent.

---

## Ticket AC → code + tests

| Ticket AC | Expected (spec/plan) | On disk | Result |
|-----------|----------------------|---------|--------|
| Engine awaiting reflects step **or** label-based drift compare | When `creation.active`, compare to `CREATION_STATUS_LABELS[step]` | `orchestrator.py` L202–203: `narrated_awaiting != engine_awaiting` for any scope turn with `Awaiting:` | **FAIL** |
| No `creation_drift` every healthy creation turn | Golden path: footer matches step, engine stays `CHARACTER_CREATION` | Old compare still flags `awaiting_mismatch` each turn | **FAIL** (behavior) |
| Domain spec documents engine vs narration contract | § Awaiting contract in `tmp/app-character-creation-spec.md` | Present (draft, 2026-05-20) | **PASS** (docs only) |
| Optional `test_creation_flow.py` no-drift assert | `drift_events == []` monkeypatch | Not in `test_creation_flow.py` | **FAIL** (optional AC; planned WS2) |

---

## Spec R1–R6 → implementation

| Req | Status | Evidence |
|-----|--------|----------|
| **R1** Two-layer contract documented | **PASS** (spec) | `tmp/app-character-creation-spec.md` L150–163; `tmp/app-logging-qa-spec.md` § `creation_drift` |
| **R2** Compare narrated awaiting to `CREATION_STATUS_LABELS[step]` when `creation.active` | **FAIL** | No `CREATION_STATUS_LABELS` import; no `_expected_creation_awaiting_label()`; L202–203 use `engine_awaiting` |
| **R2** Resume edge: skip awaiting when not `creation.active` | **FAIL** | L202 runs for any `narrated_awaiting` in scope, including resume edge |
| **R3** Phase drift during desk creation | **PASS** (unchanged) | `phase_mismatch` only when both phases present (L204–205); `premature_exploration_phase` guard L206–207 |
| **R4** `_creation_drift_scope` unchanged | **PASS** | L172–182 matches plan |
| **R5** Optional `expected_awaiting` in payload | **FAIL** | Payload L212–221 has no `expected_awaiting` |
| **R6** `test_creation_flow.py` green + optional drift assert | **PARTIAL** | Pytest green; no drift collector / assert |

---

## Findings

### IMPL-001 — blocker (WS1 not implemented)

**File:** `app/gm/orchestrator.py` (`_check_creation_drift`, ~L184–221)

**Expected (plan §3, spec R2):**

```python
if self.creation.active and narrated_awaiting:
    expected_awaiting = self._expected_creation_awaiting_label()
    if narrated_awaiting != expected_awaiting:
        reasons.append("awaiting_mismatch")
# resume edge: not creation.active → no awaiting compare
```

**Actual:**

```python
engine_awaiting = str(status.get("awaiting") or "").strip().upper()
# ...
if narrated_awaiting and narrated_awaiting != engine_awaiting:
    reasons.append("awaiting_mismatch")
```

**Impact:** Every healthy creation turn with a granular footer (`SKILLS_INPUT`, etc.) while engine `awaiting` is `CHARACTER_CREATION` still logs `creation_drift` with `awaiting_mismatch` — the original APP-066 bug.

**Also missing:** `CREATION_STATUS_LABELS` import (plan §1), `_expected_creation_awaiting_label()` helper (plan §2).

---

### IMPL-002 — blocker (WS2 not implemented)

**File:** `app/tests/test_creation_flow.py`

**Expected (plan §7):** Monkeypatch `gm.orchestrator.log_creation_drift`; after `INPUTS` loop, `assert drift_events == []`.

**Actual:** No `drift_events` list; no monkeypatch; git diff vs `HEAD` only shows APP-068 name→race assertions and `test_name_advance_presents_race_table`.

**Impact:** Regression lock for APP-066 absent; pytest green does not prove drift silence.

---

### IMPL-003 — non-blocker (release hygiene)

- Domain spec changelog has **APP-066 spec draft** only — no **done** row for implemented drift compare (acceptable at impl QA if ticket still open; required before `release --done`).
- `status.md` checklist: WS1/WS2 marked complete in narrative elsewhere but code contradicts — update after re-impl.

---

### IMPL-004 — non-blocker (scope noise)

`git diff HEAD` on `orchestrator.py` / `test_creation_flow.py` includes **APP-068** name→race changes, not APP-066. Batch mixing increases risk of lost WS1 edits (observed).

---

## Dev artifacts vs workspace

| Artifact | Claims | Workspace |
|----------|--------|-----------|
| `reflection-dev-impl-WS1.md` | Label compare shipped | **Not present** in `orchestrator.py` |
| `reflection-dev-impl-WS2.md` | `drift_events == []` assert | **Not present** in `test_creation_flow.py` |

Treat dev reflections as **intent only** until code matches.

---

## Re-test after fix

```bash
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest play/tomb_gm/tests/test_campaign_session.py -q
```

**Manual:** `new game` through creation; grep `app/logs/session-*.jsonl` — no `creation_drift` with `awaiting_mismatch` when footer matches `creation.step`.

**Negative probe (optional):** `_check_creation_drift` with `step=SKILLS`, narration `Awaiting: CLASS_INPUT` → `awaiting_mismatch` + `expected_awaiting: SKILLS_INPUT`.

---

## Handoff

**Return to Dev (WS1 then WS2)** per `workstreams.md`. Re-run implementation QA round 1 after `orchestrator.py` and test assert land and match `spec.md` / `plan.md`.
