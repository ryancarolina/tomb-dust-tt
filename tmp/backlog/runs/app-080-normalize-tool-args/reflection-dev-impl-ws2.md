# Reflection: Dev impl WS2 — APP-080

**Date:** 2026-05-21  
**Stream:** WS2 — Orchestrator wire + cleanup  
**Agent:** Dev  
**Files:** `app/gm/orchestrator.py`

## What shipped

- Import `normalize_tool_args`, `validate_tool_args` from `gm.tool_args`.
- Wired normalize → validate → dispatch at all three `json.loads` tool-call sites:
  - `_creation_llm_loop` — `set_creation_choice` path
  - `_combat_llm_loop_inner` — `combat_action` path
  - `_llm_loop` — general exploration/tools path
- Removed ad-hoc `enter_dungeon` `site_id` → `site_address` rewrite in `_execute_tool`; alias now only in `tool_args._normalize_enter_dungeon`.
- `log_tool_call(fn_name, args, result)` receives post-normalize `args` at each site.

## Wire pattern (identical at each site)

```python
args = json.loads(...)
except JSONDecodeError:
    args = {}
args = normalize_tool_args(fn_name, args)
if err := validate_tool_args(fn_name, args):
    result = {"ok": False, "error": err}
else:
    result = ...  # existing handler
```

Creation/combat loops still reject wrong tool names before validate (unchanged guard messages).

## Verification

| Check | Result |
|-------|--------|
| `rg "site_id.*site_address\|pop(\"site_id\")" app/gm/orchestrator.py` | no matches |
| `pytest tests/test_tool_args.py -v` | 15 passed |

## Pytest results

```text
cd app && python -m pytest tests/test_tool_args.py -v
15 passed in 0.65s
```

## Out of scope (ticket release)

- `tmp/app-llm-orchestrator-spec.md` changelog + validate wire step
- `tmp/app-gamebridge-spec.md` cross-link confirm
- `tmp/app-master-spec.md` owns row
- Full `app/tests/` suite gate (workstreams § WS2 optional broader gate)
- `log_tool_arg_coerced` telemetry (APP-034)

## Risks / notes

- `_dispatch_like_llm_loop` in tests now matches production `_llm_loop` contract; no test edits required.
- Tools not in v1 whitelist still passthrough normalize; validate returns `None` — bridge may still error on bad types for unlisted tools (unchanged).
- WS2 did not run full `app/tests/` per user request (single-file gate only).

## Done when (WS2 gate)

```bash
cd app && python -m pytest tests/test_tool_args.py -q
rg "site_id.*site_address|pop(\"site_id\")" app/gm/orchestrator.py  # expect empty
```

Met.
