# Research Brief: APP-024-block-site-fiction

**Date:** 2026-05-21
**Question:** Where and how should the orchestrator block site-entry fiction unless the current turn's tool chain ended with a successful `enter_dungeon` or `site_enter`?

**backlog_ticket:** APP-024
**ticket_path:** tmp/backlog/app-024-block-site-fiction-without-enter-tool.md
**domain_spec:** tmp/app-exploration-delve-spec.md
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket domain spec is [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) — it already states **"Never narrate entering a site without successful `enter_dungeon` / `site_enter`"** (Delve play §) and lists the problem in § Problem (from logs). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Exploration & delve** owns `travel/site tools in orchestrator + map UI`. Cross-cutting mechanical-truth rule also appears in [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) § Mechanical truth. No new domain spec file needed.

## Summary

The bug is prompt-only today: `system_prompt.py` forbids narrating site entry without tools, but exploration narration from `_llm_loop` is returned raw to `_emit_narration` with no post-process gate. When the LLM skips tools or tools fail, fiction still reaches the player — especially via the `all_failed and content` early-return path that prepends a failure banner but keeps the model's success prose.

Creation has code-owned sanitizers (`strip_llm_status_tags`, `sanitize_premature_completion_flavor`) and drift logging; combat hard-gates tools to `combat_action` and uses a two-phase mechanics-then-narrate loop. Exploration has neither a compose/sanitize step nor tool-success enforcement for site entry.

Implementation should live in `orchestrator.py` (ticket Expected files): track successful entry tools across the `_llm_loop` chain, then strip or replace site-entry prose when `party.mode` is still surface (or otherwise not committed) and no successful `enter_dungeon` / `site_enter` occurred this turn. APP-077 (code-owned exploration footer) is complementary — it fixes status-line lies, not interior fiction.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Turn entry | `app/gm/orchestrator.py` `process_turn` | Builds context, calls `_llm_loop`, `_emit_narration` |
| LLM + tools | `app/gm/orchestrator.py` `_llm_loop`, `_execute_tool` | Resets `_last_tool_results` at depth 0; recurses until no tool_calls |
| Entry dispatch | `app/gm/orchestrator.py` `_execute_tool` L2050–2090 | `site_enter` → `bridge.site_enter`; `enter_dungeon` maps `site_id` alias → `bridge.enter_dungeon` |
| Bridge entry | `app/gm/bridge.py` `site_enter`, `enter_dungeon` | Two paths: legacy graph (`mode=site`) vs exploration rooms (`mode=dungeon`) |
| Engine commit | `play/tomb_gm/services/site.py` `enter_site` | Legacy: `mode='site'`, `site_node_id` |
| Engine commit | `play/tomb_gm/services/exploration.py` `enter_site` | Room nav: `mode='dungeon'`, `dungeon_room_id` |
| LLM context | `app/gm/context.py` `build_state_context` | Exposes `party.mode`, site id, dungeon_info when in site |
| Prompt rules | `app/gm/system_prompt.py` L215–268 | Mandates tools-first; warns against site entry without tool — not enforced in code |
| Creation gate pattern | `app/gm/orchestrator.py` `_compose_creation_narration`, `_check_creation_drift` | Strip/sanitize + log-only drift — mirror for exploration fiction |
| Combat gate pattern | `app/gm/orchestrator.py` `_combat_llm_loop_inner`, `_execute_tool` L2020–2026 | Hard tool allowlist during combat |
| Tool schemas | `app/gm/tools.py` | Both `site_enter` and `enter_dungeon` exposed |
| Mechanical truth spec | `tmp/app-llm-orchestrator-spec.md` L13–15 | "site entry" outcomes require `ok: true` tool |
| Related tickets | APP-022 (hint on failed `set_phase`), APP-077 (footer), APP-028 (combat failure narration) | APP-024 is code gate; APP-022 is failure hints only |

## Code-path traces

### Exploration turn → narration (happy path)

1. Entry: `orchestrator.py:process_turn` — after creation/combat branches, loads `status`/`check`/`suggest`/`exploration`, builds messages.
2. `_llm_loop(messages, depth=0)` — `chat_completion` with full `TOOLS`.
3. Model returns `tool_calls` (e.g. `enter_dungeon`) + optional assistant `content`.
4. `_execute_tool` → `bridge.enter_dungeon` → `ExplorationService.enter_site` sets `party_state.mode='dungeon'`.
5. On `ok: true`, tool result appended; loop recurses until model returns text-only response.
6. Exit: `process_turn` L813–814 — `narration = self._llm_loop(...)` then `_emit_narration(narration)` with **no exploration sanitizer**.

### Site entry without tool commit (failure path)

1. Player asks to enter crypt; model returns `content` only (no `tool_calls`) **or** calls failing tools (`set_phase(delve)`, bad `enter_dungeon` args).
2. `_llm_loop` L1959–1960: if no tool_calls, returns raw `content` immediately.
3. Or L1999–2006: if all tools failed but assistant had `content`, returns `"[Mechanics failed — …]\n\n{content}"` — **success fiction preserved**.
4. Failed tools inject system message L1986–1991 ("MUST narrate failure") but model may ignore on recurse or early return.
5. `_emit_narration` L317–319 only runs `_check_creation_drift` — no exploration fiction check.
6. Persistence: DB still `mode=surface`; player read fiction contradicting `build_state_context` Location line.

### `enter_dungeon` vs `site_enter`

1. **`enter_dungeon`** (preferred in prompt L236–238): `bridge.enter_dungeon` → resolve AV-GRID/slug → `ExplorationService.enter_site` → `mode='dungeon'`.
2. **`site_enter`** (also in TOOLS + prompt L218): `bridge.site_enter` → `tomb_gm.services.site.enter_site` → `mode='site'`, graph node navigation.
3. Ticket AC names **both** as valid commit tools; gate must treat either successful `ok: true` as authorization for entry fiction on that turn.

### Existing gating patterns (templates for APP-024)

1. **Creation sanitize** (`creation.py:sanitize_premature_completion_flavor`, orchestrator `_compose_creation_narration`): regex blanking of forbidden flavor; code-owned body/footer appended after strip.
2. **Creation drift** (`_check_creation_drift`): logs `premature_exploration_phase` when narrated phase is delve/ingress without engine match — **telemetry only, does not block**.
3. **Combat tool gate** (`_execute_tool` combat branch): rejects non-`combat_action` tools at dispatch.
4. **Combat narrate** (`_combat_llm_loop_inner` L1867–1880): second LLM call with mechanical brief, `tools=None` — separates mechanics from fiction.

## Existing specs & docs

- Ticket domain spec: [`tmp/app-exploration-delve-spec.md`](../../../app-exploration-delve-spec.md) — Delve play rule + Problem bullet "GM narrated entering crypt without tool commit"
- Orchestrator spec: [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) — mechanical truth includes site entry
- GameBridge: [`tmp/app-gamebridge-spec.md`](../../../app-gamebridge-spec.md) — `enter_dungeon` alias documented (APP-021)
- APP-077: code-owned exploration footer — complementary, not substitute for fiction gate
- APP-022: hints on failed `set_phase(delve)` — does not block fiction

## Tests & commands

```bash
# Engine site entry (no app fiction gate today)
python -m pytest play/tomb_gm/tests/test_site.py -q
python -m pytest play/tomb_gm/tests/test_beat.py -q -k site_enter

# App tests — none cover exploration fiction gate yet
python -m pytest app/tests/ -q

# Content / integration
python build/tools/validate_content.py
python -m tomb_gm --workspace play/workspace check
```

**Test gap:** No `app/tests/test_*` for `_llm_loop` exploration post-process or site-entry sanitizer. PM should require mock-LLM tests (pattern referenced in orchestrator spec L76) asserting: surface mode + narration with entry markers + no successful entry tool → stripped or replaced.

## Risks & unknowns

- **AC scope:** "last tool was successful enter_dungeon / site enter" — clarify whether gate applies only when `party.mode` is surface/`site` pre-entry, or on every turn (must not block in-dungeon room description when no re-entry tool called).
- **Dual entry systems:** `enter_dungeon` sets `mode=dungeon`; `site_enter` sets `mode=site`. Sanitizer must accept both and not assume only `dungeon`.
- **`all_failed` early return:** L1999–2006 is a primary leak path; fix may need to drop or rewrite `content` when entry fiction detected, not only post-process final narration.
- **Regex brittleness:** Creation uses marker regexes; site-entry fiction ("you step into the crypt", "torchlight reveals", wrong `mode: dungeon` in LLM status line) may need marker set + engine mode check hybrid.
- **Prompt inconsistency:** `system_prompt.py` L218 says `site_enter`; L236–268 emphasize `enter_dungeon`. Out of ticket Expected files but may confuse model until aligned.
- **APP-077 overlap:** If both land, coordinate `strip_llm_status_tags` / compose helper so APP-024 fiction gate and APP-077 footer compose share one pipeline.
- **Session evidence:** Domain spec cites log failure; session JSONL is gitignored — not replayed in this research run.

## Raw notes

### Key orchestrator snippets

- `_last_tool_results` reset at `_llm_loop` depth 0 (L1925–1926); dict keyed by tool name — last result per name only if multiple calls same tool.
- `_emit_narration` → `log_gm_narration` + `_check_creation_drift` only.
- `build_state_context` already shows `mode: surface` when not entered — model still hallucinates entry.

### grep: site / enter in app

```
app/gm/orchestrator.py:2050 site_enter, 2086 enter_dungeon
app/gm/system_prompt.py:218 site_enter rule, 268 enter_dungeon rule
app/gm/tools.py:127 site_enter schema, 378 enter_dungeon schema
```

### Domain spec problem (from logs)

- `enter_dungeon(site_id=…)` wrong param (bridge alias fixed APP-021)
- `set_phase(delve)` rejected from `preparation`
- GM narrated entering crypt without tool commit ← **APP-024 target**

### Related backlog

| Ticket | Relationship |
|--------|--------------|
| APP-022 | Hint correct tool on failed set_phase — not fiction block |
| APP-077 | Code-owned status footer — fixes bracket lies, not interior prose |
| APP-028 | Combat failure narration — parallel "mechanics failed" content leak class |

### Proposed implementation loci (for PM/Dev — not spec)

1. Track `_turn_entry_committed: bool` or scan `_last_tool_results` for successful `enter_dungeon`/`site_enter` at end of `_llm_loop`.
2. Add `sanitize_premature_site_entry_flavor(narration, *, mode, entry_committed)` — possibly in orchestrator or shared module with creation strippers.
3. Wire in `process_turn` after `_llm_loop` before `_emit_narration`, gated on `party.mode not in ('dungeon', 'site')` OR `not entry_committed`.
4. Optional: `log_exploration_drift` when strip fires (mirror APP-002 creation_drift).
