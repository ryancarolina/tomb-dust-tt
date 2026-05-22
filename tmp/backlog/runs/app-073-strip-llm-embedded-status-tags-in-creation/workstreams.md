# Workstreams: APP-073-strip-llm-embedded-status-tags-in-creation

**backlog_ticket:** APP-073

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Creation flavor sanitizers | — | `app/gm/creation.py`, `app/tests/test_creation_flavor_sanitize.py` (unit only) | S1–S2 shipped; `test_strip_llm_status_tags_inline_awaiting` + `test_strip_flavor_stats_table_unit` green |
| WS2 | Compose hook, prompt, integration tests | WS1 | `app/gm/orchestrator.py`, `app/tests/test_creation_flavor_sanitize.py` (compose + integration) | S3–S8 shipped; grep audit clean; full pytest gates green |

**Stream count:** 2 — WS1 is pure `creation.py` sanitizers with direct unit tests (plan tasks 1–2, test §5.1–5.2); WS2 imports helpers, wires compose + ROLL_STATS prompt, and owns end-to-end compose/integration tests (plan tasks 3–5, test §5.3–5.5).

**Out of workstreams (ticket release):** `tmp/app-character-creation-spec.md` changelog + AC checkboxes + `claim_ticket.py release APP-073 --done` (plan task 6).

---

## WS1 — Creation flavor sanitizers

**Scope:** Plan §1–2 — harden `strip_llm_status_tags` / `_LLM_STATUS_TAG_RE`; add `strip_flavor_stats_table()` mirroring APP-072 `strip_flavor_race_table`; scaffold new test module with S1/S2 unit tests.

**Requirements covered:** spec S1 (any `Awaiting:` in flavor), S2 (stat-table block + line fallback strip).

### Implementation order (within stream)

| # | Task | Location | Plan ref |
|---|------|----------|----------|
| 1 | Broaden `_LLM_STATUS_TAG_RE` | `creation.py` L82–85 | §1.1 |
| 2 | Keep `strip_llm_status_tags` cleanup | `creation.py` L537–540 | §1.2 |
| 3 | Add header regex constants | `creation.py` after L545 | §2 |
| 4 | Implement `strip_flavor_stats_table` | `creation.py` after `strip_flavor_race_table` (~L568) | §2 |
| 5 | New test module + unit tests | `app/tests/test_creation_flavor_sanitize.py` | §5.1–5.2 |

### Task 1 — `_LLM_STATUS_TAG_RE` (plan §1.1)

**Before:**

```python
_LLM_STATUS_TAG_RE = re.compile(
    r"\[Location:[^\]]*\]|\[Phase:[^\]]*\]|^\s*Awaiting:\s*[A-Z0-9_]+\s*$",
    re.I | re.MULTILINE,
)
```

**After:**

```python
_LLM_STATUS_TAG_RE = re.compile(
    r"\[Location:[^\]]*\]|\[Phase:[^\]]*\]|Awaiting:\s*[A-Z0-9_]+",
    re.I | re.MULTILINE,
)
```

- Removes inline `Clerk nods. Awaiting: SKILL_INPUT` and whole-line matches.
- Bracket Location/Phase strip unchanged (anywhere in text).
- Helper is **flavor-only** by contract — never run on composed narration footer.

**Optional (only if unit test fails):** trailing punctuation after token; orphaned double-space cleanup on lines.

### Task 2 — `strip_llm_status_tags` (plan §1.2)

Keep post-sub: collapse `\n{3,}` → `\n\n`, `.strip()`.

### Task 3–4 — `strip_flavor_stats_table` (plan §2)

**Placement:** immediately after `strip_flavor_race_table`, before `_PREMATURE_FLAVOR_MARKERS`.

**New constants (after `_MD_TABLE_ROW_RE` ~L545):**

| Constant | Pattern |
|----------|---------|
| `_STATS_TABLE_HEADER_RE` | `^\s*\| Attr \|` |
| `_STATS_HEADING_RE` | `^\s*#{1,3}\s+Your Attributes\b` |
| `_COMPACT_ATTR_HEADER_RE` | `^\s*\| STR \|.*\| AGI \|` (or explicit `\| STR \| AGI \| STA \|`) |

**Algorithm (mirror `strip_flavor_race_table` L548–568):**

1. Empty input → `""`.
2. Line scan: on header match, skip optional separator + subsequent table rows.
3. Heading-only: drop `### Your Attributes` + following table rows if present.
4. **Line fallback** on kept lines — drop lines containing:
   - `\| Attr \| Base \|`
   - `` `roll_attributes( ``
   - compact fingerprint `\| STR \| AGI \|` (require AGI to reduce false positives)
5. Rejoin; collapse `\n{3,}`; `.strip()`.

**Non-goals:** do not strip `\| Category \| Skill \|`, `\| School \|`, `\| Class \|`.

**Reuse:** `_MD_TABLE_SEPARATOR_RE`, `_MD_TABLE_ROW_RE` (shared with APP-072).

### Task 5 — Unit tests (plan §5.1–5.2)

Create `app/tests/test_creation_flavor_sanitize.py` with:

**`test_strip_llm_status_tags_inline_awaiting` (S1):**

| Case | Input | Assert |
|------|-------|--------|
| Inline awaiting | `"The clerk nods. Awaiting: SKILL_INPUT"` | no `Awaiting:`; `"The clerk nods"` retained |
| Bracket block | `"[Location: 32-C \| Phase: desk \| Awaiting: SKILL_INPUT]"` | no bracket fragments; no `Awaiting:` |
| Whole-line awaiting | `"Awaiting: MAGIC_SCHOOLS_INPUT\n\nProse."` | no `Awaiting:`; prose retained |
| Prose only | `"Registry dust hangs in the air."` | unchanged |

**`test_strip_flavor_stats_table_unit` (S2):**

| Case | Input shape | Assert |
|------|-------------|--------|
| Heading block | `### Your Attributes` + separator + rows + trailing prose | no heading, no `\| Attr \|`; trailing prose retained |
| Full stats table | prose + `\| Attr \| Base \| Genetic \| …` + rows | no `\| Attr \| Base \|`; leading prose retained |
| Compact header | `\| STR \| AGI \| STA \| INT \| SPI \| LUC \|` + partial row | no `\| STR \| AGI \|` |
| Tool fragment | `` The dice clatter. `roll_attributes(race `` `` | no `` `roll_attributes( `` |
| Prose only | unchanged | equal to input |

**Fixture note:** paste Spluffy/Tuffy evidence strings from ticket into heading/compact cases if plan defaults are insufficient.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Flavor-only helpers | S1/S2 never applied to code `body` or explicit `footer` |
| APP-072 template | Block-scoped strip + line fallback — match `strip_flavor_race_table` structure |
| C5 scope | Do **not** add stats re-strip in C5 block — status-only re-strip preserved for WS2 |
| Out of scope | `orchestrator.py` (WS2), compose/integration tests (WS2), domain spec edit |

### Test gates (WS1 done when)

```bash
cd app && python -m pytest tests/test_creation_flavor_sanitize.py::test_strip_llm_status_tags_inline_awaiting -q
cd app && python -m pytest tests/test_creation_flavor_sanitize.py::test_strip_flavor_stats_table_unit -q
```

**Minimum WS1 close:** both helpers exported from `creation.py`; unit tests pass; no orchestrator edits.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-073
ticket: tmp/backlog/app-073-strip-llm-embedded-status-tags-in-creation.md
run-folder: tmp/backlog/runs/app-073-strip-llm-embedded-status-tags-in-creation/
spec: spec.md | plan: plan.md §1–2, §5.1–5.2 | domain spec: tmp/app-character-creation-spec.md (read only until release)
workstreams: workstreams.md § WS1

Implement WS1 only — creation.py S1/S2 sanitizers + test_creation_flavor_sanitize.py unit tests per plan §1–2, §5.1–5.2.
AGENTS.md: claim APP-073 before app/ edits; stay within Expected files; no orchestrator edits.
Run unit test gates in workstreams.md § WS1.
Write reflection-dev-impl-WS1.md before return.
```

---

## WS2 — Compose hook, prompt, integration tests

**Scope:** Plan §3–5 — import + wire `strip_flavor_stats_table` in `_compose_creation_narration`; tighten `_auto_roll_stats` flavor instruction; S6 grep audit; add compose + ROLL_STATS integration tests; regression on existing creation tests.

**Depends on:** WS1 — `strip_flm_status_tags` (hardened) and `strip_flavor_stats_table` present in `creation.py`.

**Requirements covered:** spec S3–S8 (compose pipeline, ROLL_STATS prompt, single authoritative table, bad-flavor compose).

### Implementation order (within stream)

| # | Task | Location | Plan ref |
|---|------|----------|----------|
| 1 | Import `strip_flavor_stats_table` | `orchestrator.py` L17–31 | §3.1 |
| 2 | Wire compose pipeline | `_compose_creation_narration` L637–639 | §3.2 |
| 3 | Tighten `_auto_roll_stats` instruction | `orchestrator.py` L1111–1114 | §4.1 |
| 4 | Prompt audit (grep) | `orchestrator.py` | §4.2 |
| 5 | Compose test | `test_creation_flavor_sanitize.py` | §5.3 |
| 6 | ROLL_STATS integration test | `test_creation_flavor_sanitize.py` | §5.4 |
| 7 | Regression suite | — | §5.5 |

### Task 1–2 — Compose hook (plan §3)

**Import:** add `strip_flavor_stats_table` alongside `strip_flavor_race_table`.

**Planned compose order (flavor only):**

```python
cleaned = strip_llm_status_tags(flavor)
cleaned = strip_flavor_race_table(cleaned)
cleaned = strip_flavor_stats_table(cleaned)
cleaned = self._sanitize_creation_flavor(cleaned)
# ... premature sanitizer + C5 status re-strip unchanged ...
```

**Call-site policy:** **only** in `_compose_creation_narration` — all eight compose paths inherit (same as APP-072).

**C5 block (L651–654):** re-run `strip_llm_status_tags` only when premature sanitizer mutates — do **not** add stats re-strip.

**Must not change:** explicit `footer=` in `_auto_finalize` (reception `Awaiting: RECEPTION_CHOICE` never passes flavor sanitizers); code `body` never stripped.

### Task 3 — `_auto_roll_stats` prompt (plan §4.1)

**Replace instruction block (~L1111–1114) with:**

```text
The clerk reacts briefly to the dice roll for a delver whose lineage is **{race_title}**.
Write 1–2 sentences of Registry banter only — mood, ledger ink, superstition.
Do not name or imply any other race.
Do not present attribute numbers, HP, or markdown tables; code appends the full roll readout.
Do not include status lines or Awaiting labels.
```

Aligns with global `_creation_flavor_messages` L702–704 and domain spec § ROLL_STATS flavor policy.

### Task 4 — Prompt audit (plan §4.2)

```bash
rg "SKILL_INPUT|MAGIC_SCHOOLS|EQUIPMENT_CONFIRMATION|Present attribute roll" app/gm/orchestrator.py
```

Expected after edit: **no matches**. Global flavor block already forbids status lines and tables.

### Task 5 — `_flavor_region` helper + compose test (plan §5.3)

Add to test module (if not in WS1):

```python
def _flavor_region(narration: str, body_marker: str = "| Attr | Base |") -> str:
    idx = narration.find(body_marker)
    return narration[:idx] if idx >= 0 else narration.rsplit("Awaiting:", 1)[0]
```

**`test_compose_flavor_sanitize_status_and_stats` (S3–S4, S8):**

| Setup | Detail |
|-------|--------|
| `flavor` | BAD_FLAVOR: inline `Awaiting: SKILL_INPUT` + embedded stat table + `[Phase: creation]` |
| `body` | real `format_roll_stats_table(FIXED_ROLL)` or minimal `\| Attr \| Base \| …` block |
| `creation.step` | e.g. `CLASS` → footer `Awaiting: CLASS_INPUT` |

| Assert | |
|--------|--|
| `narration.count("\| Attr \| Base \|") == 1` | |
| `narration.count("Awaiting:") == 1` | |
| `"Awaiting: CLASS_INPUT" in narration` | |
| `"SKILL_INPUT" not in _flavor_region(narration)` | |
| `"### Your Attributes" not in _flavor_region(narration)` | |

Drive via `orchestrator._compose_creation_narration` directly or minimal orchestrator fixture.

### Task 6 — ROLL_STATS integration (plan §5.4)

**`test_roll_stats_narration_single_stats_table` (S7):**

| Step | Detail |
|------|--------|
| Stub | `_patch_llm_content(monkeypatch, BAD_STAT_FLAVOR, finish_reason="length")` — mimic Spluffy/Tuffy: `### Your Attributes` or compact `\| STR \|` with **wrong** Final values |
| Monkeypatch | `roll_attributes` → `{**FIXED_ROLL, "race": race}` |
| Drive | `"new game"` → name → `"undead"` (or `"human"`) |
| Assert | `creation.step == "CLASS"`; `count("\| Attr \| Base \|") == 1`; Final values from `FIXED_ROLL["final_attributes"]`; wrong LLM values absent from flavor region; `"Awaiting: CLASS_INPUT" in narration`; `"Test narration." not in narration` |

Copy `_patch_llm_content` pattern from `test_creation_tables.py` L17–40; import or duplicate `FIXED_ROLL` from `test_creation_flow.py`.

### Task 7 — Regression (plan §5.5)

```bash
cd app && python -m pytest tests/test_creation_flavor_sanitize.py -q
cd app && python -m pytest tests/test_creation_tables.py -q
cd app && python -m pytest tests/test_creation_flow.py -q
```

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Default path | Thin LLM flavor + post-hoc strip — **not** ROLL_STATS flavor skip |
| Footer immunity | `_auto_finalize(..., footer=footer)` — never sanitize footer |
| Body immunity | `format_roll_stats_table`, `format_races_table`, etc. — S2/S3 flavor-only |
| C5 unchanged | Status re-strip only after APP-070 blanking — no stats re-strip |
| Out of scope | `system_prompt.py`, `logger.py`, `app/ui/app.py`, `conftest.py` global stub |

### Test gates (WS2 done when all pass)

```bash
cd app && python -m pytest tests/test_creation_flavor_sanitize.py -q
cd app && python -m pytest tests/test_creation_tables.py -q
cd app && python -m pytest tests/test_creation_flow.py -q
rg "SKILL_INPUT|MAGIC_SCHOOLS|EQUIPMENT_CONFIRMATION|Present attribute roll" app/gm/orchestrator.py  # expect no matches
```

### Post-impl (not WS2 — ticket release)

- Verify domain spec § **Flavor sanitization pipeline (APP-073)** (L151–212) matches shipped behavior
- Update § **File map**: add `strip_flavor_stats_table`, `test_creation_flavor_sanitize.py`
- Changelog: `| 2026-05-20 | APP-073 done: hardened strip_llm_status_tags; strip_flavor_stats_table; compose hook; _auto_roll_stats prompt; test_creation_flavor_sanitize.py |`
- Mark ticket AC checkboxes + **Closed** date
- `python tmp/backlog/claim_ticket.py release APP-073 --done`

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-073
ticket: tmp/backlog/app-073-strip-llm-embedded-status-tags-in-creation.md
run-folder: tmp/backlog/runs/app-073-strip-llm-embedded-status-tags-in-creation/
spec: spec.md | plan: plan.md §3–5 | domain spec: tmp/app-character-creation-spec.md (read only until release)
workstreams: workstreams.md § WS2

Prerequisite: WS1 present — strip_llm_status_tags hardened + strip_flavor_stats_table in creation.py; unit tests green.
Implement WS2 only — orchestrator compose hook + _auto_roll_stats prompt + compose/integration tests per plan §3–5.
AGENTS.md: claim APP-073 if not active; no system_prompt/logger/ui edits.
Run full test gates in workstreams.md § WS2; grep audit per plan §4.2.
Write reflection-dev-impl-WS2.md before return.
```
