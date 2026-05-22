# APP-089: Encounter awareness before combat (detect / avoid / ambush)

| Field | Value |
|-------|-------|
| **ID** | APP-089 |
| **Type** | feature |
| **Priority** | P1 |
| **Status** | open |
| **Domain spec** | [`app-exploration-delve-spec.md`](../app-exploration-delve-spec.md) |
| **Created** | 2026-05-22 |

**Implements:** encounter FSM + **APP-083 verify→retry→publish** for pre-combat exploration prose; **combat handoff** when `start_combat` commits.

## Summary

Entering a site with an **enemy** room feature must not immediately start combat. The player needs a chance to **notice**, **avoid**, **sneak past**, or **engage** — with **ambush** only when stealth vs Perception resolves in the monster’s favor (canon: [`build/systems/combat/encounter.md`](../../build/systems/combat/encounter.md) § Surprise).

## Problem (observed)

Session `app/logs/session-2026-05-22.jsonl` (09:35):

1. `enter_dungeon` → `32-C-UG-1` **Chapel descent** with `feature_type: enemy` (`grave-ghoul`) — correct engine data.
2. Same turn, LLM calls **`start_combat`** without a player attack or awareness beat.
3. Player never chose to fight; no Stealth / Perception contest.

Today there is **no app-layer encounter FSM** between “enemy feature present” and `start_combat`. Prompt says *“do not call start_combat manually unless needed”* but the model treats visible enemies as mandatory combat.

## Design (target behavior)

### Encounter states (room / feature scoped)

| State | Meaning | Player options (examples) |
|-------|---------|---------------------------|
| **Unnoticed** | Threat in room data; PC has not perceived it | Move carefully, Listen/Perception, Stealth |
| **Detected** | PC aware; monster may or may not be aware | Sneak past (Stealth vs Perception), withdraw, ready weapon, attack to open fight |
| **Engaged** | Fight agreed or unavoidable contact | `start_combat` allowed |
| **Ambush** | Monster won Stealth vs PC passive Perception before round 1 | `start_combat` with **surprised** flag on PC (canon surprise rules) |

Transitions use **tools + rolls** (`roll_d20`, `process_beat`, or dedicated encounter tools) — not narration alone.

### Hard rules

- **`enter_dungeon` / `site_enter` success** → populate room + features in context; **do not** call `start_combat`.
- **`start_combat`** only when: player declares hostile action, failed sneak, monster aggro script, or ambush outcome.
- **Enemy features** in `enter_dungeon` result are **threats available**, not “combat started”.

### Canon alignment

- Stealth vs Perception: `build/systems/skills/physical-skills.md` (Stealth), `encounter.md` (surprise).
- Extraction clock / noise may feed future aggro (soft hint only in v1).

### Narration gate (APP-083) — required, not optional

Encounter prose uses the same **TurnTruth → prompt → verify → retry → publish** pipeline as creation ([`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) § Mechanical-truth narration gate). **Strip-only** gates (APP-024) remain defense-in-depth **after** verify passes.

**Builder:** `build_encounter_turn_truth(status, encounter_state, tool_results, gate_flags) -> TurnTruth`

| Field | Source |
|-------|--------|
| `mode` | `"exploration"` |
| `encounter_phase` | FSM: `unnoticed` \| `detected` \| `engaged` \| `ambush` \| `in_combat` |
| `threats` | Room `features` where `feature_type == enemy` (monster id, count) |
| `tools_ok_this_turn` | Ordered list: `enter_dungeon`, `roll_d20`, `process_beat`, `start_combat`, … |
| `combat_active` | `bool(status.get("combat"))` |
| `entry_committed` | sticky `entry_committed_this_turn` (APP-024) |
| `last_roll` | Stealth / Perception contest outcome if any this turn |

**Inject:** `format_turn_truth_for_prompt(truth)` in exploration/encounter LLM messages **before** generation (same helper as creation; extend `narration_verify.py`).

**Verify rules (encounter-specific violations):**

| Violation | When fail |
|-----------|-----------|
| `premature_combat_start` | Prose asserts fight started / initiative / “combat begins” while `combat_active` false and `start_combat` not ok this turn |
| `unauthorized_start_combat_tool` | *(tool layer)* orchestrator blocks `start_combat` unless `encounter_phase in (engaged, ambush)` or player hostile + failed sneak recorded |
| `spatial_entry` | APP-024 rules via verify (interior fiction on surface without entry ok) — **retry**, not strip-first |
| `outcome_without_roll` | Claims Stealth/Perception **success or failure** without matching `roll_d20` / beat mechanical row this turn |
| `wrong_monster` | Names monster not in `threats` or canon catalog |
| `surprise_without_ambush` | PC “surprised” / flat-footed opener unless `encounter_phase == ambush` and contest resolved |

**Retry:** `_narrate_with_verification` (or exploration path calling it) — log `narration_verify_fail` with `mode: exploration`, `step: encounter_{phase}`; max `NARRATION_VERIFY_MAX_RETRIES`; exhaustion → code-owned fallback (threat present, choices listed, no combat).

**Publish:** Only after pass → `_compose_exploration_narration` (APP-024 strip + APP-077 footer when landed).

### Combat system integration

```text
enter_dungeon (ok) → encounter_phase detected (threats in truth)
       → player: sneak / perceive / fight
       → roll tools record outcome → truth updated
       → engaged OR ambush → start_combat (ok) → encounter_phase in_combat
       → route process_turn → _combat_turn
       → build_combat_turn_truth (APP-083 Phase 3 / APP-090)
       → verify combat phase prose separately
```

| Handoff point | Behavior |
|---------------|----------|
| **Before `start_combat`** | `mode=exploration`, encounter verify rules; **no** `COMBAT_TURN` footer |
| **`start_combat` ok same turn** | Truth records `tools_ok: start_combat`; verify may describe encounter opening; **surprise** flags passed to engine per canon |
| **After combat active** | Orchestrator **must** use `_combat_llm_loop` / `_combat_turn` only; encounter verify **not** applied to combat-phase narration (combat builder instead) |
| **`process_beat` → `combat_trigger`** | Unchanged beat path; on `start_combat_from_trigger` failure → APP-028 message; on success → combat truth + APP-090 phased narrate |

**Same-turn discipline:** If LLM calls `enter_dungeon` + `start_combat` without an authorized encounter transition, **tool block** on `start_combat` **and** verify fail on prose claiming combat started (Chubby repro).

## Acceptance criteria

### Spec / prompt

- [ ] Domain spec § **Encounter awareness** documents states, transitions, and tool boundaries.
- [ ] `system_prompt.py`: on site entry, **forbid** `start_combat` until Engaged/Ambush; instruct GM to describe threats and offer detect / sneak / fight choices.
- [ ] Game state context exposes **room features** (enemy id, disposition) without implying combat active.

### Code (minimum viable)

- [ ] Encounter FSM state on orchestrator (or bridge session row) persisted across turns in site mode.
- [ ] Orchestrator **blocks** `start_combat` when `encounter_phase` not in `(engaged, ambush)` (strict default).
- [ ] `build_encounter_turn_truth` + encounter verify rules in `narration_verify.py`.
- [ ] Exploration/encounter narration via **`_narrate_with_verification`** (verify → retry → publish).
- [ ] `format_turn_truth_for_prompt` includes threats, phase, tools_ok, “do not start combat in prose”.
- [ ] `enter_dungeon` tool result / exploration context includes **“Combat not started — threat present”** hint for the model.
- [ ] **Detect / sneak** path: Stealth or Perception via `roll_d20` / `process_beat` with outcome in `tool_results` before engage.
- [ ] **Ambush path**: contest → `start_combat` + surprise per engine; truth `encounter_phase=ambush`.
- [ ] **Combat handoff:** after `start_combat` ok, `process_turn` routes to `_combat_turn`; encounter verify skipped on combat paths.

### Verify / retry tests

- [ ] Unit: prose “combat begins / initiative” with `combat_active=false` → `premature_combat_start`.
- [ ] Unit: prose “you sneak past unnoticed” without roll ok → `outcome_without_roll`.
- [ ] Unit: benign threat tease with phase `detected` → pass.
- [ ] Mock LLM: bad prose retried; `narration_verify_pass` before `gm_narration` emit.
- [ ] Mock LLM: `enter_dungeon` + `start_combat` same turn → tool block + no combat in DB.

### Integration tests

- [ ] Successful Stealth vs passive Perception → no `start_combat`; verified bypass narration.
- [ ] Failed Stealth or explicit attack → `start_combat` OK → `_combat_turn` on next player line.
- [ ] Replay Chubby entry — ghoul visible, player chooses sneak or fight; no instant combat on entry alone.

## Expected files

- `app/gm/orchestrator.py` (FSM, tool gate, `_narrate_with_verification` wire)
- `app/gm/narration_verify.py` (`build_encounter_turn_truth`, encounter verify rules)
- `app/gm/system_prompt.py`
- `app/gm/tools.py` _(optional `encounter_*` tools)_
- `app/gm/logger.py` _(verify events with `step: encounter_*`)_
- `app/gm/bridge.py` _(if engine helpers needed)_
- `play/tomb_gm/services/` _(surprise flags, feature encounter — if engine work required)_
- `app/tests/test_encounter_awareness.py`
- `app/tests/test_narration_verify.py` _(encounter cases)_
- `tmp/app-exploration-delve-spec.md`
- `tmp/app-combat-play-spec.md` _(handoff §)_
- `tmp/app-llm-orchestrator-spec.md` _(exploration verify Phase 2 + encounter builder)_

## Spec sync (required on close)

1. Mark **Status** → `done` and set **Closed** date.
2. Changelog in exploration + combat specs.
3. Link canon `encounter.md` surprise section from app spec.

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| **APP-083** | **blocks** encounter narration quality — extend Phase 2 exploration verify with `build_encounter_turn_truth`; shared `_narrate_with_verification` |
| APP-024 | Spatial rules → verify failures (retry); sanitizer after pass |
| APP-029 | Monster auto-chain **after** combat legitimately starts |
| APP-027 | Valid monster ids at `start_combat` |
| APP-028 | Failed combat start narration |
| APP-090 | Phased combat narration + death beat **after** handoff from this ticket |

Soft hint:

| Ticket | Relationship |
|--------|--------------|
| APP-077 | Status footer during pre-combat exploration (after verified prose) |

## Notes

### Log reference

```
enter_dungeon ok → room chapel-stairs, feature enemy grave-ghoul
→ start_combat grave-ghoul:1 (same turn, player: "I enter the dungeon")
```

### Out of scope (follow-ups)

- Full room aggro radius / patrol AI.
- Multi-enemy coordination.
- UI map “threat” overlay (see APP-063).

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-089 --task encounter-awareness-before-combat
python tmp/backlog/claim_ticket.py release APP-089 --done
```
