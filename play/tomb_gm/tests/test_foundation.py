from __future__ import annotations


def test_init_status_check_suggest(run_tomb_gm, clear_active_session):
    clear_active_session()
    out = run_tomb_gm("init")
    assert out["ok"] is True
    assert out["schema_version"] >= 1
    st = run_tomb_gm("status")
    assert st["ok"] is True
    assert st["awaiting"] == "SETUP"
    chk = run_tomb_gm("check", expect_ok=False)
    assert "blocked" in chk
    sug = run_tomb_gm("suggest")
    assert sug["ok"] is True
