# Implementation Plan: APP-027-validate-monster-id-combat

**Status:** draft  
**backlog_ticket:** APP-027  
**ticket_path:** [tmp/backlog/app-027-validate-monster-id-at-combat-start.md](../../app-027-validate-monster-id-at-combat-start.md)  
**domain_spec:** [tmp/app-combat-play-spec.md](../../../app-combat-play-spec.md)  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Add **layered monster-spec validation** before any `combat_state` INSERT:

1. **R1 — Engine `validate_monster_specs`** — sole implementation in `combat.py`; checks non-empty list, format (`MONSTER_SPEC_RE` / `parse_monster_specs`), and JSON file presence.
2. **R2 — Bridge pre-check** — `start_combat` / `start_combat_from_trigger` call R1 before engine; return `{ok: false, error}` without calling engine on fail.
3. **R3 — App `validate_tool_args("start_combat")`** — block missing/empty/malformed `monster_specs` in exploration `_llm_loop` **before** `_execute_tool` (APP-080 pattern; wire already exists at L2573–2576).
4. **R5 — No fiction** — unchanged APP-028 paths consume `{ok: false}`; tests assert `status.combat` null + prefix-only return.
5. **R6 (optional)** — Replace `hollow-knight:1` in `tools.py` example with canon ids.

**Orchestrator:** No wire changes required — `_llm_loop` already runs `normalize_tool_args` → `validate_tool_args` → `_execute_tool`; beat / `pending_start` already delegate to `bridge.start_combat_from_trigger` → R2.

**Out of scope:** mixed-tool fiction (failed `start_combat` + ok tool), beat `MONSTER_ID_RE` content fix, CLI `{ok: false}` contract, domain spec changelog until close, `test_tool_args.py` optional unit (V5 supersedes).

**Stable error string (QA adversarial):** Use **`monster_specs required`** everywhere for empty/missing list — R1 step 1 **and** R3 — so V3/V5 match.

**Files (ticket Expected files only):**

| File | Change |
|------|--------|
| `play/tomb_gm/services/simulation/combat.py` | **R1** `validate_monster_specs`; optional call at top of `start_combat` (defense-in-depth) |
| `app/gm/bridge.py` | **R2** pre-check in `start_combat` |
| `app/gm/tool_args.py` | **R3** `_normalize_start_combat`, whitelist entry, `validate_tool_args` branch |
| `app/gm/tools.py` | **optional R6** example hygiene |
| `app/tests/test_combat_monster_validation.py` | **new** V1–V8 |
| `play/tomb_gm/tests/test_validate_monster_specs.py` | **new** V9 |

_Not in ticket Expected files:_ `app/gm/orchestrator.py` (wire unchanged), `tmp/app-combat-play-spec.md` (sync on close).

---

## Code-path traces (current → planned)

### Flow A — `validate_monster_specs` (R1, new)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `combat.py:MONSTER_SPEC_RE` | Regex at L13 | unchanged — reused by validator |
| 2 | `combat.py:parse_monster_specs` | Raises `ValueError` on bad format/count (L16–27) | unchanged — validator catches and returns `str(exc)` |
| 3 | `combat.py:load_monster_json` | Raises `FileNotFoundError` with `monster JSON not found: {id}` (L30–33) | unchanged — validator checks `path.is_file()` and returns same substring **without raising** |
| 4 | `combat.py:validate_monster_specs` | _(missing)_ | **New** `(content_root, monster_specs) -> str \| None` per domain § R1 |
| 5 | `combat.py:start_combat` | `_spawn_instances` first (L237) then INSERT (L249+) | **Optional:** call `validate_monster_specs` at top; on error `return {"ok": False, "error": err}` — bridge R2 already blocks, engine call is defense-in-depth |
| 6 | `combat.py:_spawn_instances` | parse + load per spec (L122–123) | unchanged fallback if R1 bypassed |

**R1 algorithm (locked):**

```python
def validate_monster_specs(content_root: Path, monster_specs: list[str]) -> str | None:
    if not monster_specs:
        return "monster_specs required"
    for raw in monster_specs:
        if not isinstance(raw, str) or not raw.strip():
            return f"invalid monster spec: {raw!r} (use id or id:count)"
        try:
            pairs = parse_monster_specs([raw.strip()])
        except ValueError as exc:
            return str(exc)
        monster_id = pairs[0][0]
        path = content_root / "data" / "monsters" / f"{monster_id}.json"
        if not path.is_file():
            return f"monster JSON not found: {monster_id} ({path})"
    return None
```

**V9 coverage:** direct unit calls with repo `build/` content root (via `play/tomb_gm/tests/helpers.py` `REPO / "build"` or `play_ctx.config.content_root`).

---

### Flow B — `bridge.start_combat` / `start_combat_from_trigger` (R2)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `bridge.py:start_combat` | Resolves session/campaign → engine `start_combat` (L224–239) | **After** session resolution, **before** engine import/call: `err = validate_monster_specs(content_root, monster_specs)` |
| 2 | same | `except (ValueError, FileNotFoundError)` → `{ok: false, error}` | **Retain** as defense-in-depth after R1 pass |
| 3 | same | On R1 fail | **`return {"ok": False, "error": err}`** — no INSERT, no exception |
| 4 | `bridge.py:start_combat_from_trigger` | `combat already active` guard (L304–306) then `start_combat` (L307) | unchanged order — duplicate guard **before** R1; R1 runs inside delegated `start_combat` |
| 5 | `bridge.status()` | `combat` null on fail | unchanged — V1/V6/V8 assert |

```
bridge.start_combat(monster_specs)
  ├─ _active_session_id / _campaign_slug
  ├─ [NEW] validate_monster_specs(content_root, monster_specs) → err | None
  ├─ if err: return {ok: false, error: err}
  └─ engine start_combat(...) → {ok: true, action: combat_start} | except → {ok: false}
```

**Import:** `from tomb_gm.services.simulation.combat import validate_monster_specs, start_combat` — **no** duplicate regex in `app/gm/`.

---

### Flow C — `validate_tool_args("start_combat")` (R3)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `tool_args.py:_ALLOWED_KEYS` | No `start_combat` entry (L11–21) | Add `"start_combat": frozenset({"monster_specs", "include_party"})` |
| 2 | `tool_args.py` normalizers | No `_normalize_start_combat` | **New:** coerce `monster_specs` to `list[str]` (strip each; drop empty strings after strip); default `include_party=True` via `_coerce_bool` or passthrough |
| 3 | `tool_args.py:validate_tool_args` | No `start_combat` branch — falls through `return None` (L164–191) | **New elif:** missing / not list / empty → `"monster_specs required"`; non-string elements → `"invalid monster_specs entry"` |
| 4 | `orchestrator.py:_llm_loop` | `normalize → validate → _execute_tool` (L2572–2576) | **unchanged** — R3 activates existing gate |
| 5 | On validate fail | `result = {ok: false, error: err}`; bridge **not** called | V5 spy on `bridge.start_combat` |

**R3 vs R1 split:** R3 = structural (required list, string elements). R1 = semantic (regex, JSON exists). Invalid format like `"not a spec"` passes R3 if non-empty string → fails at R2/R1 with `invalid monster spec`.

**Error string:** `"monster_specs required"` for `[]`, missing key, and non-list — matches R1 empty-list return (QA note 1).

---

### Flow D — Orchestrator `_llm_loop` (R4 — wire unchanged)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `_llm_loop` depth 0 | Reset `_last_tool_results`, `_beat_combat_start_failure` (L2507–2510) | unchanged |
| 2 | Tool batch loop | `normalize_tool_args` → `validate_tool_args` → `_execute_tool` (L2572–2576) | R3 blocks bad args **here** |
| 3 | `_execute_tool("start_combat")` | `bridge.start_combat(**args)` (L2684–2685) | R2 runs inside bridge |
| 4 | `all_failed and content` | `_COMBAT_TOOL_NAMES` → prefix only (L2615–2628) | unchanged APP-028 — V8 uses this |
| 5 | `_handle_combat_trigger` | `start_combat_from_trigger` on beat (L2480–2499) | R2 via bridge; V7 real path |
| 6 | `_combat_turn` `pending_start` | `start_combat_from_trigger` (L2266–2273) | same R2 — no live setter today |

```
_llm_loop (exploration)
  for each tool_call:
    normalize_tool_args("start_combat", args)
    validate_tool_args("start_combat", args)     ← [NEW R3 rules]
      └─ err → {ok: false, error} (bridge skipped)
    _execute_tool("start_combat", args)
      └─ bridge.start_combat
           └─ validate_monster_specs           ← [NEW R2/R1]
           └─ engine start_combat
  if all_failed and start_combat failed:
    return "[Mechanics failed — start_combat: …]" only   ← APP-028 (V8)
```

**Beat path (V7):** `_execute_tool("process_beat")` → `_handle_combat_trigger` → `bridge.start_combat_from_trigger(["hollow-knight:1"])` — **does not** pass through `validate_tool_args` (no LLM args); R2/R1 only.

---

### Flow E — Tests V1–V9 (mapping)

| ID | Entry | Mocking | Assert |
|----|-------|---------|--------|
| **V1** | `bridge.start_combat(monster_specs=["hollow-knight:1"])` | Real bridge + `isolated_workspace` (`content_root` → repo `build/`) | `{ok: false}`, error contains `monster JSON not found: hollow-knight` |
| **V2** | `bridge.start_combat(monster_specs=["not a spec"])` | Real bridge | `{ok: false}`, `invalid monster spec` in error |
| **V3** | `bridge.start_combat(monster_specs=[])` | Real bridge | `{ok: false}` before engine; error contains `monster_specs required` |
| **V4** | Valid `grave-ghoul:1` | Real bridge + roster fixture | `{ok: true}` — **skip/xfail** if session/roster setup heavy (defer APP-030) |
| **V5** | `_dispatch_like_llm_loop(orch, "start_combat", {"monster_specs": []})` | Import helper from `app/tests/test_tool_args.py` L33–39; `MagicMock` on `orch.bridge.start_combat` | `{ok: false}`, `monster_specs required`; mock **not** called |
| **V6** | `orch._execute_tool("start_combat", {"monster_specs": ["hollow-knight:1"]})` | Real bridge (bypasses R3 — intentional) | `{ok: false}`; `bridge.status()["combat"]` is None |
| **V7** | `orch._handle_combat_trigger(beat_result)` with `monster_specs: ["hollow-knight:1"]` | Real `start_combat_from_trigger` (no mock); patch `_combat_active_in_db` → False | Failure string matches APP-028 shape; `combat.active` False; `run_combat_monster_turns` not called |
| **V8** | `orch._llm_loop(messages)` single `start_combat` + pre-tool fiction | **Unmocked** `bridge.start_combat`; mock `chat_completion` only | Prefix `[Mechanics failed — start_combat:` + `hollow-knight`; no initiative/charge fiction; `status.combat` null — **not** APP-028 T3 mock |
| **V9** | `validate_monster_specs(build_root, ["hollow-knight:1"])` | None — engine unit | Returns error str with `monster JSON not found: hollow-knight`; valid `grave-ghoul:1` → `None` |

**Fixtures:** Reuse `bridge` / `orchestrator` from `app/tests/conftest.py` (`isolated_workspace` → `content_root: build/`). Engine V9: `REPO / "build"` from `play/tomb_gm/tests/helpers.py`.

**Regression (required after impl):**

```bash
python -m pytest app/tests/test_combat_monster_validation.py -q
python -m pytest app/tests/test_combat_failure_narration.py -k start_combat -q
python -m pytest play/tomb_gm/tests/test_validate_monster_specs.py -q
```

Optional: `python -m pytest play/tomb_gm/tests/test_simulation.py -k unknown_monster -q` (CLI exit code only — not V9).

---

## Task breakdown

### 1. R1 — `validate_monster_specs` — `play/tomb_gm/services/simulation/combat.py`

1. Add public `validate_monster_specs(content_root, monster_specs) -> str | None` after `load_monster_json` (reuse `parse_monster_specs`, mirror error text).
2. **Optional:** At top of `start_combat`, if err := validate_monster_specs(...): return `{ok: False, error: err}` — keeps CLI/engine direct callers consistent without changing CLI contract.
3. Do **not** change `_spawn_instances` or INSERT logic beyond optional early return.

### 2. R2 — Bridge pre-check — `app/gm/bridge.py`

1. Import `validate_monster_specs` alongside `start_combat`.
2. In `start_combat`, after session/campaign resolution, call validator with `self.ctx.config.content_root`.
3. Early return `{ok: False, error: err}` on non-None.
4. Leave `start_combat_from_trigger` as thin wrapper (duplicate-combat guard → `start_combat`).

### 3. R3 — Tool args — `app/gm/tool_args.py`

1. Add `_ALLOWED_KEYS["start_combat"]`.
2. Add `_normalize_start_combat` — list coercion for `monster_specs` (handle single string → one-element list if LLM sends wrong shape; optional minimal).
3. Register in `_NORMALIZERS`.
4. Add `validate_tool_args` branch: empty/missing/non-list → `"monster_specs required"`; non-string elements → `"invalid monster_specs entry"`.

### 4. R6 (optional) — `app/gm/tools.py`

Replace example `['grave-ghoul:2', 'hollow-knight:1']` with canon-only ids (e.g. `grave-ghoul:2`, `ash-shade:1`).

### 5. Tests — TDD order

1. **`play/tomb_gm/tests/test_validate_monster_specs.py`** — V9 (+ happy `grave-ghoul:1` → None, empty list → `monster_specs required`, bad format).
2. Implement R1 until V9 green.
3. **`app/tests/test_combat_monster_validation.py`** — V1–V3, V6–V8, V5 (import `_dispatch_like_llm_loop`); V4 skip.
4. Implement R2 + R3 until app tests green.
5. Run APP-028 regression — error substrings `monster JSON not found: grave-ghoul` / `hollow-knight` must remain valid.

---

## APP-028 / TurnTruth checklist

| Question | Answer |
|----------|--------|
| Emits LLM prose on this path? | V8 — yes; failure path is code-owned `[Mechanics failed — …]` via existing `_llm_loop` strip |
| TurnTruth builder needed? | **No** — validation failure is code-only message, legitimate bypass per turn-truth rule |
| verify_narration before publish? | **No change** — failure short-circuit bypasses LLM narrate on all-failed combat tools |

---

## Risks

| Risk | Mitigation |
|------|------------|
| Error string drift breaks APP-028 T1–T3 | Preserve `monster JSON not found: {id}` substring; run failure narration tests |
| R1/R3 empty-list strings diverge | Single literal `"monster_specs required"` in both |
| V8 flaky if bridge mocked globally | Use `exploration_ready` fixture; mock **only** `chat_completion` |
| V7 needs roster for `include_party=True` | Unknown id fails at JSON check **before** roster spawn — no roster required |
| Double validation perf | Acceptable — combat start is rare |

---

## Close checklist (post-impl, not plan scope)

- [ ] `python tmp/backlog/claim_ticket.py release APP-027 --done`
- [ ] Update `tmp/app-combat-play-spec.md` § APP-027 changelog
- [ ] All V1–V9 green + APP-028 regression green
