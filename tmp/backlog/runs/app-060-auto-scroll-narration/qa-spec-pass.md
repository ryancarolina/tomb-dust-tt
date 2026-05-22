# QA PASS: spec — round 1

**Task:** app-060-auto-scroll-narration
**backlog_ticket:** APP-060
**ticket_path:** [tmp/backlog/app-060-auto-scroll-narration-on-input-and-response.md](../../app-060-auto-scroll-narration-on-input-and-response.md)
**Round:** 1
**domain_spec_creation:** not_needed (registry_gap false)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Dispatch note

Dispatch prompt cited `APP-036`; run folder, `status.md`, and artifacts are **APP-060**. This review covers APP-060 only.

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec field = `app-pygame-ui-spec.md`
- [x] Ticket Expected files ⊆ run `spec.md` § Affected paths (no hook allow-list gap)
- [x] Acceptance criteria testable (R1–R4, ticket AC, pytest + manual commands)
- [x] Code traces match repo (independent verification below)
- [x] AGENTS.md / canon compliance (app UI only; no mechanics drift)
- [x] Tests/commands listed (`test_narration_scroll.py`, `test_ui_map_creation_gate.py` regression)
- [x] registry_gap false — `tmp/app-pygame-ui-spec.md` owns § Narration scroll behavior
- [x] Every ticket AC row mapped in run spec + domain spec

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | P1 bug; in_progress; four Expected files aligned |
| registry_gap | **PASS** | false; no new domain spec |
| AC testability | **PASS** | Layout-correct pin, queue paths, policy, unit + manual |
| Code traces | **PASS** | Root cause confirmed at cited paths |
| Domain spec sync | **PASS** | § Narration scroll behavior + Tests + file map + changelog draft |
| Expected files ⊆ spec | **PASS** | `narration.py`, `app.py`, domain spec, `test_narration_scroll.py` |

## Code trace verification

| Claim | Repo evidence | Match |
|-------|---------------|-------|
| `add_line` / `add_lines` defer rebuild | `narration.py:51–58` sets `_dirty = True` only | ✓ |
| `scroll_to_bottom()` uses stale `_total_height` | `narration.py:72–73` before `draw()` rebuild | ✓ |
| `_rebuild()` only in `draw()` when dirty | `narration.py:161–163` | ✓ |
| Queue scroll on player / narration / narration_text | `app.py:163–171` → `_smooth_scroll_to_bottom()` | ✓ |
| Error path append, no scroll | `app.py:202–204` — `add_line` only | ✓ |
| `_smooth_scroll_to_bottom` is instant, not animated | `app.py:225–226` → `scroll_to_bottom()` | ✓ |
| Frame order queue → wheel → draw | `app.py:87–92` | ✓ |
| Wheel scroll independent | `app.py:65–67`, `212–217` | ✓ |

## Acceptance criteria mapping

| Ticket AC | Spec / domain | Testable | QA |
|-----------|---------------|----------|-----|
| Player submit pins player line | R2 queue matrix; domain § Queue paths `player` | unit + manual creation submit | **PASS** |
| GM response full content (narration, narration_text, error) | R1 layout-correct pin; R2 all three types | unit tall content + manual long reply | **PASS** |
| Scroll after height known | R1 `_follow_tail` in `draw()` (preferred) or rebuild-before-scroll alt | stale vs fixed pytest | **PASS** |
| Tables / multi-paragraph without wheel | R2 manual repro; R4 tall-content tests | manual + unit | **PASS** |
| Manual scroll up; new content returns to bottom | R3 always-follow policy; domain § Tail-follow policy | manual history + submit | **PASS** |
| Domain spec § Narration scroll behavior | domain spec L38–105; R6 via changelog on close | review | **PASS** |

## Adversarial notes (non-blocking)

1. **Always-follow policy** — Ticket AC allows near-bottom-only; PM chose always-follow and documents deferral. Product may revisit at playtest; spec satisfies AC wording.
2. **APP-036 batch overlap** — Both touch `app/ui/app.py`; spec notes sequential Stage 7a. Dev plan should call out merge order per batch board.
3. **APP-090 multi-chunk narration** — Non-goals note coalesce expectation; no per-chunk scroll spec. `_follow_tail` flag should suffice; plan QA can confirm.
4. **Session load / resize** — Explicitly out of scope; acceptable per ticket.
5. **`_smooth_scroll_to_bottom` naming** — Spec allows thin wrapper; rename not required.
6. **Test module not yet present** — Expected at impl; spec correctly requires `app/tests/test_narration_scroll.py`.

## Summary

Run `spec.md` and `tmp/app-pygame-ui-spec.md` § Narration scroll behavior fully cover ticket AC with testable R1–R4 requirements, correct root-cause traces, and aligned Expected files. Implementation-ready for Dev plan.

## Re-review focus

_None — proceed to Dev plan + QA plan gates._
