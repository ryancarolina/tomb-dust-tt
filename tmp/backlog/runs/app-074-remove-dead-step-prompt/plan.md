# Implementation Plan: APP-074-remove-dead-step-prompt

**Status:** draft  
**backlog_ticket:** APP-074  
**ticket_path:** tmp/backlog/app-074-remove-dead-get-step-prompt.md  
**domain_spec:** tmp/app-character-creation-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Deletion-only chore: remove the unused `get_step_prompt(state)` function from `app/gm/creation.py` (lines **742–833**, ~92 lines). No orchestrator, bridge, or test edits — zero callers under `app/`. Live creation stays on `_creation_turn` → `_auto_present_*` / `format_*_table` / `_execute_creation_choice`.

On ticket close, sync domain spec changelog from APP-074 **spec draft** to **removed legacy prompt builder** (§ Step content sources already describes target state).

---

## Code-path traces (planned)

### Change: Remove dead step prompt builder

| Step | File:symbol | Action |
|------|-------------|--------|
| 1 | `app/gm/creation.py:get_step_prompt` (742–833) | **Delete** entire function (NAME/RACE/CLASS tool mandates, inline RACE table, vacated ROLL_STATS branch) |
| 2 | `app/gm/creation.py` | Leave `parse_player_race` and all `format_*_table` helpers unchanged |
| 3 | `app/gm/orchestrator.py` | **No edit** — already imports `format_*` only; no `get_step_prompt` import |
| 4 | `tmp/app-character-creation-spec.md` | **Close only:** replace changelog draft row with dated “removed legacy prompt builder”; confirm § Step content sources / § Removed patterns / file map unchanged |

### Unchanged live path (regression contract)

| Layer | Source | Symbol |
|-------|--------|--------|
| Router | `orchestrator.py` | `_creation_turn` → `_creation_turn_body` |
| Flavor | `orchestrator.py` | `_auto_present_*` → `_narrate_flavor` + `_creation_flavor_messages` |
| Body | `creation.py` | `format_races_table`, `format_roll_stats_table`, `format_classes_table`, … |
| Footer | `creation.py` | `format_creation_status()` |
| Commit | `orchestrator.py` | `_handle_creation_response` → `_execute_creation_choice` |

**Contrast (do not touch):** `get_combat_step_prompt` in `combat_fsm.py` — live, used by orchestrator.

---

## Task breakdown

### 1. Delete `get_step_prompt` — `app/gm/creation.py`

1. Open `app/gm/creation.py`; locate `def get_step_prompt(state: CreationState) -> str:` at line **742**.
2. Delete from that `def` through the final `return ""` and closing blank line before `def parse_player_race` (~742–833).
3. Ensure a single blank line remains between the preceding helper (`validate_skills` / related) and `parse_player_race` — no orphaned imports or references inside the file.
4. **Do not** modify `format_races_table`, `RACES`, parsers, or `CreationState`.

### 2. Grep verification — `app/`

```bash
rg "get_step_prompt" app/
```

**Expected:** zero matches (exit code 1 / no output).

If any hit remains (import, docstring, comment), remove or reword within **Expected files only**; do not expand scope to `system_prompt.py` or backlog markdown in impl stage.

### 3. Regression pytest

```bash
python -m pytest app/tests/test_creation_flow.py -q
python -m pytest app/tests/test_creation_tables.py -q
python -m pytest play/tomb_gm/tests/test_creation_gating.py -q
```

**Expected:** all green. No new tests required (per ticket AC and qa-spec-pass).

### 4. Domain spec changelog — `tmp/app-character-creation-spec.md` (on close)

PM already added target-state prose in § **Step content sources (APP-074)**, § **Removed patterns**, and file map. At **`release --done`**:

1. Replace changelog row `APP-074 spec draft: …` with: `APP-074: removed legacy get_step_prompt() step-instruction builder from creation.py`.
2. Verify spec ↔ code: no mention of `get_step_prompt` as live or present-tense “defines” — only past tense / “deleted APP-074”.
3. Mark ticket AC checkboxes and run `python tmp/backlog/claim_ticket.py release APP-074 --done`.

**Optional close hygiene (not impl-stage files):** update `tmp/backlog/app-059-standardize-creation-table-outputs.md` prose that still cites `get_step_prompt` as RACE problem source (spec Non-goals).

---

## Files (must ⊆ ticket Expected files)

| File | Change |
|------|--------|
| `app/gm/creation.py` | Delete `get_step_prompt` (~92 lines) |
| `tmp/app-character-creation-spec.md` | Changelog finalize on close; no structural rewrite if § APP-074 already correct |

**Out of scope (explicit):**

- `app/gm/orchestrator.py` (`_creation_llm_loop`)
- `app/gm/system_prompt.py` (still mentions `set_creation_choice`)
- `app/gm/tools.py`, `app/tests/*` (unless grep finds stray reference in Expected files)
- `format_races_table()` Description column — APP-059
- Negative grep guard test — optional, not in AC
- `tmp/backlog/app-059-*.md` — close hygiene only

---

## Tests

| Step | Command | Expected |
|------|---------|----------|
| Pre-delete baseline (optional) | Same pytest trio below | Green (confirms suite healthy before edit) |
| Post-delete grep | `rg "get_step_prompt" app/` | Zero matches |
| Post-delete regression | `python -m pytest app/tests/test_creation_flow.py -q` | Pass |
| Post-delete regression | `python -m pytest app/tests/test_creation_tables.py -q` | Pass |
| Post-delete regression | `python -m pytest play/tomb_gm/tests/test_creation_gating.py -q` | Pass |

**Human smoke (Stage 7):** `cd app && python main.py` — `new game` → name → race: single code race table + `Awaiting: RACE_INPUT` unchanged (see spec.md human hints).

---

## Rollback / flags

- **Rollback:** `git checkout -- app/gm/creation.py` restores function; no migrations or config.
- **Risk:** Low — definition-only symbol; pytest failure would indicate hidden coupling (unlikely).
- **Drift gate:** Do not `release --done` until grep clean and domain changelog says “removed”, not “spec draft”.

---

## Open questions

_None — QA spec PASS; research confirms zero callers._
