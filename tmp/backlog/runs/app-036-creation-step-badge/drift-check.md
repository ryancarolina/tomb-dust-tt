# Drift Check: app-036-creation-step-badge

**backlog_ticket:** APP-036  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-pygame-ui-spec.md`](../../../app-pygame-ui-spec.md) | was yes (§ Implementation files omitted `sidebar.py`) | **Synced:** added `sidebar.py` row; § Creation step badge, checklist `[x]`, changelog **APP-036 done** confirmed |
| Run [`spec.md`](./spec.md) R1–R6 | no | Verified against `creation.py`, `orchestrator.py`, `app.py`, `stats.py`, `sidebar.py`, tests |
| Ticket [`app-036-creation-step-badge-in-ui.md`](../../app-036-creation-step-badge-in-ui.md) | was yes (AC unchecked) | **Synced:** all AC checked; status `done`; Closed 2026-05-22 |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **Source** — `Orchestrator.get_creation_step_badge()` | `orchestrator.py` L385–389 | yes |
| **Show when** — `creation.active == True` | returns `{step, display_label}` | yes |
| **Hide when** — inactive / post-finalize | returns `None`; enrich sets keys to `None` | yes |
| **Display labels** — `CREATION_STEP_DISPLAY` keyed by step; ≠ footer tokens | `creation.py` L98–109; invariant test | yes |
| **Unknown step** — title-case fallback | `format_creation_step_display` L112–113 | yes |
| **Enrich keys** — `creation_step`, `creation_step_display` | `_enrich_status_for_ui` L350–356 | yes |
| **UI refresh** — init + turn `finally` | `_init_orchestrator` L127–128; `_queue_turn_status` in `finally` L323 | yes |
| **StatsPanel** — `Registry:` badge at top | `stats.py` L95–104 | yes |
| **Sidebar** — cache + re-apply on `_do_layout` | `sidebar.py` L18–19, L34–38, L42–44 | yes |
| **No narration scrape** | badge path reads orchestrator only | yes |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| Visible badge during `creation.active` with human label | ✓ `CREATION_STEP_DISPLAY` + `StatsPanel` `Registry: {label}` |
| Badge hidden after creation completes / roster live | ✓ `get_creation_step_badge` returns `None` when inactive |
| Data from orchestrator / engine — never narration scrape | ✓ enrich via `get_creation_step_badge()` only |
| Placement compatible with APP-062 layout | ✓ top of stats region in sidebar; resize cache test |

## Run spec R1–R6 ↔ code

| ID | Requirement | Result |
|----|-------------|--------|
| **R1** | `CREATION_STEP_DISPLAY` step-keyed; ≠ footer tokens; fallback | **PASS** |
| **R2** | `get_creation_step_badge()` active/inactive contract | **PASS** |
| **R3** | Enrich on every status push (init + turn success/exception) | **PASS** |
| **R4** | StatsPanel badge + sidebar resize preserve | **PASS** |
| **R5** | APP-062 layout — stats region, draw-only | **PASS** |
| **R6** | Domain spec sync on close | **PASS** |

## Tests run

```bash
cd app; python -m pytest tests/test_ui_creation_badge.py tests/test_ui_map_creation_gate.py tests/test_creation_flow.py tests/test_creation_restore.py -q
```

**Result:** 34 passed (5.10s)

| Module | Tests | Result |
|--------|-------|--------|
| `app/tests/test_ui_creation_badge.py` | 9 — display map, helper, enrich, panel, sidebar resize, exception path | ✓ |
| `app/tests/test_ui_map_creation_gate.py` | 10 — enrich regression (`get_creation_step_badge.return_value = None`) | ✓ |
| `app/tests/test_creation_flow.py` | 8 — post-finalize regression | ✓ |
| `app/tests/test_creation_restore.py` | 7 — resume/session regression (no badge-specific asserts) | ✓ |

## Grep / symbol checks

| Check | Evidence | Result |
|-------|----------|--------|
| Badge source is orchestrator | `_enrich_status_for_ui` → `get_creation_step_badge()` | ✓ |
| No narration scrape | no `Awaiting:` / narration parse in badge path | ✓ |
| Display labels ≠ footer tokens | `test_creation_step_display_covers_all_steps` | ✓ |
| Map-gate mock fix | `get_creation_step_badge.return_value = None` in enrich tests | ✓ |

## Ticket close (drift stage)

- [x] Ticket acceptance criteria checked in ticket file
- [x] Domain spec checklist + changelog — **APP-036 done**
- [x] Spec ↔ code — no functional drift
- [ ] `python tmp/backlog/claim_ticket.py release APP-036 --done` — **orchestrator** (QA drift: not run per convention)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- **Non-blocking:** `test_creation_restore.py` has no explicit badge asserts; resume badge behavior covered indirectly via enrich + helper tests; recommend Stage 7 human check after continue.
- **Non-blocking:** Badge draw path not pixel-tested; state + enrich paths covered.
- **Batch:** APP-060 shares `app/ui/app.py`; sequential Stage 7a per batch board.
- **Human playtest:** Live PyGame badge visibility / step advance deferred to Stage 7 `human-test-plan.md`.
