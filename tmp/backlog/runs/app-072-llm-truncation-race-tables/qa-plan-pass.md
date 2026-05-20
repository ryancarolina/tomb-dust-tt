# QA PASS: plan

**Task:** APP-072-llm-truncation-race-tables  
**backlog_ticket:** APP-072  
**ticket_path:** tmp/backlog/app-072-llm-truncation-duplicate-race-tables.md  
**Round:** 1  
**domain_spec_creation:** not_needed (spec QA confirmed `registry_gap: false`)

**Verified:**

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-character-creation-spec.md` § RACE flavor must not duplicate code table, § Tests APP-072)
- [x] Acceptance criteria testable (T1–T6 → locus + tests mapped below)
- [x] Code traces match repo (symbols and call order spot-checked; line refs approximate)
- [x] AGENTS.md / canon compliance (app-only; no `build/` drift)
- [x] Tests/commands listed (`pytest app/tests/test_creation_tables.py`, regression `test_creation_flow.py`)
- [x] Plan files ⊆ ticket Expected files (strict equality on impl set)
- [x] registry_gap matches reality (N/A at plan gate — spec QA confirmed `false`)
- [x] Single sanitizer call site locked (`_compose_creation_narration` after `strip_llm_status_tags`; per qa-spec-pass note)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/gm/creation.py` — `strip_flavor_race_table()` | Yes |
| `app/gm/orchestrator.py` — import, compose hook, RACE instruction | Yes |
| `app/tests/test_creation_tables.py` (new) | Yes |
| `tmp/app-character-creation-spec.md` (changelog on close) | Yes |

Explicit out-of-scope: `conftest.py`, `format_races_table()` column change (APP-059), `get_step_prompt` (APP-074), history omission (APP-069), cross-step table strip — no unauthorized paths.

## Code trace audit

Independent spot-check against live repo:

| Symbol / flow | File | Present | Plan ref |
|---------------|------|---------|----------|
| `_compose_creation_narration` (flavor → status strip → body → footer) | `orchestrator.py` L520–537 | Yes | T3 hook |
| `_auto_present_race` (`races_table_shown`, flavor + `format_races_table()` body) | `orchestrator.py` L694–704 | Yes | T1, T2 |
| `_creation_turn_body` RACE branches (auto-present + re-prompt) | `orchestrator.py` L603–608 | Yes | Flow A/B |
| `_narrate_flavor` / `_CREATION_FLAVOR_MAX_TOKENS` (120, no retry) | `orchestrator.py` L558–575 | Yes | T2 non-goal |
| `_creation_flavor_messages` global “no markdown tables” | `orchestrator.py` L539–556 | Yes | T2 baseline |
| `strip_llm_status_tags` | `creation.py` L532–535 | Yes | hook order |
| `format_races_table` (`Pick **one race**`, `\| Race \| Adjustments \|`) | `creation.py` L544–555 | Yes | T1/T5 fingerprint |
| Chain NAME→RACE via `_handle_creation_response` / `_chain_after_creation_choice` | `orchestrator.py` | Yes | Flow C |
| Dead `_creation_llm_loop` / `get_step_prompt` RACE | — | Not on live path | Out of scope ✓ |

Line numbers differ slightly from plan (`~` notation) — acceptable; topology matches `research-brief.md`, `qa-spec-pass.md`, and live orchestrator.

## Approach (single path)

Plan locks **three layers** with one choke point:

1. **T1** — body unchanged (`err + format_races_table()`).
2. **T2** — RACE-only instruction strengthen (not global flavor rewrite).
3. **T3–T4** — `strip_flavor_race_table` on flavor in `_compose_creation_narration` only (never `body`).

No competing call-site options left open (qa-spec-pass sanitizer note resolved). Compose hook covers all `_auto_present_*` / chain / re-prompt paths without per-method duplication (T6 by design).

## Ticket AC → plan / tests

| Ticket AC | Plan coverage | Test / mechanism |
|-----------|---------------|------------------|
| RACE body only `format_races_table()` | T1 — `_auto_present_race` body unchanged | `test_race_narration_single_table_header` — `Pick **one race**` |
| Flavor ≤2 sentences, no tables (prompt + post-check) | T2 instruction + T3–T4 sanitizer | Prompt change; unit + integration prove post-check |
| Strip `\| Race \|` / token budget → prose only | T3 block strip + T4 line fallback; 120-token cap unchanged; no retry on `length` | `test_strip_flavor_race_table_unit` (truncated header + partial row); integration with `finish_reason="length"` |
| No duplicate race tables in one turn | T5 — compose hook | `count("\| Race \| Adjustments \|") == 1` |
| Mock LLM embedded table test | §4.3 integration stub | `test_race_narration_single_table_header` |
| Spec sync APP-059 on close | §5 changelog; stable fingerprint survives Description removal | Domain § Creation tables RACE row |

### Domain T1–T6 map

| ID | Plan locus | Test |
|----|------------|------|
| T1 | `_auto_present_race` body | Integration |
| T2 | RACE `instruction` string | Integration (violations handled by T3) |
| T3 | `creation.py:strip_flavor_race_table` + compose | Unit + integration |
| T4 | Helper step 5 line fallback | Unit cases |
| T5 | Compose output | Integration count |
| T6 | Compose choke (not `_auto_present_race`-local) | Optional invalid-race turn; design satisfies AC |

## Scope boundary (re-check)

| Topic | Plan handling |
|-------|---------------|
| APP-059 Description column removal | Excluded; fingerprint `\| Race \| Adjustments \|` stable |
| APP-069 history / `_sanitize_creation_flavor` | Excluded; merge-order note in open questions |
| APP-074 dead `get_step_prompt` | Excluded |
| Cross-step `\| Attr \|` / `\| Category \|` strip | Excluded |
| `finish_reason: length` retry | Explicit non-goal |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-072 `in_progress`; domain spec aligned |
| Plan ⊆ Expected files | **PASS** | Four files; no scope creep |
| Code traces | **PASS** | Flows A/B/C verified independently |
| AC testability | **PASS** | T1–T6 + ticket AC mapped to tests |
| Single enforcement path | **PASS** | Compose hook only; no double-strip risk |
| Test commands | **PASS** | New module + regression listed |
| APP-059/069/074 boundaries | **PASS** | Non-goals explicit |

## Notes (non-blocking — impl QA)

1. **Stub patch target:** Plan §4.1 suggests monkeypatching `create_client` factory; `orchestrator` fixture already binds `self.client` at construct time. Impl should override `orchestrator.client.chat.completions.create`, patch `gm.openrouter.chat_completion`, or replace `orchestrator.client` — not rely on a second `create_client` patch alone.
2. **T6 re-prompt turn:** Invalid-race second turn marked optional; compose choke-point still satisfies T6 — impl QA may add if cheap.
3. **APP-069 concurrent merge:** If `_sanitize_creation_flavor` lands same branch, order must be `strip_llm_status_tags` → APP-069 sanitizer → `strip_flavor_race_table` (plan open questions).
4. **Truncated-table heuristic:** Header without separator still stripped — unit test must include ticket evidence shape (header + partial row).
5. **Session claim:** Plan reminds `tmp/.active-ticket.json` before `app/` edits — hooks dependency.

**Verdict:** PASS — ready for Stage 4 (workstreams + implementation).
