# Spec: APP-073-strip-llm-embedded-status-tags-in-creation

**Status:** draft  
**backlog_ticket:** APP-073  
**ticket_path:** [tmp/backlog/app-073-strip-llm-embedded-status-tags-in-creation.md](../../app-073-strip-llm-embedded-status-tags-in-creation.md)  
**domain_spec:** [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-character-creation-spec.md`

## Problem

APP-007 shipped `format_creation_status()` and a **partial** `strip_llm_status_tags()` — bracket `[Location:…]` / `[Phase:…]` blocks and **whole-line** `Awaiting:` only. Inline or mid-sentence wrong labels (`Awaiting: SKILL_INPUT`, `MAGIC_SCHOOLS_INPUT`, `EQUIPMENT_CONFIRMATION`) survive in flavor, appear **before** the code footer, and become the **first** match for `parse_narration_status_line()` → `creation_drift` `awaiting_mismatch` and stale APP-065 chips.

APP-072 added `strip_flavor_race_table()` for RACE duplicate tables; **no equivalent** exists for ROLL_STATS. `_auto_roll_stats()` rolls in code and appends `format_roll_stats_table()` + `format_classes_table()` in the body, but thin LLM flavor (`max_tokens=120`) still invents attribute markdown (`### Your Attributes`, compact `| STR | AGI | … |`, truncated `` `roll_attributes( ``) with **wrong numbers**. Model swap does not fix it.

**Evidence:** `session-2026-05-20.jsonl` — Spluffy/Tuffy undead roll turns; Supa/Bumpy wrong awaiting labels (gitignored; cited in ticket).

## Goals

- Flavor after sanitizers is **prose only** — no status tags, no duplicate mechanical tables.
- Player-facing narration has **exactly one** `Awaiting:` from `format_creation_status()` (or explicit reception `footer` at finalize).
- ROLL_STATS → CLASS turn shows **one** attribute breakdown from `format_roll_stats_table`; Final values match `roll_attributes` / `creation.roll_result`.
- Complete APP-007 strip behavior in spec + code; note APP-007 checklist item superseded by APP-073.

## Non-goals

| Deferred | Ticket |
|----------|--------|
| Suggestion chip source-of-truth / stale clear | [APP-065](../../app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md) — implement after APP-073 per batch board |
| Strip `\| Category \| Skill \|`, `\| School \|`, class tables from flavor on other steps | Out of APP-073 scope (shared helper future ticket) |
| Retry on `finish_reason: length` | Post-hoc strip only; no automatic LLM retry |
| Remove Description column from race table | [APP-059](../../app-059-standardize-creation-table-outputs.md) |
| Change `SYSTEM_PROMPT` exploration state-line template | Sanitizer is pass gate; prompt-only fix insufficient |

## Requirements (summary)

Full behavior and test contracts: domain spec § **Flavor sanitization pipeline (APP-073)**.

| ID | Summary | Locus |
|----|---------|-------|
| **S1** | Harden `strip_llm_status_tags`: remove bracket Location/Phase anywhere; remove **any** `Awaiting:` token in flavor (inline or whole-line), not only `^\s*Awaiting:…$` | `creation.py` `_LLM_STATUS_TAG_RE` / `strip_llm_status_tags` |
| **S2** | Add `strip_flavor_stats_table(text)` mirroring APP-072 block-scoped strip — fingerprints: `### Your Attributes`, `\| Attr \| Base \|`, compact attr header (`\| STR \| AGI \| STA \| … \|`), `` `roll_attributes( `` fragments | `creation.py` |
| **S3** | Wire stats strip in `_compose_creation_narration` **after** `strip_flavor_race_table`, **before** `_sanitize_creation_flavor`; flavor only — never `body` or `footer` | `orchestrator.py` |
| **S4** | `_compose_creation_narration` remains sole composer of footer + mechanical body; C5 re-strip after premature sanitizer still applies | `orchestrator.py` |
| **S5** | Tighten `_auto_roll_stats` flavor instruction: clerk reaction to dice only — **no** numbers, HP, or markdown tables (code appends roll readout) | `orchestrator.py` `_auto_roll_stats` |
| **S6** | Global `_creation_flavor_messages` already forbids status lines and tables; step instructions must not teach non-canonical labels (`SKILL_INPUT`, `MAGIC_SCHOOLS_*`, `EQUIPMENT_CONFIRMATION`) | `orchestrator.py` |
| **S7** | Composed ROLL_STATS narration: `count("\| Attr \| Base \|") == 1`; Final column matches `roll_result["final_attributes"]` | Integration test |
| **S8** | Composed narration with bad-flavor fixture: single canonical footer; no duplicate stat/race table headers in flavor region; no inline wrong `Awaiting:` before footer | Unit + compose tests |

### Compose order (flavor, after APP-073)

`strip_llm_status_tags` → `strip_flavor_race_table` (APP-072) → **`strip_flavor_stats_table` (APP-073)** → `_sanitize_creation_flavor` (APP-069) → `sanitize_premature_completion_flavor` (APP-070, when active or empty roster) → re-run `strip_llm_status_tags` if premature sanitizer mutated (C5) → append code `body` + `format_creation_status` footer.

### Acceptable alternative (ROLL_STATS)

Skip LLM flavor entirely on ROLL_STATS (code-only intro line + tables). If Dev chooses this, document in domain spec § ROLL_STATS orchestration and adjust tests — **default spec path:** keep thin flavor + stats strip.

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| Bracket Location/Phase anywhere in flavor | S1 — domain spec § `strip_llm_status_tags` hardened |
| Remove any `Awaiting:` in flavor | S1 |
| `_compose_creation_narration` prose-only flavor after sanitizers | S3–S4 |
| Prompts do not teach non-canonical labels | S5–S6 |
| `strip_flavor_stats_table` + compose wiring | S2–S3 |
| ROLL_STATS single authoritative table | S7 |
| Tests: bad status + stat table flavor → clean compose | S8 — `test_creation_flavor_sanitize.py` |
| Spec sync; APP-007 note completed | Domain spec changelog |

## Test plan

```bash
python -m pytest app/tests/test_creation_flavor_sanitize.py -q   # new per ticket
python -m pytest app/tests/test_creation_tables.py -q            # no regressions (APP-072)
python -m pytest app/tests/test_creation_flow.py -q              # golden path
```

**Primary new tests** (`app/tests/test_creation_flavor_sanitize.py` or extend `test_creation_tables.py`):

| Test | Setup | Pass |
|------|-------|------|
| `test_strip_llm_status_tags_inline_awaiting` | Direct call: `"Clerk nods. Awaiting: SKILL_INPUT"` + bracket blocks | No `Awaiting:` in output; prose retained where applicable |
| `test_strip_flavor_stats_table_unit` | Direct call: `### Your Attributes` block, full `\| Attr \| Base \|` table, compact `\| STR \| AGI \|`, `` `roll_attributes( `` fragment | No stat-table fingerprints; prose retained |
| `test_compose_flavor_sanitize_status_and_stats` | Call `_compose_creation_narration` (or orchestrator with patched flavor) with embedded status + stat table in flavor, code body with real table | One `\| Attr \| Base \|`; one `Awaiting:` matching `CREATION_STATUS_LABELS[step]`; no wrong label in flavor region |
| `test_roll_stats_narration_single_stats_table` | Stub LLM returns stat-table flavor on RACE→ROLL_STATS turn (`"human"` or `"undead"`) with `FIXED_ROLL` monkeypatch | `count("\| Attr \| Base \|") == 1`; Final values match fixture; `Awaiting: CLASS_INPUT` |

Use `_patch_llm_content` / monkeypatch `create_client` — default mock `"Test narration."` cannot regress leaks.

## Expected files (implementation)

- `app/gm/creation.py` — hardened `strip_llm_status_tags`, `strip_flavor_stats_table`
- `app/gm/orchestrator.py` — compose pipeline; optional `_auto_roll_stats` prompt tighten
- `app/tests/test_creation_flavor_sanitize.py` — **new** per ticket
- `tmp/app-character-creation-spec.md` — § Flavor sanitization pipeline (APP-073); changelog on close

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **RACE→ROLL_STATS→CLASS:** After race pick, narration shows **one** attribute breakdown table; clerk flavor above has no second stat block or `### Your Attributes`.
- **Gated steps (SKILLS, schools, equipment):** Footer `Awaiting:` matches step; no stale `SKILL_INPUT` / `MAGIC_SCHOOLS_INPUT` / `EQUIPMENT_CONFIRMATION` in flavor region above footer.
- **Drift log:** `app/logs/session-*.jsonl` — no `awaiting_mismatch` on clean play when flavor sanitizer is working.
- **Undead roll (regression):** Replay ticket evidence path — LLM wrong STR/STA in flavor must not appear; code Final column is authoritative.

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — compose traces, regex gap, APP-072 template, drift first-match behavior
- **Domain truth:** [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md) — § Flavor sanitization pipeline (APP-073); § ROLL_STATS orchestration flavor policy; updated compose order in APP-069/APP-070 sections
- **Related:** APP-007 (partial strip — completed by APP-073), APP-072 (race table strip template), APP-065 (chips — after APP-073), APP-066 (canon labels)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Initial PM draft — status tag hardening + stats table strip; domain spec compose pipeline updated |
