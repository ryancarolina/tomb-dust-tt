# Workstreams: APP-057-test-creation-flow

**backlog_ticket:** APP-057

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Creation R6 table-shown + chain fixes | — | `app/gm/creation.py`, `app/gm/orchestrator.py` | R6 gates/chains/guards in place; engine gating regression green |
| WS2 | Full creation integration test | WS1 | `app/tests/test_creation_flow.py` | `python -m pytest app/tests/test_creation_flow.py -q` exit 0; smoke + engine gating regressions green |

**Stream count:** 2 — WS1 unblocks the canonical 8-input Apprentice path; WS2 asserts it end-to-end (depends on WS1).

---

## WS1 — Creation R6 table-shown + chain fixes

**Scope:** Plan §1 (`creation.py`) + §2 (`orchestrator.py`) — requirements R6 only. Fix `CreationState` race/class `*_table_shown` flags, routing gates, auto-present flags, NAME→RACE and ROLL_STATS→CLASS chains, and execute guards so the code-first 8-input path reaches `_auto_finalize` without re-presenting tables on player commits.

**Requirements covered:** spec R6 (ticket Expected files: `creation.py`, `orchestrator.py`).

### Implementation order (within stream)

| # | Task | File | Plan ref |
|---|------|------|----------|
| 1 | Add `races_table_shown`, `classes_table_shown`; `advance()` resets on enter RACE/CLASS | `creation.py` | §1.1–1.2 |
| 2 | `to_dict()` / `from_dict()` serialization (default `False`) | `creation.py` | §1.3–1.4 |
| 3 | Swap `_creation_turn_body` RACE/CLASS gates to `*_table_shown` | `orchestrator.py` ~590, ~597 | §2.1 |
| 4 | Set flags at start of `_auto_present_race` / `_auto_present_class` | `orchestrator.py` ~681, ~692 | §2.2–2.3 |
| 5 | NAME→RACE chain; extend ROLL_STATS→CLASS nested chain | `orchestrator.py` ~839 | §2.4 |
| 6 | RACE/CLASS execute guards in `_execute_creation_choice` | `orchestrator.py` ~1190, ~1200 | §2.5 |

**Do not** add a standalone `if step == "CLASS"` chain branch (CLASS reached via ROLL_STATS path only).

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Flag vs value | Reset `races_table_shown` / `classes_table_shown` on `advance()` enter step; **do not** clear `race` / `chosen_class` on advance |
| Gate parity | RACE/CLASS routing mirrors SKILLS: gate on `not *_table_shown`, not `not race` / `not chosen_class` |
| Present flags | Set `races_table_shown` / `classes_table_shown` at **start** of `_auto_present_*` (mirror `_auto_present_skills`) |
| ROLL_STATS chain | After `_auto_roll_stats`, if step is `CLASS`, chain `_auto_present_class`; do **not** modify `_auto_roll_stats` body |
| Execute guards | Mirror SKILLS error strings; guard runs before parsing/commit |
| Resume | `from_dict` defaults `False` for missing keys — acceptable per QA (APP-010 edge) |
| Out of scope | No `test_creation_flow.py`; no `conftest.py`; no domain spec edit |

### Test gates (WS1 done when all pass)

```bash
# From repo root — regression (no new test file yet)
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
python -m pytest app/tests/test_smoke.py -q
```

**Expected:** exit 0. Manual optional: replay 8 inputs in PyGame after WS2 — not required to close WS1.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-057
ticket: tmp/backlog/app-057-test-creation-flow.md
run-folder: tmp/backlog/runs/app-057-test-creation-flow/
spec: spec.md | plan: plan.md §1–2 | domain spec: tmp/app-character-creation-spec.md (read only until release)
workstreams: workstreams.md § WS1

Implement WS1 only (creation.py + orchestrator.py R6). Follow plan.md task order 1–5.
AGENTS.md: claim ticket if not active; stay within Expected files; no domain spec edit during impl.
Run: python -m pytest play/tomb_gm/tests/test_creation_gating.py -q && python -m pytest app/tests/test_smoke.py -q
Write reflection-dev-impl-WS1.md before return.
```

---

## WS2 — Full creation integration test

**Scope:** Plan §3 — new `app/tests/test_creation_flow.py` with `test_full_creation_apprentice_caster`: deterministic `roll_attributes` monkeypatch, 8-input turn loop with per-step assertions, post-finalize roster/status/footer checks. Requirements R1–R3.

**Depends on:** WS1 — without R6 fixes, turn 3+ stalls (race/class re-present) and finalize never runs.

**Requirements covered:** spec R1–R3 (ticket AC: test file + pytest green).

### Implementation order (within stream)

| # | Task | Detail | Plan ref |
|---|------|--------|----------|
| 1 | New module `test_creation_flow.py` | Module docstring; `FIXED_ROLL` constant | §3.1–3.2 |
| 2 | `roll_attributes` monkeypatch | `lambda race: {**FIXED_ROLL, "race": race}` on `orchestrator.bridge` | §3.3 |
| 3 | Turn loop + step assertions | `INPUTS` 8-tuple list; assert `creation.active` after `"new game"` | §3.4 |
| 4 | Post-finalize assertions | roster, `awaiting`, footer strings, no `PRE_DELVE` | §3.5 |

### Critical constraints (impl agent must not skip)

| Constraint | Detail |
|------------|--------|
| Fixtures | `orchestrator` + `monkeypatch` only — transitive `mock_openrouter_client`, `isolated_workspace` |
| Forbidden imports | No module-level `from gm.orchestrator import Orchestrator` |
| Forbidden duplication | No inline `mock_openrouter_client`; no import from `play/tomb_gm/tests/test_creation_gating.py` |
| Conftest | **No change** to `app/tests/conftest.py` (R4 — roll mock inline only) |
| `FIXED_ROLL` | `ok: True`, `INT >= 8`, `apprentice` ∈ `eligible_classes`, include `militia`/`peasant` |
| Isolation | `isolated_workspace` — no writes under `play/workspace` |
| Out of scope | No `creation.py` / `orchestrator.py` edits unless WS1 incomplete |

### Test gates (WS2 done when all pass)

```bash
# From repo root — primary
python -m pytest app/tests/test_creation_flow.py -q

# Regression
python -m pytest app/tests/test_smoke.py -q
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
```

**Expected:** ≥1 test collected in `test_creation_flow.py`, all commands exit 0.

### Post-impl (not WS2 — ticket release step)

- `tmp/app-character-creation-spec.md` — checklist + changelog (plan R5)
- `python tmp/backlog/claim_ticket.py release APP-057 --done`

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-057
ticket: tmp/backlog/app-057-test-creation-flow.md
run-folder: tmp/backlog/runs/app-057-test-creation-flow/
spec: spec.md | plan: plan.md §3 | domain spec: tmp/app-character-creation-spec.md (read only until release)
workstreams: workstreams.md § WS2

Prerequisite: WS1 merged or present in branch (R6 fixes in creation.py + orchestrator.py).
Implement WS2 only — new test_creation_flow.py per plan §3. Do not edit conftest unless roll mock duplicated elsewhere.
Run: python -m pytest app/tests/test_creation_flow.py -q && python -m pytest app/tests/test_smoke.py -q && python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
Write reflection-dev-impl-WS2.md before return.
```
