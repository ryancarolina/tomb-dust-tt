# Implementation Plan: APP-072-llm-truncation-race-tables

**Status:** draft  
**backlog_ticket:** APP-072  
**ticket_path:** tmp/backlog/app-072-llm-truncation-duplicate-race-tables.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

RACE body is already code-owned (`format_races_table()` in `_auto_present_race`). The bug is **unconstrained flavor**: the model can emit a full or truncated markdown race table at 120 tokens; `_compose_creation_narration` concatenates flavor + body → two `\| Race \|` blocks.

Fix in three layers (domain T1–T3):

1. **T1** — Keep body path unchanged (already correct); lock with integration test.
2. **T2** — Tighten RACE flavor instruction so the clerk prompt explicitly forbids listing races / duplicating the table.
3. **T3** — Add `strip_flavor_race_table()` in `creation.py`; call from `_compose_creation_narration` after `strip_llm_status_tags` (single choke point — covers `_auto_present_race`, re-prompt, and NAME→RACE chain per qa-spec-pass note).

No retry on `finish_reason: length`; no APP-059 Description column change; no cross-step table strip.

---

## Code-path traces (current → planned)

### Flow A — NAME→RACE presentation (primary failure)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `orchestrator.py:_creation_turn_body` ~603–604 | `RACE` + `not races_table_shown` → `_auto_present_race` | unchanged |
| 2 | `orchestrator.py:_auto_present_race` ~694–704 | `races_table_shown = True`; flavor LLM; `body = err + format_races_table()` | **T2:** stronger `instruction` string; body unchanged |
| 3 | `orchestrator.py:_narrate_flavor` ~558–575 | returns raw LLM content (may include table; `finish_reason` logged only) | unchanged |
| 4 | `orchestrator.py:_compose_creation_narration` ~520–537 | `strip_llm_status_tags(flavor)` → join body + footer | **T3:** `strip_flavor_race_table(cleaned)` after status-tag strip |
| 5 | `creation.py:strip_flavor_race_table` | _(missing)_ | block-scoped table removal + line fallback (T4) |

### Flow B — RACE re-prompt (invalid pick)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `_creation_turn_body` ~605–608 | `_handle_creation_response` or `_auto_present_race(..., error=...)` | same compose hook — T6 satisfied without duplicate call sites |

### Flow C — Chain after NAME (APP-068)

| Step | File:symbol | Current | Planned |
|------|-------------|---------|---------|
| 1 | `_chain_after_creation_choice` / `_execute_creation_choice` | advances to `RACE`, calls `_auto_present_race` | inherits compose hook automatically |

**Out of scope paths:** `_creation_llm_loop`, `get_step_prompt()` RACE branch — zero callers.

---

## Task breakdown

### 1. `strip_flavor_race_table(text)` — `app/gm/creation.py`

**Placement:** immediately after `strip_llm_status_tags` (~L535), before `format_creation_status`.

**Signature:** `def strip_flavor_race_table(text: str) -> str`

**Algorithm (T3 + T4):**

1. If not `text`, return `""`.
2. Split into lines; scan for a **race table header** line matching `^\s*\| Race \|` (case-sensitive — matches code header fingerprint).
3. When header found:
   - If the **next** line matches markdown separator `^\s*\|[-:\s|]+\|\s*$`, treat as table block start.
   - If no separator (truncated LLM output), still treat header as block start (truncated-table failure mode from ticket evidence).
   - Consume subsequent lines while they match `^\s*\|.*\|` (data rows); stop at first non-table line or EOF (handles mid-row truncation).
   - Mark consumed lines for removal; continue scan for additional blocks (model unlikely to emit two, but safe).
4. **T4 fallback:** on remaining lines, drop any line containing `\| Race \|`.
5. Rejoin non-removed lines; collapse `\n{3,}` → `\n\n`; `.strip()`.

**Non-goals:**

- Do not strip `\| Attr \|`, `\| Category \|`, etc. (APP-072 scope).
- Never call on `body` — flavor-only helper.

**Unit-test fixtures (T3):**

| Input shape | Expected output |
|-------------|-----------------|
| Leading prose + full table (header, separator, 2 rows) + trailing prose | Prose only; no `\| Race \|` |
| Prose + truncated table (header + partial row, no separator) | Prose only |
| Prose only, no table | Unchanged prose |
| Empty / whitespace | `""` |

---

### 2. Compose hook — `app/gm/orchestrator.py`

#### 2.1 Import

Add `strip_flavor_race_table` to `from gm.creation import (...)` block (~L16–44).

#### 2.2 `_compose_creation_narration` — **L520–537**

```python
cleaned = strip_llm_status_tags(flavor)
cleaned = strip_flavor_race_table(cleaned)
```

**Call-site policy:** **only** here — not in `_auto_present_race` directly. All eight `_auto_present_*` / `_auto_roll_stats` / `_auto_finalize` paths that use compose get sanitization without per-method duplication (mirrors APP-069/070 compose pattern per qa-spec-pass).

**T1 guard:** `body` argument is never passed through `strip_flavor_race_table`.

#### 2.3 Optional R6 (non-blocking)

If strip removes content (`len(out) < len(pre_strip)`), optional debug log via existing logger — **skip unless trivial**; `log_llm_response` already records `finish_reason: length`.

---

### 3. RACE prompt tightening (T2) — `app/gm/orchestrator.py`

#### `_auto_present_race` — **L697–701**

Strengthen the `instruction` passed to `_creation_flavor_messages` (RACE-only; do **not** change global flavor rules for other steps):

**Current:**

```text
The clerk writes down '{name}' and asks about lineage.
```

**Planned:**

```text
The clerk writes down '{name}' and asks about lineage.
Write 1–2 sentences of Registry clerk banter only.
The full race table is appended by code — do not list races, adjustments, or descriptions; do not use markdown tables.
```

Global system block at L549–551 already says “Do NOT include markdown tables”; RACE instruction repeats the contract at the step that regresses (history may contain prior full tables — APP-069 deferred).

**No change** to `_CREATION_FLAVOR_MAX_TOKENS` (120).

---

### 4. Tests — `app/tests/test_creation_tables.py` (new)

**Module:** ticket Expected file; do not extend `test_creation_flow.py` for APP-072 (keeps golden-path stub on `"Test narration."`).

**Fixtures:** reuse `orchestrator` from `conftest.py`; local helper to patch LLM stub content.

#### 4.1 Stub helper (in test module)

```python
def _patch_llm_content(monkeypatch, content: str, *, finish_reason: str = "stop"):
    # monkeypatch gm.orchestrator.create_client factory → stub chat.completions.create
    # return SimpleNamespace choices[0].message.content = content, finish_reason
```

Pattern: copy `conftest.py` `_StubCompletions` shape; override `content` / `finish_reason` per test (default `"Test narration."` cannot regress duplicate tables).

#### 4.2 `test_strip_flavor_race_table_unit` — **T3**

Direct import: `from gm.creation import strip_flavor_race_table`.

| Case | Assert |
|------|--------|
| Truncated table + prose before/after | `"The clerk"` in out; `"\| Race \|" not in out` |
| Full table with separator | same |
| Prose-only | unchanged |

#### 4.3 `test_race_narration_single_table_header` — **T1 + T5 + T6**

| Step | Detail |
|------|--------|
| Stub | `_patch_llm_content(monkeypatch, BAD_FLAVOR, finish_reason="length")` where `BAD_FLAVOR` = 1–2 prose sentences + embedded `\| Race \| Adjustments \| Description \|` + separator + partial `\| Human \|` row (truncated) |
| Drive | `process_turn("new game")` → `process_turn("Dumpy")` |
| Assert T1/T5 | `"Pick **one race**" in narration`; `narration.count("\| Race \| Adjustments \|") == 1` |
| Assert footer | `"Awaiting: RACE_INPUT" in narration` |
| Assert T6 path | `orchestrator.creation.races_table_shown is True`; optional second turn: invalid race → re-show still `count == 1` (same stub) |

**Stable fingerprint:** use `\| Race \| Adjustments \|` (not full Description header) — survives APP-059 column removal.

#### 4.4 Optional (not required to close)

`test_format_races_table_contract` — header + 16 rows; docstring notes APP-059 target vs current Description column.

#### 4.5 Commands

```bash
cd app && python -m pytest tests/test_creation_tables.py -q
cd app && python -m pytest tests/test_creation_flow.py -q   # no regressions
```

---

### 5. Spec changelog on close — `tmp/app-character-creation-spec.md`

**Not in impl diff until release** — on `claim_ticket.py release APP-072 --done`:

1. Confirm § **RACE flavor must not duplicate code table (APP-072)** matches shipped behavior (T1–T6).
2. Append changelog row (draft already at L544):

   `| 2026-05-20 | APP-072 done: strip_flavor_race_table; compose hook; test_creation_tables.py |`

3. Mark backlog ticket AC checkboxes + **Closed** date.

---

## Requirements → implementation map

| ID | Requirement | Locus | Test |
|----|-------------|-------|------|
| **T1** | Body = `err + format_races_table()` only | `_auto_present_race` ~703 (unchanged) | `test_race_narration_single_table_header` — `Pick **one race**` |
| **T2** | Flavor prompt: ≤2 sentences, no tables | `_auto_present_race` instruction ~698 | Prompt change; integration proves post-check handles violations |
| **T3** | Block-scoped strip on flavor before compose | `creation.py:strip_flavor_race_table` + compose hook | `test_strip_flavor_race_table_unit` |
| **T4** | Line fallback if `\| Race \|` remains | same helper step 5 | covered by unit cases |
| **T5** | Exactly one `\| Race \| Adjustments \|` in composed narration | compose hook | `test_race_narration_single_table_header` |
| **T6** | Re-prompt path same sanitize | compose hook (not `_auto_present_race`-local) | optional invalid-race turn in integration test |

---

## Files (must ⊆ ticket Expected files)

| File | Changes |
|------|---------|
| `app/gm/creation.py` | Add `strip_flavor_race_table()` |
| `app/gm/orchestrator.py` | Import helper; compose hook; RACE instruction tighten |
| `app/tests/test_creation_tables.py` | **New** — T3 unit + T1/T5 integration |
| `tmp/app-character-creation-spec.md` | Changelog on close (verify draft § APP-072) |

**Out of scope:** `conftest.py` (per-test stub patch in new module), `format_races_table()` column change (APP-059), `get_step_prompt` (APP-074), history omission (APP-069).

---

## Rollback

Revert four files restores pre-APP-072 behavior (duplicate tables possible). No feature flags.

---

## Open questions

- **None blocking.** If APP-069 lands concurrent compose changes (`_sanitize_creation_flavor`), merge order: `strip_llm_status_tags` → APP-069 sanitizer → `strip_flavor_race_table` → append parts (both flavor-only).
- **Session claim:** ensure `tmp/.active-ticket.json` includes APP-072 before impl edits under `app/`.
