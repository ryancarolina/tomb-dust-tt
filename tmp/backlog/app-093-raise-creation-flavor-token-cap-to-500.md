# APP-093: Raise creation flavor token cap to 500

| Field | Value |
|-------|-------|
| **ID** | APP-093 |
| **Type** | feature |
| **Priority** | P2 |
| **Status** | open |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) |
| **Created** | 2026-05-22 |

## Summary

Creation flavor LLM calls are capped at **`_CREATION_FLAVOR_MAX_TOKENS = 120`** (APP-012 thin-flavor decision). That budget is too small for reliable prose: session logs show frequent `finish_reason: length` on steps like EQUIPMENT_GOLD and WORLD_INTRO, triggering APP-079 `discard_flavor` and leaving players with code tables only.

APP-079 explicitly deferred cap changes to a separate tuning ticket. Raise the creation flavor cap to **500 tokens** so flavor can complete without changing the code-owned table / verify / discard policy.

## Acceptance criteria

- [ ] `_CREATION_FLAVOR_MAX_TOKENS` (or equivalent config key) is **500** — used by `_narrate_flavor` / `_narrate_creation_flavor` / `_call_narration_llm` creation paths.
- [ ] Prompt copy and docstrings that say “~120 tokens” updated to reflect **500** (or “configurable cap”) without weakening “no tables / no mechanics” flavor rules (APP-012, APP-083).
- [ ] Domain specs updated: [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) § creation flavor + APP-079 length section; [`app-character-creation-spec.md`](../app-character-creation-spec.md) flavor bullets.
- [ ] Optional: expose `llm.creation_flavor_max_tokens` in `app/config.yaml` (default 500) per APP-046 config-key pattern — if not config-driven, constant-only change is acceptable.
- [ ] Tests: mock LLM asserts `max_tokens=500` on at least one creation flavor call; existing APP-079 / APP-083 / creation-flow tests remain green.
- [ ] Manual spot-check: one full creation run shows LLM prose on EQUIPMENT_GOLD or WORLD_INTRO without `discard_flavor` from length alone (log `finish_reason: stop` or non-empty flavor retained).

## Expected files

- `app/gm/orchestrator.py`
- `app/config.yaml` _(optional config key)_
- `app/gm/system_prompt.py` _(if prompt mentions 120-token budget)_
- `app/tests/test_llm_truncation_recovery.py` _(or creation/orchestrator test asserting max_tokens)_
- `tmp/app-llm-orchestrator-spec.md`
- `tmp/app-character-creation-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Update orchestrator + character-creation spec flavor token references and changelog.
3. Note cost/latency tradeoff in ticket Notes if playtest shows regressions.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-093 --task creation-flavor-token-cap
python tmp/backlog/claim_ticket.py release APP-093 --done
```

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-012 | Parent decision — thin LLM flavor during creation (cap tuning only; policy unchanged) |
| APP-079 | Length recovery stays; higher cap should reduce `discard_flavor` frequency |
| APP-083 | TurnTruth verify still required before publish — cap increase does not bypass verify |

## Notes

- **Scope:** Creation flavor calls only — not global `llm.max_tokens` (2048) or exploration/combat narration.
- **Non-goals:** Removing code-owned tables, relaxing verify rules, or re-enabling LLM-authored mechanics tables (APP-072/073/078 mitigations stay).
- **Risk:** ~4× token spend per creation flavor call; acceptable for ~10–15 steps per character if prose quality improves materially.
