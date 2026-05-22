# QA PASS: spec — round 1

**Task:** app-073-strip-llm-embedded-status-tags-in-creation  
**backlog_ticket:** APP-073  
**ticket_path:** [tmp/backlog/app-073-strip-llm-embedded-status-tags-in-creation.md](../../app-073-strip-llm-embedded-status-tags-in-creation.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (registry_gap false; existing owner updated)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`
- [x] Ticket domain spec matches spec updates (`tmp/app-character-creation-spec.md`)
- [x] Acceptance criteria testable (S1–S8 + domain § Tests APP-073; pytest commands listed)
- [x] Code traces match repo (research-brief + live read: narrow `_LLM_STATUS_TAG_RE`, no `strip_flavor_stats_table`, compose gap at L637–638, `_auto_roll_stats` mixed-signal prompt — all reflected in spec intent)
- [x] AGENTS.md / canon compliance (app-only sanitizers; no mechanics drift)
- [x] Tests/commands listed (`test_creation_flavor_sanitize.py`, regression suite)
- [x] registry_gap false — character-creation domain spec owns expected files
- [x] Every ticket AC row mapped in `spec.md` § Acceptance criteria mapping and domain § Flavor sanitization pipeline (APP-073)

## AC coverage (ticket → spec → domain)

| Ticket AC | spec.md | Domain spec |
|-----------|---------|-------------|
| Bracket Location/Phase anywhere in flavor | S1 | § `strip_llm_status_tags` — Remove table |
| Remove any `Awaiting:` in flavor | S1 | Same; C5 re-strip documented |
| `_compose_creation_narration` prose-only flavor; sole body/footer composer | S3–S4 | § Player-facing contract; compose order L70, L449 |
| Prompts do not teach non-canonical labels | S5–S6 | § Canon labels; ROLL_STATS prompt policy L191–193, L243 |
| `strip_flavor_stats_table` + compose wiring | S2–S3 | § `strip_flavor_stats_table`; defense-in-depth table |
| ROLL_STATS single authoritative table | S7 | § Composed ROLL_STATS contract; `format_roll_stats_table` |
| Acceptable alternative (skip LLM flavor) | § Acceptable alternative | § ROLL_STATS — acceptable alternative |
| Tests: bad status + stat flavor → clean compose | S8 | § Tests APP-073 (four cases) |
| Spec sync / APP-007 note on close | Expected files + changelog | Checklist L266; changelog L543 (draft) |

## Adversarial notes (non-blocking)

1. **F2 vs APP-073 wording** — § Flavor must reflect committed FSM (F2) still says “dice readout” while APP-073 forbids numbers/tables in ROLL_STATS flavor. § ROLL_STATS orchestration (L243) and S5 override for implementers; recommend PM tighten F2 cross-reference on close to avoid Dev leaving `_auto_roll_stats` “Present attribute roll results” text.
2. **Prompt-hygiene AC** — No static test that prompt strings exclude `SKILL_INPUT` / `MAGIC_SCHOOLS_*`; covered by S5–S6 + planned `_auto_roll_stats` edit. Dev plan should include grep/audit of `_creation_flavor_messages` and `_auto_roll_stats` instruction; human playtest § drift log is belt-and-suspenders.
3. **“Flavor region” assertion** — `test_compose_flavor_sanitize_status_and_stats` should slice narration before first code `body` marker (e.g. first `\| Attr \| Base \|` from body) when asserting no inline `Awaiting:`; domain spec does not define slice helper — acceptable to specify in `plan.md`.
4. **File map** — § File map (L516) omits `strip_flavor_stats_table` and `test_creation_flavor_sanitize.py`; update when APP-073 closes.
5. **Checklist L266** — `[x]` with “completed by APP-073” reads as shipped; code still has partial strip. Changelog correctly says “spec draft”; impl QA must verify before treating APP-007 strip as done in drift review.
6. **Session evidence** — gitignored log unverified (research); human playtest hints adequate for Stage 7.

## Summary

`spec.md` and domain § Flavor sanitization pipeline (APP-073) fully cover ticket scope, compose order, trust model, tests, and non-goals (APP-065 deferred). No registry gap. Spec is implementation-ready; minor wording/file-map cleanup can ride impl close or plan phase.

## Re-review focus

_None required for round 2 unless PM revises F2/checklist or adds flavor-region test helper to domain spec._
