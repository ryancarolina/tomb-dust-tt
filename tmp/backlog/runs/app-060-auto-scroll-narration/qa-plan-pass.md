# QA PASS: plan — round 1

**Task:** app-060-auto-scroll-narration  
**backlog_ticket:** APP-060  
**ticket_path:** [tmp/backlog/app-060-auto-scroll-narration-on-input-and-response.md](../../app-060-auto-scroll-narration-on-input-and-response.md)  
**Round:** 1  
**domain_spec_creation:** not_needed (`registry_gap: false`)

**Verdict:** PASS

**Reviewer role:** QA (adversarial)

## Verified

- [x] Backlog ticket valid; status `in_progress`; domain spec `tmp/app-pygame-ui-spec.md`
- [x] Plan files ⊆ ticket Expected files (strict four-file scope)
- [x] Acceptance criteria testable — ticket AC + spec R1–R4 mapped in § Acceptance criteria mapping
- [x] Code traces match repo (independent verification below)
- [x] AGENTS.md / canon compliance (app UI only; no mechanics drift)
- [x] Tests/commands listed (`test_narration_scroll.py`, regressions, manual repro)
- [x] Spec R1–R4 coverage in plan (layout-correct pin, queue matrix incl. **error**, always-follow policy, unit module)
- [x] Out-of-scope boundaries explicit (session load, resize, animated scroll, `_target_scroll`)
- [x] APP-036 batch overlap noted (sequential Stage 7a)

## Plan files ⊆ Expected files

| Plan change target | In ticket Expected files? |
|--------------------|---------------------------|
| `app/ui/panels/narration.py` — `_follow_tail`, `request_follow_tail()`, `draw()` tail block, `clear()` reset | Yes |
| `app/ui/app.py` — `_smooth_scroll_to_bottom()` → follow API; **error** handler tail follow | Yes |
| `app/tests/test_narration_scroll.py` (new) | Yes |
| `tmp/app-pygame-ui-spec.md` — checklist + changelog on close | Yes |

No files outside ticket Expected files.

## Spec / ticket AC → plan / tests

| Requirement | Plan locus | Test / mechanism |
|-------------|------------|------------------|
| R1 layout-correct pin after `_total_height` known | §1 `_follow_tail` in `draw()` after `_rebuild()` | `test_stale_scroll_before_rebuild_fails`, `test_request_follow_tail_after_draw_pins_bottom` |
| R1 single rebuild per dirty frame | §1.3 apply tail after one `_rebuild()` in `draw()` | coalesce test + Flow A frame order |
| R2 `player` / `narration` / `narration_text` follow tail | §2.1–2.3, Flow B/C | existing call sites + tall-content tail test |
| R2 **error** follow tail (AC gap) | §2.2 error handler wiring | `test_error_line_follows_tail` |
| R2 non-paths (`clear_narration`, status, etc.) | Flow F matrix | no new call sites |
| R3 always-follow on new queued content | § Approach policy + Flow E | manual history + submit (Stage 7) |
| R3 wheel scroll unchanged | Flow E; §2.4 do-not-touch | regression via existing wheel path |
| R4 unit module required | §3 `test_narration_scroll.py` | pytest command in § Tests |
| Ticket: player submit visible | §2.3 + §3 player test | unit + manual creation submit |
| Ticket: GM full content (tables, paragraphs) | §3 table fixture + Flow B | tall-content tests + manual |
| Ticket: manual scroll up; new content returns bottom | R3 always-follow via queue calls | manual (Stage 7) |
| Ticket: domain spec § Narration scroll behavior | §4 PM draft exists; close checklist | release gate |

## Code trace verification

| Claim | Repo evidence | Match |
|-------|---------------|-------|
| Frame order: queue → wheel → draw | `app.py:87–92` | ✓ |
| Stale scroll on `player` / `narration` / `narration_text` | `app.py:163–171` → `_smooth_scroll_to_bottom()` → `scroll_to_bottom()` | ✓ |
| Error append, **no** scroll today | `app.py:202–204` — `add_line` only | ✓ |
| `_smooth_scroll_to_bottom` instant, not animated | `app.py:225–226` | ✓ |
| `add_line` / `add_lines` defer rebuild | `narration.py:51–58` sets `_dirty = True` only | ✓ |
| `scroll_to_bottom()` uses current `_total_height` | `narration.py:72–73` | ✓ |
| `_rebuild()` only in `draw()` when dirty | `narration.py:161–163` | ✓ |
| `clear()` resets offset, no follow flag yet | `narration.py:60–65` | ✓ (plan adds `_follow_tail` reset) |
| Player submit queues `("player", text)` | `app.py:253–265` | ✓ |
| Turn success queues `("narration_text", …)` | `app.py:300` | ✓ |
| Turn/init errors queue `("error", …)` | `app.py:151–152`, `281`, `316–318` | ✓ |
| Wheel momentum independent | `app.py:65–67`, `212–217` | ✓ |

## Gates (summary)

| Gate | Result | Notes |
|------|--------|-------|
| Ticket gate | **PASS** | APP-060 `in_progress`; four Expected files |
| Plan ⊆ Expected files | **PASS** | No scope creep |
| Spec R1–R4 in plan | **PASS** | PM-preferred `_follow_tail`; error path committed |
| Code traces | **PASS** | Line refs spot-checked against live `app.py` / `narration.py` |
| Test plan vs `qa-spec-pass` | **PASS** | All R4 minimum cases covered for shipped API |
| AC mapping | **PASS** | § Acceptance criteria mapping complete |
| Batch / merge risk | **PASS** | APP-036 note present |

## Adversarial notes (non-blocking — implementation QA)

1. **Tall-content fixture** — §3 describes table block but not verbatim string; impl may need one iteration if 120px viewport + font metrics differ on CI (Dev reflection flagged same).
2. **`add_lines` / `narration_text` paths** — No dedicated unit test; same `request_follow_tail()` + `draw()` mechanism as `add_line`. Panel tall-content + player/error tests sufficient for v1; impl QA may add `add_lines` case if tail pin fails on batch startup only.
3. **App-level error queue test** — Plan marks optional; spec R4 does not require it. Panel error test + single error-handler wiring point acceptable.
4. **`clear()` + pending `_follow_tail`** — Defensive reset in plan (not in PM spec prose) is correct for same-frame clear edge case.
5. **APP-036 merge** — Both touch `app/ui/app.py`; follow batch board sequential Stage 7a when landing commits.

## Summary

`plan.md` implements the qa-spec-pass-approved `_follow_tail` approach with correct frame-order traces, all four queue scroll paths (including the missing **error** wiring), defensive `clear()` reset, and a complete R4 test matrix within ticket scope. Ready for workstreams + implementation (Stage 4).

## Re-review focus

_None — proceed to Dev workstreams + implementation._
