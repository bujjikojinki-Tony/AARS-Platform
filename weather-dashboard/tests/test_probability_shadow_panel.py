from __future__ import annotations

from weather_dashboard.ui import probability_shadow_panel


def test_probability_shadow_panel_includes_promotion_fields(monkeypatch) -> None:
    captured_sections: list[tuple[str, list[tuple[str, object]]]] = []
    captured_metrics: list[tuple[str, object]] = []

    monkeypatch.setattr(probability_shadow_panel, "render_panel_title", lambda *args, **kwargs: None)
    monkeypatch.setattr(probability_shadow_panel, "render_compact_note", lambda *args, **kwargs: None)
    monkeypatch.setattr(probability_shadow_panel.st, "info", lambda *args, **kwargs: None)
    monkeypatch.setattr(probability_shadow_panel.st, "expander", lambda *args, **kwargs: _DummyCtx())

    def fake_render_kv_section(title, rows, metric_label=None, metric_value=None):
        captured_sections.append((title, list(rows)))
        if metric_label is not None:
            captured_metrics.append((metric_label, metric_value))

    monkeypatch.setattr(probability_shadow_panel, "render_kv_section", fake_render_kv_section)
    monkeypatch.setattr(probability_shadow_panel.st, "metric", lambda *args, **kwargs: None)

    probability_shadow_panel.render_probability_shadow_panel(
        {
            "market_id": "m1",
            "calibration_status": "not_calibrated",
            "probability_mode": "heuristic_not_calibrated",
            "execution_constraint": "manual_advisory_only",
            "approved_for_live": False,
            "deployment_mode": "shadow",
            "promotion_state": {
                "probability_mode": "heuristic_not_calibrated",
                "promotion_reason": "validation_report_stale",
                "demotion_reason": "validation_freshness_blocked",
            },
            "promotion_reason": "validation_report_stale",
            "demotion_reason": "validation_freshness_blocked",
            "fair_value": 0.61,
            "edge": 0.08,
        }
    )

    assert captured_sections
    title, rows = captured_sections[0]
    assert title == "Fair Value Shadow"
    assert ("Promotion State", "heuristic_not_calibrated") in rows
    assert ("Promotion Reason", "validation_report_stale") in rows
    assert ("Demotion Reason", "validation_freshness_blocked") in rows


class _DummyCtx:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False
