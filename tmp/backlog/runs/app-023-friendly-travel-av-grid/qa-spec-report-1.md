# QA Report: spec — round 1

**Task:** app-023-friendly-travel-av-grid
**backlog_ticket:** APP-023
**ticket_path:** [tmp/backlog/app-023-friendly-travel-name-to-av-grid.md](../../app-023-friendly-travel-name-to-av-grid.md)
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)
**domain_spec_creation:** not_needed (registry_gap false)

## Findings

### SPEC-001 — blocker

- **Location:** `spec.md` T1/T6 + domain spec § Matching (scores 60–80) + § Tests King's Road row; `build/data/av-grid/av-grid.json` `33-C` record; `play/tomb_gm/services/site_resolve.py` `_match_score` L21–33
- **Issue:** Primary fixture query **`kings road`** (no apostrophe) **does not score > 0** against exit **`33-C`** (`displayName`: `"King's Road (east bend)"`) using the documented scoring rules. Verified with `site_resolve._match_score` logic: slug `"kings-road"` is not a substring of slug `"king-s-road-east-bend"` (score 70 = 0); substring `"kings road"` is not in `"king's road (east bend)"` due to apostrophe (score 60 = 0). Exit **`33-C` has no `tradeRoute` field** in `av-grid.json` (L25532–25557), so spec score **80** cannot apply to that candidate. Current cell **`32-C`** has `tradeRoute: kings-road` (L24640) but is **not** in the exit candidate set — correctly excluded — so its route tag cannot rescue T1.
- **Implementation gap:** Dev implementing per spec will ship resolver that still returns `UNKNOWN_ADDRESS` for the ticket's headline repro; T1/T6 and domain § Tests King's Road row will fail.
- **Suggested fix:** Pick one durable approach and pin in both `spec.md` and domain § Matching: (a) apostrophe-insensitive / token-normalized substring or slug match so `kings road` ↔ `King's Road`; (b) change canonical fixture query to `king's road` everywhere (research, T1, human playtest); (c) add `tradeRoute: kings-road` to road exit cells like `33-C` in JSON **and** document exit-level route scoring; or (d) explicit cross-exit route hint from current cell's `tradeRoute` to adjacent road-named exits. Re-run scoring proof against live JSON before PM resubmit.

### TICKET-001 — blocker

- **Location:** Ticket § Expected files; `spec.md` § Requirement summary R6, § Affected paths (`play/tomb_gm/services/beat.py`, `test_world.py`, `test_beat.py`); domain spec § Wiring `process_beat` row
- **Issue:** Ticket **Expected files** lists only `world.py`, optional `av-grid.json`, and `bridge.py`. Run spec **R6** requires **`beat.py`** parity (same resolver when `_find_address` misses) and names **`test_world.py` / `test_beat.py`**. Research brief L110 flags the same gap. Spec notes Dev should add paths later — **ticket not updated yet**.
- **Implementation gap:** Backlog hooks and plan QA gate use Expected files as edit allow-list; Dev adding beat wiring or tests risks hook denial or plan FAIL (same pattern as APP-065 TICKET-001).
- **Suggested fix:** Extend ticket Expected files to include `play/tomb_gm/services/beat.py`, `play/tomb_gm/tests/test_world.py`, `play/tomb_gm/tests/test_beat.py` (and optional `app/gm/tools.py` if tool description lands same PR).

### SPEC-002 — blocker

- **Location:** Domain spec § Friendly surface travel resolution § Matching (L38–52) vs § Outcomes `USE_ENTER_DUNGEON` row (L61); `spec.md` T5; `research-brief.md` § Risks L109
- **Issue:** Surface-only candidate filter is specified, and outcome **`USE_ENTER_DUNGEON`** is defined, but **no algorithm** describes the **secondary pass** on layered exits in `legal_exits` (e.g. `32-C-UG-1` "Breley undercrypt" for query `undercrypt`). Matching section scores **surface candidates only**; layered addresses are dropped before scoring with no follow-up step documented.
- **Implementation gap:** Dev may return `UNKNOWN_ADDRESS` for all UG-intent queries (T5 allows that) or call `resolve_site_address` (violates enter_dungeon split) or invent ad hoc layered scoring — three incompatible behaviors from the same spec.
- **Suggested fix:** Add explicit **Layered fallback** subsection: when best surface score = 0, score **non-surface** addresses still in `legal_exits(from)` with the same table (minus tradeRoute-on-current rule); if best layered score > 0 → `USE_ENTER_DUNGEON`; else `UNKNOWN_ADDRESS`. Pin T5 to **require** `USE_ENTER_DUNGEON` for `undercrypt` from `32-C` (not "or unknown").

### SPEC-003 — major

- **Location:** Domain spec § Wiring `process_beat` row (L70); § Outcomes `UNKNOWN_ADDRESS` (L60); `play/tomb_gm/services/beat.py` L456–463 (`error: NO_DESTINATION`)
- **Issue:** Resolver outcomes use **`UNKNOWN_ADDRESS`** / **`AMBIGUOUS_ADDRESS`**. Beat wiring lists **`NO_DESTINATION | AMBIGUOUS_ADDRESS | USE_ENTER_DUNGEON`** but does not map resolver **`UNKNOWN_ADDRESS`** → beat's existing **`NO_DESTINATION`** code (beat L460 today).
- **Implementation gap:** Tests asserting `error == "UNKNOWN_ADDRESS"` on beat path vs `NO_DESTINATION` on resolver unit tests will diverge; LLM/tool consumers may see inconsistent error enums across `world_travel` and `process_beat`.
- **Suggested fix:** Document in § Wiring: beat maps resolver `UNKNOWN_ADDRESS` → `NO_DESTINATION` (preserve message/hints); pass through `AMBIGUOUS_ADDRESS` and `USE_ENTER_DUNGEON` unchanged. Add one beat test row for error code mapping.

### SPEC-004 — minor

- **Location:** `research-brief.md` L123; `build/tools/av_grid.py` L130–135 (`resolve_surface`); `spec.md` R1 API name `resolve_surface_address`
- **Issue:** Research flags naming collision with grid tool **`resolve_surface`** (parses surface root from id). Run spec does not note the distinction for Dev.
- **Suggested fix:** One line in spec § Requirements or Non-goals: engine API is **`resolve_surface_address`** — not `build/tools/av_grid.py:resolve_surface`.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | Valid P1 feature; `in_progress`; domain spec field matches |
| registry_gap | **PASS** | false — `app-exploration-delve-spec.md` owns behavior; PM added § APP-023 + changelog |
| AC testability (core) | **FAIL** | SPEC-001 — headline fixture `kings road` untestable with documented scores + live JSON |
| Code traces | **PASS** | `bridge.world_travel` L184–208 passes through to `can_travel`; beat travel L431–464 regex-only dest; `site_resolve` pattern confirmed |
| Domain spec sync | **PASS** (structure) | § APP-023, file map, problem strikethrough, tests bullet — content gaps above |
| Expected files ⊆ spec scope | **FAIL** | TICKET-001 |
| Research risks addressed | **PARTIAL** | Exit scope, ambiguity, beat parity flagged — layered algorithm + scoring proof gaps remain |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Map friendly place names to AV-GRID for surface travel via engine `world.py` | R1–R4; T1–T6 | King's Road fixture | **FAIL** until SPEC-001 |
| Spec sync on close | Domain § APP-023 + changelog | Drift gate Stage 6 | **PASS** (intent) |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| `world_travel` no name resolution today | `app/gm/bridge.py` L198 `world.can_travel(from_addr, to_address)` direct |
| Beat travel regex-only dest | `beat.py` L433 `_find_address`; L456–463 `NO_DESTINATION` |
| `legal_exits` includes UG children from `32-C` | `world.py` L57–58 childAddresses; research L76 |
| `33-C` displayName King's Road (east bend), no tradeRoute | `av-grid.json` L25543–25556 |
| `32-C` tradeRoute kings-road, displayName Breley Keep | `av-grid.json` L24631–24640 |
| `site_resolve._match_score` template | `site_resolve.py` L21–33 — no tradeRoute tier |
| `resolve_surface` tool name exists | `av_grid.py` L130 — different purpose |
| Domain spec PM draft landed | `app-exploration-delve-spec.md` L19–93, changelog L344 |

## Summary

**FAIL** — fix **SPEC-001** (prove `kings road` → `33-C` against live JSON with pinned normalization or data rule), **TICKET-001** (Expected files for `beat.py` + tests), and **SPEC-002** (layered `USE_ENTER_DUNGEON` algorithm + single T5 outcome) before Dev plan. Address **SPEC-003** (beat error mapping) in the same PM revision. Registry/drift ownership is correct; research risks are mostly reflected but the primary acceptance fixture is **mathematically inconsistent** with the spec scoring table as written.

## Re-review focus

- Scoring proof for `kings road` / `32-C` → `33-C` with cited rule tier
- Ticket Expected files include all R6 + test paths
- Layered fallback algorithm + T5 pinned to `USE_ENTER_DUNGEON`
- Beat `NO_DESTINATION` vs resolver `UNKNOWN_ADDRESS` mapping
- Optional: `resolve_surface_address` vs `av_grid.resolve_surface` note
