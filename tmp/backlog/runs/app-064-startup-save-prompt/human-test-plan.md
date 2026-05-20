# Human test plan — APP-064 startup save prompt

## Setup

- Workspace with active session + empty roster (mid-creation or wiped roster), **or** fresh workspace with no save.

## Cases

1. **No resumable save:** Launch app → expect **no** "You have a saved game"; suggestion chip **new game** only.
2. **Resumable save:** Complete creation, quit, relaunch → "You have a saved game" + **load game** / **new game** chips; load succeeds.

## Pass

Both cases match engine `has_save_session()` behavior.
