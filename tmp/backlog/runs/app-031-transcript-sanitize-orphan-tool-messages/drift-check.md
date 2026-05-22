# Drift Check: APP-031-transcript-sanitize-orphan-tool-messages

**backlog_ticket:** APP-031  
**Verdict:** PASS (synced)

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) § Transcript sanitize (APP-031) | was minor (open work still listed APP-031) | **Synced:** removed APP-031 from open-work line; checklist `[x]`, changelog, behavior § already matched code |
| Run [`spec.md`](./spec.md) R1–R6 | no | Verified against `orchestrator.py`, `test_transcript_sanitize.py` |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| `sanitize_transcript_messages` — non-mutating, never raises | `orchestrator.py` L244–309; shallow copies; `_normalize_assistant_message` pass 1 | yes |
| Valid `tool_call` structural rules (`id`, `function.name`, `arguments` string) | `_is_valid_tool_call` L189–206 | yes |
| Orphan / unmatched `tool` dropped | Pass 2: L266–268 (no preceding assistant), L287–290 (id mismatch) | yes |
| Assistant de-tooled when no valid calls after strip | `_normalize_assistant_message` L216–223 | yes |
| APP-028 reorder — tools immediately after assistant; system after tool block | Pass 2 partition L284–296 | yes |
| Safe-prefix fallback (leading system + last user) | `_safe_prefix_fallback` L226–241; guard L307–308 | yes |
| Wire before every orchestrator `chat_completion` | `_chat_completion` L1174–1192; six call sites L1198, L1822, L1842, L2185, L2266, L2339; no bypass | yes |
| `openrouter.chat_completion` pass-through | `openrouter.py` L21; sanitize only in orchestrator | yes |
| Optional `transcript_sanitized` JSONL | not implemented | deferred (APP-034; spec optional v1) |
| APP-032 truncate/retry | not in scope | N/A (APP-032) |

## Spec test matrix → pytest

| Spec case | Test | Result |
|-----------|------|--------|
| Orphan `tool` with no preceding assistant | T1 `test_orphan_tool_no_preceding_assistant` | ✓ |
| Assistant `tool_calls: []` + following `tool` | T2 | ✓ |
| Invalid `tool_calls` + `tool` | T3, T7 | ✓ |
| Valid assistant + two tools, one id unmatched | T5 | ✓ |
| Assistant → system TOOL FAILED → `tool` | T6, T8 | ✓ |
| Valid multi-tool chain round-trip | T4 | ✓ |
| Mock `_llm_loop` depth ≥1 invariants | T8 | ✓ |
| Non-mutating contract | T9 | ✓ |
| Safe-prefix fallback | T10 (3 param cases) | ✓ |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| Sanitize transcript: no orphan tool messages without preceding tool_calls | ✓ |

## Tests run

```bash
cd app; python -m pytest tests/test_transcript_sanitize.py -q
```

**Result:** 12 passed (0.50s)

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-22
- [ ] `python tmp/backlog/claim_ticket.py release APP-031 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Pre-drift lag was documentation only: open-work line still referenced APP-031 while checklist/changelog marked done.
- R5 observability (`transcript_sanitized` JSONL) explicitly deferred to APP-034 — not AC drift.
- Human multi-tool / Google 400 regression playtest deferred to Stage 7 (`human-test-plan.md`).
- APP-032 should reuse `sanitize_transcript_messages` / `_safe_prefix_fallback` after truncate — shared primitive ready.
