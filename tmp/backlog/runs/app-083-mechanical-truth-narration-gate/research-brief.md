# Research Brief: APP-083-mechanical-truth-narration-gate

**Date:** 2026-05-21  
**Question:** Where does creation (and later exploration/combat) narration diverge from code-owned mechanical truth today, and how should `TurnTruth` → prompt injection → `verify_narration` → `narrate_with_verification` wire in for Phase 1?

**backlog_ticket:** APP-083  
**ticket_path:** tmp/backlog/app-083-creation-flavor-verification-gate.md  
**domain_spec:** tmp/app-llm-orchestrator-spec.md  
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket **Domain spec** is [`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **LLM orchestrator** already owns `gm/orchestrator.py`, `context.py`, `system_prompt.py`, and related turn-loop modules. APP-083 extends that spec with § Mechanical-truth narration gate; cross-domain rule matrices land in creation/exploration/combat specs in later phases — no new top-level domain spec required.

## Summary

Creation narration today is **thin LLM flavor + code body + code footer**, but flavor is generated **without step catalogs** (schools, spells, kit, GP) and published **immediately** after regex strippers in `_compose_creation_narration`. The Sumpty session (`app/logs/session-2026-05-21.jsonl` L4743, L4749, L4755) shows wrong schools, fake spell tables, and invented kit/GP **above** the correct code tables — strippers remove duplicate race/stats tables (APP-072/073) but **do not** catch catalog hallucinations or economy claims. There is **no** `TurnTruth`, `verify_narration`, or retry loop anywhere in `app/`. Exploration uses APP-024 line stripping; combat uses APP-028 failure prefixes — both reactive, no verify→retry→publish. Phase 1 should ship the **shared framework** plus **creation-only** builders and rules, wiring every creation flavor LLM call through `narrate_with_verification` while leaving exploration/combat loops unchanged until Phases 2–3.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Creation FSM + catalogs | `app/gm/creation.py` | `school_catalog()`, `spell_catalog()`, `format_*_table()`, `ensure_equipment_gold()`, strippers APP-073/070 |
| Turn loop + flavor | `app/gm/orchestrator.py` | `_creation_turn`, `_compose_creation_narration`, `_creation_flavor_messages`, `_narrate_flavor`, `_auto_present_*` |
| Global LLM persona | `app/gm/system_prompt.py` | Conflicts: tells LLM to emit markdown tables during creation |
| Exploration context | `app/gm/context.py` | `build_state_context` — authoritative for exploration, not creation steps |
| Logging | `app/gm/logger.py` | `log_gm_narration`, `log_llm_*` — no `narration_verify_*` events yet |
| Canon spell data | `build/data/spells/schools.json`, `spells.json` | Source for `school_catalog()` / `tier1_spells_for_schools()` |
| Tests | `app/tests/test_creation_flavor_sanitize.py`, `test_creation_flow.py`, `test_creation_tables.py` | Strip/compose only; no verify-retry tests |
| **Missing (ticket Expected files)** | `app/gm/narration_verify.py`, `app/tests/test_narration_verify.py` | Not present in repo |

## Code-path traces

### Creation flavor → emit (current)

1. **Entry:** `Orchestrator.process_turn` → `_creation_turn` → `_creation_turn_body` (step dispatch).
2. **Present step:** e.g. `_auto_present_schools` → `_creation_table_flavor` → `_narrate_flavor` → `chat_completion` (`max_tokens=120`, no tools).
3. **Prompt build:** `_creation_flavor_messages(instruction, player_input)` — `SYSTEM_PROMPT` + desk block with `creation.step`, `_committed_state_flavor_block()` (name/race/class/skills only), flavor-only instruction. **No** eligible schools/spells/kit/GP.
4. **Compose:** `_compose_creation_narration(flavor, body)` — sequential strippers on flavor only (`strip_llm_status_tags`, `strip_flavor_race_table`, `strip_flavor_stats_table`, `_sanitize_creation_flavor`, `sanitize_premature_completion_flavor`) → append code `body` (`format_schools_table`, etc.) → `format_creation_status` footer.
5. **Exit:** `_emit_narration` → `log_gm_narration` → UI/TTS. **No verification gate; failed/strip-empty flavor still ships** if body/footer carry the turn.

**Creation flavor call sites (all use `_narrate_flavor` directly or via helpers):**

| Symbol | Steps | Pattern |
|--------|-------|---------|
| `_auto_present_name` | NAME | `_narrate_flavor` |
| `_auto_present_race` | RACE | `_narrate_flavor` |
| `_auto_present_class` | CLASS | `_narrate_flavor` |
| `_auto_present_skills` | SKILLS | `_creation_table_flavor` (skips LLM on `error=`) |
| `_auto_present_schools` | SPELL_SCHOOLS | `_creation_table_flavor` |
| `_auto_present_spells` | SPELLS | `_creation_table_flavor` |
| `_auto_present_equipment` | EQUIPMENT_GOLD | `_narrate_flavor` |
| `_auto_roll_stats` | ROLL_STATS→CLASS | `_narrate_creation_flavor` |
| `_auto_finalize` | FINALIZE→WORLD_INTRO | `_narrate_flavor` + custom footer |

Central choke points: **`_narrate_flavor`** (LLM call), **`_creation_flavor_messages`** (prompt), **`_compose_creation_narration`** (post-process).

### Sumpty repro (session evidence)

| Log line | Step | LLM violation | Code truth (body below flavor) |
|----------|------|---------------|--------------------------------|
| L4743 | SPELL_SCHOOLS | Lists Restoration, Evocation, Abjuration, … (8 generic schools) | Pyromancy, Ward, Biomancy, Necromancy, Ether, Divine table |
| L4749 | SPELLS | Fake `\| School \| Spells \|` table; Restoration, Communion, Warding; `finish_reason: length` | Mend Light, Consecrate Ground, Aegis Spark table |
| L4755 | EQUIPMENT_GOLD | *bedroll, waterskin, rope, flint, 50 gold*; premature delve readiness | Warhammer kit, **20 gp** in `format_equipment_summary` |

Player sees **both** wrong flavor and correct body in one `gm_narration` blob — TTS reads flavor first.

### Exploration (Phase 2 — trace only)

1. `process_turn` → `_llm_loop` (full tools) → raw `content`.
2. `_compose_exploration_narration(prose, gate_active)` — `sanitize_premature_site_entry_flavor` (APP-024) strips interior fiction when surface + no `enter_dungeon` ok; may replace with refusal line. **No retry.**

### Combat (Phase 3 — trace only)

1. `_combat_turn` → `_combat_llm_loop_inner` → tool chain → optional final narrate pass.
2. On `all_failed`: returns `[Mechanics failed — …]` prefix, strips assistant success prose. **No verify/retry** on success-path narration.

## Current architecture gaps

| Gap | Detail | Partial mitigation today |
|-----|--------|---------------------------|
| **No mechanical truth in flavor prompt** | `_committed_state_flavor_block()` omits step catalogs, GP, kit, spell/school allowlists | Prompt says "no tables" but model fills from training data |
| **Scrub-and-ship, not verify→retry** | `_compose_creation_narration` deletes bad regions; does not regenerate | APP-072/073 race/stats table strips |
| **No catalog/economy rules** | Wrong school names (Restoration, Evocation), fake spell tables, wrong GP/kit ship in flavor | None for schools/spells; APP-059 `strip_flavor_equipment_claims` **spec'd but not implemented** |
| **Truncation still publishes** | `_CREATION_FLAVOR_MAX_TOKENS = 120`; SPELLS repro `finish_reason: length` leaves partial fake table in flavor | No length recovery on flavor path (APP-079 is exploration-oriented) |
| **Prompt conflict** | `system_prompt.py` § Character creation instructs LLM to list races in tables and present equipment — fights code-owned tables (APP-006/069) | `_creation_flavor_messages` secondary instruction partially overrides |
| **Fragmented enforcement** | Creation strippers, exploration site strip, combat failure prefix — no unified policy | APP-024, APP-028, APP-070, APP-073 |
| **Spec/code drift on compose pipeline** | `app-character-creation-spec.md` documents `strip_flavor_equipment_claims` in compose order; code lacks it | APP-059 open |
| **No observability** | No `narration_verify_fail/pass/exhausted` JSONL | — |
| **Exploration/combat prose ungated** | Full `_llm_loop` content can assert mechanics without verify | Prompt + tool-failure messages only |

## Proposed wiring (APP-083)

### New module: `app/gm/narration_verify.py`

| Type / function | Responsibility |
|-----------------|----------------|
| `TurnTruth` dataclass | `mode`, `step`, `engine`, `tool_results`, `allowed`, `forbidden`, `code_blocks` (per ticket) |
| `VerificationResult` | `passed: bool`, `violations: list[str]` |
| `format_turn_truth_for_prompt(truth) -> str` | Compact `## Authoritative facts (do not contradict)` block |
| `verify_narration(prose, truth) -> VerificationResult` | Universal rules + mode delegate |
| `CREATION_CATALOG_DENYLIST` | Generic TTRPG schools (Restoration, Evocation, Abjuration, Conjuration, Transmutation, Divination, Enchantment, Communion, Warding, …) |

### `build_creation_turn_truth(creation)` — `app/gm/creation.py`

Build from same sources as mechanics (never parse markdown back):

| Step | `allowed` (examples) | `forbidden` / notes |
|------|------------------------|---------------------|
| SPELL_SCHOOLS | `eligible_schools_for_class` display names + ids; novice Divine+1 rule | denylist schools; no markdown `\| School \|` in flavor |
| SPELLS | `tier1_spells_for_schools(chosen_schools)` ids/names; min Divine rule | fake school groupings; spell tables |
| EQUIPMENT_GOLD | `creation.equipment_kit`, `creation.starting_gold` after `ensure_equipment_gold` | GP/kit prose, premature finalize/delve |
| ROLL_STATS | committed race; roll in `creation.roll_result` | stat numbers, `\| Attr \|` |
| RACE/CLASS/SKILLS | committed + table eligibility | duplicate tables, wrong race (existing F3) |
| All active steps | committed block | `Awaiting:`, `[Location:`, `Phase:` in flavor |

Set `code_blocks` to human-readable hints ("code will append school pick table — do not duplicate") not full markdown tables.

### `format_turn_truth_for_prompt` — inject in `_creation_flavor_messages`

Replace/enhance thin committed block:

```text
## Authoritative facts (do not contradict)
Step: SPELL_SCHOOLS
Rule: Choose Divine + 1 other school (2 total).
Allowed schools: Pyromancy, Ward, Biomancy, Necromancy, Ether, Divine
Committed: name Sumpty, race Undead, class Novice, skills …
Code will append: full school pick table — do not duplicate
```

On retry: append same truth block + `Your last draft violated: {violations}. Rewrite banter only.`

### `narrate_with_verification` — `app/gm/orchestrator.py`

Suggested signature:

```python
def narrate_with_verification(
    self,
    *,
    mode: Literal["creation", "exploration", "combat"],
    build_messages: Callable[[str | None], list[dict]],  # violations feedback
    truth: TurnTruth,
    presenting_step: str | None = None,
) -> str:
```

Loop:

1. `truth = build_creation_turn_truth(self.creation)` (or passed in).
2. Messages = `build_messages(None)` including `format_turn_truth_for_prompt(truth)`.
3. `prose = _narrate_flavor(messages)` (keep 120-token cap for creation Phase 1).
4. `result = verify_narration(prose, truth)` → pass → return prose.
5. Fail → log `narration_verify_fail` → `build_messages(violations)` → goto 3.
6. Exhaust `NARRATION_VERIFY_MAX_RETRIES` (config, default 5) → log `narration_verify_exhausted` → return `""` or code-owned fallback line; `_compose_creation_narration` still appends body/footer.

**Wire points (Phase 1):**

| Location | Change |
|----------|--------|
| `_creation_flavor_messages` | Add `format_turn_truth_for_prompt(build_creation_turn_truth(...))`; trim conflicting table instructions from inline block once truth block exists |
| `_narrate_flavor` | Keep as low-level LLM caller; **do not** call directly from creation presenters |
| `_narrate_creation_flavor`, `_creation_table_flavor`, all `_auto_present_*` flavor paths | Call `narrate_with_verification` instead of `_narrate_flavor` |
| `_compose_creation_narration` | Phase 1: retain strippers as **defense in depth** OR fold into `verify_narration` and simplify compose (PM decision); ticket AC implies verify is primary gate |
| `_emit_narration` | Unchanged — only receives post-verify composed string |
| `system_prompt.py` | Phase 1 prompt hygiene: remove creation table mandates that fight code-owned bodies |

**Phase 2–3 (out of Phase 1 impl):**

| Path | Builder | Verify hook |
|------|---------|-------------|
| `_llm_loop` return | `build_exploration_turn_truth(status, tool_results, gate_flags)` | Before `_compose_exploration_narration` |
| `_combat_llm_loop_inner` final narrate | `build_combat_turn_truth` | Replace/supplement failure-prefix-only path |

### Creation verify rule set (Phase 1 minimum)

Fold existing stripper behavior into **fail** (trigger retry), not silent delete:

| Rule class | Implementation sketch |
|------------|----------------------|
| Universal | Markdown table rows in flavor; `Awaiting:` / `[Location:` / `Phase:` tags |
| Catalog | School/spell token ∉ `allowed`; denylist match (Restoration, Evocation, …) |
| Economy | `\d+\s*(gp|gold|coin)` or kit inventory prose when step is EQUIPMENT_GOLD |
| Race | Whole-word other race titles (current `_sanitize_creation_flavor`) |
| Premature completion | APP-070 patterns |
| Stats | APP-073 fingerprints (`\| Attr \|`, `### Your Attributes`) |

**Sumpty repro:** L4743/L4749/L4755 flavor regions **must fail** verify; mock LLM retry with benign banter **must pass** before `_emit_narration`.

## Phase 1 scope recommendation (this batch)

**In scope:**

- New `narration_verify.py` + `test_narration_verify.py` with shared types and logging hooks.
- `build_creation_turn_truth` + creation branch of `verify_narration` + `format_turn_truth_for_prompt`.
- `narrate_with_verification` wired for **all creation flavor paths** listed above (including `_auto_finalize` world-intro flavor — still `creation.active` transition).
- Orchestrator + `app-llm-orchestrator-spec.md` § Mechanical-truth narration gate; creation spec rule matrix (Phase 1 section).
- Supersede APP-082 / creation slices of APP-078/059/073 **in docs** — implement denylist/catalog/economy verify instead of-only strippers.
- Unit tests: Sumpty violations, benign banter pass, mock retry integration.

**Out of scope (explicit defer):**

- `build_exploration_turn_truth` / `_llm_loop` gate (Phase 2).
- `build_combat_turn_truth` / combat loop gate (Phase 3).
- Economy/inventory assertions in play (Phase 4).
- UI wait indicator for retries.
- Replacing tool/FSM gates (APP-080 stays sibling layer).

**Ticket close note:** Ticket AC lists Phases 2–3 as "required for close" — PM should decide single ticket vs sub-tickets; research recommends **framework + Phase 1 land in this batch**, Phases 2–3 as follow-on work with shared module already present.

## Existing specs & docs

- **Ticket:** `tmp/backlog/app-083-creation-flavor-verification-gate.md` — full architecture, phased AC.
- **Primary domain spec:** `tmp/app-llm-orchestrator-spec.md` — mechanical-truth principle stated; no verify pipeline yet.
- **Creation spec:** `tmp/app-character-creation-spec.md` — documents stripper pipeline as "pass gate" (Option A); **will need rewrite** for verify→retry→publish (APP-083).
- **Logging spec:** `tmp/app-logging-qa-spec.md` — add `narration_verify_*` events on implement.
- **Related open tickets subsumed Phase 1:** APP-059 (equipment strip), APP-072/073 (table dedup), APP-070 (premature completion), APP-082 (creation flavor verification — duplicate intent).

## Tests & commands

```bash
# Existing creation flavor / table tests (strip-only today)
cd app && python -m pytest tests/test_creation_flavor_sanitize.py tests/test_creation_tables.py tests/test_creation_flow.py -q

# New (ticket Expected files)
cd app && python -m pytest tests/test_narration_verify.py -q

# Full app suite before close
cd app && python -m pytest tests/ -q
```

**Minimum new tests (from ticket AC):**

| Test | Assert |
|------|--------|
| `format_turn_truth_for_prompt` unit | SPELL_SCHOOLS includes allowed school ids/names; no full duplicate table markdown |
| Creation verify — Sumpty strings | L4743/L4749/L4755 flavor excerpts → `fail` with catalog/economy violations |
| Creation verify — benign banter | Short clerk line with no catalogs → `pass` |
| Integration mock retry | Stub LLM fails twice (injected bad prose) then passes → player sees only passing flavor in composed narration |
| Integration exhausted | Stub always fails → no bad prose in final emit; `narration_verify_exhausted` logged |

## Risks & unknowns

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Latency** | Each verify fail = extra LLM round-trip at desk | Log `attempts`; 120-token flavor calls stay cheap; cap retries at 5 |
| **Over-aggressive verify** | Benign fantasy words false-positive (e.g. "evocation" in metaphor) | Word-boundary + denylist for known wrong **school names**; allowlist-first for SPELLS step |
| **120-token truncation** | Model starts table, hits length, partial fake table fails verify repeatedly | Treat partial `\|` tables as fail; consider bumping flavor max tokens or empty fallback after N fails |
| **Stripper vs verify duplication** | Two systems diverge | Phase 1: verify primary; strippers optional safety net until PM consolidates compose |
| **system_prompt.py scope** | Trimming may affect dead `_creation_llm_loop` paths | Scope trim to creation sections; code FSM does not use tool loop for gated steps |
| **Phased ticket close** | AC requires Phases 2–3 for `done` | PM/spec must split close criteria or sub-tickets |
| **`_auto_finalize` footer** | Custom `[Location: …\| Phase: preparation]` footer is code-owned — verify must not run on footer | Verify flavor only before compose (unchanged boundary) |
| **APP-059 not implemented** | Equipment GP leak until verify lands | Phase 1 verify economy rules cover Sumpty L4755 |

## Raw notes

- `_CREATION_FLAVOR_MAX_TOKENS = 120` at `orchestrator.py:81`.
- `strip_flavor_equipment_claims` — documented in `app-character-creation-spec.md` § APP-059, **grep finds no implementation** in `app/`.
- Canon schools (`build/data/spells/schools.json`): pyromancy, ward, biomancy, necromancy, ether, divine — six schools, not eight generic.
- `_creation_llm_loop` exists but gated steps use code-first `_handle_creation_response`; flavor path is separate from tool loop.
- `build_state_context` (`context.py`) is exploration authoritative block — ticket proposes parallel `TurnTruth` builder for creation, extend/replace for exploration Phase 2.
- Session SKILL step (L4737): LLM also embeds ask prose duplicating code table prompt — lower priority than catalog bugs; verify "no duplicate step instructions" optional Phase 1 stretch.
