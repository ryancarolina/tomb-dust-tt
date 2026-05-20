# QA PASS: spec

**Task:** APP-066-sync-engine-awaiting-with-creation-step  
**backlog_ticket:** APP-066  
**ticket_path:** tmp/backlog/app-066-sync-engine-awaiting-with-creation-step.md  
**Round:** 1  
**domain_spec_creation:** not_needed

**Verdict:** PASS

**Verified:**

- [x] Backlog ticket valid; status `in_progress`; `tmp/.active-ticket.json` matches APP-066
- [x] Ticket domain spec `tmp/app-character-creation-spec.md` matches spec updates (awaiting contract §)
- [x] Secondary owner `tmp/app-logging-qa-spec.md` updated for `creation_drift` semantics (no drift)
- [x] Acceptance criteria testable and mapped in run `spec.md` R1–R6
- [x] Code traces match repo: `orchestrator.py` `_check_creation_drift` (L184–221) compares narrated awaiting to `engine_awaiting`; `creation.py` `CREATION_STATUS_LABELS` + `format_creation_status()` (L69–80, L538–541); `cmd_core.py` coarse `CHARACTER_CREATION` per research-brief
- [x] AGENTS.md / drift policy: `registry_gap: false` in research-brief and `spec.md`; no new `tmp/app-*-spec.md`; master registry row **Character creation** owns behavior
- [x] Tests/commands listed (`test_creation_flow.py`, `test_campaign_session.py`, JSONL grep playtest)
- [x] registry_gap matches reality — intentional two-layer model documented; minimal fix scoped to `orchestrator.py` import of `CREATION_STATUS_LABELS`
- [x] No scope creep — non-goals exclude `play/tomb_gm` per-step awaiting, footer label changes, APP-036 UI, post-finalize reception semantics; implementation ⊆ ticket Expected files (orchestrator + domain specs; engine/bridge explicitly out of scope)

## AC coverage

| Ticket AC | Spec / domain coverage |
|-----------|-------------------------|
| Engine awaiting reflects step **or** label-based drift compare | **R2** + domain § Awaiting contract — OR satisfied via label compare (research-recommended path); engine stays `CHARACTER_CREATION` (documented, non-goal) |
| No `creation_drift` every healthy creation turn | **R2**, **R3**, logging § Healthy golden path |
| Domain spec documents engine vs narration contract | **R1** + `app-character-creation-spec.md` § Awaiting contract (engine vs app) |
| Optional golden-path drift assert in `test_creation_flow.py` | **R6** — optional; not required for ticket close |

## Contract clarity for Dev

- **Single change site:** `_check_creation_drift` in `app/gm/orchestrator.py` — import `CREATION_STATUS_LABELS`; when `creation.active`, expected = `CREATION_STATUS_LABELS.get(step, f"{step}_INPUT").upper()`; do not compare to `status["awaiting"]`.
- **Phase:** suppress `phase_mismatch` when `narrated_phase` absent during desk creation; keep `premature_exploration_phase` guard.
- **Resume edge:** when scope true and `creation.active` false, skip awaiting compare (**R4**).
- **Do not edit** `bridge.py`, `creation.py` (beyond import), or `play/tomb_gm/` per spec Affected paths.

## Notes (non-blocking)

1. **Ticket Expected files vs optional test:** AC references `app/tests/test_creation_flow.py` but ticket **Expected files** omits `app/tests/`. If Dev adds the optional drift assert, add that path to the ticket before editing (backlog gate).
2. **`expected_awaiting` JSONL field (R5):** optional — recommend including for grep/debug; not required for PASS.
3. **`status.md` goal line** still says “sync engine awaiting”; run `spec.md` + domain spec correctly describe drift-only fix — Dev should follow `spec.md`.
4. **Post-finalize / resume edge:** spec calls out `WORLD_INTRO` / `RECEPTION_CHOICE` and resume skip; no unit test yet — cover in plan QA or implementation QA / human playtest.

## Re-review focus

_N/A — PASS round 1._
