# APP-090: Combat phased narration and death beat

| Field | Value |
|-------|-------|
| **ID** | APP-090 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-combat-play-spec.md`](../app-combat-play-spec.md) |
| **Created** | 2026-05-22 |

**Requires:** [APP-089](app-089-encounter-awareness-before-combat.md) combat handoff + [APP-083](app-083-creation-flavor-verification-gate.md) Phase 3 combat verify.

## Summary

Combat narration must be **readable beat-by-beat**, not one batched paragraph that skips the killing blow. When a PC dies, the player sees **what happened** (spell miss, crit, HP to 0) **before** the run-end / new-game message.

## Problem (observed)

Session `app/logs/session-2026-05-22.jsonl` (09:37–09:38):

1. **`_combat_auto_chain`** (APP-029) bundles PC `combat_action`, monster retaliations, and round advances into one mechanical list; `_combat_llm_loop_inner` asks the model to narrate **all of it at once**.
2. Player input *“I cast ember touch”* (round 3) → single `combat_action` mechanical chain includes miss + ghoul crit + `party_down` + `combat_finalize` + death.
3. Player-facing text jumps to **“Chubby is dead… new game”** without a clear account of the crit that ended the run (duplicate `gm_narration` lines in log).
4. Earlier turn (09:36): first *ember touch* had **no** `combat_action` but GM narrated 10 damage — fiction ahead of tools (related: APP-028 class).

Desired tone: dangerous, exciting — **one dramatic beat per phase**, not a combat log dumped into one reply.

## Design (target behavior)

### Phased narration pipeline

After each **player-initiated** `combat_action` while combat continues:

| Phase | Emit | Content |
|-------|------|---------|
| **1 — Player resolution** | Optional separate narration or clearly labeled section | Spell/attack roll, hit/miss, damage/heal, MP |
| **2 — Monster response** | If auto-chain ran | Each monster attack that actually resolved (hit, damage, conditions) |
| **3 — Round boundary** | If round advanced | Short “Round N” / whose turn next |
| **4 — Status** | Code-owned footer (APP-077) | HP, awaiting `COMBAT_TURN` |

Implementation options (PM pick one in plan):

- **A)** Multiple `_emit_narration` calls per turn (UI may need scroll/coalesce — see APP-060).
- **B)** Single message with **mandatory headings** (`## Your spell`, `## Grave Ghoul strikes`, `## Round 3`) enforced in compose.
- **C)** Split LLM calls: narrate PC result, then narrate auto-chain subset (higher latency, clearest).

### Death beat (required)

When mechanical chain includes PC **0 HP / defeat / `combat_finalize`**:

1. **Death narration pass** — code-owned template minimum, LLM flavor optional: last attack (nat roll, crit), final damage, falling/unconscious fiction.
2. **Pause** — do not call `setup_new_game` in the same composed string as the killing blow without phase 1.
3. **Run end** — second beat: corpse location, gear on body, **then** offer `new game` (existing `_handle_player_death` copy, but only after beat 1).

`_handle_player_death` today returns one block that merges death + new game (`orchestrator.py` ~718–721) and may **duplicate** emit (log lines 833–834).

### Non-combat combat turns

- Reject or strip exploration-loop narration of damage when `combat_action` was not called (09:36 first ember touch).
- During `Awaiting: COMBAT_TURN`, route only through `_combat_turn` / `_combat_llm_loop_inner`.

### Verify → retry per combat phase (APP-083 Phase 3)

Combat narration **must** use `build_combat_turn_truth` + `verify_narration` + retry — **not** one unverified batch over the full auto-chain mechanical list.

**Builder:** `build_combat_turn_truth(status, combat_state, mechanical_slice, phase_label) -> TurnTruth`

| `phase_label` | `mechanical_slice` | Allowed claims |
|---------------|-------------------|----------------|
| `player_resolve` | PC `combat_action` rows only | hit/miss, damage/heal, MP from tool ok rows |
| `monster_act` | `monster_attack` / auto-chain slice | attacks that actually fired this slice |
| `death` | finalize + killing blow row | HP 0, crit, last damage — **before** run-end copy |
| `round` | initiative / turn advance | round number, whose turn |

**Pipeline (each phase):**

1. Slice mechanical list for one phase.
2. Build truth from slice + `bridge.status()`.
3. LLM narrate **only that slice** with truth in prompt.
4. `verify_narration` → fail → retry with violations.
5. Pass → emit (multi-emit per APP-090 option A, or composed sections option B).
6. After `death` phase passes → emit run-end / `setup_new_game` block (code-owned, no verify on registry boilerplate).

**Integration with APP-089:** First combat-phase verify runs **after** encounter handoff (`start_combat` ok); truth includes `combat_active=true`, initiative order from tool result. Encounter verify **must not** run inside `_combat_llm_loop_inner`.

**Violations (combat):**

| Code | Example |
|------|---------|
| `damage_without_tool` | “10 damage” when no `combat_action` / `monster_attack` ok in slice |
| `hit_without_tool` | Hit fiction on `hit: false` row |
| `wrong_hp` | HP band contradicts status snapshot |
| `skipped_killing_blow` | Run-end text in same verified pass as spell cast without crit narration |

## Acceptance criteria

- [ ] Spec § **Phased combat narration** + § **Death beat** in `app-combat-play-spec.md`.
- [ ] Player turn with auto-chain: narration mentions PC outcome **before** monster kills blow that ends the fight (ordering test).
- [ ] Defeat turn: player sees killing attack described; **next** message or clearly separated section is run-end (not one sentence jump).
- [ ] No duplicate identical `gm_narration` on death path.
- [ ] `build_combat_turn_truth` + per-phase `verify_narration` wired in `_combat_llm_loop_inner` (not one verify over full chain).
- [ ] Each phase: `narration_verify_fail` / `pass` logged with `mode: combat`, `step: player_resolve` \| `monster_act` \| `death`.
- [ ] Death phase verify passes **before** `_handle_player_death` player message (or death message is code-owned from mechanical row).
- [ ] Optional: `log_combat_phase` JSONL events (`player_resolve`, `monster_act`, `death`, `run_end`) for QA.
- [ ] Tests: fixture mechanical list (miss + crit + finalize) → composed output order; mock death does not skip crit line.
- [ ] Tests: prose claiming damage without tool in slice → verify fail → retry.

## Expected files

- `app/gm/orchestrator.py` (`_combat_llm_loop_inner`, `_combat_auto_chain` consumers, `_handle_player_death`)
- `app/gm/narration_verify.py` (`build_combat_turn_truth`, combat verify rules)
- `app/gm/combat_fsm.py` _(phase labels / prompts)_
- `app/gm/system_prompt.py`
- `app/gm/logger.py` _(optional phase events)_
- `app/tests/test_combat_phased_narration.py`
- `tmp/app-combat-play-spec.md`
- `tmp/app-llm-orchestrator-spec.md`
- `tmp/app-logging-qa-spec.md` _(if new events)_

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Changelog in combat spec; cross-link APP-029 (auto-chain stays, narration splits around it).

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-029 | Auto-chain supplies mechanical phases to narrate — **blocks** splitting without chain data |
| APP-028 | No success fiction on failed tools — death beat must use real mechanical rows |
| APP-077 | Combat footer after each composed beat |
| **APP-089** | **blocks** — combat handoff; encounter verify ends when `start_combat` ok |
| **APP-083** | **blocks** Phase 3 — `build_combat_turn_truth`, shared retry helper |

Soft hint:

| Ticket | Relationship |
|--------|--------------|
| APP-060 | Multi-emit may need scroll behavior |

## Notes

### Chubby defeat chain (log)

`ember-touch` miss → ghoul `monster_attack` crit 10 → HP 0 → `combat_finalize` defeat → immediate new game prompt.

### Player expectation

> “I stated I wanted to cast a spell and the reply was I was dead and a new game had started.”

Fix is ordering and death beat, not removing lethality.

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-090 --task combat-phased-narration-and-death-beat
python tmp/backlog/claim_ticket.py release APP-090 --done
```
