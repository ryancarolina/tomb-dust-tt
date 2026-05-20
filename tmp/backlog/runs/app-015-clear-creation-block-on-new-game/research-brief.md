# Research Brief: APP-015-clear-creation-block-on-new-game

**Date:** 2026-05-20  
**Question:** Where can stale `creation_state` in `session_state.json` survive a `new game` command, and what must change so the on-disk creation block is explicitly cleared every time?

**backlog_ticket:** APP-015  
**ticket_path:** tmp/backlog/app-015-clear-creation-block-on-new-game.md  
**domain_spec:** tmp/app-session-persistence-spec.md  
**ticket_status_at_start:** in_progress

**registry_gap:** false

## Registry gap justification

Ticket domain spec [`tmp/app-session-persistence-spec.md`](../../app-session-persistence-spec.md) is registered in [`tmp/app-master-spec.md`](../../app-master-spec.md) § Spec registry as **Session persistence** — owns `session_state.json`, autosave, resume, and `play/workspace/`. APP-015 is listed in that spec's open checklist (APP-014–APP-020 session lifecycle batch) and the spec already documents `creation_state` persistence, `setup_new_game()` wipe behavior, and the test case "`new game` from stuck partial creation → clean NAME step." No new domain spec row is required.

## Summary

Today `setup_new_game()` eventually resets in-memory `CreationState(active=True, step="NAME")` and calls `_delete_save_file()`, which **unlink**s the entire `session_state.json`. That works on the happy path, but the creation block is not cleared **explicitly** and clearing happens **late** — only after `wipe_all_data()`, `init()`, `campaign_new()`, and `session_start()` complete. If `campaign_new()` returns early (non–"already exists" failure), neither memory nor disk is touched; stale mid-creation data survives.

Even on partial success, there is a window after engine wipe where the DB is empty but `session_state.json` still holds a rich `creation_state` (e.g. `step: "SKILLS"`, name, roll_result) — matching the live `app/session_state.json` repro in-repo. `_is_mid_creation_resume_failure()` reads that disk block (active flag or `step != "NAME"`) to classify load failures as variant B, so uncleared files mislead recovery UX. The ticket AC asks for an **explicit creation-block clear**, not reliance on whole-file delete at the end of a multi-step routine; this also future-proofs APP-016 (engine status snapshot on save) where other JSON fields may need to persist.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| New game entry | `app/gm/orchestrator.py` — `process_turn` (`new game` branch), `setup_new_game`, `_delete_save_file` | Only success path clears save; early return at `campaign_new` failure skips clear |
| Creation persistence | `app/gm/orchestrator.py` — `export_creation_state`, `import_creation_state`, `_restore_history` | Export only when `creation.active`; import on load game |
| Mid-creation disk probe | `app/gm/orchestrator.py` — `_is_mid_creation_resume_failure` | Reads `creation_state` from disk independent of in-memory reset timing |
| Creation FSM | `app/gm/creation.py` — `CreationState.to_dict` / `from_dict` | Full block includes step, name, race, roll_result, table flags |
| UI autosave | `app/ui/app.py` — `_save_session`, `_load_session`, `_autosave`, `_process_turn` | Writes `creation_state` from orchestrator; `new game` queues `clear_narration` only — no disk clear |
| Bridge wipe | `app/gm/bridge.py` — `wipe_all_data`, `session_start`, `campaign_new` | Wipe does not touch `app/session_state.json` |
| Engine session | `play/tomb_gm/domain/session.py` — `start_session` | Clears save slot + `active.json`; unrelated to app JSON |
| Live repro | `app/session_state.json` | Mid-creation `SKILLS` block after `new game` in input history — stale persistence class |
| Batch siblings | APP-014 (session end before wipe), APP-016 (engine snapshot on save), APP-018 (continue restores creation) | APP-015 should clear creation block early; APP-014 reduces setup failures that skip clear |

## Code-path traces

### Happy path: `new game` from mid-creation

1. Entry: `App._submit` → `_process_turn("new game")` → queue `clear_narration`; worker calls `orchestrator.process_turn("new game")`.
2. `setup_new_game()`:
   - `bridge.wipe_all_data()` — SQLite campaigns/sessions/characters cleared; **`session_state.json` untouched**.
   - `bridge.init()` → `campaign_new("salt-road")` → `session_start("salt-road")`.
   - **Then** `self.history.clear()`, `self.creation = CreationState(active=True, step="NAME")`, `_delete_save_file()`.
3. `_creation_turn("[SYSTEM: New game started…]")` — LLM narration for NAME step.
4. Exit: `App._process_turn` `finally` → `_save_session()` writes fresh file with `creation_state` at NAME (or `null` if inactive).
5. In-memory and on-disk creation aligned at NAME on success.

### Failure path: stale block survives

1. Same entry through `wipe_all_data()` / `init()`.
2. `campaign_new()` returns `{"ok": False, "error": …}` where error does **not** contain `"already exists"`.
3. `setup_new_game` **returns early** (orchestrator.py ~355–356) — **no** `creation` reset, **no** `_delete_save_file`.
4. `process_turn` returns `"Could not start game: …"` — in-memory creation still at prior step (e.g. SKILLS); `session_state.json` unchanged.
5. `_save_session` in UI `finally` still runs (error narration present) — **rewrites stale `creation_state`**.
6. Exit: disk + memory both stale; `_is_mid_creation_resume_failure()` continues to read old block on subsequent `load game`.

### Recovery probe reads uncleared disk block

1. Entry: `process_turn("load game")` → `session_resume()` fails (`no save session found`).
2. `_resume_failure_message` → `_is_mid_creation_resume_failure()`.
3. Checks (ordered): `self.creation.active` → engine `awaiting == CHARACTER_CREATION` + empty roster → **read `session_state.json`**.
4. If file has `creation_state.active` or `step != "NAME"`, variant B mid-creation copy is shown even when player intended a wipe via `new game` that failed or only partially ran.
5. Exit: stale creation block on disk directly affects player-facing recovery (APP-071 scope).

### UI load path (regression context)

1. `load game` queues `_load_session()` on main thread.
2. `_load_session` → `import_creation_state(data.get("creation_state"))` then `_sync_creation_from_status()`.
3. If creation block not cleared before load, UI restores old FSM step from file when engine resume succeeds with empty roster (APP-018 territory).
4. APP-015 focus: ensure `new game` clears block so load never sees pre-wipe creation.

### Autosave / threading (secondary)

1. Main thread `_autosave()` every 60s → `_save_session()` reads live `export_creation_state()`.
2. Worker thread runs `setup_new_game` synchronously at start of `process_turn`; creation reset happens before `_creation_turn` LLM wait.
3. Risk: if creation reset stays at end of `setup_new_game`, periodic autosave during a **slow** or **failed** setup could persist stale block — mitigated by clearing block **first** in `setup_new_game`.

## Existing specs & docs

- Ticket domain spec: [`tmp/app-session-persistence-spec.md`](../../app-session-persistence-spec.md) — documents `creation_state` in save schema, `setup_new_game()` wipe, problem logs (partial creation + empty roster), test "`new game` from stuck partial creation → clean NAME step", open APP-014–APP-020 checklist.
- Master registry: [`tmp/app-master-spec.md`](../../app-master-spec.md) — Session persistence row.
- Character creation spec: [`tmp/app-character-creation-spec.md`](../../app-character-creation-spec.md) — owns FSM; persistence clear is session-persistence concern.
- Player README: [`app/README.md`](../../../app/README.md) — mentions autosave/resume; APP-020 will document stuck → `new game` recovery.
- Related tickets: APP-014 (end session before wipe — reduces setup failures), APP-016 (add fields to save — strengthens need for surgical clear vs whole-file delete), APP-018 (restore creation on continue), APP-071 (variant B uses disk creation signals).

## Tests & commands

```bash
# Existing creation + resume tests (no disk creation_block assertion today)
python -m pytest app/tests -q -k "creation_flow or session_resume"
python -m pytest play/tomb_gm/tests -q -k session

# Suggested new test (PM/Dev): mid-creation → write session_state.json with SKILLS block
# → process_turn("new game") → assert file missing OR creation_state is null/fresh NAME
# → assert orchestrator.creation.step == "NAME"

# Manual repro
cd app && python main.py
# 1. new game → advance to race/class/skills
# 2. Inspect app/session_state.json — creation_state.step should not be prior step after new game
# 3. From stuck partial creation, new game → clerk asks for name (NAME), not prior step
```

No existing `app/tests` case asserts on-disk `creation_state` after `new game`. Domain spec lists the scenario but it is untested.

## Risks & unknowns

- **Late clear ordering:** Creation block cleared only after engine restart; crash or early return between wipe and `_delete_save_file` leaves empty engine + stale JSON — core stuck-state class from spec § Problem.
- **Early return on `campaign_new` failure:** Documented failure mode; without upfront clear, AC not met.
- **APP-014 coupling:** If `session_start` fails until prior session is ended, more paths may skip end-of-function clear; APP-015 should clear creation block **before** fragile engine steps or on **every** `new game` attempt regardless of engine outcome.
- **APP-016 interaction:** Engine status snapshot will add non-creation fields to `session_state.json`; whole-file delete may remain OK but AC wording favors explicit `creation_state: null` / fresh NAME template rather than assuming unlink.
- **Test isolation:** `session_state.json` path is hardcoded under `app/` (orchestrator + ui); pytest uses isolated engine workspace but shares app save path — tests must use tmp path or cleanup to avoid polluting dev save (see live `app/session_state.json`).
- **Whole-file delete vs surgical clear:** PM must choose: keep `_delete_save_file` + add early `_clear_creation_block`, or replace with read-modify-write that nulls only `creation_state` (and possibly `orchestrator_history` creation messages).
- **UI layer:** Ticket Expected files say "app/session persistence layer" — primary fix in orchestrator; optional UI hook on `clear_narration` is secondary if orchestrator always clears first.

## Raw notes

- `setup_new_game` clear is last, not first:

```348:361:app/gm/orchestrator.py
    def setup_new_game(self, campaign_slug: str = "salt-road") -> dict:
        """Wipe session/campaign data and start completely fresh. World corpses persist."""
        self.bridge.wipe_all_data()
        self.bridge.init()
        result = self.bridge.campaign_new(campaign_slug, campaign_slug.replace("-", " ").title())
        if not result.get("ok") and "already exists" in result.get("error", ""):
            pass
        elif not result.get("ok"):
            return result
        session = self.bridge.session_start(campaign_slug)
        self.history.clear()
        self.creation = CreationState(active=True, step="NAME")
        self._delete_save_file()
        return session
```

- Disk probe for mid-creation (uses stale file):

```308:318:app/gm/orchestrator.py
        save_path = Path(__file__).resolve().parents[1] / "session_state.json"
        if not save_path.exists():
            return False
        try:
            data = json.loads(save_path.read_text(encoding="utf-8"))
            creation_data = data.get("creation_state") or {}
            if creation_data.get("active"):
                return True
            step = creation_data.get("step")
            if step and step != "NAME":
                return True
```

- UI persists creation block on every save:

```415:417:app/ui/app.py
            "creation_state": (
                self._orchestrator.export_creation_state() if self._orchestrator else None
            ),
```

- Live file shows mid-creation block (`step: "SKILLS"`, name `Flupps`) with `"new game"` in `input_history` — evidence that a prior new-game attempt did not leave a clean NAME-only block (or autosave continued after partial flow).
- Domain spec problem strings (`active session already exists`, `campaign already has an open session`) are **not** present in current `play/tomb_gm` sources — likely legacy logs; APP-014 addresses session lifecycle regardless.
- `_delete_save_file` only unlinks; does not satisfy "explicitly clear creation block" if file is recreated before reset or if partial fields must persist (APP-016).
