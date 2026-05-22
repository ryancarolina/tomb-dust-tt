# QA PASS: spec — round 2

**Task:** app-079-finish-reason-length-recovery  
**backlog_ticket:** APP-079  
**ticket_path:** [tmp/backlog/app-079-finish-reason-length-recovery-policy.md](../../app-079-finish-reason-length-recovery-policy.md)  
**Round:** 2 (re-review after `qa-spec-report-1.md`)  
**domain_spec_creation:** not_needed (registry_gap false; orchestrator § updated)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence |
|----|----------|--------|----------|
| SPEC-001 | blocker | **Fixed** | § Semantics defines `body_pending` as authoritative code mechanical blocks only — not static prompt copy. Per-step table: NAME `body_pending=false`, `flavor_only=true`. R2 lists gated steps explicitly (RACE…ROLL_STATS, FINALIZE→WORLD_INTRO) and excludes NAME. Domain spec § per-step table mirrors. |
| SPEC-002 | blocker | **Fixed** | WORLD_INTRO removed from flavor-only row. FINALIZE→WORLD_INTRO handoff row: `body_pending=true`, `discard_flavor`, no retry. § WORLD_INTRO split documents post-finalize compose vs later `process_turn`. Test `test_finalize_length_discards_flavor_ships_summary` added. Code trace: `_auto_finalize` L1486–1501 composes code summary + footer. |
| SPEC-003 | blocker | **Fixed** | Full § Semantics with definitions, per-step wiring table, invariant `body_pending ⇒ ¬flavor_only`, `_creation_table_flavor` error skip. Call sites reference § Semantics table. Domain spec synced with condensed table + changelog r2 row. |
| SPEC-004 | major | **Deferred** | Mid-chain row still says “strip markdown table blocks” without normative detector. PM r2 explicitly deferred; acceptable for spec stage — Dev plan must define heuristic or reference APP-078 helper. |
| TICKET-001 | major | **Deferred** | Ticket Code AC still names `-> str | None`; run spec + domain spec require `LengthRecoveryResult`. Spec wins for impl; ticket sync recommended before close, not blocking spec gate. |
| SPEC-005 | minor | **Deferred** | Ticket exploration AC mentions “reduced `max_tokens` target”; run spec + domain spec use prompt hint only. Spec wins; align ticket on close. |

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec = `app-llm-orchestrator-spec.md`
- [x] Acceptance criteria testable (R1–R6, recovery matrix, pytest commands)
- [x] Code traces match repo (`_auto_present_name` static prompt body L1123–1124; `_auto_finalize` code summary + footer L1493–1501; no `length` branch today)
- [x] AGENTS.md / canon compliance (orchestrator policy only; no mechanics drift)
- [x] Tests/commands listed (`test_llm_truncation_recovery.py`, creation regression pair, `conftest._patch_llm_content`)
- [x] registry_gap false — orchestrator domain § owns § `finish_reason: length` recovery + APP-083 coordination
- [x] Every ticket decision AC row mapped in run spec recovery matrix + domain § Recovery matrix
- [x] APP-083 pipeline order (discard before verify when `body_pending`) and shared `NARRATION_LLM_MAX_ATTEMPTS` budget documented in both specs
- [x] Expected files in run spec match ticket + logging spec on close

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; in_progress |
| registry_gap | **PASS** | false |
| AC testability | **PASS** | R1–R6 + test table map to ticket decisions |
| Code traces | **PASS** | NAME vs finalize handoff vs gated tables align with live orchestrator |
| Internal consistency | **PASS** | R2, matrix, semantics table, domain spec aligned (round 1 blockers cleared) |
| APP-083 coordination | **PASS** | Discard-before-verify, shared budget, wire order normative |
| Domain spec sync | **PASS** | PM r2 changelog; per-step table + finalize test case |

## Acceptance criteria mapping

| Ticket AC (decision) | Spec / domain | Testable | QA |
|----------------------|---------------|----------|-----|
| Gated steps + code body → discard flavor | R2; matrix; § Semantics table | `test_creation_length_discards_flavor_when_body_pending`, SKILLS integration | **PASS** |
| Flavor-only NAME → retry or static fallback | R3; NAME row | `test_narrate_flavor_length_short_retries_or_fallback` | **PASS** |
| Exploration/combat terminal recovery | R4; matrix terminal rows | `test_exploration_length_fallback_last_content` | **PASS** |
| Never ship truncated table when code body present | R2 + matrix | RACE/SKILLS tests | **PASS** |
| Central helper + wire points | R1; § Call sites | unit tests | **PASS** |
| `llm_truncation_recovery` event | R5 | log assertions in tests | **PASS** |
| FINALIZE handoff (implicit from round 1) | FINALIZE→WORLD_INTRO row | `test_finalize_length_discards_flavor_ships_summary` | **PASS** |

## Adversarial notes (non-blocking)

1. **Mid-chain strip (SPEC-004)** — Dev plan must specify table-strip heuristic (pipe-row heuristic, fenced blocks, or shared helper). Domain spec test case expects “tables stripped” without algorithm — plan-stage ownership.
2. **Ticket Code AC (TICKET-001)** — Update ticket to `LengthRecoveryResult` + action literals before release; run spec is authoritative for impl.
3. **Exploration retry tokens (SPEC-005)** — Prompt-only retry per spec; ticket “reduced max_tokens” is stale wording.
4. **Session count** — Ticket cites 25 `length` events; run spec cites 28 (~1.9%); non-blocking for policy design.
5. **`_auto_present_*` vs `_auto_roll_stats`** — R2 prose says `_auto_present_*` but lists ROLL_STATS and `_narrate_creation_flavor` in call sites; per-step table names `_auto_roll_stats` — clear enough for Dev.
6. **Creation spec cross-link** — Deferred to ticket close per Expected files; acceptable at spec stage.

## Summary

Round 1 blockers **SPEC-001**, **SPEC-002**, and **SPEC-003** are fully addressed in `spec.md` (r2) and `tmp/app-llm-orchestrator-spec.md`. Normative creation wiring is internally consistent: NAME retry/fallback, gated steps discard, finalize handoff discard. Spec is implementation-ready for Dev plan + QA plan. Mid-chain strip algorithm and ticket AC sync remain plan/close housekeeping.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
