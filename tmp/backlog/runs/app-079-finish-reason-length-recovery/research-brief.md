# Research Brief: APP-079-finish-reason-length-recovery

**Date:** 2026-05-21  
**Question:** Where does `finish_reason: length` surface today, what player-visible harm remains after APP-072/073 strippers, and how should a central recovery policy wire in without fighting APP-083’s verify→retry gate?

**backlog_ticket:** APP-079  
**ticket_path:** tmp/backlog/app-079-finish-reason-length-recovery-policy.md  
**domain_spec:** tmp/app-llm-orchestrator-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-llm-orchestrator-spec.md`](../../../app-llm-orchestrator-spec.md) is the registered owner for `app/gm/orchestrator.py`, `openrouter.py`, and turn-loop behavior ([`tmp/app-master-spec.md`](../../../app-master-spec.md) § Spec registry — LLM orchestrator). APP-079 expected files are a subset (`orchestrator.py`, optional `logger.py`, tests, orchestrator spec + creation spec cross-link). No new domain spec file is required; PM adds § **`finish_reason: length` recovery** to the existing orchestrator spec and a pointer in `app-character-creation-spec.md` per ticket.

## Summary

The orchestrator **logs** `finish_reason` on every `log_llm_response` call but **never branches** on `"length"` — truncated assistant text is returned and composed as-is. Creation flavor is capped at **`_CREATION_FLAVOR_MAX_TOKENS = 120`** (`_narrate_flavor`), which makes `length` common during table-heavy steps; post-compose mitigations (`strip_flavor_race_table`, `strip_flavor_stats_table`, status-tag strip) remove *some* duplicate tables but not all step types (SKILLS/SCHOOLS/SPELLS/EQUIPMENT — see APP-078) and do not fix cut-off status lines or exploration/combat narration truncated at `config.yaml` **`max_tokens: 2048`**.

Session `app/logs/session-2026-05-20.jsonl` (present locally, gitignored) shows **28** `llm_response` events with `finish_reason: length` out of 1442 responses (~1.9%), overwhelmingly during long creation playtests; exploration/combat samples are thin in that log (3 exploration tool calls total). **`_last_content`** is already maintained in `_llm_loop` for depth-limit and API-error fallback but is **not** consulted when `finish_reason == "length"`.

APP-079 should introduce a single policy helper (ticket name: `handle_finish_reason_length`) called immediately after each `chat_completion` that feeds player-visible prose, with mode-specific discard / one-shot retry / `_last_content` fallback. **APP-083** (batch peer, P0) adds semantic `verify_narration` retries — batch board says length should surface as verify failures where prose still ships; PM must define **retry budget stacking** (079 max 1× length retry vs 083 default 5× verify retries) and whether 079 runs **inside** `narrate_with_verification` or as a pre-verify sanitizer.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Creation flavor LLM | `app/gm/orchestrator.py` | `_CREATION_FLAVOR_MAX_TOKENS = 81`, `_narrate_flavor` (~990–1007), `_creation_flavor_messages` |
| Creation present + compose | `app/gm/orchestrator.py` | `_auto_present_*`, `_compose_creation_narration` (~896–931), `_creation_table_flavor` (skips LLM on error) |
| Post-hoc table defense | `app/gm/creation.py` | `strip_flavor_race_table`, `strip_flavor_stats_table` (~570–623) — **no** generic table strip yet (APP-078 open) |
| Exploration loop | `app/gm/orchestrator.py` | `_llm_loop` (~2021–2144), `_compose_exploration_narration` (~383–388) |
| Combat loop | `app/gm/orchestrator.py` | `_combat_llm_loop_inner` (~1875–1976), `_narrate_only` / `_narrate_text` |
| Dead paths | `app/gm/orchestrator.py` | `_creation_llm_loop` (~1522) — **zero callers** under `app/` |
| API client | `app/gm/openrouter.py` | Passes through `choice.finish_reason` |
| Logging | `app/gm/logger.py` | `log_llm_response` — no `llm_truncation_recovery` event yet |
| Config | `app/config.yaml` | `max_tokens: 2048` for non-creation calls |
| Tests (patterns) | `app/tests/test_creation_tables.py`, `test_creation_flavor_sanitize.py`, `conftest.py` | `_patch_llm_content(..., finish_reason="length")` — assert strip/compose, not recovery policy |
| Session evidence | `app/logs/session-2026-05-20.jsonl` | 28× `length`; ticket cites RACE @ 16:44:41 |
| Batch coordination | `tmp/backlog/runs/batch-board-APP-041-APP-079-APP-083.md` | Parallel impl wave; 079 ↔ 083 retry interaction noted |

## Code-path traces

### A — Creation gated step (code `body` + flavor)

1. **Entry:** `_creation_turn_body` → e.g. `_auto_present_race` / `_auto_present_skills` / `_auto_roll_stats` (`orchestrator.py` ~1018–1399).
2. **Flavor:** `_narrate_flavor(_creation_flavor_messages(...))` or `_narrate_creation_flavor` (ROLL_STATS adds `_sanitize_creation_flavor` on flavor only, not on `finish_reason`).
3. **LLM:** `chat_completion(..., max_tokens=120)`; on success `log_llm_response(content, [], finish_reason)` then **return raw `content`** (~1005–1007).
4. **Body:** `format_*_table()` / `format_roll_stats_table()` + `format_classes_table()` — authoritative.
5. **Compose:** `_compose_creation_narration(flavor, body)` → `strip_llm_status_tags` → race/stats table strips → optional premature-completion sanitize → concat flavor + body + `format_creation_status` footer (~896–931).
6. **Emit:** `_emit_narration` → `log_gm_narration` (~372–374).

**Gap:** Step 3 can return a **partial markdown table** (`finish_reason: length`). Step 5 may leave orphan `\| … \|` rows (APP-078) or truncated inline tags; policy should **discard flavor** when `body` is non-empty (ticket AC) instead of relying on strip alone.

**NAME (flavor-only body):** `_auto_present_name` — `body` is a question string, no table; ticket allows **one** retry with “≤2 sentences, no tables” or static fallback (`orchestrator.py` ~1115–1124).

**Error paths:** `_creation_table_flavor` returns `""` without LLM when `error` set (~1317–1324) — no length issue.

### B — Exploration `_llm_loop` (tool chain → final prose)

1. **Entry:** `process_turn` exploration branch → `_llm_loop(messages, depth=0)` (~883).
2. **LLM:** `max_tokens=self.max_tokens` (from config, default 2048); captures `finish_reason` (~2060–2064) but only logs it.
3. **`_last_content`:** Updated every response: `self._last_content = content or self._last_content` (~2066) — used when `depth > 4` or API error (~2036–2057), **not** for `length`.
4. **Terminal:** `if not tool_calls: return content or self._last_content` (~2068–2069) — truncated final narration can ship.
5. **Post:** `_compose_exploration_narration` — APP-024 site-entry strip only (~383–388); APP-077 footer not in this trace.

**Mid-chain with tools:** Assistant message with truncated `content` + `tool_calls` is appended (~2071–2074); ticket says **no** content-only retry — continue loop, optionally strip table fragments from assistant content before append (policy TBD in PM spec).

### C — Combat `_combat_llm_loop_inner`

1. **Tool loop:** Same pattern as B for depth 0–3 (~1875–1932); `log_llm_response` without `length` branch (~1895).
2. **Early exit:** `if not tool_calls: return content` (~1897–1900) — truncated one-shot narration possible.
3. **Final narrate:** Separate `chat_completion` after mechanical brief (~1966–1974) — **`finish_reason` not read**; returns `content` or `brief` only.
4. **Depth cap:** Uses `_last_content` (~1877) — same as exploration, not length-aware.

### D — `_narrate_only` / combat one-shots

- `_narrate_text` → `_narrate_only` (~1736–1741, ~1503–1520): logs `finish_reason`, returns content; used for combat transitions and monster narration strings.

### E — What does not need length policy (today)

- `_creation_llm_loop` — uncalled; safe to ignore for v1 unless revived.
- Code-only paths (`_auto_finalize`, bridge errors) — no LLM truncation.

## Existing specs & docs

- **Ticket:** `tmp/backlog/app-079-finish-reason-length-recovery-policy.md` — recovery matrix, `handle_finish_reason_length`, `llm_truncation_recovery` log event, tests in `test_llm_truncation_recovery.py`.
- **Domain spec:** `tmp/app-llm-orchestrator-spec.md` — open work lists APP-079; **no** length-recovery section yet.
- **Creation spec:** `tmp/app-character-creation-spec.md` — documents `finish_reason: length` at RACE/ROLL_STATS and APP-072 strip behavior; should reference centralized policy on close (ticket Spec sync).
- **Logging spec:** `tmp/app-logging-qa-spec.md` — `llm_response` only; new event needs changelog row when implemented.
- **APP-072 / APP-073:** Shipped post-hoc strippers; APP-072 explicitly deferred length retry (superseded by 079 for policy, not necessarily delete stripper).
- **APP-078:** Open generic table strip — **defense in depth** if truncated table slips past discard (ticket dependency).
- **APP-083:** P0 mechanical-truth gate — `narrate_with_verification` with up to 5 verify retries; **does not mention APP-079** in ticket body; batch board says coordinate. Phase 1 targets creation flavor wiring — same call sites as 079 (`_narrate_flavor` / compose).
- **APP-032:** Transport/API retry — orthogonal.
- **AGENTS.md:** Spec drift policy; orchestrator spec update required on close.

## Coordination with APP-083 (verify → retry)

| Concern | APP-079 (this ticket) | APP-083 |
|---------|----------------------|---------|
| Failure signal | Provider `finish_reason == "length"` | `verify_narration(prose, TurnTruth)` violations |
| Primary fix | Discard truncated flavor when code `body` exists; bounded retry for flavor-only / empty final prose | Inject truth pre-call; reject wrong catalogs/outcomes |
| Retries | Ticket: **max 1** per turn for length | Default **5** (`NARRATION_VERIFY_MAX_RETRIES`) |
| Overlap | Truncated fake spell/school **tables** may be both `length` and verify **catalog/table** fail | 083 Phase 1 subsumes APP-078/082-style rules |

**Recommended PM decision (research, not spec):**

1. **Creation + code body:** 079 discards flavor on `length` **before** compose; 083 verify runs on surviving flavor (often empty) — low double-retry risk.
2. **Creation NAME / flavor-only:** 079 may do one “short prose” retry; 083 verify still applies to published text — cap **total** LLM calls per turn in spec.
3. **Exploration/combat final:** 079 handles `length` + `_last_content` fallback; 083 Phase 2–3 wraps the same helper — implement 079 helper signature so 083 can call it inside `narrate_with_verification` without duplicating logic.
4. **Do not** rely on verify alone for `length` with code body: verify may pass on partial benign sentences while leaving truncated `\| Race \|` rows unless table rules are exhaustive.

## Tests & commands

```bash
# Existing creation stubs (length + strip, not recovery policy)
cd app && python -m pytest tests/test_creation_tables.py tests/test_creation_flavor_sanitize.py -q

# New file per ticket
cd app && python -m pytest tests/test_llm_truncation_recovery.py -q

# Broader regression
cd app && python -m pytest tests/ -q
```

**Stub pattern:** `app/tests/conftest.py` / `_patch_llm_content` — set `finish_reason="length"` on `MockChoice`; monkeypatch `gm.orchestrator.create_client`.

**Ticket AC mapping:**

| AC | Suggested test focus |
|----|---------------------|
| Creation compose + partial `\| Race \|` in length flavor | Mock `_narrate_flavor` → `length` + table fragment; assert single race header from `format_races_table` |
| `_narrate_flavor` short content + length | Assert `discard_flavor` / retry / fallback per step policy |
| SKILLS integration | `finish_reason: length` on skills present; full code `format_skills_table` visible, no truncated LLM table above |

## Risks & unknowns

- **Double retry / cost:** 079 (1×) + 083 (5×) on same turn without a shared budget inflates latency and spend — must be specified before implementation.
- **Implement order in batch:** 079 can land a standalone helper used from `_narrate_flavor` and `_llm_loop` before 083 Phase 1; 083 refactor must not remove 079 hooks.
- **Mid-tool-chain truncation:** Stripping tables from assistant content before tool results is underspecified; wrong strip could break valid tool-arg markup (low risk if tables only).
- **`_last_content` staleness:** Exploration/combat may return content from an **earlier** depth after `length` on final call — policy should define when `_last_content` is “good” (e.g. only if prior `finish_reason == stop"`).
- **Combat final `chat_completion`:** Second call at ~1966 has no `length` handling today — easy to miss in impl if only `_narrate_flavor` is patched.
- **Provider variance:** OpenRouter/Gemini may emit `length` with non-empty but unusable prose; ticket’s “&lt; N chars” threshold not defined in code yet.
- **APP-078 overlap:** Generic stripper may mask missing discard policy in tests — AC should assert **policy action** (log `llm_truncation_recovery`) not only absence of duplicate headers.
- **Session log drift:** Ticket cites 25× `length`; 2026-05-20 log analysis shows **28×** — treat as same class of failure.

## Raw notes

- `grep finish_reason orchestrator.py`: five `log_llm_response` sites; only `_llm_loop` assigns `finish_reason` to a local variable (~2062).
- `_narrate_flavor` callers: NAME, RACE, CLASS, skills/schools/spells via `_creation_table_flavor`, equipment, WORLD_INTRO/FINALIZE chain (~1117–1501).
- `_creation_table_flavor` skips LLM on validation error — good reference for “discard without retry.”
- `tmp/analyze_session_log.py` confirms `finish_reason` distribution on 2026-05-20 session.
- Batch: `batch-board-APP-041-APP-079-APP-083.md` — impl wave 1 parallel, no hard deps.
