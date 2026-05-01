from __future__ import annotations

from pathlib import Path

from weather_dashboard.ui import pwb01_runtime


def test_pwb01_runtime_scan_and_simulate(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(pwb01_runtime, "PWB01_DB_PATH", tmp_path / "pwb01_dashboard.sqlite")
    pwb01_runtime.get_pwb01_runtime.cache_clear()

    runtime = pwb01_runtime.get_pwb01_runtime()

    assert runtime.settings_routes.get_mode()["mode"] == "OBSERVE_ONLY"
    scan_response = runtime.opportunity_routes.post_scan()
    assert scan_response["ok"] is True
    assert scan_response["candidate_count"] >= 1

    candidate_id = scan_response["candidates"][0]["candidate_id"]
    simulate_response = runtime.command_routes.post_command(f"/simulate {candidate_id}")
    assert simulate_response["ok"] is True
    assert simulate_response["simulation"]["result_status"] == "COMPLETED"


def test_app_routes_pwb01_views_from_runtime_profile() -> None:
    source = Path("src/weather_dashboard/app.py").read_text(encoding="utf-8")

    assert 'runtime_profile == "pwb01"' in source
    assert "render_pwb01_opportunity_board_page()" in source
    assert "render_pwb01_command_page()" in source
    assert "render_pwb01_history_page()" in source
    assert 'render_pwb01_settings_page(section=view_id)' in source


def test_app_persists_runtime_profile_selection() -> None:
    source = Path("src/weather_dashboard/app.py").read_text(encoding="utf-8")

    assert "OUTPUT_DIR" in source
    assert 'RUNTIME_PROFILE_JSON = OUTPUT_DIR / "runtime_profile.json"' in source
    assert 'st.session_state.setdefault("dashboard_runtime_profile", persisted_runtime_profile)' in source
    assert "def _on_runtime_profile_change() -> None:" in source
    assert "on_change=_on_runtime_profile_change" in source
