# Spec: APP-070-block-premature-pre-delve

**Status:** draft (PM round 1)  
**backlog_ticket:** APP-070  
**ticket_path:** [tmp/backlog/app-070-block-premature-pre-delve-narration.md](../../app-070-block-premature-pre-delve-narration.md)  
**domain_spec:** [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md)  
**registry_gap:** false (per research-brief)  
**Domain specs touched:** `tmp/app-character-creation-spec.md`

## Problem

First-session **Dumpy** run showed exploration/reception **completion copy** (`Phase: PRE_DELVE`, `Awaiting: RECEPTION_CHOICE`, “registered Delver”) while the FSM stayed on desk steps (`SKILLS` / `SPELL_SCHOOLS`) and `bridge.status()["roster"]` remained empty — no `character_create` tool call. **APP-009** already blocks code from reaching `WORLD_INTRO` without a non-empty roster in `_auto_finalize()`; it does **not** stop thin-LLM **flavor** from inventing false completion prose during gated steps.

`PRE_DELVE` is LLM jargon (not in engine `PHASES`). Legitimate post-finalize reception uses code footer `Phase: preparation` + `Awaiting: RECEPTION_CHOICE` at `WORLD_INTRO` only.

## Goals

- **P0 compose guard:** While `creation.active` or `roster_len == 0`, strip completion markers from flavor before `_compose_creation_narration` ships to the player.
- **P0 drift:** Extend `_check_creation_drift` so `premature_exploration_phase` (and optional `premature_completion_copy`) fire when empty roster + false exploration/reception signals appear in narration.
- **P0 test:** Inject bad LLM completion prose on the `SKILLS` turn; assert FSM/roster unchanged and forbidden substrings absent from player narration.

## Non-goals

| Deferred | Ticket |
|----------|--------|
| Flavor/body FSM alignment (race, tables) | APP-069 |
| Stronger bracket tag stripping in flavor | APP-073 |
| Duplicate LLM markdown tables in flavor | APP-072 |
| Re-open APP-009 `_auto_finalize` roster gate | done — APP-070 extends narration layer only |

## Requirements (summary)

Full behavior and test contracts live in the domain spec § **Block premature completion copy (APP-070)**.

| ID | Summary | Domain spec |
|----|---------|-------------|
| **C1** | Compose-time sanitizer on flavor when `creation.active` or empty roster | § Compose sanitization |
| **C2** | Must not strip legitimate `WORLD_INTRO` footer after successful finalize | § Compose sanitization — guard conditions |
| **D1** | Extend `premature_exploration_phase` for `PRE_DELVE` / `preparation` / `RECEPTION_CHOICE` when `roster_len == 0` | § Drift — `premature_exploration_phase` |
| **D2** | Optional `premature_completion_copy` for “registered Delver” prose when `roster_len == 0` | § Drift |
| **T1** | `test_skills_turn_rejects_premature_completion_flavor` (mock bad LLM on SKILLS) | § Tests APP-070 |

## Acceptance criteria mapping

| Ticket AC | Spec / deliverable |
|-----------|-------------------|
| No `PRE_DELVE`, `RECEPTION_CHOICE`, or “registered Delver” until finalize + non-empty roster | C1–C2 (compose); extends APP-009 |
| `_check_creation_drift` flags `premature_exploration_phase` for PRE_DELVE / preparation reception when `roster_len == 0` | D1 |
| Regression test: mock LLM PRE_DELVE prose at SKILLS does not change `creation.step` or show false completion | T1 |

## Implementation pointers (Dev plan)

| Area | Path | Notes |
|------|------|-------|
| Compose | `app/gm/orchestrator.py` | `_compose_creation_narration` — call sanitizer on `flavor` after `strip_llm_status_tags`, before append |
| Sanitizer | `app/gm/creation.py` or `orchestrator.py` | e.g. `_sanitize_premature_completion_flavor(flavor, *, creation, roster_len)` |
| Drift | `app/gm/orchestrator.py` | `_check_creation_drift`, `_PREMATURE_EXPLORE_PHASES` or parallel sets; always pass `roster_len` in payload (already does) |
| Tests | `app/tests/test_creation_flow.py` | Monkeypatch `_narrate_flavor` or `mock_openrouter_client` on turn 5 (`SKILLS` input) |
| Cross-link | APP-009 | `_auto_finalize` ~1018–1026 — do not regress |

## Test plan

```bash
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
```

## Human playtest hints (Stage 7)

- **Dumpy repro:** `new game` → full desk through skills; if using a live model, confirm narration never says “registered Delver” or `PRE_DELVE` until equipment **yes** and roster populated.
- **False yes:** At `SPELL_SCHOOLS`, reply `yes` — must re-show schools table (existing guard); no reception copy.
- **Legitimate end:** After equipment confirm, footer may show `Phase: preparation` + `RECEPTION_CHOICE` only when roster non-empty.

## References

- Research: [research-brief.md](./research-brief.md)
- Related tickets: APP-009 (finalize/roster), APP-069 (flavor FSM), APP-073 (status tags)
- Logging row: `tmp/app-logging-qa-spec.md` (Dumpy PRE_DELVE + empty roster)
