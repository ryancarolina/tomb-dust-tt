# APP-077: Code-owned exploration status footer

| Field | Value |
|-------|-------|
| **ID** | APP-077 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | done |
| **Closed** | 2026-05-22 |
| **Domain spec** | [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) |
| **Created** | 2026-05-20 |

## Summary

During exploration and combat, the LLM is prompted to emit `[Location: … | Phase: … | HP: … | Awaiting: …]` (`system_prompt.py`). Creation already uses a **code-owned footer** (`format_creation_status`) with flavor sanitizers (APP-007/073). Exploration has no equivalent — models invent wrong GP, phase, or awaiting values (session `15:51:59`: LLM status line showed `GP: 61` while correcting the player).

Generalize the creation pattern: **strip LLM status lines from narration, append one authoritative footer from `bridge.status()`.**

## Problem (observed)

- `system_prompt.py` L213 mandates LLM-authored status line every turn.
- `_emit_narration` runs `_check_creation_drift` only in creation scope — exploration drift is invisible.
- `strip_llm_status_tags()` exists but is wired only in `_compose_creation_narration`, not `_llm_loop` / combat paths.
- Suggestion chips and UI may parse the **first** `Awaiting:` in narration — LLM-invented tokens poison chips (same class of bug as APP-065/073).

Session `app/logs/session-2026-05-22.jsonl`:

- Exploration turns embed `[Location: … | Phase: … | GP: … | Awaiting: PLAYER_ACTIONS]` in LLM prose (player reads model-authored state).
- Quest accept turn ends with stray `---\n**Campaign Memory Updated:**` after the bracket line (meta leak; should not be player-facing).
- When APP-087 strips body but leaves LLM bracket line, player sees **footer-only** narration — code-owned footer makes that impossible (strip + single append).

## Acceptance criteria

### Decision (document in domain spec)

- [x] **Exploration footer contract:** player-facing status line is code-owned from engine snapshot, not LLM prose.
- [x] **Combat footer contract:** when `combat.active`, footer includes turn/actor context from engine (or combat-specific subset documented in spec).

### Code

- [x] `format_exploration_status(status: dict) -> str` (or extend existing helper) builds canonical bracket line from `GameBridge.status()` — address, phase, roster HP summary, fortune, GP in transit, `awaiting`.
- [x] `_compose_exploration_narration(prose: str, status: dict) -> str` — run `strip_llm_status_tags(prose)` on LLM body, append code footer (mirror `_compose_creation_narration` minus creation-only strippers).
- [x] Strip LLM **meta narration** leaks (`**Campaign Memory Updated:**`, horizontal-rule + empty memory banners) via shared helper with `strip_llm_status_tags` or sibling regex.
- [x] If body empty after strip (and not refusal line), still append code footer — never emit bracket-only with no prose unless refusal path applies.
- [x] Wire `_llm_loop` final return and `_combat_llm_loop_inner` success path through compose helper (or equivalent post-process before `_emit_narration`).
- [x] Update `system_prompt.py` — remove or soften “you must emit status line”; instruct GM that the client appends authoritative state.
- [x] Optional: `log_exploration_drift` when stripped prose contained `[Location:` / `Awaiting:` disagreeing with engine (telemetry only, like APP-002).

### Tests

- [x] Unit: `format_exploration_status` golden snapshot from fixture `status` dict.
- [x] Unit: `_compose_exploration_narration` strips inline `[Location:…]` and `[Awaiting:…]` from LLM prose; exactly one footer from engine.
- [x] Integration: mock LLM returns narration with wrong GP in status line; composed output shows engine GP only in footer region.

## Expected files

- `app/gm/orchestrator.py`
- `app/gm/creation.py` _(reuse `strip_llm_status_tags` — do not duplicate)_
- `app/gm/system_prompt.py`
- `app/gm/logger.py` _(optional exploration_drift event)_
- `app/tests/test_exploration_status_footer.py`
- `app/tests/test_exploration_site_entry_gate.py` _(APP-024 regression — footer assertions on in-dungeon bypass)_
- `tmp/app-exploration-delve-spec.md`
- `tmp/app-llm-orchestrator-spec.md` _(cross-link compose pattern)_

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Add § **Code-owned status footer (exploration)** to [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) with footer fields + changelog.
3. Update [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) — exploration/combat narration compose pipeline.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-007 | pattern source (creation footer) |
| APP-073 | reuses `strip_llm_status_tags` |
| APP-024 | complementary — blocks site fiction; this ticket fixes status-line lies |
| APP-087 | sanitizer may leave LLM bracket line alone — code footer + strip fixes footer-only turns |
| APP-088 | independent — remember_fact timing |
| APP-041 | TTS may consume same stripped prose; coordinate bracket strip rules |

Soft hint:

| Ticket | Relationship |
|--------|--------------|
| APP-065 | chips parse first `Awaiting:` — footer ownership reduces stale tokens |

## Notes

### Proposed footer shape (starting point)

```
[Location: {address} | Phase: {phase} | HP: {hp}/{max} | Fortune: {fortune} | GP: {gold} | Awaiting: {awaiting}]
```

Source fields from `bridge.status()` party + roster slot 1 (document exact mapping in spec).

### Defense in depth

| Layer | Behavior |
|-------|----------|
| Prompt | Do not ask LLM to emit status bracket line |
| Post-sanitize | `strip_llm_status_tags` on exploration prose |
| Footer | Single code-owned line from engine |

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-077 --task code-owned-exploration-status-footer
python tmp/backlog/claim_ticket.py release APP-077 --done
```
