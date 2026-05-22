# APP-083: Mechanical-truth narration gate (verify → retry → publish)

| Field | Value |
|-------|-------|
| **ID** | APP-083 |
| **Type** | feature |
| **Priority** | P0 |
| **Status** | done |
| **Closed** | 2026-05-21 (Phase 1 only) |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) (primary); cross-domain updates in creation, exploration, combat specs |
| **Created** | 2026-05-21 |

## Summary

Tomb Dust has **rules enforced in code** (engine, bridge, FSM, catalogs). The LLM adds **flavor and fiction** but routinely **invents mechanics** — wrong schools, spells, kit, gold, site entry, combat outcomes. Today enforcement is **fragmented**: creation strippers (APP-072/073/082), exploration site-entry gate (APP-024), combat failure prefixes (APP-028), tool-arg coercion (APP-080). There is **no unified policy** that bad prose is **withheld, regenerated, and only published after verification passes**.

Introduce a **game-wide narration gate**: build **TurnTruth** before the LLM call, **inject truth into the prompt** so the model writes fitting prose, then **verify → retry until pass → publish**. Code owns mechanical truth; the LLM colors inside those bounds — it does not invent parallel facts.

**Phase status (2026-05-22):** **Phase 1 (creation)** shipped. **Phase 2 (exploration)** partial → [APP-084](app-084-key-npc-canon-registry.md) key-NPC verify + [APP-077](app-077-code-owned-exploration-status-footer.md) footer. **Phase 2 encounter slice:** [APP-089](app-089-encounter-awareness-before-combat.md) — `build_encounter_turn_truth`, pre-combat verify, combat handoff. **Phase 3 (combat):** [APP-090](app-090-combat-phased-narration-and-death-beat.md) — per-phase `build_combat_turn_truth`. **Phase 4 (economy)** open. This ticket is **closed for Phase 1** only; later phases ship via linked tickets.

## Problem (observed)

### Creation (clearest repro)

Session `app/logs/session-2026-05-21.jsonl`, Sumpty (Undead Novice):

| Step | LLM flavor (wrong) | Code truth |
|------|-------------------|------------|
| `SPELL_SCHOOLS` | Restoration, Evocation, Abjuration, … | Pyromancy…Divine table |
| `SPELLS` | Fake `\| School \| Spells \|` table | Mend Light, Consecrate Ground, Aegis Spark |
| `EQUIPMENT_GOLD` | *50 gold*, bedroll kit | Novice kit + **20 gp** |

Player never sees failed validation, but narration **actively misleads** before the code block.

### Exploration & combat (same class, different shape)

| Failure mode | Example | Partial fix today |
|--------------|---------|-------------------|
| Site entry without tool | *"You step into the torchlit crypt"* while `mode=surface` | APP-024 strip (reactive, no retry) |
| Combat success without tool | Hit/damage fiction when `combat_attack` `ok: false` | APP-028 failure prefix (no retry) |
| Wrong location/phase in prose | `[Location: …]` / `Phase: delve` while on surface | Partial tag strip (APP-073) |
| Invented loot/spells/NPC facts | Not systematically checked | Prompt only |

**Root pattern:** the LLM is asked for flavor **without** the authoritative facts for the current step (creation flavor gets step name + committed fields, not eligible schools/kit/GP). It fills gaps from training data. Prose then ships **before** verification. Prompts and post-hoc strippers are insufficient ([`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md): *code state leads narration*).

## Solution (game-wide architecture)

### Core principle

```text
Mechanics in code  →  TurnTruth built  →  truth injected into LLM prompt
       →  LLM drafts fitting prose  →  verify(prose, truth)
       →  fail? retry (same truth + violation feedback)  →  pass? publish
```

**Truth serves two roles:** (1) **context in** — tell the model what is actually true so it can write appropriately; (2) **gate out** — reject prose that still contradicts truth. Verification is the safety net, not the only line of defense.

**The player never sees unverified narration.** Retry until pass; circuit breaker only for hung API / runaway loops.

### Two layers (keep both)

| Layer | What | When | Existing work |
|-------|------|------|---------------|
| **Tool / FSM gate** | Args valid; bridge call succeeds; state transitions committed | Before / during turn | APP-080, bridge, combat FSM |
| **Narration gate** | Prose does not assert facts outside truth snapshot | After LLM draft, before emit | **This ticket** |

Tool gate answers *"did the action happen?"* Narration gate answers *"does the story match what happened?"*

### `TurnTruth` — one snapshot type, mode-specific builders

```python
TurnTruth(
    mode: Literal["creation", "exploration", "combat"],
    step: str | None,                    # creation FSM step
    engine: dict,                        # bridge.status() slice
    tool_results: list[ToolResult],      # this turn, in order
    allowed: AllowedClaims,              # what prose MAY reference
    forbidden: ForbiddenClaims,          # hard deny patterns
    code_blocks: list[str],              # body/footer strings code will append
)
```

**Builders** (each reads same sources as mechanics, never parses markdown back):

| Mode | Builder | `allowed` examples |
|------|---------|-------------------|
| **creation** | `build_creation_turn_truth(creation)` | eligible schools/spells, kit, GP, committed race/class/skills |
| **exploration** | `build_exploration_turn_truth(status, tool_results, gate_flags)` | current address/mode, exits if queried, items in pack, tools that succeeded this turn |
| **combat** | `build_combat_turn_truth(status, combat_state, tool_results)` | active combatants, HP bands, last attack outcome, legal targets |

Catalog denylist (Restoration, Evocation, …) shared across modes where relevant.

### Truth-as-context — inject before the LLM call

If truth is built before generation, **send it to the LLM** — do not hoard it for post-hoc verification only.

**Helper:** `format_turn_truth_for_prompt(truth: TurnTruth) -> str` — compact, structured system block (not player-facing).

**Prompt contract (all modes):**

- Include an **## Authoritative facts (do not contradict)** section derived from `TurnTruth`.
- State explicitly: *"The UI will append code-owned tables/footers below your prose. Write 1–3 sentences of clerk/scene banter only. Do not list picks, stats, kit, gold, schools, spells, or outcomes — reference the facts block if needed."*
- On **retry**, re-send the **same truth block** plus *"Your last draft violated: {violations}. Rewrite banter only."*

**Creation example** (SPELL_SCHOOLS / Novice) — facts block includes:

```text
Step: SPELL_SCHOOLS
Rule: Choose Divine + 1 other school (2 total).
Allowed schools: Pyromancy, Ward, Biomancy, Necromancy, Ether, Divine
Committed: name Sumpty, race Undead, class Novice, skills Medicine/Spellcasting/Mana Control
Code will append: full school pick table — do not duplicate
```

**Exploration example** — facts block includes: `mode`, `address`, `tools_ok_this_turn` (e.g. `enter_dungeon: false`), pack summary if relevant, last check result.

**Combat example** — facts block includes: turn owner, HP snapshot, last `combat_action` result (`hit/miss`, damage if ok).

**Replace thin context today:** `_creation_flavor_messages` only sends committed name/race/class/skills — **not** step catalogs. Phase 1 must wire `format_turn_truth_for_prompt` into every creation flavor call. Exploration already has `build_state_context` — extend/replace with truth block from same `TurnTruth` builder (one source, two formatters: prompt vs verify).

**Do not** dump full markdown tables into the prompt if code body will append them — send **allowed ids/names + rules**, not duplicate table layout. Goal: model knows the canon vocabulary, not re-print the UI.

### `verify_narration(prose, truth) -> VerificationResult`

Single entry point; **mode delegates** to rule sets:

| Rule class | Applies | Examples |
|------------|---------|----------|
| **Universal** | all | no duplicate code tables; no `Awaiting:` / fake status tags in flavor |
| **Catalog** | creation (+ spell lists in play) | no school/spell/item outside allowed sets |
| **Economy** | creation equipment, vendors | no GP/kit claims ≠ truth |
| **Spatial** | exploration | no interior/site fiction when `mode=surface` and entry tool not ok this turn (APP-024 rules → verify fail) |
| **Combat outcome** | exploration + combat | no hit/damage/kill/start/end unless matching tool ok this turn (APP-028 rules → verify fail) |
| **Stat/mechanical** | creation rolls, combat HP | no numbers contradicting engine snapshot |

Outcomes: **pass** | **fail(violations: list[str])** — no scrub-and-ship.

### `narrate_with_verification(...) -> str`

Shared orchestrator helper used by all modes:

1. Build `TurnTruth` for current turn.
2. Build LLM messages with **`format_turn_truth_for_prompt(truth)`** in system context (mode-specific instruction + player input).
3. Generate LLM prose.
4. `verify_narration(prose, truth)` → pass → compose final string (prose + code blocks + footers) → return.
5. Fail → append violation feedback (**truth block unchanged**) → goto 3.
6. After `NARRATION_VERIFY_MAX_RETRIES` (config, default **5**) → log `narration_verify_exhausted`; ship code-owned fallback only.

**Emit once** per turn after pass (or exhaustion) — UI/TTS never see intermediate failures.

### Where it wires in

| Path | Current | Target |
|------|---------|--------|
| `_creation_turn` / `_compose_creation_narration` | flavor + body concat | verified flavor via `narrate_with_verification` |
| `_llm_loop` exploration return | `_compose_exploration_narration` strip only | verify full prose + retry; then APP-024/077 compose |
| `_combat_llm_loop_inner` return | failure prefix on tool fail | verify + retry; failure prefix when tools fail AND prose claims success |
| Code-only paths (errors, resume) | bypass | unchanged — no LLM |

### Relationship to existing tickets

| Ticket | After APP-083 |
|--------|---------------|
| APP-082, APP-078, APP-059 flavor strips | **Folded into** verify rules (Phase 1) |
| APP-024 site-entry strip | **Becomes** exploration verify rules (Phase 2) |
| APP-028 combat failure narration | **Becomes** combat verify rules (Phase 2) |
| APP-070 premature completion | creation verify rules |
| APP-080 tool args | **Stays** — pre-dispatch sibling layer |
| APP-077 exploration footer | **Stays** — code-owned compose after verified prose |

Implement APP-083 **instead of** closing APP-082/078 flavor slices separately.

### Phased delivery

| Phase | Scope | Domain spec updates | Why first |
|-------|-------|---------------------|-----------|
| **1** | Creation flavor + code bodies | `app-character-creation-spec.md` | Finite catalogs; Sumpty repro; no tool loop |
| **2** | Exploration prose after `_llm_loop` | `app-exploration-delve-spec.md` | APP-024/028 patterns → verify+retry |
| **3** | Combat prose after combat loop | `app-combat-play-spec.md` | Outcome claims vs tool results |
| **4** | Economy/inventory assertions in play | `app-economy-inventory-play-spec.md` | loot/GP/vendor claims |

Each phase lands tests + changelog before the next. Shared framework (`TurnTruth`, `verify_narration`, `narrate_with_verification`, logging) ships in **Phase 1** even if rule sets start narrow.

### Observability

JSONL events (all modes):

| Event | When |
|-------|------|
| `narration_verify_fail` | Each failed attempt (`mode`, `step`, `violations`, `attempt`) |
| `narration_verify_pass` | Success (`attempts`) |
| `narration_verify_exhausted` | Circuit breaker |

### Prompt hygiene (Phase 1)

`system_prompt.py` still instructs creation markdown tables — conflicts with code-owned tables (APP-006/069). Trim conflicting static lore; step facts come from `TurnTruth` prompt block per turn.

## Acceptance criteria

### Decision (document in specs)

- [ ] **TurnTruth in, verify out** — truth injected into every narration LLM call; same object used for verification.
- [ ] **Verify → retry until pass → publish** is the canonical app-wide narration policy ([`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md)).
- [ ] Failed prose is **never** shown; retries are bounded with documented fallback.
- [ ] Per-mode rule sets documented in respective domain specs; master spec links the pipeline.

### Phase 1 — Creation (required for close)

- [ ] `TurnTruth` + `build_creation_turn_truth(creation)`.
- [ ] `format_turn_truth_for_prompt(truth)` + wired into `_creation_flavor_messages` (replaces thin committed-only block for gated steps).
- [ ] `verify_narration` with creation rule set (catalog, economy, tables, tags).
- [ ] `narrate_with_verification` retry loop wired into all creation flavor paths.
- [ ] Sumpty repro lines (L4743, L4749, L4755) fail verify; mock retry produces pass before emit.
- [ ] Supersede APP-082 / creation flavor slices of APP-078/059 in docs.

### Phase 2 — Exploration (required for close)

- [ ] `build_exploration_turn_truth` + spatial/entry rules (APP-024 parity + retry).
- [ ] `_llm_loop` final content through narration gate before `_compose_exploration_narration`.

### Phase 3 — Combat (required for close)

- [ ] `build_combat_turn_truth` + outcome rules (APP-028 parity + retry).
- [ ] Combat loop content through narration gate.

### Tests (minimum)

- [ ] Unit: `format_turn_truth_for_prompt` includes allowed schools/spells/kit for step — no full duplicate table.
- [ ] Unit: creation verify — Sumpty violations, benign banter pass.
- [ ] Unit: exploration verify — site entry fiction on surface without tool → fail.
- [ ] Unit: combat verify — hit fiction without `combat_attack` ok → fail.
- [ ] Integration: mock LLM fails twice then passes → player sees only passing prose.
- [ ] Integration: mock always fails → exhausted fallback, no bad prose leaked.

## Expected files

- `app/gm/narration_verify.py` (or `app/gm/verify.py`) — `TurnTruth`, verify, shared types
- `app/gm/logger.py` — `narration_verify_*`, `llm_truncation_recovery` JSONL helpers
- `app/gm/creation.py` — creation truth builder
- `app/gm/orchestrator.py` — `narrate_with_verification`, mode wiring
- `app/tests/test_narration_verify.py`
- `app/tests/test_llm_truncation_recovery.py`
- `app/tests/test_creation_flow.py` — mock `_call_narration_llm` for flavor capture
- `tmp/app-llm-orchestrator-spec.md` — primary spec home
- `tmp/app-character-creation-spec.md` — Phase 1 rules
- `tmp/app-exploration-delve-spec.md` — Phase 2 rules
- `tmp/app-combat-play-spec.md` — Phase 3 rules
- `tmp/app-logging-qa-spec.md` — log events
- `tmp/app-master-spec.md` — pipeline link

## Spec sync (required on close)

1. Mark **Status** → `done` + **Closed** date when **Phase 1** complete _(Phases 2–4 tracked in APP-084, APP-077, combat/economy follow-ons)_.
2. Add **§ Mechanical-truth narration gate** to orchestrator spec — architecture diagram, TurnTruth, verify, retry, compose order.
3. Update creation / exploration / combat specs with per-mode rule matrices.
4. Changelog entries in each touched spec.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-012 | thin creation flavor — preserved inside verified gate |
| APP-069 | code-owned creation bodies — unchanged |
| APP-073/072/082/078/059 | creation flavor strippers — **Phase 1 verify replaces need for new strip work**; APP-078/082 **cancelled** |
| APP-024/028/070 | exploration/combat strips — **subsumed** Phases 2–3 |
| APP-084 | Phase 2 partial — key NPC TurnTruth + verify on exploration prose |
| APP-080 | orthogonal — tool args before dispatch |

## Notes

### Mental model for designers

```text
         ┌─────────────────────────────────────┐
         │         CODE (rules / engine)        │
         │  FSM · tools · catalogs · status     │
         └──────────────┬──────────────────────┘
                        │ TurnTruth
            ┌───────────┴───────────┐
            ▼                       ▼
   format_turn_truth_for_prompt   verify_narration
            │                       ▲
            ▼                       │
         ┌─────────────────────────────────────┐
         │   LLM (banter; truth in context)     │
         └──────────────┬──────────────────────┘
                        │ fail → retry (same truth)
                        ▼ pass
         ┌─────────────────────────────────────┐
         │   PUBLISH: verified prose + code     │
         │   blocks + footers → UI / TTS        │
         └─────────────────────────────────────┘
```

### Context + verify (belt and suspenders)

Injecting truth **reduces** hallucination rate; verification **guarantees** nothing false ships. Neither replaces the other. Do not rely on context alone — Sumpty repro shows models invent catalogs even when told "flavor only" without the allowed list.

### Latency

Retries add LLM round-trips. Log `attempts` per mode. Optional UI wait indicator — not required for v1.

### Non-goals

- Replacing tool/FSM enforcement (bridge still authoritative for state changes).
- Verifying player-authored input.
- Canon `build/systems/` content changes (APP-061 etc.).

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-083 --task mechanical-truth-narration-gate
python tmp/backlog/claim_ticket.py release APP-083 --done
```
