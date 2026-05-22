# Spec: APP-027-validate-monster-id-combat

**Status:** draft  
**backlog_ticket:** APP-027  
**ticket_path:** [tmp/backlog/app-027-validate-monster-id-at-combat-start.md](../../app-027-validate-monster-id-at-combat-start.md)  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md)  
**registry_gap:** false  
**Domain specs touched:** `tmp/app-combat-play-spec.md`

## Problem

Unknown monster ids (e.g. `hollow-knight` in tool examples / beat regex) can reach `start_combat`. Engine `load_monster_json` already raises before DB write, and the bridge maps that to `{ok: false, error: …}`, but **app-layer gaps** remain: no `validate_tool_args` for `start_combat`, empty `monster_specs` not blocked, **no integration tests** with real content root, and canon drift trains the LLM on non-existent ids.

APP-028 fixed **narration** on all-failed turns; it did **not** add validation. Ticket AC: validate at `start_combat`, clear error, **no fiction on unknown id**.

**Evidence:** [research-brief.md](./research-brief.md) paths A–E; domain spec problem line `monster JSON not found: hollow-knight`.

## Goals

- **Fail before combat DB write** for unknown, malformed, or empty `monster_specs`.
- **Stable `{ok: false, error: …}`** from bridge; preserve `monster JSON not found: {id}` substring for APP-028 tests.
- **App tests** with real `hollow-knight:1` against repo content root.
- **Spec-owned** empty-list policy: non-empty `monster_specs` required.

## Non-goals

| Deferred | Note |
|----------|------|
| Mixed-tool turn fiction (failed `start_combat` + ok tool) | APP-028 depth+1; optional follow-up |
| Beat `MONSTER_ID_RE` content fix (`hollow-knight`, `rust-slime`) | Canon/content ticket; validation still fails at start |
| CLI `combat start` `{ok: false}` contract | Bridge is app canonical; CLI may keep raising |
| `ContentService.load_monster` blocker codes | Optional alignment; not AC |
| Full golden-path combat fixture | [APP-030](../../app-030-combat-integration-test.md) |

## Requirements (summary)

**Authoritative behavior:** domain spec § **Monster id validation at combat start (APP-027)**.

| Req | Summary |
|-----|---------|
| **R1** | `validate_monster_specs` in **engine only** (`combat.py`); app imports — no duplicate regex |
| **R2** | `bridge.start_combat` calls R1 before engine; failure `{ok: false, error}` only |
| **R3** | `validate_tool_args("start_combat")` in `_llm_loop` **before** `_execute_tool` (APP-080 pattern) |
| **R4** | Wire: exploration `_llm_loop`, `start_combat_from_trigger`, beat / `pending_start` paths |
| **R5** | No fiction: `status.combat` null + APP-028 failure narration |
| **R6** | Optional: fix `tools.py` examples to canon monster ids |

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| Validate monster specs at `start_combat` | R1–R2 |
| Clear error (no fiction on unknown id) | R5 + APP-028 §; V1, V6–V8 (V8 = real `_llm_loop` integration) |
| Spec sync on close | Domain spec § + changelog **done** entry |

## Test plan

```bash
python -m pytest app/tests/test_combat_monster_validation.py -q
python -m pytest app/tests/test_combat_failure_narration.py -k start_combat -q
python -m pytest play/tomb_gm/tests/test_validate_monster_specs.py -q
# optional CLI regression (exit code only — not V9):
python -m pytest play/tomb_gm/tests/test_simulation.py -k unknown_monster -q
```

See domain spec test table **V1–V9**.

## Affected paths

_Must match ticket **Expected files**._

- `play/tomb_gm/services/simulation/combat.py` — `validate_monster_specs` (R1)
- `app/gm/bridge.py` — R2 pre-check
- `app/gm/tool_args.py` — R3
- `app/gm/orchestrator.py` — wire unchanged; consumes bridge errors
- `app/gm/tools.py` — optional R6
- `app/tests/test_combat_monster_validation.py` — **new** (V1–V8; use `_dispatch_like_llm_loop` for V5)
- `play/tomb_gm/tests/test_validate_monster_specs.py` — **new** (V9 engine unit)
- `tmp/app-combat-play-spec.md` — § APP-027
- _(optional)_ `app/tests/test_tool_args.py` — `validate_tool_args("start_combat", …)` unit only

## Pointers

| Artifact | Path |
|----------|------|
| Research | [research-brief.md](./research-brief.md) |
| Domain spec § | [app-combat-play-spec.md § Monster id validation](../../../app-combat-play-spec.md) |
| Failure narration (sibling) | [app-combat-play-spec.md § APP-028](../../../app-combat-play-spec.md) |
| Engine spawn | `play/tomb_gm/services/simulation/combat.py` |
| Bridge | `app/gm/bridge.py` `start_combat`, `start_combat_from_trigger` |
| Related open | [APP-030](../../app-030-combat-integration-test.md) |

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- LLM or dev forces `start_combat` with bogus id → `[Mechanics failed — start_combat: monster JSON not found: …]`; no initiative/charge fiction; map/combat HUD unchanged.
- Beat-trigger encounter with invalid id in prose → `Combat could not begin.`; no ghoul-attack fiction while `combat: null`.
- Valid `grave-ghoul:1` start → combat as today.

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | PM draft: R1–R6, tests V1–V9, domain spec § APP-027 |
| 2026-05-22 | PM r2: QA spec round 1 — TICKET-001 Expected files; V5 `_dispatch_like_llm_loop`; R3/R4 `_llm_loop` wire; R1 engine-only; V8 integration; V9 engine test split from CLI |
