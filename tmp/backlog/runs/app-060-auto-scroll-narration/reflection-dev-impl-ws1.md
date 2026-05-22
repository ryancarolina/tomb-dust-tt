# Dev reflection — APP-060 implementation (ws1)

**Ticket:** APP-060  
**Agent:** Dev  
**Date:** 2026-05-22

## What was implemented

1. **`NarrationPanel._follow_tail`** — deferred tail pin flag; `request_follow_tail()` sets flag without scrolling.
2. **`draw()` tail block** — after `_rebuild()` when dirty, applies `scroll_to_bottom()` and clears flag so offset uses fresh `_total_height`.
3. **`clear()` reset** — clears pending `_follow_tail` so a clear in the same frame cannot spuriously scroll.
4. **`App._smooth_scroll_to_bottom()`** — thin wrapper now calls `request_follow_tail()` instead of immediate `scroll_to_bottom()`.
5. **Error path** — `msg_type == "error"` handler calls `_smooth_scroll_to_bottom()` after `add_line` (init failure, turn exception, orchestrator errors).
6. **Tests** — 6 cases in `test_narration_scroll.py`: stale pre-rebuild scroll, follow-tail pin, player/error lines, coalesce, clear reset.
7. **Domain spec** — APP-060 moved to checklist done; changelog entry appended.

## Deviations / notes

- **`test_stale_scroll_before_rebuild_fails`:** Compares stale offset to post-`draw()` expected bottom (not pre-rebuild `_total_height == 0`) so the regression is unambiguous on CI.
- **Tall fixture:** Markdown table + long notes row exceeds 120px viewport on Windows Consolas without extra tuning.
- **No App-level error queue test:** Panel error test + single handler wiring point per plan optional note.

## Verification

```text
python -m pytest app/tests/test_narration_scroll.py -v  → 6 passed
```

## TurnTruth gate

No LLM narration/orchestrator paths touched — N/A for APP-060.

## Risks for QA

- Short single-line player/error replies may not visibly exercise scroll (offset 0 == bottom); tall-table manual repro still required for AC.
- Session load (`_load_session`) intentionally does not auto-pin — out of scope per spec.
