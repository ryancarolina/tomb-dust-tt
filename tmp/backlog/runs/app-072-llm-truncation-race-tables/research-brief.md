# Research Brief: APP-072-llm-truncation-race-tables

**Date:** 2026-05-20  
**Question:** How do duplicate or truncated race tables appear in creation narration, and where should flavor sanitization live so RACE body stays code-only?

**backlog_ticket:** APP-072  
**ticket_path:** tmp/backlog/app-072-llm-truncation-duplicate-race-tables.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) is the registered owner for `app/gm/creation.py` and the creation branch of `app/gm/orchestrator.py` ([`tmp/app-master-spec.md`](../../../app-master-spec.md) § Spec registry — Character creation). APP-072 expected files are a subset of that domain (`orchestrator.py`, `creation.py`, `test_creation_tables.py`, domain spec changelog). No new domain spec row is required.

## Summary

The **code-first RACE path** already sets `body = format_races_table()` in `_auto_present_race`, but **flavor is unconstrained** beyond a system prompt and `max_tokens=120`. The model can still emit a full 16-row markdown race table in flavor; when the response hits **`finish_reason: length`**, the table truncates mid-row, and `_compose_creation_narration` appends the **complete** code table unchanged — producing **two** `\| Race \|` blocks in one `gm_narration` (ticket evidence: Caddy @ 16:44:41).

`_compose_creation_narration` only runs `strip_llm_status_tags` on flavor — **no** markdown-table stripping and **no** branch on `finish_reason`. Integration tests use `mock_openrouter_client`, which always returns `"Test narration."` with `finish_reason: stop`, so they **cannot** regress duplicate or truncated flavor tables. `app/tests/test_creation_tables.py` is listed in the ticket but **does not exist** yet.

The ticket’s opposite failure (Bumpy: single ~10k-char LLM table, no code table) likely reflects an **older or alternate** path (pre-APP-006/068) or a turn where presentation did not reach `_auto_present_race`; current `_creation_turn_body` always chains code `format_races_table()` when presenting RACE. Fix should centralize **flavor sanitization** (strip `\| Race \|` table blocks, optional length/finish_reason handling) before compose, with a **unit/integration test** that stubs an embedded-table LLM response.

**APP-059 / APP-074:** `format_races_table()` still includes a **Description** column (wide cells); APP-072 close should note spec sync per ticket. Dead `get_step_prompt()` still documents “output EXACT markdown table” for RACE — no runtime caller ([APP-074](../../../app-074-remove-dead-get-step-prompt.md)).

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Flavor LLM | `app/gm/orchestrator.py` | `_CREATION_FLAVOR_MAX_TOKENS = 120`, `_narrate_flavor`, `_creation_flavor_messages` |
| RACE present | `app/gm/orchestrator.py` | `_auto_present_race` — flavor then `format_races_table()` |
| Compose | `app/gm/orchestrator.py` | `_compose_creation_narration` — `strip_llm_status_tags` only |
| Race table body | `app/gm/creation.py` | `format_races_table()` — 16 races, Description column |
| Legacy prompts | `app/gm/creation.py` | `get_step_prompt()` RACE branch embeds same table — **uncalled** |
| Status strip | `app/gm/creation.py` | `strip_llm_status_tags` — Awaiting/Phase tags, not tables |
| Drift QA | `app/gm/orchestrator.py` | `_check_creation_drift` — footer tags only; no `\| Race \|` in flavor |
| Tests | `app/tests/test_creation_flow.py`, `conftest.py` | Asserts one code race header; stub flavor constant |
| Missing | `app/tests/test_creation_tables.py` | Ticket Expected file — not in repo |
| Logging | `app/gm/logger.py` | `log_llm_response` records `finish_reason`, `content_length` |
| Session evidence | `app/logs/session-2026-05-20.jsonl` | **gitignored**; cited in ticket, not in workspace |

## Code-path traces

### A — RACE presentation (normal / NAME→RACE chain)

1. **Entry:** `_creation_turn_body` when `creation.step == "RACE"` and (`is_system_trigger` or `not races_table_shown`) → `_auto_present_race` (`orchestrator.py` ~603–604, ~694–704).
2. **Flag:** `races_table_shown = True` before LLM call.
3. **Flavor:** `_narrate_flavor(_creation_flavor_messages("The clerk writes down '{name}'…", player_input))` — system text says “Do NOT include markdown tables” (`orchestrator.py` ~539–556, ~697–701).
4. **LLM:** `chat_completion(..., max_tokens=120)`; logs `finish_reason` but **returns raw content** (`orchestrator.py` ~558–575).
5. **Body (authoritative):** `err + format_races_table()` from `creation.py` ~544–555.
6. **Compose:** `_compose_creation_narration(flavor, body)` → `strip_llm_status_tags(flavor)` + body + `format_creation_status` → `Awaiting: RACE_INPUT` (`orchestrator.py` ~520–537).
7. **Persist:** `_emit_narration` → history append full composed string (`orchestrator.py` ~660–662).

**Failure injection:** If step 4 returns a partial markdown table (length) or full table (model ignores prompt), step 6 concatenates both → duplicate `\| Race \| Adjustments \| Description \|` headers in one narration.

### B — RACE re-prompt (invalid input)

1. **Entry:** `step == "RACE"` and `races_table_shown` → `_handle_creation_response` or `_auto_present_race` with error (`orchestrator.py` ~605–608).
2. Same flavor + `format_races_table()` path as A — duplicate-table risk on every re-show.

### C — Chain after NAME commit (APP-068)

1. `_execute_creation_choice("NAME")` → `advance()` → `RACE`, `races_table_shown = False` (`creation.py` advance on RACE entry).
2. `_chain_after_creation_choice` or direct return calls `_auto_present_race` — trace A applies in same `process_turn`.

### D — What does *not* run

- `_creation_llm_loop` — defined, **zero callers** (historical LLM+tool race tables).
- `get_step_prompt()` — **zero callers** under `app/` (legacy “EXACT markdown table” instruction).
- Exploration `_llm_loop` — blocked while `creation.active`.

## Existing specs & docs

- **Ticket:** `tmp/backlog/app-072-llm-truncation-duplicate-race-tables.md` — AC: code-only RACE body, flavor ≤2 sentences, strip `\| Race \|`, no duplicate tables, mock test.
- **Domain spec:** `tmp/app-character-creation-spec.md` — presentation pattern (flavor + code body + footer); APP-072 owns flavor table strip; test row “LLM duplicate race table” (~364).
- **Related:** [APP-059](../../../app-059-standardize-creation-table-outputs.md) (Description column / UI width), [APP-067](../../../app-067-code-owned-roll-stats-table.md) (code-owned body pattern), [APP-069](../../../app-069-creation-narration-must-match-fsm-step.md) (optional `narrated_step_mismatch` — not implemented), [APP-074](../../../app-074-remove-dead-get-step-prompt.md) (dead race prompt).
- **AGENTS.md:** app spec drift policy; no ticket needed for run artifacts.

## Tests & commands

```bash
# Existing — does not cover duplicate flavor tables
python -m pytest app/tests/test_creation_flow.py -q

# After impl (ticket)
python -m pytest app/tests/test_creation_tables.py -q
```

**Acceptance mapping (ticket → implementation locus):**

| AC | Suggested locus |
|----|-----------------|
| RACE body only `format_races_table()` | Already true in `_auto_present_race`; enforce via flavor strip + tests |
| Flavor ≤2 sentences, no tables | `_creation_flavor_messages` + post-sanitize in `_compose_creation_narration` or `_narrate_flavor` |
| Strip `\| Race \|` / token budget | New helper in `creation.py` or orchestrator; call before compose |
| No duplicate `\| Race \|` in one turn | Assert in new `test_creation_tables.py` with custom mock content |
| Spec sync APP-059 | Domain spec changelog on close (Description column policy) |

## Risks & unknowns

- **Over-stripping:** Naive line filter on `\|` may damage rare prose; prefer detecting markdown **table blocks** (header + separator + rows) scoped to race header fingerprint.
- **Scope creep:** Same sanitization may be needed for `\| Attr \|`, `\| Category \|`, etc., if models emit other step tables in flavor — ticket is RACE-focused; consider shared `strip_flavor_markdown_tables(markers)` for all `_auto_present_*`.
- **`finish_reason: length`:** Logged but ignored; retry vs truncate-vs-strip policy undefined in ticket.
- **History bias:** `_creation_flavor_messages` includes `history[-4:]` with prior assistant messages that **contain** full race tables — may encourage the model to regenerate tables in flavor.
- **Bumpy 10k table:** Not reproduced on current code path without reading local session log; treat as historical unless playtest confirms on current `main`.
- **APP-059 column change:** If Description column is removed later, duplicate-detection tests should key on stable header/substrings agreed in spec.
- **UI:** PyGame `render_table` truncates wide cells separately from narration duplication (APP-059).

## Raw notes

### Token / size budget

- `_CREATION_FLAVOR_MAX_TOKENS = 120` (~480 chars upper bound; actual provider behavior varies).
- Full `format_races_table()` is ~3–4k+ characters (16 races × Description prose) — far exceeds flavor budget if model attempts full table in flavor.

### Duplicate detection heuristic

- Count occurrences of `\| Race \| Adjustments \| Description \|` in composed narration — expect **1** after fix.
- Truncated LLM table often lacks closing rows or ends mid-cell (ticket: cut-off Human row).

### `format_races_table` (code body)

```544:555:app/gm/creation.py
def format_races_table() -> str:
    lines = [
        "Pick **one race**. Reply with the race name.",
        "",
        "| Race | Adjustments | Description |",
        ...
```

### `_auto_present_race` compose

```694:704:app/gm/orchestrator.py
    def _auto_present_race(self, player_input: str, error: str | None = None) -> str:
        self.creation.races_table_shown = True
        ...
        flavor = self._narrate_flavor(...)
        body = err + format_races_table()
        return self._compose_creation_narration(flavor, body)
```

### Legacy `get_step_prompt` (dead)

```694:708:app/gm/creation.py
    if state.step == "RACE":
        ...
        "Present this EXACT markdown table of all 16 races ..."
```

### Test gap

- `mock_openrouter_client` → `"Test narration."`, `finish_reason="stop"` always (`conftest.py` ~46–58).
- `test_creation_flow.py` asserts `\| Race \|` **in** narration but not **count == 1**.

### Session log (ticket, not verified locally)

| Time | Symptom |
|------|---------|
| 16:44:41 | `finish_reason: length`; truncated LLM race table + full code table |
| Earlier Bumpy | Single LLM ~10k race table, no code table (opposite mode) |
