from __future__ import annotations

from pathlib import Path


def test_pwb02_ui_modules_import() -> None:
    from weather_dashboard.lib.api import apiGet
    from weather_dashboard.lib.api import apiPost
    from weather_dashboard.ui.pwb02_pages import render_pwb02_evidence_raw_page
    from weather_dashboard.ui.pwb02_pages import render_pwb02_pipeline_page
    from weather_dashboard.ui.pwb02_pages import render_pwb02_workstation_page

    assert callable(apiGet)
    assert callable(apiPost)
    assert callable(render_pwb02_evidence_raw_page)
    assert callable(render_pwb02_workstation_page)
    assert callable(render_pwb02_pipeline_page)


def test_app_routes_pwb02_views_from_runtime_profile() -> None:
    source = Path("src/weather_dashboard/app.py").read_text(encoding="utf-8")

    assert '"pwb02"' in source
    assert "PWB-02 Weather Intelligence" in source
    assert "render_pwb02_evidence_raw_page()" in source
    assert "render_pwb02_workstation_page()" in source
    assert "render_pwb02_pipeline_page()" in source
