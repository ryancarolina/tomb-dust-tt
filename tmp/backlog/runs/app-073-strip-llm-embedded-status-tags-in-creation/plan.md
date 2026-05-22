# Implementation Plan: APP-073-strip-llm-embedded-status-tags-in-creation

**Status:** draft  
**backlog_ticket:** APP-073  
**ticket_path:** tmp/backlog/app-073-strip-llm-embedded-status-tags-in-creation.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

APP-007 shipped a **partial** status strip and APP-072 added race-table dedup; creation flavor still leaks (1) inline/wrong `Awaiting:` tokens and (2) duplicate ROLL_STATS attribute tables with **wrong numbers**. Models hit `finish_reason: length` at 120 tokens and embed truncated stat markdown in flavor while code appends authoritative `format_roll_stats_table()`.

Fix in four layers (spec S1–S8):

1. **S1** — Harden `strip_llm_status_tags` / `_LLM_STATUS_TAG_RE`: remove **any** `Awaiting:` in flavor (inline or whole-line); keep bracket Location/Phase strip.
2. **S2** — Add `strip_flavor_stats_table()` in `creation.py`, mirroring APP-072 block-scoped strip for stat-table fingerprints.
3. **S3–S4** — Wire stats strip in `_compose_creation_narration` after race strip, before APP-069/070 sanitizers; preserve C5 re-strip of status tags only.
4. **S5–S6** — Tighten `_auto_roll_stats` flavor instruction (clerk reaction only — no numbers/tables); audit prompts for non-canonical awaiting labels.
5. **S7–S8** — New `test_creation_flavor_sanitize.py` with unit + compose + ROLL_STATS integration tests using bad-flavor fixtures.

**Default path:** keep thin LLM flavor on ROLL_STATS + post-hoc strip (not code-only skip).  
**Out of scope:** APP-065 chips, APP-059 columns, `SYSTEM_PROMPT` exploration state-line change, cross-step skill/school table strip.

---

## Code-path traces (current → planned)

### Flow A — All creation narration (compose choke point)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_auto_present_*` / `_auto_roll_stats` / `_auto_finalize` | Each returns via `_compose_creation_narration(flavor, body[, footer])` — e.g. L855, L869, L884, L1057, L1073, L1086, L1099, L1120, L1222 | unchanged |
| 2 | `orchestrator.py:_compose_creation_narration` | L637: `strip_llm_status_tags(flavor)` | **S1:** hardened strip (inline `Awaiting:`) |
| 3 | same | L638: `strip_flavor_race_table(cleaned)` | unchanged (APP-072) |
| 4 | same | _(missing)_ | **S3:** `strip_flavor_stats_table(cleaned)` |
| 5 | same | L639: `_sanitize_creation_flavor(cleaned)` | unchanged (APP-069) |
| 6 | same | L644–654: `sanitize_premature_completion_flavor` when `active` or `roster_len == 0`; C5 re-run `strip_llm_status_tags` if mutated | unchanged; C5 does **not** re-run stats strip (blanked flavor is safe) |
| 7 | same | L655–661: append cleaned flavor + `body` + `format_creation_status()` / explicit `footer` | unchanged — footer is never sanitized |
| 8 | `logger.py:parse_narration_status_line` | L74–76: **first** `Awaiting:` in full narration wins | fixed indirectly — flavor has zero `Awaiting:` before footer |

**Planned compose order (flavor only):**

`strip_llm_status_tags` → `strip_flavor_race_table` → **`strip_flavor_stats_table`** → `_sanitize_creation_flavor` → `sanitize_premature_completion_flavor` (when active/empty roster) → C5 `strip_llm_status_tags` if premature sanitizer mutated → append `body` + footer.

### Flow B — ROLL_STATS → CLASS (duplicate stat tables)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_chain_after_creation_choice` | RACE commit → `_auto_roll_stats` | unchanged |
| 2 | `orchestrator.py:_auto_roll_stats` | L1103–1107: `bridge.roll_attributes`; store `roll_result`; `advance()` → `CLASS` | unchanged |
| 3 | same | L1111–1117: `_narrate_creation_flavor` with “Present attribute roll results… dice readout” | **S5:** clerk reaction only — no numbers, HP, or markdown tables |
| 4 | same | L1118: `body = format_roll_stats_table(result) + format_classes_table(eligible)` | unchanged (authoritative) |
| 5 | same | L1120: `_compose_creation_narration(flavor, body)` | inherits S1–S3; one `\| Attr \| Base \|` block |
| 6 | `creation.py:format_roll_stats_table` | L619–648: code-owned `\| Attr \| Base \| Genetic \| Life Evt \| Racial \| Final \|` | unchanged |
| 7 | `orchestrator.py:_narrate_flavor` | L721–738: raw LLM content, `max_tokens=120` | unchanged — strip is post-hoc |

**Failure modes addressed (ticket evidence):**

| Symptom | LLM leak | Code body | Strip target |
|---------|----------|-----------|--------------|
| Spluffy / undead @ 18:50 | `### Your Attributes` + wrong STR/STA | `format_roll_stats_table` | S2 heading + table block |
| Tuffy / undead @ 19:02 | compact `\| STR \| AGI \| … \|` + `` `roll_attributes( `` | same | S2 compact header + line fallback |

### Flow C — Status tag leak (inline / wrong label)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_creation_flavor_messages` | L702–704: global “Do NOT include … Awaiting” | unchanged (defense in depth) |
| 2 | `orchestrator.py:_narrate_flavor` | returns flavor with possible inline `Awaiting: SKILL_INPUT` | unchanged |
| 3 | `creation.py:_LLM_STATUS_TAG_RE` | L82–85: third branch `^\s*Awaiting:…$` — **line-anchored only** | **S1:** remove `^`/`$` anchors on Awaiting branch |
| 4 | `creation.py:strip_llm_status_tags` | L537–540: regex sub + blank-line collapse | **S1:** picks up hardened regex |
| 5 | `creation.py:CREATION_STATUS_LABELS` | L69–80: canon tokens (`SKILLS_INPUT`, `SPELL_SCHOOLS_INPUT`, `EQUIPMENT_GOLD_CONFIRMATION`) | reference only — strip removes **all** flavor `Awaiting:` regardless of label |
| 6 | `orchestrator.py:_check_creation_drift` | L202–238: `awaiting_mismatch` vs canon | no direct edit — compose fix prevents first-match poison |

**Bracket blocks:** `[Location:…]` and `[Phase:…]` already stripped anywhere (L83); keep as-is.

### Flow D — What must not change

| Path | File:symbol | L | Reason |
|------|-------------|---|--------|
| Reception footer | `_auto_finalize` → `_compose_creation_narration(..., footer=footer)` | L1222 | Explicit `footer` with `Awaiting: RECEPTION_CHOICE` is legitimate post-roster; never pass through flavor sanitizers on footer |
| Code body | `format_roll_stats_table`, `format_races_table`, etc. | `creation.py` | S2/S3 apply to **flavor only** — never strip `body` |
| Golden path mock | `conftest.py` default `"Test narration."` | — | existing tests stay green; new tests use bad-flavor stubs |

---

## Task breakdown

### 1. Harden `strip_llm_status_tags` — `app/gm/creation.py`

#### 1.1 `_LLM_STATUS_TAG_RE` — **L82–85**

**Current:**

```python
_LLM_STATUS_TAG_RE = re.compile(
    r"\[Location:[^\]]*\]|\[Phase:[^\]]*\]|^\s*Awaiting:\s*[A-Z0-9_]+\s*$",
    re.I | re.MULTILINE,
)
```

**Planned:** replace third alternation with global awaiting removal:

```python
r"\[Location:[^\]]*\]|\[Phase:[^\]]*\]|Awaiting:\s*[A-Z0-9_]+"
```

- Removes inline `Clerk nods. Awaiting: SKILL_INPUT` and whole-line matches.
- Case-insensitive via `re.I`.
- Token charset `[A-Z0-9_]+` matches wrong labels (`MAGIC_SCHOOLS_INPUT`, `EQUIPMENT_CONFIRMATION`) and canon labels equally — flavor should have **zero** awaiting tokens.

**Edge cases:**

- Trailing punctuation after token (rare): if model emits `Awaiting: SKILL_INPUT.` consider optional `\b` or trailing `\s*` cleanup pass — only if unit test fails.
- Do **not** strip `Awaiting:` from composed narration — helper is flavor-only by contract.

#### 1.2 `strip_llm_status_tags` — **L537–540**

Keep post-sub cleanup: collapse `\n{3,}` → `\n\n`, `.strip()`.

After inline removal, scan for orphaned clauses (double spaces); optional single `re.sub(r"  +", " ", …)` on lines — **only if** prose looks broken in tests.

---

### 2. `strip_flavor_stats_table(text)` — `app/gm/creation.py`

**Placement:** immediately after `strip_flavor_race_table` (**L568**), before `_PREMATURE_FLAVOR_MARKERS` (**L571**).

**Signature:** `def strip_flavor_stats_table(text: str) -> str`

**Reuse:** `_MD_TABLE_SEPARATOR_RE` / `_MD_TABLE_ROW_RE` at **L544–545** (shared with APP-072).

**Header regexes (new module-level constants after L545):**

| Constant | Pattern | Purpose |
|----------|---------|---------|
| `_STATS_TABLE_HEADER_RE` | `^\s*\| Attr \|` | Code fingerprint `\| Attr \| Base \| …` |
| `_STATS_HEADING_RE` | `^\s*#{1,3}\s+Your Attributes\b` | LLM `### Your Attributes` blocks |
| `_COMPACT_ATTR_HEADER_RE` | `^\s*\| STR \|.*\| AGI \|` (or explicit `\| STR \| AGI \| STA \|`) | Compact attribute row |

**Algorithm (mirror `strip_flavor_race_table` L548–568):**

1. If not `text.strip()`, return `""`.
2. Split lines; scan with index `i`.
3. On line matching any header regex:
   - Advance past optional separator (`_MD_TABLE_SEPARATOR_RE`).
   - Consume subsequent `_MD_TABLE_ROW_RE` lines.
   - Skip block (do not append).
4. For heading-only blocks (`### Your Attributes`): consume following table rows if present; if next lines are prose, drop heading line only.
5. **Line fallback** on kept lines — drop any line containing:
   - `\| Attr \| Base \|`
   - `` `roll_attributes( ``
   - compact fingerprint `\| STR \| AGI \|` (require AGI to reduce false positives)
6. Rejoin; collapse `\n{3,}`; `.strip()`.

**Non-goals:** do not strip `\| Category \| Skill \|`, `\| School \|`, `\| Class \|` (out of APP-073 scope).

---

### 3. Compose hook + import — `app/gm/orchestrator.py`

#### 3.1 Import — **L17–31**

Add `strip_flavor_stats_table` to `from gm.creation import (...)` alongside `strip_flavor_race_table`.

#### 3.2 `_compose_creation_narration` — **L637–638**

**Current:**

```python
cleaned = strip_llm_status_tags(flavor)
cleaned = strip_flavor_race_table(cleaned)
cleaned = self._sanitize_creation_flavor(cleaned)
```

**Planned:**

```python
cleaned = strip_llm_status_tags(flavor)
cleaned = strip_flavor_race_table(cleaned)
cleaned = strip_flavor_stats_table(cleaned)
cleaned = self._sanitize_creation_flavor(cleaned)
```

**Call-site policy:** **only** in `_compose_creation_narration` — all eight compose paths inherit automatically (same as APP-072).

**C5 block (L651–654):** re-run `strip_llm_status_tags` only when premature sanitizer mutates — do **not** add stats re-strip (flavor blanked or prose-only).

---

### 4. ROLL_STATS prompt tighten (S5–S6) — `app/gm/orchestrator.py`

#### 4.1 `_auto_roll_stats` instruction — **L1111–1114**

**Current:**

```text
Present attribute roll results for a delver whose lineage is **{race_title}**.
Do not name or imply any other race.
You are presenting ROLL_STATS results (dice readout) — not asking for class yet.
```

**Planned:**

```text
The clerk reacts briefly to the dice roll for a delver whose lineage is **{race_title}**.
Write 1–2 sentences of Registry banter only — mood, ledger ink, superstition.
Do not name or imply any other race.
Do not present attribute numbers, HP, or markdown tables; code appends the full roll readout.
Do not include status lines or Awaiting labels.
```

Aligns with global block at **L702–704** and domain spec § ROLL_STATS flavor policy (L191–193, L243).

#### 4.2 Prompt audit (S6) — grep before close

Run in `app/gm/orchestrator.py`:

```bash
rg "SKILL_INPUT|MAGIC_SCHOOLS|EQUIPMENT_CONFIRMATION|Present attribute roll" app/gm/orchestrator.py
```

Expected after edit: **no matches**. Global `_creation_flavor_messages` (**L702–704**) already forbids status lines and tables; no other step instructions teach non-canonical labels today.

**Out of scope:** `app/gm/system_prompt.py` exploration state-line template — sanitizer remains pass gate per spec non-goals.

---

### 5. Tests — `app/tests/test_creation_flavor_sanitize.py` (new)

**Module:** per ticket Expected files; separate from `test_creation_tables.py` (APP-072) to keep concerns isolated.

**Fixtures:** copy `_patch_llm_content` pattern from `test_creation_tables.py` **L17–40**; import `FIXED_ROLL` from `test_creation_flow.py` or duplicate minimal dict.

**Helper — flavor region slice (qa-spec-pass note 3):**

```python
def _flavor_region(narration: str, body_marker: str = "| Attr | Base |") -> str:
    idx = narration.find(body_marker)
    return narration[:idx] if idx >= 0 else narration.rsplit("Awaiting:", 1)[0]
```

Use for asserting no inline `Awaiting:` / stat fingerprints **above** code body.

#### 5.1 `test_strip_llm_status_tags_inline_awaiting` — **S1**

Direct import: `from gm.creation import strip_llm_status_tags`.

| Case | Input | Assert |
|------|-------|--------|
| Inline awaiting | `"The clerk nods. Awaiting: SKILL_INPUT"` | `"Awaiting:" not in out`; `"The clerk nods"` retained |
| Bracket block | `"[Location: 32-C \| Phase: desk \| Awaiting: SKILL_INPUT]"` | no bracket fragments; no `Awaiting:` |
| Whole-line awaiting | `"Awaiting: MAGIC_SCHOOLS_INPUT\n\nProse."` | no `Awaiting:`; prose retained |
| Prose only | `"Registry dust hangs in the air."` | unchanged |

#### 5.2 `test_strip_flavor_stats_table_unit` — **S2**

Direct import: `from gm.creation import strip_flavor_stats_table`.

| Case | Input shape | Assert |
|------|-------------|--------|
| Heading block | `### Your Attributes` + separator + data rows + trailing prose | no `### Your Attributes`, no `\| Attr \|`; trailing prose retained |
| Full stats table | prose + `\| Attr \| Base \| Genetic \| …` + rows | no `\| Attr \| Base \|`; leading prose retained |
| Compact header | `\| STR \| AGI \| STA \| INT \| SPI \| LUC \|` + partial row | no `\| STR \| AGI \|` |
| Tool fragment | `` The dice clatter. `roll_attributes(race `` `` | no `` `roll_attributes( `` |
| Prose only | unchanged | equal to input |

#### 5.3 `test_compose_flavor_sanitize_status_and_stats` — **S3–S4, S8**

Drive `orchestrator._compose_creation_narration` directly (or via minimal orchestrator fixture):

| Setup | Detail |
|-------|--------|
| `flavor` | BAD_FLAVOR = inline `Awaiting: SKILL_INPUT` + embedded stat table + bracket `[Phase: creation]` |
| `body` | real `format_roll_stats_table(FIXED_ROLL)` snippet or minimal `\| Attr \| Base \| …` block |
| `creation.step` | e.g. `CLASS` so footer = `Awaiting: CLASS_INPUT` |

| Assert | |
|--------|--|
| `narration.count("\| Attr \| Base \|") == 1` | |
| `narration.count("Awaiting:") == 1` | |
| `"Awaiting: CLASS_INPUT" in narration` | |
| `"SKILL_INPUT" not in _flavor_region(narration)` | |
| `"### Your Attributes" not in _flavor_region(narration)` | |

#### 5.4 `test_roll_stats_narration_single_stats_table` — **S7**

Integration via `process_turn`:

| Step | Detail |
|------|--------|
| Stub | `_patch_llm_content(monkeypatch, BAD_STAT_FLAVOR, finish_reason="length")` where BAD_STAT_FLAVOR mimics Tuffy/Spluffy: `### Your Attributes` or compact `\| STR \|` row with **wrong** Final values (e.g. STR 14) |
| Monkeypatch | `roll_attributes` → `{**FIXED_ROLL, "race": race}` |
| Drive | `"new game"` → name → `"undead"` (or `"human"`) |
| Assert | `orchestrator.creation.step == "CLASS"`; `narration.count("\| Attr \| Base \|") == 1`; Final values from `FIXED_ROLL["final_attributes"]` present; wrong LLM values (e.g. `\| 14 \|` for STR if not in fixture) absent from flavor region; `"Awaiting: CLASS_INPUT" in narration`; `"Test narration." not in narration` (proves stub used) |

#### 5.5 Commands

```bash
cd app && python -m pytest tests/test_creation_flavor_sanitize.py -q
cd app && python -m pytest tests/test_creation_tables.py -q
cd app && python -m pytest tests/test_creation_flow.py -q
```

---

### 6. Spec changelog on close — `tmp/app-character-creation-spec.md`

**Not in impl diff until release** — on `claim_ticket.py release APP-073 --done`:

1. Verify § **Flavor sanitization pipeline (APP-073)** (L151–212) matches shipped behavior.
2. Update § **File map** (L516–519): add `strip_flavor_stats_table`, `test_creation_flavor_sanitize.py`.
3. Tighten § **Flavor must reflect committed FSM** cross-reference if still saying “dice readout” in flavor (qa-spec-pass adversarial note 1) — point to § ROLL_STATS flavor policy.
4. Append changelog row (draft at L543):

   `| 2026-05-20 | APP-073 done: hardened strip_llm_status_tags; strip_flavor_stats_table; compose hook; _auto_roll_stats prompt; test_creation_flavor_sanitize.py |`

5. Mark backlog ticket AC checkboxes + **Closed** date.

---

## Requirements → implementation map

| ID | Requirement | Locus | Test |
|----|-------------|-------|------|
| **S1** | Bracket Location/Phase anywhere; **any** `Awaiting:` in flavor | `creation.py` L82–85, L537–540 | `test_strip_llm_status_tags_inline_awaiting` |
| **S2** | `strip_flavor_stats_table` block + line fallback | `creation.py` after L568 | `test_strip_flavor_stats_table_unit` |
| **S3** | Wire after race strip, before APP-069 | `orchestrator.py` L637–639 | `test_compose_flavor_sanitize_status_and_stats` |
| **S4** | Sole composer; C5 status re-strip preserved | `orchestrator.py` L628–662 | compose test + no footer mutation |
| **S5** | ROLL_STATS clerk-only prompt | `orchestrator.py` L1111–1114 | grep audit + integration |
| **S6** | No non-canonical label teaching | `orchestrator.py` L688–709 | grep audit |
| **S7** | One `\| Attr \| Base \|`; Final from `roll_result` | compose + `_auto_roll_stats` | `test_roll_stats_narration_single_stats_table` |
| **S8** | Bad status + stat flavor → clean compose | compose hook | `test_compose_flavor_sanitize_status_and_stats` |

---

## Files (must ⊆ ticket Expected files)

| File | Changes |
|------|---------|
| `app/gm/creation.py` | Harden `_LLM_STATUS_TAG_RE` + `strip_llm_status_tags`; add `strip_flavor_stats_table` |
| `app/gm/orchestrator.py` | Import helper; compose hook L638; `_auto_roll_stats` instruction L1111–1114 |
| `app/tests/test_creation_flavor_sanitize.py` | **New** — S1/S2 unit + S3/S7/S8 compose/integration |
| `tmp/app-character-creation-spec.md` | Changelog + file map on close (verify draft § APP-073) |

**Out of scope:** `app/ui/app.py` (APP-065), `app/gm/system_prompt.py`, `app/gm/logger.py`, `conftest.py` (local stub in new test module).

---

## Rollback

Revert four files restores pre-APP-073 behavior (inline awaiting + duplicate stat tables possible). No feature flags.

---

## Open questions

- **None blocking.** Default = thin flavor + strip (not ROLL_STATS flavor skip).
- **Over-stripping compact `\| STR \|` in prose:** block-scoped + AGI column requirement mitigates; adjust fallback if unit test false-positive.
- **Session claim:** ensure `tmp/.active-ticket.json` includes APP-073 before impl edits under `app/`.
- **C5 scope:** spec intentionally re-strips status tags only after APP-070 blanking — do not extend C5 to stats strip without PM approval.
