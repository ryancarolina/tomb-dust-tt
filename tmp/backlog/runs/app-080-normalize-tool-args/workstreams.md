# Workstreams: APP-080-normalize-tool-args

**backlog_ticket:** APP-080

| ID | Name | Depends on | Files | Done when |
|----|------|------------|-------|-----------|
| WS1 | Tool-args module | — | `app/gm/tool_args.py` | Helpers, `_ALLOWED_KEYS`, `normalize_tool_args`, `validate_tool_args` exported; module importable |
| WS3 | Unit + integration tests | WS1 | `app/tests/test_tool_args.py` | Plan test matrix green; Holt fixture covered |
| WS2 | Orchestrator wire + cleanup | WS3 | `app/gm/orchestrator.py` | Three loops wired; `enter_dungeon` ad-hoc rewrite removed; full `app/tests/` green |

**Stream count:** 3 — WS1 ships the normalization boundary module (plan step 1); WS3 locks behavior with unit + `_execute_tool` integration tests before orchestrator touch (plan step 2); WS2 wires all three LLM loops and removes duplicate alias logic (plan step 3).

**Implementation order:** WS1 → WS3 → WS2 (plan § Implementation order; qa-plan-pass accepts tests-before-orchestrator gate).

**Out of workstreams (ticket release):** `tmp/app-llm-orchestrator-spec.md`, `tmp/app-gamebridge-spec.md`, `tmp/app-master-spec.md` changelog + AC checkboxes + `claim_ticket.py release APP-080 --done` (plan step 5).

---

## WS1 — Tool-args module

**Scope:** Plan § Module `tool_args.py`, § Allowed-key whitelist, § Tool-specific normalize rules, § Validate rules — new module only; no orchestrator edits.

**Requirements covered:** spec R1, R2, R3 (drop `amount`); plan SPEC-001 (validate separate from normalize), SPEC-002 (whitelist), SPEC-005 (`top_k` wins).

### Implementation order (within stream)

| # | Task | Symbol / detail | Plan ref |
|---|------|-----------------|----------|
| 1 | Markup strip helper | `_strip_tool_markup(s)` — cut at first `</invoke>`, `</parameter>`, `<invoke`, `<parameter`; trim | § Module |
| 2 | Coercion helpers | `_coerce_int`, `_coerce_str`, `_coerce_str_list` | § Module |
| 3 | Whitelist constant | `_ALLOWED_KEYS: dict[str, frozenset[str]]` per v1 table | § Allowed-key whitelist |
| 4 | `normalize_tool_args` | Per-tool branches; never raises; unknown tools → shallow `dict(args)` copy | § Tool-specific normalize |
| 5 | `validate_tool_args` | Returns `"<field> required"` or `None`; not folded into normalize | § Validate rules |

### `_ALLOWED_KEYS` (output keys only)

| `tool_name` | Allowed keys |
|-------------|--------------|
| `remember_fact` | `fact`, `entities`, `importance` |
| `memory_recall` | `query`, `top_k` (legacy `top` consumed, dropped) |
| `fortune_spend` | `character_id` |
| `clock_tick` | `clock`, `segments` |
| `enter_dungeon` | `site_address` |
| `set_creation_choice` | `step`, `value` |
| `combat_action` | `action`, `actor_id`, `target_id`, `weapon_id`, `spell_id` |

### Per-tool normalize summary

| Tool | Rules |
|------|-------|
| `remember_fact` | `fact` str (no markup strip on prose); `entities` list[str]; `importance` int 1–5 default 3 with markup strip on string input |
| `memory_recall` | `top_k` present → canonical; else `top` → `top_k`; **both → `top_k` wins**; `query` str; `top_k` int ≥ 1 default 5; drop `top` |
| `fortune_spend` | `character_id` str + markup strip; drop `amount` and all other keys |
| `clock_tick` | `clock` str; `segments` int 1–100 default 1 |
| `enter_dungeon` | `site_id` → `site_address` when address missing; output `site_address` only |
| `set_creation_choice` | `step`, `value` str |
| `combat_action` | string-coerce present keys |
| Other | Passthrough shallow copy (whitelist not applied) |

### `validate_tool_args` returns

| Tool | Error when |
|------|------------|
| `remember_fact` | empty/missing `fact` → `"fact required"` |
| `memory_recall` | empty `query` → `"query required"` |
| `fortune_spend` | empty `character_id` → `"character_id required"` |
| `clock_tick` | empty `clock` → `"clock required"` |
| `enter_dungeon` | empty `site_address` (post-alias) → `"site_address required"` |
| `set_creation_choice` | empty `step` / `value` |
| `combat_action` | empty `action` / `actor_id` |
| Other | `None` |

### Critical constraints

| Constraint | Detail |
|------------|--------|
| No orchestrator import | `tool_args.py` must not import `orchestrator` |
| Normalize never raises | Coercion failures use defaults; invalid ints → default + clamp |
| Validate separate | Do not merge validate into normalize return type |
| Scalar markup only | v1: no strip on long `fact` prose |
| Optional telemetry | `log_tool_arg_coerced` deferred unless trivial (APP-034) |

### WS1 done when

```bash
cd app && python -c "from gm.tool_args import normalize_tool_args, validate_tool_args"
```

No pytest gate in WS1 — WS3 owns tests. Module must be complete enough for WS3 to import all public symbols.

### Prompt seed for Task subagent (WS1 impl)

```
backlog_ticket: APP-080
ticket: tmp/backlog/app-080-normalize-tool-args-before-dispatch.md
run-folder: tmp/backlog/runs/app-080-normalize-tool-args/
spec: spec.md | plan: plan.md § Module, whitelist, normalize/validate rules | domain spec: tmp/app-llm-orchestrator-spec.md (read only until release)
workstreams: workstreams.md § WS1

Implement WS1 only — app/gm/tool_args.py per plan § Module through § Validate rules.
AGENTS.md: claim APP-080 before app/ edits; no orchestrator.py or test edits.
Write reflection-dev-impl-ws1.md before return.
```

---

## WS3 — Unit + integration tests

**Scope:** Plan § Test plan — new `app/tests/test_tool_args.py`; full matrix green before WS2 touches orchestrator.

**Depends on:** WS1 — `normalize_tool_args`, `validate_tool_args`, and helpers importable from `gm.tool_args`.

**Requirements covered:** spec test plan table; plan Holt regression; SPEC-001 negative validate; SPEC-004 extended normalize tests; SPEC-005 precedence test.

### Fixtures

```python
HOLT_CORRUPTED_IMPORTANCE = (
    '4</importance>\n</invoke>\n<invoke name="enter_dungeon">...'
)
HOLT_REMEMBER_FACT_ARGS = {
    "fact": "<valid quest prose>",
    "entities": ["Marshal Holt"],
    "importance": HOLT_CORRUPTED_IMPORTANCE,
}
```

Copy exact Holt payload from ticket/session evidence; do not depend on gitignored `app/logs/session-2026-05-20.jsonl`.

### Unit — helpers

| Test | Assert |
|------|--------|
| `test_coerce_int_markup_prefix` | `"4</importance>..."` → `4` |
| `test_coerce_int_invalid` | `"abc"` → default `3` |
| `test_strip_tool_markup_truncates_invoke_tail` | tail after `</invoke>` removed |

### Unit — normalize

| Test | Assert |
|------|--------|
| `test_normalize_remember_fact_corrupted_importance` | `importance` is `int` 4; entities `list[str]` |
| `test_normalize_remember_fact_no_typeerror_via_semantic` | normalize then `semantic.remember` — no `TypeError` on clamp |
| `test_normalize_memory_recall_top_k_string` | `"5"` → `5` |
| `test_normalize_memory_recall_legacy_top` | `top: "3"` → `top_k: 3`; no `top` |
| `test_normalize_memory_recall_top_k_wins_over_top` | both present → `top_k` value kept |
| `test_normalize_fortune_spend_drops_amount` | only `character_id` |
| `test_normalize_enter_dungeon_site_id_alias` | `site_id` only → `site_address`; no `site_id` |
| `test_normalize_clock_tick_segments_string` | `"2"` → `2` |

### Unit — validate (minimum v1; add more if cheap)

| Test | Assert |
|------|--------|
| `test_validate_remember_fact_missing_fact` | `{}` after normalize → `"fact required"` |
| `test_validate_memory_recall_missing_query` | `"query required"` |
| `test_validate_fortune_spend_missing_character_id` | `"character_id required"` |

Optional (qa-plan adversarial note): `enter_dungeon` / `clock_tick` validate rows if trivial.

### Integration

| Test | Assert |
|------|--------|
| `test_execute_tool_remember_fact_corrupted_importance_ok` | `_execute_tool("remember_fact", raw_args)` with Holt fixture → `{ok: True}` (mock bridge or minimal orchestrator fixture) |

Use patterns from `test_creation_flavor_sanitize.py` / `test_creation_flow.py` for orchestrator construction.

**Defer (documented):** stringified JSON array for `entities` (SPEC-008); full `_llm_loop` mock chain.

### Test gates (WS3 done when)

```bash
cd app && python -m pytest tests/test_tool_args.py -q
```

WS2 must not start until this gate is green.

### Prompt seed for Task subagent (WS3 impl)

```
backlog_ticket: APP-080
ticket: tmp/backlog/app-080-normalize-tool-args-before-dispatch.md
run-folder: tmp/backlog/runs/app-080-normalize-tool-args/
spec: spec.md | plan: plan.md § Test plan | workstreams: workstreams.md § WS3

Prerequisite: WS1 landed — gm.tool_args complete.
Implement WS3 only — app/tests/test_tool_args.py per plan test matrix + Holt fixtures.
Do not edit orchestrator.py.
Run: cd app && python -m pytest tests/test_tool_args.py -q
Write reflection-dev-impl-ws3.md before return.
```

---

## WS2 — Orchestrator wire + cleanup

**Scope:** Plan § Orchestrator wiring (SPEC-003) — normalize + validate at three `json.loads` sites; remove `enter_dungeon` rewrite in `_execute_tool`; post-normalize args in `log_tool_call`.

**Depends on:** WS3 — `test_tool_args.py` green (plan: tests before orchestrator touch).

**Requirements covered:** spec R4, R5; plan paths A/B (Holt fixed); enter_dungeon alias migration.

### Wire pattern (all three sites)

```python
args = json.loads(...)
except JSONDecodeError:
    args = {}
args = normalize_tool_args(fn_name, args)
if err := validate_tool_args(fn_name, args):
    result = {"ok": False, "error": err}
else:
    result = ...  # existing dispatch
```

Import from `gm.tool_args`: `normalize_tool_args`, `validate_tool_args`.

### Site 1 — `_creation_llm_loop` (~1493–1507)

| Step | After APP-080 |
|------|---------------|
| Parse | unchanged (`JSONDecodeError` → `{}`) |
| Normalize | `normalize_tool_args("set_creation_choice", args)` |
| Validate | before `_execute_creation_choice` |
| Dispatch | unchanged; args already coerced strings |

### Site 2 — `_combat_llm_loop_inner` (~1831–1840)

| Step | After APP-080 |
|------|---------------|
| Parse | unchanged |
| Normalize | `normalize_tool_args("combat_action", args)` |
| Validate | before `_execute_combat_action(**args)` |
| Dispatch | unchanged signature |

### Site 3 — `_llm_loop` (~1969–1976) — critical path

| Step | After APP-080 |
|------|---------------|
| Parse | unchanged |
| Normalize | `normalize_tool_args(fn_name, args)` |
| Validate | before `_execute_tool(fn_name, args)` |
| Dispatch | unchanged |

### Remove duplicate alias

Delete `enter_dungeon` `site_id` → `site_address` rewrite in `_execute_tool` (~2086–2090); normalizer owns migration.

### Logging

`log_tool_call(fn_name, args, result)` logs **post-normalize** args (document in spec on close).

### Out of scope

| Path | Reason |
|------|--------|
| `_remember_player_choice` (~620) | orchestrator-internal; already typed `int`; no `json.loads` |
| `GameBridge` / engine | no bridge markup strip |
| Pre-normalize snapshot in logs | post-normalize only unless APP-034 needs both |

### Test gates (WS2 done when)

```bash
cd app && python -m pytest tests/test_tool_args.py -q
cd app && python -m pytest tests/ -q
```

Confirm no remaining ad-hoc `site_id` rewrite:

```bash
rg "site_id.*site_address|pop\(\"site_id\"\)" app/gm/orchestrator.py
```

Expect alias logic absent from `_execute_tool` (may exist only in comments if any).

### Prompt seed for Task subagent (WS2 impl)

```
backlog_ticket: APP-080
ticket: tmp/backlog/app-080-normalize-tool-args-before-dispatch.md
run-folder: tmp/backlog/runs/app-080-normalize-tool-args/
spec: spec.md | plan: plan.md § Orchestrator wiring, deep paths A/B | workstreams: workstreams.md § WS2

Prerequisite: WS3 green — test_tool_args.py passes.
Implement WS2 only — orchestrator.py three wire sites + remove enter_dungeon rewrite ~2086–2090.
Import normalize_tool_args, validate_tool_args from gm.tool_args.
Run full app/tests/ gates in workstreams.md § WS2.
Write reflection-dev-impl-ws2.md before return.
```

---

## Post-impl (not WS2 — ticket release)

| Doc | Update |
|-----|--------|
| `tmp/app-llm-orchestrator-spec.md` | `validate_tool_args` in Helpers; wire step; `top_k` precedence; APP-080 checklist; changelog |
| `tmp/app-gamebridge-spec.md` | Confirm typed-args cross-link |
| `tmp/app-master-spec.md` | Add `tool_args.py` owns row (SPEC-006) |
| Ticket | AC checkboxes + `release APP-080 --done` |
