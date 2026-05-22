# QA PASS: plan — round 2

**Task:** app-023-friendly-travel-av-grid  
**backlog_ticket:** APP-023  
**ticket_path:** [tmp/backlog/app-023-friendly-travel-name-to-av-grid.md](../../app-023-friendly-travel-name-to-av-grid.md)  
**Round:** 2 (re-review after `qa-plan-report-1.md`)  
**domain_spec:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md) § Friendly surface travel resolution (APP-023)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Round 1 findings — resolution

| ID | Severity | Status | Evidence in `plan.md` / domain spec |
|----|----------|--------|-------------------------------------|
| PLAN-001 | blocker | **Fixed** | § Flow C `_score_surface_candidate` compound gate (`display_score > 0` before route tier 80); full pass-1 candidate table for `32-C` + `kings road`; scoring policy paragraph; domain spec § Matching rows 80 + proof table; `spec.md` R2 + SPEC-001 proof |
| PLAN-002 | major | **Fixed** | §4.1 **T8** `test_world_travel_friendly_kings_road_bridge`; Requirements map R5; `spec.md` test plan T8 row; T8 asserts `GameBridge.world_travel`, `to == "33-C"`, `bridge.status()["party"]["address"] == "33-C"` |

## Independent verification (PLAN-001)

Ran scoring trace against live JSON (`WorldService.legal_exits("32-C")`, compound-gated tiers):

| Exit | displayName | tradeRoute | display tier | route (gated) | **Total** |
|------|-------------|------------|--------------|---------------|-----------|
| `33-C` | King's Road (east bend) | — | **70** | — | **70** |
| `32-D` | Heartland mile post | kings-road | 0 | suppressed | **0** |
| `31-C`, `32-B` | — | — | 0 | — | 0 |

**Winner:** `33-C` only — matches plan table, T1/T6/T8 expectations, and human Breley hub playtest.

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-exploration-delve-spec.md`
- [x] Ticket Expected files ⊆ plan § Files (`world.py`, `beat.py`, `bridge.py`, `test_world.py`, `test_beat.py`, optional `tools.py`; no unauthorized JSON / `cmd_world.py`)
- [x] Acceptance criteria testable — engine resolver R1–R4 + bridge/beat wiring R5–R7
- [x] Code traces match repo (`bridge.world_travel` L198 direct `can_travel` today; planned pre-resolve hook; `beat.py` travel branch; `world.legal_exits`)
- [x] AGENTS.md / canon compliance (no `av-grid.json` edit; d20 / AV-GRID unchanged; TurnTruth out of scope)
- [x] Tests/commands listed (`test_world.py`, `test_beat.py`, `test_site_resolve.py` regression; `impl-check APP-023` before `app/` edits)
- [x] Spec R1–R7 coverage in plan § Requirements → implementation map
- [x] Compound gate does not regress T4/T5 — ambiguity still tied display **90** @ `1-B`; undercrypt pass-2 display **70** @ `32-C-UG-1` (plan + domain proof unchanged)
- [x] Beat error map T7 — `UNKNOWN_ADDRESS` → `NO_DESTINATION`; resolver-only for `travel` intent, not `travel_hint`
- [x] Round 1 “verified” items still hold (file scope, beat wiring, T3 exit scope, passthrough R7, apostrophe fold + `_slug` import)

## T8 bridge test (PLAN-002)

| Check | Result |
|-------|--------|
| Named in plan §4.1 | **T8** `test_world_travel_friendly_kings_road_bridge` |
| File scope | `play/tomb_gm/tests/test_world.py` (Expected files) |
| Fixture pattern | `isolated_workspace` + `GameBridge.init()` + session bootstrap — mirrors `_bootstrap_session` / `test_campaign_session.py` `status()["party"]["address"]` |
| Import path | Root `conftest.py` adds `app/` to `sys.path` — `from gm.bridge import GameBridge` feasible from `play/tomb_gm/tests/` |
| Assertions | Pre-resolve hook + DB UPDATE covered (`ok`, `to`, party address) — adequate for R5 |

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `play/tomb_gm/services/world.py` | Yes |
| `play/tomb_gm/services/beat.py` | Yes |
| `app/gm/bridge.py` | Yes |
| `play/tomb_gm/tests/test_world.py` (T1, T3–T6, T8) | Yes |
| `play/tomb_gm/tests/test_beat.py` (T2, T7) | Yes |
| `app/gm/tools.py` (optional) | Yes |
| `tmp/app-exploration-delve-spec.md` | Close-time only (noted) |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-023 `in_progress` |
| Plan ⊆ Expected files | **PASS** | No scope creep |
| Spec R1–R7 in plan | **PASS** | Compound gate closes scoring defect |
| Code traces | **PASS** | Line refs spot-checked |
| Fixture / scoring proof | **PASS** | Full `32-C` surface table; independent script confirms `33-C` |
| Test plan vs qa-spec-pass | **PASS** | T8 closes R5 bridge gap |
| Beat error mapping | **PASS** | T7 + pseudocode |
| T4/T5 fixtures | **PASS** | Unchanged under compound gate |
| Round 1 re-review focus | **PASS** | PLAN-001 + PLAN-002 addressed |

## Notes (non-blocking — implementation QA)

1. **T8 bootstrap:** Plan references patterns but does not paste full test body — Dev should mirror `_bootstrap_session` (party at `32-C`) + `GameBridge` lifecycle from `app/tests/test_setup_new_game_lifecycle.py` / `test_campaign_session.py`.
2. **First `GameBridge` use in `test_world.py`:** No existing bridge tests in that module; verify `isolated_workspace` + `test_db`/`test_config` fixture interplay during impl.
3. **Scoring proof is plan-level only** — `resolve_surface_address` not in repo yet; impl must match compound gate exactly (especially `display_score > 0` guard before route tier).
4. **`impl-check APP-023`** required before `app/gm/bridge.py` edits — noted in plan open questions.

**Verdict:** PASS — ready for workstreams + implementation (Stage 4).
