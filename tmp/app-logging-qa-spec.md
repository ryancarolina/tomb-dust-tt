# Spec — App Logging & QA

**Parent:** [`app-master-spec.md`](app-master-spec.md)  
**Status:** In progress  
**Owns:** `app/gm/logger.py`, `app/logs/`, `app/tests/`

---

## Spec

### JSONL session logs (`app/logs/session-YYYY-MM-DD.jsonl`)

| Event type | When |
|------------|------|
| `player_input` | Every player line |
| `llm_request` / `llm_response` | Every API call |
| `tool_call` | Every tool name, args, result |
| `gm_narration` | Final text to UI |
| `error` | Exceptions, setup failures |
| `creation_drift` | Narration `Phase:` / `Awaiting:` disagrees with **expected** creation state while drift scope is active (`Orchestrator._check_creation_drift`) — see § `creation_drift` |
| `creation_step` | `{creation.step, roster_len, awaiting, creation.active}` each creation turn (`Orchestrator._creation_turn` finally) |
| `creation_advanced` | `{completed_step, advanced_to}` on every successful `_execute_creation_choice` |
| `creation_finalize` | `{character_create_ok, character_create_error, engine_status}` after `character_create` in `_auto_finalize` |

### `creation_drift` (APP-002, semantics APP-066)

Emitted from `Orchestrator._check_creation_drift` after `_emit_narration` when `_creation_drift_scope()` is true (`creation.active`, or engine `CHARACTER_CREATION` with empty roster).

**Scope:** Active desk creation and resume edges before roster exists. Not a substitute for `creation_step` snapshots (APP-003).

**Awaiting compare (APP-066):**

| Condition | Expected narrated `Awaiting:` | Do **not** compare to |
|-----------|------------------------------|------------------------|
| `creation.active` | `CREATION_STATUS_LABELS[creation.step]` (same as `format_creation_status()`) | Engine `status["awaiting"]` (`CHARACTER_CREATION` is normal) |
| `creation.active` false but scope true (resume edge) | Skip awaiting compare until `creation_state` restores step | Engine alone |

**Reasons:**

| Reason | Meaning |
|--------|---------|
| `awaiting_mismatch` | Footer `Awaiting:` ≠ expected label for current `creation.step` (or unknown-step fallback) |
| `phase_mismatch` | Narrated `Phase:` present and ≠ engine `party.phase` when comparison applies; suppressed for benign omission during desk creation per APP-066 implementation |
| `premature_exploration_phase` | `creation.active` and narrated phase in premature explore set (`_PREMATURE_EXPLORE_PHASES`) |

**Healthy golden path:** No `creation_drift` on every turn solely because granular footer differs from engine `CHARACTER_CREATION`.

**Payload fields (typical):** `step`, `roster_len`, `awaiting` (engine), `creation.active`, `narrated_phase`, `narrated_awaiting`, `engine_phase`, `reasons`; optional `expected_awaiting` after APP-066 impl.

### QA suite

- `app/tests/` — orchestrator, creation flow, bridge smoke, mock LLM golden path.
- CI / local gate: pytest app + tomb_gm + validate_content.

### App test package (`app/tests/`) — APP-049

Scaffolding only; behavioral tests are separate tickets (APP-057, APP-051).

| Path | Role |
|------|------|
| `app/tests/__init__.py` | Package marker for pytest discovery |
| `app/tests/helpers.py` | `REPO = Path(__file__).resolve().parents[2]` (**not** `parents[3]` — engine tests use `parents[3]`), `APP = REPO / "app"`, `PLAY`, `BUILD`, `make_isolated_workspace(base)` — same contract as `play/tomb_gm/tests/helpers.py` |
| `app/tests/conftest.py` | Repo-root `sys.path` + shared fixtures (see below) |
| `app/tests/test_smoke.py` | One test: `bridge` fixture → `status()` dict with `roster` key (avoids empty-collection exit code 5) |

**Import paths (conftest, module level):** Before collection, ensure `sys.path` contains `REPO/app`, `REPO/play`, `REPO/build/tools` where `REPO = Path(__file__).resolve().parents[2]` (mirror `app/main.py` plus explicit `app/` so `import gm.*` works with cwd = repo root).

**Workspace safety:** All bridge/orchestrator fixtures use `isolated_workspace` under pytest `tmp_path`. Never touch `play/workspace` (engine `_assert_not_play_workspace` guard when pytest is loaded). Post-init bridge swap alone is insufficient — see § Orchestrator fixture workspace safety.

**OpenRouter mock (import discipline):** Patch **`gm.orchestrator.create_client`**, not only `gm.openrouter.create_client`. `gm.orchestrator` binds `create_client` at import (`from gm.openrouter import create_client`). **Forbidden:** module-level `from gm.orchestrator import Orchestrator` in `app/tests/**`. Lazy-import `Orchestrator` inside fixtures after `mock_openrouter_client` applies the patch.

**Orchestrator fixture workspace safety:** `Orchestrator.__init__` runs `GameBridge()` before tests can swap `orchestrator.bridge`; default workspace is `play/workspace` and opens SQLite + migrations. **Preferred:** `monkeypatch` `gm.orchestrator.GameBridge` (or `GameBridge.__init__` in fixture scope) so `Orchestrator.__init__` constructs against `isolated_workspace`. **Minimum:** construct stock `Orchestrator`, immediately replace `orchestrator.bridge = GameBridge(workspace=isolated_workspace)`, close default bridge in teardown; do not call orchestrator methods while default bridge still points at `play/workspace`. Constructor injection is out of scope for APP-049.

**Run command (repo root):** `python -m pytest app/tests -q`

### Fixture inventory (`app/tests/conftest.py`)

| Fixture | Scope | Depends on | Behavior |
|---------|-------|------------|----------|
| `isolated_workspace` | function | `tmp_path` | `make_isolated_workspace(tmp_path)` → tmp workspace with `config.yaml` pointing at `build/` |
| `bridge` | function | `isolated_workspace` | `GameBridge(workspace=…)`, `init()`, yield bridge |
| `app_config` | session or function | — | Load `app/config.yaml` dict (LLM/TTS/UI keys) |
| `mock_openrouter_client` | function | `monkeypatch` | Patch **`gm.orchestrator.create_client`** → stub client; no API key. Must run before any import of `gm.orchestrator` / lazy `Orchestrator` import in fixture |
| `orchestrator` | function | `app_config`, `isolated_workspace`, `mock_openrouter_client` | Workspace-safe: monkeypatch `gm.orchestrator.GameBridge` **or** swap bridge immediately after `__init__` + close default bridge in teardown; never yield with bridge on `play/workspace` |

Downstream tickets add test modules only (`test_creation_flow.py`, golden-path helpers); extend this conftest if a new fixture is shared across ≥2 modules.

---

## Task checklist

- [x] JSONL logger with core event types
- [x] **APP-049** — Create `app/tests/` package + `conftest.py` (+ helpers, smoke test per spec § App test package) — **done 2026-05-20**
- [ ] **APP-051** — Golden path fixture with mock LLM
- [ ] **APP-054** — `python -m pytest app/tests` green when full suite exists
- [ ] **APP-057** — `test_creation_flow.py` (depends on APP-049)

**Open work:** [APP-051](backlog/app-051-golden-path-fixture-with-mock-llm.md)–[APP-057](backlog/app-057-test-creation-flow.md) in [`tmp/backlog/README.md`](backlog/README.md) (APP-049 closed).

---

## Tests (this spec owns the gate commands)

```bash
python -m pytest app/tests -q
python -m pytest play/tomb_gm/tests -q
python build/tools/validate_content.py
python -m tomb_gm --workspace play/workspace check
```

**App smoke:** `cd app && python main.py` → `new game` → complete creation → one surface beat → save → resume.

**Done when:**

- CI fails if creation completes without roster or if `validate_content` errors.
- Golden path runs headless without OpenRouter key.

---

## Known issues (from log review)

| Session | Issue |
|---------|-------|
| 2026-05-20 Dumpy | PRE_DELVE UI, empty roster, no JSONL errors (LLM narrated only) |
| 2026-05-19 | Creation step order; delve/combat tool failures |
| 2026-05-18 | SQLite thread; Google 400 malformed transcript |

---

## File map

| Path | Role |
|------|------|
| `gm/logger.py` | Log writers |
| `logs/*.jsonl` | Session transcripts (local) |
| `tests/` | App test package — layout and fixtures per § App test package |
| `tests/conftest.py` | `sys.path`, isolated workspace, bridge, app_config, mock OpenRouter, orchestrator |
| `tests/helpers.py` | `make_isolated_workspace`, path constants |
| `tests/test_smoke.py` | Minimal bridge `status()` smoke (APP-049) |

---

## Changelog

| Date | Change |
|------|--------|
| 2026-05-20 | **APP-049 implemented:** `app/tests/` package (`helpers`, `conftest`, `test_smoke`); fixtures per § Fixture inventory; gate `python -m pytest app/tests -q` green |
| 2026-05-20 | **spec draft APP-049:** § App test package, fixture inventory, task checklist APP-049 specified |
| 2026-05-20 | **APP-049 spec R2 (QA round 1):** `parents[2]` for app helpers; patch `gm.orchestrator.create_client` + lazy-import rule; orchestrator fixture workspace safety (monkeypatch GameBridge or swap+close) |
| 2026-05-20 | Spec created; merged sync-logging + regression-suite content |
| 2026-05-20 | APP-002: `creation_drift` JSONL via `log_creation_drift` + orchestrator drift check |
| 2026-05-20 | APP-003: `creation_step` JSONL via `log_creation_step` + `_creation_turn` finally snapshot |
| 2026-05-20 | APP-004: `creation_advanced` JSONL on successful `_execute_creation_choice` |
| 2026-05-20 | APP-005: `creation_finalize` JSONL with full `bridge.status()` after `character_create` |
| 2026-05-20 | APP-066 spec draft: `creation_drift` compares narrated awaiting to `CREATION_STATUS_LABELS[step]` when `creation.active`, not engine `CHARACTER_CREATION` |
| 2026-05-20 | APP-066 done: `creation_drift` awaiting compare uses expected label from `creation.step`; payload includes `expected_awaiting` when compare runs; golden-path integration test locks drift silence |
