# Spec: APP-083-mechanical-truth-narration-gate

**Status:** draft  
**backlog_ticket:** APP-083  
**ticket_path:** [tmp/backlog/app-083-creation-flavor-verification-gate.md](../../app-083-creation-flavor-verification-gate.md)  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) (primary)  
**registry_gap:** false  
**Domain specs touched:** `tmp/app-llm-orchestrator-spec.md`, `tmp/app-character-creation-spec.md` (Phase 1); Phases 2–3 defer to exploration/combat specs

## Batch close scope (PM decision)

**This batch closes APP-083 Phase 1 only.** Shared framework (`TurnTruth`, `verify_narration`, `narrate_with_verification`, logging) ships in Phase 1; exploration and combat wiring are **documented as future phases** — not required for ticket `done` in this batch.

| Phase | Scope | Batch |
|-------|-------|-------|
| **1 — Creation** | Truth builder, prompt injection, verify+retry on all creation flavor paths | **Required for close** |
| **2 — Exploration** | `build_exploration_turn_truth`, `_llm_loop` gate (APP-024 parity + retry) | Future — follow-on ticket or same ticket reopen |
| **3 — Combat** | `build_combat_turn_truth`, combat loop gate (APP-028 parity + retry) | Future |
| **4 — Economy in play** | loot/GP/vendor prose assertions | Future |

## Problem

Creation (and later exploration/combat) narration is **thin LLM flavor + code body + code footer**, but flavor is generated **without step catalogs** (schools, spells, kit, GP) and published **immediately** after regex strippers. Sumpty session (`app/logs/session-2026-05-21.jsonl` L4743, L4749, L4755): wrong schools (Restoration, Evocation…), fake spell tables, invented kit/GP **above** correct code tables. Strippers (APP-072/073/070) delete duplicate race/stats tables but **do not** catch catalog hallucinations or economy claims — and **scrub-and-ship** never regenerates.

**Root pattern:** no unified **verify → retry until pass → publish** policy; truth is not injected into flavor prompts.

## Goals

- **TurnTruth in, verify out** — same snapshot injected into every narration LLM call and used for post-draft verification.
- **Player never sees unverified flavor** — failed drafts retry with violation feedback; bounded circuit breaker with code-owned fallback.
- **Phase 1:** all creation flavor paths through `narrate_with_verification`; Sumpty repro strings **fail** verify; mock retry **passes** before emit.
- **Supersede** creation-only strip-first policy in docs (APP-082; creation slices of APP-078/059/073) — verify is primary; strippers optional defense-in-depth in compose.

## Non-goals (Phase 1)

| Deferred | Phase / ticket |
|----------|----------------|
| `_llm_loop` exploration gate | Phase 2 — `app-exploration-delve-spec.md` |
| Combat loop gate | Phase 3 — `app-combat-play-spec.md` |
| Economy/inventory assertions in play | Phase 4 |
| UI wait indicator for retries | Optional v1 |
| Replacing tool/FSM gates | APP-080 stays sibling layer |
| Canon `build/systems/` content changes | APP-061 etc. |

## Requirements (summary)

Full architecture: domain spec § **Mechanical-truth narration gate** ([`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md)). Creation rule matrix: [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) § **Mechanical-truth narration gate (APP-083 Phase 1)**.

| ID | Summary | Locus |
|----|---------|-------|
| **N1** | `TurnTruth` dataclass + `VerificationResult` | `app/gm/narration_verify.py` |
| **N2** | `build_creation_turn_truth(creation)` — allowed schools/spells/kit/GP/committed fields from same sources as mechanics | `app/gm/creation.py` |
| **N3** | `format_turn_truth_for_prompt(truth)` — compact `## Authoritative facts (do not contradict)` block; no full duplicate markdown tables | `app/gm/narration_verify.py` |
| **N4** | `verify_narration(prose, truth)` — universal + creation rule set (catalog denylist, economy, tables, tags, race, premature completion) | `app/gm/narration_verify.py` |
| **N5** | `narrate_with_verification(...)` — build truth → prompt → generate → verify → retry or publish; max `NARRATION_VERIFY_MAX_RETRIES` (default 5) | `app/gm/orchestrator.py` |
| **N6** | Wire all creation flavor call sites through N5 (not raw `_narrate_flavor`) | `orchestrator.py` — `_auto_present_*`, `_creation_table_flavor`, `_narrate_creation_flavor`, `_auto_finalize` flavor |
| **N7** | `_creation_flavor_messages` includes `format_turn_truth_for_prompt`; retry appends violation feedback, truth block unchanged | `orchestrator.py` |
| **N8** | JSONL: `narration_verify_fail`, `narration_verify_pass`, `narration_verify_exhausted` | `app/gm/logger.py` + logging spec on implement |
| **N9** | Prompt hygiene: trim `system_prompt.py` creation table mandates that conflict with code-owned bodies | `app/gm/system_prompt.py` |
| **N10** | Exhaustion fallback: empty flavor or code-owned one-liner; `_compose_creation_narration` still appends body + footer | `orchestrator.py` |

### Phase 1 creation verify rules (minimum)

| Rule class | Fail when | Notes |
|------------|-----------|-------|
| Universal | Markdown table rows in flavor; `Awaiting:` / `[Location:` / `Phase:` in flavor | Fold APP-073 strip behavior into **fail** |
| Catalog | School/spell ∉ allowed; denylist (Restoration, Evocation, Abjuration, …) | Sumpty L4743/L4749 |
| Economy | GP/kit prose on EQUIPMENT_GOLD | Sumpty L4755; replaces unimplemented APP-059 strip |
| Race | Whole-word other race title | APP-069 F3 |
| Premature completion | APP-070 patterns while desk active | |
| Stats | APP-073 fingerprints (`\| Attr \|`, `### Your Attributes`) | |

**Verify boundary:** flavor only — never code `body` or explicit `footer` (`_auto_finalize` reception footer unchanged).

### Compose after verify (Phase 1)

Verified flavor → `_compose_creation_narration` may retain strippers as **defense in depth** until Dev consolidates; **verify is the pass gate** — unverified flavor never reaches compose.

## Acceptance criteria mapping (Phase 1 batch close)

| Ticket AC (Phase 1) | Spec / test |
|---------------------|-------------|
| `TurnTruth` + `build_creation_turn_truth` | N1–N2 |
| `format_turn_truth_for_prompt` wired into `_creation_flavor_messages` | N3, N7 |
| `verify_narration` creation rule set | N4 |
| `narrate_with_verification` on all creation flavor paths | N5–N6 |
| Sumpty L4743/L4749/L4755 fail verify; mock retry pass before emit | `test_narration_verify.py` |
| Supersede APP-082 / creation flavor slices in docs | Domain spec changelog + this spec |
| Decision: verify→retry→publish canonical | Orchestrator spec § Mechanical-truth narration gate |

**Not required for this batch close:** Phase 2 exploration AC, Phase 3 combat AC (documented as future in domain specs).

## Test plan

```bash
cd app && python -m pytest tests/test_narration_verify.py -q          # new
cd app && python -m pytest tests/test_creation_flavor_sanitize.py -q  # no regressions
cd app && python -m pytest tests/test_creation_flow.py -q
cd app && python -m pytest tests/ -q                                   # before release
```

| Test | Assert |
|------|--------|
| `format_turn_truth_for_prompt` unit | SPELL_SCHOOLS includes allowed school ids/names; no full duplicate table markdown |
| Creation verify — Sumpty excerpts | L4743/L4749/L4755 flavor → `fail` with catalog/economy violations |
| Creation verify — benign banter | Short clerk line → `pass` |
| Integration mock retry | Stub LLM bad twice then good → player sees only passing flavor in composed narration |
| Integration exhausted | Stub always bad → no bad prose in emit; `narration_verify_exhausted` logged |

## Expected files (implementation)

- `app/gm/narration_verify.py` — **new**
- `app/gm/creation.py` — `build_creation_turn_truth`
- `app/gm/orchestrator.py` — `narrate_with_verification`, creation wiring
- `app/gm/system_prompt.py` — Phase 1 prompt hygiene
- `app/gm/logger.py` — verify events (or defer to logging spec sync)
- `app/tests/test_narration_verify.py` — **new**
- `tmp/app-llm-orchestrator-spec.md` — § Mechanical-truth narration gate
- `tmp/app-character-creation-spec.md` — Phase 1 rule matrix + cross-link

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Novice caster (Sumpty path):** SPELL_SCHOOLS / SPELLS / EQUIPMENT_GOLD flavor must not list generic D&D schools, fake spell tables, or wrong GP/kit — only clerk banter above code tables.
- **Retries invisible:** Player must not see failed LLM drafts; if model keeps failing, clerk line may be empty/minimal but body/footer still correct.
- **Session log:** `narration_verify_pass` / `narration_verify_fail` with `attempt` counts on creation desk steps.

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — code traces, Sumpty evidence, wiring table, Phase 1 vs 2–3 split
- **Ticket (full AC):** [app-083-creation-flavor-verification-gate.md](../../app-083-creation-flavor-verification-gate.md)
- **Primary domain truth:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) — § Mechanical-truth narration gate
- **Creation rules:** [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md) — § Mechanical-truth narration gate (APP-083 Phase 1)
- **Subsumed (Phase 1 docs):** APP-082, creation slices APP-078/059/073; strippers remain optional defense-in-depth
- **Future phases:** APP-024 → Phase 2 exploration verify; APP-028 → Phase 3 combat verify

## Changelog

| Date | Change |
|------|--------|
| 2026-05-21 | Initial PM draft — Phase 1 batch close scope; verify→retry→publish; Phases 2–3 deferred |
