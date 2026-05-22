# APP-088: Defer remember_fact until facts are narrated to the player

| Field | Value |
|-------|-------|
| **ID** | APP-088 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) |
| **Created** | 2026-05-22 |

## Summary

The GM calls `remember_fact` in the same turn as hook dialogue, storing quest objectives (Undercrypt, reward, ring) **before** the player-facing narration includes those details. Campaign memory leads narration on later turns and can spoil or contradict what was actually said.

## Problem (observed)

Session `app/logs/session-2026-05-22.jsonl` (08:30:52):

- Player: *"I want to talk to Holt"*
- `llm_response` + `tool_call remember_fact`: fact includes Aldric, Breley Undercrypt, signet ring, **200 gold**, three months.
- `gm_narration` to player: Holt only offers vague *"We've got work, if you're interested"* — no Undercrypt, ring, or reward yet.

Later turn (08:44) player asks *"What kind of work?"* and receives ring hook prose — memory already held full quest text from the prior turn.

`system_prompt.py` already says use `remember_fact` after significant events — model is not complying; code has no guard.

## Acceptance criteria

- [ ] **Policy documented** in `app-llm-orchestrator-spec.md`: `remember_fact` only after the same turn's composed player narration includes the fact (or on a later turn after explicit narrate).
- [ ] **Prompt** tightened: forbid `remember_fact` for quest offers until terms are spoken in narration; examples for Holt-style hooks.
- [ ] **Optional code guard (preferred):** reject or defer `remember_fact` when `gate_active` exploration turn's final `gm_narration` does not contain key entities from `fact` (lightweight heuristic) — log `remember_fact_deferred` in JSONL.
- [ ] **Integration test:** mock LLM returns `remember_fact` + short hook prose; assert either deferred call or second-pass narration before memory write.
- [ ] Session golden: first Holt approach does not persist Undercrypt/200gp until player hears hook (manual or mock LLM).

## Expected files

- `app/gm/orchestrator.py` (`_llm_loop` / tool dispatch)
- `app/gm/system_prompt.py`
- `app/gm/logger.py` _(optional `remember_fact_deferred` event)_
- `app/tests/` _(new or extend mock-LLM test)_
- `tmp/app-llm-orchestrator-spec.md`
- `tmp/app-logging-qa-spec.md` _(if new log event)_

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. § Mechanical truth / tool policy — `remember_fact` timing.
3. Changelog with session log reference.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-051 | Golden-path mock LLM may share fixtures |
| APP-085 | Quest system — memory should align with canon quests when that lands |
| APP-087 | **blocks** Holt quest dialogue on surface — fix before quest E2E playtest |

Soft hint:

| Ticket | Relationship |
|--------|--------------|
| APP-077 | Independent — status footer vs memory timing |

## Notes

### Defense layers (pick ≥2)

| Layer | Behavior |
|-------|----------|
| Prompt | "Do not remember_fact quest terms until you have narrated them to the player this turn." |
| Tool result | Return `ok: false, error: deferred_until_narrated` when fact keywords ⊄ composed narration |
| Second LLM pass | After tools, require non-empty narration before closing turn (existing empty follow-up at 08:31 is related) |

### Long-term (APP-085)

When [APP-085](app-085-quest-system-key-npc-quests-ui.md) lands, **quest state** (`offer_quest` / `accept_quest`) is authoritative for objectives — `remember_fact` becomes supplemental recap only, not the quest log. APP-088 still needed for non-quest memory leaks until prompt/guard covers all fact types.

- Empty `llm_response` (`content_length: 0`) after `remember_fact` — narration assembled from prior chunk; fragile if tool-only turn.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-088 --task defer-remember-fact-until-narrated
python tmp/backlog/claim_ticket.py release APP-088 --done
```
