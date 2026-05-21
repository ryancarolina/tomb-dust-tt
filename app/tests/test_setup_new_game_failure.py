"""setup_new_game failure recovery (APP-019): T-019a–f.

Run with: pytest -k "setup_new_game_failure or setup_new_game"
"""

# Module-level only — lazy-import Orchestrator inside tests (APP-049)


def _patch_logging(monkeypatch):
    narration_calls: list[str] = []
    error_calls: list[tuple[str, str]] = []
    drift_events: list[dict] = []

    monkeypatch.setattr(
        "gm.orchestrator.log_gm_narration",
        lambda text: narration_calls.append(text),
    )
    monkeypatch.setattr(
        "gm.orchestrator.log_error",
        lambda context, error: error_calls.append((context, error)),
    )
    monkeypatch.setattr(
        "gm.orchestrator.log_creation_drift",
        lambda data: drift_events.append(data),
    )
    return narration_calls, error_calls, drift_events


def _simulate_combat_death_emit(orchestrator, death_result):
    """Mirror combat caller branch (~1764): skip _emit_narration when already emitted."""
    narration_calls: list[str] = []
    original_emit = orchestrator._emit_narration

    def _capture_emit(message: str) -> None:
        narration_calls.append(message)
        original_emit(message)

    orchestrator._emit_narration = _capture_emit  # type: ignore[method-assign]

    if death_result is not None:
        if not death_result.already_emitted:
            orchestrator._emit_narration(death_result.message)
        orchestrator.history.append(
            {"role": "assistant", "content": death_result.message}
        )

    return narration_calls


def test_t019a_command_failure_mapped_cause(orchestrator, monkeypatch):
    """T-019a: explicit new game failure shows R2 copy + mapped cause + dual JSONL."""
    narration_calls, error_calls, _ = _patch_logging(monkeypatch)
    monkeypatch.setattr(
        orchestrator,
        "setup_new_game",
        lambda *args, **kwargs: {
            "ok": False,
            "error": "campaign not found: salt-road",
        },
    )

    result = orchestrator.process_turn("new game")

    assert result.startswith("Could not start a fresh session.")
    assert "The save campaign could not be found in the workspace database." in result
    assert "[Awaiting: new game]" in result
    assert "Could not start game:" not in result
    assert "campaign not found: salt-road" not in result
    assert len(narration_calls) == 1
    assert narration_calls[0] == result
    assert error_calls == [("setup_new_game", "campaign not found: salt-road")]


def test_t019b_command_failure_default_map(orchestrator, monkeypatch):
    """T-019b: unknown engine error maps to default cause line."""
    narration_calls, error_calls, _ = _patch_logging(monkeypatch)
    monkeypatch.setattr(
        orchestrator,
        "setup_new_game",
        lambda *args, **kwargs: {"ok": False, "error": "something weird"},
    )

    result = orchestrator.process_turn("new game")

    first_line = result.splitlines()[0]
    assert first_line == "Could not start a fresh session."
    assert "Something went wrong while resetting the workspace for a new run." in result
    assert "something weird" not in result
    assert "Could not start game:" not in result
    assert len(narration_calls) == 1
    assert error_calls == [("setup_new_game", "something weird")]


def test_t019c_death_failure_caller_contract(orchestrator, monkeypatch):
    """T-019c: death restart failure emits once inside handler; caller skips _emit_narration."""
    narration_calls, error_calls, _ = _patch_logging(monkeypatch)
    mechanical = [{"death_results": [{"ok": True, "dead_character_id": "char-1"}]}]
    monkeypatch.setattr(
        orchestrator.bridge,
        "extract_death_from_mechanical",
        lambda _mech: {"character_id": "char-1"},
    )
    monkeypatch.setattr(
        orchestrator.bridge,
        "process_delver_death",
        lambda _char_id: {
            "ok": True,
            "corpse": {
                "display_name": "Rick",
                "site_address": "23-A-UG-1",
                "room_id": "entry",
            },
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "setup_new_game",
        lambda *args, **kwargs: {"ok": False, "error": "database is locked"},
    )

    death_result = orchestrator._handle_player_death(mechanical)

    assert death_result is not None
    assert death_result.already_emitted is True
    assert "**Rick** is dead." in death_result.message
    assert "23-A-UG-1 / entry" in death_result.message
    assert "registry could not open a fresh desk session" in death_result.message
    assert "new game has started" not in death_result.message.lower()
    assert "What is your name?" not in death_result.message
    assert "[Awaiting: new game]" in death_result.message
    assert len(narration_calls) == 1
    assert narration_calls[0] == death_result.message
    assert error_calls == [("setup_new_game", "database is locked")]

    caller_narration = _simulate_combat_death_emit(orchestrator, death_result)
    assert caller_narration == []


def test_t019d_run_ended_failure(orchestrator, monkeypatch):
    """T-019d: run_ended resume + setup failure shows R4 copy without NAME desk."""
    narration_calls, error_calls, _ = _patch_logging(monkeypatch)
    monkeypatch.setattr(
        orchestrator.bridge,
        "session_resume",
        lambda: {
            "ok": True,
            "run_ended": True,
            "campaign_slug": "salt-road",
            "corpses": [
                {
                    "site_address": "47-B-UG-3",
                    "room_id": "vault",
                }
            ],
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "setup_new_game",
        lambda *args, **kwargs: {"ok": False, "error": "permission denied"},
    )

    result = orchestrator.process_turn("load game")

    assert "Your previous delver did not survive" in result
    assert "47-B-UG-3 / vault" in result
    assert "registry could not open a fresh desk session" in result
    assert "new game has started" not in result.lower()
    assert "What is your delver's name?" not in result
    assert "[Awaiting: new game]" in result
    assert len(narration_calls) == 1
    assert narration_calls[0] == result
    assert error_calls == [("setup_new_game", "permission denied")]
    assert orchestrator.creation.step != "NAME" or not orchestrator.creation.active


def test_t019e_drift_silence_on_setup_failure(orchestrator, monkeypatch):
    """T-019e: recovery footers do not emit creation_drift awaiting_mismatch."""
    _, _, drift_events = _patch_logging(monkeypatch)

    monkeypatch.setattr(
        orchestrator,
        "setup_new_game",
        lambda *args, **kwargs: {
            "ok": False,
            "error": "campaign not found: salt-road",
        },
    )
    orchestrator.process_turn("new game")

    mechanical = [{"death_results": [{"ok": True, "dead_character_id": "char-2"}]}]
    monkeypatch.setattr(
        orchestrator.bridge,
        "extract_death_from_mechanical",
        lambda _mech: {"character_id": "char-2"},
    )
    monkeypatch.setattr(
        orchestrator.bridge,
        "process_delver_death",
        lambda _char_id: {
            "ok": True,
            "corpse": {"display_name": "Dumpy", "site_address": "23-A"},
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "setup_new_game",
        lambda *args, **kwargs: {"ok": False, "error": "something weird"},
    )
    orchestrator._handle_player_death(mechanical)

    mismatch = [
        e for e in drift_events if "awaiting_mismatch" in (e.get("reasons") or [])
    ]
    assert mismatch == []


def test_t019f_success_regression_reaches_name(orchestrator):
    """T-019f: happy-path new game still opens NAME desk (T-014a regression)."""
    result = orchestrator.process_turn("new game")

    assert orchestrator.creation.active is True
    assert orchestrator.creation.step == "NAME"
    assert "name" in result.lower() or "registry" in result.lower()
