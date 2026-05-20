# QA PASS: Implementation

**Task:** APP-066-sync-engine-awaiting-with-creation-step  
**backlog_ticket:** APP-066  
**Round:** 2  
**Verdict:** **PASS**

## Summary

Round 1 blockers are **cleared on disk**. `orchestrator.py` compares narrated `Awaiting:` to `CREATION_STATUS_LABELS[creation.step]` when `creation.active`; `test_creation_flow.py` locks golden-path drift silence via `drift_events == []`. Mandated pytest green.

**Blocker count:** 0

---

## Round 1 follow-up (on disk)

| Finding | Round 2 status |
|---------|----------------|
| IMPL-001 — label-based drift compare missing | **Resolved** — `CREATION_STATUS_LABELS` import (L18), `_expected_creation_awaiting_label()` (L174–178), compare only when `creation.active` (L210–213); no `engine_awaiting` compare |
| IMPL-002 — `drift_events == []` assert missing | **Resolved** — `test_full_creation_apprentice_caster` L39–43, L81 |

---

## Tests run

| Command | Result |
|---------|--------|
| `python -m pytest app/tests/test_creation_flow.py -q` (repo root) | **pass** — 2 passed in 0.70s |
| `python -m pytest play/tomb_gm/tests/test_campaign_session.py -q` | **pass** — 1 passed in 1.09s |

Golden-path integration test monkeypatches `log_creation_drift` and asserts zero events through full creation FSM.

---

## Ticket AC → code + tests

| Ticket AC | On disk | Result |
|-----------|---------|--------|
| Label-based drift compare (not engine `CHARACTER_CREATION`) | `_check_creation_drift` L210–213; `expected_awaiting` in payload L232–233 | **PASS** |
| No `creation_drift` every healthy creation turn | Match path returns early (L219–220); test `drift_events == []` | **PASS** |
| Domain spec documents engine vs narration contract | `tmp/app-character-creation-spec.md` § Awaiting contract; `tmp/app-logging-qa-spec.md` § `creation_drift` | **PASS** |
| Optional golden-path no-drift assert | `test_creation_flow.py` L39–43, L81 | **PASS** |

---

## Spec R1–R6 → implementation

| Req | Status | Evidence |
|-----|--------|----------|
| **R1** Two-layer contract documented | **PASS** | Domain specs (draft + behavior bullets) |
| **R2** Compare to `CREATION_STATUS_LABELS[step]` when `creation.active` | **PASS** | L210–213; helper L174–178 |
| **R2** Resume edge: skip awaiting when not `creation.active` | **PASS** | Awaiting compare gated on `self.creation.active` |
| **R3** Phase drift during desk creation | **PASS** | `phase_mismatch` only when both phases present (L214–215); premature explore guard L216–217 |
| **R4** `_creation_drift_scope` unchanged | **PASS** | L180–190 |
| **R5** Optional `expected_awaiting` in payload | **PASS** | L232–233 when awaiting compare runs |
| **R6** Pytest green + drift assert | **PASS** | 2/2 creation flow tests; drift collector |

---

## Code verification (disk)

**`app/gm/orchestrator.py`**

- Import `CREATION_STATUS_LABELS` from `gm.creation` (L18).
- `_expected_creation_awaiting_label()` uses map + `{step}_INPUT` fallback (L174–178).
- `awaiting_mismatch` only when `creation.active` and `narrated_awaiting != expected_awaiting` (L210–213).
- Engine `status["awaiting"]` retained in payload for QA grep, not used for mismatch (L225).

**`app/tests/test_creation_flow.py`**

- `drift_events` list + monkeypatch on `log_creation_drift` (L39–43).
- `assert drift_events == []` after full `INPUTS` loop (L81).

---

## Non-blocking (release stage)

- Domain spec changelogs still **APP-066 spec draft** rows only — add **done** entry at `release --done`.
- Ticket checkboxes / `status.md` Stage 6–7 — after drift check + human playtest.
- Manual JSONL golden-path grep not run in this round (pytest lock sufficient for impl QA).

---

## Handoff

**Ready for:** Drift check, `release APP-066 --done`, spec changelog sync, human playtest per `spec.md` § Human playtest hints.
