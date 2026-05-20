# Research Brief: APP-070-block-premature-pre-delve

**Date:** 2026-05-20  
**Question:** How can LLM creation narration show `PRE_DELVE`, `RECEPTION_CHOICE`, or “registered Delver” while `creation.step` stays on gated desk steps and `bridge.status()["roster"]` is empty — and what code paths must harden to prevent it?

**backlog_ticket:** APP-070  
**ticket_path:** tmp/backlog/app-070-block-premature-pre-delve-narration.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**ticket_status_at_start:** in_progress  

**registry_gap:** false

## Registry gap justification

[`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) already owns `app/gm/creation.py`, creation routing in `app/gm/orchestrator.py`, and documents APP-009 finalize/roster gates plus APP-070 boundaries (§ Ticket boundaries). [`tmp/app-master-spec.md`](../../../app-master-spec.md) registry row **Character creation** points to that spec. APP-070 expected files are a subset of the registered owner. Cross-cutting drift logging is documented in [`tmp/app-logging-qa-spec.md`](../../../app-logging-qa-spec.md); no new domain spec is required.

## Summary

The Dumpy session failure is **narration-only false completion**: the FSM and engine never finalized (`character_create` absent, `roster_len == 0`), but the player saw exploration/reception copy (`Phase: PRE_DELVE`, `Awaiting: RECEPTION_CHOICE`, “registered Delver”). **APP-009** already blocks *code* from advancing to `WORLD_INTRO` without a non-empty roster inside `_auto_finalize()`; it does **not** stop the thin-LLM **flavor** layer from inventing completion prose during earlier steps.

Today’s defenses are partial: `strip_llm_status_tags()` removes bracketed `[Phase:…]` / `[Location:…]` from flavor before compose; the code-owned footer uses `format_creation_status()` (granular `*_INPUT` labels until finalize). `_check_creation_drift()` logs `awaiting_mismatch` when narrated `Awaiting:` ≠ `CREATION_STATUS_LABELS[step]`, and `premature_exploration_phase` only for engine phases `delve|ingress|extract|aftermath` — **not** `pre_delve`, `preparation`, `RECEPTION_CHOICE`, or “registered Delver” body copy. Integration tests stub all flavor as `"Test narration."`, so they cannot regress LLM-invented completion. **APP-070** should add compose-time sanitization and/or drift reasons keyed on `roster_len == 0`, plus a targeted mock-LLM test at `SKILLS` (ticket AC).

`PRE_DELVE` is an **LLM-invented** phase label (not in `play/tomb_gm` `PHASES`); canon reception after finalize uses `Phase: preparation` in the code footer at `WORLD_INTRO`.

## Code map

| Area | Paths | Notes |
|------|-------|-------|
| Creation FSM | `app/gm/creation.py` | `CREATION_STEPS`, `CREATION_STATUS_LABELS`, `strip_llm_status_tags`, `format_creation_status` |
| Turn routing | `app/gm/orchestrator.py` | `process_turn` → `_creation_turn` when `creation.active`; `_llm_loop` blocked (L1545–1547) |
| Compose | `app/gm/orchestrator.py` | `_compose_creation_narration` — flavor strip + code body + code footer |
| Flavor LLM | `app/gm/orchestrator.py` | `_creation_flavor_messages`, `_narrate_flavor` (~120 tokens, no tools) |
| Finalize / roster gate | `app/gm/orchestrator.py` | `_auto_finalize` — `character_create`, roster check (APP-009), `WORLD_INTRO` footer |
| Drift QA | `app/gm/orchestrator.py`, `app/gm/logger.py` | `_check_creation_drift`, `parse_narration_status_line`, `log_creation_drift` |
| Tools | `app/gm/tools.py` | `character_create` removed from LLM tools; finalize is code-only |
| UI suggestions | `app/ui/app.py` | `_extract_suggestions` parses `Awaiting:` inside `[…]` bracket blocks only |
| Stats phase badge | `app/ui/panels/stats.py` | Phase from `bridge.status()["party"]["phase"]`, not narration |
| App integration tests | `app/tests/test_creation_flow.py`, `app/tests/conftest.py` | Golden path; constant mock flavor |
| Engine creation parsers | `play/tomb_gm/tests/test_creation_gating.py` | Parsers/tables only — **no** PRE_DELVE / orchestrator test (spec cites APP-070) |
| Session evidence | `app/logs/session-2026-05-20.jsonl` | Referenced in ticket; **gitignored** — not in workspace clone |

## Code-path traces

### A — Dumpy failure (skills + “yes” → false completion, empty roster)

1. **Entry:** `process_turn` with `creation.active` → `_creation_turn` → `_creation_turn_body` (`orchestrator.py` ~468–469, ~586–658).
2. **Skills commit:** `_handle_creation_response` at `step == "SKILLS"` → `_execute_creation_choice("SKILLS", …)` → `creation.advance()` → typically `SPELL_SCHOOLS` (apprentice + Spellcasting) → `_chain_after_creation_choice` presents schools table same turn (`orchestrator.py` ~768–794, ~854–866).
3. **“Yes” at wrong step:** If player says `yes` at `SKILLS` / `SPELL_SCHOOLS`, `is_equipment_confirm` is caught and re-presents the step table with an error — FSM does **not** advance to `FINALIZE` (`orchestrator.py` ~769–773, ~797–801). Ticket’s `14:10:04` “registered Delver” therefore did **not** come from a successful equipment confirm on current guards (likely **LLM flavor** on a prior turn or pre-hardening build).
4. **Authoritative state:** `creation.step` remains a desk step; `bridge.status()["roster"]` stays `[]`; engine `awaiting` stays `CHARACTER_CREATION` (APP-066).
5. **Narration compose:** Each `_auto_present_*` calls `_narrate_flavor` → `_compose_creation_narration(flavor, body)` → footer `format_creation_status()` → e.g. `Awaiting: SPELL_SCHOOLS_INPUT` (`orchestrator.py` ~520–537, `creation.py` ~538–541).
6. **Leak vector:** If mock/real LLM returns `"You are now a registered Delver. [Phase: PRE_DELVE | Awaiting: RECEPTION_CHOICE]"` in **flavor**:
   - `strip_llm_status_tags` may remove the bracket block (`_LLM_STATUS_TAG_RE` includes `\[Phase:[^\]]*\]`) but **prose** (“registered Delver”) remains.
   - `parse_narration_status_line` may still see `Phase: PRE_DELVE` / `Awaiting: RECEPTION_CHOICE` if tags survive or appear unbracketed in flavor+body.
7. **Drift today:** `awaiting_mismatch` if `RECEPTION_CHOICE` parsed while `creation.active` and step ≠ `WORLD_INTRO`. **`premature_exploration_phase` does not fire** for `pre_delve` or `preparation` (`_PREMATURE_EXPLORE_PHASES` = delve/ingress/extract/aftermath only, `orchestrator.py` ~65, ~216–217).
8. **Emit:** `_emit_narration` → history stores full string shown to player (`orchestrator.py` ~660–662).

### B — Legitimate completion path (contrast)

1. **Entry:** `EQUIPMENT_GOLD` confirm → `_execute_creation_choice` → `advance()` → `FINALIZE` → chain calls `_auto_finalize` (`orchestrator.py` ~839–875, ~969+).
2. **Engine:** `bridge.character_create(...)` + implicit roster; `log_tool_call("character_create", …)` (`orchestrator.py` ~988–1005).
3. **Roster gate (APP-009):** If `not roster` after ok result → stay in creation, error narration, no `WORLD_INTRO` (`orchestrator.py` ~1018–1026).
4. **Success:** `creation.active = False`, `step = WORLD_INTRO`; footer code sets `Phase: preparation` + `Awaiting: RECEPTION_CHOICE` (`orchestrator.py` ~1028–1055). Body includes `**{name}** is registered — …`.

### C — Drift scope and `premature_exploration_phase`

1. **Scope:** `_creation_drift_scope()` true when `creation.active` OR (engine `CHARACTER_CREATION` and empty roster) (`orchestrator.py` ~180–190).
2. **Parse:** `parse_narration_status_line` regex `Phase:\s*([^|\]]+)` and `Awaiting:\s*([^|\]]+)` (`logger.py` ~65–77).
3. **Reasons:** `awaiting_mismatch` (active creation + narrated awaiting ≠ label map); `phase_mismatch` (narrated vs engine party phase); `premature_exploration_phase` (active + narrated phase in `_PREMATURE_EXPLORE_PHASES` only).
4. **Gap vs ticket AC:** No branch for `PRE_DELVE`, `preparation` reception copy, or `RECEPTION_CHOICE` when `roster_len == 0` unless it also triggers `awaiting_mismatch`. No check for “registered Delver” / `is registered` completion phrases in body/flavor.

### D — Exploration loop guard (cannot finalize via tools mid-creation)

1. `_llm_loop` if `creation.active`: return `_creation_turn("[SYSTEM: Finish character creation first.]")` (`orchestrator.py` ~1545–1547).
2. `_execute_tool` during creation: only `set_creation_choice` (`orchestrator.py` ~1652–1660).
3. `character_create` not in `TOOLS` (`tools.py` comment ~203). Historical sessions without these guards could reach PRE_DELVE via tool+LLM path; current tree blocks that.

## Existing specs & docs

- **Ticket:** `tmp/backlog/app-070-block-premature-pre-delve-narration.md` — Dumpy log evidence, three AC (narration gate, drift extension, regression test).
- **Domain spec:** `tmp/app-character-creation-spec.md` — APP-009 finalize gate done; APP-070 boundary table; golden-path `PRE_DELVE not in last`; `"Yes"` at `SPELL_SCHOOLS` → APP-070 test note.
- **Related:** APP-009 (roster after `_auto_finalize`), APP-069 (body/flavor FSM alignment), APP-073 (strip embedded status tags in flavor), APP-066 (engine vs app awaiting), `tmp/app-llm-orchestrator-spec.md` (code state leads narration).
- **Logging:** `tmp/app-logging-qa-spec.md` — known issue row for Dumpy PRE_DELVE + empty roster.

## Tests & commands

```bash
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
```

**Existing coverage:**

| Test | What it proves | Gap for APP-070 |
|------|----------------|-----------------|
| `test_full_creation_apprentice_caster` | End-to-end finalize; roster non-empty; last narration has `RECEPTION_CHOICE` + `Phase: preparation`; **`PRE_DELVE` not in last** | Does not inject bad LLM flavor mid-FSM |
| `test_creation_gating.py` | Parsers, tables, equipment confirm | No orchestrator / PRE_DELVE case (spec defers to APP-070) |

**Ticket AC test sketch:** Monkeypatch `_narrate_flavor` or `mock_openrouter_client` to return completion prose on turn 5 (`SKILLS`); assert `creation.step` still `SPELL_SCHOOLS` (or next desk step), `len(roster)==0`, narration lacks `PRE_DELVE` / `registered Delver` / `RECEPTION_CHOICE` (or drift event logged).

## Risks & unknowns

- **Historical vs current build:** Ticket notes log may predate `character_create` removal from tools; reproduction on current `main` requires live or stubbed LLM returning completion copy — headless golden path alone will not fail today.
- **`PRE_DELVE` vs `preparation`:** Engine canon phase is `preparation`; `PRE_DELVE` is LLM jargon. Drift AC conflates both — implementation must not block legitimate post-finalize `Phase: preparation` footer.
- **Footer vs flavor:** Code footer after finalize intentionally uses `RECEPTION_CHOICE`; guards must key off `roster_len` and `creation.active` / `creation.step`, not blanket-ban substring in successful `WORLD_INTRO` narration.
- **UI phase badge:** Stats panel reads engine `party.phase`, not narration — false `PRE_DELVE` in prose may mislead via suggestion chips (`_extract_suggestions` reads bracket `Awaiting:`) more than phase badge.
- **APP-073 overlap:** Stronger tag stripping may help bracket forms; APP-070 still needs roster-gated completion **prose** and drift reasons ticket lists.
- **Session log unavailable:** Cannot re-verify line-level `creation_advanced` sequence in clone; rely on ticket timestamps + code trace.

## Raw notes

| Symbol | Location | Role |
|--------|----------|------|
| `_PREMATURE_EXPLORE_PHASES` | `orchestrator.py:65` | `delve`, `ingress`, `extract`, `aftermath` only |
| `_check_creation_drift` | `orchestrator.py:192–234` | Logs `creation_drift` with `roster_len` |
| `_auto_finalize` roster check | `orchestrator.py:1018–1026` | APP-009 |
| `strip_llm_status_tags` | `creation.py:532–535` | Bracket Phase/Location/Awaiting lines |
| `CREATION_STATUS_LABELS["WORLD_INTRO"]` | `creation.py:79` | `RECEPTION_CHOICE` (desk steps use `*_INPUT`) |
| `is_equipment_confirm("yes")` | `creation.py` `EQUIPMENT_CONFIRM_RE` | Rejected at SKILLS/SPELL_SCHOOLS with error re-show |

**Recommended implementation axes (for PM/plan, not spec):**

1. **Compose-time guard** in `_compose_creation_narration` or post-flavor helper: when `creation.active` or `roster_len == 0`, strip or replace completion markers (`PRE_DELVE`, `registered Delver`, `RECEPTION_CHOICE` in flavor; optional neutral fallback).
2. **Extend `_check_creation_drift`:** treat `narrated_phase` in `{pre_delve, pre-delve}` or `narrated_awaiting == RECEPTION_CHOICE` with `roster_len == 0` as `premature_exploration_phase` (or new reason `premature_completion_copy`); add `preparation` only when `creation.active` and step ∉ `{WORLD_INTRO}`.
3. **Test:** custom mock LLM content on SKILLS turn per ticket AC; assert FSM + roster unchanged and forbidden substrings absent (or drift logged).
