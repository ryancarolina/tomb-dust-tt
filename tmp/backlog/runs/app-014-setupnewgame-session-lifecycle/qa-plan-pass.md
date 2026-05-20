# QA PASS: plan

**Task:** APP-014-setupnewgame-session-lifecycle  
**backlog_ticket:** APP-014  
**ticket_path:** tmp/backlog/app-014-setupnewgame-session-lifecycle.md  
**Round:** 1  
**domain_spec_creation:** not_needed (spec QA round 1 confirmed)

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-session-persistence-spec.md` § setup_new_game lifecycle (APP-014))
- [x] Acceptance criteria testable (L1/L1b → L2 → L4 → L5; T-014a–c; manual APP-064 follow-on)
- [x] Code traces match repo (independent re-trace below)
- [x] AGENTS.md / canon compliance (orchestrator lifecycle only; no mechanics/canon drift)
- [x] Tests/commands listed (primary module + regression `-k` filters + engine session smoke)
- [x] Plan files ⊆ ticket Expected files (with pre-impl ticket metadata note — see Scope gate)
- [x] registry_gap not applicable at plan stage (spec QA confirmed `false`)

## Independent code trace (adversarial)

| Claim | Repo evidence | Verdict |
|-------|---------------|---------|
| Bug: wipe-first, no session end | `app/gm/orchestrator.py:348–361` — `setup_new_game` opens with `wipe_all_data()` | Confirmed |
| L1b must be orchestrator-owned | `app/gm/bridge.py:399–405` — `end_session` only calls `force_close_all_sessions` on **exception**; `play/tomb_gm/domain/session.py:311–324` returns `{"ok": False, …}` for missing/already-ended session | Confirmed — plan L1b block is required |
| Wipe excludes corpses | `app/gm/bridge.py:423–440` — `tables` list has no `world_corpses` | Confirmed |
| New-game turn path | `app/ui/app.py:283–289` clears narration; `orchestrator.process_turn` ~495–500 checks `ok` and surfaces error | Confirmed |
| Death restart uses hub | `orchestrator.py:382–383` — `setup_new_game(campaign_slug)` with no duplicate lifecycle | Confirmed |
| Resume `run_ended` uses hub | `orchestrator.py:509–518` — `setup_new_game(campaign_slug)` before death_msg | Confirmed |
| Failure autosave race | `app/ui/app.py:323–325` — `_save_session()` in `finally` when `narration is not None`; failed setup returns error string (narration set) | Confirmed — APP-015 scope; plan correctly defers |
| Session start after wipe | `play/tomb_gm/domain/session.py:161–207` — INSERT id `current`, `write_active`, `replaced_previous: True` | Confirmed |
| Fixtures exist | `app/tests/conftest.py:25–36` (`isolated_workspace`, `bridge`), `74–90` (`orchestrator`) | Confirmed |
| Corpse death pattern | `play/tomb_gm/tests/test_death_rules.py:115–134` — `process_delver_death` + corpse row survives character DELETE | Plan T-014c reference valid |

## AC mapping (plan → ticket → domain)

| Ticket AC | Plan / domain coverage | Test |
|-----------|------------------------|------|
| session end → wipe → campaign new → session start | L1/L1b prepend; L2–L5 unchanged order (`init` L3 retained per domain) | T-014a, T-014b |
| Domain spec updated on close | Plan §3 — checklist + changelog at release | Impl close |
| Stuck partial creation → `new game` → NAME | Trace A + L6 reset; mid-creation fixture in T-014a | T-014a + manual (Stage 7) |
| `world_corpses` persist | Invariant L5; wipe table list verified | T-014c |

## Scope gate

| Path | In ticket Expected? | In plan | Role |
|------|---------------------|---------|------|
| `app/gm/orchestrator.py` | Yes | Yes | **Edit** — L1/L1b prepend |
| `app/main flow` (interpreted) | Yes (vague) | `app/ui/app.py` read-only trace A3–A8 | Read-only |
| `app/tests/test_setup_new_game_lifecycle.py` | **No** (gap) | Yes | **Add** — T-014a–c |
| `app/gm/bridge.py` | No | Read-only API reference | Read-only — OK |
| `tmp/app-session-persistence-spec.md` | Spec sync on close | Plan §3 | Close metadata — OK |

**Pre-impl action (non-blocking for plan PASS):** Update ticket **Expected files** to name `app/tests/test_setup_new_game_lifecycle.py` (and optionally `app/ui/app.py` explicitly) before Stage 4 / `impl-check`, per qa-spec-pass note and APP-057 precedent. Domain spec § Tests APP-014 already mandates T-014a–c; plan is correct to add the test module.

## Out-of-scope boundaries (verified)

| Deferred item | Plan owner | Leak in plan? |
|---------------|------------|---------------|
| Failure-path creation disk clear | APP-015 | No — trace C4, §4 |
| `engine_status` snapshot | APP-016 | No |
| Caller `ok` / UI toast | APP-019 | No — optional note only |
| Bridge/orchestrator `"already exists"` swallow | Unchanged | No |

Batch note: APP-015 may prepend C1–C2 **before** L1 in same function — plan documents merge order (014 first).

## Notes (non-blocking)

1. **T-014c fixture depth:** Plan references `test_death_rules.py` pattern but does not spell minimal character + session setup — impl agent should read `death_db` / `process_delver_death` prerequisites; risk of over-heavy fixture (Dev reflection aligns).
2. **T-014b assertion:** After L2 wipe, prior session row may be **deleted** rather than ended — plan allows both; impl should assert post-condition (≤1 open session, new id `current`) not intermediate L1 state alone.
3. **Pytest not run:** Plan phase only; impl QA must run commands in plan §Tests.
4. **Ticket Expected files:** Vague `app/main flow` — plan interprets as orchestrator + UI pipeline; acceptable for plan gate with metadata fix before impl.

**Verdict:** PASS — plan is implementation-ready; minimal L1/L1b prepend matches domain spec and qa-spec-pass L1b requirement; tests and traces are sufficient for workstreams.
