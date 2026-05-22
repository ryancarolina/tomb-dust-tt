# QA Report: spec — round 1

**Task:** app-037-block-map-travel-during-creation
**backlog_ticket:** APP-037
**ticket_path:** [tmp/backlog/app-037-block-map-travel-during-creation.md](../../app-037-block-map-travel-during-creation.md)
**Round:** 1
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)
**domain_spec_creation:** not_needed (registry_gap false)

## Findings

### TICKET-001 — blocker

- **Location:** Ticket § Expected files vs `spec.md` § File map (implementation); `spec.md` R1 / R6; `tmp/app-pygame-ui-spec.md` § Tests
- **Issue:** Run spec requires edits to **`app/gm/orchestrator.py`** (`is_map_travel_blocked()`) and a new **`app/tests/test_ui_map_creation_gate.py`**, but neither path appears in the ticket **Expected files** list. Backlog hooks and `impl-check` use Expected files as the edit allow-list (same failure mode as APP-065 round 1).
- **Implementation gap:** Dev implementing per spec risks hook denial when adding the blocked helper on orchestrator or the focused pytest module.
- **Suggested fix:** Extend ticket Expected files to include `app/gm/orchestrator.py` and `app/tests/test_ui_map_creation_gate.py` (or consolidate tests into an existing module listed on the ticket — then update run spec file map + domain § Tests to match).

### SPEC-001 — major

- **Location:** `spec.md` § File map (`app/gm/orchestrator.py`) vs `tmp/app-pygame-ui-spec.md` § Implementation files (APP-037)
- **Issue:** Run spec places `is_map_travel_blocked()` on `Orchestrator` under `app/gm/orchestrator.py`; domain spec § Implementation files lists only `app/ui/app.py`, `sidebar.py`, and `map_view.py` (with a prose note that the signal “may live on Orchestrator… or equivalent helper invoked from `app.py`”).
- **Implementation gap:** PM artifacts disagree on whether orchestrator is in scope; Dev may implement a duplicate helper in `app.py` to stay inside ticket Expected files, diverging from R1 AC (“lives on `Orchestrator`”).
- **Suggested fix:** Pick one home (prefer orchestrator per R1); align run spec file map, domain § Implementation files, and ticket Expected files to the same path set.

### SPEC-002 — minor

- **Location:** `spec.md` R2 acceptance (“success or exception — same path as suggestions APP-065”); `app/ui/app.py` `_process_turn` L315–320
- **Issue:** Today `("status", …)` is queued only on the success path (L299–300); suggestions refresh unconditionally in `finally` via `_queue_turn_suggestions`. R2 requires map gate refresh on exception too but does not name the concrete hook (e.g. enrich + queue status in `finally` alongside suggestions).
- **Implementation gap:** Low risk of Dev only enriching the existing success-path status push, leaving blocked overlay stale after a turn error during creation.
- **Suggested fix:** Add one bullet under R2: on `_process_turn` exception, queue enriched status in `finally` (mirror `_queue_turn_suggestions`), not only after successful `process_turn`.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | Valid P1 feature; `in_progress`; domain spec field = `app-pygame-ui-spec.md` |
| registry_gap | **PASS** | false — pygame-ui spec owns map travel block; APP-008 remains engine gate |
| AC testability (intent) | **PASS** | R1–R7 + domain § Map travel during creation map all ticket AC rows |
| Code traces | **PASS** | Map click → `_submit` at `app/ui/app.py` 68–71; stub `handle_click` at `map_view.py` 94–95; APP-008 creation routing confirmed in research-brief |
| APP-008 mirror | **PASS** | Defense-in-depth layers documented; engine gate not replaced; typed travel explicitly non-goal |
| AGENTS.md / drift policy | **PASS** | Domain spec draft updated; changelog on close noted |
| Expected files ⊆ plan scope | **FAIL** | TICKET-001 — orchestrator + test module missing from ticket |
| PM artifact consistency | **WARN** | SPEC-001 — orchestrator placement split across run vs domain spec |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Travel disabled when `creation.active` or creation-scoped `awaiting` | R1 dual condition; domain § Travel-blocked signal | unit + integration tests in spec | **PASS** (intent) |
| Tooltip / label *"Finish Registry intake first"* | R4; domain § Player copy | MapView state + headless helper | **PASS** |
| Re-enable after finalize / live delver on surface | R6; domain § Re-enable | `test_creation_flow` regression | **PASS** |
| Map still displays hub cell; travel only blocked | R4–R5; domain § intro paragraph | draw + `update_position` AC | **PASS** |
| Compatible with APP-062 narrowed map column | R5, R7; domain § Layout (APP-062) | resize AC | **PASS** |
| Domain spec sync | R7; domain § Map travel during creation | review | **PASS** (draft; finalize on close) |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| Map click submits travel when address returned | `app/ui/app.py` 68–71 |
| `handle_click` stub — no address today | `app/ui/panels/map_view.py` 94–95 |
| `get_status()` has no `creation.active` | `orchestrator.py` 222–223 → `bridge.status()` only |
| Chips already read `creation.active` | `get_player_suggestions()` ~225–238 |
| APP-008 blocks exploration tools during creation | research-brief traces L2188–2341 |
| Status not refreshed on turn exception today | `app/ui/app.py` 315–318 early return; status only L299–300 |

## Summary

Spec content is strong: ticket AC coverage, APP-008 defense-in-depth, APP-065 desync guard parity, APP-062/063 forward compatibility, and domain spec § Map travel during creation are implementation-ready **after scope alignment**. **Block release to Dev plan until TICKET-001 is fixed** (Expected files must include orchestrator + test module, or spec must consolidate to ticket-listed paths only).

## Re-review focus

- Ticket Expected files updated to match final file map (minimum: orchestrator + `test_ui_map_creation_gate.py` if R1 stands).
- Domain § Implementation files aligned with run spec (no orchestrator-or-app ambiguity).
- Optional: R2 `finally`-path status enrichment spelled explicitly.
