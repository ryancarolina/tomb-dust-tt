# Spec — App Exploration & Delve Play

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** exploration path in orchestrator, map travel UX, site/delve tools

**Engine/canon (not a separate tmp spec):** site JSON fixes in `build/data/sites/` per [`build/docs/engine-integration.md`](../build/docs/engine-integration.md)

---

## Spec

### Surface play

- Player describes actions or clicks map → `world_travel(to_address)` or `process_beat`.
- `compass_exits` / `world_exits` for directions; friendly names should resolve to AV-GRID (engine).
- Wilderness: `wilderness_encounter` when travel flags demand it.

### Delve play

- Enter site via **`enter_dungeon(site_address)`** — not `set_phase(delve)` alone.
- In site mode: `site_move`, `search_site`, `interact_feature`, `move_room`, `exit_dungeon`.
- Phase/clock transitions via bridge extraction services.
- **Never** narrate entering a site without successful `enter_dungeon` / `site_enter` — enforced in code by § [Site-entry fiction gate (APP-024)](#site-entry-fiction-gate-app-024).
- On failed **`set_phase(delve)`**, orchestrator emits code-owned **`compass_exits` + `enter_dungeon`** hints — § [Failed set_phase(delve) hint (APP-022)](#failed-set_phasedelve-hint-app-022).

### Failed set_phase(delve) hint (APP-022)

**Ticket:** [APP-022](backlog/app-022-hint-enterdungeon-on-failed-setphasedelve.md)

**Problem:** LLM calls `set_phase(phase="delve")` from **`preparation`** (or other illegal states). Engine returns `ok: false` (e.g. `Cannot transition from preparation to delve`). Generic `TOOL FAILED` text does not name the correct tools.

**Policy:** Hints only — does **not** change phase FSM, block fiction (APP-024), or replace exploration footer (APP-077).

#### Trigger

| Condition | Required |
|-----------|----------|
| Tool | `set_phase` |
| Arg `phase` (normalized) | `"delve"` |
| Result | `ok: false` |

No hint for failed `set_phase` with other phases or successful calls.

#### Hint text

Code-owned helper `_delve_entry_tool_hint` in `orchestrator.py`:

> Do not use set_phase to enter a site. Call **compass_exits** to list below addresses, then **enter_dungeon(site_address)**. enter_dungeon advances preparation→ingress→delve automatically.

Optional suffix when `bridge.compass_exits()` returns non-empty `exits.below`: list AV-GRID addresses from current cell.

#### Injection (`_llm_loop`)

1. **Tool result:** add `"hint"` field to failed result dict (logged; visible to model on retry).
2. **System message:** append ` Hint: …` to existing `TOOL FAILED (set_phase): …` line.
3. **Player-visible:** on `all_failed and content` at depth 0 when this failure occurred — insert hint between `[Mechanics failed — …]` prefix and APP-024-sanitized assistant content (not inside sanitizer).

**Compose order with APP-024 / APP-077:** failure prefix → APP-022 hint (if applicable) → sanitized content → exploration footer (APP-077 when landed).

#### Tests (APP-022)

```bash
python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q
```

| Case | Setup | Pass |
|------|-------|------|
| Failed preparation→delve | Mock `set_phase(delve)` `ok: false` | Tool `hint` + system/player text mention `compass_exits` and `enter_dungeon` |
| Wrong phase arg | Failed `set_phase(ingress)` | No hint |
| Success | `set_phase(delve)` from `ingress` `ok: true` | No hint |
| APP-024 regression | Failed `set_phase(delve)` + entry `content` | Hint present; entry fiction still stripped when gate active |

### Site-entry fiction gate (APP-024)

**Problem:** Prompt rules alone; `_llm_loop` returned raw narration including the `all_failed and content` path (failure banner + success entry prose). Engine stayed `mode=surface` while player read interior fiction.

**Mechanical truth:** Site entry outcomes require `"ok": true` from **`enter_dungeon`** or **`site_enter`** in the **current turn's** tool chain ([`app-llm-orchestrator-spec.md`](app-llm-orchestrator-spec.md) § Mechanical truth).

#### When the gate runs

| Condition | Gate |
|-----------|------|
| Engine `party.mode == "surface"` at compose time **and** no successful entry tool this turn | **Active** — strip/replace site-entry fiction |
| Engine `party.mode in ("dungeon", "site")` at compose time | **Bypass** — in-site room/move/search narration allowed without re-calling entry tools |
| Successful `enter_dungeon` or `site_enter` (`ok: true`) anywhere in current turn's `_llm_loop` chain | **Bypass** — entry fiction allowed; engine mode typically already committed |

**Entry committed this turn:** `True` iff the depth-0 `_llm_loop` chain includes **at least one** successful (`ok: true`) **`enter_dungeon` or `site_enter`**. Implementation must use a **sticky per-turn flag** (set on first success, never cleared within the turn) **or** scan accumulated per-turn tool results — **not** final `_last_tool_results[tool_name]` alone, because that dict overwrites on each call with the same name (`orchestrator.py` L1978). Both entry tools are equivalent for authorization (`enter_dungeon` → `mode=dungeon`; `site_enter` → `mode=site`).

**Not in scope:** Gate does **not** apply on every turn globally — only blocks **premature site entry** while still on surface without a successful entry tool this turn.

#### Sanitizer contract

**Helper:** `sanitize_premature_site_entry_flavor(text, *, gate_active: bool) -> str`

When `gate_active`:

- Remove flavor that asserts site entry or interior presence while engine is still on surface — e.g. threshold crossing, stepping inside, torchlit corridors/vault interior, "you are now in the crypt/dungeon" without tool commit.
- Strip LLM status claims of in-dungeon/in-site mode (`Phase: delve`, interior `Location:`) when engine snapshot is still surface (hybrid marker + mode check; exact patterns in code).
- Preserve non-entry surface prose (travel banter, NPC talk at entrance) where separable.

When strip removes all flavor and gate was active, return this **code-owned refusal line** (`_SITE_ENTRY_REFUSAL_LINE` in `orchestrator.py`; must not imply success if tools failed this turn):

> The entrance holds you at the threshold — the Registry ledger still shows you on the surface. Crossing requires a successful **enter_dungeon** or **site_enter** call; the delving clock does not start until then.

#### Wiring (orchestrator)

1. At `_llm_loop` depth 0: reset `_last_tool_results` (existing) **and** set `entry_committed_this_turn = False`. After each tool call, if `fn_name in ("enter_dungeon", "site_enter")` and `result.get("ok")`, set `entry_committed_this_turn = True` (sticky for remainder of turn).
2. After `_llm_loop` in exploration `process_turn`, before `_emit_narration`: if gate active (`party.mode == "surface"` and not `entry_committed_this_turn`), run sanitizer on full narration string.
3. **`all_failed and content` early return:** compute gate from pre-turn surface mode + `entry_committed_this_turn`; run the same sanitizer on `content` **before** prepending `[Mechanics failed — …]` — player must not see entry success prose behind the banner.
4. Optional telemetry: log `premature_site_entry` drift when strip fires (does not replace sanitizer).

#### APP-077 coordination

[APP-077](backlog/app-077-code-owned-exploration-status-footer.md) adds code-owned exploration footer via `_compose_exploration_narration`. **Order when both land:**

1. `sanitize_premature_site_entry_flavor` (APP-024) — interior/entry fiction
2. `strip_llm_status_tags` + append `format_exploration_status` footer (APP-077) — bracket status lies

APP-024 does **not** depend on APP-077; APP-077 must not remove APP-024 strip. Shared compose entry point lives in `orchestrator.py` exploration path.

#### Tests (APP-024)

```bash
python -m pytest app/tests/test_exploration_site_entry_gate.py -q
```

### Encounter awareness before combat (APP-089) — draft

**Ticket:** [APP-089](backlog/app-089-encounter-awareness-before-combat.md)

Enemy room features are **threats**, not automatic combat. An **encounter FSM** sits between site entry and `start_combat`.

#### Encounter phases

| Phase | Engine / FSM | `start_combat` |
|-------|----------------|----------------|
| `unnoticed` | Threat in room features; PC may not know | **Blocked** |
| `detected` | PC aware; contest not resolved | **Blocked** |
| `engaged` | Hostile action or player chooses fight | **Allowed** |
| `ambush` | Monster won Stealth vs Perception (canon surprise) | **Allowed** (with surprise) |
| `in_combat` | `status.combat` active | N/A — route `_combat_turn` |

Canon: [`build/systems/combat/encounter.md`](../build/systems/combat/encounter.md) § Surprise.

#### Narration gate (verify → retry → publish)

Pre-combat encounter prose uses **APP-083** ([`app-llm-orchestrator-spec.md`](app-llm-orchestrator-spec.md)):

1. `build_encounter_turn_truth(status, encounter_phase, tool_results, gate_flags)`
2. `format_turn_truth_for_prompt(truth)` before LLM
3. `verify_narration(prose, truth)` — fail → retry; pass → publish
4. `_compose_exploration_narration` (APP-024 + APP-077) **after** verify pass only

**Key verify failures:** `premature_combat_start`, `outcome_without_roll`, spatial entry (APP-024 as verify rule), `wrong_monster`.

**Tool gate (sibling layer):** orchestrator blocks `start_combat` unless phase is `engaged` or `ambush`.

#### Combat handoff

When `start_combat` returns `ok: true` in a turn:

- Set encounter phase `in_combat`
- Next narration uses **combat** truth builder (APP-083 Phase 3 + [APP-090](backlog/app-090-combat-phased-narration-and-death-beat.md)), not encounter rules
- `process_turn` routes to `_combat_turn` while `awaiting == COMBAT_TURN`

`process_beat` → `combat_trigger` path remains; failures use APP-028 shape.

#### Tests (APP-089)

```bash
python -m pytest app/tests/test_encounter_awareness.py -q
python -m pytest app/tests/test_narration_verify.py -q  # encounter_* cases
```

| Case | Engine start | Mock / tools | Pass |
|------|--------------|--------------|------|
| No-tool entry hallucination | `mode=surface` | Content-only entry prose | No entry/interior markers in output; `mode` still `surface` |
| Failed entry + content leak | `mode=surface` | Failing `enter_dungeon` + entry `content` (`all_failed` path) | Failure banner OK; **no** entry success prose |
| Successful `enter_dungeon` | `mode=surface` → `dungeon` | `enter_dungeon` `ok: true` + entry prose | Entry prose retained |
| Success then failed `enter_dungeon` (same turn) | `mode=surface` → `dungeon` | `enter_dungeon` `ok: true`, then `enter_dungeon` `ok: false`, then entry prose | Entry prose **retained** — sticky flag; final dict slot must not drive gate |
| Successful `site_enter` | `mode=surface` → `site` | `site_enter` `ok: true` + entry prose | Entry prose retained (dual-tool) |
| In-dungeon room turn | `mode=dungeon` | Room description, no entry tools | Prose unchanged (gate bypass) |
| Helper unit | n/a | Marker fixtures | Entry segments stripped; benign surface prose kept |

### UI

- Map click sends travel intent; blocked during creation/combat as appropriate.
- **Map UX redesign** (design + implementation): [APP-063](backlog/app-063-map-ux-redesign-useful-navigation.md) — compass-backed exits, labels, working clicks, dungeon exits.

---

## Site edge types (canon)

Canonical types in `validate_content.py` (`SITE_EDGE_TYPES`): `door`, `archway`, `stairs`, `secret`, `hatch`, `collapse`.

**Canon decision (2026-05-20, APP-001 / APP-013):** Remap legacy `passage` and `gap` to **`archway`** in site JSON — do **not** add new `SITE_EDGE_TYPES`. Optional edge metadata (e.g. `hazard`) is preserved on the edge object.

---

## Problem (from logs)

- `enter_dungeon(site_id=…)` — wrong param (bridge accepts alias)
- `set_phase(delve)` rejected from `preparation`
- `process_beat` travel → `NO_DESTINATION` for vague names (“kings road”)
- GM narrated entering crypt without tool commit

---

## Task checklist

- [x] `world_travel`, `process_beat`, `enter_dungeon` tools exposed
- [x] Map click → travel string to orchestrator
- [x] `enter_dungeon` accepts `site_address` and `site_id` alias in bridge

**Open work:** [APP-025](backlog/app-025-registry-hub-loop-integration-test.md), [APP-063](backlog/app-063-map-ux-redesign-useful-navigation.md), [APP-077](backlog/app-077-code-owned-exploration-status-footer.md), [APP-089](backlog/app-089-encounter-awareness-before-combat.md) in [`tmp/backlog/README.md`](backlog/README.md).

- [x] **APP-022:** Failed `set_phase(delve)` hint — `_delve_entry_tool_hint`, R1–R3 injection in `_llm_loop`, tests in `app/tests/test_exploration_set_phase_delve_hint.py`
- [x] **APP-024:** Site-entry fiction gate — `sanitize_premature_site_entry_flavor`, `_llm_loop` + `all_failed` path, tests in `app/tests/test_exploration_site_entry_gate.py`

---

## Tests

- Travel `32-C` → `33-C` via tool; status address updates.
- Enter Breley Undercrypt from `32-C`; mode becomes site.
- Vague travel → `NO_DESTINATION` with helpful prompt, not fake arrival.
- **APP-024:** Surface + entry hallucination → stripped; successful `enter_dungeon` / `site_enter` → allowed; in-dungeon turns bypass gate (see § Site-entry fiction gate).

```bash
python -m pytest play/tomb_gm/tests/test_extraction_slice.py -q
python -m pytest app/tests/test_exploration_site_entry_gate.py -q
python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q
python build/tools/validate_content.py
python -m tomb_gm --workspace play/workspace check
```

---

## File map

| File | Role |
|------|------|
| `gm/orchestrator.py` | Exploration `_llm_loop` |
| `gm/tools.py` | `world_travel`, `enter_dungeon`, `site_*`, `process_beat` |
| `gm/system_prompt.py` | Delve entry rules |
| `ui/panels/map_view.py` | Click travel |
| `gm/bridge.py` | World/site/exploration methods |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | Spec created; merged delve-travel + site-edge validation content |
| 2026-05-20 | APP-001: remapped `passage`/`gap` → `archway` in boydon-undercroft + shadowfen-vaults; unblocks validate_content / tomb_gm check |
| 2026-05-20 | APP-013: closed decision ticket — canon is remap-to-archway (implemented in APP-001) |
| 2026-05-20 | APP-021: `enter_dungeon(site_address)` primary in tool schema; `site_id` alias; orchestrator maps before bridge |
| 2026-05-21 | APP-024 spec draft: § Site-entry fiction gate — surface-only compose sanitizer, dual entry tools, `all_failed+content` path, APP-077 compose order |
| 2026-05-21 | APP-024 PM r2: entry commit via sticky `entry_committed_this_turn` (not `_last_tool_results` overwrite); success-then-failed regression test |
| 2026-05-21 | APP-024 done: site-entry sanitizer + sticky `entry_committed_this_turn`; compose on `process_turn` and `all_failed+content`; refusal line pinned; 7 tests in `test_exploration_site_entry_gate.py` |
| 2026-05-22 | APP-089 draft: § Encounter awareness — FSM, verify→retry via `build_encounter_turn_truth`, combat handoff to APP-090 |
| 2026-05-22 | APP-022 draft: § Failed set_phase(delve) hint — dual injection (tool/system/player), `_delve_entry_tool_hint`, tests in `test_exploration_set_phase_delve_hint.py` |
| 2026-05-22 | APP-022 done: `_delve_entry_tool_hint`, `_should_delve_entry_hint`, `_build_delve_entry_hint`; R1–R3 in `_llm_loop`; sticky `_delve_entry_hint_this_turn`; 6 tests in `test_exploration_set_phase_delve_hint.py` |
