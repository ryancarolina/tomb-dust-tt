# Implementation Plan: APP-083-mechanical-truth-narration-gate (Phase 1 — Creation)

**Status:** draft (plan r2 — qa-plan-report-1)  
**backlog_ticket:** APP-083  
**ticket_path:** [tmp/backlog/app-083-creation-flavor-verification-gate.md](../../app-083-creation-flavor-verification-gate.md)  
**domain_spec:** [tmp/app-llm-orchestrator-spec.md](../../../app-llm-orchestrator-spec.md) (primary); [tmp/app-character-creation-spec.md](../../../app-character-creation-spec.md) (Phase 1 rule matrix)  
**Spec:** [spec.md](spec.md) · [qa-spec-pass.md](qa-spec-pass.md) · [research-brief.md](research-brief.md)  
**QA plan r1:** [qa-plan-report-1.md](qa-plan-report-1.md) · **Dev reflection r2:** [reflection-dev-plan-r2.md](reflection-dev-plan-r2.md)

## Batch close scope

**Phase 1 creation only.** Shared framework ships in this batch; exploration/combat wiring is documented but **not** implemented. Ticket close uses **Phase 1 AC** from run spec + domain spec § Phase 1 batch close — not ticket § Phases 2–3 AC.

## Approach

Creation flavor today: `_narrate_flavor` → immediate compose strippers → emit. No step catalogs in prompt; no verify→retry. Sumpty session (`app/logs/session-2026-05-21.jsonl` L4743/L4749/L4755) shows wrong schools, fake spell tables, wrong kit/GP **above** correct code bodies.

Fix in five layers (N1–N10):

1. **N1–N4** — New `app/gm/narration_verify.py`: `TurnTruth`, `VerificationResult`, `format_turn_truth_for_prompt`, `verify_narration` (universal + creation rules).
2. **N2** — `build_creation_turn_truth(creation)` in `app/gm/creation.py` — same catalog sources as mechanics.
3. **N5–N7, N10** — `narrate_with_verification` in `orchestrator.py`; wire all 9 creation flavor call sites; exhaustion → `""` or clerk fallback; compose unchanged boundary (verify flavor only).
4. **N8** — JSONL helpers in `logger.py` (`narration_verify_fail/pass/exhausted`).
5. **N9** — Trim conflicting creation table mandates in `system_prompt.py`.

**Verify is the pass gate.** `_compose_creation_narration` strippers (L905–923) remain defense-in-depth until consolidated.

**Normative loop order** (orchestrator spec § Mechanical-truth narration gate + APP-079 coordination):

```text
build TurnTruth → build messages (truth block + retry feedback)
  → chat_completion (_narrate_flavor low-level)
  → log_llm_response
  → length recovery (079 stub or shared helper) — branch on body_pending / flavor_only (domain per-step table)
  → verify_narration
  → pass → return prose | fail → retry (shared NARRATION_LLM_MAX_ATTEMPTS; verify subset cap)
  → exhausted → "" / clerk fallback
  → _compose_creation_narration (strippers + body + footer)
```

**APP-079 parallel batch:** `handle_finish_reason_length` does not exist yet. Phase 1 ships an **inline stub** inside `narrate_with_verification` keyed by caller flags (domain spec § `finish_reason: length` recovery — per-step wiring):

| Branch | Condition | Action |
|--------|-----------|--------|
| Discard | `body_pending=True` and `finish_reason=="length"` | `prose=""`; do not verify discarded text |
| Length retry / fallback | `flavor_only=True` and `finish_reason=="length"` | One retry (`LENGTH_MAX_RECOVERY_RETRIES=1`, tightened “≤2 sentences, no tables”) or static clerk fallback; then verify surviving candidate |
| **Invariant** | `body_pending=True` ⇒ `flavor_only=False` | Assert at call sites |

When APP-079 lands, replace stub with `handle_finish_reason_length` import — no duplicated length logic long-term.

---

## Code-path traces (current → planned)

### Flow A — Creation turn emit (unchanged shell)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:process_turn` → `_creation_turn` | L765 → L1011 | unchanged |
| 2 | `orchestrator.py:_creation_turn_body` | L1018–1095: dispatch → compose → `_emit_narration` L1092 | unchanged shell; inner presenters return verified compose |
| 3 | `orchestrator.py:_emit_narration` | L372–374: `log_gm_narration` + drift check | unchanged — only post-verify composed strings arrive |
| 4 | `orchestrator.py:_compose_creation_narration` | L896–931: strippers → body → footer | **unchanged** Phase 1; strippers = defense-in-depth |

### Flow B — Flavor generation (current choke → planned gate)

| Step | File:symbol | Current (L) | Planned |
|------|-------------|-------------|---------|
| 1 | `orchestrator.py:_creation_flavor_messages` | L957–978: `SYSTEM_PROMPT` + desk block + `_committed_state_flavor_block()` L933–944 only | **N7:** inject `format_turn_truth_for_prompt(build_creation_turn_truth(self.creation))`; fold committed fields into truth block; drop duplicate `committed_block` append; on retry append violation feedback to instruction (same truth block) |
| 2 | `orchestrator.py:_narrate_flavor` | L990–1007: raw `chat_completion`, `max_tokens=120`, no verify | **Keep** as low-level LLM caller; creation presenters stop calling directly |
| 3 | _(missing)_ | — | **N5:** new `narrate_with_verification` (~after L1007): truth → messages → `_narrate_flavor` → length stub → `verify_narration` → retry/exhaust |
| 4 | All `_auto_present_*` / `_creation_table_flavor` / `_narrate_creation_flavor` | See wire table below | Call `narrate_with_verification` instead of `_narrate_flavor` |

### Flow C — Nine creation flavor wire points (N6)

Per-step flags match domain spec § `finish_reason: length` recovery — per-step wiring (`tmp/app-llm-orchestrator-spec.md`). **NAME is not `body_pending`** — static body is `"What name shall I put on the Registry ledger?"` (L1123); only banter is LLM-generated.

| Symbol | Step | Current call (L) | `body_pending` | `flavor_only` | Planned call |
|--------|------|------------------|----------------|---------------|--------------|
| `_auto_present_name` | NAME | `_narrate_flavor(...)` L1117–1122 | `false` | `true` | `narrate_with_verification(..., body_pending=False, flavor_only=True)` |
| `_auto_present_race` | RACE | L1129–1136 | `true` | `false` | `narrate_with_verification(..., body_pending=True, flavor_only=False)` |
| `_auto_present_class` | CLASS | L1145–1150 | `true` | `false` | same |
| `_auto_present_skills` → `_creation_table_flavor` | SKILLS | L1330–1334; L1317–1324 `error=` → `""` | `true` | `false` | `narrate_with_verification` when no error; **`skip_llm=True` when `error=`** (APP-075) |
| `_auto_present_schools` | SPELL_SCHOOLS | L1345–1349 | `true` | `false` | same as skills |
| `_auto_present_spells` | SPELLS | L1357–1361 | `true` | `false` | same |
| `_auto_present_equipment` | EQUIPMENT_GOLD | L1369–1374 | `true` | `false` | same |
| `_auto_roll_stats` → `_narrate_creation_flavor` | ROLL_STATS→CLASS | L1388–1396; wrapper L980–988 | `true` | `false` | `narrate_with_verification(..., presenting_step="ROLL_STATS", body_pending=True, flavor_only=False)`; drop post-hoc `_sanitize_creation_flavor` (verify covers race rule) |
| `_auto_finalize` | FINALIZE→WORLD_INTRO | L1486–1492 flavor only | `true` | `false` | `narrate_with_verification(..., body_pending=True, flavor_only=False)` — **footer L1500 never verified** |

**Central replacements:**

| Helper | Current (L) | Planned |
|--------|-------------|---------|
| `_creation_table_flavor` | L1317–1324: `_narrate_flavor` | Delegate to `narrate_with_verification` or inline gate call |
| `_narrate_creation_flavor` | L980–988: `_narrate_flavor` + optional `_sanitize_creation_flavor` | Thin wrapper → `narrate_with_verification` with `presenting_step` |

### Flow D — Sumpty repro (must fail verify before emit)

| Session line | Step | Flavor violation (excerpt) | Verify rule |
|--------------|------|----------------------------|-------------|
| L4743 | SPELL_SCHOOLS | `Restoration, Transmutation, Divination, Evocation, Abjuration, Conjuration, Necromancy, Enchantment` | Catalog denylist + schools ∉ allowed (Pyromancy…Divine) |
| L4749 | SPELLS | `\| School \| Spells \|` + `Restoration`, `Communion`, `Warding` | Markdown table + denylist + spells ∉ tier1 allowlist |
| L4755 | EQUIPMENT_GOLD | `bedroll, waterskin, rope, flint, and 50 gold` + premature delve | Economy (GP≠20, kit prose) + premature completion |

Embed these flavor strings (not gitignored JSONL) in `test_narration_verify.py`.

### Flow E — What must not change

| Path | File:symbol | L | Reason |
|------|-------------|---|--------|
| Code body | `format_schools_table`, `format_spells_table`, etc. | `creation.py` L385–733 | Verify never runs on body |
| Reception footer | `_auto_finalize` → `_compose_creation_narration(..., footer=footer)` | L1500–1501 | Explicit footer with `[Location:` / `Awaiting: RECEPTION_CHOICE` is code-owned |
| Error re-show | `_creation_table_flavor` when `error=` | L1320–1321 | APP-075: skip LLM, `flavor=""` |
| Exploration/combat loops | `_llm_loop`, `_combat_llm_loop_inner` | — | Phase 2–3 defer |

---

## Task breakdown

### 1. New module — `app/gm/narration_verify.py` (N1, N3, N4)

#### 1.1 Types

```python
@dataclass(frozen=True)
class VerificationResult:
    passed: bool
    violations: list[str]

@dataclass(frozen=True)
class TurnTruth:
    mode: Literal["creation", "exploration", "combat"]
    step: str | None
    engine: dict[str, Any]          # Phase 1: {} or minimal slice
    tool_results: list[dict[str, Any]]  # Phase 1: []
    allowed: dict[str, Any]         # step-keyed allowlists — see §1.3
    forbidden: dict[str, Any]       # e.g. {"denylist_schools": [...]}
    code_blocks: list[str]          # hints for prompt, not full tables
```

`AllowedClaims` / `ForbiddenClaims` as typed aliases optional; **dict fields sufficient** for Phase 1 (qa-spec-pass note 7).

#### 1.2 Constants

`CREATION_CATALOG_DENYLIST`: whole-word match (case-insensitive) for generic TTRPG school/spell fiction:

`Restoration`, `Evocation`, `Abjuration`, `Conjuration`, `Transmutation`, `Divination`, `Enchantment`, `Communion`, `Warding`, … (creation spec § denylist).

Reuse table fingerprints from existing strippers conceptually:

- Markdown table row: `re.search(r"\|.+\|", prose)` on non-empty lines (exclude single `|` noise if needed)
- Status tags: mirror `strip_llm_status_tags` patterns (`Awaiting:`, `[Location:`, `Phase:`)
- Stats: `\| Attr \|`, `### Your Attributes`, `| STR | AGI |` (APP-073)
- Premature: patterns from `sanitize_premature_completion_flavor` L626–631 in `creation.py`

#### 1.3 `format_turn_truth_for_prompt(truth: TurnTruth) -> str`

Output compact block:

```text
## Authoritative facts (do not contradict)
Step: SPELL_SCHOOLS
Rule: Choose Divine plus 1 other school (2 total).
Allowed schools: Pyromancy, Ward, Biomancy, Necromancy, Ether, Divine
Committed: name Sumpty, race Undead, class Novice, skills Medicine, Spellcasting, Mana Control
Code will append: full school pick table — do not duplicate

Write 1–3 sentences of Registry clerk banter only. Do not list picks, stats, kit, gold, schools, spells, or outcomes.
```

- Include `truth.code_blocks` lines.
- **No** full markdown table reproduction.
- Fold former `_committed_state_flavor_block()` fields here (creation spec F4 cross-ref on close).

#### 1.4 `verify_narration(prose: str, truth: TurnTruth) -> VerificationResult`

Entry point → `_verify_universal(prose)` then mode delegate `_verify_creation(prose, truth)`.

| Rule class | Creation implementation |
|------------|-------------------------|
| Universal | Table rows; `Awaiting:` / `[Location:` / `Phase:` anywhere in flavor |
| Catalog | Denylist word-boundary match; any school/spell token in prose not in `truth.allowed["schools"]` / `["spells"]` when step is SPELL_SCHOOLS/SPELLS |
| Economy | EQUIPMENT_GOLD: `\d+\s*(gp|gold|coin)` must match `truth.allowed["starting_gold"]`; kit item lists (bedroll, waterskin, …) when step is EQUIPMENT_GOLD |
| Race | Whole-word other race title vs `truth.allowed["committed_race"]` (mirror `_sanitize_creation_flavor` L946–955) |
| Premature completion | APP-070 markers when desk active |
| Stats | ROLL_STATS / CLASS flavor: stat table fingerprints |

Return `VerificationResult(passed=len(violations)==0, violations=violations)` with human-readable violation strings for retry feedback.

**Export:** `TurnTruth`, `VerificationResult`, `format_turn_truth_for_prompt`, `verify_narration`, `CREATION_CATALOG_DENYLIST`.

---

### 2. Truth builder — `app/gm/creation.py` (N2)

Add **`build_creation_turn_truth(creation: CreationState) -> TurnTruth`** after catalog helpers (~L433, after `format_spells_table`).

| Step | `allowed` population | `code_blocks` hint |
|------|---------------------|-------------------|
| `NAME` | committed name (if any) | "code will append name prompt" |
| `RACE` | — | "full race table — do not duplicate" |
| `ROLL_STATS` / `CLASS` | `committed_race`, `roll_result` keys (no stat numbers in flavor) | "roll readout + class table" |
| `SKILLS` | eligible skills for class | "skills pick table" |
| `SPELL_SCHOOLS` | `eligible_schools_for_class(chosen_class)` display names + ids; rule string from `format_schools_table` first line logic | "school pick table" |
| `SPELLS` | `tier1_spells_for_schools(chosen_schools)` ids/names; min Divine note if profile | "spell pick table" |
| `EQUIPMENT_GOLD` | call `ensure_equipment_gold(creation)`; `equipment_kit`, `starting_gold` | "kit + gold summary" |
| `FINALIZE` / world intro | full committed snapshot | "registration summary + stats line" |

Sources (never parse markdown back):

- `school_catalog()` L332, `eligible_schools_for_class()` L369, `tier1_spells_for_schools()` L377
- `ensure_equipment_gold()` L754, `starting_spell_profile()` L340
- `RACES`, `CLASS_INFO`, `race_display_title()`, committed FSM fields

Set `mode="creation"`, `step=creation.step`, `engine={}`, `tool_results=[]`, `forbidden={"denylist_schools": CREATION_CATALOG_DENYLIST}` (import from `narration_verify`).

---

### 3. Orchestrator gate — `app/gm/orchestrator.py` (N5–N7, N10)

#### 3.1 Config — `Orchestrator.__init__` L149–154

Read from `config` (add keys to `app/config.yaml` under new `narration:` section or `llm:`):

| Key | Default | Purpose |
|-----|---------|---------|
| `NARRATION_LLM_MAX_ATTEMPTS` | `6` | **Shared** cap per published turn — every LLM call (length retry on NAME + verify regeneration) |
| `NARRATION_VERIFY_MAX_RETRIES` | `5` | Max **verify-fail** regeneration attempts (subset of shared cap) |
| `LENGTH_MAX_RECOVERY_RETRIES` | `1` | Max length-specific retries per turn on `flavor_only` paths (subset of shared cap) |

Store as `self._narration_llm_max_attempts`, `self._narration_verify_max_retries`, `self._length_max_recovery_retries`.

**Budget semantics** (orchestrator spec § Config): one counter (`attempt`) increments on **every** `chat_completion` inside the gate loop. Loop continues only while `attempt < NARRATION_LLM_MAX_ATTEMPTS`. On verify fail, also require `verify_fail_count < NARRATION_VERIFY_MAX_RETRIES` before another verify retry — if verify subset is exhausted, exit loop early (log exhausted) even if one shared slot remains. Length retry on NAME counts against the same `attempt` counter. Do **not** treat `NARRATION_VERIFY_MAX_RETRIES` as a second independent loop guard without the shared cap.

#### 3.2 `narrate_with_verification` — insert ~L1008

Suggested signature:

```python
def narrate_with_verification(
    self,
    instruction: str,
    player_input: str,
    *,
    body_pending: bool = False,
    flavor_only: bool = False,
    presenting_step: str | None = None,
    skip_llm: bool = False,  # error= path
) -> str:
```

**Invariant:** `body_pending=True` ⇒ `flavor_only=False`. Call sites pass both flags explicitly (Flow C). Debug assert if violated.

Loop (normative order):

1. If `skip_llm`: return `""`.
2. `truth = build_creation_turn_truth(self.creation)`; override `truth.step` with `presenting_step` when set (ROLL_STATS presents as CLASS in FSM but verify as ROLL_STATS).
3. `attempt = 0`; `verify_fail_count = 0`; `length_recovery_used = False`; `violations_feedback: str | None = None`.
4. While `attempt < self._narration_llm_max_attempts`:
   - Build messages via refactored `_creation_flavor_messages(instruction, player_input, truth=truth, violations=violations_feedback)`.
   - `raw = self._narrate_flavor(messages)` — capture `finish_reason` via `self._last_finish_reason` or tuple return (§3.5).
   - **Length stub (079)** — before verify:
     - If `body_pending` and `finish_reason == "length"`: `prose = ""`; log `llm_truncation_recovery` action `discard_flavor`; **do not** treat truncated table text as verify input.
     - Elif `flavor_only` and `finish_reason == "length"`:
       - If `length_recovery_used < self._length_max_recovery_retries`: append tightened instruction (“≤2 sentences, no tables”); `length_recovery_used += 1`; `attempt += 1`; **continue** (no verify on truncated slice).
       - Else: `prose = _NAME_LENGTH_STATIC_FALLBACK` (e.g. `"The clerk glances up from the ledger."`) — pre-approved static; verify may no-op pass.
     - Else: `prose = raw`.
   - `result = verify_narration(prose, truth)`.
   - If pass: `log_narration_verify_pass(mode="creation", step=truth.step, attempts=attempt+1)`; return prose.
   - Fail: `log_narration_verify_fail(...)`; `verify_fail_count += 1`.
   - If `verify_fail_count >= self._narration_verify_max_retries`: **break** (verify subset exhausted).
   - `violations_feedback = "; ".join(result.violations)`; `attempt += 1`.
5. `log_narration_verify_exhausted(...)`; return `""` (N10 — compose still appends body/footer).

**Exhaustion fallback:** empty flavor acceptable; optional static `"The clerk glances up from the ledger."` only if empty fails UX tests — prefer `""` per spec N10.

#### 3.3 Refactor `_creation_flavor_messages` — L957–978

Add optional params: `truth: TurnTruth | None = None`, `violations: str | None = None`.

- When `truth`: append `format_turn_truth_for_prompt(truth)` instead of standalone `_committed_state_flavor_block()`.
- When `violations`: append retry instruction block.
- Keep global banter-only instruction; remove redundant catalog hints now in truth block.

#### 3.4 Wire nine call sites

Replace `_narrate_flavor(...)` / `_creation_table_flavor` / `_narrate_creation_flavor` with `narrate_with_verification(...)` at lines documented in Flow C. Use the **per-step flag table** — not a blanket `body_pending=True`:

| Step(s) | `body_pending` | `flavor_only` | Notes |
|---------|----------------|---------------|-------|
| NAME | `False` | `True` | Static name prompt in `body`; length → retry/fallback, not discard |
| RACE, CLASS, SKILLS, SPELL_SCHOOLS, SPELLS, EQUIPMENT_GOLD, ROLL_STATS, FINALIZE | `True` | `False` | Code table / summary appended in compose |

`_creation_table_flavor` / `_narrate_creation_flavor` forward the same flags from their presenter.

#### 3.5 `_narrate_flavor` tweak — L990–1007

Option A (minimal): set `self._last_finish_reason = response.get("finish_reason", "")` for length stub consumer.

Option B: return `(content, finish_reason)` — update only `narrate_with_verification` caller.

Keep API exception fallback L1003–1004 unchanged.

#### 3.6 Imports — L19–50

Add: `build_creation_turn_truth` from `gm.creation`; `TurnTruth`, `format_turn_truth_for_prompt`, `verify_narration` from `gm.narration_verify`; verify log helpers from `gm.logger`.

---

### 4. Logging — `app/gm/logger.py` (N8)

Add after `log_llm_response` L88–94:

```python
def log_narration_verify_fail(*, mode: str, step: str | None, violations: list[str], attempt: int): ...
def log_narration_verify_pass(*, mode: str, step: str | None, attempts: int): ...
def log_narration_verify_exhausted(*, mode: str, step: str | None, attempts: int): ...
```

Each calls `log_entry("narration_verify_fail"|..., {...})` with fields from orchestrator spec § Observability. Sync `tmp/app-logging-qa-spec.md` on ticket close (deferred during impl per qa-spec note 4).

---

### 5. Prompt hygiene — `app/gm/system_prompt.py` (N9)

Trim **creation-only** conflicts L29–38:

| Current (L) | Change |
|-------------|--------|
| L21–25 global table mandate | Add caveat: "During Registry creation desk, code appends tables — flavor is banter only." |
| L33: "MUST list ALL 16 races in a table" | Replace with: "Registry desk steps use code-owned tables; write banter only; obey Authoritative facts block." |
| L34–37: present stats/equipment in tables via LLM | Remove for creation FSM path; tool-loop path unchanged |

Do **not** remove exploration/combat table guidance.

---

### 6. Config — `app/config.yaml`

Add (example):

```yaml
narration:
  llm_max_attempts: 6
  verify_max_retries: 5
  length_max_recovery_retries: 1
```

Wire in `Orchestrator.__init__` with defaults matching domain spec § Config.

---

### 7. Tests — `app/tests/test_narration_verify.py` (new)

Follow stub pattern from `test_creation_flavor_sanitize.py` L15–47 (`_patch_llm_content`).

| Test | Assert |
|------|--------|
| `test_format_turn_truth_spell_schools` | Novice creation state → prompt contains Pyromancy…Divine; no `\| School \|` markdown table |
| `test_verify_sumpty_l4743_fails` | Embedded L4743 flavor → `passed=False`; violations mention Restoration/Evocation or denylist |
| `test_verify_sumpty_l4749_fails` | L4749 excerpt → fail; table + Communion/Warding |
| `test_verify_sumpty_l4755_fails` | L4755 excerpt → fail; economy (50 gold) + premature delve |
| `test_verify_benign_banter_passes` | `"The clerk adjusts her spectacles."` → pass for SPELL_SCHOOLS truth |
| `test_narrate_with_verification_mock_retry` | Stub LLM: bad prose ×2 then good → composed narration flavor region has no Restoration; only good line |
| `test_narration_verify_exhausted` | Stub always bad → flavor region empty or fallback; no denylist terms; exhausted event logged (caplog or mock `log_entry`) |
| `test_name_length_flavor_only_retry_or_fallback` | Stub `finish_reason=length` on NAME step → one retry or static fallback; **not** silent discard; static name prompt body still present |

**Sumpty fixtures** (embed verbatim flavor regions from session L4743/L4749/L4755 — see Flow D).

**Regression trio** (must stay green):

```bash
cd app && python -m pytest tests/test_narration_verify.py -q
cd app && python -m pytest tests/test_creation_flavor_sanitize.py -q
cd app && python -m pytest tests/test_creation_flow.py -q
cd app && python -m pytest tests/ -q
```

---

## Implementation order (suggested)

1. `narration_verify.py` — types, `format_turn_truth_for_prompt`, `verify_narration` + unit tests for Sumpty/benign.
2. `creation.py` — `build_creation_turn_truth` + unit test for truth shape.
3. `logger.py` — verify event helpers.
4. `orchestrator.py` — `narrate_with_verification`, `_creation_flavor_messages` refactor, wire 9 sites.
5. `system_prompt.py` — hygiene trim.
6. `config.yaml` + `Orchestrator.__init__` config read.
7. Integration tests (mock retry, exhausted).
8. Full suite + domain spec changelog on close.

---

## Acceptance mapping (Phase 1 batch close)

| AC | Plan section |
|----|--------------|
| TurnTruth + build_creation_turn_truth | §1, §2 |
| format_turn_truth in _creation_flavor_messages | §3.3 |
| verify_narration creation rules | §1.4 |
| narrate_with_verification on all paths | §3.2, Flow C |
| APP-079 length before verify (NAME vs gated steps) | §Approach, §3.2, Flow C, §7 `test_name_length_*` |
| Sumpty fail + mock retry pass | §7 |
| Supersede APP-082/078/059/073 creation docs | spec/domain changelog on close |
| verify→retry→publish canonical | §Approach, orchestrator spec already updated |

---

## Risks & mitigations

| Risk | Mitigation |
|------|------------|
| Over-aggressive verify false positives | Denylist + allowlist-first on SPELLS; word-boundary regex; benign banter test |
| 079 not landed | Inline stub: `body_pending` discard + `flavor_only` NAME retry/fallback; import hook documented |
| Latency (extra LLM calls) | Cap at 6 attempts; log `attempts` |
| `_narrate_flavor` finish_reason not exposed | Minimal `self._last_finish_reason` stash |
| F4 vs truth block drift | Fold committed fields into `format_turn_truth_for_prompt`; note F4 cross-ref on close |

---

## Expected files (stay in scope)

| File | Action |
|------|--------|
| `app/gm/narration_verify.py` | **new** |
| `app/gm/creation.py` | add `build_creation_turn_truth` |
| `app/gm/orchestrator.py` | `narrate_with_verification` + wiring |
| `app/gm/system_prompt.py` | Phase 1 hygiene |
| `app/gm/logger.py` | verify events |
| `app/tests/test_narration_verify.py` | **new** |
| `app/config.yaml` | narration config keys |
| `tmp/app-llm-orchestrator-spec.md` | changelog on close only |
| `tmp/app-character-creation-spec.md` | F4 cross-ref + changelog on close |

**Out of scope:** `_llm_loop`, combat loop, `tmp/app-logging-qa-spec.md` (sync on close), exploration/combat unit tests in ticket AC.

---

## Handoff

**Ready for:** QA plan gate round 2 (Stage 3b) → implementation dispatch after plan PASS  
**Escalate human if:** APP-079 lands mid-impl and conflicts with inline length stub; or verify false-positive rate blocks desk playtest
