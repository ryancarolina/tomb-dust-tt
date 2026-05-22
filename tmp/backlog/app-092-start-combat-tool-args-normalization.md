# APP-092: start_combat tool arg normalization (APP-027 R3)

| Field | Value |
|-------|-------|
| **ID** | APP-092 |
| **Type** | bug |
| **Priority** | P1 |
| **Status** | done |
| **Domain spec** | [`app-llm-orchestrator-spec.md`](../app-llm-orchestrator-spec.md) |
| **Closed** | — |
| **Created** | 2026-05-22 |

## Summary

APP-027 R3 specified `normalize_tool_args` / `validate_tool_args` for `start_combat` so empty `monster_specs` fail before bridge dispatch. Implementation was documented in [`app-combat-play-spec.md`](../app-combat-play-spec.md) but **`app/gm/tool_args.py` was not updated** — V5 in `test_combat_monster_validation.py` could not pass.

## Acceptance criteria

- [x] `start_combat` in `_ALLOWED_KEYS`, `_NORMALIZERS`, and `validate_tool_args` (empty/missing specs → `"monster_specs required"`).
- [x] Coerce `monster_specs` from string or list; `include_party` bool default `True`.
- [x] `tools.py` example uses canon monster id (`ash-shade`), not `hollow-knight`.
- [x] Unit tests in `test_tool_args.py`; V5 in `test_combat_monster_validation.py` green.
- [x] Domain spec coercion table + changelog updated.

## Expected files

- `app/gm/tool_args.py`
- `app/gm/tools.py`
- `app/tests/test_tool_args.py`
- `tmp/app-llm-orchestrator-spec.md`
- `tmp/app-combat-play-spec.md` _(changelog only — R3 already documented)_

## Dependencies

| Ticket | Relationship |
|--------|--------------|
| APP-027 | Parent — R3 tool-args gate |
| APP-080 | Normalization pipeline pattern |

## Claim / release

```bash
python tmp/backlog/claim_ticket.py APP-092 --task start-combat-tool-args
python tmp/backlog/claim_ticket.py release APP-092 --done
```

## Notes

**Run folder:** `C:/Users/PC/Desktop/development/ttTomb-Dust/tmp/backlog/runs/app-092-start-combat-tool-args`
