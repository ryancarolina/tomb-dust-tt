# QA Report: spec — round 1

**Task:** app-041-strip-status-tags-before-tts  
**backlog_ticket:** APP-041  
**ticket_path:** [tmp/backlog/app-041-strip-status-tags-before-tts.md](../../app-041-strip-status-tags-before-tts.md)  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)  
**domain_spec_creation:** not_needed (registry_gap false)

## Findings

### TICKET-001 — blocker

- **Location:** Ticket § Expected files vs `spec.md` § Expected files (implementation); backlog hook allow-list
- **Issue:** Ticket lists `app/gm/tts or narration layer` — that path does not exist. PM spec correctly targets `play/tomb_gm/services/tts/scene.py`, `play/tomb_gm/tests/test_tts_scene.py`, and `tmp/app-tts-narration-spec.md`, but **none of those appear in the ticket Expected files**. Hooks and plan QA gate use ticket Expected files as the edit allow-list.
- **Implementation gap:** Dev implementing per spec will be denied when editing `play/tomb_gm/services/tts/scene.py` or adding leak-matrix tests unless the ticket is updated first.
- **Suggested fix:** Replace ticket Expected files with the paths in `spec.md` § Expected files (lines 111–116). Remove the stale placeholder path.

### TICKET-002 — major

- **Location:** Ticket § Acceptance criteria vs `spec.md` § Acceptance criteria mapping (R2)
- **Issue:** Ticket has a single AC: “Strip status tags before TTS payload.” Run spec and domain spec define a second requirement — narration panel continues to show raw status tags (`narration_text` queue unchanged). That AC is mapped in spec but **not listed on the ticket**.
- **Implementation gap:** Ticket could be marked `done` after engine strip lands without verifying display/speak split; human playtest has no ticket-level AC anchor.
- **Suggested fix:** Add ticket AC: “Narration panel still displays status tags (Location / Phase / Awaiting); strip applies to TTS speak payload only.”

### SPEC-001 — major

- **Location:** `spec.md` R3 — CLI / dev speak path; `play/tomb_gm/cli/cmd_speak.py` L134–143, L90–108; `play/tomb_gm/services/tts/queue.py` L35
- **Issue:** R3 states CLI paths “inherit R1 without separate changes unless they bypass `parse_scene` (verify in plan; **expected: no bypass**).” Verified bypasses exist today:
  - `cmd_speak --text` passes `lines=[{"text": args.text, …}]` — `speak_scene` uses `lines_from_payload`, **never** `parse_scene`.
  - `cmd_speak --lines` JSON — same bypass.
  - `cmd_narrate push` and `cmd_speak --scene` **do** call `parse_scene` via `speak_scene(text)` when `lines` is omitted (canonical).
- **Implementation gap:** Dev may assume R3 is satisfied by default; dev `--text` / `--lines` would still speak status tags after R1 lands. Spec contradicts repo without scoping the bypass.
- **Suggested fix:** Either (a) add Non-goal: “CLI `--text` / `--lines` bypass — dev-only, out of scope,” or (b) require `cmd_speak` to run `parse_scene` on `--text` / validate `--lines` through the same strip (and add a test).

### SPEC-002 — minor

- **Location:** `spec.md` R1 strip scope; research leak matrix
- **Issue:** Requirements cover inline `Awaiting: TOKEN`, bracket blocks, unclosed `[Location:…`, and **whole-line** unbracketed `Location:` / `Phase:` footers. No explicit rule for **inline** unbracketed `Location: … | Phase: …` embedded mid-sentence (only whole-line in R1 item 4).
- **Implementation gap:** Residual leak class if LLM embeds pipe-separated status mid-prose; low probability given prompt shape but not ruled out.
- **Suggested fix:** Add one bullet: inline `Location:\s*…` / `Phase:\s*…` fragments anywhere in line (mirror `_LLM_STATUS_TAG_RE` unbracketed forms), or document as accepted residual risk in Non-goals.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | Valid P2 feature; `in_progress`; domain spec field matches |
| registry_gap | **PASS** | false — `tmp/app-tts-narration-spec.md` owns TTS strip |
| AC testability | **WARN** | Core strip AC testable; panel AC missing on ticket (TICKET-002) |
| Code traces | **PASS** | Leak matrix verified live (`parse_scene` probes match research-brief) |
| Domain spec sync | **PASS** | § Status tag strip before TTS (APP-041) aligned with run spec |
| Expected files ⊆ plan scope | **FAIL** | TICKET-001 |
| CLI / bypass accuracy | **FAIL** | SPEC-001 — R3 “expected: no bypass” is false |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| App path: raw narration → panel; parsed lines → TTS | `app/ui/app.py` L294–297, L344+ |
| `speak_scene` uses `lines` when provided, else `parse_scene(text)` | `queue.py` L35 |
| Whole-line `Awaiting:` skipped | `_SKIP_LINE` L13; probe: whole-line case not spoken |
| Inline `Awaiting: SKILL_INPUT` spoken today | Probe: `'The clerk nods. Awaiting: SKILL INPUT'` |
| Whole-line `Phase: preparation` spoken | Probe: unchanged |
| Unclosed bracket fragment spoken | Probe: full fragment retained |
| AV-GRID in fiction preserved | Probe: `32-C-UG-1` line passes through |
| Holt regression fixture exists | `test_tts_scene.py` HOLT_SCENE + voice-split tests |
| Domain spec updated by PM | `tmp/app-tts-narration-spec.md` L22–48, changelog L98 |
| Ticket Expected files stale | `app-041-strip-status-tags-before-tts.md` L22 |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Strip status tags before TTS payload | R1; domain § Strip scope | `test_tts_scene.py` leak matrix + pytest command | **PASS** (intent) |
| Panel still shows status *(spec only)* | R2; domain § Display vs speak | manual playtest; no `narration_text` edit | **WARN** — not on ticket (TICKET-002) |

## Summary

**FAIL** — fix **TICKET-001** (Expected files must list real engine/test/spec paths) before Dev plan or impl. Add **TICKET-002** panel AC. Clarify **SPEC-001** CLI bypass scope or require strip on `--text`/`--lines`. Domain spec and run-spec behavior contract (R1–R2, tests, non-goals vs APP-073/077/042) are otherwise strong and match live code traces.

## Re-review focus

- Ticket Expected files match `spec.md` § Expected files
- Ticket AC includes display/speak split
- R3: explicit Non-goal or requirement for CLI bypass paths
- Optional: inline unbracketed Location/Phase mid-line (SPEC-002)
