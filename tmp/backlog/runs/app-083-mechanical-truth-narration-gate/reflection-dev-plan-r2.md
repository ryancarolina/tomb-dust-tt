# Reflection: Dev — APP-083 plan r2 (qa-plan-report-1)

**Agent:** Dev (plan revision)  
**Round:** 2  
**Input:** [qa-plan-report-1.md](qa-plan-report-1.md) (FAIL — PLAN-001 major, PLAN-002 minor)  
**Deliverables:** [plan.md](plan.md) (r2), reflection-dev-plan-r2.md

## Changes made (qa-plan-report-1)

### PLAN-001 — NAME `body_pending` / `flavor_only` (major)

- **Root cause:** Flow C assigned `body_pending=True` to `_auto_present_name`, contradicting domain spec per-step table (NAME = static prompt body, LLM banter only).
- **Fix:**
  - Flow C rewritten with explicit `body_pending` / `flavor_only` columns for all nine wire points; NAME → `(False, True)`.
  - `narrate_with_verification` signature extended with `flavor_only: bool = False` and invariant `body_pending=True` ⇒ `flavor_only=False`.
  - §3.2 length stub branches: `body_pending` → discard; `flavor_only` → one length retry (`LENGTH_MAX_RECOVERY_RETRIES=1`) or static clerk fallback before verify.
  - §3.4 replaced blanket “pass `body_pending=True` whenever compose appends table” with per-step flag table aligned to orchestrator spec.
  - Added `test_name_length_flavor_only_retry_or_fallback` in §7.

### PLAN-002 — retry budget clarity (minor)

- **Root cause:** Plan listed `NARRATION_VERIFY_MAX_RETRIES` but loop text only referenced `_narration_llm_max_attempts`.
- **Fix:** §3.1 documents shared `attempt` counter vs `verify_fail_count` subset; early break when verify subset exhausted; `LENGTH_MAX_RECOVERY_RETRIES` wired for NAME length branch; config example includes `length_max_recovery_retries`.

### Not addressed in r2 (minor — next round or ticket update)

- **PLAN-003:** `app/config.yaml` still in plan Expected files but not ticket Expected files — impl agent should add path to ticket before edit or read keys from existing `llm:` section.
- **PLAN-004:** Close checklist for `tmp/app-logging-qa-spec.md` + `tmp/app-master-spec.md` — still deferred in plan §4 / Expected files; add on-close row when closing ticket.

## Self-critique (r2)

- Plan r1 correctly stated §3.4 “pass `body_pending` only when compose appends code table” but Flow C contradicted it for NAME — r2 reconciles table, §3.4, and §3.2 stub.
- Inline 079 stub is now flag-driven; when APP-079 lands, replace stub body with `handle_finish_reason_length(..., body_pending=, flavor_only=)` — same call-site flags from Flow C.
- Verify subset early-exit may leave one unused slot in shared cap — matches orchestrator spec “subset of shared cap” semantics.

## Did I miss anything?

- [x] PLAN-001 / PLAN-002 from qa-plan-report-1
- [x] Re-review focus items: NAME row, signature flags, retry semantics
- [ ] PLAN-003 / PLAN-004 — documented as follow-up above
- [x] N1–N10, nine wire traces, Sumpty tests unchanged in intent

## Handoff

**Ready for:** QA plan gate round 2 (Stage 3b)  
**Re-review focus:** NAME `(body_pending=False, flavor_only=True)`; length stub vs verify order; `verify_fail_count` vs shared `attempt`; optional ticket Expected files for `config.yaml`
