# Drift Check: APP-071-friendly-load-no-save

**backlog_ticket:** APP-071  
**Verdict:** **PASS**

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § Resume failure — `load game` with no engine save (APP-071) | no | Variant table, emit path, drift/logging notes match `orchestrator.py`; checklist `[x]` APP-071; changelog **APP-071 done** row present |
| Run `spec.md` R0–R5, T1–T3 | no | Verified against `app/gm/orchestrator.py`, `app/tests/test_session_resume_failure.py` |
| [`tmp/backlog/app-071-friendly-load-game-when-no-save.md`](../../app-071-friendly-load-game-when-no-save.md) | no | AC checked in ticket file (drift stage); **Status** remains `in_progress` — no `release` |

## Code ↔ domain spec (APP-071)

| Requirement | Code | Match |
|-------------|------|-------|
| Commands `load game`, `load`, `continue`, `resume` → `session_resume()` | `process_turn` L502–508 | yes |
| Variant selection: mid-creation signals **before** cold (B then A) | `_is_mid_creation_resume_failure` L294–321: `creation.active` → engine `CHARACTER_CREATION` + empty roster → `session_state.json` creation signals | yes |
| Variant A: no saved game + `new game` hint; footer `[Awaiting: new game]` | `_resume_failure_message` L341–346 | yes |
| Variant B: finished-save wording, step in prose, `new game` wipe warn; `format_creation_status` footer | L328–339 | yes |
| Engine `no save session found` not shown verbatim to player | L325–326 normalize; tests assert absent from return | yes |
| `log_error("session_resume", …)` retained | L505; `test_load_game_failure_retains_log_error` | yes |
| Recovery emit: `_emit_recovery_narration` → `log_gm_narration` only (no `_check_creation_drift`) | L290–292, L507; T2 no `awaiting_mismatch` drift | yes |
| Success path unchanged (`_emit_narration`, recap/creation resume) | L509+ branch untouched by failure helpers | yes |
| APP-019 scope: `setup_new_game` failure path unchanged | L495–499 | yes |
| APP-071 does not require `app/ui/app.py` changes | No diff in expected scope | yes |

## Ticket AC ↔ code

| Acceptance criterion | Result |
|----------------------|--------|
| `process_turn("load game")` returns player-facing narration (not silent / terse engine string) | **PASS** |
| JSONL `error` retained; same text in `gm_narration` | **PASS** (`log_error` + `_emit_recovery_narration` / `log_gm_narration`) |
| Mid-creation vs cold copy distinguished | **PASS** (variant B vs A; T2) |
| APP-019 not bundled (`new game` toast unchanged) | **PASS** |

**Note:** Ticket AC optional `log_player_message` — helper does not exist in codebase; spec/run spec use `log_gm_narration` via recovery emit instead. No drift.

## Tests ↔ domain spec § Tests APP-071

| Spec ID | Test | Result |
|---------|------|--------|
| **T3a** | `test_load_game_no_save_variant_a` | **PASS** |
| **T3b** | `test_load_game_mid_creation_variant_b_no_drift` | **PASS** |
| **T3c** | _(not in APP-071 file)_ | **deferred** — successful resume regression not added; full `app/tests` green; manual TC-C / Stage 7 |

```bash
cd app && python -m pytest tests/test_session_resume_failure.py -v
cd app && python -m pytest tests -q -k "session_resume or load_game"
```

**Result:** 3 passed (0.80s); 3 passed, 8 deselected (0.82s)

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec § Resume failure + changelog aligned with code
- [ ] Ticket **Status** → `done` / **Closed** date — orchestrator at `release APP-071 --done`
- [ ] `python tmp/backlog/claim_ticket.py release APP-071 --done` — orchestrator (not QA drift agent)

## Ancillary notes (non-blocking)

1. **Alias commands:** `continue` / `resume` / `load` share the failure branch but are not individually pytest’d — acceptable; same code path as `load game`.
2. **Engine-only mid-creation:** Variant B when `creation.active` false but engine `CHARACTER_CREATION` + empty roster — implemented (R0 desync) but no dedicated automated test; human TC-B / optional hardening per impl QA.
3. **T3c:** Spec lists successful-resume regression case; not in `test_session_resume_failure.py` — coverage gap vs spec test table only, not code↔spec behavior drift.
4. Domain spec header **Status: In progress** reflects broader session backlog (APP-014–APP-020), not APP-071 regression.
