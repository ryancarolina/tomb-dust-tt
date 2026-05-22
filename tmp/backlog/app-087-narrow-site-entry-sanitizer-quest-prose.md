# APP-087: Narrow site-entry sanitizer for quest/direction prose

| Field | Value |
|-------|-------|
| **ID** | APP-087 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) |
| **Created** | 2026-05-22 |

## Summary

APP-024 `sanitize_premature_site_entry_flavor` uses line-level markers that match **any mention** of `undercrypt`, `corridor`, `torchlit`, etc. On surface, that strips legitimate NPC/quest answers while the LLM `[Location: …]` footer line survives — player sees an empty GM reply.

## Problem (observed)

Session `app/logs/session-2026-05-22.jsonl` (09:16:13):

- Player: *"Where did holt say he last saw his brother?"*
- LLM response (~529 chars) explained Aldric / **Breley Undercrypt** / under the keep.
- `gm_narration` emitted **only** `[Location: 32-C | Phase: preparation | … | Awaiting: PLAYER_ACTIONS]` — all quest prose removed.

Root cause: `_SITE_ENTRY_MARKER_RES` in `orchestrator.py` includes bare `\bundercrypt\b` (and similar nouns) at **line** granularity. Spec intent (APP-024) is to block **asserted entry / interior presence**, not surface discussion of a site name.

## Acceptance criteria

- [ ] **Line-level markers** target crossing/entry assertions only (e.g. `step into`, `cross the threshold`, `you enter/stand in the crypt`, false `Phase: delve`, interior `[Location: … UG-…]`) — **not** bare site nouns (`undercrypt`, `corridor`, `torchlit`, `catacomb`) on their own.
- [ ] **Paragraph fallback** (when stitched prose still reads as interior entry) may use broader interior ambiance patterns — document split in spec § Site-entry fiction gate.
- [ ] Surface quest Q&A preserved: fixture prose mentioning *"Breley Undercrypt lies beneath the keep"* / *"went down into the undercrypt"* passes sanitizer with `gate_active=True`.
- [ ] Entry hallucination still blocked: `You step into the torchlit crypt. Corridors stretch ahead.` → stripped or refusal line per APP-024.
- [ ] Regression test in `app/tests/test_exploration_site_entry_gate.py` (or new module) for quest-prose + entry-prose cases.
- [ ] Domain spec updated: clarify noun-mention vs entry-assertion markers; changelog entry.

## Expected files

- `app/gm/orchestrator.py` (`_SITE_ENTRY_MARKER_RES`, `sanitize_premature_site_entry_flavor`)
- `app/tests/test_exploration_site_entry_gate.py`
- `tmp/app-exploration-delve-spec.md`

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Amend § Site-entry fiction gate — marker tiers (line vs paragraph).
3. Changelog dated entry referencing session log repro.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-024 | Parent feature — this ticket fixes over-broad markers without removing the gate |
| APP-085 | **blocks** Holt quest offer/Q&A E2E until surface direction prose is not stripped |
| APP-077 | Compose order unchanged — sanitizer still runs before footer strip (when APP-077 lands) |

## Notes

### Design (recommended)

| Tier | Strip when | Examples kept / dropped |
|------|------------|-------------------------|
| **Line** | Player fiction **crosses** or **is inside** without tools | Keep: "Undercrypt is under the keep." Drop: "You step into the torchlit crypt." |
| **Paragraph** | Residual block still asserts interior scene after line pass | Drop stitched entry-only paragraphs |

### Repro commands

```bash
python -m pytest app/tests/test_exploration_site_entry_gate.py -q
```

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-087 --task narrow-site-entry-sanitizer-quest-prose
python tmp/backlog/claim_ticket.py release APP-087 --done
```
