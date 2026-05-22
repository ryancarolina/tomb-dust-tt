# QA PASS: plan — round 1

**Task:** app-027-validate-monster-id-combat  
**backlog_ticket:** APP-027  
**ticket_path:** [tmp/backlog/app-027-validate-monster-id-at-combat-start.md](../../app-027-validate-monster-id-at-combat-start.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (qa-spec-pass round 2 confirmed `registry_gap: false`)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

**Blocker count:** 0

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec = `app-combat-play-spec.md`
- [x] Ticket domain spec matches plan (`spec.md`, `tmp/app-combat-play-spec.md` § Monster id validation at combat start)
- [x] Acceptance criteria testable (R1–R6 → V1–V9; pytest commands listed)
- [x] Code traces match repo (symbols and flows spot-checked independently; line refs approximate but correct)
- [x] AGENTS.md / canon compliance (engine-only R1; no `build/` drift; bridge contract; APP-028 substring stability)
- [x] Tests/commands listed (three required pytest modules + optional CLI regression)
- [x] Plan files ⊆ ticket Expected files (strict subset + domain spec on close)
- [x] registry_gap matches reality (N/A at plan gate — spec QA confirmed `false`)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `play/tomb_gm/services/simulation/combat.py` — R1 `validate_monster_specs` | Yes (`play/tomb_gm/`) |
| `app/gm/bridge.py` — R2 pre-check | Yes (`app/gm/`) |
| `app/gm/tool_args.py` — R3 normalize + validate | Yes (`app/gm/`) |
| `app/gm/tools.py` — optional R6 example hygiene | Yes (`app/gm/`) |
| `app/tests/test_combat_monster_validation.py` — V1–V8 | Yes (explicit path) |
| `play/tomb_gm/tests/test_validate_monster_specs.py` — V9 | Yes (`play/tomb_gm/`) |
| `tmp/app-combat-play-spec.md` — changelog on `release --done` | Yes (ticket § Spec sync) |

Explicit out-of-scope: `app/gm/orchestrator.py` wire changes, mixed-tool fiction, beat `MONSTER_ID_RE` content, CLI `{ok: false}` contract, `test_tool_args.py` optional unit (V5 supersedes), APP-030 golden path — no unauthorized paths.

## Code trace audit

Independent spot-check against live repo:

| Symbol / flow | File | Present (pre/planned) | Plan ref |
|---------------|------|------------------------|----------|
| `MONSTER_SPEC_RE`, `parse_monster_specs`, `load_monster_json` | `combat.py` L13–33 | Yes | Flow A |
| `_spawn_instances` before INSERT | `combat.py` L237 → L249+ | Yes | Flow A step 5–6 |
| No `validate_monster_specs` yet | `combat.py` | Yes (planned new) | R1 |
| `bridge.start_combat` → engine; `ValueError`/`FileNotFoundError` catch | `bridge.py` L224–239 | Yes | Flow B |
| `start_combat_from_trigger` duplicate guard → `start_combat` | `bridge.py` L302–307 | Yes | Flow B step 4 |
| No `start_combat` in `_ALLOWED_KEYS` / `validate_tool_args` | `tool_args.py` L11–21, L164–191 | Yes | Flow C |
| `_dispatch_like_llm_loop` helper | `test_tool_args.py` L33–39 | Yes | V5 |
| Exploration `_llm_loop`: normalize → validate → `_execute_tool` | `orchestrator.py` L2572–2576 | Yes | Flow C/D |
| `_execute_tool("start_combat")` direct bridge | `orchestrator.py` L2684–2685 | Yes | V6 intentional bypass |
| APP-028 `_COMBAT_TOOL_NAMES` all_failed strip | `orchestrator.py` L2615–2628 | Yes | Flow D / V8 |
| `_handle_combat_trigger` → `start_combat_from_trigger` | `orchestrator.py` L2480–2499 | Yes | V7 |
| `pending_start` → `start_combat_from_trigger` | `orchestrator.py` L2266–2273 | Yes | Flow D step 6 |
| `hollow-knight` in tool schema; no JSON in `build/` | `tools.py` L163; `build/data/monsters/` | Yes | V1/V8/V9 |
| `grave-ghoul.json` exists | `build/data/monsters/grave-ghoul.json` | Yes | V4/V9 happy path |
| `isolated_workspace` → `content_root: build/` | `app/tests/helpers.py` L15–22 | Yes | Fixtures |
| APP-028 T3 mocks bridge (not real validation) | `test_combat_failure_narration.py` L175–188 | Yes | V8 distinction |

Plan line anchors (~2572, ~2684, ~224) verified 2026-05-22; may drift before impl — use symbol search.

## qa-spec-pass (round 2) → plan resolution

| Spec QA item | Plan handling |
|--------------|---------------|
| TICKET-001 Expected files include test module | Plan files table + task 5; ticket L24 lists `app/tests/test_combat_monster_validation.py` |
| SPEC-001 V5 wire via `_llm_loop` not `_execute_tool` alone | V5 uses `_dispatch_like_llm_loop`; V6 explicitly bypasses R3 for bridge R1 |
| SPEC-002 R1 engine-only | Flow A/B import from `tomb_gm.services.simulation.combat`; no duplicate regex in `app/gm/` |
| SPEC-003 V8 unmocked integration | V8: mock `chat_completion` only; real `bridge.start_combat`; not APP-028 T3 mock |
| SPEC-004 V9 engine unit split | `play/tomb_gm/tests/test_validate_monster_specs.py`; CLI demoted optional |
| Adversarial empty-list string | Locked `"monster_specs required"` in R1 + R3 (plan L23, L111) |

## Ticket AC → plan / tests

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| Validate monster specs at `start_combat` | R1–R4 layered gates; Flows A–D | V1–V3 (bridge), V5 (tool args), V6–V7 (orchestrator paths), V9 (engine unit) |
| Clear error (no fiction on unknown id) | R5 + APP-028 paths unchanged | V1, V6–V8; APP-028 regression `-k start_combat` |
| Spec sync on close | Close checklist § domain changelog | `release APP-027 --done` |

### Requirement map

| ID | Plan locus | Test |
|----|------------|------|
| R1 | `combat.py:validate_monster_specs` (+ optional engine early return) | V9, V1–V3 via bridge R2 |
| R2 | `bridge.py:start_combat` pre-check | V1–V3, V6–V8 |
| R3 | `tool_args.py` normalize + validate | V5 |
| R4 | Wire unchanged in `orchestrator.py` | V5, V6–V8, V7 beat path |
| R5 | APP-028 consumption of `{ok: false}` | V7, V8 |
| R6 | optional `tools.py` example | none required |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-027 `in_progress` |
| Plan ⊆ Expected files | **PASS** | Six code paths + spec on close |
| Code traces | **PASS** | Flows A–E verified independently |
| Spec R1–R6 coverage | **PASS** | All requirements mapped to locus + tests |
| AC testability | **PASS** | V1–V9 + APP-028 regression |
| APP-028 compatibility | **PASS** | Substring contract + regression commands |
| TurnTruth / narration | **PASS** | Code-owned failure bypass documented |
| qa-spec-pass alignment | **PASS** | Round 2 blockers addressed in plan |

## Notes (non-blocking — impl QA)

1. **Session bootstrap for bridge tests:** Plan R2 validates after `_active_session_id()` / `_campaign_slug()` (domain § R2). `bridge` fixture calls `init()` only; `orchestrator` fixture does not start a session. V1–V3, V6–V8 need a shared fixture (`init` + `campaign_new` + `session_start`) or tests will raise `NO_ACTIVE_SESSION` before monster validation. Recommend documenting in test module setup.
2. **Validation-before-session alternative:** Moving R2 before session resolution would simplify negative tests but diverges from domain spec ordering — follow spec unless ticket amended.
3. **`_normalize_start_combat` coercion:** Single string → list is implied, not in PM spec — acceptable APP-080 consistency; skip if no test requires it.
4. **Engine optional early R1 in `start_combat`:** Defense-in-depth for CLI; bridge R2 is AC-critical.
5. **V4 happy path:** Skip/defer per spec; APP-030 owns golden start.
6. **Line number drift:** Plan cites ~2572 / ~2684 / ~224; use symbol search during impl.

**Verdict:** PASS — ready for workstreams + implementation.
