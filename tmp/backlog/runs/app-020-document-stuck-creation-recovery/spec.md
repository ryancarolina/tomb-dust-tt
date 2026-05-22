# Spec: APP-020-document-stuck-creation-recovery

**Status:** draft (PM round 1)  
**backlog_ticket:** APP-020  
**ticket_path:** [tmp/backlog/app-020-document-stuck-creation-recovery.md](../../app-020-document-stuck-creation-recovery.md)  
**domain_spec:** [tmp/app-session-persistence-spec.md](../../../app-session-persistence-spec.md)  
**registry_gap:** false  
**Domain specs touched:** `tmp/app-session-persistence-spec.md`

## Problem

Engineering recovery for **stuck partial character creation** is implemented (APP-014/015/019, APP-064 boot path, APP-071 resume failure copy) but **not surfaced** in the player README. [`app/README.md`](../../../../app/README.md) line 15 claims the app "auto-resumes if `session_state.json` or a workspace save exists" — **incorrect** after APP-064: boot uses **`bridge.has_save()`** only (living slotted character), not app autosave alone. Mid-creation partial saves show the **new-game-only** startup path; players who quit mid-desk need explicit guidance to type **`new game`**.

## Goals

- **P0:** Add a player-facing **stuck creation recovery** section in `app/README.md`: symptoms → type **`new game`** → data-loss warning.
- **P0:** Correct Quick Start / Features persistence wording so it matches APP-064 (finished save vs partial creation).
- **P0:** Document domain-spec behavior checklist for README sync (§ Stuck creation recovery — player documentation).

## Non-goals

| Deferred | Note |
|----------|------|
| Code changes to orchestrator, UI, or bridge | Expected files: **`app/README.md` only** |
| New pytest for README prose | Acceptance = checklist review against domain spec § APP-020 |
| Hand-editing `session_state.json` / workspace DB | Forbidden for players per AGENTS.md |
| `tomb_gm` CLI / Cursor chat GM | Obsolete play paths — do not document |
| Mid-creation **continue** without engine save | APP-018 restore on load/continue — README may mention **`load game`** only for **finished** saves |
| Full APP-019 error catalog in README | Brief retry hint only |

## Requirements (summary)

Full doc contract lives in domain spec § **Stuck creation recovery — player documentation (APP-020)**.

| ID | Summary | Domain spec |
|----|---------|-------------|
| **D1** | New README subsection: "Stuck during character creation?" (or equivalent) | § Player README content |
| **D2** | List common stuck symptoms (repeated prompts, wrong step, blank GM, setup error footer) | § Symptoms |
| **D3** | Recovery: type **`new game`** (`start` / `new` accepted); wipes in-progress creation + workspace campaign data | § Recovery command |
| **D4** | Contrast **finished save** (`load game`) vs **partial creation** (`new game` reset) | § Partial vs finished save |
| **D5** | Fix Quick Start line 15 — no "auto-resumes" when only `session_state.json` exists | § Quick Start correction |
| **D6** | Align Features "Session persistence" bullet with boot vs load behavior | § Features correction |
| **D7** | Suggest retry one clerk input before wipe when glitch is transient | § When to retry first |

## Acceptance criteria mapping

| Ticket AC | Spec / deliverable |
|-----------|-------------------|
| `app/README.md` documents stuck creation → type **`new game`** | D1–D3 |
| Domain spec updated on close | § APP-020 + changelog |
| No code drift | README matches existing `setup_new_game()` behavior (§ APP-014, APP-015) |

## Implementation pointers (Dev plan)

| Area | Path | Notes |
|------|------|-------|
| Target doc | `app/README.md` | Only Expected file |
| Placement | After **Quick Start** or under **Features** | PM preference: dedicated subsection after Quick Start |
| Quick Start fix | Line 15 | Replace auto-resume claim with: finished saves offer **`load game`** at relaunch; partial creation uses **`new game`** |
| Features fix | Line 59 | "auto-saves every 60s" OK; "restores on relaunch" → qualify **load game** for finished saves |
| Behavior source | `app/gm/orchestrator.py` `setup_new_game`, `process_turn` | No edits — reference only |
| Startup UX | `app/ui/app.py` `_init_orchestrator` | APP-064 chips when `has_save()` false |
| In-app recovery copy | APP-071 variant B, APP-019 failure | README must align, not contradict |

**Suggested README outline (Dev):**

1. **Quick Start** — corrected resume sentence + link to stuck section.
2. **Stuck during character creation?** — bullets: symptoms; "type **`new game`**"; progress lost; **`load game`** only when you had a living character on roster.
3. **Features** — persistence bullet qualified.

## Test plan

No automated README tests. QA spec/plan gates:

- [ ] README contains stuck-creation subsection with **`new game`** recovery.
- [ ] Quick Start no longer implies boot auto-restore from `session_state.json` alone.
- [ ] Wipe warning present (in-progress creation lost).
- [ ] No instruction to edit saves by hand or use `tomb_gm` CLI.
- [ ] Prose matches domain spec § APP-020 checklist.

Manual cross-check (optional, maps APP-014 human-test-plan):

```bash
cd app && python main.py
# Partial creation → Escape quit → relaunch → README says new game, not load
```

## Human playtest hints (for Stage 7)

- **Doc-only ticket:** Human plan = read README while reproducing APP-014 TC-1 (partial creation → relaunch → **`new game`**).
- Player following README only (no spec) can recover from stuck creation without hand-editing files.
- After finalize + quit, README still correctly describes **`load game`** path.

## Affected paths

Must match ticket **Expected files**:

- `app/README.md`
- `tmp/app-session-persistence-spec.md` — § Stuck creation recovery — player documentation (APP-020); checklist + changelog on close

## Pointers (source of truth)

| Topic | Location |
|-------|----------|
| Player doc contract & checklist | [`tmp/app-session-persistence-spec.md`](../../../app-session-persistence-spec.md) § Stuck creation recovery — player documentation (APP-020) |
| Recovery behavior | Same spec § setup_new_game lifecycle (APP-014), § New game — creation block clear (APP-015), § New game failure (APP-019) |
| Boot vs save | Same spec § Startup save-detection (APP-064) |
| Load failure copy | Same spec § Resume failure (APP-071) |
| Research traces | [`research-brief.md`](research-brief.md) |
| Manual repro | [`../app-014-setupnewgame-session-lifecycle/human-test-plan.md`](../app-014-setupnewgame-session-lifecycle/human-test-plan.md) TC-1 |
| Play rule | [`AGENTS.md`](../../../../AGENTS.md) — PyGame `app/main.py` canonical |

## Changelog

| Date | Change |
|------|--------|
| 2026-05-22 | Initial PM draft (APP-020) — doc chore; domain spec § APP-020 |
