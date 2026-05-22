# Reflection: QA spec — APP-079 finish-reason-length-recovery

**Agent:** QA (adversarial)  
**Round:** 1  
**Verdict:** FAIL  
**Artifacts:** `qa-spec-report-1.md`

## What I reviewed

- `spec.md`, ticket `app-079-finish-reason-length-recovery-policy.md`, `research-brief.md`
- PM updates in `tmp/app-llm-orchestrator-spec.md` § `finish_reason: length` recovery and APP-083 coordination
- Live `app/gm/orchestrator.py` traces for `_auto_present_name`, `_auto_finalize` WORLD_INTRO handoff, `_narrate_flavor`, `_llm_loop`, `_combat_llm_loop_inner`

## Why FAIL (not PASS)

Default FAIL until proven otherwise. Three blockers are **implementation-breaking**, not wording nits:

1. **R2 vs matrix** — “non-empty code body ⇒ `body_pending=True`” would break NAME (has prompt body, must retry/fallback).
2. **WORLD_INTRO mis-tag** — finalize handoff has authoritative HP/MP/body + footer; flavor-only retry is wrong policy.
3. **Missing semantics** — helper params undefined for callers; Dev cannot wire consistently.

Orchestrator domain spec avoids the worst R2 wording (NAME-only flavor-only row) but run spec still lists WORLD_INTRO under flavor-only — PM must sync both on revision.

## What was solid

- Central helper + `LengthRecoveryResult` + observability event
- Discard-before-verify when table body pending (APP-083)
- Shared `NARRATION_LLM_MAX_ATTEMPTS` budget
- Combat ~1966 and mid-chain called out in research/spec
- Test plan maps to ticket AC with existing stub patterns

## Self-critique

- Did not re-count session `length` events (gitignored log) — counts in spec/ticket differ (25 vs 28); non-blocking.
- Did not require `app-character-creation-spec.md` forward pointer pre-impl — ticket defers to close; noted as partial credit.
- Mid-chain strip left as major, not blocker — could escalate if PM leaves vague after round 2.

## Handoff

**PM revision round 1:** fix SPEC-001–003 in `spec.md` and mirror orchestrator domain §; align ticket Code AC (TICKET-001).  
**Re-review:** semantics table + R2 + WORLD_INTRO row + NAME test still valid.
