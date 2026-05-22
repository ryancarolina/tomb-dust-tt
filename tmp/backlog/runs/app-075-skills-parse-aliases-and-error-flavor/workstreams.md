# Workstreams: APP-075-skills-parse-aliases-and-error-flavor

**backlog_ticket:** APP-075

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Compact parse + error helper + T1 | — | `app/gm/creation.py`, `play/tomb_gm/tests/test_creation_gating.py` | P1 + P3 shipped; gating pytest green |
| WS2 | Error-path flavor + integration tests | WS1 for T2b only | `app/gm/orchestrator.py`, `app/tests/test_creation_flow.py` | E1–E2 + T2/T2b/T3 shipped; flow pytest green |

**Stream count:** 2 — WS1 owns `creation.py` compact normalization (P1), `format_skill_parse_error` (P3), and T1 unit tests (plan §1–2, §4.1); WS2 owns orchestrator flavor skip (E1–E2), SKILLS error wiring import, and T2/T2b/T3 integration tests (plan §3–4.2). T2 (bogus token) and T3 (schools flavor) can land with WS2 before WS1 completes; **T2b** (glued alias advance) requires WS1.

**Out of workstreams (ticket release):** `tmp/app-character-creation-spec.md` changelog + AC checkboxes + `claim_ticket.py release APP-075 --done` (plan §5).

---

## WS1 — Compact parse + error helper + T1

**Scope:** Plan §1–2 — `_SKILL_COMPACT_MAP`, compact pass in `normalize_skill_slug`, `format_skill_parse_error`; extend `test_creation_gating.py` per T1 table.

**Requirements covered:** spec P1, P2, P3 (helper only — orchestrator wiring is WS2), T1.

### Implementation order (within stream)

| # | Task | Location | Plan ref |
|---|------|----------|----------|
| 1 | Add `_compact_skill_token` helper | `creation.py` (near aliases) | §1.1 |
| 2 | Build `_SKILL_COMPACT_MAP` at module load | `creation.py` after `SKILL_PARSE_ALIASES` | §1.1 |
| 3 | Extend `normalize_skill_slug` step 5 | `creation.py` ~286–296 | §1.2 |
| 4 | Add `format_skill_parse_error` | `creation.py` near `parse_player_skills` (~781+) | §2.1 |
| 5 | Extend / add T1 tests | `play/tomb_gm/tests/test_creation_gating.py` | §4.1 |

### Task 1–2 — Compact map (plan §1.1)

**Helper:**

```python
def _compact_skill_token(s: str) -> str:
    return s.replace(" ", "").replace("-", "")
```

**Map build (once at import):**

- For each slug in `ALL_SKILL_SLUGS`: `_compact_skill_token(slug) → slug`
- For each alias key in `SKILL_PARSE_ALIASES`: `_compact_skill_token(alias) → target slug`
- **Collision policy:** exact / alias / hyphen checks run first (steps 1–4); compact is step 5 only. Map is collision-free on current 32-skill catalog (research verified).

### Task 3 — `normalize_skill_slug` (plan §1.2)

**Current resolution ends at hyphen pass → `None`.**

**Planned order (unchanged steps 1–4, then):**

| Step | Check | Example |
|------|-------|---------|
| 5 | **NEW** `key = _compact_skill_token(lower)` → `_SKILL_COMPACT_MAP.get(key)` | `manacontrol` → `mana-control` |
| 6 | No match → `None` | `bogus` → `None` |

**Non-comma path:** `parse_player_skills` substring scan (`creation.py` ~797–807) calls `normalize_skill_slug` on discovered tokens — P1 benefits glued paste without commas; no separate change.

**Do not change:** public signature of `normalize_skill_slug` or `parse_player_skills` return type (`list[str] | None`).

### Task 4 — `format_skill_parse_error` (plan §2.1)

**Signature:** `format_skill_parse_error(text: str, class_key: str) -> str`

**Logic (comma path only — matches P3 priority):**

1. If `is_clarification(text)` or no `,` in text → generic count message: `Name exactly 3 skills from the table, comma-separated.`
2. Split comma parts; for each part call `normalize_skill_slug`.
3. Collect `unknown` parts where slug is `None`.
4. If `unknown` non-empty:
   - One: `Unrecognized skill: {part}. Name exactly 3 skills from the table, comma-separated.`
   - Many: `Unrecognized skills: {a, b}. Name exactly 3 skills from the table, comma-separated.`
5. Else (all parts recognized but count ≠ 3) → generic count message only.

**Note:** `class_key` is required by spec but unused in message text today — keep parameter for API stability.

**Export** for orchestrator + tests (WS2 imports).

### Task 5 — T1 unit tests (plan §4.1)

Extend `test_normalize_skill_slug` and `test_parse_player_skills_comma_list`; add `test_format_skill_parse_error`:

| Case | Assert |
|------|--------|
| `normalize_skill_slug("manacontrol")` | `"mana-control"` |
| `normalize_skill_slug("sleightofhand")` | `"sleight-of-hand"` |
| `parse_player_skills("spellcasting, medicine, manacontrol", "apprentice")` | 3 slugs incl. `mana-control` |
| `parse_player_skills("spellcasting, medicine, mana control", "apprentice")` | regression — spaced alias path |
| `parse_player_skills("spellcasting, medicine, bogus", "apprentice")` | `None` |
| `format_skill_parse_error("spellcasting, medicine, bogus", "apprentice")` | contains `bogus` + count guidance |

Import `format_skill_parse_error` in gating test module.

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Resolution order | Exact → alias → hyphen → **compact** → `None`; never let compact override earlier matches |
| APP-059 | Do not change table column formatting |
| APP-070/069 | Do not modify `_compose_creation_narration` or `_sanitize_creation_flavor` |
| Non-goals | Glued `normalize_spell_id` / school ids; structured `parse_player_skills` return type |
| Out of scope | `orchestrator.py` (WS2), `test_creation_flow.py` (WS2), domain spec edit |

### Test gates (WS1 done when)

```bash
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
```

**Local repro (post-WS1):**

```bash
cd app && python -c "from gm.creation import parse_player_skills; print(parse_player_skills('spellcasting, medicine, manacontrol', 'apprentice'))"
```

Expected: `['spellcasting', 'medicine', 'mana-control']`.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-075
ticket: tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md
run-folder: tmp/backlog/runs/app-075-skills-parse-aliases-and-error-flavor/
spec: spec.md | plan: plan.md §1–2, §4.1 | domain spec: tmp/app-character-creation-spec.md (read only until release)
workstreams: workstreams.md § WS1

Implement WS1 only — creation.py P1 compact map + P3 format_skill_parse_error + test_creation_gating.py T1 per plan §1–2, §4.1.
AGENTS.md: claim APP-075 before app/ edits; stay within Expected files; no orchestrator edits.
Run test gates in workstreams.md § WS1.
Write reflection-dev-impl-WS1.md before return.
```

---

## WS2 — Error-path flavor + integration tests

**Scope:** Plan §3–4.2 — `_creation_table_flavor` helper; update `_auto_present_skills`, `_auto_present_schools`, `_auto_present_spells`; wire `format_skill_parse_error` on SKILLS parse-fail; T2, T2b, T3 in `test_creation_flow.py`.

**Depends on:** WS1 for **T2b only** (glued alias must parse). T2 and T3 can be implemented before WS1 lands if tests use inputs that do not require compact pass.

**Requirements covered:** spec E1–E2, P3 (orchestrator wiring), T2, T2b, T3.

### Implementation order (within stream)

| # | Task | Location | Plan ref |
|---|------|----------|----------|
| 1 | Add `_creation_table_flavor` | `orchestrator.py` | §3.1 |
| 2 | Update `_auto_present_skills`, `_auto_present_schools`, `_auto_present_spells` | `orchestrator.py` ~1046–1086 | §3.2 |
| 3 | Wire SKILLS parse-fail error | `orchestrator.py` ~939–944 | §2.2 |
| 4 | Add T2 integration test | `app/tests/test_creation_flow.py` | §4.2 |
| 5 | Add T2b positive regression | `app/tests/test_creation_flow.py` | §4.2 |
| 6 | Add T3 schools error flavor | `app/tests/test_creation_flow.py` | §4.2 |
| 7 | Regression suite | — | Verification |

### Task 1–2 — Error-path flavor (plan §3)

**New private helper (same file):**

```python
def _creation_table_flavor(
    self, instruction: str, player_input: str, *, error: str | None
) -> str:
    if error:
        return ""  # V2 preferred — skip LLM on validation failure
    return self._narrate_flavor(
        self._creation_flavor_messages(instruction, player_input)
    )
```

**Each `_auto_present_skills|schools|spells`:** replace inline `_narrate_flavor(...)` with helper call. Preserve:

```python
err = f"**Note:** {error}\n\n" if error else ""
body = err + format_*_table(...)
return self._compose_creation_narration(flavor, body)
```

**Compose on error:** `**Note:**` + table intro (V4) + `Awaiting: *_INPUT` footer (V5). No congratulatory stub when flavor is `""`.

**Do not change:** `_auto_present_equipment`, `_auto_present_race`, `_auto_present_class` (out of scope).

**Post-validate path:** `orchestrator.py` ~948–958 (`validate_skill_picks` failure) already passes enriched `error=` — inherits V2 skip via same helper.

### Task 3 — SKILLS error wiring (plan §2.2)

**Import** `format_skill_parse_error` alongside existing `creation` imports.

**Replace fixed string at parse-fail branch (~939–944):**

```python
# Before
error="Name exactly 3 skills from the table, comma-separated."

# After
error=format_skill_parse_error(player_input, self.creation.chosen_class)
```

### Task 4 — T2 SKILLS error flavor (plan §4.2)

Pattern from `test_skills_turn_rejects_premature_completion_flavor` (`test_creation_flow.py` ~133–162):

| Step | Detail |
|------|--------|
| Setup | `FIXED_ROLL` monkeypatch + turns 1–4 from `INPUTS[:4]` |
| Stub | `monkeypatch.setattr(orchestrator, "_narrate_flavor", lambda _msgs: "Smart choices for a Supa.")` |
| Turn 5 | `spellcasting, medicine, bogus` |
| Assert | `step == "SKILLS"`; `**Note:**` in narration; `bogus` in narration; `Awaiting: SKILLS_INPUT`; forbidden markers absent (`smart choices`, `excellent`, `moving on` — case-insensitive); stub string **absent** (V2 skip) |

### Task 5 — T2b positive regression (plan §4.2) — **requires WS1**

Same setup turns 1–4; turn 5: `spellcasting, medicine, manacontrol`.

| Assert | |
|--------|--|
| `step == "SPELL_SCHOOLS"` | |
| `Awaiting: SPELL_SCHOOLS_INPUT` | |
| No `**Note:**` error prefix | |

### Task 6 — T3 schools error flavor (plan §4.2)

| Step | Detail |
|------|--------|
| 1 | Drive to `SPELL_SCHOOLS`: turns 1–5 with valid skills — turn 5 uses `spellcasting, medicine, manacontrol` (needs WS1) |
| 2 | Congratulatory `_narrate_flavor` stub |
| 3 | Turn 6: invalid input e.g. `pyromancy` (single school — parse returns `None`) |
| Assert | `step == "SPELL_SCHOOLS"`; `**Note:**` present; forbidden congratulation markers absent; `Awaiting: SPELL_SCHOOLS_INPUT` |

**Impl note:** Confirm apprentice path has `needs_spell_picks` true after T2b skills; if school table auto-skips for non-caster, T3 must use a caster class path.

Optional spells mirror at **SPELLS** — same V1–V5 pattern; not required for close.

### Task 7 — Regression (plan Verification)

```bash
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m pytest app/tests/test_creation_flow.py -q -k "skill or school or glued"
python -m pytest app/tests/test_creation_flow.py -q
```

| Guard | Check |
|-------|-------|
| Spaced alias | T1 regression: `mana control` still parses |
| APP-070 | `_compose_creation_narration` unchanged |
| APP-069 | `_sanitize_creation_flavor` unchanged |
| Success-path flavor | `_auto_present_*` without `error` still calls `_narrate_flavor` |
| Golden path | `test_full_creation_apprentice_caster` still green |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| V2 only | Skip `_narrate_flavor` when `error` set — do not use correction-only LLM instruction path |
| Three symbols only | skills / schools / spells — not race / class / equipment |
| Defense order | Parser (WS1) → helper names unknown tokens → error re-show omits congratulatory flavor |
| T2b ordering | Do not mark WS2 done until T2b passes (depends on WS1 compact pass) |
| Out of scope | `normalize_spell_id` glued ids; domain spec changelog (release step) |

### Test gates (WS2 done when all pass)

```bash
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m pytest app/tests/test_creation_flow.py -q -k "skill or school or glued"
python -m pytest app/tests/test_creation_flow.py -q
```

### Post-impl (not WS2 — ticket release)

- Verify domain spec §§ **Skill slug normalization (APP-075)** and **Gated-step flavor on validation failure (APP-075)** match shipped behavior
- Optional file map: `format_skill_parse_error`, `test_creation_gating.py` cases
- Changelog: `| 2026-05-20 | APP-075 done: compact skill slug pass; format_skill_parse_error; error-path flavor skip on skills/schools/spells; T1–T3 tests |`
- Mark ticket AC checkboxes + **Closed** date
- `python tmp/backlog/claim_ticket.py release APP-075 --done`

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-075
ticket: tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md
run-folder: tmp/backlog/runs/app-075-skills-parse-aliases-and-error-flavor/
spec: spec.md | plan: plan.md §3–4.2 | domain spec: tmp/app-character-creation-spec.md (read only until release)
workstreams: workstreams.md § WS2

Prerequisite: WS1 present — format_skill_parse_error + compact normalize_skill_slug; gating pytest green.
Implement WS2 only — orchestrator _creation_table_flavor + SKILLS error wiring + test_creation_flow.py T2/T2b/T3 per plan §3–4.2.
AGENTS.md: claim APP-075 if not active; stay within Expected files.
Run full test gates in workstreams.md § WS2.
Write reflection-dev-impl-WS2.md before return.
```
