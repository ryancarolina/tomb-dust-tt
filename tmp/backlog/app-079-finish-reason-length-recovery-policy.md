# APP-079: finish_reason length recovery policy

| Field | Value |
|-------|-------|
| **ID** | APP-079 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) |
| **Created** | 2026-05-20 |

## Summary

When the LLM hits `finish_reason: length`, truncated output is returned as-is. APP-072 mitigates **race** duplicate tables via post-sanitize; session `2026-05-20` logged **25** `length` responses across creation and play — truncated tables, cut-off status lines, and incomplete combat/exploration narration.

Define a **central recovery policy**: detect `length`, apply mode-specific sanitize-or-retry, never ship half a markdown table or broken status line to the player.

## Problem (observed)

- `_narrate_flavor` / `_llm_loop` / `_combat_llm_loop_inner` log `finish_reason` but do not branch on `length`.
- Creation flavor cap `_CREATION_FLAVOR_MAX_TOKENS = 120` frequently triggers truncation mid-table.
- Exploration uses `max_tokens` from config (much larger) — truncation still occurs on long tool-chain turns.
- APP-072 non-goal explicitly deferred length retry; this ticket generalizes policy across modes.

## Acceptance criteria

### Decision (document in domain spec)

- [ ] **Creation (gated steps with code body):** on `length`, discard truncated flavor; ship code body + footer only (no LLM retry required).
- [ ] **Creation (flavor-only steps e.g. NAME):** on `length`, one retry with stricter prompt (“≤2 sentences, no tables”) OR static fallback string.
- [ ] **Exploration/combat:** on `length` with empty/minimal content, one retry with reduced `max_tokens` target or “complete in ≤3 sentences”; if still `length`, return last good `_last_content` or safe fallback.
- [ ] **Never** append truncated markdown table fragments when code body already provides the table (coordinate with APP-078).

### Code

- [ ] `handle_finish_reason_length(response, *, mode, creation_step, body_pending) -> str | None` helper (or inline policy in orchestrator) — returns recovered content or `None` to signal discard-and-fallback.
- [ ] Branch in `_narrate_flavor`, `_narrate_creation_flavor`, `_llm_loop`, `_combat_llm_loop_inner` after `log_llm_response`.
- [ ] Creation path: if `length` and `_compose_creation_narration` has non-empty `body`, set flavor to `""` before compose (or skip flavor LLM output).
- [ ] Optional single retry: only when flavor-only and content unusably short (< N chars); max **one** retry per turn to control cost.
- [ ] Log `llm_truncation_recovery` JSONL event with mode, step, action taken (`discard_flavor`, `retry`, `fallback`).

### Tests

- [ ] Unit: creation compose with `length` flavor containing partial `\| Race \|` — final narration has single table from body.
- [ ] Unit: `_narrate_flavor` stub returns `length` + short content — retry or fallback invoked per policy.
- [ ] Integration: mock `chat_completion` to return `finish_reason: length` on SKILLS step — player sees full code skills table, no truncated LLM table above it.

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/logger.py` _(optional `llm_truncation_recovery` event)_
- `app/tests/test_llm_truncation_recovery.py`
- `tmp/app-llm-orchestrator-spec.md`
- `tmp/app-character-creation-spec.md` _(creation-mode policy cross-link)_

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Add § **`finish_reason: length` recovery** to [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) with per-mode table + changelog.
3. Update creation spec compose section to reference centralized policy (replace APP-072 “no retry” non-goal for creation flavor-only cases).

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-072 | race table strip — partial mitigation; this ticket owns policy |
| APP-078 | generic table strip — defense if truncated table slips through |
| APP-077 | exploration footer — reduces harm from truncated status lines |

Soft hint:

| Ticket | Relationship |
|--------|--------------|
| APP-032 | API retry — orthogonal (transport vs truncation) |

## Notes

### Recovery matrix (starting point)

| Context | On `length` | Retry? |
|---------|-------------|--------|
| Creation + code `body` pending | Discard LLM flavor | No |
| Creation flavor-only (NAME) | Retry once ≤2 sentences | Yes (1×) |
| Exploration final narration | Retry once “≤3 sentences” OR `_last_content` | Yes (1×) |
| Combat final narration | Mechanical brief + retry | Yes (1×) |
| Tool loop mid-chain | Continue loop with truncated assistant content stripped of tables | No retry on content alone |

### Session evidence

- `16:44:41` — RACE flavor `length` + truncated race table (APP-072 strip fixes duplicate; policy would discard flavor entirely).
- Multiple creation steps with 1k–10k `content_length` before code-first hardening — historical; policy guards regressions.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-079 --task finish-reason-length-recovery
python tmp/backlog/claim_ticket.py release APP-079 --done
```
