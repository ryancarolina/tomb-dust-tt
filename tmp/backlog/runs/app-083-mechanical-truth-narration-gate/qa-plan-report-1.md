# QA Report: plan — round 1

**Task:** app-083-mechanical-truth-narration-gate  
**backlog_ticket:** APP-083  
**ticket_path:** [tmp/backlog/app-083-creation-flavor-verification-gate.md](../../app-083-creation-flavor-verification-gate.md)  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)

## Findings

### PLAN-001 — major

- **Location:** `plan.md` Flow C wire table (`_auto_present_name` / NAME); vs `plan.md` §3.4; vs `tmp/app-llm-orchestrator-spec.md` § `finish_reason: length` recovery — Per-step wiring (NAME row)
- **Issue:** Flow C assigns `narrate_with_verification(..., body_pending=True)` to `_auto_present_name`, but domain spec defines NAME as `body_pending=false`, `flavor_only=true` with **length retry or static fallback** — not discard-on-length. Plan §3.4 correctly states: pass `body_pending=True` only when compose appends a **code table** body; NAME body is static prompt copy (`"What name shall I put on the Registry ledger?"`) with no table.
- **Implementation gap:** If Dev follows Flow C, the APP-079 inline stub (`body_pending + length → discard_flavor`) silently drops NAME flavor on truncation instead of one retry/static fallback — behavior regression vs normative orchestrator spec and inconsistent with plan's own §3.4 rule.
- **Suggested fix:**
  - Flow C: `_auto_present_name` → `narrate_with_verification(..., body_pending=False, flavor_only=True)`.
  - Extend `narrate_with_verification` signature (§3.2) with `flavor_only: bool = False` per domain invariant (`body_pending=True` ⇒ `flavor_only=False`).
  - Document NAME length branch in §3.2 loop: on `length` + `flavor_only` → one retry with tightened instruction or static clerk fallback (stub until APP-079 lands; align with orchestrator spec recovery matrix).
  - Reconcile Flow C "same" rows for RACE/CLASS/etc. — explicit `body_pending=True` only for steps in domain per-step table.

### PLAN-002 — minor

- **Location:** `plan.md` §3.1 Config + §3.2 loop; vs `tmp/app-llm-orchestrator-spec.md` § Config
- **Issue:** Plan stores both `NARRATION_LLM_MAX_ATTEMPTS` (6) and `NARRATION_VERIFY_MAX_RETRIES` (5) but the while-loop uses only `_narration_llm_max_attempts`. Unclear whether verify failures are capped at 5 within the shared 6 or the second key is dead config.
- **Implementation gap:** Impl may ignore `NARRATION_VERIFY_MAX_RETRIES` or apply conflicting caps.
- **Suggested fix:** State explicitly in §3.2: loop guard is shared `NARRATION_LLM_MAX_ATTEMPTS`; optionally track verify-only attempts and fail early at `NARRATION_VERIFY_MAX_RETRIES` if domain spec intends a subset — cite orchestrator spec § Config semantics.

### PLAN-003 — minor

- **Location:** `plan.md` §6 Config — `app/config.yaml`; vs ticket **Expected files**
- **Issue:** `app/config.yaml` is in plan Expected files but not listed in ticket Expected files (dev reflection acknowledges this).
- **Implementation gap:** Hooks / backlog gate may deny config edit unless ticket Expected files updated before impl.
- **Suggested fix:** Add `app/config.yaml` to ticket Expected files **or** read narration keys from existing `llm:` section without new file — document chosen path in plan § Expected files.

### PLAN-004 — minor

- **Location:** `plan.md` § Expected files (batch close); vs ticket Expected files
- **Issue:** Ticket lists `tmp/app-logging-qa-spec.md` and `tmp/app-master-spec.md`; plan defers logging spec (§4) and omits master spec pipeline link from close checklist. Acceptable for Phase 1 deferral but not documented in plan handoff.
- **Suggested fix:** Add **on close** row to § Expected files: sync logging spec events (N8), master spec pipeline link per ticket § Spec sync — Phase 1 only; exploration/combat specs unchanged this batch.

## Verified (no findings)

- [x] Backlog ticket valid; status `in_progress`; domain specs `tmp/app-llm-orchestrator-spec.md` + `tmp/app-character-creation-spec.md`
- [x] Phase 1 batch close scope explicit — exploration/combat wiring deferred (plan § Batch close scope; Flow E)
- [x] Code traces match repo — nine flavor wire points at `orchestrator.py` L957–1007, L1115–1501; `_creation_table_flavor` error skip L1320–1321; `_compose_creation_narration` L896–931; catalog helpers `creation.py` L332–385/L626–651/L754; `logger.py` L88–94; `system_prompt.py` creation conflicts L29–38; no `narration_verify.py` yet
- [x] N1–N10 mapped to locus, implementation order, and acceptance table
- [x] qa-spec-pass adversarial notes largely addressed — shared LLM budget, APP-079 inline stub, Sumpty pytest excerpts (Flow D + §7), F4/truth-block fold (§1.3), APP-075 error path (Flow C SKILLS/SCHOOLS/SPELLS + `skip_llm`)
- [x] Verify boundary — flavor only; `_auto_finalize` footer L1500 never verified
- [x] Test plan covers Sumpty L4743/L4749/L4755 fail, benign pass, mock retry, exhausted + regression trio commands
- [x] AGENTS.md / canon compliance — catalogs from `creation.py` / engine sources; no `build/` mechanics drift
- [x] Run spec Expected files mostly covered — `system_prompt.py`, `logger.py` included (ticket broader than Phase 1 close subset)

## Plan files vs Expected files

| Plan change target | In ticket Expected files? | In run spec Expected files? |
|--------------------|---------------------------|-----------------------------|
| `app/gm/narration_verify.py` (new) | Yes | Yes |
| `app/gm/creation.py` | Yes | Yes |
| `app/gm/orchestrator.py` | Yes | Yes |
| `app/gm/system_prompt.py` | No (ticket) | Yes |
| `app/gm/logger.py` | No (ticket) | Yes |
| `app/tests/test_narration_verify.py` (new) | Yes | Yes |
| `app/config.yaml` | **No** | No |
| `tmp/app-llm-orchestrator-spec.md` (close) | Yes | Yes |
| `tmp/app-character-creation-spec.md` (close) | Yes | Yes |
| `tmp/app-logging-qa-spec.md` (close) | Yes (ticket) | Deferred in plan |
| `tmp/app-master-spec.md` (close) | Yes (ticket) | Not in plan |

Phase 1 code paths ⊆ ticket + run spec. `config.yaml` and close-only spec paths need ticket/plan alignment before impl.

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| TurnTruth + build_creation_turn_truth | §1, §2 | `test_format_turn_truth_spell_schools` |
| format_turn_truth in messages | §3.3 | truth block unit test |
| verify_narration creation rules | §1.4 | Sumpty L4743/L4749/L4755 + benign |
| narrate_with_verification all paths | Flow C, §3.4 | mock retry + exhausted |
| Sumpty fail + mock retry pass | §7, Flow D | embedded fixtures |
| APP-079 length before verify | §Approach, §3.2 | **PARTIAL** — NAME `body_pending` wrong (PLAN-001) |
| N8 logging events | §4 | exhausted test (caplog/mock) |
| N9 prompt hygiene | §5 | manual grep + creation flow regression |
| Phase 1 only close | § Batch close scope | Flow E out-of-scope |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-083 `in_progress` |
| Phase 1 scope | **PASS** | Phases 2–3 deferred |
| Code traces | **PASS** | Line refs spot-checked |
| N1–N10 / AC mapping | **PASS** | |
| APP-079 coordination | **FAIL** | NAME `body_pending` / missing `flavor_only` (PLAN-001) |
| Plan ⊆ Expected files | **PARTIAL** | `config.yaml` scope (PLAN-003) |
| Test plan vs qa-spec-pass | **PASS** | |
| Close checklist completeness | **PARTIAL** | logging + master spec (PLAN-004) |

## Summary

Plan is strong on module design, nine wire-point traces, Sumpty fixtures, verify boundary, and APP-075 error skip — but **fails round 1** because Flow C contradicts domain spec and plan §3.4 on NAME `body_pending` / length recovery. Dev must revise `plan.md` §3.2, Flow C, and config/close checklist, then re-submit for QA plan round 2.

## Re-review focus

- NAME row: `body_pending=False`, `flavor_only=True`; length stub behavior for flavor-only steps documented.
- `narrate_with_verification` signature includes both flags with domain invariant.
- `NARRATION_VERIFY_MAX_RETRIES` semantics vs shared cap clarified.
- Ticket Expected files updated for `app/config.yaml` or config read path documented without new file.
- Close checklist names logging spec + master spec sync (Phase 1).
