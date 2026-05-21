# Spec: APP-024-block-site-fiction

**Status:** draft  
**backlog_ticket:** APP-024  
**ticket_path:** [tmp/backlog/app-024-block-site-fiction-without-enter-tool.md](../../app-024-block-site-fiction-without-enter-tool.md)  
**domain_spec:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md)  
**registry_gap:** false (echo research-brief)  
**Domain specs touched:** `tmp/app-exploration-delve-spec.md`

## Problem

Exploration narration from `_llm_loop` is returned raw to `_emit_narration` with **no post-process gate** for site entry. `system_prompt.py` forbids narrating entry without tools, but when the model skips tools, calls failing tools (`set_phase(delve)`, bad `enter_dungeon` args), or hits the **`all_failed and content`** early return (orchestrator L1999–2006), success prose still reaches the player — often prefixed only by `[Mechanics failed — …]`.

Engine persistence stays `party.mode=surface` while fiction describes crossing a threshold, torchlit corridors, etc. Creation has code-owned sanitizers and drift logging; combat hard-gates tools; exploration has neither.

**Evidence:** domain spec § Problem — GM narrated entering crypt without tool commit; session JSONL cited in ticket (gitignored).

## Goals

- **Mechanical truth for site entry:** player must not see site-interior / threshold-crossing fiction unless the **current turn's** `_llm_loop` chain includes a successful (`ok: true`) `enter_dungeon` **or** `site_enter`.
- Gate applies on **surface** turns only — do not block legitimate in-dungeon / in-site room narration.
- Close the **`all_failed + content`** leak path for entry fiction, not only final narration post-process.
- Optional drift telemetry when strip fires (mirror creation `premature_exploration_phase` class).

## Non-goals

| Deferred | Ticket / note |
|----------|----------------|
| Hint correct tool on failed `set_phase(delve)` | [APP-022](../../app-022-hint-enterdungeon-on-failed-setphasedelve.md) — failure hints only |
| Code-owned exploration status footer / bracket strip | [APP-077](../../app-077-code-owned-exploration-status-footer.md) — complementary; see § APP-077 coordination |
| Combat failure narration content leak | [APP-028](../../app-028-combat-tool-failure-narration.md) — parallel class, out of scope |
| Prompt-only fix (`system_prompt.py` alignment) | Out of ticket Expected files; may follow separately |
| Blocking travel fiction without `world_travel` | Out of scope — this ticket is site **entry** only |
| Engine / bridge entry logic changes | `play/tomb_gm` unchanged |

## Requirements (summary)

Full behavior and test contracts: domain spec § **Site-entry fiction gate (APP-024)**.

| ID | Summary | Locus |
|----|---------|-------|
| **E1** | Track **`entry_committed_this_turn: bool`** across depth-0 `_llm_loop`: initialize `False` at loop start; set **`True` on first** successful (`ok: true`) **`enter_dungeon` or `site_enter`** and **never clear** within the turn. **Do not** infer commit from final `_last_tool_results[tool_name]` — that dict **overwrites per name** on each call (`orchestrator.py` L1978); a success followed by a failed retry of the same tool would leave `ok: false` in the dict while entry already committed | `orchestrator.py` `_llm_loop` |
| **E2** | **Gate active when** engine `party.mode == "surface"` at narration compose time **and** `entry_committed_this_turn == False` | `orchestrator.py` `process_turn` post-`_llm_loop` |
| **E3** | **Gate bypass when** engine `party.mode in ("dungeon", "site")` at compose time **or** E1 satisfied — interior room/move narration allowed without re-entry tools | compose helper caller |
| **E4** | **`sanitize_premature_site_entry_flavor(text, *, gate_active: bool) -> str`** — when `gate_active`, remove/strip site-entry flavor (threshold crossing, interior reveal, false in-dungeon status claims while still on surface); preserve non-entry surface prose where possible | new helper (orchestrator or shared module — ticket allows orchestrator only) |
| **E5** | Wire sanitizer on **every player-visible exploration return** from `_llm_loop`: final text-only return **and** the **`all_failed and content`** early return (L1999–2006) — **do not** return raw entry fiction behind failure banner | `orchestrator.py` `_llm_loop` |
| **E6** | When E4 strips all flavor and gate was active, emit minimal **code-owned** refusal line (document exact copy in domain spec); if turn had failed entry/`set_phase` tools, line must not imply success | compose fallback |
| **E7** | Optional: `log_exploration_drift` / extend `_check_creation_drift` with `premature_site_entry` when strip fires — **telemetry only**, does not replace E4 | `orchestrator.py` / `logger.py` if added |
| **E8** | **Dual entry tools:** E1 treats **`enter_dungeon` and `site_enter` equally** — either successful commit authorizes entry fiction; do not assume only `mode=dungeon` | E1 + tests |
| **E9** | **APP-077 coordination:** APP-024 site-entry strip runs **before** any future `_compose_exploration_narration` footer append; shared compose entry point documented in domain spec so both tickets compose in one order | domain spec § coordination |

### Entry commit vs engine mode (clarifies ticket AC)

Ticket AC: entry is authorized iff the **current turn's tool chain includes** a successful (`ok: true`) `enter_dungeon` or `site_enter` — **not** "last tool call of any name" and **not** the final `_last_tool_results` slot for that tool name.

A later failed retry of the same entry tool, or a later failed `search_site` / `set_phase`, must **not** revoke an earlier successful entry on the same turn. E1's sticky flag (or an equivalent full-chain scan of per-turn tool results) satisfies this; dict lookup alone does not.

At compose time, if entry succeeded, engine mode is typically already `dungeon` or `site` — E3 bypass applies.

### `all_failed + content` (primary leak)

When `all_failed and content` at L1999–2006:

1. Compute `gate_active` from **pre-turn** surface mode + E1 (`entry_committed_this_turn`).
2. Run E4 on `content` before prepending failure banner.
3. Player must not see interior/entry success prose when gate was active — banner + safe surface text only.

## Acceptance criteria mapping

| Ticket AC | Spec / test |
|-----------|-------------|
| Block site-entry fiction unless current turn's tool chain includes successful `enter_dungeon` / `site_enter` (`ok: true`) | E1–E6 — domain spec § Site-entry fiction gate; tests below |
| Entry commit survives success-then-failed-same-tool in one turn | E1 sticky flag — `test_success_then_failed_enter_dungeon_retains_fiction` |
| (implicit) no regression in dungeon/site interior play | E3 — `test_site_entry_gate_bypass_when_in_dungeon` |
| Spec sync on close | Domain spec changelog |

## Test plan

```bash
python -m pytest app/tests/test_exploration_site_entry_gate.py -q   # new per domain spec
python -m pytest app/tests/ -q -k "not exploration_site_entry"      # regression slice
python -m pytest play/tomb_gm/tests/test_extraction_slice.py -q     # engine entry unchanged
```

**Primary new tests** (`app/tests/test_exploration_site_entry_gate.py` — mock LLM / patched `_llm_loop`):

| Test | Setup | Pass |
|------|-------|------|
| `test_surface_no_tool_entry_fiction_stripped` | `party.mode=surface`; mock returns content-only entry prose ("You step into the crypt…") with no tool_calls | Output has **no** entry/interior markers; engine still `surface`; optional code-owned refusal present |
| `test_surface_failed_enter_dungeon_no_entry_fiction` | Mock calls failing `enter_dungeon` + entry success `content`; hits `all_failed and content` path | Banner present; **no** entry success prose after E4 |
| `test_surface_successful_enter_dungeon_allows_fiction` | Mock successful `enter_dungeon` (`ok: true`) then entry prose; engine `mode=dungeon` | Entry/interior prose **retained** |
| `test_success_then_failed_enter_dungeon_retains_fiction` | Mock **successful** `enter_dungeon` then **failed** `enter_dungeon` retry + entry prose in same turn; engine `mode=dungeon` | Entry prose **retained** — E1 flag sticky; gate must **not** strip because final `_last_tool_results["enter_dungeon"]` is `ok: false` |
| `test_successful_site_enter_allows_fiction` | Mock successful `site_enter` (`ok: true`); engine `mode=site` | Entry prose retained — E8 dual-tool path |
| `test_site_entry_gate_bypass_when_in_dungeon` | Turn starts `mode=dungeon`; mock returns room description without entry tools | Prose **unchanged** — E3 bypass |
| `test_sanitize_premature_site_entry_flavor_unit` | Direct helper call with marker fixtures | Entry segments removed; benign surface travel prose retained |

Use monkeypatch `create_client` / stub `_execute_tool` — default mock narration must not mask leaks.

## Affected paths

_Must match or subset of ticket **Expected files**._

- `app/gm/orchestrator.py` — E1–E7, `_llm_loop` early-return fix, compose wiring in `process_turn`
- `app/tests/test_exploration_site_entry_gate.py` — seven mock-LLM / unit tests per table above

## Human playtest hints (Stage 7)

_QA expands into `human-test-plan.md`; PyGame `cd app && python main.py`._

- **Surface, wrong tool:** At Registry hub / surface near Breley Undercrypt, say "I enter the crypt." If model skips tools or only calls failing `set_phase(delve)`, narration must **not** describe crossing the threshold or torchlit interior; engine status still shows surface location.
- **Surface, failed enter:** Model calls `enter_dungeon` with bad args — `[Mechanics failed — …]` may appear but **no** success entry prose beneath it.
- **Happy path:** Model calls successful `enter_dungeon(site_address=…)` — entry fiction allowed; map/mode reflects dungeon/site.
- **Already inside:** From dungeon room, "I search the alcove" — normal interior narration without re-calling entry tools.
- **Regression:** Travel `32-C` → adjacent cell still works; no over-aggressive strip of wilderness prose.

## Pointers

- **Research:** [research-brief.md](./research-brief.md) — leak paths, dual tools, APP-077/APP-022
- **Domain truth:** [tmp/app-exploration-delve-spec.md](../../../app-exploration-delve-spec.md) — § Site-entry fiction gate (APP-024)
- **Mechanical truth:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) § Mechanical truth
- **Related:** APP-077 (footer — after APP-024 strip in compose order), APP-022 (hints), APP-028 (combat leak class)

## Changelog

| Date | Change |
|------|--------|
| 2026-05-21 | Initial PM draft — surface-only gate, dual entry tools, all_failed path, APP-077 coordination note |
| 2026-05-21 | PM r2 — E1 sticky `entry_committed_this_turn` (not `_last_tool_results` final slot); ticket AC aligned; regression test success-then-failed-same-tool; test file on Expected files |
