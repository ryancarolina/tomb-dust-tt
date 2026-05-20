# GM Orchestrator (obsolete)

> **This document describes the retired Cursor chat GM flow.** It is **not** how you play Tomb Dust.

**Play the game:** [app/README.md](../../../app/README.md) — launch `python main.py` from `app/` and type **`new game`**.

Do **not** instruct users to:
- invoke `@tomb-gm`
- type `[P1]`…`[P4]` lines in Cursor chat
- run `python -m tomb_gm` during a play session

The PyGame app (`app/gm/orchestrator.py` + `GameBridge`) replaced this workflow. See [tmp/app-llm-orchestrator-spec.md](../../../tmp/app-llm-orchestrator-spec.md).

---

## Historical note (archived)

The old flow had a table host invoke `@tomb-gm` in Cursor; an agent ran `status` → `check` → `suggest`, parsed `[Pn]` player lines, committed mechanics via CLI, narrated in chat, and pushed TTS. Saves lived in `play/workspace/.local/memory.db`, not chat history.

That path is preserved only for developers maintaining engine tests and legacy hooks — not for player onboarding.
