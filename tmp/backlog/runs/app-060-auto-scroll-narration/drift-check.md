# Drift Check: app-060-auto-scroll-narration

**backlog_ticket:** APP-060  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md) | no | § [Narration scroll behavior](../../../app-pygame-ui-spec.md#narration-scroll-behavior-app-060) matches shipped code; checklist `[x]`; changelog **APP-060 done** row present — no edit required |
| Run [`spec.md`](./spec.md) R1–R4 | no | Verified against `narration.py`, `app.py`, `test_narration_scroll.py` |
| Ticket [`app-060-auto-scroll-narration-on-input-and-response.md`](../../app-060-auto-scroll-narration-on-input-and-response.md) | was yes (AC open; status `in_progress`) | **Synced:** all AC checked; status `done`; Closed 2026-05-22 |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **Layout-correct pin** — scroll after `_total_height` current | `_follow_tail` + `request_follow_tail()`; `draw()` rebuilds then `scroll_to_bottom()` | yes |
| **Preserve +40 clamp** | `scroll_to_bottom()` L74–75 unchanged | yes |
| **Coalesce** multiple tail requests per frame | Flag stays true; cleared once in `draw()` | yes |
| **Queue: player, narration, narration_text, error** | `_process_ui_queue` L163–171, L202–204 → `_smooth_scroll_to_bottom()` | yes |
| **No tail on clear/status/map/etc.** | Only append handlers call wrapper; `clear()` resets `_follow_tail` | yes |
| **Always-follow policy** | No near-bottom guard; documented in domain spec § Tail-follow policy | yes |
| **Wheel momentum unchanged** | `_update_scroll` → `narration.scroll(dy)` untouched | yes |
| **Error path newly wired** | `error` handler adds line + `_smooth_scroll_to_bottom()` | yes |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| Player submit pins player line | ✓ `player` handler + `test_player_line_follows_tail` |
| GM response (`narration`, `narration_text`, `error`) shows full new content | ✓ all three handlers follow tail; tall-table + error tests |
| Layout-correct: scroll after height known | ✓ `draw()` order; `test_stale_scroll_before_rebuild_fails` |
| Long tables / multi-paragraph without manual wheel | ✓ `TALL_TABLE` fixture; `test_request_follow_tail_after_draw_pins_bottom` |
| Manual scroll up works; new content returns to bottom | ✓ wheel path unchanged; always-follow documented |
| Domain spec § Narration scroll behavior | ✓ L38–105, checklist L285, changelog L339 |

## Run spec R1–R4 ↔ code

| ID | Requirement | Result |
|----|-------------|--------|
| **R1** | Layout-correct bottom pin after rebuild | **PASS** |
| **R1** | One rebuild per dirty frame on tail path | **PASS** (`test_multiple_follow_requests_coalesce`) |
| **R2** | Queue paths player/narration/narration_text/error | **PASS** |
| **R2** | No tail on clear/status/map | **PASS** |
| **R3** | Always-follow + wheel unchanged | **PASS** |
| **R4** | Unit module + regression pytest green | **PASS** |

## Tests run

```bash
cd app; python -m pytest tests/test_narration_scroll.py tests/test_ui_map_creation_gate.py -q
```

**Result:** 16 passed (3.81s)

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_narration_scroll.py` | 6 (stale vs fixed, player/error tail, coalesce, clear flag) | ✓ |
| `app/tests/test_ui_map_creation_gate.py` | 10 (APP-037 regression per plan R4) | ✓ |

## Code-path verification

| Flow | Trace | Result |
|------|-------|--------|
| Frame order | `_process_ui_queue()` → `_update_scroll()` → `narration.draw()` | ✓ |
| Player submit | `_submit` → `("player", …)` → add + `request_follow_tail()` → draw pins | ✓ |
| GM reply | `narration_text` / `narration` → add + follow → draw | ✓ |
| Error | `error` → add + `_smooth_scroll_to_bottom()` → draw | ✓ |
| Defensive clear | `request_follow_tail()` then `clear()` → flag false, offset 0 | ✓ |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec checklist + changelog — **APP-060 done**
- [x] Spec ↔ code — no drift on tail-follow, queue matrix, or always-follow policy
- [ ] `python tmp/backlog/claim_ticket.py release APP-060 --done` — **orchestrator** (QA drift: not run per convention)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Domain spec was updated at impl QA; drift found **no residual gap** between spec prose and code.
- **Preferred path shipped:** `_follow_tail` in `draw()` — spec’s optional `scroll_to_bottom_after_rebuild()` not implemented (acceptable per run spec).
- **Batch bleed:** `tmp/app-pygame-ui-spec.md` and `app/ui/app.py` may carry APP-036/065 hunks; APP-060 scroll wiring is isolated and correct.
- **Non-blocking:** No App-level queue integration test (plan optional); panel tests satisfy R4. Human creation-table / long-reply / wheel-up-then-submit playtest deferred to Stage 7 `human-test-plan.md`.
- **Out of scope acknowledged:** session-load pin, resize re-pin, animated scroll — not implemented (per spec).
