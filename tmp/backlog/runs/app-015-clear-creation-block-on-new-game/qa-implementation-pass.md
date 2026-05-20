# QA PASS: Implementation

**Task:** APP-015-clear-creation-block-on-new-game  
**backlog_ticket:** APP-015  
**ticket_path:** tmp/backlog/app-015-clear-creation-block-on-new-game.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**Round:** 1 (implementation review)  
**Verdict:** **PASS**

## Diff scope reviewed

| File | Change |
|------|--------|
| `app/gm/orchestrator.py` | `_session_state_path`, `_reset_creation_for_new_game`, `_clear_creation_block_on_disk`; C1–C2 prepended at `setup_new_game` entry; disk path unified in `_is_mid_creation_resume_failure` / `_delete_save_file` |
| `app/tests/test_creation_block_on_new_game.py` | **New** — T-015a–d (5 tests); tmp-path monkeypatch; never touches dev `session_state.json` |
| `tmp/app-session-persistence-spec.md` | PM/batch draft sections (APP-014/015/016); not yet APP-015 **done** changelog — Stage 6 |

**Not changed (per plan):** `app/ui/app.py` — orchestrator-first clear makes `_save_session()` idempotent.

## Tests run

| Command | Result |
|---------|--------|
| `cd app && python -m pytest tests/test_creation_block_on_new_game.py -q` | **5 passed** (0.83s) |
| `cd app && python -m pytest tests -q -k "creation_block or new_game_creation"` | **5 passed**, 18 deselected |
| `cd app && python -m pytest tests -q -k "creation_flow or session_resume"` | **8 passed**, 15 deselected |
| `cd app && python -m pytest tests -q` | **23 passed** (4.18s) |

## Ticket acceptance criteria

| AC | Status | Evidence |
|----|--------|----------|
| On **new game**, explicitly clear `session_state.json` **creation block** | **PASS** | `_clear_creation_block_on_disk` R-M-W sets `creation_state` from `export_creation_state()` after `_reset_creation_for_new_game`; runs as first steps in `setup_new_game` (lines 368–369) |

## Domain requirements (C1–C4)

| Req | Status | Evidence |
|-----|--------|----------|
| **C1** — Memory reset + disk persist **before** engine wipe | **PASS** | `_reset_creation_for_new_game()` then `_clear_creation_block_on_disk()` before `end_session` / `wipe_all_data` |
| **C2** — Surgical disk mutation; `engine_status` removed; other keys preserved | **PASS** | `data["creation_state"] = export…`; `data.pop("engine_status", None)`; T-015a preserves `narration_lines` / `input_history`; T-015d both branches |
| **C3** — All exit paths (early return) | **PASS** | T-015b mocked `campaign_new` failure — disk + memory NAME-fresh before return |
| **C4** — Batch vs APP-014/016 | **PASS** | C1–C2 before L1 `end_session`; L7 `_delete_save_file` unchanged on success; `engine_status` clear owned by APP-015 C2, not preserved |

## Automated test mapping (T-015a–d)

| Spec case | Test | Result |
|-----------|------|--------|
| **T-015a** — stale SKILLS + success | `test_t015a_setup_new_game_clears_stale_creation_on_disk` | **PASS** |
| **T-015b** — `campaign_new` failure | `test_t015b_campaign_new_failure_still_clears_creation` | **PASS** (disk + memory) |
| **T-015c** — `load game` after new game | `test_t015c_load_game_after_new_game_uses_name_not_stale_disk` | **PASS** — no SKILLS/Flupps; `[Awaiting: NAME_INPUT]` |
| **T-015d** — stale `engine_status` cleared | `test_t015d_engine_status_cleared_on_new_game_success` + `…_early_return` | **PASS** |

## Code review notes (non-blocking)

1. **`session_start` failure:** Not pytest’d; structurally identical to T-015b (C1–C2 run before L5) — acceptable per spec/plan.
2. **Missing save file:** `_clear_creation_block_on_disk` no-op when absent; no dedicated test (plan open question #1).
3. **T-015a / T-015d success:** `_delete_save_file` monkeypatched to no-op so post-L7 disk remains assertable — valid test technique; production L7 still unlinks on success.
4. **Spec sync:** Domain spec § APP-015 checklist/changelog still PM-draft / open `[ ]` — update on `release APP-015 --done` (Stage 6).
5. **Git:** `test_creation_block_on_new_game.py` is untracked (`??`) — include in Stage 7 commit.
6. **Manual smoke:** Stage 7 human playtest (mid-creation SKILLS → **new game** → inspect save; failure-path reload) per `human-test-plan.md` when present.

## Gate outcome

Implementation matches approved plan (round 2), domain § **New game — creation block clear (APP-015)**, and ticket AC. **Ready for:** drift check, `release APP-015 --done`, domain spec changelog + ticket close, Stage 7 manual playtest.
