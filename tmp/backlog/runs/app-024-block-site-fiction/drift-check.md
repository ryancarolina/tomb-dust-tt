# Drift Check: APP-024-block-site-fiction

**backlog_ticket:** APP-024  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) | was yes (checklist `[ ]`, refusal copy placeholder) | **Synced:** checklist APP-024 `[x]`; refusal line pinned; changelog **APP-024 done** (2026-05-21) |
| Run [`spec.md`](./spec.md) E1–E9 | no | Verified against `orchestrator.py`, `test_exploration_site_entry_gate.py` |
| [`tmp/app-master-spec.md`](../../../app-master-spec.md) | no | Exploration domain row unchanged; no registry gap |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| Sticky `entry_committed_this_turn` at depth 0 | Reset L2030; set L2091–2092 on first `ok: true` `enter_dungeon` / `site_enter` | yes |
| Gate active: surface + not committed | `_exploration_gate_active` L376–381; `process_turn` uses `pre_turn_mode` L882–884 | yes |
| Bypass: `dungeon`/`site` pre-turn or committed | L377–380; `test_site_entry_gate_bypass_when_in_dungeon` | yes |
| `sanitize_premature_site_entry_flavor` | L119–131 + `_SITE_ENTRY_MARKER_RES` L98–116 | yes |
| Compose on final return + `all_failed and content` | Post-loop L885; in-loop L2133–2135 before banner | yes |
| Refusal when strip empties prose | `_SITE_ENTRY_REFUSAL_LINE` L93–96; `_compose_exploration_narration` L386–387 | yes |
| Dual entry tools | L2091; `test_successful_site_enter_allows_fiction` | yes |
| APP-077 compose order (strip before footer) | `_compose_exploration_narration` docstring L384; footer not landed yet — APP-024 strip only | yes |
| Optional `premature_site_entry` telemetry | Not implemented | defer (spec § optional) |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| Block site-entry fiction unless current turn includes successful `enter_dungeon` or `site_enter` | ✓ |
| Entry commit not revoked by later failed retry / final `_last_tool_results` slot | ✓ (`test_success_then_failed_enter_dungeon_retains_fiction`) |

## Tests run

```bash
cd app; python -m pytest tests/test_exploration_site_entry_gate.py -q
```

**Result:** 7 passed (2.14s)

| Case (domain spec table) | Test | Result |
|--------------------------|------|--------|
| No-tool entry hallucination | `test_surface_no_tool_entry_fiction_stripped` | ✓ |
| Failed entry + `all_failed` content leak | `test_surface_failed_enter_dungeon_no_entry_fiction` | ✓ |
| Successful `enter_dungeon` | `test_surface_successful_enter_dungeon_allows_fiction` | ✓ |
| Success then failed `enter_dungeon` | `test_success_then_failed_enter_dungeon_retains_fiction` | ✓ |
| Successful `site_enter` | `test_successful_site_enter_allows_fiction` | ✓ |
| In-dungeon room turn | `test_site_entry_gate_bypass_when_in_dungeon` | ✓ |
| Helper unit | `test_sanitize_premature_site_entry_flavor_unit` | ✓ |

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-21
- [x] Domain spec checklist + changelog updated
- [ ] `python tmp/backlog/claim_ticket.py release APP-024 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Domain spec § Site-entry fiction gate matched implementation before drift; only checklist, refusal copy pin, and changelog lagged.
- **Compose order:** `all_failed` path sanitizes in-loop (L2133–2135); `process_turn` composes again (L885) — idempotent for refusal/markers per qa-implementation-pass.
- **Combat split:** `failed_names & _COMBAT_TOOL_NAMES` → prefix-only (APP-028); exploration failures use sanitizer — shared block L2119–2135.
- **Non-blocking:** E7 drift telemetry deferred; no dedicated `mode=site` bypass test (symmetric to `dungeon` in gate); human PyGame playtest deferred to Stage 7.
