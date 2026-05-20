# QA Report: plan — round 1

**Task:** APP-015-clear-creation-block-on-new-game  
**backlog_ticket:** APP-015  
**ticket_path:** tmp/backlog/app-015-clear-creation-block-on-new-game.md  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)

## Findings

### PLAN-001 — blocker (domain drift)

- **Location:** [plan.md](plan.md) WS1 §3 `_clear_creation_block_on_disk`, WS2 `seed_stale_creation` helper note, Files table
- **Issue:** Plan instructs implementers to **preserve** `engine_status` during the surgical C2 read-modify-write (“Do not strip other keys (APP-016 `engine_status` preservation)”). Domain spec § **New game — creation block clear (APP-015)** C2 and § **Engine status snapshot — New game — stale snapshot** require the opposite: on every `setup_new_game()` entry, C2 must **remove** `engine_status` or set it to **`null`** (T-015d).
- **Evidence:**
  - Domain: `tmp/app-session-persistence-spec.md` lines 187, 247–248, 301 (T-015d).
  - Plan: `plan.md` WS1 item 3 bullet “Do not strip other keys (APP-016 `engine_status` preservation)” and WS2 seed note “verify surgical write preserves” `engine_status`.
  - QA spec round 1 note (preserve `engine_status`) is **superseded** by domain PM r2 (changelog 2026-05-20 APP-016 r2).
- **Implementation gap:** If Dev follows the plan, post-wipe disk can retain fresh `creation_state` (NAME) with stale `engine_status.awaiting` / `roster` — exactly the batch-table failure mode domain assigns to APP-015.
- **Suggested fix:** Update `_clear_creation_block_on_disk` spec in plan: after setting `creation_state`, `data.pop("engine_status", None)` or `data["engine_status"] = None`. Add **T-015d** to WS2 table and `seed_stale_creation` assertions. Cross-reference domain C2 + APP-016 batch row, not “preserve engine_status.”

### PLAN-002 — blocker (incomplete test plan)

- **Location:** [plan.md](plan.md) WS2 test table; [spec.md](spec.md) C5 / Test plan (T-015a–c only)
- **Issue:** Domain spec mandates **T-015d** (stale `engine_status` cleared on `setup_new_game` entry). Plan lists only T-015a–c and pytest `-k "creation_block or new_game_creation"` with no T-015d case.
- **Suggested fix:** Add T-015d row: seed file with mismatched `engine_status` + stale `creation_state`; assert after `setup_new_game()` (success or mocked early return) `engine_status` absent or `null`. Include in new test module and manual Stage 7 bullet.

### PLAN-003 — minor (run spec index stale)

- **Location:** [spec.md](spec.md) Non-goals (“APP-016 `engine_status` snapshot on save”), C5 (“Tests T-015a–c”)
- **Issue:** Run `spec.md` still indexes a–c only and defers APP-016; domain spec now owns **engine_status removal on new game** under APP-015 C2. Not a plan-only defect, but Dev should treat **domain spec** as authority when revising plan.
- **Suggested fix:** PM revision optional; plan must cite domain T-015a–**d**.

## Verified (no blocker)

| Gate | Result |
|------|--------|
| Ticket valid (`in_progress`), domain spec pointer | OK |
| AC testable (explicit disk `creation_state` clear on `new game`) | OK — mapped to C1–C3 |
| Code traces A–E match repo | OK — see independent traces below |
| Plan files ⊆ ticket scope | OK — `app/gm/orchestrator.py` + `app/tests/` match ticket “session persistence layer” and run `spec.md` Affected paths |
| AGENTS.md / canon | OK — app-only, no `build/` |
| Prepend C1–C2 before `wipe_all_data` | OK — aligns with domain C1 and current `setup_new_game` at `app/gm/orchestrator.py:348–356` |
| T-015b in-memory assertion | OK — plan includes `orchestrator.creation.step == "NAME"` on failure (qa-spec follow-up) |
| APP-014 ordering note | OK — C1→C2 before L1 when merged |
| UI out of scope | OK — orchestrator-first clear; `app/ui/app.py:323–325` `finally` trace confirmed |

### Independent code traces (plan round 1)

| Trace | Plan claim | Verified |
|-------|------------|----------|
| A — happy `new game` | Reset only after engine success; L7 unlink | `setup_new_game` `348–361`: wipe→campaign→session_start, then `history.clear()`, `CreationState`, `_delete_save_file` |
| B — `campaign_new` failure | Early return `355–356`; no reset; `finally` saves stale | Confirmed; `process_turn` `495–499` returns error string (truthy → `_save_session`) |
| C — resume probe | Disk `step != "NAME"` → variant B | `_is_mid_creation_resume_failure` `308–318`; `_resume_failure_message` uses `self.creation.step` `328–339` |
| D — autosave | 60s `_save_session` can persist stale mid-setup | `app/ui/app.py:216–220`, `393–425` |
| E — callers | `process_turn` new game, death, run_ended | `495–500`, `383`, `518` — single `setup_new_game` hub |

**Gap confirmed:** No `_clear_creation_block_on_disk` / `_session_state_path` today; three inline `Path(__file__).parents[1] / "session_state.json"` usages (`107`, `308`, `397`).

**UI note:** `_save_session` does not yet write `engine_status` (APP-016 not implemented). T-015d is still required so C2 clear is specified before APP-016 lands.

## Summary

Plan structure, traces, prepend ordering, and orchestrator/test scope are sound. **FAIL** because C2 contradicts the domain spec on **`engine_status`** (preserve vs remove) and the test plan omits **T-015d**. Dev must revise `plan.md` (round 2) before implementation.

## Re-review focus

- WS1 `_clear_creation_block_on_disk`: explicit `engine_status` removal per domain C2
- WS2: T-015d test + seed fixture asserting absent/null `engine_status`
- Remove or correct any “preserve `engine_status`” language in WS1/WS2
- Confirm merged APP-014 order: **C1 → C2 → L1 → L1b → L2 …**
