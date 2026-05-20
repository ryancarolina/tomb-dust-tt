# QA PASS: spec

**Task:** APP-067-code-owned-roll-stats-table  
**backlog_ticket:** APP-067  
**ticket_path:** tmp/backlog/app-067-code-owned-roll-stats-table.md  
**Round:** 1  
**domain_spec_creation:** not_needed

**Verified:**

- [x] Backlog ticket valid; status `in_progress` (ticket file `tmp/backlog/app-067-code-owned-roll-stats-table.md`)
- [x] Ticket domain spec matches spec updates (`tmp/app-character-creation-spec.md` — APP-067 sections present)
- [x] Acceptance criteria testable (mapped to run `spec.md` R1–R4 and domain spec § Tests APP-067)
- [x] Code traces match repo (`orchestrator.py` `_auto_roll_stats` ~924–956 uses `_narrate_only`; `_chain_after_creation_choice` ~846–850 duplicates class table; `bridge.py` `roll_attributes` ~48–163 payload shape documented in research)
- [x] AGENTS.md / canon compliance (HP `10 + STA×5` cites `derived-stats.md` / `compute_hp()`; no parallel rules)
- [x] Tests/commands listed (`pytest tests/test_creation_flow.py`; optional `test_creation_tables.py`; human playtest hints in run spec)
- [x] registry_gap matches reality (`false` — character-creation spec owns `creation.py` + orchestrator creation branch per `app-master-spec.md` registry)
- [x] If registry_gap true: N/A — `registry_gap: false`; no new domain spec required

## Ticket AC coverage

| Ticket AC | Spec / domain mapping |
|-----------|------------------------|
| `format_roll_stats_table(roll_result)` in `creation.py` from payload only | R1; domain spec § `format_roll_stats_table` (lines 75–97) |
| `_auto_roll_stats()` thin flavor + code table + `format_classes_table` — no `_narrate_only` stat math | R2; domain spec § ROLL_STATS orchestration (lines 99–113) |
| Narrated HP matches `10 + STA×5` | R1 HP line + R2; domain spec HP line contract (line 95) |
| Test asserts table cells match monkeypatched `roll_result` | R4; domain spec § APP-067 assertions (lines 195–207) |

## Scope gate

Run `spec.md` **Affected paths** ⊆ ticket **Expected files**:

- `app/gm/creation.py` ✓
- `app/gm/orchestrator.py` ✓
- `app/tests/test_creation_flow.py` or `app/tests/test_creation_tables.py` ✓
- `tmp/app-character-creation-spec.md` ✓

No out-of-scope paths in requirements (bridge/engine unification correctly listed as non-goal).

## Notes

- `tmp/.active-ticket.json` currently claims **APP-066**, not APP-067 — orchestrator should re-claim APP-067 before Dev/plan stage; does not block spec content.
- Domain spec test contract asserts **Final** column + HP + single class table; ticket wording “table cells” is satisfied for the reported bug (wrong finals). Dev may optionally assert intermediate columns for stronger coverage — not required for spec PASS.
- `tmp/app-gamebridge-spec.md` lists `roll_attributes` but does not document payload keys; creation spec owns formatter contract. Optional one-line cross-ref on ticket close.
