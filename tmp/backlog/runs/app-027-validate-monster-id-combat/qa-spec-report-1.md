# QA Report: spec — round 1

**Task:** app-027-validate-monster-id-combat  
**backlog_ticket:** APP-027  
**ticket_path:** [tmp/backlog/app-027-validate-monster-id-at-combat-start.md](../../app-027-validate-monster-id-at-combat-start.md)  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)  
**domain_spec_creation:** not_needed (registry_gap false)

## Findings

### TICKET-001 — blocker

- **Location:** `tmp/backlog/app-027-validate-monster-id-at-combat-start.md` L21–23 (Expected files); `spec.md` L75; `tmp/app-combat-play-spec.md` L369, L412
- **Issue:** Ticket Expected files list only `app/gm/` and `play/tomb_gm/`. Run spec and domain spec require a **new** module `app/tests/test_combat_monster_validation.py` (V1–V8). Sibling tickets APP-026 and APP-028 explicitly list their test modules in Expected files.
- **Implementation gap:** Backlog hooks gate `app/**` edits to ticket Expected files (`tomb-dust-backlog.mdc`). Dev cannot land V1–V8 without expanding the ticket or hook denial on `app/tests/`.
- **Suggested fix:** Add `app/tests/test_combat_monster_validation.py` to ticket Expected files (and optionally `app/tests/test_tool_args.py` if adding `start_combat` validate unit tests there). Mirror in run `spec.md` § Affected paths note.

### SPEC-001 — blocker

- **Location:** `spec.md` test V5; domain spec § R3 L339, § R4 L345, § Tests V5 L379; `app/gm/orchestrator.py` L2684–2685 vs L2573–2576
- **Issue:** V5 asserts `_execute_tool("start_combat", {monster_specs: []})` returns `{ok: false}` **via tool_args** with `bridge.start_combat` **not called**. In the repo, `validate_tool_args` runs in `_llm_loop` / combat inner loop **before** `_execute_tool`, not inside `_execute_tool`. `_execute_tool("start_combat")` dispatches straight to `bridge.start_combat(**args)` with no arg validation.
- **Implementation gap:** Dev following V5 literally either (a) adds validation inside `_execute_tool` — diverging from `enter_dungeon` / existing APP-080 pattern — or (b) writes a test that cannot pass. Domain R3 claim that `_execute_tool` “already maps” `validate_tool_args` is false for `enter_dungeon` and `start_combat` today.
- **Suggested fix:** Rewire V5 to match APP-080: use `_dispatch_like_llm_loop` helper (`app/tests/test_tool_args.py` L33–39) or `_llm_loop` E2E with `MagicMock` on `bridge.start_combat` and assert `assert_not_called()`. Correct R3/R4 prose: “`_llm_loop` calls `validate_tool_args` then `_execute_tool`” (same as `enter_dungeon`). Optionally add unit test in `test_tool_args.py`: `validate_tool_args("start_combat", {"monster_specs": []}) == "monster_specs required"`.

### SPEC-002 — minor

- **Location:** `spec.md` R1 L41, L74; domain spec § R1 L296
- **Issue:** R1 allows `validate_monster_specs` in engine **or** “thin wrapper in `app/gm/`” without mandating import of `MONSTER_SPEC_RE` / `parse_monster_specs`.
- **Implementation gap:** Dev could duplicate regex and drift from engine messages that V2/V9 and APP-028 substring contracts depend on.
- **Suggested fix:** Require engine module as sole implementation site; if app needs import, say “import from `tomb_gm.services.simulation.combat` — no duplicate regex.”

### SPEC-003 — minor

- **Location:** `spec.md` L53, L82; domain spec § Tests V8 L382
- **Issue:** V8 says “APP-028 T3 regression with real error from V1 mock **or** integration” — contradictory (mock vs real). T3 today mocks `bridge.start_combat` (`test_combat_failure_narration.py` L184–188).
- **Implementation gap:** Dev may skip integration and only re-run mocked T3, leaving no test that real `validate_monster_specs` errors flow through `_llm_loop` all_failed strip.
- **Suggested fix:** Define V8 explicitly: e.g. parametrized `_llm_loop` test with **unmocked** `bridge.start_combat` (orchestrator + real content_root) for `hollow-knight:1`, assert prefix-only return; or drop V8 and rely on V6 + `pytest app/tests/test_combat_failure_narration.py -k start_combat`.

### SPEC-004 — minor

- **Location:** `spec.md` L61; domain spec § Tests commands L395
- **Issue:** Test plan includes `play/tomb_gm/tests/test_simulation.py -k unknown_monster`. Existing test only asserts CLI `returncode != 0` (`test_simulation.py` L114–136), not `validate_monster_specs` message or `{ok: false}` shape.
- **Implementation gap:** Dev may treat V9 as satisfied without adding engine unit test for `validate_monster_specs`.
- **Suggested fix:** Split command: new `test_validate_monster_specs_*` in `play/tomb_gm/tests/` for V9; keep CLI test as optional regression note only.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 feature; `in_progress`; domain spec field matches |
| registry_gap | **PASS** | false — `app-combat-play-spec.md` owns bridge + engine combat; research + PM justified |
| AC testability | **WARN** | Core AC mappable after TICKET-001 + SPEC-001 fixes |
| Code traces | **PASS** | Research paths A–E verified; engine `load_monster_json` L30–33; bridge catch L238–239; no `start_combat` in `validate_tool_args` L164–191 |
| Expected files ⊆ plan scope | **FAIL** | TICKET-001 — `app/tests/` missing |
| Wire / test design | **FAIL** | SPEC-001 — V5 vs `_llm_loop` validation architecture |
| Domain spec sync | **PASS** (draft) | § APP-027 mirrors run spec R1–R6, V1–V9; PM draft changelog dated 2026-05-22 |
| AGENTS.md drift policy | **PASS** | Behavior in domain spec; ticket AC minimal; no orphan canon edits |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Validate monster specs at `start_combat` | R1–R2, R4; V1–V3, V6–V7 | pytest (after fixes) | **WARN** until V5 wire fixed |
| Clear error (no fiction on unknown id) | R5 + APP-028 §; V1, V6–V8 | pytest + playtest hints | **PASS** (intent via APP-028 sibling) |
| Spec sync on close | Ticket § Spec sync; domain § + changelog | process | **PASS** (draft stage) |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| Engine rejects unknown id before DB write | `combat.py` L122–123, L237 — `_spawn_instances` before INSERT L249 |
| Bridge maps exceptions to `{ok: false}` | `bridge.py` L238–239 |
| No `start_combat` rules in `validate_tool_args` | `tool_args.py` L164–191 |
| `_execute_tool("start_combat")` has no pre-validation | `orchestrator.py` L2684–2685 |
| `validate_tool_args` runs in exploration loop only | `orchestrator.py` L2573–2576 before `_execute_tool` L2576 |
| APP-080 dispatch pattern for arg validation | `test_tool_args.py` L33–39 `_dispatch_like_llm_loop` |
| APP-028 T3 mocks bridge error (not real validation) | `test_combat_failure_narration.py` L136–141, L184–188 |
| `hollow-knight` in tool schema trains bad id | `tools.py` L163 |
| Empty `monster_specs` can start zero-monster combat today | `parse_monster_specs([])` → `[]`; `start_combat` L237 proceeds to party spawn |
| registry_gap false | `research-brief.md` L13–15; combat spec L278–398 |

## Summary

**FAIL** — fix **TICKET-001** (add test module to Expected files) and **SPEC-001** (V5/R3 wire: validation in `_llm_loop`, not `_execute_tool`) before Dev plan. PM draft is otherwise strong: layered R1–R3 validation, APP-028 error substring stability, empty-list policy, research-backed gaps, non-goals scoped. Address **SPEC-002**–**SPEC-004** in same PM revision for clearer Dev fixtures.

## Re-review focus

- Ticket Expected files include `app/tests/test_combat_monster_validation.py`
- V5 uses `_dispatch_like_llm_loop` or `_llm_loop` + bridge spy; R3/R4 prose corrected
- Optional: V8 integration definition; V9 new engine unit test vs CLI regression
- R1 single-source engine location mandated
