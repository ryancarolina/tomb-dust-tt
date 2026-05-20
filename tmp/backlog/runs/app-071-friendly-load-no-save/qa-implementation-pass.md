# QA PASS: Implementation

**Task:** APP-071-friendly-load-no-save  
**backlog_ticket:** APP-071  
**ticket_path:** tmp/backlog/app-071-friendly-load-game-when-no-save.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**Round:** 1 (implementation review)  
**Verdict:** **PASS**

## Diff scope reviewed

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | `_emit_recovery_narration`, `_is_mid_creation_resume_failure`, `_resume_failure_message`; resume failure branch wired |
| `app/tests/test_session_resume_failure.py` | T1 (variant A), T2 (variant B + no drift), T3 (`log_error` retention) |
| `tmp/app-session-persistence-spec.md` | § Resume failure, APP-071 checklist/changelog (spec sync with impl) |

**Not changed (per R5 / ticket):** `app/ui/app.py` — orchestrator return + footer only.

## Tests run

| Command | Result |
|---------|--------|
| `cd app && python -m pytest tests/test_session_resume_failure.py -v` | **3 passed** (0.63s) |
| `cd app && python -m pytest tests -q -k "session_resume or load_game"` | **3 passed**, 8 deselected |
| `cd app && python -m pytest tests -q` | **11 passed** (1.56s) |

## Ticket acceptance criteria

| AC | Status | Evidence |
|----|--------|----------|
| `load game` returns player-facing narration (not silent / terse engine string) | **PASS** | Failure branch builds `message`, `_emit_recovery_narration`, returns `message`; T1/T2 assert no `no save session found` in return |
| JSONL `error` retained; same text in `gm_narration` | **PASS** | `log_error("session_resume", …)` unchanged; T3 asserts context/error; T1/T2 monkeypatch `log_gm_narration` — last call equals return |
| Mid-creation vs cold copy distinguished | **PASS** | `_is_mid_creation_resume_failure` → variant B vs A; T2 asserts `finished save`/`unsaved`, step `race`, `[Awaiting: RACE_INPUT]` |
| APP-019 not bundled (`new game` toast unchanged) | **PASS** | `setup_new_game` failure path untouched (lines 495–499); scope limited to resume failure |

## Spec requirements (R0–R5)

| Req | Status | Evidence |
|-----|--------|----------|
| **R0** Ordered variant selection (B before A) | **PASS** | `_is_mid_creation_resume_failure`: `creation.active` → engine `CHARACTER_CREATION` + empty roster → `session_state.json` creation signals; `_resume_failure_message` branches on that |
| **R1** Drift-safe recovery emit + dual JSONL | **PASS** | `_emit_recovery_narration` = `log_gm_narration` only (no `_check_creation_drift`); failure path retains `log_error`; raw engine error not in return; T2 no `awaiting_mismatch` drift |
| **R2** Variant A copy + `[Awaiting: new game]` | **PASS** | Cold branch prose + footer; T1 asserts `no saved`, `new game`, footer |
| **R3** Variant B copy + `format_creation_status` footer | **PASS** | Finished-save wording, step in prose, `new game` in prose only; footer `[{format_creation_status}]` → `[Awaiting: RACE_INPUT]`; forbidden human tokens not in brackets |
| **R4** APP-019 alignment | **PASS** | Narration-only for resume failure; `setup_new_game` unchanged |
| **R5** No required UI edits | **PASS** | No `app/ui/app.py` diff |

## Automated test mapping (spec T1–T3)

| Spec case | Test | Result |
|-----------|------|--------|
| T1 — cold workspace, variant A | `test_load_game_no_save_variant_a` | **PASS** |
| T2 — mid-creation, no drift | `test_load_game_mid_creation_variant_b_no_drift` | **PASS** |
| T3 — `log_error` retained | `test_load_game_failure_retains_log_error` | **PASS** |

## Code review notes (non-blocking)

1. **R3 step prose:** Variant B uses `step.lower().replace("_", " ")` (e.g. `race`) rather than `CREATION_STATUS_LABELS` display strings — within spec allowance (“prose derived”); not exercised for steps like `ROLL_STATS` → `STATS_REVIEW`.
2. **R0 engine-only desync:** Variant B selected when engine reports `CHARACTER_CREATION` + empty roster but `creation.active` is false — prose uses `self.creation.step or "NAME"`; no automated test for that edge path (human TC-B / drift QA).
3. **Synonyms / regression:** `continue` / `resume` / `load` share the same `elif` branch (not individually pytest’d). Spec **T3c** (successful resume) not added in APP-071 file; full `app/tests` green — regression relies on existing suite, not new T3c.
4. **Manual smoke:** Spec TC-A/B/C and chip appearance still for Stage 7 human playtest (`human-test-plan.md`).

## Advisory (impl QA round 2 — optional hardening)

- Add pytest for engine-only mid-creation signal (`creation.active` false, mocked `bridge.status()`).
- Add `-k` or case for `continue` / `load` alias parity if drift QA wants belt-and-suspenders.

## Gate outcome

Implementation matches approved spec/plan, ticket AC, and domain spec § Resume failure. **Ready for:** drift check (`drift-check.md`), ticket `release APP-071 --done`, Stage 7 manual playtest.
