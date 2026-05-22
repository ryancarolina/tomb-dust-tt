# QA Report: spec — round 1

**Task:** app-065-suggestion-chips-no-stale-tokens
**backlog_ticket:** APP-065
**ticket_path:** tmp/backlog/app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md
**Verdict:** FAIL
**Reviewer role:** QA (adversarial)
**domain_spec_creation:** not_needed (registry_gap false)

## Findings

### TICKET-001 — blocker

- **Location:** Ticket § Expected files vs `spec.md` § Affected paths / R2; `tmp/app-pygame-ui-spec.md` § File map (`ui/suggestions.py`); `spec.md` § Test plan (`app/tests/test_ui_suggestions.py`)
- **Issue:** PM spec and domain spec require a new module `app/ui/suggestions.py` and new pytest module `app/tests/test_ui_suggestions.py`, but neither path appears in the ticket **Expected files** list. Backlog hooks and plan QA gate use Expected files as the edit allow-list.
- **Implementation gap:** Dev implementing per spec risks hook denial or plan QA FAIL when adding the builder module or tests.
- **Suggested fix:** Extend ticket Expected files to include `app/ui/suggestions.py` and `app/tests/test_ui_suggestions.py` (or one existing test module if PM consolidates — then update spec test plan accordingly).

### SPEC-001 — blocker

- **Location:** `spec.md` R3 acceptance (“matches `EQUIPMENT_OBJECTION_RE` or documented alias”); domain spec § Curated player map (`aligned with is_equipment_confirm / is_equipment_objection`)
- **Issue:** Chip text `I need different gear` does **not** match `EQUIPMENT_OBJECTION_RE` in `app/gm/creation.py` (patterns: `wrong`, `change`, `go back`, etc. — no `gear` / `different`). Behavior still works today because `_handle_creation_response` at `EQUIPMENT_GOLD` uses `is_equipment_objection(player_input) or not is_equipment_confirm(player_input)` (`orchestrator.py` ~1004–1008) — the objection chip triggers **re-present via non-confirm**, not via objection regex.
- **Implementation gap:** Unit tests written to assert `is_equipment_objection("I need different gear")` will fail; Dev may wrongly extend objection regex instead of documenting the non-confirm path.
- **Suggested fix:** In `spec.md` + domain spec, state explicitly: objection chip must satisfy `not is_equipment_confirm(text)` (re-present kit); optional future alignment of `EQUIPMENT_OBJECTION_RE` is out of scope. Remove or rewrite R3 AC bullet that requires objection-regex match.

### SPEC-002 — major

- **Location:** `spec.md` R2 lookup order vs coarse `awaiting` table row `CHARACTER_CREATION` → “Delegate to creation.step map”; domain spec same
- **Issue:** Step 1 applies only when `creation.active`. Step 2 row says delegate to `creation.step` but does not define behavior when `creation.active` is false while engine `awaiting` is still `CHARACTER_CREATION` (resume/desync) or when `creation.step` is stale (e.g. `EQUIPMENT_GOLD` after `creation.active` cleared at finalize — `orchestrator.py` ~1196–1197 sets `active=False`, `step=WORLD_INTRO`).
- **Implementation gap:** A naive “delegate” that reads `creation.step` without gating on `creation.active` could re-show equipment chips after finalize; conversely, only checking `awaiting == CHARACTER_CREATION` without `creation.active` could return wrong defaults.
- **Suggested fix:** Replace the `CHARACTER_CREATION` table row with: “When `creation.active`, use step map (step 1); when not active, `[]`.” Add one sentence: post-finalize chips come from engine `awaiting` only (typically `PLAYER_ACTIONS` → `[]`), never from stale `creation.step`.

### SPEC-003 — major (residual risk)

- **Location:** `spec.md` R1 (only “successful `_process_turn`”); `app/ui/app.py` `_process_turn` except path ~319–322
- **Issue:** On turn exception, the UI does not queue suggestion refresh; prior equipment or startup chips can remain while error is shown.
- **Implementation gap:** Not in ticket repro, but contradicts “stale chips never persist” spirit if player hits a failed turn after equipment step.
- **Suggested fix:** Either add R1 bullet: on `_process_turn` failure, queue `("suggestions", get_player_suggestions())` or `[]` in `finally`; or document as known v1 limitation in Non-goals.

### SPEC-004 — minor

- **Location:** `tmp/app-pygame-ui-spec.md` § Tests (still “Future: headless panel” only)
- **Issue:** Run `spec.md` lists concrete pytest commands; domain spec Tests section was not updated with APP-065 test commands (file map references `suggestions.py` but Tests does not).
- **Suggested fix:** Add bullet under domain spec Tests: `python -m pytest app/tests/test_ui_suggestions.py -q` (+ regression pair from run spec).

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | Valid P1 bug; `in_progress`; domain spec field matches `app-pygame-ui-spec.md` |
| registry_gap | **PASS** | false — pygame-ui spec owns behavior; PM updated domain spec § Suggestion chips |
| AC testability (core) | **PASS** | Stale clear, no tokens, player phrases, spec sync — mappable after SPEC-001 fix |
| Code traces | **PASS** | Stale bug confirmed `app/ui/app.py` 315–317; regex 339–348; equipment handler 1004–1008; finalize footer 1221 |
| Domain spec sync (R6) | **PASS** (content) | Source-of-truth, maps, blocklist, always-clear documented in domain spec |
| Expected files ⊆ plan scope | **FAIL** | TICKET-001 |
| Equipment chip semantics | **FAIL** | SPEC-001 — test/AC vs real handler |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Empty extract → clear chips | R1; domain § Always refresh | pytest + manual Bumpy repro | **PASS** (intent) |
| Never show internal tokens | R2–R4; domain § Blocklist | `test_ui_suggestions` blocklist | **PASS** (intent) |
| Player-facing actions only | R2–R3 | map + no narration scrape | **PASS** |
| Equipment confirm examples | R3 | manual + unit map | **WARN** until SPEC-001 (objection chip semantics) |
| Startup load/new game | R3 SETUP row; `_init_orchestrator` 141–146 | manual | **PASS** |
| Click submits label not token | R5; v1 same string | manual | **PASS** |
| Domain spec documents rules | R6; domain § Suggestion chips | review | **PASS** |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| Stale chips: skip update when parse empty | `app/ui/app.py` 315–317 `if suggestions:` |
| Parser requires bracketed `Awaiting:` | `app/ui/app.py` 341 `\[.*?Awaiting:` |
| Post-finalize footer often unbracketed | `orchestrator.py` 1221 two-line footer |
| `get_status()` has no `creation.step` | `orchestrator.py` 102–103 → `bridge.status()` only |
| `creation.step` / `EQUIPMENT_GOLD` exist | `creation.py` 20–30, 77–78 |
| Confirm regex matches “ready” not token | `creation.py` 93–97; ticket repro “I am ready” |
| Objection chip phrase ≠ objection regex | `creation.py` 99–103; no match for “I need different gear” |
| Non-confirm re-presents equipment | `orchestrator.py` 1004–1008 |
| Domain spec updated by PM | `tmp/app-pygame-ui-spec.md` 38–88, changelog 129 |

## Summary

**FAIL** — fix **TICKET-001** (Expected files for `suggestions.py` + tests) and **SPEC-001** (equipment objection chip vs `is_equipment_confirm` / re-present path) before Dev plan. Address **SPEC-002** (`CHARACTER_CREATION` + inactive creation) and optionally **SPEC-003** (error-path stale) in the same PM revision. Domain spec content for source-of-truth is otherwise strong and aligned with research traces.

## Re-review focus

- Ticket Expected files include all new paths
- R3 / domain map: objection chip documented as non-confirm → re-present, not `EQUIPMENT_OBJECTION_RE` match
- Lookup order explicit when `creation.active` is false
- Optional: domain spec Tests § pytest commands; R1 error-path or Non-goals note
