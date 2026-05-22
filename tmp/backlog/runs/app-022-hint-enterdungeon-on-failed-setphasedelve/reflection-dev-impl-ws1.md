# Dev implementation reflection — APP-022 (WS1)

**backlog_ticket:** APP-022  
**Date:** 2026-05-22

## What shipped

1. **`_delve_entry_tool_hint`** — module helper after `_SITE_ENTRY_REFUSAL_LINE`; core copy names `compass_exits` then `enter_dungeon(site_address)`; optional R4 suffix when `below_addresses` provided.

2. **`_should_delve_entry_hint`** — predicate: `set_phase` + normalized `phase=="delve"` + `ok: false`.

3. **`_build_delve_entry_hint`** — instance helper; calls `bridge.compass_exits()` in try/except; collects `exits.below[].address`; never fails hint build.

4. **Sticky `_delve_entry_hint_this_turn`** — init `None`; reset at `_llm_loop` depth 0; set on first triggered failure in batch (mirrors APP-024 `entry_committed_this_turn`).

5. **R1 + R2 in tool loop** — before `log_tool_call`: enrich failed result with `"hint"`; append ` Hint: …` to system `TOOL FAILED` inject.

6. **R3 in `all_failed and content`** — at depth 0 with sticky hint: `prefix\n\n{hint}\n\n{safe}`; combat-tool early return unchanged; partial success skips R3 because `all_failed` is false.

7. **`app/tests/test_exploration_set_phase_delve_hint.py`** — T1–T6: tool JSON hint, player banner via `process_turn`, ingress no-hint, success no-hint, partial success no R3 banner, system message inspect via direct `_llm_loop`.

## Deviations / notes

- Hint inject uses plain tool names (no markdown `**`) per plan — matches system-message style; domain spec keeps bold for docs.
- T2 uses `process_turn` so double `_compose_exploration_narration` path is exercised (inherited APP-024); hint text avoids `_SITE_ENTRY_MARKER_RES`.
- Optional R4 below-address test not added — hub cell may lack `below` in test fixture; core hint satisfies AC.
- No edits to bridge, tools, prompt, or FSM (in scope).

## Verification

```text
python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -v
6 passed in 1.98s
```

## Risks / follow-ups

- If `compass_exits()` is slow or flaky, hint build is wrapped in try/except — core hint still emitted.
- Orchestrator spec open-work checklist update noted in plan §6 — coordination on `release --done`, not impl Expected files.
