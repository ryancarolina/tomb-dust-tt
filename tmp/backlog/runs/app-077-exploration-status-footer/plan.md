# Implementation Plan: APP-077-exploration-status-footer

**Status:** draft  
**backlog_ticket:** APP-077  
**ticket_path:** tmp/backlog/app-077-code-owned-exploration-status-footer.md  
**domain_spec:** tmp/app-exploration-delve-spec.md  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)

## Approach

Mirror the creation compose pattern (APP-007/073): **strip LLM status + meta from prose, append one code-owned footer from fresh `bridge.status()`**. Exploration already has a compose choke point (`_compose_exploration_narration`) for APP-024; extend it with strip helpers + `format_exploration_status`. Combat paths currently emit raw LLM text — wire the same helper before `_emit_narration`.

**F8 idempotency:** `strip_llm_status_tags` (F4 broad bracket) removes any prior footer (LLM or code-owned) **before** append. Inner `_llm_loop` compose + outer `process_turn` compose therefore yield exactly one footer without a separate “already composed” flag.

**Out of scope:** APP-083 Phase 2 verify gate, TTS policy (APP-041), multi-PC footer aggregation, L2287 early combat-end return without `_emit_narration` (qa-spec-pass NOTE-003).

---

## Code-path traces (current → planned)

### Flow A — Exploration happy path (`process_turn`)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:process_turn` | L1135–1167: build context; L1170 `_llm_loop` | unchanged |
| 2 | same | L1171–1172: `_compose_exploration_narration(narration, gate_active=…)` — APP-024 only | **F6:** strip tags → meta → append `format_exploration_status(bridge.status())` |
| 3 | same | L1173 `_emit_narration` | unchanged (creation drift still no-ops) |
| 4 | `creation.py:strip_llm_status_tags` | L115–118, L573–576: Location/Phase brackets + inline `Awaiting:` | **F4:** add full exploration bracket alternation |
| 5 | `creation.py` | _(missing)_ | **F1:** `format_exploration_status`; **F5:** `strip_llm_meta_narration` |

**Post-tool status:** compose calls `self.bridge.status()` at append time (after tools in `_llm_loop`), not the pre-turn snapshot at L1135.

### Flow B — `_llm_loop` `all_failed and content` (double-compose path)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_llm_loop` | L2615–2634: prefix + optional hint + `_compose_exploration_narration(content)` | compose returns **body + footer** |
| 2 | `process_turn` | L1172: compose again on `prefix\n\nhint\n\nbody\n\nfooter` | **F8:** F4 strip removes first footer; re-append one fresh footer |
| 3 | Prefix preservation | L2622–2633: `[Mechanics failed — …]` prepended outside compose | compose runs on assistant `content` only inside loop; outer compose strips/re-footers **entire** string — prefix/hint lines lack bracket tokens, survive strip |

**Planned inner return shape:** `f"{prefix}\n\n{hint?}\n\n{composed_content}"` where `composed_content` = steps 1–5 of compose order on `content` only (unchanged from today’s call boundary).

**Outer compose:** runs on full string; broad bracket strip removes inner footer; meta/status strip on prose; single new footer at end. **Mandatory idempotency gate:** `test_compose_idempotent_double_call`.

### Flow C — Combat PC turn (`_combat_turn` → `_combat_llm_loop_inner`)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `_combat_llm_loop_inner` | L2444–2450: `final.get("content")` raw | unchanged at source |
| 2 | `_combat_turn` | L2317 / L2329: narration from loop | unchanged |
| 3 | `_combat_turn` | L2334 `_emit_narration(narration)` — **no compose** | **F9:** `_compose_exploration_narration(n, gate_active=False)` before emit when not code-only |
| 4 | `_combat_turn` | L2299 `_narrate_text` combat end | same compose before L2302 `_emit_narration` |
| 5 | `_combat_llm_loop_inner` | L2413–2427: `all_failed` → prefix only | **skip compose** (F9 code-only) |
| 6 | `_handle_player_death` | L2320–2326, L2433–2437 | **skip compose** (code boilerplate) |

**Out of scope:** L2282–2287 `pending_start` early return via `_narrate_text` without `_emit_narration`.

### Flow D — Creation reference (do not change)

| Step | File:symbol | Notes |
|------|-------------|-------|
| `_compose_creation_narration` | L1183–1218 | Uses `format_creation_status` (`Awaiting:` only) — **not** `format_exploration_status` |
| `_auto_finalize` footer | L1992 | Shape reference only |

### Flow E — Prompt mandate removal

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| `system_prompt.py` | L213 step 6 | “Include state line: [Location: …” | **F10:** remove; instruct client appends state |
| same | L271–273 Response Format | bracket mandate | replace with “do not emit `[Location:` or `Awaiting:` tags” |

---

## Task breakdown

### 1. `format_exploration_status` — `app/gm/creation.py`

**Placement:** after `format_creation_status` (~L671–674).

**Signature:** `def format_exploration_status(status: dict) -> str`

**Helper (module-private):**

```python
def _primary_roster_entry(status: dict) -> dict:
    roster = status.get("roster") or []
    if not roster:
        return {}
    return min(roster, key=lambda r: r.get("slot", 999))
```

**Field mapping (F1–F3, qa-spec-pass SPEC-002/003):**

| Token | Source | Empty-roster fallback |
|-------|--------|------------------------|
| `Location` | `party.display_address` or `party.address` | `"?"` |
| `Phase` | `party.phase` | `"?"` |
| `HP` | primary entry `hp` | `"?/?"` |
| `Fortune` | primary entry `fortune` | `"?/1"` |
| `GP` | primary entry `gold`; if `party.gold_in_transit > 0` → `"{gold} (+{transit} transit)"` | `"0"` |
| `Turn` | `combat.turn_id` when `status.get("combat")` truthy | `"?"` (qa-spec-pass: **no** `actor` fallback) |
| `Awaiting` | `status.awaiting` | `"?"` |

**Output shapes (normative):**

```text
[Location: {loc} | Phase: {phase} | HP: {hp} | Fortune: {fortune} | GP: {gp} | Awaiting: {awaiting}]
[Location: {loc} | Phase: {phase} | HP: {hp} | Fortune: {fortune} | GP: {gp} | Turn: {turn_id} | Awaiting: {awaiting}]
```

**Golden fixtures** (for tests):

| Variant | Key fields |
|---------|------------|
| Surface | `party.address=32-C`, `phase=preparation`, roster slot 1 hp/fortune/gold |
| Delve | `display_address=32-C-UG-1 / antechamber`, `phase=delve` |
| Combat | above + `combat.turn_id=pc-1` |
| Transit GP | `gold=61`, `party.gold_in_transit=12` → `GP: 61 (+12 transit)` |

---

### 2. Extend `strip_llm_status_tags` — `app/gm/creation.py` (F4)

**Current `_LLM_STATUS_TAG_RE` (L115–118):**

```python
r"\[Location:[^\]]*\]|\[Phase:[^\]]*\]|Awaiting:\s*[A-Z0-9_]+"
```

**Planned:** add third alternation for **full exploration bracket** (defense for models that emit canonical shape + idempotent re-compose):

```python
_LLM_STATUS_TAG_RE = re.compile(
    r"\[Location:[^\]]*\]"
    r"|\[Phase:[^\]]*\]"
    r"|\[[^\]]*(?:\bLocation:|\bPhase:|\bHP:|\bFortune:|\bGP:|\bTurn:|\bAwaiting:)[^\]]*\]"
    r"|Awaiting:\s*[A-Z0-9_]+",
    re.I | re.MULTILINE,
)
```

**Creation regression:** broad bracket must not appear in creation flavor tests — creation uses `Awaiting:` footer **without** full bracket (except explicit `_auto_finalize` footer passed as `footer=` param, never through strip on composed output). Run `test_creation_flavor_sanitize.py -k status`.

**Post-sub cleanup:** keep `\n{3,}` collapse + `.strip()` (L575–576).

---

### 3. `strip_llm_meta_narration` — `app/gm/creation.py` (F5)

**Placement:** after `strip_llm_status_tags`.

**Signature:** `def strip_llm_meta_narration(text: str) -> str`

**Patterns (module-level):**

| Pattern | Action |
|---------|--------|
| `\*\*Campaign Memory Updated:?\*\*` (case-insensitive) | remove line |
| Trailing block: `\n---\n` + optional whitespace + memory banner line | remove block |
| Standalone `^---\s*$` lines immediately before/after memory banner | remove with banner |

**Algorithm:**

1. If not `text.strip()`, return `""`.
2. Apply banner regex substitutions.
3. Collapse `\n{3,}` → `\n\n`; `.strip()`.
4. Do **not** remove `---` mid-prose scene breaks unless paired with memory banner on same/adjacent line (keep conservative to avoid eating legitimate dividers).

---

### 4. `_compose_exploration_narration` — `app/gm/orchestrator.py` (F6–F8)

**Current (L657–662):** APP-024 sanitizer + refusal only.

**Planned compose order:**

1. `sanitize_premature_site_entry_flavor(prose, gate_active=gate_active)` (APP-024)
2. If `gate_active and not text.strip()` → `_SITE_ENTRY_REFUSAL_LINE` (APP-024)
3. Optional **F11:** `_log_exploration_drift_if_needed(text)` — compare bracket tokens in raw prose vs `bridge.status()` before strip; telemetry only
4. `strip_llm_status_tags(text)` — **F8:** removes LLM bracket + any prior code footer
5. `strip_llm_meta_narration(text)`
6. `footer = format_exploration_status(self.bridge.status())` — fresh snapshot
7. Join: `[text.strip(), footer]` with `\n\n` — **F7:** emit footer even when `text.strip()` empty (refusal line or strip-all)

**Code-only skip helper (F9):** add `_is_code_only_combat_narration(text: str) -> bool`:

| Skip compose when | Reason |
|-------------------|--------|
| Text matches `^\[Mechanics failed —` and no prose after first paragraph | Combat/exploration tool-fail prefix-only |
| Text from `_handle_player_death` (detect via known prefix/markers) | Code boilerplate |

Use in `_combat_turn` before compose; exploration `process_turn` never hits combat death boilerplate.

**Imports (L19–36):** add `format_exploration_status`, `strip_llm_meta_narration`.

---

### 5. Wire combat emit paths — `app/gm/orchestrator.py` (F9)

**Choke-point pattern** (prefer one place over scattering):

```python
def _emit_exploration_narration(self, narration: str, *, gate_active: bool = False) -> None:
    if not self._is_code_only_combat_narration(narration):
        narration = self._compose_exploration_narration(narration, gate_active=gate_active)
    self._emit_narration(narration)
```

**Replace `_emit_narration(narration)` in `_combat_turn` at:**

| L | Path |
|---|------|
| ~2302 | Combat ended (`_narrate_text`) |
| ~2334 | PC / monster LLM narration |

**Keep `_emit_narration` direct** for death paths (~2323, ~2435) and exploration `process_turn` (~1173) which already composes at L1172.

**Alternative (minimal diff):** inline `_compose_exploration_narration(..., gate_active=False)` before existing `_emit_narration` at combat sites only — same behavior, no new emit wrapper. Pick one; tests assert footer on combat paths either way.

**Do not compose:**

- `_combat_llm_loop_inner` L2427 prefix-only return
- `_combat_turn` L2273 combat-start failure string
- L2287 early return (no emit — out of scope)

---

### 6. Optional `log_exploration_drift` — `app/gm/logger.py` (F11)

**Add:**

```python
def log_exploration_drift(data: dict):
    log_entry("exploration_drift", data)
```

**Trigger:** new private method on orchestrator, called from `_compose_exploration_narration` **before** strip (step 3):

- Parse GP / Phase / Awaiting from prose via extended regex (reuse `parse_narration_status_line` + GP capture `GP:\s*([^|\]]+)`).
- Compare to engine snapshot from `bridge.status()`.
- If mismatch on any present field → `log_exploration_drift({...})`.
- Never block emit.

---

### 7. `system_prompt.py` — prompt policy (F10)

**Edit L207–213 (`HOW YOU WORK EACH TURN`):**

- Remove step 6 “Include state line: …”.
- Add step 6: *“Write scene prose only — the client appends an authoritative status line from the engine. Do not emit `[Location: …]`, `Awaiting:`, or bracket status tags in your narration.”*

**Edit L271–273 (`Response Format`):**

Replace bracket mandate with:

```text
Write narration as prose. End with situation and implicit/explicit choices.
Do NOT append status lines — the client adds `[Location: … | … | Awaiting: …]` from the database after your text.
```

**Preserve:** combat `turn_id` / `combat_action` tool rules (L219); exploration movement rules unchanged.

---

### 8. Tests — `app/tests/test_exploration_status_footer.py` (new)

**Style:** follow `test_exploration_site_entry_gate.py` fixtures (`_patch_llm_sequence`, `_surface_exploration_orchestrator`).

**Status fixtures** (module-level dicts — no live workspace):

```python
STATUS_SURFACE = {...}
STATUS_DELVE = {...}
STATUS_COMBAT = {...}
STATUS_GP_TRANSIT = {...}
```

#### 8.1 Unit — `format_exploration_status`

| Test | Assert |
|------|--------|
| `test_format_exploration_status_golden` | Exact strings for surface, delve, combat variants |
| `test_format_exploration_status_gp_transit` | `GP: 61 (+12 transit)` |
| `test_format_exploration_status_empty_roster` | `HP: ?/?`, `GP: 0` — documents SPEC-002 |

#### 8.2 Unit — strip helpers

| Test | Assert |
|------|--------|
| `test_strip_llm_status_tags_exploration_bracket` | Full exploration bracket + inline `Awaiting:` removed; scene prose kept |
| `test_strip_llm_meta_narration` | `---\n**Campaign Memory Updated:**` removed; leading prose kept |

#### 8.3 Unit — compose

| Test | Assert |
|------|--------|
| `test_compose_exploration_single_footer` | LLM bracket with wrong GP → one footer; GP from patched `bridge.status()` |
| `test_compose_empty_body_still_footer` | Whitespace-only input, `gate_active=False` → footer only (with `\n\n`) |
| `test_compose_app024_refusal_plus_footer` | Gate active + entry fiction stripped → refusal + footer |
| `test_compose_idempotent_double_call` | **F8 gate:** two compose calls → `narration.count("[Location:") == 1`; exactly one `GP:` in footer region |

**Footer region helper:**

```python
def _footer_region(n: str) -> str:
    idx = n.rfind("[Location:")
    return n[idx:] if idx >= 0 else ""
```

#### 8.4 Integration — combat wrong GP

| Test | Setup | Assert |
|------|-------|--------|
| `test_combat_turn_compose_wrong_gp` | Patch `bridge.status()` + `_combat_active_in_db`; stub `_combat_llm_loop` or LLM to return prose + wrong bracket; drive `_combat_turn` | Emitted narration footer has engine GP; includes `Turn:` when `combat` dict present |

#### 8.5 Regression commands

```bash
cd app && python -m pytest tests/test_exploration_status_footer.py -q
cd app && python -m pytest tests/test_exploration_site_entry_gate.py -q
cd app && python -m pytest tests/test_exploration_set_phase_delve_hint.py -q
cd app && python -m pytest tests/test_creation_flavor_sanitize.py -q -k status
```

---

## Requirements → implementation map

| ID | Requirement | Locus | Test |
|----|-------------|-------|------|
| **F1** | `format_exploration_status` | `creation.py` | `test_format_exploration_status_golden` |
| **F2** | Footer field mapping + transit GP | `creation.py` | `test_format_exploration_status_gp_transit` |
| **F3** | Combat `Turn:` from `turn_id` | `creation.py` | golden combat variant |
| **F4** | Broad bracket strip | `creation.py` `_LLM_STATUS_TAG_RE` | `test_strip_llm_status_tags_exploration_bracket` + creation regression |
| **F5** | `strip_llm_meta_narration` | `creation.py` | `test_strip_llm_meta_narration` |
| **F6** | Compose order 024 → strip → meta → footer | `orchestrator.py` L657+ | compose unit tests |
| **F7** | Empty body still footer | compose | `test_compose_empty_body_still_footer` |
| **F8** | Idempotent double-compose | F4 + compose | `test_compose_idempotent_double_call` |
| **F9** | Combat wire before emit | `_combat_turn` | `test_combat_turn_compose_wrong_gp` |
| **F10** | Prompt policy | `system_prompt.py` | manual grep / human playtest |
| **F11** | Optional drift log | `logger.py` + compose | optional unit if implemented |
| **F12** | TurnTruth doc-only | — | no code |

---

## Files (must ⊆ ticket Expected files)

| File | Changes |
|------|---------|
| `app/gm/creation.py` | `format_exploration_status`, `_primary_roster_entry`; extend `_LLM_STATUS_TAG_RE`; `strip_llm_meta_narration` |
| `app/gm/orchestrator.py` | Extend `_compose_exploration_narration`; combat compose before emit; optional `_log_exploration_drift_if_needed`, `_is_code_only_combat_narration` |
| `app/gm/system_prompt.py` | F10 prompt edits L213, L271–273 |
| `app/gm/logger.py` | Optional `log_exploration_drift` |
| `app/tests/test_exploration_status_footer.py` | **New** — full test matrix |
| `tmp/app-exploration-delve-spec.md` | Changelog on close only |
| `tmp/app-llm-orchestrator-spec.md` | Changelog on close only |

---

## Rollback

Revert helpers + compose + prompt restores LLM-authored bracket lines and wrong-GP footers. No feature flags. APP-024 sanitizer behavior preserved if compose helper reverted to stub.

---

## Open questions

- **`_emit_exploration_narration` wrapper vs inline compose in combat:** either satisfies F9; impl picks minimal diff.
- **F11 optional:** ship if low effort; skip only if time-blocked — not AC-blocking per ticket.
- **Session claim:** ensure `tmp/.active-ticket.json` includes APP-077 before `app/` edits.
- **Ticket AC signature drift (qa-spec-pass TICKET-001):** impl uses `(prose, *, gate_active)` + fresh `bridge.status()` — align ticket checkboxes on close, not in impl.
