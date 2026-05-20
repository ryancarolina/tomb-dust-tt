# Spec: APP-072-llm-truncation-race-tables

**Status:** draft  
**backlog_ticket:** APP-072  
**ticket_path:** [tmp/backlog/app-072-llm-truncation-duplicate-race-tables.md](../../app-072-llm-truncation-duplicate-race-tables.md)  
**domain_spec:** [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-character-creation-spec.md`

## Problem

At the RACE step, `_auto_present_race` already sets `body = format_races_table()`, but `_narrate_flavor` can return a full or **truncated** markdown race table (`finish_reason: length` at 120 tokens). `_compose_creation_narration` only runs `strip_llm_status_tags` on flavor — no table strip — so one turn can show **two** `\| Race \|` blocks (broken LLM table + complete code table). Opposite historical failure (LLM-only ~10k table, no code body) is not reproduced on current `_creation_turn_body` path.

**Evidence:** Caddy session @ 16:44:41 — `session-2026-05-20.jsonl` (gitignored).

## Goals

- RACE **body** remains **only** `format_races_table()` (already true; enforce via tests).
- RACE **flavor** is ≤2 sentences with **no** markdown tables — prompt + post-sanitize before compose.
- Strip `\| Race \|` table blocks (including truncated rows) from flavor; composed narration has **exactly one** race table header from the code body.
- New `app/tests/test_creation_tables.py` contract for duplicate-table regression (mock LLM embedded table).

## Non-goals

| Deferred | Ticket |
|----------|--------|
| Remove Description column from `format_races_table()` cells | [APP-059](../../app-059-standardize-creation-table-outputs.md) — catalog target documented; formatter change is APP-059 code |
| Strip `\| Attr \|`, `\| Category \|`, etc. from flavor on other steps | Out of APP-072 scope (optional shared helper later) |
| Retry on `finish_reason: length` | Strip prose-only flavor; no automatic LLM retry unless Dev plan adds one |
| Remove dead `get_step_prompt()` RACE branch | [APP-074](../../app-074-remove-dead-get-step-prompt.md) |
| Omit `history` from flavor messages | [APP-069](../../app-069-creation-narration-must-match-fsm-step.md) — reduces table regen bias; not blocking APP-072 |

## Requirements (summary)

Full behavior and test contracts: domain spec § **RACE flavor must not duplicate code table (APP-072)**.

| ID | Summary | Locus |
|----|---------|-------|
| **R1** | `_auto_present_race` body = `err_prefix + format_races_table()` only | `orchestrator.py` `_auto_present_race` |
| **R2** | Flavor system prompt: no markdown tables (existing); strengthen if needed | `_creation_flavor_messages` |
| **R3** | Post-LLM sanitize: remove markdown table blocks whose header matches `\| Race \|` (and separator + data rows) from flavor before `_compose_creation_narration` | `creation.py` helper (preferred) or orchestrator; call from `_compose_creation_narration` or `_auto_present_race` |
| **R4** | If flavor still contains `\| Race \|` after block strip, drop table lines / keep prose only | Same helper |
| **R5** | Composed RACE narration: `count("\| Race \| Adjustments \|") == 1` | Integration test |
| **R6** | Optional: log when strip runs or `finish_reason == "length"` on RACE flavor | `logger.py` / existing `log_llm_response` |

### Sanitizer design notes (Dev)

- Prefer **block-scoped** strip (header row + `\|[-:| ]+\|` separator + subsequent `\|…\|` rows) keyed on `\| Race \|`, not naive strip of every `\|` line.
- **Stable fingerprint** for duplicate assertions: `\| Race \| Adjustments \|` — survives APP-059 removal of Description column from formatter output.
- Call sanitize on **flavor only**, never on `body` (code table is authoritative).
- `_compose_creation_narration` is a reasonable single call site if sanitizer is step-agnostic (`strip_flavor_race_table(text) -> str`).

## APP-059 alignment

[APP-059](../../app-059-standardize-creation-table-outputs.md) catalog decision: RACE in-table columns are **Race + Adjustments only**; lore stays in flavor (≤2 sentences), **not** in cells. Current `format_races_table()` still emits a Description column — **APP-059** owns formatter/UI change. APP-072:

- Documents catalog target in domain spec § Creation tables.
- Does **not** require Description removal to close APP-072.
- Tests key on `\| Race \| Adjustments \|` so they remain valid when APP-059 drops Description.

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| RACE body only `format_races_table()` | R1 + existing `_auto_present_race` path |
| Flavor ≤2 sentences, no tables | R2 + R3–R4 |
| Strip `\| Race \|` / token budget | R3–R4 (`_CREATION_FLAVOR_MAX_TOKENS = 120` unchanged) |
| No duplicate race tables in one turn | R5 — `test_creation_tables.py` |
| Spec sync APP-059 | Domain spec catalog row + changelog |
| Mock LLM embedded table test | § Tests APP-072 in domain spec |

## Test plan

```bash
python -m pytest app/tests/test_creation_tables.py -q
python -m pytest app/tests/test_creation_flow.py -q   # no regressions
```

**Primary new tests** (module `app/tests/test_creation_tables.py`):

| Test | Setup | Pass |
|------|-------|------|
| `test_race_narration_single_table_header` | Monkeypatch/stub `_narrate_flavor` or LLM client to return flavor containing `\| Race \| Adjustments \| Description \|` + partial rows | After `process_turn` to RACE (NAME commit), narration `count("\| Race \| Adjustments \|") == 1`; code intro `Pick **one race**` present |
| `test_strip_flavor_race_table_unit` | Direct call on helper with truncated table + prose | Output has no `\| Race \|`; prose retained if any |
| `test_format_races_table_contract` (optional) | Call `format_races_table()` | Header contains `\| Race \| Adjustments \|`; 16 data rows; documents current vs APP-059 target in docstring |

Use `orchestrator` + `mock_openrouter_client` from `conftest.py` with **patched return content** for embedded-table case (default stub `"Test narration."` cannot regress this bug).

## Expected files (implementation)

- `app/gm/creation.py` — `strip_flavor_race_table()` (or equivalent)
- `app/gm/orchestrator.py` — wire sanitize before compose on RACE (or inside `_compose_creation_narration` for flavor input)
- `app/tests/test_creation_tables.py` — **new** per ticket
- `tmp/app-character-creation-spec.md` — changelog on close

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **NAME→RACE:** After name entry, narration shows **one** race table block; clerk flavor above is 1–2 sentences without a second table.
- **Forced length (optional):** If using a live model, watch `app/logs/session-*.jsonl` for `finish_reason: length` on RACE — narration must not show a cut-off table **above** the full code table.
- **Re-prompt:** Invalid race pick re-shows table — still only one `\| Race \| Adjustments \|` header in that turn.

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — traces A/B/C, token budget, test gap
- **Domain truth:** [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md) — § RACE flavor must not duplicate code table (APP-072); § Creation tables (APP-059 target)
- **Related:** APP-059 (column catalog), APP-067 (code-owned body pattern), APP-069 (history bias), APP-074 (dead race prompt)
