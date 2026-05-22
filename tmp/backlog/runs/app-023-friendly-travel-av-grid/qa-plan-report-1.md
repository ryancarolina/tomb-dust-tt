# QA Report: plan — round 1

**Task:** app-023-friendly-travel-av-grid  
**backlog_ticket:** APP-023  
**ticket_path:** [tmp/backlog/app-023-friendly-travel-name-to-av-grid.md](../../app-023-friendly-travel-name-to-av-grid.md)  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)

## Findings

### PLAN-001 — blocker

- **Location:** `plan.md` § Flow C pass 1 / `_score_surface_candidate` (scores 80 tradeRoute, 70 slug substring); §4.1 **T1** / **T6**; domain spec § Scoring proof table (King's Road fixture); `build/data/av-grid/av-grid.json` `32-D` + `33-C`
- **Issue:** Primary fixture **`kings road` @ `32-C`** does **not** resolve to **`33-C`** under the plan's documented scoring table. Independent trace against live JSON (`WorldService.legal_exits("32-C")` + plan score tiers):

  | Exit | displayName | tradeRoute | Score for `kings road` |
  |------|-------------|------------|------------------------|
  | `32-D` | Heartland mile post | `kings-road` | **80** (tradeRoute slug match) |
  | `33-C` | King's Road (east bend) | *(none)* | **70** (display slug substring after apostrophe fold) |

  Plan picks **single best score** (no tie at 80 vs 70). Resolver returns **`32-D`**, not **`33-C`**. T1 asserts `address == "33-C"`; T6 still passes (≠ `32-C`) but lands the **wrong** road cell. Domain § Scoring proof and qa-spec-pass round 2 proof enumerate only `33-C` — they omit competing surface exit `32-D`, which is in `legal_exits` today.
- **Implementation gap:** Dev following plan + domain spec ships resolver that fails T1 or silently mis-routes “King's Road” prose to Heartland mile post — the headline Breley hub playtest in spec § Human playtest hints.
- **Suggested fix:** Revise scoring policy in **plan + domain spec** (pick one, pin proof across **all** surface exit candidates):

  1. **Compound tradeRoute gate:** score **80** only when the same candidate also has displayName tier **> 0** (tradeRoute as boost, not standalone match); or  
  2. **Prefer display match over route-only:** when best display tier (90/70/60) > 0 on any candidate, ignore tradeRoute-only winners; or  
  3. **Re-rank tiers:** lower tradeRoute-only below slug substring (changes R2 table — coordinate with PM); or  
  4. **Data fix ticket:** remove/rename `32-D.tradeRoute` (requires JSON + validate — currently plan non-goal).

  Re-run full exit-candidate scoring script for `32-C` + `kings road` before resubmit; update T1 expected address only after policy is chosen.

### PLAN-002 — major

- **Location:** `plan.md` §4.1 / § Requirements map **R5**; `spec.md` Test plan T1 (“via resolver / `world_travel`”); domain spec § Tests King's Road row
- **Issue:** No automated test in plan for **`GameBridge.world_travel(to_address="kings road")`** (or thin wrapper). R5 coverage is resolver unit test + `can_travel` chain simulation + Stage 7 human PyGame. Bridge hook (~15 lines, pre-resolve gate, error shape merge with `from`/`to`) is untested in `app/tests/` — and Expected files do not include `app/tests/`.
- **Implementation gap:** Regression in bridge membership check (`legal_exits` set vs resolver passthrough), error dict field merge, or failure to replace `to_address` before UPDATE would not fail CI; only human playtest would catch.
- **Suggested fix:** Add one engine-level test via existing `test_world.py` session fixture **or** expand ticket Expected files with `app/tests/test_exploration_friendly_travel.py` (or similar) calling `GameBridge.world_travel` with mocked DB — at minimum assert `ok`, `to == "33-C"`, party row updated after friendly query once PLAN-001 is fixed.

## Verified (no findings)

- [x] Plan files ⊆ ticket Expected files (`world.py`, `beat.py`, `bridge.py`, `test_world.py`, `test_beat.py`, optional `tools.py`; no unauthorized JSON/cmd_world edits)
- [x] Spec R1–R7 mapped in plan § Requirements → implementation map
- [x] Code traces match repo (`bridge.world_travel` L198 direct `can_travel`; `beat.py` L431–464 regex-only + `NO_DESTINATION`; `world.legal_exits` L49–61 includes neighbors + UG children)
- [x] Beat wiring structure correct — resolver only for `travel_intent == "travel"`, not `travel_hint`; `UNKNOWN_ADDRESS` → `NO_DESTINATION` map; `continue` on fail before `_apply_travel`
- [x] Layered fallback T5 fixture verified — `undercrypt` @ `32-C` → single pass-2 winner `32-C-UG-1` score **70** → `USE_ENTER_DUNGEON`
- [x] T4 ambiguity fixture verified — `1-B` + `silversea cove` → tied **90** on `{1-A, 2-B}` → `AMBIGUOUS_ADDRESS`
- [x] T3 exit scope verified — `silversea cove` from `32-C` has no matching legal exit → `UNKNOWN_ADDRESS`
- [x] T7 beat error map specified — resolver `UNKNOWN_ADDRESS` → beat `NO_DESTINATION`
- [x] Apostrophe fold + `_slug` import from `site_resolve` — no import cycle
- [x] `impl-check APP-023` noted before `app/gm/bridge.py` edits
- [x] Regression commands include `test_site_resolve.py`
- [x] TurnTruth / LLM paths correctly out of scope
- [x] Default session hub `32-C` supports T2 beat seed without extra setup (`session.py` `DEFAULT_HUB_ADDRESS`)

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket Expected files ⊆ plan | **PASS** | |
| Spec R1–R7 in plan | **PASS** | Algorithm present; primary fixture wrong |
| Code traces | **PASS** | Line refs spot-checked |
| Fixture / scoring proof | **FAIL** | PLAN-001 — `32-D` beats `33-C` |
| Test plan vs qa-spec-pass | **FAIL** | T1 untestable as written; R5 bridge gap PLAN-002 |
| Beat error mapping | **PASS** | T7 + pseudocode |
| T4/T5 fixtures | **PASS** | Live JSON verified |

## Acceptance criteria mapping

| Ticket AC | Plan coverage | QA |
|-----------|---------------|-----|
| Map friendly place names to AV-GRID via engine `world.py` | R1–R4 + T1–T7 | **FAIL** until PLAN-001 |
| Spec sync on close | §7 domain changelog | **PASS** (intent) |

## Summary

Plan structure, file scope, beat parity wiring, and layered/ambiguity fixtures are **implementation-ready**, but the plan **fails** round 1 because the King's Road scoring proof is **incomplete**: exit **`32-D`** (`tradeRoute: kings-road`) outscores **`33-C`** under the documented tier table, so **T1/T6 and human Breley hub playtest target the wrong cell**. Fix scoring policy (plan § Flow C + domain § Matching proof) and re-verify all `32-C` surface candidates before Dev impl. Address **PLAN-002** (direct `world_travel` test) in the same revision.

## Re-review focus

- Full candidate scoring table for `kings road` @ `32-C` (all surface exits, not just `33-C`).
- T1 expected address matches revised policy.
- Optional: named bridge/`world_travel` automated test for R5.
