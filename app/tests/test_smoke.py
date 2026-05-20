"""Minimal smoke tests for app/tests scaffolding (APP-049)."""


def test_bridge_status_after_init(bridge):
    """Scaffolding validation: imports, isolated workspace, init(), and status() path."""
    status = bridge.status()
    assert isinstance(status, dict)
    assert "roster" in status
    assert isinstance(status["roster"], list)
