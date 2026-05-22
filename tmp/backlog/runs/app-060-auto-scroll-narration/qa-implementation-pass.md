# QA PASS: implementation — round 1

**Task:** app-060-auto-scroll-narration  
**backlog_ticket:** APP-060  
**ticket_path:** [tmp/backlog/app-060-auto-scroll-narration-on-input-and-response.md](../../app-060-auto-scroll-narration-on-input-and-response.md)  
**Round:** 1  
**domain_spec:** synced — § [Narration scroll behavior](../../../app-pygame-ui-spec.md#narration-scroll-behavior-app-060); checklist `[x]` + changelog **done** row present (ticket backlog file AC ticks deferred to Stage 6 release)

## Verdict

**PASS** — Tail-follow scroll deferred to `draw()` after `_rebuild()`; queue paths (`player`, `narration`, `narration_text`, `error`) request follow tail; unit + regression tests green; domain spec documents always-follow policy and queue matrix.

## Automated tests

```text
python -m pytest app/tests/test_narration_scroll.py -v
6 passed in 1.56s

python -m pytest app/tests/test_ui_map_creation_gate.py -q
10 passed in 2.15s
```

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_narration_scroll.py` | stale vs fixed scroll, player/error tail, coalesce, clear flag | ✓ 6 |
| `app/tests/test_ui_map_creation_gate.py` | APP-037 regression (plan R4) | ✓ 10 |

## Ticket AC → code

| Ticket AC | Evidence | Result |
|-----------|----------|--------|
| Player submit pins player line | `_process_ui_queue` `player` → `_smooth_scroll_to_bottom()`; `test_player_line_follows_tail` | ✓ |
| GM response (`narration`, `narration_text`, `error`) shows full new content | All three handlers call `_smooth_scroll_to_bottom()`; error handler newly wired L203–204; tall-table + error tests | ✓ |
| Layout-correct: scroll after height known | `draw()`: `_rebuild()` then `if _follow_tail: scroll_to_bottom()`; stale regression test | ✓ |
| Long tables / multi-paragraph without manual wheel | `TALL_TABLE` markdown fixture; `test_request_follow_tail_after_draw_pins_bottom` | ✓ |
| Manual scroll up works; new content returns to bottom | Wheel path unchanged (`scroll()`); always-follow via queue — documented in domain spec § Tail-follow policy | ✓ |
| Domain spec § Narration scroll behavior | `tmp/app-pygame-ui-spec.md` L38–105, checklist L285, changelog L339 | ✓ |

## Spec R1–R4 → code

| ID | Requirement | Evidence | Result |
|----|-------------|----------|--------|
| **R1** | Layout-correct bottom pin after `_total_height` current | `_follow_tail` + `request_follow_tail()`; apply in `draw()` after `_rebuild()` | ✓ |
| **R1** | Preserve `+ 40` clamp formula | `scroll_to_bottom()` unchanged L74–75 | ✓ |
| **R1** | One rebuild per dirty frame on tail path | Flag coalesces multiple `request_follow_tail()` calls; `test_multiple_follow_requests_coalesce` | ✓ |
| **R2** | Queue paths: player, narration, narration_text, error | `app.py` L163–171, L202–204; `_smooth_scroll_to_bottom()` → `request_follow_tail()` L226–227 | ✓ |
| **R2** | No tail on clear/status/map/etc. | Only append handlers call wrapper; `clear()` resets `_follow_tail` | ✓ |
| **R3** | Always-follow on new queued content | Policy documented; no near-bottom guard in code (deferred per spec) | ✓ |
| **R3** | Wheel momentum unchanged | `_update_scroll` → `narration.scroll(dy)` untouched | ✓ |
| **R4** | Unit module + pytest green | `test_narration_scroll.py` (6 cases); regression gate green | ✓ |

## Diff scope reviewed

| File | Change | In ticket Expected files? |
|------|--------|---------------------------|
| `app/ui/panels/narration.py` | `_follow_tail`, `request_follow_tail()`, apply in `draw()`, reset in `clear()` | ✓ |
| `app/ui/app.py` | `_smooth_scroll_to_bottom()` → `request_follow_tail()`; error handler adds tail follow | ✓ |
| `app/tests/test_narration_scroll.py` | **new** — 6 headless panel tests | ✓ (untracked `??`) |
| `tmp/app-pygame-ui-spec.md` | § Narration scroll behavior + checklist/changelog | ✓ (diff also carries APP-036 batch prose — see notes) |

## Code-path verification

| Flow | Trace | Result |
|------|-------|--------|
| Frame order | `_process_ui_queue()` → `_update_scroll()` → `narration.draw()` (plan Flow A) | ✓ unchanged |
| Player submit | `_submit` → `("player", …)` → add + `request_follow_tail()` → draw pins | ✓ |
| GM reply | `narration_text` / `narration` → add + follow → draw | ✓ |
| Error | `error` → add + `_smooth_scroll_to_bottom()` (new) → draw | ✓ |
| Defensive clear | `request_follow_tail()` then `clear()` → flag false, offset 0 | ✓ (`test_clear_clears_follow_flag`) |

## Scope notes (non-blocking)

| Item | Note |
|------|------|
| **Untracked test file** | `app/tests/test_narration_scroll.py` must be staged before commit. |
| **Ticket / backlog hygiene** | Ticket AC checkboxes still `[ ]`; `status.md` Stage impl not ticked — update at Stage 6 `release APP-060 --done`. |
| **No App-level queue test** | Plan marks optional; panel tests + error-line test satisfy R4. |
| **No `narration` batch-specific test** | `add_lines` path uses same follow-tail API as `narration_text`; tall GM table test covers rebuild height. |
| **Domain spec batch bleed** | `tmp/app-pygame-ui-spec.md` diff includes APP-036 sections unrelated to APP-060 impl hunks; APP-060 § content matches shipped code. |
| **Human playtest** | Creation table + submit, long reply, error-at-bottom not run in QA; defer to Stage 7 `human-test-plan.md`. |
| **Out of scope acknowledged** | Session-load pin, resize re-pin, animated scroll — not implemented (per spec). |

## Handoff

**Ready for:** Stage 6 drift check + `release APP-060 --done` (ticket AC ticks, stage checklist).  
**Stage 7:** Manual creation-table submit, long GM reply, wheel-up-then-submit, error visibility.
