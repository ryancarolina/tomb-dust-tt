# Drift Check: APP-074-remove-dead-step-prompt

**backlog_ticket:** APP-074  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) | no | § Step content sources (APP-074), § Removed patterns, file map, and changelog **APP-074 done** row match `creation.py` + `orchestrator.py` |
| Run `spec.md` R1–R3 | no | Verified against `creation.py`, `orchestrator.py`, domain spec |
| Ticket [`app-074-remove-dead-get-step-prompt.md`](../../app-074-remove-dead-get-step-prompt.md) | no | All AC checked; status `done`; Closed 2026-05-20 |

## Code ↔ domain spec (APP-074 scope)

| Requirement | Code | Match |
|-------------|------|-------|
| **No** legacy `get_step_prompt()` on live path | `rg "get_step_prompt" app/` → zero matches; no `def get_step_prompt` in `creation.py` | yes |
| **Body** from `format_*_table` / `format_equipment_summary` via `_auto_present_*` | `orchestrator.py` imports `format_races_table`, `format_roll_stats_table`, `format_classes_table`, `format_skills_table`, `format_schools_table`, `format_spells_table`; `_auto_present_race` sets `body = err + format_races_table()` | yes |
| **Flavor** thin `_narrate_flavor` + `_creation_flavor_messages` | `_narrate_flavor` at orchestrator L699; used from `_auto_present_*` paths | yes |
| **Footer** `format_creation_status()` → `CREATION_STATUS_LABELS` | `creation.py` L599–602, L69–80; orchestrator imports `CREATION_STATUS_LABELS` | yes |
| **Input commit** `_handle_creation_response` → `_execute_creation_choice` | `_execute_creation_choice` at L1322; desk parsers in `creation.py` (`parse_player_race` at L742, etc.) | yes |
| **Do not reintroduce** `get_step_prompt` mandates | Function deleted; orchestrator does not import it | yes |
| **Contrast** live `get_combat_step_prompt` (combat only) | `combat_fsm.py` L90; orchestrator import + use at L1559 | yes |
| § Removed patterns documents deleted builder | Spec L189: `get_step_prompt()` … deleted APP-074; code absent | yes |

## Ticket AC ↔ code

| Acceptance criterion | Result |
|----------------------|--------|
| Remove `get_step_prompt()` (or docs-only hint) | **PASS** — ~94 lines removed from `creation.py`; `parse_player_race` now at L742 |
| Grep `app/` confirms no references | **PASS** — `rg "get_step_prompt" app/` zero matches |
| Domain spec: prompts in `_auto_present_*` / `format_*_table` only | **PASS** — § Step content sources table + presentation pattern |

## Run spec R1–R3 ↔ code

| ID | Requirement | Result |
|----|-------------|--------|
| **R1** Delete dead function; zero `app/` references | **PASS** |
| **R2** Live path unchanged (code-first routing, no tool mandates in flavor path) | **PASS** — creation suite green; no orchestrator diff required |
| **R3** Domain § Step content sources + changelog on close | **PASS** — changelog row dated 2026-05-20 documents removal |

## Tests run

```bash
python -m pytest app/tests/test_creation_flow.py app/tests/test_creation_tables.py play/tomb_gm/tests/test_creation_gating.py -q
```

**Result:** 19 passed (1.51s)

| Module | Role | Result |
|--------|------|--------|
| `app/tests/test_creation_flow.py` | FSM integration (APP-057/067/068/069/070) | ✓ |
| `app/tests/test_creation_tables.py` | APP-072 table strip | ✓ |
| `play/tomb_gm/tests/test_creation_gating.py` | Engine gating | ✓ |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec changelog — **APP-074 done** row present
- [x] Spec ↔ code — no drift on `get_step_prompt` or step-content ownership
- [ ] `python tmp/backlog/claim_ticket.py release APP-074 --done` — **orchestrator** (QA drift: **not run** per instruction)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Ancillary notes (non-blocking)

| Item | Note |
|------|------|
| **APP-059 backlog** | `tmp/backlog/app-059-standardize-creation-table-outputs.md` still cites `get_step_prompt` as RACE problem source — hygiene deferred per run `spec.md` Non-goals; not domain-spec drift |
| **`system_prompt.py`** | Still instructs LLM `set_creation_choice` + tables — documented non-goal; separate follow-up if desired |
| **`_narrate_only`** | Still defined in `orchestrator.py` (dead LLM loop path); spec § Removed patterns refers to retired JSON-table pattern, not APP-074 deletion scope |
| **Run `status.md`** | Pipeline checklist stale (shows pre-impl stages); update at release/commit |
| **Run `spec.md`** | R1–R3 checkboxes still unchecked — run artifact only; ticket AC satisfied |
| **Human playtest** | Not required for deletion-only chore; smoke hints in run `spec.md` § Human playtest hints |
