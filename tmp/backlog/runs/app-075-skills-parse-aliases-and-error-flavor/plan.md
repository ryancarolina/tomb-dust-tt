# Implementation Plan: APP-075-skills-parse-aliases-and-error-flavor

**Status:** draft (Dev plan)  
**backlog_ticket:** APP-075  
**ticket_path:** tmp/backlog/app-075-skills-parse-aliases-and-error-flavor.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**Inputs:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Two **independent** gaps from the Supa session repro; fix both without changing `parse_player_skills` return type or APP-070/069 compose sanitizers.

| Layer | Mechanism | Owner | Spec IDs |
|-------|-----------|-------|----------|
| **P0 parser** | Compact pass in `normalize_skill_slug` (step 5 after exact/alias/hyphen) | `creation.py` | P1, P2 |
| **P0 errors** | `format_skill_parse_error` + orchestrator SKILLS wiring | `creation.py` + `orchestrator.py` | P3 |
| **P0 flavor** | Skip `_narrate_flavor` when `error=` set on skills/schools/spells (V2) | `orchestrator.py` | E1–E2, V1–V5 |
| **P0 tests** | T1 parser unit + T2/T2b/T3 integration | gating + flow modules | T1–T3 |

**Defense order:** parser resolves glued intent → helper names unknown tokens → error re-show omits congratulatory LLM flavor.

**Non-goals:** glued `normalize_spell_id` / school ids; `_auto_present_race|class|equipment` error flavor; `parse_player_skills` structured return type; APP-059 table columns.

---

## Code-path traces (current → planned)

### Flow A — Supa repro: glued token → parse fail → contradictory narration (before fix)

| # | File:lines | Current behavior | Planned |
|---|------------|------------------|---------|
| 1 | `orchestrator.py:933–944` | SKILLS: `parse_player_skills` → `None` → `_auto_present_skills(..., error=fixed string)` | **P3:** `error=format_skill_parse_error(player_input, chosen_class)` |
| 2 | `creation.py:787–795` | Comma branch: `normalize_skill_slug("manacontrol")` → `None`; 2 slugs → return `None` | **P1/P2:** third slug resolves → 3 slugs → success path |
| 3 | `creation.py:286–296` | Resolution stops at hyphen pass; no compact lookup | **P1:** step 5 compact map lookup |
| 4 | `orchestrator.py:1046–1057` | `_auto_present_skills`: `error` only prefixes body; always first-time flavor instruction | **V2:** `flavor = ""` when `error` set |
| 5 | `orchestrator.py:520–537` | `_compose_creation_narration` unchanged | unchanged — empty flavor → note + table + footer only |
| 6 | `creation.py:74` | Footer `Awaiting: SKILLS_INPUT` via `format_creation_status` | unchanged |

### Flow B — Success path after P1 (ticket repro)

| # | File:lines | Planned |
|---|------------|---------|
| 1 | `creation.py:781–795` | `parse_player_skills("spellcasting, medicine, manacontrol", "apprentice")` → `['spellcasting', 'medicine', 'mana-control']` |
| 2 | `orchestrator.py:945–959` | `_execute_creation_choice("SKILLS", ...)` → `validate_skill_picks` OK (spellcasting is key skill) → `advance()` → `SPELL_SCHOOLS` |
| 3 | `orchestrator.py:1026–1031` | `_chain_after_creation_choice` → `_auto_present_schools` (no `error=` → normal thin flavor) |

### Flow C — `normalize_skill_slug` resolution (planned)

**Current (`creation.py:286–296`):**

```286:296:app/gm/creation.py
def normalize_skill_slug(name: str) -> str | None:
    """Map player/LLM skill text to a canonical slug."""
    lower = name.strip().lower()
    if lower in ALL_SKILL_SLUGS:
        return lower
    if lower in SKILL_PARSE_ALIASES:
        return SKILL_PARSE_ALIASES[lower]
    hyphen = lower.replace(" ", "-")
    if hyphen in ALL_SKILL_SLUGS:
        return hyphen
    return None
```

**Planned resolution order (domain spec § Skill slug normalization):**

| Step | Check | Example |
|------|-------|---------|
| 1–4 | Existing exact / alias / hyphen | unchanged |
| 5 | **NEW** compact: `key = lower.replace(" ", "").replace("-", "")` → `_SKILL_COMPACT_MAP[key]` | `manacontrol` → `mana-control` |
| 6 | No match → `None` | `bogus` → `None` |

**Compact map build (module load, after `SKILL_PARSE_ALIASES`):**

- For each slug in `ALL_SKILL_SLUGS`: `compact(slug) → slug`
- For each alias key in `SKILL_PARSE_ALIASES`: `compact(alias) → target slug`
- **Collision policy:** exact/alias/hyphen always win; map is collision-free on current 32-skill catalog (research verified)

**Non-comma path:** `parse_player_skills` substring scan (`creation.py:797–807`) calls `normalize_skill_slug` on discovered tokens — P1 benefits glued paste without commas (e.g. `spellcasting medicine manacontrol`) with no separate change.

### Flow D — `format_skill_parse_error` (new, `creation.py`)

**Planned symbol:** `format_skill_parse_error(text: str, class_key: str) -> str`

**Logic (comma path only — matches P3 priority):**

1. If `is_clarification(text)` or no `,` in text → generic count message.
2. Split comma parts; for each part call `normalize_skill_slug`.
3. Collect `unknown` parts where slug is `None`.
4. If `unknown` non-empty:
   - One: `Unrecognized skill: {part}. Name exactly 3 skills from the table, comma-separated.`
   - Many: `Unrecognized skills: {a, b}. Name exactly 3 skills from the table, comma-separated.`
5. Else (all parts recognized but count ≠ 3) → generic count message only.

**Orchestrator wiring (`orchestrator.py:939–944`):**

```python
# Before
error="Name exactly 3 skills from the table, comma-separated."

# After
error=format_skill_parse_error(player_input, self.creation.chosen_class)
```

Import `format_skill_parse_error` alongside existing `creation` imports. Post-`validate_skill_picks` error path (`948–958`) already passes enriched `error=` — inherits V2 flavor fix automatically.

### Flow E — Error-path flavor (V2 skip LLM)

**Current pattern (all three symbols):**

```1046:1057:app/gm/orchestrator.py
    def _auto_present_skills(self, player_input: str, error: str | None = None) -> str:
        ...
        err = f"**Note:** {error}\n\n" if error else ""
        flavor = self._narrate_flavor(
            self._creation_flavor_messages(
                f"Ask {self.creation.name} which three skills they trained in as a {self.creation.chosen_class}.",
                player_input,
            )
        )
        body = err + format_skills_table(self.creation.chosen_class)
        return self._compose_creation_narration(flavor, body)
```

Same shape at `_auto_present_schools` (`1059–1073`) and `_auto_present_spells` (`1075–1086`).

**Planned:** Extract small private helper (same file) to DRY:

```python
def _creation_table_flavor(
    self, instruction: str, player_input: str, *, error: str | None
) -> str:
    if error:
        return ""  # V2 preferred
    return self._narrate_flavor(
        self._creation_flavor_messages(instruction, player_input)
    )
```

Each `_auto_present_skills|schools|spells` replaces inline `_narrate_flavor(...)` with helper call. **Do not** change `_auto_present_equipment`, `_auto_present_race`, `_auto_present_class` (out of scope).

**Compose result on error:** `**Note:** …` + table intro (unchanged V4) + `Awaiting: *_INPUT` footer (V5). No congratulatory stub from monkeypatched `_narrate_flavor` when skipped.

### Flow F — Test traces

#### T1 — `play/tomb_gm/tests/test_creation_gating.py`

Extend `test_normalize_skill_slug` and `test_parse_player_skills_comma_list`; add `test_format_skill_parse_error`:

| Case | Assert |
|------|--------|
| `normalize_skill_slug("manacontrol")` | `"mana-control"` |
| `normalize_skill_slug("sleightofhand")` | `"sleight-of-hand"` |
| `parse_player_skills("spellcasting, medicine, manacontrol", "apprentice")` | 3 slugs incl. `mana-control` |
| `parse_player_skills("spellcasting, medicine, mana control", "apprentice")` | regression — spaced alias path |
| `parse_player_skills("spellcasting, medicine, bogus", "apprentice")` | `None` |
| `format_skill_parse_error("spellcasting, medicine, bogus", "apprentice")` | contains `bogus` + count guidance |

#### T2 — SKILLS error-path flavor (`app/tests/test_creation_flow.py`)

Pattern from `test_skills_turn_rejects_premature_completion_flavor` (`133–162`):

1. `FIXED_ROLL` monkeypatch + turns 1–4 from `INPUTS[:4]`.
2. `monkeypatch.setattr(orchestrator, "_narrate_flavor", lambda _msgs: "Smart choices for a Supa.")`.
3. Turn 5: `spellcasting, medicine, bogus`.
4. Assert: `step == "SKILLS"`; `**Note:**` in narration; `bogus` in narration; `Awaiting: SKILLS_INPUT`; forbidden markers absent (`smart choices`, `excellent`, `moving on` — case-insensitive); stub string **absent** (V2 skip).

#### T2b — Positive regression (required)

Same setup turns 1–4; turn 5: `spellcasting, medicine, manacontrol`.

Assert: `step == "SPELL_SCHOOLS"`; `Awaiting: SPELL_SCHOOLS_INPUT`; no `**Note:**` error prefix.

#### T3 — Schools error flavor (required)

1. Drive to `SPELL_SCHOOLS`: turns 1–5 with valid skills — use ticket repro string on turn 5 (`spellcasting, medicine, manacontrol`).
2. Congratulatory `_narrate_flavor` stub.
3. Turn 6: invalid input e.g. `pyromancy` (single school — parse returns `None`).
4. Assert: `step == "SPELL_SCHOOLS"`; `**Note:**` present; forbidden congratulation markers absent; `Awaiting: SPELL_SCHOOLS_INPUT`.

Optional spells mirror at **SPELLS** — same V1–V5 pattern; not required for close.

---

## Task breakdown

### 1. Compact skill normalization (P1)

#### 1.1 Build `_SKILL_COMPACT_MAP` — `app/gm/creation.py`

- Module-level dict populated once at import (loop `ALL_SKILL_SLUGS` + `SKILL_PARSE_ALIASES` keys).
- Helper `_compact_skill_token(s: str) -> str`: `s.replace(" ", "").replace("-", "")`.

#### 1.2 Extend `normalize_skill_slug` — `app/gm/creation.py:286–296`

- After hyphen check, compact lookup before `return None`.
- No change to public signature.

### 2. Parse error helper (P3)

#### 2.1 Add `format_skill_parse_error` — `app/gm/creation.py`

- Place near `parse_player_skills` (~781+).
- Export for orchestrator + tests.

#### 2.2 Wire SKILLS branch — `app/gm/orchestrator.py:939–944`

- Replace fixed error string with helper call.
- Add import.

### 3. Error-path flavor (E1–E2, V1–V5)

#### 3.1 Add `_creation_table_flavor` helper — `app/gm/orchestrator.py`

- Returns `""` when `error` truthy; else existing `_narrate_flavor` path.

#### 3.2 Update `_auto_present_skills`, `_auto_present_schools`, `_auto_present_spells`

- Replace inline flavor calls with helper.
- Preserve `err = f"**Note:** {error}\n\n" if error else ""` body prefix (V4).

### 4. Tests (T1–T3)

#### 4.1 Parser unit — `play/tomb_gm/tests/test_creation_gating.py`

- Extend existing tests per domain spec T1 table.
- Import `format_skill_parse_error`.

#### 4.2 Integration — `app/tests/test_creation_flow.py`

- Add `test_skills_error_path_skips_congratulatory_flavor` (T2).
- Add `test_skills_glued_alias_advances_to_schools` (T2b).
- Add `test_schools_error_path_skips_congratulatory_flavor` (T3).

### 5. Domain spec sync (on ticket close — Stage 6)

#### 5.1 `tmp/app-character-creation-spec.md`

- Append changelog entry: APP-075 done.
- Optional: extend File map with `format_skill_parse_error` + `test_creation_gating.py` (QA noted non-blocking).

---

## Verification

```bash
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m pytest app/tests/test_creation_flow.py -q -k "skill or school or glued"
python -m pytest app/tests/test_creation_flow.py -q
```

**Local repro (pre/post P1):**

```bash
python -c "from gm.creation import parse_player_skills; print(parse_player_skills('spellcasting, medicine, manacontrol', 'apprentice'))"
```

Expected after fix: `['spellcasting', 'medicine', 'mana-control']`.

---

## Regression guards

| Guard | Location | Check |
|-------|----------|-------|
| Spaced alias path | T1 regression row | `mana control` still parses |
| APP-070 sanitizer | `_compose_creation_narration` | Do not modify; orthogonal to validation-failure flavor |
| APP-069 race/class flavor | `_sanitize_creation_flavor` | Unchanged |
| Success-path thin flavor | `_auto_present_*` without `error` | Still calls `_narrate_flavor` |
| Golden path | `test_full_creation_apprentice_caster` | Still green with spaced `Lore, Spellcasting, Arcana` |
| `validate_skill_picks` path | `orchestrator.py:948–958` | Key-skill errors get V2 skip via same helper |

---

## File touch list (expected files only)

| File | Change |
|------|--------|
| `app/gm/creation.py` | `_SKILL_COMPACT_MAP`, compact pass in `normalize_skill_slug`, `format_skill_parse_error` |
| `app/gm/orchestrator.py` | `_creation_table_flavor`, SKILLS `format_skill_parse_error` wiring, error skip on skills/schools/spells |
| `play/tomb_gm/tests/test_creation_gating.py` | T1 cases |
| `app/tests/test_creation_flow.py` | T2, T2b, T3 |
| `tmp/app-character-creation-spec.md` | Changelog on close |

---

## Workstream split (implementation)

| ID | Scope | Depends on | Done when |
|----|-------|------------|-----------|
| **WS1** | `creation.py` P1 + P3 + T1 | — | gating pytest green |
| **WS2** | `orchestrator.py` E1 + T2/T2b/T3 | WS1 for T2b only | flow pytest green |

WS1 and WS2 can start in parallel except T2b lands after WS1; T2 (bogus token) and T3 (schools flavor) can land with WS2 alone.

---

## Rollback / flags

No feature flags. Rollback = revert compact pass + flavor skip + tests. Spaced/hyphen parsing unchanged — zero risk to existing inputs.

---

## Open questions

_None blocking — QA spec PASS confirms normative behavior in domain spec §§ Skill slug normalization + Gated-step flavor on validation failure._
