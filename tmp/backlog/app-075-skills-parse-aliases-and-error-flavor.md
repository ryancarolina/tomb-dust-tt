# APP-075: Skills input — parse aliases and error-path flavor



| Field | Value |

|-------|-------|

| **ID** | APP-075 |

| **Type** | bug |

| **Priority** | P1 |

| **Status** | done |

| **Closed** | 2026-05-20 |

| **Domain spec** | [`app-character-creation-spec.md`](../app-character-creation-spec.md) |

| **Created** | 2026-05-20 |



## Summary



At the **SKILLS** creation step, valid-looking player input can fail validation and feel like the GM **asked twice**: LLM flavor sounds like success (“Smart choices…”) while code re-shows the skills table with a `**Note:**` error. A common trigger is concatenated skill text — e.g. `manacontrol` is rejected but `mana control` works — because `SKILL_PARSE_ALIASES` only maps spaced forms, not glued tokens.



**Repro (Supa, session 2026-05-20 ~17:33):** Input `spellcasting, medicine, manacontrol` → `parse_player_skills` returns `None` (only 2 of 3 slugs) → FSM stays on `SKILLS` → `_auto_present_skills(..., error=...)` still calls `_narrate_flavor` with the normal “ask which three skills” instruction → player sees congratulatory flavor + error note + full table in one response; no `creation_advanced` for SKILLS.



## Acceptance criteria



### Parse aliases (creation.py)



- [x] `normalize_skill_slug` / `parse_player_skills` accept common **concatenated** forms for multi-word skills (at minimum `manacontrol` → `mana-control`; document or implement a consistent rule for other table skills, e.g. strip spaces/hyphens and match canonical slugs).

- [x] `spellcasting, medicine, manacontrol` parses to exactly three canonical slugs and advances SKILLS when class rules pass.

- [x] Invalid or unknown tokens still fail cleanly (no partial silent drop without feedback).



### Error-path flavor (orchestrator.py)



- [x] When `_auto_present_skills` (and matching `_auto_present_schools` / `_auto_present_spells` if same pattern) is called with `error=` set, flavor must **not** congratulate, confirm picks, or imply the step advanced — use a correction-only instruction (or skip LLM flavor and rely on `**Note:**` + table).

- [x] Single response on validation failure: error note + table + `Awaiting: SKILLS_INPUT`; no duplicate “ask” framing that contradicts the note.



### Errors and tests



- [x] When comma-separated input has unrecognized tokens, error message names the problem when practical (e.g. unknown skill name), not only “exactly 3 skills”.

- [x] Unit tests for `normalize_skill_slug` / `parse_player_skills` alias cases.

- [x] Integration or orchestrator test: invalid skills input → no success/completion flavor markers in narration; step unchanged.

- [x] Domain spec § SKILLS input / parsers updated in changelog on close.



## Expected files



- `app/gm/creation.py` — `SKILL_PARSE_ALIASES`, `normalize_skill_slug`, `parse_player_skills`, `format_skill_parse_error` (P3 error helper)

- `app/gm/orchestrator.py` — `_auto_present_skills` (and schools/spells if aligned); error-specific flavor instruction or no-flavor-on-error path; SKILLS branch calls `format_skill_parse_error`

- `play/tomb_gm/tests/test_creation_gating.py` — T1 parser unit cases (extend existing tests)

- `app/tests/test_creation_flow.py` — T2/T2b/T3 orchestrator error-flavor regression tests

- `tmp/app-character-creation-spec.md`



## Spec sync (required on close)



1. Mark **Status** → `done` in this ticket (add **Closed** date).

2. Update the domain spec checklist / changelog in [`app-character-creation-spec.md`](../app-character-creation-spec.md) — § parsers, § gated-step flavor on validation failure.

3. If behavior changed, ensure [`app-master-spec.md`](../app-master-spec.md) priority table still accurate.



## Claim / release



```bash

python tmp/backlog/claim_ticket.py APP-075 --task skills-parse-error-flavor

python tmp/backlog/claim_ticket.py release APP-075 --done

```



## Notes



- **Workaround until fixed:** use spaced table names — `spellcasting, medicine, mana control`.

- `_handle_creation_response` already re-shows table on parse failure (APP-011); this ticket fixes **why** valid intent fails and **how** the re-prompt reads.

- Consider the same glued-token rule for schools/spells parsers if players paste ids without hyphens (stretch — only if trivial once skill helper exists).



## Dependencies



| Ticket | Relationship |

|--------|--------------|

| APP-011 | related — invalid input re-shows table (done) |

| APP-069 | related — flavor must match FSM step (done) |

| APP-070 | related — blocks premature completion flavor (done); error-path success tone is a separate gap |

