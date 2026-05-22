# QA Report: spec — round 1

**Task:** app-031-transcript-sanitize-orphan-tool-messages  
**backlog_ticket:** APP-031  
**ticket_path:** [tmp/backlog/app-031-transcript-sanitize-orphan-tool-messages.md](../../app-031-transcript-sanitize-orphan-tool-messages.md)  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)  
**domain_spec_creation:** not_needed (registry_gap false)

## Findings

### TICKET-001 — blocker

- **Location:** Ticket § Expected files vs `spec.md` § Affected paths / § Test plan; domain spec § Tests (APP-031) (`tests/test_transcript_sanitize.py`)
- **Issue:** Run spec and domain spec require a **new** pytest module `app/tests/test_transcript_sanitize.py` (eight unit/integration cases including Holt fixture and `_llm_loop` wrapper assertion), but ticket **Expected files** lists only `app/gm/orchestrator.py`. Run spec L130 explicitly notes the test file is “not in ticket Expected files.” Backlog hooks and Dev plan gate treat Expected files as the edit allow-list.
- **Implementation gap:** Dev cannot land AC-verifying tests without ticket amendment; plan QA will FAIL on scope mismatch; hooks may deny `app/tests/` writes mid-impl.
- **Suggested fix:** Extend ticket Expected files to include `app/tests/test_transcript_sanitize.py` (and keep `tmp/app-llm-orchestrator-spec.md` under spec-sync on close — exempt from hooks). Mirror path in `spec.md` § Affected paths without the deferral footnote.

### SPEC-001 — major (non-blocking)

- **Location:** `spec.md` R1 (“worst case returns a safe prefix (at minimum system + last user if entire tail is invalid)”); domain spec § Invariants (no equivalent row)
- **Issue:** Tail-truncation fallback is normative in run R1 but has no test row, no algorithm steps, and no domain-spec mirror. Edge cases (messages with only `system`, no `user`, empty input) undefined.
- **Implementation gap:** Two implementers could diverge on prefix selection; pytest matrix cannot regress the contract.
- **Suggested fix:** Either (a) add `test_tail_invalid_returns_safe_prefix` with explicit input/output fixture, or (b) narrow R1 to “never raise; drop invalid tail only” and remove “safe prefix” language if full-array walk is sufficient for v1.

### SPEC-002 — minor (non-blocking)

- **Location:** `spec.md` R1 purity contract vs domain spec (silent on mutability)
- **Issue:** Run spec allows “returns new list **or** shallow-copies” and optional in-place mutation “if documented and tested.” Domain spec does not pick one contract.
- **Suggested fix:** Dev plan should pin non-mutating behavior (preferred for shared helper) and add one test that caller list is unchanged after sanitize.

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | Valid P1 feature; `in_progress`; domain spec field matches orchestrator owner |
| registry_gap | **PASS** | false — `app-master-spec.md` LLM orchestrator row; research-brief justified |
| Domain spec present / synced | **PASS** | § Transcript sanitize (APP-031) in `tmp/app-llm-orchestrator-spec.md`; checklist + changelog updated |
| Run spec ↔ domain spec | **PASS** | Invariants, wire points (6 sites), APP-028 reorder, tests aligned |
| AC testability | **PASS** (content) | Ticket AC maps to R2–R4 + domain invariants + pytest matrix |
| Code traces | **PASS** | Six `chat_completion` call sites verified at L1046, L1673, L1700, L2047, L2132, L2212; APP-028 system-before-tool pattern at L2276–2287 |
| AGENTS.md / drift policy | **PASS** | Behavior in domain spec; orchestrator-only scope; no canon drift |
| APP-032 boundary | **PASS** | Clear pairing — see below |
| Scope ⊆ Expected files | **FAIL** | TICKET-001 |

## APP-032 boundary (confirmed clear)

| Layer | APP-031 | APP-032 |
|-------|---------|---------|
| **When** | Proactive — every pre-send | Reactive — on malformed-transcript 400 |
| **Action** | `sanitize_transcript_messages` enforces invariants | Truncate to safe prefix → reuse same helper → retry **once** |
| **Scope** | No 400 detection, no history truncation, no retry loops (R6) | Owns catch/truncate/retry |
| **Shared primitive** | Export/importable helper for 032 reuse | Must not duplicate repair logic |
| **Docs** | Run spec R6 + Non-goals table; domain § APP-031 vs APP-032; ticket Notes “Pair with APP-032” |

No overlap or ambiguity that would block either ticket’s implementation order (**031 prevent → 032 recover**).

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Sanitize transcript: no orphan tool messages without preceding `tool_calls` | R2 invariants; domain § Invariants; R4 wire all six call sites | Yes — unit + mock `_llm_loop` | **PASS** (spec content) |
| (Process) spec sync on close | Domain § + changelog 2026-05-22 | Process | **PASS** |
| Land tests proving AC | `test_transcript_sanitize.py` matrix | Blocked | **FAIL** — TICKET-001 |

## Verified (code evidence)

| Claim | Evidence |
|-------|----------|
| No transcript sanitizer today | `grep sanitize_transcript` — absent; `openrouter.chat_completion` pass-through |
| Six orchestrator `chat_completion` sites | `orchestrator.py` L1046, L1673, L1700, L2047, L2132, L2212 |
| APP-028 system inserted before tool on failure | `orchestrator.py` L2276–2287 (exploration); research cites combat ~L2091–2098 |
| 400 today → fallback, no repair | `orchestrator.py` L2220–2224 (`log_error`; APP-032 gap) |
| Persisted history has no tool roles | research-brief + `_restore_history` pattern |
| APP-080 normalizes args but not transcript | `normalize_tool_args` at L2260; transcript append unchanged |
| `test_transcript_sanitize.py` absent | Expected at spec stage |

## Summary

Run `spec.md` and domain § Transcript sanitize (APP-031) are **strong**: Holt regression context, OpenAI tool-message invariants, APP-028 reorder rule, six verified wire points, shared helper for APP-032, and a concrete pytest matrix. `registry_gap` is correctly **false**. **APP-032 boundary is clear** (proactive sanitize vs reactive 400 retry; shared `sanitize_transcript_messages`).

**FAIL** on one blocker: ticket **Expected files** omit `app/tests/test_transcript_sanitize.py`, which hooks and plan QA require before Dev plan/impl. Address TICKET-001 in PM revision round 2; optionally tighten R1 tail-fallback (SPEC-001) and mutability contract (SPEC-002) in plan phase.

**Blocker count:** 1 blocker (TICKET-001) + 1 major + 1 minor (non-blocking).

## Re-review focus

- Ticket Expected files include `app/tests/test_transcript_sanitize.py`
- Remove “not in ticket Expected files” deferral from `spec.md` § Affected paths
- Optional: tail-fallback test or narrowed R1 wording; pinned non-mutating helper contract
