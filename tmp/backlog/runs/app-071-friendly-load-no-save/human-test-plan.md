# Human test plan — APP-071 load game failure copy

## Cases

1. **Cold workspace:** `load game` → friendly "No saved game…" + **new game** hint; no raw `no save session found` in panel.
2. **Mid-creation:** `new game` → name → `load game` → explains unfinished save + current step; suggests continue or **new game** to wipe.

## Automated

`python -m pytest app/tests/test_session_resume_failure.py -q`
