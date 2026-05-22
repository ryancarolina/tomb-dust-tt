# Spec: APP-025-registry-hub-loop-test

**Status:** approved  
**backlog_ticket:** APP-025  
**ticket_path:** [tmp/backlog/app-025-registry-hub-loop-integration-test.md](../../app-025-registry-hub-loop-integration-test.md)  
**domain_spec:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md)  
**registry_gap:** false  
**Domain specs touched:** `tmp/app-exploration-delve-spec.md`

## Problem

The extraction fantasy loop — **preparation** at the Registry hub → **ingress** → **delve** underground → **extract** with salvage — is documented in canon and wired through `GameBridge`, but **no automated test** in `app/tests/` walks the full phase FSM end-to-end.

Coverage today is **fragmented**:

| Suite | What it covers | Gap |
|-------|----------------|-----|
| `play/tomb_gm/tests/test_site_resolve.py` | `advance_phase_for_dungeon_entry`, illegal `preparation→delve` | Engine context only; no `GameBridge.enter_dungeon` |
| `app/tests/test_exploration_site_entry_gate.py` | APP-024 fiction gate via mock LLM | Single-tool mocks; stops at entry authorization |
| `app/tests/test_exploration_set_phase_delve_hint.py` | APP-022 failed `set_phase(delve)` hints | Does not assert successful hub loop |
| `app/tests/test_creation_flow.py` | Creation FSM through `preparation` | Stops before delve |
| `play/tomb_gm/tests/test_extraction_slice.py` | Economy vertical slice at `32-C` | Phase seeded `delve`; no FSM walk |

**Risk:** Regressions in `bridge.enter_dungeon`, `bridge.exit_dungeon`, or `bridge.set_phase` could break the canonical Breley hub loop without failing any app integration test.

## Goals

- Add a **deterministic, bridge-direct** integration test that exercises the Registry hub extraction loop at **Breley Keep (`32-C`)** without LLM mocks.
- Pin the **canonical app path**: `enter_dungeon` → `ExplorationService.enter_site` (`mode=dungeon`) → `advance_phase_for_dungeon_entry` — **not** CLI `site_enter` / `mode=site`.
- Assert that **`exit_dungeon` returns to surface but does not advance to `extract`**; **`set_phase("extract")`** is a separate step while phase is still **`delve`**.

## Non-goals

| Deferred | Ticket / note |
|----------|----------------|
| Mock-LLM golden path (creation → undercrypt → beat) | [APP-051](../../app-051-golden-path-fixture-with-mock-llm.md) — broader scope under logging/QA spec |
| Manual PyGame smoke | [APP-052](../../app-052-release-smoke-new-game-through-save-resume.md) |
| Holt quest accept → undercrypt → signet turn-in | Ticket note; extend after [APP-085](../../app-085-quest-system-key-npc-quests-ui.md) |
| Registry stamp buy / equip prep fiction | Engine CLI only (`registry_stamp_buy`); not on `GameBridge` |
| Surface travel beat (`world_travel` King's Road) | [APP-023](../../app-023-friendly-travel-av-grid.md) covered elsewhere; optional future test in same module |
| Character roster / creation bootstrap | Live probe succeeded without roster; do not block ticket on creation |
| Orchestrator tool-dispatch or narration gates | Bridge-only; APP-051 may reuse bootstrap helper later |

## Requirements

Full behavior and test contracts: domain spec § **Registry hub loop integration test (APP-025)**.

### R1: Bridge-direct test path (primary)

**Bootstrap** (isolated workspace via `conftest.py` — never `play/workspace`):

1. `GameBridge(workspace=isolated_workspace).init()`
2. `bridge.campaign_new("salt-road", "Salt Road")` — tolerate `already exists`
3. `bridge.session_start("salt-road")` → party at **`32-C`**, **`mode=surface`**, **`phase=preparation`**

**Loop sequence** (single test function or ordered sub-steps):

| Step | Call | Assert |
|------|------|--------|
| **S0 — preparation** | (bootstrap only) | `status()["party"]`: `address=="32-C"`, `mode=="surface"`, `phase=="preparation"` |
| **S1 — ingress + delve** | `bridge.enter_dungeon(site_address="32-C-UG-1")` **or** `"undercrypt"` | `ok: true`; party `phase=="delve"`, `mode=="dungeon"`, `site_id=="32-C-UG-1"` |
| **S2 — exit site** | `bridge.exit_dungeon()` | `ok: true`; party `mode=="surface"`, `site_id` null/absent; **`phase` still `"delve"`** |
| **S3 — extract** | `bridge.set_phase("extract")` | `ok: true`; party `phase=="extract"` |

**Site resolution:** Accept either canonical id **`32-C-UG-1`** or friendly slug **`undercrypt`** (both resolve from `32-C` per `resolve_site_address`).

**Do not use:** `bridge.site_enter`, `set_phase("delve")` from `preparation`, or `world_travel("32-C-UG-1")` (APP-023 `USE_ENTER_DUNGEON`).

### R2: Ingress sub-step observability

`advance_phase_for_dungeon_entry` runs **synchronously inside** `enter_dungeon`; final `status()` after S1 shows **`phase=delve`** only.

**Requirement:** Assert **`events`** rows with `type=="phase.set"` and payload transitions:

- `{from: "preparation", to: "ingress"}`
- `{from: "ingress", to: "delve"}`

Query via `bridge.ctx.conn` (same session as active save). Order among matching rows must preserve preparation → ingress → delve.

### R3: Extract vs exit_dungeon contract

Document and test explicitly:

- **`exit_dungeon`** → surface **`mode`**, clears **`site_id`**; **does not** set **`extract`**
- **`set_phase("extract")`** → legal only from **`delve`** per `PHASE_TRANSITIONS`

Include assertion that calling `set_phase("extract")` **before** `exit_dungeon` (while still `mode=dungeon`) also succeeds — phase FSM is independent of surface/dungeon mode. Optional sub-test or inline step; not required for ticket AC if full loop test covers post-exit path.

### R4: Test module and fixtures

| Item | Value |
|------|-------|
| **Module** | `app/tests/test_registry_hub_loop.py` |
| **Fixtures** | `bridge` from `conftest.py`; optional local `_ensure_salt_road_session(bridge)` helper (pattern from `test_combat_monster_validation.py`) |
| **LLM** | **None** — direct `GameBridge` calls only |
| **Workspace** | `isolated_workspace` / `tmp_path` — never mutate `play/workspace` |

### R5: No production code changes (expected)

Ticket is **test + spec sync** unless implementation discovers a bridge/FSM bug — then fix under same ticket with spec changelog note.

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| Test covers preparation → ingress → delve → extract loop | R1 S0–S3; **T1** |
| Spec sync on close | Domain spec § APP-025 + changelog; ticket Expected files |

## Test plan

```bash
# New module (APP-025)
python -m pytest app/tests/test_registry_hub_loop.py -q

# Regression — related exploration / phase FSM
python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_advance_phase_for_dungeon_entry -q
python -m pytest play/tomb_gm/tests/test_site_resolve.py::test_set_phase_rejects_preparation_to_delve -q
python -m pytest app/tests/test_exploration_set_phase_delve_hint.py -q

# Full app suite gate
python -m pytest app/tests -q
```

**Primary new tests** (`app/tests/test_registry_hub_loop.py`):

| ID | Test | Setup | Pass |
|----|------|-------|------|
| **T1** | `test_registry_hub_loop_preparation_through_extract` | Bootstrap at `32-C` / `preparation` | Full S0→S3; all `ok: true`; final `phase=="extract"`, `mode=="surface"` |
| **T2** | `test_enter_dungeon_resolves_undercrypt_from_breley` | Same bootstrap; `enter_dungeon("undercrypt")` | Resolves to `32-C-UG-1`; `mode=="dungeon"`, `phase=="delve"` |
| **T3** | `test_enter_dungeon_logs_ingress_phase_transitions` | After S1 in T1 | `events` contains `phase.set` preparation→ingress and ingress→delve |
| **T4** | `test_exit_dungeon_keeps_delve_phase` | After S1; before S3 | After `exit_dungeon`: `mode=="surface"`, `phase=="delve"` |
| **T5** | `test_set_phase_extract_from_delve` | Party at `delve` on surface (post S2) | `set_phase("extract")` → `ok: true`, `phase=="extract"` |

**T1** may subsume T4–T5 as inline assertions; separate test functions preferred for failure isolation.

## Affected paths

| File | Change |
|------|--------|
| `app/tests/test_registry_hub_loop.py` | **new** — T1–T5 |
| `tmp/app-exploration-delve-spec.md` | § Registry hub loop integration test (APP-025) |

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **New game → finish creation** → confirm hub at Breley (`32-C`), Registry badge shows preparation.
- **Enter undercrypt** via natural language or suggestion that triggers **`enter_dungeon`** — phase advances to delve; map/HUD reflect dungeon mode.
- **Leave site** (exit threshold / `exit_dungeon` tool path) — back on surface; phase still delve until GM/player declares extract.
- **Declare extract** — phase pill shows extract; save/resume preserves phase.
- **Regression:** Failed `set_phase(delve)` from surface still shows APP-022 hint; no entry fiction without tool (APP-024).

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — bridge-direct trace, dual site models, APP-051 overlap
- **Domain truth:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md) — § Registry hub loop integration test (APP-025)
- **GameBridge API:** [tmp/app-gamebridge-spec.md](../../../app-gamebridge-spec.md) — `enter_dungeon`, `exit_dungeon`, `set_phase`
- **Canon loop:** [build/systems/world/extraction.md](../../../build/systems/world/extraction.md) — five phases
- **Related:** APP-021 (`site_address`), APP-024 (entry gate), APP-051 (mock-LLM golden path)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Initial PM draft — bridge-direct hub loop R1–R5, T1–T5, domain spec § |
