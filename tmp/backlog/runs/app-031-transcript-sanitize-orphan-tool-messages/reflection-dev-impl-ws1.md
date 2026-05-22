# Dev reflection — APP-031 implementation (ws1)

**backlog_ticket:** APP-031  
**Round:** implementation  
**Date:** 2026-05-22

## What shipped

- Module-level `sanitize_transcript_messages`, `_safe_prefix_fallback`, `_is_valid_tool_call`, `_normalize_assistant_message` in `app/gm/orchestrator.py`.
- `Orchestrator._chat_completion` wrapper sanitizes then delegates to `gm.openrouter.chat_completion`.
- All six in-orchestrator call sites wired: `_call_narration_llm`, `_narrate_only`, `_creation_llm_loop`, `_combat_llm_loop_inner`, combat narrate pass, `_llm_loop`.
- APP-028 reorder implemented in pass 2 (tools immediately after assistant; system TOOL FAILED lines deferred after tool block). Loop append order unchanged.
- New test module `app/tests/test_transcript_sanitize.py` — full T1–T10 matrix plus `assert_transcript_invariants` helper and `_llm_loop` integration mock (T8).

## Test results

```text
python -m pytest app/tests/test_transcript_sanitize.py -v
12 passed in 0.48s
```

## Deviations / notes

- None from plan. T4 assertion uses `out is not messages` (not `!=`) because equal content is expected for valid round-trip.
- R5 `transcript_sanitized` JSONL deferred per spec.
- Domain spec checklist marked done; changelog entry appended.

## APP-032 handoff

- `sanitize_transcript_messages` and `_safe_prefix_fallback` are module-level exports for truncate-then-sanitize retry path.
- Helper is non-mutating (T9) — safe for shared arrays after truncate.

## Risks

- Safe-prefix fallback drops trailing content-only assistant (documented non-goal); APP-032 may extend.
- Over-stripping only occurs on structurally invalid tool rounds; valid chains pass through unchanged (T4).
