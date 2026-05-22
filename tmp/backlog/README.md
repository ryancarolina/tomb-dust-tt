# App backlog (`tmp/backlog/`)

Work items for the **Tomb Dust pygame app** (`app/`). Every change under `app/` (and any path listed in a ticket) **must** have a backlog ticket before implementation.

## Workflow

1. **Pick or create a ticket** — copy [`TEMPLATE.md`](TEMPLATE.md); see [`APP-000-example-ticket.md`](APP-000-example-ticket.md).
2. **Set status** to `in_progress` when starting work.
3. **Implement** only files listed in the ticket (update the ticket first if scope grows).
4. **Close** — mark `done`, update domain spec + changelog, run tests from the ticket/spec.
5. **No ticket, no change** — enforced by [`.cursor/rules/tomb-dust-backlog.mdc`](../../.cursor/rules/tomb-dust-backlog.mdc).

## Priority snapshot (P0 — open / in progress)


_All P0 tickets closed._

## Priority snapshot (P1 — open / in progress)

| Ticket | Status | Title |
|--------|--------|-------|
| [APP-025](app-025-registry-hub-loop-integration-test.md) | open | Registry hub loop integration test |
| [APP-030](app-030-combat-integration-test.md) | open | Combat integration test |
| [APP-036](app-036-creation-step-badge-in-ui.md) | in_progress | Creation step badge in UI |
| [APP-039](app-039-gm-tool-for-useitem-and-consumables.md) | open | GM tool for use_item and consumables |
| [APP-040](app-040-economy-playtest-loop-test.md) | open | Economy playtest loop test |
| [APP-059](app-059-standardize-creation-table-outputs.md) | open | Standardize creation table outputs |
| [APP-062](app-062-left-character-panel-inventory-spells-tabs.md) | open | Left character panel — inventory & spells tabs |
| [APP-063](app-063-map-ux-redesign-useful-navigation.md) | open | Map UX redesign — useful navigation |
| [APP-077](app-077-code-owned-exploration-status-footer.md) | open | Code-owned exploration status footer |
| [APP-084](app-084-key-npc-canon-registry.md) | open | Key NPC canon registry + TurnTruth verify |
| [APP-085](app-085-quest-system-key-npc-quests-ui.md) | open | Quest system — key NPC quests, lifecycle, Quests tab UI |
| [APP-086](app-086-inventory-quest-item-bridge.md) | open | Inventory bridge — quest item checks and delivery |
| [APP-087](app-087-narrow-site-entry-sanitizer-quest-prose.md) | open | Narrow site-entry sanitizer for quest/direction prose |
| [APP-088](app-088-defer-remember-fact-until-narrated.md) | open | Defer remember_fact until facts are narrated to the player |
| [APP-089](app-089-encounter-awareness-before-combat.md) | open | Encounter awareness before combat (detect / avoid / ambush) |
| [APP-090](app-090-combat-phased-narration-and-death-beat.md) | open | Combat phased narration and death beat |

## Grooming stats

| Status | Count |
|--------|-------|
| open | 27 |
| in_progress | 1 |
| done | 60 |
| **Total** | **93** |

_Last README rebuild from ticket files — run `python tmp/backlog/_build_readme.py` after bulk status changes._

## Full index

| ID | Priority | Type | Title | Domain spec | File |
|----|----------|------|-------|-------------|------|
| [APP-001](app-001-fix-site-passage-edge-types.md) | P0 | bug | Fix site passage edge types | [app-exploration-delve-spec.md](../app-exploration-delve-spec.md) | `app-001-fix-site-passage-edge-types.md` |
| [APP-002](app-002-log-creationdrift-events.md) | P0 | feature | Log creation_drift events | [app-logging-qa-spec.md](../app-logging-qa-spec.md) | `app-002-log-creationdrift-events.md` |
| [APP-003](app-003-log-creation-step-snapshot-each-turn.md) | P0 | feature | Log creation step snapshot each turn | [app-logging-qa-spec.md](../app-logging-qa-spec.md) | `app-003-log-creation-step-snapshot-each-turn.md` |
| [APP-004](app-004-log-advancedto-on-creation-choice.md) | P0 | feature | Log advanced_to on creation choice | [app-logging-qa-spec.md](../app-logging-qa-spec.md) | `app-004-log-advancedto-on-creation-choice.md` |
| [APP-005](app-005-log-engine-status-after-finalize.md) | P0 | feature | Log engine status after finalize | [app-logging-qa-spec.md](../app-logging-qa-spec.md) | `app-005-log-engine-status-after-finalize.md` |
| [APP-006](app-006-deterministic-creation-tables-from-code.md) | P0 | feature | Deterministic creation tables from code | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-006-deterministic-creation-tables-from-code.md` |
| [APP-007](app-007-code-owned-creation-status-line.md) | P0 | feature | Code-owned creation status line | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-007-code-owned-creation-status-line.md` |
| [APP-008](app-008-hard-gate-exploration-during-creation.md) | P0 | feature | Hard gate exploration during creation | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-008-hard-gate-exploration-during-creation.md` |
| [APP-009](app-009-finalize-gate---non-empty-roster.md) | P0 | feature | Finalize gate — non-empty roster | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-009-finalize-gate---non-empty-roster.md` |
| [APP-010](app-010-persist-creation-across-restart.md) | P0 | feature | Persist creation across restart | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-010-persist-creation-across-restart.md` |
| [APP-011](app-011-invalid-input-at-wrong-creation-step.md) | P0 | feature | Invalid input at wrong creation step | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-011-invalid-input-at-wrong-creation-step.md` |
| [APP-012](app-012-decision-llm-flavor-during-creation.md) | P0 | decision | Decision: LLM flavor during creation | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-012-decision-llm-flavor-during-creation.md` |
| [APP-013](app-013-decision-passage-edge-type-canon.md) | P0 | decision | Decision: passage edge type canon | [app-exploration-delve-spec.md](../app-exploration-delve-spec.md) | `app-013-decision-passage-edge-type-canon.md` |
| [APP-014](app-014-setupnewgame-session-lifecycle.md) | P1 | feature | setup_new_game session lifecycle | [app-session-persistence-spec.md](../app-session-persistence-spec.md) | `app-014-setupnewgame-session-lifecycle.md` |
| [APP-015](app-015-clear-creation-block-on-new-game.md) | P1 | feature | Clear creation block on new game | [app-session-persistence-spec.md](../app-session-persistence-spec.md) | `app-015-clear-creation-block-on-new-game.md` |
| [APP-016](app-016-snapshot-engine-status-on-save.md) | P1 | feature | Snapshot engine status on save | [app-session-persistence-spec.md](../app-session-persistence-spec.md) | `app-016-snapshot-engine-status-on-save.md` |
| [APP-017](app-017-reconcile-empty-roster-on-load.md) | P1 | feature | Reconcile empty roster on load | [app-session-persistence-spec.md](../app-session-persistence-spec.md) | `app-017-reconcile-empty-roster-on-load.md` |
| [APP-018](app-018-continue-restores-creation-state.md) | P1 | feature | Continue restores creation state | [app-session-persistence-spec.md](../app-session-persistence-spec.md) | `app-018-continue-restores-creation-state.md` |
| [APP-019](app-019-surface-new-game-failure-errors.md) | P1 | feature | Surface new game failure errors | [app-session-persistence-spec.md](../app-session-persistence-spec.md) | `app-019-surface-new-game-failure-errors.md` |
| [APP-020](app-020-document-stuck-creation-recovery.md) | P1 | chore | Document stuck-creation recovery | [app-session-persistence-spec.md](../app-session-persistence-spec.md) | `app-020-document-stuck-creation-recovery.md` |
| [APP-021](app-021-enterdungeon-primary-tool-arg.md) | P1 | feature | enter_dungeon primary tool arg | [app-exploration-delve-spec.md](../app-exploration-delve-spec.md) | `app-021-enterdungeon-primary-tool-arg.md` |
| [APP-022](app-022-hint-enterdungeon-on-failed-setphasedelve.md) | P1 | feature | Hint enter_dungeon on failed set_phase(delve) | [app-exploration-delve-spec.md](../app-exploration-delve-spec.md) | `app-022-hint-enterdungeon-on-failed-setphasedelve.md` |
| [APP-023](app-023-friendly-travel-name-to-av-grid.md) | P1 | feature | Friendly travel name to AV-GRID | [app-exploration-delve-spec.md](../app-exploration-delve-spec.md) | `app-023-friendly-travel-name-to-av-grid.md` |
| [APP-024](app-024-block-site-fiction-without-enter-tool.md) | P1 | feature | Block site fiction without enter tool | [app-exploration-delve-spec.md](../app-exploration-delve-spec.md) | `app-024-block-site-fiction-without-enter-tool.md` |
| [APP-025](app-025-registry-hub-loop-integration-test.md) | P1 | feature | Registry hub loop integration test | [app-exploration-delve-spec.md](../app-exploration-delve-spec.md) | `app-025-registry-hub-loop-integration-test.md` |
| [APP-026](app-026-combat-attack-gating.md) | P1 | feature | Combat attack gating | [app-combat-play-spec.md](../app-combat-play-spec.md) | `app-026-combat-attack-gating.md` |
| [APP-027](app-027-validate-monster-id-at-combat-start.md) | P1 | feature | Validate monster id at combat start | [app-combat-play-spec.md](../app-combat-play-spec.md) | `app-027-validate-monster-id-at-combat-start.md` |
| [APP-028](app-028-combat-tool-failure-narration.md) | P1 | feature | Combat tool failure narration | [app-combat-play-spec.md](../app-combat-play-spec.md) | `app-028-combat-tool-failure-narration.md` |
| [APP-029](app-029-auto-chain-monster-turns-after-pc-action.md) | P1 | feature | Auto-chain monster turns after PC action | [app-combat-play-spec.md](../app-combat-play-spec.md) | `app-029-auto-chain-monster-turns-after-pc-action.md` |
| [APP-030](app-030-combat-integration-test.md) | P1 | feature | Combat integration test | [app-combat-play-spec.md](../app-combat-play-spec.md) | `app-030-combat-integration-test.md` |
| [APP-031](app-031-transcript-sanitize-orphan-tool-messages.md) | P1 | feature | Transcript sanitize orphan tool messages | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-031-transcript-sanitize-orphan-tool-messages.md` |
| [APP-032](app-032-400-retry-on-malformed-transcript.md) | P1 | feature | 400 retry on malformed transcript | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-032-400-retry-on-malformed-transcript.md` |
| [APP-033](app-033-sqlite-threading-policy.md) | P2 | feature | SQLite threading policy | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-033-sqlite-threading-policy.md` |
| [APP-034](app-034-log-tool-chain-on-api-errors.md) | P2 | feature | Log tool chain on API errors | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-034-log-tool-chain-on-api-errors.md` |
| [APP-035](app-035-stats-panel-reads-engine-status.md) | P1 | feature | Stats panel reads engine status | [app-pygame-ui-spec.md](../app-pygame-ui-spec.md) | `app-035-stats-panel-reads-engine-status.md` |
| [APP-036](app-036-creation-step-badge-in-ui.md) | P1 | feature | Creation step badge in UI | [app-pygame-ui-spec.md](../app-pygame-ui-spec.md) | `app-036-creation-step-badge-in-ui.md` |
| [APP-037](app-037-block-map-travel-during-creation.md) | P1 | feature | Block map travel during creation | [app-pygame-ui-spec.md](../app-pygame-ui-spec.md) | `app-037-block-map-travel-during-creation.md` |
| [APP-038](app-038-inventory-and-stash-summary-strip.md) | P1 | feature | Inventory and stash summary strip | [app-pygame-ui-spec.md](../app-pygame-ui-spec.md) | `app-038-inventory-and-stash-summary-strip.md` |
| [APP-039](app-039-gm-tool-for-useitem-and-consumables.md) | P1 | feature | GM tool for use_item and consumables | [app-economy-inventory-play-spec.md](../app-economy-inventory-play-spec.md) | `app-039-gm-tool-for-useitem-and-consumables.md` |
| [APP-040](app-040-economy-playtest-loop-test.md) | P1 | feature | Economy playtest loop test | [app-economy-inventory-play-spec.md](../app-economy-inventory-play-spec.md) | `app-040-economy-playtest-loop-test.md` |
| [APP-041](app-041-strip-status-tags-before-tts.md) | P2 | feature | Strip status tags before TTS | [app-tts-narration-spec.md](../app-tts-narration-spec.md) | `app-041-strip-status-tags-before-tts.md` |
| [APP-042](app-042-tts-stop-on-player-interrupt.md) | P2 | feature | TTS stop on player interrupt | [app-tts-narration-spec.md](../app-tts-narration-spec.md) | `app-042-tts-stop-on-player-interrupt.md` |
| [APP-043](app-043-document-tts-voice-keys-in-spec.md) | P2 | chore | Document TTS voice keys in spec | [app-tts-narration-spec.md](../app-tts-narration-spec.md) | `app-043-document-tts-voice-keys-in-spec.md` |
| [APP-044](app-044-startup-health-logging.md) | P2 | feature | Startup health logging | [app-shell-config-spec.md](../app-shell-config-spec.md) | `app-044-startup-health-logging.md` |
| [APP-045](app-045-fail-fast-on-missing-imports.md) | P2 | feature | Fail fast on missing imports | [app-shell-config-spec.md](../app-shell-config-spec.md) | `app-045-fail-fast-on-missing-imports.md` |
| [APP-046](app-046-document-config-keys-in-spec.md) | P2 | chore | Document config keys in spec | [app-shell-config-spec.md](../app-shell-config-spec.md) | `app-046-document-config-keys-in-spec.md` |
| [APP-047](app-047-gamebridge-api-appendix.md) | P2 | chore | GameBridge API appendix | [app-gamebridge-spec.md](../app-gamebridge-spec.md) | `app-047-gamebridge-api-appendix.md` |
| [APP-048](app-048-fix-memoryrecall-topk-param.md) | P2 | bug | Fix memory_recall top_k param | [app-gamebridge-spec.md](../app-gamebridge-spec.md) | `app-048-fix-memoryrecall-topk-param.md` |
| [APP-049](app-049-create-app-tests-package.md) | P1 | chore | Create app/tests package | [app-logging-qa-spec.md](../app-logging-qa-spec.md) | `app-049-create-app-tests-package.md` |
| [APP-050](app-050-ci-or-documented-local-test-gate.md) | P2 | chore | CI or documented local test gate | [app-logging-qa-spec.md](../app-logging-qa-spec.md) | `app-050-ci-or-documented-local-test-gate.md` |
| [APP-051](app-051-golden-path-fixture-with-mock-llm.md) | P2 | feature | Golden path fixture with mock LLM | [app-logging-qa-spec.md](../app-logging-qa-spec.md) | `app-051-golden-path-fixture-with-mock-llm.md` |
| [APP-052](app-052-release-smoke-new-game-through-save-resume.md) | P2 | feature | Release smoke: new game through save/resume | [app-master-spec.md](../app-master-spec.md) | `app-052-release-smoke-new-game-through-save-resume.md` |
| [APP-053](app-053-keep-domain-specs-drift-free.md) | P2 | chore | Keep domain specs drift-free | [app-master-spec.md](../app-master-spec.md) | `app-053-keep-domain-specs-drift-free.md` |
| [APP-054](app-054-app-tests-pytest-green.md) | P2 | chore | app/tests pytest green | [app-master-spec.md](../app-master-spec.md) | `app-054-app-tests-pytest-green.md` |
| [APP-055](app-055-tombgm-tests-pytest-green.md) | P2 | chore | tomb_gm tests pytest green | [app-master-spec.md](../app-master-spec.md) | `app-055-tombgm-tests-pytest-green.md` |
| [APP-056](app-056-validatecontent-clean.md) | P2 | chore | validate_content clean | [app-master-spec.md](../app-master-spec.md) | `app-056-validatecontent-clean.md` |
| [APP-057](app-057-test-creation-flow.md) | P0 | feature | test_creation_flow.py | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-057-test-creation-flow.md` |
| [APP-058](app-058-ui-toggle-narration-tts-on-off.md) | P2 | feature | UI toggle for narration (TTS) on/off | [app-pygame-ui-spec.md](../app-pygame-ui-spec.md) | `app-058-ui-toggle-narration-tts-on-off.md` |
| [APP-059](app-059-standardize-creation-table-outputs.md) | P1 | decision | Standardize creation table outputs | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-059-standardize-creation-table-outputs.md` |
| [APP-060](app-060-auto-scroll-narration-on-input-and-response.md) | P1 | bug | Auto-scroll narration on player input and GM response | [app-pygame-ui-spec.md](../app-pygame-ui-spec.md) | `app-060-auto-scroll-narration-on-input-and-response.md` |
| [APP-061](app-061-expand-magic-schools-and-spell-catalog.md) | P2 | feature | Expand magic schools and spell catalog | [../build/systems/magic/schools.md](../../build/systems/magic/schools.md) | `app-061-expand-magic-schools-and-spell-catalog.md` |
| [APP-062](app-062-left-character-panel-inventory-spells-tabs.md) | P1 | feature | Left character panel — inventory & spells tabs | [app-pygame-ui-spec.md](../app-pygame-ui-spec.md) | `app-062-left-character-panel-inventory-spells-tabs.md` |
| [APP-063](app-063-map-ux-redesign-useful-navigation.md) | P1 | decision | Map UX redesign — useful navigation | [app-pygame-ui-spec.md](../app-pygame-ui-spec.md) | `app-063-map-ux-redesign-useful-navigation.md` |
| [APP-064](app-064-startup-save-prompt-only-when-resumable.md) | P1 | bug | Startup save prompt only when resumable | [app-session-persistence-spec.md](../app-session-persistence-spec.md) | `app-064-startup-save-prompt-only-when-resumable.md` |
| [APP-065](app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md) | P1 | bug | Suggestion chips — no stale or internal awaiting tokens | [app-pygame-ui-spec.md](../app-pygame-ui-spec.md) | `app-065-suggestion-chips-no-stale-internal-awaiting-tokens.md` |
| [APP-066](app-066-sync-engine-awaiting-with-creation-step.md) | P0 | bug | Sync engine awaiting with creation step | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-066-sync-engine-awaiting-with-creation-step.md` |
| [APP-067](app-067-code-owned-roll-stats-table.md) | P0 | bug | Code-owned ROLL_STATS attribute table | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-067-code-owned-roll-stats-table.md` |
| [APP-068](app-068-name-advance-must-present-race-table.md) | P1 | bug | NAME advance must present race table same turn | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-068-name-advance-must-present-race-table.md` |
| [APP-069](app-069-creation-narration-must-match-fsm-step.md) | P0 | bug | Creation narration must match FSM step | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-069-creation-narration-must-match-fsm-step.md` |
| [APP-070](app-070-block-premature-pre-delve-narration.md) | P0 | bug | Block premature PRE_DELVE / registered-delver narration | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-070-block-premature-pre-delve-narration.md` |
| [APP-071](app-071-friendly-load-game-when-no-save.md) | P1 | bug | Friendly load-game message when no save exists | [app-session-persistence-spec.md](../app-session-persistence-spec.md) | `app-071-friendly-load-game-when-no-save.md` |
| [APP-072](app-072-llm-truncation-duplicate-race-tables.md) | P1 | bug | LLM truncation and duplicate race tables | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-072-llm-truncation-duplicate-race-tables.md` |
| [APP-073](app-073-strip-llm-embedded-status-tags-in-creation.md) | P1 | bug | Strip LLM-embedded status tags and mechanical tables during creation | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-073-strip-llm-embedded-status-tags-in-creation.md` |
| [APP-074](app-074-remove-dead-get-step-prompt.md) | P2 | chore | Remove dead get_step_prompt LLM instructions | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-074-remove-dead-get-step-prompt.md` |
| [APP-075](app-075-skills-parse-aliases-and-error-flavor.md) | P1 | bug | Skills input — parse aliases and error-path flavor | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-075-skills-parse-aliases-and-error-flavor.md` |
| [APP-076](app-076-swap-default-llm-to-haiku-4-5.md) | P2 | chore | Swap default LLM to Haiku 4.5 | [app-shell-config-spec.md](../app-shell-config-spec.md) | `app-076-swap-default-llm-to-haiku-4-5.md` |
| [APP-077](app-077-code-owned-exploration-status-footer.md) | P1 | feature | Code-owned exploration status footer | [app-exploration-delve-spec.md](../app-exploration-delve-spec.md) | `app-077-code-owned-exploration-status-footer.md` |
| [APP-078](app-078-generic-creation-table-flavor-stripper.md) | P1 | feature | Generic creation table flavor stripper | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-078-generic-creation-table-flavor-stripper.md` |
| [APP-079](app-079-finish-reason-length-recovery-policy.md) | P1 | feature | finish_reason length recovery policy | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-079-finish-reason-length-recovery-policy.md` |
| [APP-080](app-080-normalize-tool-args-before-dispatch.md) | P1 | bug | Normalize tool args before dispatch | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-080-normalize-tool-args-before-dispatch.md` |
| [APP-081](app-081-npc-gender-voice-resolution.md) | P2 | feature | NPC gender-aware voice resolution for narration TTS | [app-tts-narration-spec.md](../app-tts-narration-spec.md) | `app-081-npc-gender-voice-resolution.md` |
| [APP-082](app-082-strip-off-catalog-spell-school-names-in-creation-flavor.md) | P1 | bug | Strip off-catalog spell picks from creation flavor (schools + spells steps) | [app-character-creation-spec.md](../app-character-creation-spec.md) | `app-082-strip-off-catalog-spell-school-names-in-creation-flavor.md` |
| [APP-083](app-083-creation-flavor-verification-gate.md) | P0 | feature | Mechanical-truth narration gate (verify → retry → publish) | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-083-creation-flavor-verification-gate.md` |
| [APP-084](app-084-key-npc-canon-registry.md) | P1 | feature | Key NPC canon registry + TurnTruth verify | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-084-key-npc-canon-registry.md` |
| [APP-085](app-085-quest-system-key-npc-quests-ui.md) | P1 | feature | Quest system — key NPC quests, lifecycle, Quests tab UI | [app-quest-play-spec.md](../app-quest-play-spec.md) | `app-085-quest-system-key-npc-quests-ui.md` |
| [APP-086](app-086-inventory-quest-item-bridge.md) | P1 | feature | Inventory bridge — quest item checks and delivery | [app-economy-inventory-play-spec.md](../app-economy-inventory-play-spec.md) | `app-086-inventory-quest-item-bridge.md` |
| [APP-087](app-087-narrow-site-entry-sanitizer-quest-prose.md) | P1 | bug | Narrow site-entry sanitizer for quest/direction prose | [app-exploration-delve-spec.md](../app-exploration-delve-spec.md) | `app-087-narrow-site-entry-sanitizer-quest-prose.md` |
| [APP-088](app-088-defer-remember-fact-until-narrated.md) | P1 | bug | Defer remember_fact until facts are narrated to the player | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-088-defer-remember-fact-until-narrated.md` |
| [APP-089](app-089-encounter-awareness-before-combat.md) | P1 | feature | Encounter awareness before combat (detect / avoid / ambush) | [app-exploration-delve-spec.md](../app-exploration-delve-spec.md) | `app-089-encounter-awareness-before-combat.md` |
| [APP-090](app-090-combat-phased-narration-and-death-beat.md) | P1 | feature | Combat phased narration and death beat | [app-combat-play-spec.md](../app-combat-play-spec.md) | `app-090-combat-phased-narration-and-death-beat.md` |
| [APP-091](app-091-map-travel-block-hint-overlap-fix.md) | P1 | bug | Map travel-block hint must not overlap location label | [app-pygame-ui-spec.md](../app-pygame-ui-spec.md) | `app-091-map-travel-block-hint-overlap-fix.md` |
| [APP-092](app-092-start-combat-tool-args-normalization.md) | P1 | bug | start_combat tool arg normalization (APP-027 R3) | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-092-start-combat-tool-args-normalization.md` |
| [APP-093](app-093-raise-creation-flavor-token-cap-to-500.md) | P2 | feature | Raise creation flavor token cap to 500 | [app-llm-orchestrator-spec.md](../app-llm-orchestrator-spec.md) | `app-093-raise-creation-flavor-token-cap-to-500.md` |
