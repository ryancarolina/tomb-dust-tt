# QA Report: spec — round 1

**Task:** app-024-block-site-fiction  
**backlog_ticket:** APP-024  
**Verdict:** FAIL  
**Reviewer role:** QA (adversarial)

## Findings

### SPEC-001 — blocker

- **Location:** `spec.md` E1 (L42–43); `tmp/app-exploration-delve-spec.md` § Site-entry fiction gate (L40); `research-brief.md` L115–116
- **Issue:** Spec text says entry is committed if **`enter_dungeon` / `site_enter` succeeded “anywhere in the current turn's `_llm_loop` chain”**, but the proposed signal is **`_last_tool_results[tool_name]`** after the loop. In `app/gm/orchestrator.py` L1978, each tool name is **overwritten** on every call (`self._last_tool_results[fn_name] = result`). A successful `enter_dungeon` followed by a failed retry (or a second call with the same name) leaves `ok: false` in the dict even though entry already committed — gate would strip legitimate post-entry prose or block fiction after a real commit.
- **Implementation gap:** E1/E3 bypass and `test_surface_successful_enter_dungeon_allows_fiction` assume “any success in chain”; implementers following `_last_tool_results` alone will ship a latent bug.
- **Suggested fix:** Replace dict lookup with an explicit **`entry_committed_this_turn: bool`** set to `True` on first `ok: true` for either tool inside `_llm_loop` (depth 0), **or** scan accumulated per-turn results (list/flag), not final dict slot. Align domain spec § Entry committed and E1 wording; add test: successful `enter_dungeon` then failed `enter_dungeon` + entry prose → fiction **retained**.

### TICKET-001 — blocker

- **Location:** `tmp/backlog/app-024-block-site-fiction-without-enter-tool.md` § Acceptance criteria (L18)
- **Issue:** Ticket AC still reads *“unless **last** tool was successful `enter_dungeon` / `site enter`”* — not testable as written and contradicts run spec § Entry commit vs engine mode (L52–56), which correctly requires **any successful entry tool in the turn chain**. A later failed `search_site` or `set_phase` must not revoke an earlier successful entry. Ticket file was not updated when PM clarified semantics.
- **Suggested fix:** Rewrite ticket AC to match domain spec (e.g. *“unless the current turn's tool chain includes a successful `enter_dungeon` or `site_enter` (`ok: true`)"*). Add mapping row in ticket or mirror run `spec.md` § Acceptance criteria mapping.

### SCOPE-001 — non-blocker (plan gate)

- **Location:** `spec.md` test plan (L76–96); ticket Expected files (orchestrator.py only)
- **Issue:** Spec mandates `app/tests/test_exploration_site_entry_gate.py`; ticket **Expected files** omit it. Hooks/plan QA will block impl unless ticket is amended.
- **Suggested fix:** Before Stage 4, add test file to ticket Expected files (PM note L96 already flags this — execute at plan phase).

### NOTE-001 — non-blocker (orchestrator spec cross-link)

- **Location:** `tmp/app-llm-orchestrator-spec.md` § Mechanical truth (L13–15); open-work checklist (L103)
- **Issue:** Mechanical truth already requires `ok: true` for site entry; exploration spec documents APP-024 gate. LLM orchestrator spec does not list APP-024 in checklist or wire points — dual ownership is acceptable per master registry, but implementers may miss the `_llm_loop` early-return fix.
- **Suggested fix:** On close, add one checklist bullet + changelog pointer to exploration § Site-entry fiction gate, or a single cross-link under § Mechanical truth.

### NOTE-002 — non-blocker (refusal copy)

- **Location:** `tmp/app-exploration-delve-spec.md` L54–55; `spec.md` E6 (L47)
- **Issue:** Code-owned refusal line deferred to implementation (“e.g. entrance waits…”). Acceptable for spec draft (mirrors APP-070 pattern) if `plan.md` pins exact string for tests.
- **Suggested fix:** Dev plan should freeze refusal copy before impl QA.

## Verified (no blocker)

| Check | Evidence |
|-------|----------|
| Backlog ticket valid | APP-024 `in_progress`; domain spec linked |
| `registry_gap: false` | `research-brief.md` L11–15; exploration spec owns behavior |
| Surface-only gate clarity | Domain spec table L34–38; E2/E3; bypass when `dungeon`/`site` |
| Dual entry tools | E8; domain L40; tests `test_successful_site_enter_allows_fiction` |
| `all_failed + content` path | Code `orchestrator.py` L1999–2006; E5; domain § Wiring (3) |
| Implementation locus ⊆ orchestrator | Affected paths `orchestrator.py` only; E7 optional logger called out |
| LLM mechanical-truth alignment | `app-llm-orchestrator-spec.md` L15 consistent with exploration § L30 — no contradictory rules |
| Code traces | `_llm_loop` no sanitizer today; `_emit_narration` L317; entry tools L2050–2090 — match research |
| Test plan testable | Six cases + pytest commands (once SPEC-001/TICKET-001 fixed) |
| APP-077 coordination | E9; domain § order strip → footer |

## Summary

Spec is strong on surface-only gating, dual `enter_dungeon`/`site_enter`, and the `all_failed and content` leak path (verified at `orchestrator.py` L1999–2006). **FAIL** because entry-commit detection contradicts real `_last_tool_results` semantics and ticket AC still says “last tool.” PM must fix E1/domain § Entry committed + ticket AC before Dev plan.

## Re-review focus

1. E1 uses explicit per-turn flag or full-chain scan — not final dict slot alone; add regression test for success-then-failed-same-tool.
2. Ticket AC rewritten to match clarified semantics.
3. (Plan) Add `app/tests/test_exploration_site_entry_gate.py` to ticket Expected files.
4. Optional: pin refusal-line copy in domain spec or `plan.md`.
