# Reflection: Dev — APP-049 implementation plan

**Agent:** Dev (plan phase)  
**Inputs:** PASS `spec.md`, `qa-spec-pass.md`, `research-brief.md`, ticket, domain spec, live code in `app/gm/*`, `app/main.py`, `play/tomb_gm/tests/*`  
**Deliverable:** `plan.md`

## Code review takeaways

| Area | Finding | Plan decision |
|------|---------|---------------|
| `app/main.py` path setup | Inserts `play/` + `build/tools/` only; relies on cwd `app/` for `gm.*` | conftest adds **`REPO/app`** explicitly for repo-root pytest |
| `Orchestrator.__init__` | `create_client()` then `GameBridge()` with no workspace | Patch **`gm.orchestrator.create_client`**; factory-patch **`gm.orchestrator.GameBridge`** before lazy `Orchestrator` import |
| `GameBridge` teardown | No `.close()` method | Fixture teardown: **`bridge.ctx.conn.close()`** |
| Engine helpers depth | `parents[3]` at `play/tomb_gm/tests/helpers.py:8` | App helpers use **`parents[2]`** — called out in plan with anti-copy-paste note |
| `app/tests/` | Absent (0 files) | Greenfield; no migration of existing tests |
| Workspace guard | `_assert_not_play_workspace` on session **start**, not bridge ctor | Confirms post-init swap alone is insufficient; monkeypatch ctor is right default |

## Spec alignment

- Plan follows PASS spec R1–R4 and domain spec § App test package / § Fixture inventory verbatim.
- Smoke test intentionally avoids `orchestrator` fixture to keep APP-049 gate fast and independent of OpenRouter stub shape beyond fixture presence.
- Domain spec changelog deferred to **ticket close** per user instruction and backlog workflow.

## Implementation risks I’m flagging for impl QA

1. **Collection-time imports:** Any accidental `import gm.orchestrator` in `conftest.py` at module level (e.g. for typing) would bind `create_client` before `mock_openrouter_client` runs — plan restricts orchestrator import to inside fixtures after patch.
2. **GameBridge patch as callable:** `Orchestrator` uses `GameBridge()` — patched name must be **callable**, not a subclass-only patch, unless a small factory class with `__new__` is used; plan documents lambda/factory pattern.
3. **Minimum swap pattern:** Documented as fallback only; QA impl should verify preferred path in actual conftest.

## Open questions (none blocking plan)

- `app_config` session vs function scope: spec allows either; plan picks **function** for consistency — no behavioral difference for YAML load.
- Whether to add `utc_now` / `seed_campaign` to helpers for parity: deferred until APP-057 needs them.

## Handoff

**Ready for:** QA plan PASS → implementation workstreams  
**Impl agent should:** Implement files in plan order; run both pytest commands; prefer GameBridge factory monkeypatch; do not edit domain spec until `release --done`.
