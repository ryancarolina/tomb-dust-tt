# Human Playtest — APP-005

**Entry:** `cd app && python main.py` → new game → complete creation

## TC-1 — creation_finalize in JSONL

- [ ] Pass / Fail
- **Steps:** Finish character creation (finalize)
- **Check:** `app/logs/session-*.jsonl` contains `"type": "creation_finalize"` with `character_create_ok: true` and `engine_status` including non-empty `roster`
- **Fail:** Finalize completes but no `creation_finalize` or `roster_len` still 0 in snapshot
