# Spec — App Exploration & Delve Play

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** exploration path in orchestrator, map travel UX, site/delve tools

**Engine/canon (not a separate tmp spec):** site JSON fixes in `build/data/sites/` per [`build/docs/engine-integration.md`](../build/docs/engine-integration.md)

---

## Spec

### Surface play

- Player describes actions or clicks map → `world_travel(to_address)` or `process_beat`.
- `compass_exits` / `world_exits` for directions; **friendly names resolve to AV-GRID via exit-scoped engine lookup** — § [Friendly surface travel resolution (APP-023)](#friendly-surface-travel-resolution-app-023).
- Wilderness: `wilderness_encounter` when travel flags demand it.

### Friendly surface travel resolution (APP-023)

**Ticket:** [APP-023](backlog/app-023-friendly-travel-name-to-av-grid.md)

**Problem:** Surface travel accepts **only canonical AV-GRID ids** today. `WorldService.can_travel` validates graph edges but does not parse prose. `bridge.world_travel` and `process_beat` travel lines pass destination strings straight through — vague names like “kings road” fail with `UNKNOWN_ADDRESS` / `NO_DESTINATION` even when a **legal exit** has a matching `displayName` (e.g. `32-C` → `33-C` “King's Road (east bend)”). **155** duplicate case-insensitive `displayName` values across surface cells forbid global name lookup.

**Policy:** Add engine **`resolve_surface_address`** (in `play/tomb_gm/services/world.py`) that maps a player/LLM query to a **single legal surface exit** from the party's current cell. Reuse scoring/normalization patterns from `site_resolve.py`. Wire **`bridge.world_travel`** and **`process_beat`** travel intent so both paths share the same resolver. **Site/dungeon entry by name stays on `enter_dungeon` + `resolve_site_address`** — not this resolver.

#### Candidate set (exit-scoped, surface-only)

| Rule | Detail |
|------|--------|
| **Scope** | Candidates = addresses in `WorldService.legal_exits(from_address)` **only** — never scan the full grid |
| **Surface filter** | Keep candidates whose cell has **empty** `layerStack` (surface layer). **Drop** UG/EP/BV/SK child exits from surface-travel resolution |
| **Passthrough** | If query (normalized) is already a canonical id **and** ∈ `legal_exits(from)`, return it unchanged (score 100) |
| **Current cell** | Never resolve to `from_address` unless query is an exact address match for the current cell (no “travel to Breley Keep” while already at `32-C`) |

**Rationale:** Global `displayName` lookup mis-resolves duplicate coast names. Exit scoping ties names to compass-adjacent choices. Layered addresses in `legal_exits` (e.g. `32-C-UG-1`) belong to **`enter_dungeon`** / `resolve_site_address`, not surface `world_travel`.

#### Matching (within candidates)

**Normalization (before scoring):**

1. Strip whitespace; lower-case query.
2. **Apostrophe folding:** remove ASCII `'` and `'` from query and candidate `displayName` before substring checks and before slug generation for scores 60–90. Keeps `kings road` aligned with `King's Road` without JSON edits.
3. Build `query_slug` via same `_slug` rules as `site_resolve.py` (on folded text).

For each surface candidate, load `displayName` and optional `tradeRoute` from `av-grid.json`. Score (highest wins):

| Score | Match |
|-------|--------|
| 100 | Exact AV-GRID id (case-insensitive) or slug-equal to address |
| 90 | Exact folded `displayName` (case-insensitive) or slug-equal to folded display name |
| 80 | Slug-equal to candidate's `tradeRoute` enum (e.g. `kings-road` ↔ query `kings road`) — **only when the same candidate also scores > 0 on rows 100–60** (compound gate) |
| 70 | Query slug substring of display-name slug (or reverse), both from folded text |
| 60 | Folded query substring of folded display name (case-insensitive) |

**Compound `tradeRoute` gate:** Score **80** for `tradeRoute` is a **boost**, not a standalone match. Apply it only when the candidate's display/address tiers (60–100) are already > 0. Prevents route-metadata-only cells (e.g. `32-D` Heartland mile post on `kings-road`) from beating a neighbor whose **display name** matches the query (e.g. `33-C` King's Road east bend). No JSON edit required.

`tradeRoute` on the **current** cell must **not** alone match a query when the party is already there (e.g. at `32-C` with `tradeRoute: kings-road`, query `kings road` must match exit **`33-C`**, not stay at `32-C`). Score **80** applies to **exit candidates'** `tradeRoute` fields only — not inherited from the current cell; and only when that exit's display name also matches per gate above.

**Scoring proof — King's Road fixture (live JSON, no grid change):**

Pass 1 surface candidates from `32-C` (excludes current cell + layered):

| Exit | displayName | tradeRoute | display tier | route tier (gated) | **Total** |
|------|-------------|------------|--------------|-------------------|-----------|
| `31-C` | Crystaline hills | — | 0 | — | 0 |
| `32-B` | Heartland fields | — | 0 | — | 0 |
| `32-D` | Heartland mile post | kings-road | 0 | suppressed | **0** |
| `33-C` | King's Road (east bend) | — | **70** (slug `kings-road` ⊆ `kings-road-east-bend`; also **60** name substring) | — | **70** |

| Step | Value |
|------|--------|
| Party at | `32-C` (`displayName`: Breley Keep; `tradeRoute`: kings-road — **not** in candidate set) |
| Query | `kings road` |
| Winner | **`33-C`** at best score **70** — T1/T6/T8 pass |

#### Layered fallback (USE_ENTER_DUNGEON)

When **pass 1** (surface candidates only) yields best score **0**, run **pass 2** on **non-surface** addresses still in `legal_exits(from_address)` (UG/EP/BV/SK child exits filtered out of pass 1). Use the same scoring table on each layered candidate's `displayName` / `tradeRoute` / address — **omit** the current-cell `tradeRoute` exclusion (layered cells are never `from_address`).

| Pass 2 result | Outcome |
|---------------|---------|
| Exactly one layered candidate at best score > 0 | **`USE_ENTER_DUNGEON`** — player must **`enter_dungeon(site_address)`**, not `world_travel` |
| Two+ layered candidates tie at best score > 0 | **`AMBIGUOUS_ADDRESS`** with layered `options` |
| Best layered score still 0 | **`UNKNOWN_ADDRESS`** with legal **surface** exit hint list |

**Proof — undercrypt from `32-C`:** pass 1 surface-only → 0; pass 2 candidate `32-C-UG-1` (`displayName`: Breley undercrypt); query `undercrypt` → slug `undercrypt` ⊆ `breley-undercrypt` → score **70** → **`USE_ENTER_DUNGEON`** (T5).

#### Outcomes

| Result | When | Shape |
|--------|------|--------|
| **Resolved** | Exactly one candidate at best score | `{ok: true, address: "<AV-GRID>", resolved_from: "<query>", displayName: "…"}` |
| **Ambiguous** | Two+ candidates tie at best score > 0 | `{ok: false, error: "AMBIGUOUS_ADDRESS", query, options: [{address, displayName}, …], message: …}` |
| **Unknown** | No candidate scores > 0 | `{ok: false, error: "UNKNOWN_ADDRESS", query, message: …}` — message lists **legal surface exits** with `displayName` when available |
| **Layered intent** | Pass 1 surface score 0; pass 2 layered fallback yields exactly one match (see § Layered fallback) | `{ok: false, error: "USE_ENTER_DUNGEON", query, message: …}` — direct player/LLM to **`enter_dungeon(site_address)`** or **`compass_exits`**, not `world_travel` |

After resolution, existing **`can_travel(from, resolved)`** gate unchanged. Resolution failure → **`ok: false`** — **never** travel on ambiguity or unknown.

#### Wiring

| Path | Behavior |
|------|----------|
| **`bridge.world_travel(to_address)`** | If `to_address` not an exact grid id in `legal_exits`, call `resolve_surface_address(content, to_address, from_address=party.address)`. On resolve success, replace `to_address` with resolved id before `can_travel`. On resolve failure, return resolver error dict (preserve `from` / `to` fields). |
| **`process_beat` travel** (`beat.py`) | After `_find_address` (AV-GRID regex) returns nothing and travel intent detected: call same `resolve_surface_address`. On success, `_apply_travel` to resolved id. On failure, map resolver errors to beat shape: **`UNKNOWN_ADDRESS` → `NO_DESTINATION`** (preserve `message` / hints); pass through **`AMBIGUOUS_ADDRESS`** and **`USE_ENTER_DUNGEON`** unchanged — **no** fake arrival. |
| **`enter_dungeon`** | Unchanged — `resolve_site_address` with child-first then global layered scope. |
| **Map click** | Unchanged — submits canonical ids. |
| **LLM tool schema** (`tools.py`) | On ticket close: describe `to_address` as AV-GRID id **or** friendly surface place name visible on current compass exits. |

Optional parity (not ticket AC): `play/tomb_gm/cli/cmd_world.py` `handle_travel` may call the same helper.

#### Tests (APP-023)

```bash
python -m pytest play/tomb_gm/tests/test_world.py -q
python -m pytest play/tomb_gm/tests/test_beat.py -q
python -m pytest play/tomb_gm/tests/test_site_resolve.py -q  # scoring regression
```

| Case | Setup | Pass |
|------|-------|------|
| King's Road | Party at `32-C`; query `kings road` | Resolves to `33-C`; `world_travel` + `process_beat` travel line succeed |
| Canonical passthrough | `world_travel(to_address="33-C")` from `32-C` | Unchanged success |
| Exit scope | Query matches global duplicate name **not** in `legal_exits` | `UNKNOWN_ADDRESS`, no travel |
| Ambiguity | Two legal surface exits tie on score | `AMBIGUOUS_ADDRESS` + `options`; no travel |
| UG child | From `32-C`, query `undercrypt` | **`USE_ENTER_DUNGEON`** (layered fallback → `32-C-UG-1`); **no** `world_travel` to UG id |
| Beat error map | Resolver returns `UNKNOWN_ADDRESS` on beat travel line | Beat mechanical `error: NO_DESTINATION` (same message) |
| Stay put | At `32-C`, query `breley` / `kings road` | Resolves to **`33-C`** for road name, not `32-C` |
| Invalid edge | Resolved id not in `legal_exits` | `INVALID_TRAVEL` (existing `can_travel`) |

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

[APP-077](backlog/app-077-code-owned-exploration-status-footer.md) adds code-owned exploration/combat footer via `_compose_exploration_narration`. **Order when both land:**

1. `sanitize_premature_site_entry_flavor` (APP-024) — interior/entry fiction
2. `strip_llm_status_tags` + `strip_llm_meta_narration` + append `format_exploration_status` footer (APP-077) — bracket status lies and meta leaks

APP-024 does **not** depend on APP-077; APP-077 must not remove APP-024 strip. Shared compose entry point lives in `orchestrator.py` exploration path. Full contract: § [Code-owned status footer (exploration & combat) (APP-077)](#code-owned-status-footer-exploration--combat-app-077). Orchestrator cross-link: [`app-llm-orchestrator-spec.md`](app-llm-orchestrator-spec.md) § Code-owned exploration/combat status footer (APP-077).

#### Tests (APP-024)

```bash
python -m pytest app/tests/test_exploration_site_entry_gate.py -q
```

### Registry hub loop integration test (APP-025)

**Ticket:** [APP-025](backlog/app-025-registry-hub-loop-integration-test.md)

**Problem:** The canonical Registry hub extraction loop (`preparation → ingress → delve → extract`) is wired through `GameBridge` but has **no** end-to-end test in `app/tests/`. Engine and exploration unit tests cover fragments only.

**Policy:** Add a **bridge-direct** integration test — no LLM mocks — that bootstraps an isolated session at **Breley Keep (`32-C`)** and walks the phase FSM via the same APIs the orchestrator dispatches.

#### Canonical loop (v1)

| Step | Bridge call | Party state (assert) |
|------|-------------|----------------------|
| Bootstrap | `campaign_new` + `session_start` | `address=32-C`, `mode=surface`, `phase=preparation` |
| Ingress + delve | `enter_dungeon(site_address)` — `32-C-UG-1` or `undercrypt` | `mode=dungeon`, `site_id=32-C-UG-1`, `phase=delve` |
| Exit site | `exit_dungeon()` | `mode=surface`, `site_id` cleared; **`phase` stays `delve`** |
| Extract | `set_phase("extract")` | `phase=extract` |

**Path constraints:**

- Use **`bridge.enter_dungeon`** → `ExplorationService.enter_site` (`mode=dungeon`) + `advance_phase_for_dungeon_entry` — **not** `site_enter` / `mode=site`.
- Do **not** call `set_phase("delve")` from `preparation` (illegal; see APP-022).
- Do **not** use `world_travel` to a layered address — APP-023 returns `USE_ENTER_DUNGEON`.

**Ingress observability:** `advance_phase_for_dungeon_entry` runs inside `enter_dungeon`; final status shows `phase=delve`. Assert **`events`** rows `type=phase.set` with `{from: preparation, to: ingress}` and `{from: ingress, to: delve}`.

**Out of scope v1:** registry stamp buy, Holt quest scenario (extend after APP-085), mock-LLM golden path (APP-051), surface travel prep beat (APP-023).

#### Tests (APP-025)

```bash
python -m pytest app/tests/test_registry_hub_loop.py -q
python -m pytest app/tests -q
```

| Case | Setup | Pass |
|------|-------|------|
| Full hub loop | Bootstrap `32-C` / `preparation` | S0→S3 sequence; final `phase=extract`, `mode=surface` |
| Friendly site name | `enter_dungeon("undercrypt")` from `32-C` | Resolves `32-C-UG-1`; `mode=dungeon`, `phase=delve` |
| Phase audit | After `enter_dungeon` | `events` contains preparation→ingress→delve `phase.set` rows |
| Exit vs extract | After entry, `exit_dungeon` | Surface mode; phase still `delve` until `set_phase("extract")` |

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

### Code-owned status footer (exploration & combat) (APP-077)

**Ticket:** [APP-077](backlog/app-077-code-owned-exploration-status-footer.md) · **Run spec:** [spec.md](backlog/runs/app-077-exploration-status-footer/spec.md)

**Problem:** `system_prompt.py` mandates LLM-authored `[Location: … | Phase: … | … | Awaiting: …]` every turn. Exploration/combat paths emit raw model prose — no strip, no code footer (unlike creation's `_compose_creation_narration`). Models invent wrong GP, phase, or awaiting values; meta banners (`**Campaign Memory Updated:**`) leak into player view.

**Policy:** **Strip LLM status + meta from prose; append one authoritative footer from `bridge.status()`.** Prompt instructs GM that the client appends state — do not emit bracket tags in flavor.

#### Footer contract

| Field | Source (`bridge.status()`) | Notes |
|-------|------------------------------|-------|
| `Location` | `party.display_address` if set, else `party.address` | `display_address` when `mode=dungeon` (site / room) |
| `Phase` | `party.phase` | e.g. `preparation`, `delve`, `ingress` |
| `HP` | Lowest-`slot` roster entry `hp` | `"current/max"` string from engine |
| `Fortune` | Same roster entry `fortune` | `"current/max"` string |
| `GP` | Same roster entry `gold` | Sheet `goldGp`; if `party.gold_in_transit > 0`, format `{gold} (+{transit} transit)` |
| `Turn` | `combat.turn_id` | **Combat only** — when `status.combat` truthy, inserted before `Awaiting` |
| `Awaiting` | Top-level `status.awaiting` | e.g. `PLAYER_ACTIONS`, `COMBAT_TURN` |

**Roster pin:** footer uses the roster character with the **lowest `slot`** value (typically slot 1). Multi-PC aggregation is out of scope.

**Exploration shape:**

```text
[Location: {location} | Phase: {phase} | HP: {hp} | Fortune: {fortune} | GP: {gp} | Awaiting: {awaiting}]
```

**Combat shape** (when `combat.active` / `status.combat` present):

```text
[Location: {location} | Phase: {phase} | HP: {hp} | Fortune: {fortune} | GP: {gp} | Turn: {turn_id} | Awaiting: {awaiting}]
```

Shape reference (creation handoff only): `_auto_finalize` explicit footer in `orchestrator.py`.

#### Helpers

| Helper | Module | Role |
|--------|--------|------|
| `format_exploration_status(status)` | `creation.py` | Build canonical bracket line from status dict |
| `strip_llm_status_tags(text)` | `creation.py` | APP-073 + **broad bracket strip** for exploration footer tokens (`Location`, `Phase`, `HP`, `Fortune`, `GP`, `Turn`, `Awaiting` inside `[…]`) |
| `strip_llm_meta_narration(text)` | `creation.py` | Remove `**Campaign Memory Updated:**` and `---` memory banner leaks |
| `_compose_exploration_narration(prose, *, gate_active)` | `orchestrator.py` | APP-024 → strip tags → strip meta → append footer from **fresh** `bridge.status()` |

#### Compose order (with APP-024 / APP-022)

1. APP-024 sanitizer (+ refusal line when gate active and body empty)
2. `strip_llm_status_tags`
3. `strip_llm_meta_narration`
4. Append `format_exploration_status(status)`

**Failure prefix paths:** `[Mechanics failed — …]` (APP-028 class) and APP-022 delve hint prepend **before** sanitized content; steps 1–4 still run on assistant content; footer always appended unless entire return is code-only failure with no prose (combat tool-fail early return).

**Empty body:** after strip, if only whitespace remains (and not APP-024 refusal-only), still append footer — never bracket-only player view.

**Idempotency:** strip F4 bracket shape before append so inner `_llm_loop` compose + outer `process_turn` compose yield exactly one footer.

#### Wiring

| Path | Compose before `_emit_narration` |
|------|----------------------------------|
| Exploration `process_turn` | Yes — post-`_llm_loop` (existing call site) |
| `_llm_loop` `all_failed and content` | Yes — helper must be complete (no second compose) |
| `_combat_turn` LLM narration (`_combat_llm_loop`, `_narrate_text`) | **Yes** — `gate_active=False` |
| Code-only (`[Mechanics failed]` only, death boilerplate) | No footer required |

**Prompt (`system_prompt.py`):** remove mandatory state-line steps; instruct client appends authoritative status — see orchestrator spec § APP-077.

**Optional telemetry:** `log_exploration_drift` when stripped prose contained bracket values disagreeing with engine (mirror APP-002 creation drift — does not block emit).

**APP-083 / APP-089:** verify pass → compose (024 + 077). Strip remains defense-in-depth after verify ships.

#### Tests (APP-077)

```bash
python -m pytest app/tests/test_exploration_status_footer.py -q
```

| Case | Setup | Pass |
|------|-------|------|
| Golden footer | Fixture status dicts (surface, delve, combat) | Exact bracket strings |
| GP transit | `gold` + `gold_in_transit` | `GP: N (+M transit)` |
| Strip + compose | LLM prose with wrong GP bracket | Engine GP only in footer region; one footer |
| Meta strip | `Campaign Memory Updated` banner | Not in composed output |
| Empty body | Strip-all prose | Footer still present |
| APP-024 + footer | Gate refusal turn | Refusal line + footer |
| Combat wire | Mock combat LLM return | `Turn:` segment; composed before emit |
| APP-024 regression | Existing site-entry tests | Unchanged gate behavior |

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
- ~~`process_beat` travel → `NO_DESTINATION` for vague names (“kings road”)~~ — **APP-023** exit-scoped resolution
- GM narrated entering crypt without tool commit

---

## Task checklist

- [x] `world_travel`, `process_beat`, `enter_dungeon` tools exposed
- [x] Map click → travel string to orchestrator
- [x] `enter_dungeon` accepts `site_address` and `site_id` alias in bridge

**Open work:** [APP-063](backlog/app-063-map-ux-redesign-useful-navigation.md), [APP-089](backlog/app-089-encounter-awareness-before-combat.md) in [`tmp/backlog/README.md`](backlog/README.md).

- [x] **APP-022:** Failed `set_phase(delve)` hint — `_delve_entry_tool_hint`, R1–R3 injection in `_llm_loop`, tests in `app/tests/test_exploration_set_phase_delve_hint.py`
- [x] **APP-023:** Friendly surface travel — `resolve_surface_address` exit-scoped two-pass resolver; `bridge.world_travel` + `process_beat` parity; tests in `play/tomb_gm/tests/test_world.py` + `test_beat.py`
- [x] **APP-024:** Site-entry fiction gate — `sanitize_premature_site_entry_flavor`, `_llm_loop` + `all_failed` path, tests in `app/tests/test_exploration_site_entry_gate.py`
- [x] **APP-077:** Code-owned exploration/combat status footer — `format_exploration_status`, `_compose_exploration_narration` strip+footer, combat wire, `test_exploration_status_footer.py`; APP-024 regression footer assert in `test_exploration_site_entry_gate.py`
- [x] **APP-025:** Registry hub loop integration test — bridge-direct `32-C` → `enter_dungeon` → `exit_dungeon` → `set_phase(extract)` in `app/tests/test_registry_hub_loop.py`

---

## Tests

- Travel `32-C` → `33-C` via tool (canonical id or friendly `kings road` per APP-023); status address updates.
- Enter Breley Undercrypt from `32-C`; `mode=dungeon` via `enter_dungeon` (APP-025 hub loop test).
- Unknown/ambiguous friendly travel → structured error with exit hints, **not** fake arrival (APP-023).
- **APP-024:** Surface + entry hallucination → stripped; successful `enter_dungeon` / `site_enter` → allowed; in-dungeon turns bypass gate (see § Site-entry fiction gate).

```bash
python -m pytest play/tomb_gm/tests/test_extraction_slice.py -q
python -m pytest app/tests/test_exploration_site_entry_gate.py -q
python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q
python -m pytest app/tests/test_exploration_status_footer.py -q  # APP-077
python -m pytest app/tests/test_registry_hub_loop.py -q  # APP-025
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
| `play/tomb_gm/services/world.py` | `legal_exits`, `can_travel`, **`resolve_surface_address`** (APP-023) |
| `play/tomb_gm/services/beat.py` | `process_beat` travel → shared surface resolver (APP-023) |
| `gm/creation.py` | `format_exploration_status`, `strip_llm_meta_narration`, extended `strip_llm_status_tags` (APP-077) |
| `app/tests/test_registry_hub_loop.py` | Bridge-direct Breley hub loop T1–T5 (APP-025) |

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
| 2026-05-22 | APP-023 PM draft: § Friendly surface travel resolution — exit-scoped surface-only `resolve_surface_address`, `world_travel` + `process_beat` parity, UG vs `enter_dungeon` split, ambiguity/unknown errors |
| 2026-05-22 | APP-023 PM r2: apostrophe folding + King's Road scoring proof; layered fallback algorithm; beat `UNKNOWN_ADDRESS`→`NO_DESTINATION` map; T5 pinned to `USE_ENTER_DUNGEON` |
| 2026-05-22 | APP-023 Dev plan r2: compound `tradeRoute` gate (display tier > 0 required); full `32-C` exit candidate table; T8 `GameBridge.world_travel` bridge test |
| 2026-05-22 | APP-023 done: `resolve_surface_address` in `world.py`; `bridge.world_travel` + `process_beat` shared resolver; exit-scoped scoring, layered `USE_ENTER_DUNGEON` fallback; 10 tests in `test_world.py`, 2 in `test_beat.py` |
| 2026-05-22 | APP-077 PM draft: § Code-owned status footer — field mapping, compose order with APP-024/022, combat `Turn:` segment, meta strip, test matrix; orchestrator spec cross-link |
| 2026-05-22 | APP-077 done: `format_exploration_status`, `strip_llm_meta_narration`, broadened `strip_llm_status_tags`; `_compose_exploration_narration` + `_emit_exploration_narration`; `log_exploration_drift`; `system_prompt.py` client-appends-state; 10 tests in `test_exploration_status_footer.py`; APP-024 in-dungeon bypass asserts code footer |
| 2026-05-22 | APP-025 PM draft: § Registry hub loop integration test — bridge-direct Breley loop, `test_registry_hub_loop.py`, exit_dungeon vs set_phase(extract) contract |
| 2026-05-22 | APP-025 done: bridge-direct hub loop integration test — T1–T5 in `test_registry_hub_loop.py`; `events` `phase.set` audit for preparation→ingress→delve; exit_dungeon vs set_phase(extract) contract pinned |
