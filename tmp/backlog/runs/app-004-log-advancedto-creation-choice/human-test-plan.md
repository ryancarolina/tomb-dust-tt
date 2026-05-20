# Human Playtest — APP-004

**Entry:** `cd app && python main.py` → new game

## TC-1 — creation_advanced in JSONL

- [ ] Pass / Fail
- **Steps:** New game; complete NAME step (enter a name, confirm)
- **Check:** Open `app/logs/session-YYYY-MM-DD.jsonl`; find `"type": "creation_advanced"` with `completed_step` `NAME` and `advanced_to` next step
- **Fail:** No `creation_advanced` after successful name entry

## TC-2 — failed choice does not log advanced

- [ ] Pass / Fail
- **Steps:** At RACE, send invalid race; retry with valid
- **Expected:** No `creation_advanced` for failed attempt; one event after valid pick
