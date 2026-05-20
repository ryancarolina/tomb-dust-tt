# QA PASS: spec

**Task:** APP-015-clear-creation-block-on-new-game
**backlog_ticket:** APP-015
**ticket_path:** tmp/backlog/app-015-clear-creation-block-on-new-game.md
**Round:** 1
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-session-persistence-spec.md`)
- [x] Acceptance criteria testable
- [x] Code traces match repo (research-brief + domain § align with `orchestrator.py:348–361` early-return gap and `_is_mid_creation_resume_failure` disk probe)
- [x] AGENTS.md / canon compliance (app persistence only; no `build/` changes)
- [x] Tests/commands listed (`T-015a–c`, pytest `-k "creation_block or new_game_creation"`)
- [x] registry_gap matches reality (`false`; Session persistence row in `tmp/app-master-spec.md`)
- [x] If registry_gap true: domain spec exists or approved § Proposed domain spec (spec only) — N/A

**Notes:**

- **Ticket gate:** APP-015 is `in_progress`; domain spec pointer matches ticket. Run `spec.md` correctly indexes domain § **New game — creation block clear (APP-015)** with C1–C4.
- **Registry / drift:** `registry_gap: false` is correct — behavior belongs under existing Session persistence spec; no orphan spec proposed.
- **AC coverage:** Ticket AC (“explicitly clear `session_state.json` creation block on new game”) maps to domain C1–C3 and tests T-015a–c. C3 early-return case (mock `campaign_new` failure) is covered; `session_start` failure is structurally identical once C1–C2 prepend at `setup_new_game` entry — acceptable for spec stage.
- **Batch boundaries (APP-014 / APP-016):** Domain § batch table and C4 are consistent: APP-015 prepends in-memory + disk clear **before** APP-014 L1/L2; APP-014 owns L1–L5 lifecycle and L6–L7 success reset; APP-016 `engine_status` preserved by surgical C2 write rule. APP-014 run spec and domain § explicitly defer failure-path creation clear to APP-015 — no ownership conflict.
- **Non-blocker follow-ups for Dev plan:** (1) T-015b should assert in-memory `creation.step == NAME` on failure path, not disk alone — guards UI `_save_session()` finally rewriting stale memory. (2) Ticket **Expected files** is vague (“session persistence layer”); plan stage should pin `app/gm/orchestrator.py` + `app/tests/` (already in run `spec.md` Affected paths). (3) Domain spec references § Engine status snapshot (APP-016) in checklist/changelog but section body is not yet present — APP-016 debt; APP-015 C2 inline rule is sufficient for implementers.
