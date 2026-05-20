# QA PASS: plan

**Task:** APP-016-snapshot-engine-status-on-save
**backlog_ticket:** APP-016
**ticket_path:** tmp/backlog/app-016-snapshot-engine-status-on-save.md
**Round:** 1
**domain_spec_creation:** not_needed (spec QA round 2 confirmed)

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec/plan (`tmp/app-session-persistence-spec.md` § Engine status snapshot on save (APP-016))
- [x] Acceptance criteria testable (snapshot on save; failure omit; legacy load unchanged; batch coordination)
- [x] Code traces match repo (independent re-trace below)
- [x] AGENTS.md / canon compliance (write-only persistence; no `build/` changes)
- [x] Tests/commands listed (T4a–d; pytest `-k "engine_status or save_session"`)
- [x] Plan files ⊆ ticket Expected files
- [x] registry_gap not applicable at plan stage (spec QA confirmed `false`)

## Independent code trace (adversarial)

| Claim | Repo evidence | Verdict |
|-------|---------------|---------|
| `_save_session` partial `get_status()` today | `app/ui/app.py:393–404` — extracts `active.session_id` / `campaign_slug`; swallows exceptions | Confirmed |
| No `engine_status` on disk yet | `app/ui/app.py:405–421` — `data` keys listed; no snapshot field | Confirmed |
| Single-call optimization (S5c) | Same block already calls `get_status()` once | Confirmed — plan B1–B3 refactor is minimal |
| Save triggers unchanged | `app/ui/app.py:57,78` (quit); `216–220` (`_autosave_interval = 60.0`); `323–325` (`_process_turn` `finally`) | Confirmed |
| `get_status()` → `handle_status` | `app/gm/orchestrator.py:101–102` → `app/gm/bridge.py:37` → `play/tomb_gm/cli/cmd_core.py:84–98` (`ok`, `awaiting`, `roster`, `party`, `combat`, `active`) | Confirmed |
| Prior art payload shape | `app/gm/orchestrator.py:275–284` — `_log_creation_finalize_status` logs full `bridge.status()` as `engine_status` | Confirmed |
| Load path out of scope | `app/ui/app.py:427–451` — no `engine_status` read; `import_creation_state` + `_sync_*` from live status only | Confirmed — plan correctly forbids edits |
| Failure omit (S5d) | Plan B3: exception / `ok is False` / `_error` → omit key; matches domain S5d | Confirmed — defensive `ok`/`_error` aligns with finalize logging pattern |
| Mid-creation fixture realism | `app/tests/test_creation_flow.py:26–28` — `new game` → NAME; `Dumpy` → RACE; engine `CHARACTER_CREATION` + empty roster typical before finalize | Confirmed for T4a |
| Isolated save path | `app/ui/app.py:18` — `SAVE_PATH`; monkeypatch plan is correct | Confirmed |
| Orchestrator tests exist | `app/tests/conftest.py:25–90` — `isolated_workspace`, `orchestrator`, `mock_openrouter_client` | Confirmed — T4a/b can reuse; no App tests exist yet (new fixture) |

## AC mapping (plan → ticket → domain)

| Ticket / domain AC | Plan coverage | Test |
|--------------------|---------------|------|
| Snapshot `status()` on save | WS1 — conditional `engine_status` in `_save_session` | T4a, T4b |
| Full dict / reconcile keys | B3 assign full `status`; T4a asserts `awaiting`, `roster` | T4a, T4b |
| Failure non-blocking | B3 omit key; no `null` on failure | T4d |
| Legacy load unchanged | Explicit out-of-scope; no `_load_session` edits | T4c |
| Triggers unchanged | Trace A; no new call sites | Review only |
| APP-015 owns new-game clear | G batch table; no `orchestrator.py` in plan | T-015d (015); batch note |
| APP-017/018 consumers | Write-only; optional docstring | N/A this ticket |

## Scope gate

| Path | In ticket Expected? | In plan | Role |
|------|---------------------|---------|------|
| `app/ui/app.py` | Yes | Yes | **Edit** — `_save_session` snapshot |
| `app/tests/test_engine_status_on_save.py` | Yes (`app/tests/`) | Yes | **Add** — T4a–d |
| `app/tests/conftest.py` | Yes (under `app/tests/`) | Optional | **Maybe** — `headless_app` / `save_path` |
| `tmp/app-session-persistence-spec.md` | Yes | WS3 on close | Changelog / AC — not blocking code |
| `app/gm/orchestrator.py` | Batch note only | Out of scope | **APP-015** — correct |

## Cross-checks (spec QA round 2 → plan)

- [x] Plan honors qa-spec-pass: write-only; APP-015 C2 clears stale `engine_status` on `setup_new_game`; implement-order note (015 with or before 016)
- [x] S5d canonical: omit key on save failure (plan B4); does not write `engine_status: null` on failure
- [x] Single `get_status()` per save (S5c) — no second bridge round-trip
- [x] Run `spec.md` R1–R3 and domain § APP-016 aligned with plan traces C–F

## Notes (non-blocking)

1. **Pytest path when `cd app`:** Plan §Tests uses `app/tests/test_engine_status_on_save.py`. From `app/` cwd the collect path must be `tests/test_engine_status_on_save.py` (verified: `app/tests/...` fails). Domain spec uses the same `cd app && pytest app/tests` wording — impl/QA should run `tests/...` from `app/` or `app/tests/...` from repo root.
2. **T4d vs spec T4d:** Spec allows error-shaped `get_status()` return; plan implements B3 logic but T4d only monkeypatches raise. Impl should add optional `test_save_omits_engine_status_on_error_shaped_status` (`ok: False` or `_error`) or fold into T4d — low risk because `handle_status` normally returns `ok: True`.
3. **First headless `App` tests:** No existing `pygame`/`App` usage under `app/tests/`; plan’s `SDL_VIDEODRIVER=dummy` fixture is new surface — impl QA must run the module on Windows/Linux CI.
4. **T4b cost:** Full `INPUTS` loop is heavy but matches `test_creation_flow.py` — acceptable; plan correctly reuses `FIXED_ROLL` / constants.
5. **T4c assertion vagueness:** “smoke: `creation.active` or history length” is enough for plan gate; impl QA may tighten asserts.
6. **Pytest not run:** Plan phase only; implementation QA must execute commands in plan §Tests.
7. **Batch:** If APP-015 lands after APP-016 without C2, failure-path `new game` can leave stale `engine_status` — plan documents ordering; batch board should enforce 015 C2 before or with 016 merge.

**Verdict:** PASS — plan is implementation-ready; minimal `_save_session` diff, isolated tests, and scope boundaries match domain spec and qa-spec-pass round 2.
