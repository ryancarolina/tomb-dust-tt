# QA PASS: plan

**Task:** APP-071-friendly-load-no-save  
**backlog_ticket:** APP-071  
**ticket_path:** tmp/backlog/app-071-friendly-load-game-when-no-save.md  
**Round:** 1  
**Reviewer role:** QA (adversarial, code-level)

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches plan (`tmp/app-session-persistence-spec.md`)
- [x] Acceptance criteria testable via plan tasks (R0–R5, T1–T3, manual TC-A/B/C)
- [x] Code traces match repo (independent verification below)
- [x] AGENTS.md / canon compliance (app-only; no engine eligibility changes)
- [x] Tests/commands listed; `conftest.py` orchestrator fixture + monkeypatch patterns exist
- [x] Plan files ⊆ ticket Expected files
- [x] registry_gap N/A at plan stage (spec PASS: `not_needed`)

## Independent code traces (round 1)

| Claim | Repo evidence | Result |
|-------|---------------|--------|
| Failure branch at 444–448 | `app/gm/orchestrator.py:444–448` — `session_resume()` → `log_error` → terse return; no `_emit_*` | **Match** |
| Resume before creation guard | Failure branch at 444–448; `if self.creation.active` at 494 — mid-creation hits failure first | **Match** |
| `_emit_narration` triggers drift | `_emit_narration` 286–288 → `log_gm_narration` + `_check_creation_drift` | **Match** |
| `_creation_drift_scope` | 189–199 — true when `creation.active` or engine `CHARACTER_CREATION` + empty roster | **Match** |
| Recovery emit must bypass drift | Plan `_emit_recovery_narration` = `log_gm_narration` only — aligns with spec R1 / qa-spec SPEC-001 fix | **Match** |
| Variant A footer allowed | Cold path: `_creation_drift_scope()` false → `[Awaiting: new game]` safe per spec R2 | **Match** |
| Variant B footer contract | `format_creation_status` (`creation.py:599–602`) → `Awaiting: {label}`; plan wraps in `[…]` for `_extract_suggestions` | **Match** |
| UI chip extraction | `app/ui/app.py:339–347` — regex `\[.*?Awaiting:\s*(.+?)\]` on return string; no orchestrator emit required for panel | **Match** |
| UI load ordering (documented) | `app/ui/app.py:281–282` queues `load_session` before `process_turn`; plan D1 defers reorder — spec non-goal | **Match** |
| App save path for R0 #2 | `_restore_history` 104–118 uses `Path(__file__).parents[1] / "session_state.json"` + `creation_state.active` | **Match** |
| Imports already present | `orchestrator.py:18,28` — `CREATION_STATUS_LABELS`, `format_creation_status` | **Match** |
| Test patterns | `conftest.py:74+` orchestrator fixture; `test_creation_flow.py:38–43` `log_creation_drift` monkeypatch | **Match** |
| Success path unchanged | 466–492 recap / `_creation_turn` resume — plan trace C; no planned edits | **Match** |

## Plan ↔ spec ↔ ticket mapping

| Ticket AC | Plan coverage |
|-----------|---------------|
| Player-facing narration; not silent | §2 failure branch + `_resume_failure_message`; `_emit_recovery_narration` |
| JSONL `error` retained; player-visible log | Retain `log_error("session_resume", …)` + `log_gm_narration` via recovery emit (T3) |
| Distinguish no save vs mid-creation | `_is_mid_creation_resume_failure` + variants A/B (R0); T1 vs T2 |
| APP-019 not bundled | No toast; `setup_new_game` unchanged; plan § D2 / risks |

| Spec requirement | Plan coverage |
|------------------|---------------|
| R0 ordered variant B first | `_is_mid_creation_resume_failure` three OR signals |
| R1 drift-safe recovery emit | `_emit_recovery_narration`; explicit no `_emit_narration` on failure |
| R2 variant A copy + footer | `_resume_failure_message` else branch; `[Awaiting: new game]` |
| R3 variant B copy + `format_creation_status` footer | Step label + prose-only `new game`; bracket footer |
| R4 APP-019 split | Out of scope table; no `setup_new_game` edit |
| R5 UI optional fallback | No required `app/ui/app.py`; documented fallback if chips fail manual QA |
| T1–T3 automated | `test_session_resume_failure.py` cases mapped |

## Scope gate

**Plan files ⊆ ticket Expected files:**

| Path | In plan | In ticket Expected files |
|------|---------|--------------------------|
| `app/gm/orchestrator.py` | Helpers + failure branch | ✓ |
| `app/tests/test_session_resume_failure.py` | New T1–T3 | ✓ |
| `tmp/app-session-persistence-spec.md` | Changelog / checklist on close | ✓ |
| `app/ui/app.py` | Explicit out of scope (fallback only) | ✓ optional |

No unauthorized paths. Engine (`play/tomb_gm/domain/session.py`), APP-064, APP-019 correctly excluded.

## Test plan adequacy

| Case | Plan | Adequate for AC |
|------|------|-----------------|
| T1 cold `load game` | Variant A keywords + `log_gm_narration` once | ✓ |
| T2 mid-creation `load game` | After `new game` → `Dumpy`; no `awaiting_mismatch` drift | ✓ |
| T3 error retention | `log_error` with `session_resume` context | ✓ |
| Success regression | Manual TC-C; `test_creation_flow.py -q` green — no automated T3c in plan | ✓ (non-blocking gap — see notes) |

Commands and `-k "session_resume or load_game"` filter align with domain spec § Tests APP-071.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-071 `in_progress`; domain spec linked |
| Plan ⊆ Expected files | **PASS** | Three required paths; UI optional only |
| Code-path accuracy | **PASS** | Failure branch, emit/drift, UI chips verified independently |
| Spec alignment | **PASS** | R0–R5 and qa-spec-pass round 2 resolutions reflected |
| Test commands | **PASS** | T1–T3 + regression trio sufficient for scope |
| Scope / non-goals | **PASS** | Matches spec, ticket, research |
| Drift / logging contract | **PASS** | Recovery emit bypasses `_check_creation_drift` |

## Notes (non-blocking — impl / close)

- **Spec R1 “appends to narration history”:** Plan omits `self.history` append; `_emit_narration` also does not append history (append happens in `_creation_turn` / exploration paths). UI panel uses `process_turn` return via `narration_text` queue (`app/ui/app.py:297`). Impl should follow plan (JSONL + return string); clarify domain spec wording on close if needed.
- **Domain T3c vs plan T1–T3:** Domain spec lists automated resume-success regression (T3c); plan relies on manual TC-C + unchanged success-path code. Acceptable for APP-071 close; add T3c only if impl agent wants extra safety.
- **R0 signal #2 (app save file):** Fuzziest predicate; T2 covers primary path (`creation.active` after `new game` → name). File signal is desync fallback — impl should unit-test signal #1+#3 first.
- **Variant B step label:** Plan allows `CREATION_STATUS_LABELS` or `format_creation_status` — impl must ensure footer bracket token matches `format_creation_status(self.creation)` exactly (spec R3 AC).

**Verdict:** **PASS** — ready for Stage 4 (workstreams + implementation).
