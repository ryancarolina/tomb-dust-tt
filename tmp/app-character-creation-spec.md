# Spec — App Character Creation

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress — **P0 hardening**  
**Owns:** `app/gm/creation.py`, creation branch of `app/gm/orchestrator.py`

---

## Problem (2026-05-20 session)

Gated steps (`SKILLS`, `SPELL_SCHOOLS`, `SPELLS`, `EQUIPMENT_GOLD`) use `_narrate_only()`. Gemini invented equipment/PRE_DELVE while code stayed on `SPELL_SCHOOLS`. `character_create` never ran — empty roster, UI showed registered delver.

---

## Spec

Code-enforced state machine for new delvers at Registry (`32-C`).

### Steps (order)

`NAME` → `RACE` → `ROLL_STATS` → `CLASS` → `SKILLS` → (`SPELL_SCHOOLS` → `SPELLS` if caster) → `EQUIPMENT_GOLD` → `FINALIZE` → `WORLD_INTRO`

### Rules

- Apprentice/Novice with **Spellcasting** skill → must pick schools + tier-1 spells.
- Without Spellcasting → auto-skip schools/spells (`skip_inapplicable_spell_steps`).
- Tables emitted **by code**, not LLM-only.
- `character_create` + `roster_set` only in `_auto_finalize()` after equipment confirm.
- LLM adds **thin flavor only** (~120 tokens); cannot skip steps or emit false `[Phase: PRE_DELVE]`.

### LLM during creation (APP-012 decision)

**Chosen approach:** thin LLM wrapper — `_narrate_flavor()` for 1–2 sentences; **code** appends markdown tables, kit/GP numbers, and `format_creation_status()` footer. No exploration `_llm_loop` while `creation.active`. Interactive step validation is code-first (`_handle_creation_response`); LLM does not call tools for SKILLS/SCHOOLS/SPELLS/EQUIPMENT steps.

### Step content sources (APP-074)

Character creation has **no** legacy `get_step_prompt()` step-instruction builder on the live path. All desk-step presentation is code-first:

| Layer | Owner | Symbols |
|-------|-------|---------|
| **Body** | Code | `format_races_table`, `format_roll_stats_table`, `format_classes_table`, `format_skills_table`, `format_schools_table`, `format_spells_table`, `format_equipment_summary` — invoked from `_auto_present_*`, `_auto_roll_stats`, `_handle_creation_response`, `_chain_after_creation_choice` |
| **Flavor** | Thin LLM | `_narrate_flavor` + `_creation_flavor_messages` (~120 tokens; no tables, no `set_creation_choice` mandates) |
| **Footer** | Code | `format_creation_status()` → `CREATION_STATUS_LABELS[creation.step]` |
| **Input commit** | Code parsers | `_handle_creation_response` → `_execute_creation_choice` — **not** LLM `set_creation_choice` tool calls during desk steps |

**Do not reintroduce:** `get_step_prompt()` strings that instruct the LLM to emit markdown tables or call `set_creation_choice` per step. That path is dead; `orchestrator.py` does not import it. (Contrast: `get_combat_step_prompt` in combat FSM **is** live for exploration combat — different symbol, different domain.)

### Presentation pattern

```text
flavor = verified short LLM (~120 tokens, verify→retry→publish — APP-083)
body   = code-generated markdown (exact format_*_table output)
footer = code-generated status line (format_creation_status)
```

**Narration gate (APP-083 Phase 1):** Thin LLM flavor must pass `verify_narration(prose, build_creation_turn_truth(creation))` before compose. Truth is injected into the flavor prompt via `format_turn_truth_for_prompt`. Failed drafts retry with violation feedback; player never sees unverified flavor. Full pipeline: [`app-llm-orchestrator-spec.md`](app-llm-orchestrator-spec.md) § **Mechanical-truth narration gate**. **Phase 1 batch close = creation only**; exploration/combat gates are Phases 2–3 (future).

**Table catalog:** § [Creation tables](#creation-tables) below; full standardization tracked in [APP-059](backlog/app-059-standardize-creation-table-outputs.md). **ROLL_STATS** catalog and formatter contract added by APP-067.

### Mechanical-truth narration gate (APP-083 Phase 1)

**Cross-domain owner:** [`app-llm-orchestrator-spec.md`](app-llm-orchestrator-spec.md) § **Mechanical-truth narration gate** — architecture, `TurnTruth`, `narrate_with_verification`, retry policy, Phases 2–3 deferral.

**Creation scope (this batch):** All creation flavor LLM calls wire through `narrate_with_verification` with `build_creation_turn_truth(creation)`. Verify runs on **flavor only** — never code `body` or explicit `footer`.

#### Pass gate policy (supersedes strip-first for flavor)

| Era | Pass gate | On violation |
|-----|-----------|--------------|
| APP-069–073 (pre-083) | Post-compose strippers (Option A) | Silent delete; ship if body carries turn |
| **APP-083 Phase 1** | `verify_narration` before compose | **Retry** LLM with same truth + violations; never publish bad flavor |

Compose strippers (`strip_llm_status_tags`, `strip_flavor_race_table`, etc.) remain **defense in depth** until Dev consolidates into verify-only compose — verify is primary.

#### `build_creation_turn_truth(creation)` — allowed claims by step

Built from same sources as mechanics (`school_catalog`, `spell_catalog`, `ensure_equipment_gold`, committed FSM fields) — never parse markdown back.

| Step | `allowed` (in prompt + verify) | Verify fail examples |
|------|--------------------------------|----------------------|
| `SPELL_SCHOOLS` | Eligible school display names/ids; class school-pick rule (e.g. Novice: Divine + 1) | Restoration, Evocation, Abjuration…; fake `\| School \|` tables |
| `SPELLS` | Tier-1 spells for chosen schools (ids/names); min Divine if applicable | Fake school groupings; spell markdown tables |
| `EQUIPMENT_GOLD` | `creation.equipment_kit`, `creation.starting_gold` after `ensure_equipment_gold` | *50 gold*, bedroll kit lists; premature delve/finalize copy |
| `ROLL_STATS` | Committed race; roll in `creation.roll_result` | Stat numbers, `\| Attr \|`, `### Your Attributes` |
| `RACE` / `CLASS` / `SKILLS` | Committed + table eligibility | Duplicate tables; wrong race (F3) |
| All active desk steps | Committed name/race/class/skills | `Awaiting:`, `[Location:`, `Phase:` in flavor |

**Denylist (catalog):** Generic TTRPG school names (Restoration, Evocation, Abjuration, Conjuration, Transmutation, Divination, Enchantment, Communion, Warding, …) — shared constant in `narration_verify.py`.

**Prompt block:** `_creation_flavor_messages` includes `format_turn_truth_for_prompt(truth)` — replaces thin `_committed_state_flavor_block()`-only context for gated steps. Do not duplicate full markdown tables in prompt when code body appends them.

#### Wire points (creation flavor call sites)

All must use `narrate_with_verification` (not raw `_narrate_flavor`):

| Symbol | Steps |
|--------|-------|
| `_auto_present_name` | NAME |
| `_auto_present_race` | RACE |
| `_auto_present_class` | CLASS |
| `_auto_present_skills` / `_creation_table_flavor` | SKILLS |
| `_auto_present_schools` | SPELL_SCHOOLS |
| `_auto_present_spells` | SPELLS |
| `_auto_present_equipment` | EQUIPMENT_GOLD |
| `_auto_roll_stats` / `_narrate_creation_flavor` | ROLL_STATS→CLASS |
| `_auto_finalize` | FINALIZE→WORLD_INTRO flavor only |

**Error re-show (APP-075 V2):** When `error=` is set on skills/schools/spells re-present, preferred path remains `flavor = ""` (skip LLM) — verify gate does not apply when LLM is skipped.

#### Regression targets

| Session | Lines | Violation |
|---------|-------|-----------|
| Sumpty / Undead Novice | `session-2026-05-21.jsonl` L4743, L4749, L4755 | Wrong schools, fake spell table, wrong kit/GP in flavor |

#### Subsumed tickets (Phase 1 docs)

| Ticket | After APP-083 Phase 1 |
|--------|----------------------|
| APP-082 | Folded into verify rules |
| APP-078, APP-059 (creation flavor) | Catalog/economy verify replaces strip-only targets |
| APP-073, APP-072, APP-070 | Strip behaviors → verify **fail** rules (retry, not silent delete) |

#### Tests (Phase 1)

See [`app-llm-orchestrator-spec.md`](app-llm-orchestrator-spec.md) § Tests APP-083 and run spec [`spec.md`](backlog/runs/app-083-mechanical-truth-narration-gate/spec.md).

```bash
cd app && python -m pytest tests/test_narration_verify.py -q
```

### Flavor must reflect committed FSM state (APP-069)

When `creation.active`, thin LLM flavor must not contradict committed FSM fields. Code enforces via **TurnTruth prompt injection + `verify_narration` (APP-083)** and post-compose sanitizers (defense in depth). Prompt alone is insufficient.

| ID | Requirement |
|----|-------------|
| **F1** | `_auto_roll_stats` flavor instruction cites committed race via `race_display_title(creation.race)` |
| **F2** | Roll presentation instruction names **ROLL_STATS** context (dice readout — not class pick) |
| **F3** | `_sanitize_creation_flavor`: if flavor contains a whole-word match of any **other** race title → blank entire flavor string |
| **F4** | `_committed_state_flavor_block()` appended to flavor system message when fields set: name, race, class, skills |
| **F5** | `_creation_flavor_messages` omits `history[-4:]` while `creation.active` |

**Compose pipeline:** `_compose_creation_narration` applies `strip_llm_status_tags` → `strip_flavor_race_table` → `strip_flavor_stats_table` → `strip_flavor_equipment_claims` (APP-059 target) → `_sanitize_creation_flavor` → (when active or empty roster) `sanitize_premature_completion_flavor` → (C5 re-strip if premature sanitizer mutated) → code `body` → `format_creation_status` footer. Full sanitizer contracts: § [Flavor sanitization pipeline (APP-073)](#flavor-sanitization-pipeline-app-073).

**Helper:** `race_display_title(race_key)` in `creation.py` (shared by committed-state block and sanitizer).

**Regression target:** Rick / Undead @ session 17:09 — roll turn must not ship “Human lineage…” flavor while `creation.race == "undead"` and body shows APP-067 roll table.

### Gated-step body contract (APP-069)

For `SKILLS`, `SPELL_SCHOOLS`, `SPELLS`, `EQUIPMENT_GOLD`: narration **body** is only from `_auto_present_*` / `_handle_creation_response` using `format_skills_table`, `format_schools_table`, `format_spells_table`, `format_equipment_summary`. LLM supplies flavor only; never free LLM tables, kit blocks, or cross-step headers on these steps.

#### Body-level drift (stretch — deferred)

Optional `_check_creation_drift` reason `narrated_step_mismatch` when body/footer implies a step other than `creation.step`. Not required for APP-069 close; Phase 2 keyword tests substitute.

### Skill slug normalization (APP-075)

Player skill text at **SKILLS** must resolve glued/compact forms of multi-word slugs (e.g. `manacontrol` → `mana-control`) without changing the public `parse_player_skills` return type (`list[str] | None`).

#### Resolution order (`normalize_skill_slug`)

Apply in order; first match wins:

| Step | Check | Example |
|------|-------|---------|
| 1 | Lowercase + strip | ` Lore ` → `lore` |
| 2 | Exact slug in `ALL_SKILL_SLUGS` | `medicine` → `medicine` |
| 3 | Spaced alias in `SKILL_PARSE_ALIASES` | `mana control` → `mana-control` |
| 4 | Spaces → hyphens, match slug | `mana control` (if not in aliases) → `mana-control` |
| 5 | **Compact pass** — remove spaces and hyphens from input; lookup precomputed `{compact(slug): slug}` built from every canonical slug and alias key | `manacontrol` → `mana-control`; `sleightofhand` → `sleight-of-hand` |
| 6 | No match | `None` |

**Compact map rule:** Precompute once at module load. Keys are `token.replace(" ", "").replace("-", "")` for each slug and alias key. **Exact / alias / hyphen checks always run before compact** so future slug collisions resolve to the longest-established canonical slug first. Current 32-skill catalog is collision-free under this rule (verified in research).

**Nine hyphenated skills (minimum glued coverage):** `shield-use`, `unarmed-combat`, `dual-wielding`, `heavy-weapons`, `thrown-weapons`, `sleight-of-hand`, `magical-knowledge`, `mana-control`, `battlefield-awareness`.

#### `parse_player_skills` behavior

| ID | Requirement |
|----|-------------|
| **P1** | Comma branch and non-comma branch both call `normalize_skill_slug` per token/part — compact pass in P1 benefits **both** paths (non-comma substring scan normalizes discovered tokens). |
| **P2** | Comma-separated: split on `,`, strip parts, resolve each via `normalize_skill_slug`; dedupe while preserving first-seen order; return list **only** when exactly three distinct slugs resolved. Ticket repro `spellcasting, medicine, manacontrol` (apprentice) → `['spellcasting', 'medicine', 'mana-control']`. |
| **P3** | Unknown comma-separated tokens must not fail silently — see § Parse error messaging below. |

Non-comma input (no `,` in string): existing substring scan over `SKILL_PARSE_ALIASES.keys() | ALL_SKILL_SLUGS` (longest first) unchanged except tokens now resolve glued forms via P1 step 5. Glued paste without commas (e.g. `spellcasting medicine manacontrol`) is **in scope** when compact normalization is in `normalize_skill_slug`.

#### Parse error messaging (P3)

**Owner:** `app/gm/creation.py` exposes a **documented helper** (e.g. `format_skill_parse_error(text, class_key) -> str`) that inspects comma-separated parts and returns the full `error=` string. **`_handle_creation_response`** SKILLS branch (`orchestrator.py` ~939–944) **must call this helper** instead of a fixed generic string when `parse_player_skills` returns `None`. Do not build unknown-token text only in tests or only inside `parse_player_skills` — the orchestrator passes the helper result to `_auto_present_skills(..., error=...)`.

**Priority:** When any comma-separated part fails `normalize_skill_slug`, name the unrecognized part(s) **before** the generic count message.

| Input (apprentice) | Required error substring(s) |
|--------------------|------------------------------|
| `spellcasting, medicine, bogus` | `bogus` (e.g. `Unrecognized skill: bogus`) **and** guidance to pick 3 from table |
| `foo, bar, medicine` | both unknown tokens named when practical (e.g. `Unrecognized skills: foo, bar`) |

**Normative examples (shape, not exact punctuation):**

- Single unknown: `Unrecognized skill: bogus. Name exactly 3 skills from the table, comma-separated.`
- Multiple unknown: `Unrecognized skills: foo, bar. Name exactly 3 skills from the table, comma-separated.`
- Wrong count with all tokens recognized: generic count message only (no fake “unrecognized” line).

`parse_player_skills` return type stays `list[str] | None`; diagnostics live in the helper only.

### Gated-step flavor on validation failure (APP-075)

When `_auto_present_skills`, `_auto_present_schools`, or `_auto_present_spells` is called with non-empty `error=`, flavor must not contradict the validation failure. `_auto_present_race`, `_auto_present_class`, and `_auto_present_equipment` are **out of scope** unless a follow-up ticket aligns them.

| ID | Requirement |
|----|-------------|
| **V1** | Do **not** use the first-time step instruction (“Ask {name} which three skills…”, “Ask which two schools…”, etc.) when `error` is set. |
| **V2** | **Preferred:** `flavor = ""` — skip `_narrate_flavor` on error re-show; player sees `**Note:**` + code table only. **Allowed alternative:** one brief correction-only LLM instruction (no congratulations, no confirm picks, no “moving on”) — if used, instruction text must differ from the first-time ask. |
| **V3** | Flavor must not congratulate, confirm accepted picks, or imply the step advanced (same intent as ticket AC / APP-070 but for **validation failure**, not premature completion). |
| **V4** | Code **body** unchanged: `**Note:** {error}\n\n` + `format_*_table(...)` intro/table for the **current** step. |
| **V5** | Single response contract: one narration with note + table + `format_creation_status()` footer for the **current** step (`Awaiting: SKILLS_INPUT`, `SPELL_SCHOOLS_INPUT`, or `SPELLS_INPUT`). No duplicate “ask” framing that contradicts the note. |
| **E1** | V1–V3 apply to all three symbols: `_auto_present_skills`, `_auto_present_schools`, `_auto_present_spells`. |
| **E2** | Post-`validate_skill_picks` / school / spell validation errors that call `_auto_present_*` with enriched `error=` follow the same V1–V5 rules (not only raw parse failure). |

**Regression target:** Supa session 2026-05-20 — `spellcasting, medicine, manacontrol` before P1 fix: congratulatory flavor + `**Note:**` + skills table + `Awaiting: SKILLS_INPUT` in one response.

### Table-shown gating (APP-057)

Gated steps must not treat “field still empty” as “show table again” — that blocks commits on the next player turn.

| Step | Flag | Set in | `_creation_turn_body` auto-present when |
|------|------|--------|----------------------------------------|
| `RACE` | `races_table_shown` | `_auto_present_race` | `is_system_trigger` or `not races_table_shown` |
| `CLASS` | `classes_table_shown` | `_auto_roll_stats` (chain) or `_auto_present_class` (direct/resume) | `is_system_trigger` or `not classes_table_shown` |
| `SKILLS` | `skills_table_shown` | `_auto_present_skills` | `is_system_trigger` or `not skills_table_shown` |
| `SPELL_SCHOOLS` | `schools_table_shown` | `_auto_present_schools` | same pattern |
| `SPELLS` | `spells_table_shown` | `_auto_present_spells` | same pattern |

`_execute_creation_choice` rejects RACE/CLASS/SKILLS/SCHOOLS/SPELLS if the step’s `*_table_shown` is false (player must see the code table first).

**Chain after commit:** `_chain_after_creation_choice` appends the next step’s table in the **same** narration when advancing to `RACE`, `ROLL_STATS`, `SKILLS`, `SPELL_SCHOOLS`, `SPELLS`, or `EQUIPMENT_GOLD`. Required for APP-057/067: **NAME→RACE** and **RACE→ROLL_STATS→CLASS** — after race pick, `_auto_roll_stats` emits stats table + class table in **one** response (APP-067); chain must **not** also call `_auto_present_class` (duplicate class table).

#### NAME→RACE same-turn presentation (APP-068)

After a successful NAME commit (`_execute_creation_choice("NAME", …)` → `advance()` to `RACE`, `races_table_shown = False` per `creation.py`):

| ID | Requirement |
|----|-------------|
| **R1** | Same `process_turn` narration **must** include `_auto_present_race()` output: `body` = `format_races_table()` (intro `Pick **one race**` + header `\| Race \| Adjustments \| Description \|`) and `footer` from `format_creation_status()` → **`Awaiting: RACE_INPUT`**. Thin LLM flavor via `_narrate_flavor` inside `_auto_present_race` is allowed; it is **not** a substitute for the code table. Set `races_table_shown = True` before return. |
| **R2** | When `creation.step == "RACE"` and race is unset, narration **must not** be exactly `"The clerk waits."` (the `_chain_after_creation_choice` default `return prior or "The clerk waits."` when no step branch matches). NAME success must invoke the `RACE` chain branch or return `_auto_present_race(...)` directly — never the empty-prior fallthrough. |

**Observed failure (regression target):** `creation_advanced` `NAME`→`RACE` logged while `gm_narration` is only `"The clerk waits."` with no `llm_request` — chain did not call `_auto_present_race`. See APP-068 ticket / `app/logs/session-2026-05-20.jsonl`.

### Creation tables

Code-owned markdown tables per step. LLM flavor is ≤2 sentences **before** the table block; never invents table cells.

| Step | Formatter | In-table columns | Out of table |
|------|-----------|------------------|--------------|
| RACE | `format_races_table()` | Race, Adjustments, Description | Registry clerk banter (flavor only) |
| **ROLL_STATS** | `format_roll_stats_table(roll_result)` | Attr, Base, Genetic, Life Evt, Racial, Final | Life event **name** on intro line above table; HP line below table |
| CLASS | `format_classes_table(eligible)` | Class, Requirement, Key skills, Starting GP | Class fantasy blurb |
| SKILLS | `format_skills_table(chosen_class)` | Category, Skill, Class key? | Pick rules in intro lines |
| SPELL_SCHOOLS | `format_schools_table(chosen_class)` | School, Tradition, Themes | Pick rules in intro lines |
| SPELLS | `format_spells_table(...)` | Spell, School, MP, Effect | Full spell text in canon only |
| EQUIPMENT_GOLD | `format_equipment_summary(state)` | Kit, Starting GP, Confirm prompt | Clerk commentary (flavor) |

**APP-059 catalog target (RACE):** in-table columns **Race + Adjustments only**; lore stays in flavor (≤2 sentences), not in cells. Current `format_races_table()` still emits a Description column — formatter change is [APP-059](backlog/app-059-standardize-creation-table-outputs.md). APP-072 tests key on `\| Race \| Adjustments \|` so they remain valid when Description is removed.

**APP-059 catalog target (EQUIPMENT_GOLD):** kit and starting GP live only in `format_equipment_summary` body; LLM flavor is clerk banter without GP/kit prose. Session 2026-05-20: flavor *"fifty gold pieces"* vs body `Starting gold: 5 gp` — implement `strip_flavor_equipment_claims` + tightened `_auto_present_equipment` prompt per [APP-059](backlog/app-059-standardize-creation-table-outputs.md).

#### RACE flavor must not duplicate code table (APP-072)

At the RACE step, `_auto_present_race` sets `body = err_prefix + format_races_table()` only. LLM flavor (`_narrate_flavor`, `_CREATION_FLAVOR_MAX_TOKENS = 120`) must not supply a second race table — but responses can still embed or truncate markdown tables (`finish_reason: length`).

**Defense in depth:**

| Layer | Locus | Behavior |
|-------|-------|----------|
| Prompt | `_auto_present_race` instruction | “Brief clerk banter only — do not list races or use markdown tables; the Registry ledger appends the race table.” |
| Global prompt | `_creation_flavor_messages` | “Do NOT include markdown tables …” (all creation steps) |
| Post-sanitize | `_compose_creation_narration` | `strip_flavor_race_table(cleaned)` on **flavor only** before body append |

**Composed RACE narration contract:** exactly **one** `\| Race \| Adjustments \|` header block — from the code body, never from flavor.

#### `strip_flavor_race_table(text)` (APP-072)

**Input:** LLM flavor string (never the code `body`).

**Block-scoped strip:** starting at a line matching `^\s*\| Race \|`, consume optional markdown separator row (`^\s*\|[-:\s|]+\|\s*$`) and subsequent `\|…\|` data rows; drop the block.

**Line fallback:** remove any remaining lines containing `\| Race \|`.

**Output:** retained prose (leading/trailing clerk banter) with collapsed blank lines; empty/whitespace → `""`.

### Flavor sanitization pipeline (APP-073)

Completes APP-007 status-tag strip and adds ROLL_STATS duplicate-table defense (same class of bug as APP-072 race tables). All helpers apply to **flavor only** — never code `body` or explicit `footer` (preserves `_auto_finalize` reception footer).

#### Player-facing contract

| Region | Owner | Must not contain |
|--------|-------|------------------|
| Flavor (after sanitizers) | Thin LLM, cleaned | Status tags, `Awaiting:`, duplicate mechanical tables |
| Body | Code `format_*_table` | — (authoritative) |
| Footer | `format_creation_status()` or explicit reception `footer` | Exactly **one** canonical `Awaiting:` for desk steps |

`parse_narration_status_line()` uses the **first** `Awaiting:` in full narration — flavor-region stale tokens poison drift and APP-065 chips before the code footer is reached.

#### `strip_llm_status_tags(text)` — hardened (APP-007 completed by APP-073)

**Input:** LLM flavor string (never `body` / `footer`).

**Remove:**

| Pattern | Notes |
|---------|--------|
| `[Location:…]` bracket blocks | Anywhere in string (existing APP-007) |
| `[Phase:…]` bracket blocks | Anywhere in string (existing APP-007) |
| `Awaiting:` + token | **Any** occurrence — inline (`Clerk nods. Awaiting: SKILL_INPUT`) or whole-line; not only `^\s*Awaiting:…$` |

**Preserve:** Prose clauses not matching above; collapse excess blank lines.

**Canon labels:** Player-facing narration has exactly one `Awaiting:` from `format_creation_status()` using `CREATION_STATUS_LABELS` — e.g. `SKILLS_INPUT` (not `SKILL_INPUT`), `SPELL_SCHOOLS_INPUT` (not `MAGIC_SCHOOLS_*`), `EQUIPMENT_GOLD_CONFIRMATION` (not `EQUIPMENT_CONFIRMATION`). Prompts must not teach non-canonical tokens; sanitizer is the pass gate when models ignore prompts.

**C5 interaction:** Re-run after `sanitize_premature_completion_flavor` when that helper mutates flavor (APP-070).

#### ROLL_STATS flavor must not duplicate code table (APP-073)

At ROLL_STATS → CLASS chain, `_auto_roll_stats` sets `body = format_roll_stats_table(result) + format_classes_table(eligible)`. LLM flavor must not supply a second attribute presentation — but models embed `### Your Attributes`, full `\| Attr \| Base \| … \|` tables, compact `\| STR \| AGI \| STA \| … \|` rows, or truncated `` `roll_attributes( `` fragments (`finish_reason: length` at 120 tokens).

**Defense in depth:**

| Layer | Locus | Behavior |
|-------|-------|----------|
| Prompt | `_auto_roll_stats` instruction | Brief clerk reaction to the roll only — **do not** present numbers, HP, or markdown tables; code appends the roll readout |
| Global prompt | `_creation_flavor_messages` | “Do NOT include markdown tables … mechanical numbers” (all creation steps) |
| Post-sanitize | `_compose_creation_narration` | `strip_flavor_stats_table(cleaned)` on **flavor only** after `strip_flavor_race_table` |

**Composed ROLL_STATS narration contract:** exactly **one** `\| Attr \| Base \|` header block — from the code body, never from flavor. **Final** column values match `creation.roll_result["final_attributes"]` / `bridge.roll_attributes` only; never merge LLM-invented scores.

**Acceptable alternative:** Skip LLM flavor on ROLL_STATS (code-only intro + tables). If Dev chooses this, document here and adjust tests; default path is thin flavor + stats strip.

#### `strip_flavor_stats_table(text)` (APP-073)

**Input:** LLM flavor string (never the code `body`).

**Block-scoped strip** (mirror APP-072):

1. Starting at a line matching `^\s*\| Attr \|` **or** a markdown heading line `^\s*#{1,3}\s+Your Attributes`, consume optional separator row (`^\s*\|[-:\s|]+\|\s*$`) and subsequent `\|…\|` data rows; drop the block.
2. Starting at a compact attribute header row matching `^\s*\| STR \|` (with AGI/STA/INT/SPI/LUC columns), same consume pattern.

**Line fallback:** remove lines containing `\| Attr \| Base \|`, `` `roll_attributes( ``, or compact `\| STR \| AGI \|` header fingerprints.

**Output:** retained prose with collapsed blank lines; empty/whitespace → `""`.

Reuse `_MD_TABLE_SEPARATOR_RE` / `_MD_TABLE_ROW_RE` from APP-072.

#### EQUIPMENT_GOLD flavor must not duplicate code summary (APP-059)

At EQUIPMENT_GOLD, `_auto_present_equipment` sets `body = format_equipment_summary(self.creation)` only. LLM flavor must not state GP amounts, coin pouches, or kit inventories — models invent round numbers (*"fifty gold pieces"*) that contradict `creation.starting_gold` in the code body.

**Defense in depth:**

| Layer | Locus | Behavior |
|-------|-------|----------|
| Prompt | `_auto_present_equipment` instruction | Brief clerk banter only — do not mention kit contents, gold amounts, or GP; code appends the Registry kit summary |
| Global prompt | `_creation_flavor_messages` | “Do NOT include … mechanical numbers” (all creation steps) |
| Post-sanitize | `_compose_creation_narration` | `strip_flavor_equipment_claims(cleaned)` on **flavor only** after `strip_flavor_stats_table` |

**Composed EQUIPMENT_GOLD contract:** exactly **one** `**Registry kit:**` / `**Starting gold:**` block — from the code body, never from flavor.

#### `strip_flavor_equipment_claims(text)` (APP-059)

**Input:** LLM flavor string (never the code `body`).

**Remove:** lines or sentences mentioning GP/gold/coin economics or kit enumeration — e.g. `\d+\s*gp\b`, `\bgold pieces\b`, `\bfifty gold\b`, `\bcoin pouch\b`, `\bstarting (coin|gold)\b`, `\bRegistry kit\b` when used as an inventory list in flavor.

**Preserve:** generic clerk banter and confirmation asks (*"sign here?"*, *"ready to head out?"*) that do not state amounts or gear.

**Output:** retained prose with collapsed blank lines; empty/whitespace → `""`.

#### `format_roll_stats_table(roll_result)` (APP-067)

**Input:** successful `GameBridge.roll_attributes()` dict (see [`app-gamebridge-spec.md`](app-gamebridge-spec.md) / `bridge.py`). Formatter reads payload fields only — no re-roll, no LLM.

**Intro line:** `Life event: {life_event["name"]}` (or equivalent single line citing `roll_result["life_event"]["name"]`).

**Table header:** `| Attr | Base | Genetic | Life Evt | Racial | Final |`

**Rows STR, AGI, STA, INT, SPI** — one row per attribute:

| Column | Source |
|--------|--------|
| Base | `base_rolls[attr]` |
| Genetic | `genetic_factors[attr]["mod"]` |
| Life Evt | `life_event["mods"].get(attr, 0)` |
| Racial | `racial_adjustments.get(attr, 0)` |
| Final | `final_attributes[attr]` — **authoritative**; may differ from column sum when bridge applies `max(1, …)` clamp |

**LUC row contract:** LUC is not broken out in `base_rolls` / `genetic_factors` / `life_event.mods`. Show one LUC row with `—` in Base, Genetic, Life Evt, and Racial columns; **Final** = `final_attributes["LUC"]` only.

**HP line (after table, blank line):** `**HP:** {hp} (10 + STA {sta} × 5)` where `sta = final_attributes["STA"]` and `hp = 10 + sta * 5` (canon: `build/systems/core/derived-stats.md`, `compute_hp()`).

**Clamp vs Final:** Tests and display use **Final** from `final_attributes`, not `Base + Genetic + Life Evt + Racial`. Do not assert or narrate recomputed sums when clamp changed a value.

#### ROLL_STATS orchestration (APP-067)

`_auto_roll_stats(player_input)`:

1. `bridge.roll_attributes(race)` → store `creation.roll_result`; `advance()` → step `CLASS`; `_remember_creation_step("ROLL_STATS")`.
2. `flavor = _narrate_creation_flavor(...)` — brief clerk reaction to the dice; **no tables, no stat numbers, no HP** (APP-073). Code owns all mechanical readout.
3. `body = format_roll_stats_table(result) + "\n\n" + format_classes_table(eligible)`.
4. `creation.classes_table_shown = True` before return (CLASS commit guard in `_execute_creation_choice`).
5. `return _compose_creation_narration(flavor, body)` → footer `Awaiting: CLASS_INPUT`.

**Chain dedup:** `_chain_after_creation_choice` when `step == "ROLL_STATS"`: return `_auto_roll_stats(...)` only. Do **not** append `_auto_present_class` — roll path already includes `format_classes_table`.

**Direct CLASS path:** `_auto_present_class` remains for `_creation_turn_body` when `step == "CLASS"` and `not classes_table_shown`, invalid class re-prompt, and resume edges. Body is `**Final attributes:**` one-liner + `format_classes_table` (no full stats table repeat).

**Removed patterns:** `_narrate_only()` with JSON context instructing LLM to build the attribute table; `get_step_prompt()` LLM step-instruction strings (inline RACE table + `set_creation_choice` mandates — deleted APP-074).

### Canon data

- Races, classes, skills: `creation.py` + `build/data/character/`
- Starting kits/spells: `build/data/character/starting-kits.json`, `starting-spells.json`

---

## Task checklist

- [x] `CreationState` + step enum + parsers (`parse_player_skills`, etc.)
- [x] Code-first handling for SKILLS, schools, spells, equipment confirm
- [x] Code appends `format_*_table()` + `format_equipment_summary()` (APP-006)
- [x] `format_creation_status()` + strip LLM status tags (APP-007 — **completed** by APP-073 hardened strip)
- [x] Hard gate exploration during creation (APP-008)
- [x] Finalize roster non-empty gate (APP-009)
- [x] Resume restores creation step from session_state (APP-010)
- [x] Invalid input at wrong step re-shows table + error (APP-011)
- [x] LLM flavor decision documented and implemented (APP-012)
- [x] `_auto_finalize` → `character_create` with kit cost guard

- [x] Integration test `test_creation_flow.py` — full FSM through finalize (APP-057)

- [x] Mechanical-truth narration gate — creation verify+retry (APP-083 Phase 1)

**Open work:** [APP-083](backlog/app-083-creation-flavor-verification-gate.md) Phase 1 (verify gate supersedes strip-first flavor policy), [APP-059](backlog/app-059-standardize-creation-table-outputs.md). Militia spell-skip integration test deferred (post APP-057).

### Awaiting contract (engine vs app) — APP-066

Character creation uses **two layers** of “awaiting.” They are **not** required to match each other during desk creation.

| Layer | Owner | API / symbol | When set | Purpose |
|-------|--------|--------------|----------|---------|
| **Engine (coarse)** | `play/tomb_gm` | `bridge.status()["awaiting"]` | `handle_status`: empty roster and no character rows → `CHARACTER_CREATION`; after `character_create` + `roster_set` → `PLAYER_ACTIONS` | CLI `suggest`, save/resume gates, exploration LLM context (`gm/context.py`) |
| **App (granular)** | `app/gm/creation.py` | `CREATION_STATUS_LABELS[creation.step]` in `format_creation_status()` | Every creation narration footer from `CreationState.step` | Player-facing status line, suggestion chips (parse `Awaiting:`), **expected** label for `creation_drift` when `creation.active` |

**Step truth:** `CreationState.step` (persisted in `session_state.json` as `creation_state` on resume). Engine `awaiting` does **not** encode `SKILLS` vs `SPELL_SCHOOLS`; do not drive UI step badges from engine `awaiting` alone (see APP-036).

**Drift QA:** While `creation.active`, compare narrated `Awaiting:` to `CREATION_STATUS_LABELS[step]`, **not** to engine `CHARACTER_CREATION`. Mismatch vs the label map is real drift; match with engine still `CHARACTER_CREATION` is healthy.

**Post-finalize (`WORLD_INTRO`):** `creation.active` is false; engine `awaiting` is `PLAYER_ACTIONS`; footer may use `Awaiting: RECEPTION_CHOICE` and optional `Phase: preparation` — outside granular desk-creation contract (separate reception semantics).

### Status line labels (code-owned)

Single source: `CREATION_STATUS_LABELS` in `creation.py` (also imported by orchestrator drift check).

| Step | Awaiting label |
|------|----------------|
| `NAME` | `NAME_INPUT` |
| `RACE` | `RACE_INPUT` |
| `ROLL_STATS` | `STATS_REVIEW` |
| `CLASS` | `CLASS_INPUT` |
| `SKILLS` | `SKILLS_INPUT` |
| `SPELL_SCHOOLS` | `SPELL_SCHOOLS_INPUT` |
| `SPELLS` | `SPELLS_INPUT` |
| `EQUIPMENT_GOLD` | `EQUIPMENT_GOLD_CONFIRMATION` |
| `FINALIZE` | `FINALIZE` |
| `WORLD_INTRO` | `RECEPTION_CHOICE` |

Unknown step fallback (formatter + drift): `{step}_INPUT`.

---

## Tests

```bash
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m pytest app/tests/test_creation_tables.py -q
python -m pytest app/tests/test_creation_flavor_sanitize.py -q
python -m pytest app/tests/test_creation_flow.py -q
```

### Integration test (APP-057)

**Module:** `app/tests/test_creation_flow.py`  
**Fixtures:** test uses **`orchestrator` only** from `app/tests/conftest.py` (APP-049), which transitively applies **`mock_openrouter_client`**. Do not import `Orchestrator` at module level before fixtures run.  
**Drive:** `orchestrator.process_turn(text)` end-to-end — not parser unit tests.  
**Prerequisite behavior (APP-057 in scope):** RACE/CLASS `*_table_shown` gating + NAME→RACE / ROLL_STATS→CLASS chain — see § Table-shown gating.

#### Primary: `test_full_creation_apprentice_caster`

Eight `process_turn` inputs; tables may appear in the **prior** turn via chain.

| # | Input | Step after |
|---|--------|------------|
| 1 | `new game` | `NAME` |
| 2 | `Dumpy` | `RACE` (race table chained in same narration — **APP-068:** assert table + footer on this turn) |
| 3 | `human` | `CLASS` (roll + class table chained) |
| 4 | `apprentice` | `SKILLS` |
| 5 | `Lore, Spellcasting, Arcana` | `SPELL_SCHOOLS` |
| 6 | `pyromancy, ether` | `SPELLS` |
| 7 | `ember-touch, static-lash` | `EQUIPMENT_GOLD` |
| 8 | `yes` | `WORLD_INTRO` |

**Setup:** `monkeypatch` on `orchestrator.bridge.roll_attributes` returning fixed `eligible_classes` (includes `apprentice`), `INT >= 8`, `ok: True`. **`FIXED_ROLL`** must match production `roll_attributes` shape: `genetic_factors[attr]` = `{"roll": int, "mod": int}`; `base_rolls` keys STR–SPI only (no LUC); see APP-067.

**Required assertions after final turn:**

| Check | Expected |
|-------|----------|
| `orchestrator.creation.active` | `False` |
| `orchestrator.creation.step` | `WORLD_INTRO` |
| `bridge.status()["roster"]` | non-empty |
| `bridge.status()["awaiting"]` | `PLAYER_ACTIONS` |
| Roster entry | `display_name == "Dumpy"`, `base_class == "apprentice"` |
| Final narration | contains `Awaiting: RECEPTION_CHOICE` and `Phase: preparation` |

**Out of scope (APP-057):** Militia non-caster path (spell steps skipped) — follow-up ticket.

#### APP-068: NAME→RACE narration assertions

After turn 2 (`"Dumpy"`) on fresh `new game`, when `creation.step == "RACE"`:

| Check | Expected |
|-------|----------|
| Race table intro | `Pick **one race**` in narration |
| Race table header | `\| Race \| Adjustments \| Description \|` in narration (`format_races_table`) |
| Footer | `Awaiting: RACE_INPUT` |
| Forbidden | narration stripped must **not** equal `"The clerk waits."` |
| `races_table_shown` | `True` |

May be a dedicated test (e.g. `test_name_advance_presents_race_table`) or assertions added to `test_full_creation_apprentice_caster` turn 2. Drive via `orchestrator.process_turn` with `mock_openrouter_client` fixture (same as APP-057).

#### APP-067: ROLL_STATS table assertions

After turn 3 (`"human"`), when `creation.step == "CLASS"`:

| Check | Expected |
|-------|----------|
| Table header | `Attr \| Base \| Genetic \| Life Evt \| Racial \| Final` in narration |
| STR–SPI / LUC finals | Markdown cells match `FIXED_ROLL["final_attributes"]` (assert **Final** column, not recomputed sum) |
| LUC row | Intermediate columns `—`; Final = `final_attributes["LUC"]` |
| HP line | `**HP:** 60` (or equivalent) for STA 10 — `10 + 10×5` |
| Class table | `format_classes_table` eligible rows present **once** (no duplicate from chain) |
| `classes_table_shown` | `True` after roll turn |

Optional unit test: `test_format_roll_stats_table(FIXED_ROLL)` in `test_creation_tables.py`.

#### APP-069: Flavor sanitizer + committed-state (Phase 1)

| Test | Asserts |
|------|---------|
| `test_roll_stats_flavor_reflects_committed_race` | After `new game` → `Rick` → `undead`, with stub flavor `"Human lineage shows in the ledger."`: `creation.race == "undead"`; roll table header present; `"Human" not in narration` |
| `test_creation_flavor_messages_committed_class` | After golden path through `apprentice`, captured flavor system message includes `Committed class: apprentice` and `Committed race:` |

#### APP-069: Gated-step body keywords (Phase 2)

Extend `test_full_creation_apprentice_caster` — per-turn required/forbidden substrings after turns 4–7:

| Turn input | Required | Forbidden |
|------------|----------|-----------|
| `apprentice` | `Pick **3 skills**`; `\| Category \| Skill \|`; `Awaiting: SKILLS_INPUT`; `skills_table_shown` | `\| School \| Tradition \|`; `**Registry kit:**`; `Pick **one race**` |
| `Lore, Spellcasting, Arcana` | `\| School \| Tradition \| Themes \|`; `Awaiting: SPELL_SCHOOLS_INPUT`; `schools_table_shown` | `\| Category \| Skill \|`; `**Registry kit:**`; spell table header |
| `pyromancy, ether` | `Pick **2 tier-1 spells**`; spell table header; `Awaiting: SPELLS_INPUT`; `spells_table_shown` | school table; `**Registry kit:**` |
| `ember-touch, static-lash` | `**Registry kit:**`; `**Starting gold:**`; `**Skills on record:**`; `Reply **yes**`; `Awaiting: EQUIPMENT_GOLD_CONFIRMATION` | spell/school table headers |

Turn 8 (`yes`): keep APP-057 finalize assertions; `PRE_DELVE not in last` (deeper mid-FSM PRE_DELVE gates → APP-070).

#### APP-072: race table dedup tests

**Module:** `app/tests/test_creation_tables.py`

| Test | Setup | Pass |
|------|-------|------|
| `test_strip_flavor_race_table_unit` | Direct call on truncated table (no separator), full table + prose, prose-only | No `\| Race \|` in output; prose retained |
| `test_race_narration_single_table_header` | Stub LLM returns embedded `\| Race \| Adjustments \| Description \|` table with `finish_reason: length`; drive NAME→RACE (`"Dumpy"`) and invalid re-prompt | `narration.count("\| Race \| Adjustments \|") == 1`; `Pick **one race**` present; `Awaiting: RACE_INPUT` |

Use `_patch_llm_content` (monkeypatch `create_client`) — default mock stub `"Test narration."` cannot regress duplicate-table bug.

#### APP-073: status tags + stats table dedup tests

**Module:** `app/tests/test_creation_flavor_sanitize.py` _(new)_ or extend `test_creation_tables.py`

| Test | Setup | Pass |
|------|-------|------|
| `test_strip_llm_status_tags_inline_awaiting` | Direct call: inline `Awaiting: SKILL_INPUT`, bracket `[Location:…\|Phase:…]`, whole-line awaiting | No `Awaiting:` in output |
| `test_strip_flavor_stats_table_unit` | Direct call: `### Your Attributes`, full `\| Attr \| Base \|` block, compact `\| STR \| AGI \|`, `` `roll_attributes( `` fragment | No stat-table fingerprints; prose retained where applicable |
| `test_compose_flavor_sanitize_status_and_stats` | `_compose_creation_narration` with bad flavor (status + stat table) + real code body | One canonical footer; one `\| Attr \| Base \|`; no wrong awaiting in flavor region |
| `test_roll_stats_narration_single_stats_table` | Stub LLM stat-table flavor on RACE commit (`"human"` / `"undead"`) with `FIXED_ROLL` monkeypatch | `count("\| Attr \| Base \|") == 1`; Final column matches fixture; `Awaiting: CLASS_INPUT` |

#### APP-059: equipment GP/kit flavor strip tests

**Module:** `app/tests/test_creation_flavor_sanitize.py` _(extend)_

| Test | Setup | Pass |
|------|-------|------|
| `test_strip_flavor_equipment_claims_unit` | Direct call: *"fifty gold pieces"*, *"5 gp pouch"*, kit list prose + benign clerk line | No `\d+\s*(gp\|gold\|coin)` in output; banter retained |
| `test_equipment_narration_gp_only_in_body` | Stub LLM returns GP prose on SPELLS→EQUIPMENT chain; `creation.starting_gold` known | Flavor region has no GP digits; body `**Starting gold:** {n} gp` matches state |

Turn 7 golden path (`ember-touch, static-lash`): extend forbidden list with flavor-region GP patterns when LLM stub injects economics prose.

**Regression targets:** Spluffy/Tuffy undead @ session 2026-05-20 (duplicate stat tables); Supa/Bumpy wrong awaiting labels.

### Block premature completion copy (APP-070)

While `creation.active` or `bridge.status()["roster"]` is empty, thin-LLM **flavor** must not invent post-creation completion copy (`PRE_DELVE`, `Awaiting: RECEPTION_CHOICE`, “registered Delver”, or `Phase: preparation` at desk steps). **APP-009** `_auto_finalize()` already blocks code from `WORLD_INTRO` without a non-empty roster; APP-070 hardens the **flavor layer** and drift telemetry only.

Legitimate post-finalize reception: code `footer=` at `_auto_finalize` success may include `Phase: preparation` and `Awaiting: RECEPTION_CHOICE` when roster is non-empty and `creation.step == WORLD_INTRO`. `PRE_DELVE` is LLM jargon and must never appear in player narration.

#### Compose sanitization (C1–C5)

| ID | Requirement |
|----|-------------|
| **C1** | `sanitize_premature_completion_flavor` in `creation.py`; caller invokes from `_compose_creation_narration` when `creation.active` or `roster_len == 0` |
| **C2** | Sanitizer applies to **flavor only** — never `body` or `footer` (preserves `_auto_finalize` registration body and reception footer) |
| **C3** | Blank flavor when markers match: `pre[-_]?delve`, `Awaiting: RECEPTION_CHOICE`, `registered delver`, `you are now a registered`, `is now a registered` |
| **C4** | Blank flavor when `Phase: preparation` appears while `active` and `step != WORLD_INTRO` |
| **C5** | Re-run `strip_llm_status_tags` when sanitizer mutates flavor |

**Compose order (flavor):** `strip_llm_status_tags` → `strip_flavor_race_table` (APP-072) → `strip_flavor_stats_table` (APP-073) → `strip_flavor_equipment_claims` (APP-059) → `_sanitize_creation_flavor` (APP-069) → `sanitize_premature_completion_flavor` (APP-070) → re-run `strip_llm_status_tags` if premature sanitizer mutated (C5) → append code `body` + `footer`.

#### Drift extension (D1–D2)

When `_creation_drift_scope()` and `roster_len == 0`, `_check_creation_drift` in `orchestrator.py` adds:

| ID | Condition | Reason |
|----|-----------|--------|
| **D1a** | `narrated_phase in {"pre_delve", "pre-delve"}` | `premature_exploration_phase` |
| **D1b** | `creation.active` and `narrated_awaiting == RECEPTION_CHOICE` | `premature_exploration_phase` |
| **D1c** | `creation.active` and `narrated_phase == preparation` and `step != WORLD_INTRO` | `premature_exploration_phase` |
| **D2** | Registration phrases in full narration (`registered delver`, `you are now a registered`) | `premature_completion_copy` |

Drift is belt-and-suspenders when compose sanitizer strips all markers; T1 does not require drift events.

#### Tests — APP-070 (T1)

**`test_skills_turn_rejects_premature_completion_flavor`** (`app/tests/test_creation_flow.py`):

1. Golden path turns 1–4 (`INPUTS[:4]`) with `FIXED_ROLL` monkeypatch.
2. Monkeypatch `_narrate_flavor` to return bad completion prose (`registered Delver` + `[Phase: PRE_DELVE | Awaiting: RECEPTION_CHOICE]`).
3. Turn 5: `Lore, Spellcasting, Arcana` — FSM advances to `SPELL_SCHOOLS`, roster empty.
4. Assert: no `pre_delve`, `reception_choice`, or `registered delver` in narration; `Awaiting: SPELL_SCHOOLS_INPUT` in footer.

Golden path turn 8 (`test_full_creation_apprentice_caster`) still allows `RECEPTION_CHOICE` + `Phase: preparation` with non-empty roster; `PRE_DELVE not in last`.

#### Tests — APP-075 (T1–T3)

**Primary module paths (ticket Expected files must match):**

| Test | Module | Notes |
|------|--------|-------|
| **T1** | `play/tomb_gm/tests/test_creation_gating.py` | Extend existing `test_normalize_skill_slug` / `test_parse_player_skills_comma_list` |
| **T2**, **T2b**, **T3** | `app/tests/test_creation_flow.py` | Orchestrator integration; pattern from APP-070 |

**T1 — Parser unit** (`play/tomb_gm/tests/test_creation_gating.py`):

| Case | Input / call | Expected |
|------|----------------|----------|
| Glued hyphen skill | `normalize_skill_slug("manacontrol")` | `mana-control` |
| Glued sample (representative) | `normalize_skill_slug("sleightofhand")` | `sleight-of-hand` |
| Ticket repro | `parse_player_skills("spellcasting, medicine, manacontrol", "apprentice")` | three slugs including `mana-control` |
| Unknown token parse | `parse_player_skills("spellcasting, medicine, bogus", "apprentice")` | `None` |
| P3 helper | `format_skill_parse_error("spellcasting, medicine, bogus", "apprentice")` | contains `bogus`; count guidance present |
| Regression spaced | `parse_player_skills("spellcasting, medicine, mana control", "apprentice")` | three slugs (alias path unchanged) |

**T2 — SKILLS error-path flavor** (`app/tests/test_creation_flow.py`):

1. Golden path turns 1–4 (`INPUTS[:4]`) with `FIXED_ROLL` monkeypatch.
2. Monkeypatch `_narrate_flavor` to return fixed congratulatory prose (e.g. `"Smart choices for a Supa."`).
3. Turn 5: `spellcasting, medicine, bogus` (unknown token — stable before/after P1).
4. Assert: `creation.step == "SKILLS"`; `**Note:**` in narration; `bogus` in narration (P3 via orchestrator); footer `Awaiting: SKILLS_INPUT`.
5. **Flavor isolation:** With V2 preferred (empty flavor on error), assert forbidden congratulation markers (`smart choices`, `excellent`, `moving on` — case-insensitive) are **absent from full narration** — the monkeypatched stub must not appear when `_narrate_flavor` is skipped. If implementation uses correction-only flavor (V2 alt), assert those markers absent from narration **and** first-time ask phrases absent (`which three skills they trained`).

**T2b — Positive regression (required):** Same setup as T2 turns 1–4; turn 5 input `spellcasting, medicine, manacontrol` → `creation.step == "SPELL_SCHOOLS"`; footer `Awaiting: SPELL_SCHOOLS_INPUT`; no `**Note:**` error prefix on success path.

**T3 — Schools/spells error flavor** (`app/tests/test_creation_flow.py`):

1. Drive golden path to `SPELL_SCHOOLS` (turns 1–5 with valid skills including ticket repro string).
2. Monkeypatch `_narrate_flavor` to return congratulatory prose.
3. Turn 6: invalid school input (e.g. single school or unknown id per existing validation).
4. Assert: `creation.step == "SPELL_SCHOOLS"`; `**Note:**` present; forbidden congratulation markers absent from narration; footer `Awaiting: SPELL_SCHOOLS_INPUT`.
5. Optional mirror at **SPELLS** with invalid spell pick — same V1–V5 assertions with `Awaiting: SPELLS_INPUT`.

#### Other scenarios (existing / future)

| Scenario | Asserts | Owner |
|----------|---------|-------|
| Apprentice + Spellcasting (manual) | skills → schools → spells → equipment → finalize; roster populated | Human playtest |
| LLM wrong content | tables still match `format_*_table()` | Manual / future |
| `"Yes"` at `SPELL_SCHOOLS` | no PRE_DELVE | `test_creation_gating.py` |
| Status line | matches `creation.step` | Manual / APP-007 |

**Acceptance:** Replay Dumpy flow — cannot reach PRE_DELVE without `character_create` logged. APP-057 automates the Apprentice path above.

---

## Open decisions

_All P0 creation decisions closed (APP-012: thin LLM flavor)._

## File map

| File | Role |
|------|------|
| `gm/creation.py` | State machine, `format_*_table` formatters, parsers, `build_creation_turn_truth` (APP-083), strippers (APP-072+) |
| `gm/orchestrator.py` | `_creation_turn`, `_auto_present_*`, `_compose_creation_narration`, `narrate_with_verification` (APP-083), `_auto_finalize`, `_execute_creation_choice` |
| `gm/narration_verify.py` | `TurnTruth`, `verify_narration`, `format_turn_truth_for_prompt` (APP-083) |
| `tests/test_narration_verify.py` | APP-083 Phase 1 verify + retry tests |
| `tests/test_creation_tables.py` | APP-072 race table strip + single-header integration |
| `gm/choice_memory.py` | Remember creation choices |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-21 | APP-083 Phase 1 done: creation flavor uses `narrate_with_verification` — truth injected, verify→retry→publish; Sumpty school/spell/gold drift blocked |
| 2026-05-21 | APP-083 PM spec: § Mechanical-truth narration gate (Phase 1) — verify→retry→publish supersedes strip-first pass gate; cross-link orchestrator spec; creation rule matrix + wire points; Sumpty regression targets |
| 2026-05-20 | APP-059 spec draft (equipment flavor): § EQUIPMENT_GOLD flavor must not duplicate code summary; `strip_flavor_equipment_claims` target; compose pipeline + § Tests APP-059; session Fatty *"fifty gold"* vs `Starting gold: 5 gp` |
| 2026-05-20 | APP-006–012: code-owned tables/status, exploration gate, finalize roster gate, resume step restore, invalid-input guards, thin LLM flavor decision |
| 2026-05-20 | Spec created; merged creation-orchestrator-hardening content |
| 2026-05-20 | APP-057 spec draft: integration test contract in § Integration test; militia spell-skip deferred |
| 2026-05-20 | APP-057 spec r2: § Table-shown gating (RACE/CLASS flags + chain); integration turn table; fixture import discipline; orchestrator fixes in ticket scope |
| 2026-05-20 | APP-067 spec draft: `format_roll_stats_table`, ROLL_STATS catalog row, chain dedup, LUC/HP/clamp contracts, test assertions |
| 2026-05-20 | APP-057 done: `test_full_creation_apprentice_caster` green; `races_table_shown`/`classes_table_shown` + NAME→RACE / ROLL_STATS→CLASS chain in orchestrator |
| 2026-05-20 | APP-066 spec draft: § Awaiting contract (engine `CHARACTER_CREATION` vs app `CREATION_STATUS_LABELS`); full status label table |
| 2026-05-20 | APP-066 done: drift check uses `CREATION_STATUS_LABELS` when `creation.active`; engine `CHARACTER_CREATION` documented as coarse layer; golden-path test asserts no `creation_drift` |
| 2026-05-20 | APP-068 spec draft: § NAME→RACE same-turn presentation (R1 table+footer, R2 no clerk-waits); § Tests APP-068 narration assertions |
| 2026-05-20 | APP-068 done: NAME commit returns `_auto_present_race()` same turn (direct path in `_handle_creation_response`); chain RACE fallthrough guard; `test_name_advance_presents_race_table` + turn-2 assertions in `test_full_creation_apprentice_caster` green |
| 2026-05-20 | APP-067 done: `format_roll_stats_table` in `creation.py`; `_auto_roll_stats` thin flavor + code tables; ROLL_STATS chain dedup; `test_creation_flow.py` APP-067 assertions green |
| 2026-05-20 | APP-069 done: § Flavor must reflect committed FSM state (F1–F5, Option A sanitizer); § Gated-step body contract; Phase 1–2 tests in `test_creation_flow.py`; stretch `narrated_step_mismatch` deferred |
| 2026-05-20 | APP-070 done: `sanitize_premature_completion_flavor` + compose wiring; drift D1/D2 for empty-roster completion leaks; `test_skills_turn_rejects_premature_completion_flavor` green (extends APP-009 finalize gate) |
| 2026-05-20 | APP-072 spec draft: § RACE flavor must not duplicate code table; `strip_flavor_race_table`; § Tests APP-072; APP-059 RACE catalog target note |
| 2026-05-20 | APP-072 done: `strip_flavor_race_table` in `creation.py`; compose hook in `_compose_creation_narration`; RACE prompt tightened; `test_creation_tables.py` green |
| 2026-05-20 | APP-074: removed legacy `get_step_prompt()` step-instruction builder from `creation.py`; § Step content sources — code-first `_auto_present_*` / `format_*_table` only |
| 2026-05-20 | APP-073 spec draft: § Flavor sanitization pipeline — hardened `strip_llm_status_tags` (APP-007 complete), `strip_flavor_stats_table`, ROLL_STATS flavor policy; compose order updated in APP-069/APP-070 sections; § Tests APP-073 |
| 2026-05-20 | APP-073 done: `strip_llm_status_tags` hardened (inline `Awaiting:` + brackets); `strip_flavor_stats_table` + compose hook; `_auto_roll_stats` clerk-only flavor; `test_creation_flavor_sanitize.py` green; APP-007 status-strip checklist completed |
| 2026-05-20 | APP-075 spec r2: § Skill slug normalization (P1–P3, compact order, `format_skill_parse_error` owner); § Gated-step flavor on validation failure (V1–V5, E1–E2); § Tests APP-075 (T1 gating, T2/T2b/T3 flow) |
| 2026-05-20 | APP-075 done: `_SKILL_COMPACT_MAP` + compact pass in `normalize_skill_slug`; `format_skill_parse_error` + orchestrator SKILLS branch; `_creation_table_flavor` skips LLM on `error=` for skills/schools/spells; T1 `test_creation_gating.py`, T2/T2b/T3 `test_creation_flow.py` green |
