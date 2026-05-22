# Drift Check: APP-073-strip-llm-embedded-status-tags-in-creation

**backlog_ticket:** APP-073  
**Verdict:** PASS

## Specs compared

| Spec | Drift? | Action |
|------|--------|--------|
| [`tmp/app-character-creation-spec.md`](../../../app-character-creation-spec.md) | was yes (changelog still “spec draft”) | **Synced:** changelog **APP-073 done** (2026-05-20); § Flavor sanitization pipeline (APP-073) already matched code |
| Run [`spec.md`](./spec.md) S1–S8 | no | Verified against `creation.py`, `orchestrator.py`, `test_creation_flavor_sanitize.py` |

## Code ↔ domain spec (summary)

| Requirement | Code | Match |
|-------------|------|-------|
| **S1** Harden `strip_llm_status_tags` — bracket Location/Phase anywhere; any `Awaiting:` token | `_LLM_STATUS_TAG_RE` L82–85: bracket alternates + `Awaiting:\s*[A-Z0-9_]+` (no line anchor); `strip_llm_status_tags` L537–540 | yes |
| **S2** `strip_flavor_stats_table` — heading, `\| Attr \|`, compact STR row, `` `roll_attributes( `` | `creation.py` L546–604; unit test | yes |
| **S3** Compose: stats strip after race, before `_sanitize_creation_flavor`; flavor only | `_compose_creation_narration` L638–641; body/footer never sanitized | yes |
| **S4** Single compose choke; C5 status re-strip when premature mutates | L646–656: `sanitize_premature_completion_flavor` then conditional `strip_llm_status_tags` | yes |
| **S5** `_auto_roll_stats` clerk-only flavor (no numbers/tables/status) | L1113–1118 instruction + L1117–1118 explicit bans | yes |
| **S6** Global `_creation_flavor_messages` forbids status/tables; no non-canonical labels in orchestrator prompts | L704–706; `rg` — only test fixtures use `SKILL_INPUT` / `MAGIC_SCHOOLS_*` | yes |
| **S7** ROLL_STATS composed narration: one `\| Attr \| Base \|`; finals from engine | `_auto_roll_stats` L1105–1124; `test_roll_stats_narration_single_stats_table` | yes |
| **S8** Bad-flavor compose fixture | `test_compose_flavor_sanitize_status_and_stats` + `_flavor_region` helper | yes |
| APP-007 strip behavior completed by APP-073 | Task checklist L333; § `strip_llm_status_tags` hardened | yes |

## Ticket AC → verification

| Ticket AC | Result |
|-----------|--------|
| `strip_llm_status_tags()` removes bracket Location/Phase anywhere | ✓ |
| Remove **any** `Awaiting:` in flavor | ✓ |
| `_compose_creation_narration` prose-only flavor; single code footer | ✓ |
| Prompts do not teach non-canonical labels | ✓ |
| `strip_flavor_stats_table()` + compose wiring | ✓ |
| ROLL_STATS → CLASS: one attribute breakdown; engine numbers authoritative | ✓ |
| Tests: status + stat table flavor → clean compose | ✓ |

## Tests run

```bash
cd app; python -m pytest tests/test_creation_flavor_sanitize.py tests/test_creation_tables.py tests/test_creation_flow.py -q
```

**Result:** 11 passed (1.43s)

| Module | Tests | Result |
|--------|-------|--------|
| `test_creation_flavor_sanitize.py` | 4 (APP-073) | ✓ |
| `test_creation_tables.py` | 2 (APP-072 regression) | ✓ |
| `test_creation_flow.py` | 5 (golden path + APP-069/070) | ✓ |

## Ticket close

- [x] Ticket acceptance criteria checked in ticket file
- [x] Status `done`, **Closed** 2026-05-20
- [ ] `python tmp/backlog/claim_ticket.py release APP-073 --done` — **orchestrator** (not QA drift agent)
- [ ] `tmp/.active-ticket.json` cleared — after release

## Notes

- Domain spec § APP-073 was drafted at PM stage; implementation matched before drift — only changelog/ticket close lagged.
- **Compose order (flavor):** `strip_llm_status_tags` → `strip_flavor_race_table` (APP-072) → `strip_flavor_stats_table` (APP-073) → `_sanitize_creation_flavor` (APP-069) → `sanitize_premature_completion_flavor` (APP-070) → C5 status re-strip → body + `format_creation_status` footer.
- **Non-blocking (documented in qa-implementation-pass):** Trailing punctuation after stripped `Awaiting:` token may remain; prose-only wrong stat numbers without table fingerprints not stripped — acceptable per plan; skills/schools table leaks out of scope.
- **Default path used:** thin LLM flavor + stats strip (not ROLL_STATS code-only alternative).
- Human PyGame playtest not run in drift round; see run `spec.md` § Human playtest hints for Stage 7.
