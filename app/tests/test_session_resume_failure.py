"""Resume failure recovery narration (APP-071)."""

# Module-level only — lazy-import Orchestrator inside tests (APP-049)


def test_load_game_no_save_variant_a(orchestrator, monkeypatch):
    narration_calls: list[str] = []
    monkeypatch.setattr(
        "gm.orchestrator.log_gm_narration",
        lambda text: narration_calls.append(text),
    )

    result = orchestrator.process_turn("load game")

    assert "no saved" in result.lower()
    assert "new game" in result.lower()
    assert "[Awaiting: new game]" in result
    assert "no save session found" not in result.lower()
    assert len(narration_calls) == 1
    assert narration_calls[0] == result


def test_load_game_mid_creation_variant_b_no_drift(orchestrator, monkeypatch):
    narration_calls: list[str] = []
    drift_events: list[dict] = []
    monkeypatch.setattr(
        "gm.orchestrator.log_gm_narration",
        lambda text: narration_calls.append(text),
    )
    monkeypatch.setattr(
        "gm.orchestrator.log_creation_drift",
        lambda data: drift_events.append(data),
    )

    orchestrator.process_turn("new game")
    orchestrator.process_turn("Dumpy")
    assert orchestrator.creation.active is True
    assert orchestrator.creation.step == "RACE"

    result = orchestrator.process_turn("load game")

    assert "no save session found" not in result.lower()
    assert "finished save" in result.lower() or "unsaved" in result.lower()
    assert "race" in result.lower()
    assert "[Awaiting: RACE_INPUT]" in result
    assert "new game" in result.lower()
    assert narration_calls[-1] == result
    mismatch = [
        e for e in drift_events if "awaiting_mismatch" in (e.get("reasons") or [])
    ]
    assert mismatch == []


def test_load_game_failure_retains_log_error(orchestrator, monkeypatch):
    error_calls: list[tuple[str, str]] = []
    monkeypatch.setattr(
        "gm.orchestrator.log_error",
        lambda context, error: error_calls.append((context, error)),
    )

    orchestrator.process_turn("load game")

    assert error_calls == [("session_resume", "no save session found")]
