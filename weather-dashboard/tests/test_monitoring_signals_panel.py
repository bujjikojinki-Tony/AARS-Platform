from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from weather_dashboard.ui.monitoring_signals_panel import (
    _apply_signal_section,
    _build_distribution_figure,
    _build_trend_df,
    _build_trend_figure,
    _load_json_file,
    _load_latest_json,
    _load_recent_json,
    _load_recent_jsonl,
)


def test_monitoring_signals_file_loaders_handle_latest_and_recent(tmp_path: Path) -> None:
    json_dir = tmp_path / "json"
    jsonl_dir = tmp_path / "jsonl"
    json_dir.mkdir()
    jsonl_dir.mkdir()

    first = json_dir / "first.json"
    second = json_dir / "second.json"
    first.write_text('{"market_id":"1","severity":"amber"}', encoding="utf-8")
    second.write_text('{"market_id":"2","severity":"red"}', encoding="utf-8")
    (jsonl_dir / "events.jsonl").write_text(
        '{"market_id":"3","primary_reason":"edge_dislocation"}\n'
        '{"market_id":"4","primary_reason":"source_risk_change"}\n',
        encoding="utf-8",
    )

    assert _load_json_file(first)["market_id"] == "1"
    assert _load_latest_json(json_dir)["market_id"] in {"1", "2"}
    assert len(_load_recent_json(json_dir, limit=5)) == 2
    recent_jsonl = _load_recent_jsonl(jsonl_dir, limit=5)
    assert {row["market_id"] for row in recent_jsonl} == {"3", "4"}


def test_monitoring_signals_sections_filter_by_governed_type() -> None:
    rows = [
        {"type": "alert", "status": "active", "market_label": "NY"},
        {"type": "anomaly", "status": "active", "market_label": "Houston"},
        {"type": "system", "status": "active", "market_label": "Source Layer"},
        {"type": "info", "status": "resolved", "market_label": "Scanner"},
    ]

    assert [row["type"] for row in _apply_signal_section(rows, "Alert Queue")] == ["alert"]
    assert [row["type"] for row in _apply_signal_section(rows, "Anomaly Feed")] == ["anomaly"]
    assert [row["type"] for row in _apply_signal_section(rows, "System Signals")] == ["system", "info"]
    assert [row["type"] for row in _apply_signal_section(rows, "Active Signals")] == ["alert", "anomaly", "system"]
    assert _apply_signal_section(rows, "Signal History") == rows


def test_monitoring_signals_chart_builders_degrade_without_plotly() -> None:
    now = datetime.now(timezone.utc)
    rows = [
        {"ts_dt": now - timedelta(minutes=2), "type": "alert", "severity_label": "RED"},
        {"ts_dt": now - timedelta(minutes=1), "type": "anomaly", "severity_label": "AMBER"},
        {"ts_dt": now, "type": "system", "severity_label": "BLUE"},
    ]

    trend_df = _build_trend_df(rows)
    assert {"alerts", "anomalies", "ops"}.issubset(trend_df.columns)

    trend_figure = _build_trend_figure(trend_df)
    distribution_figure = _build_distribution_figure(rows)

    assert trend_figure is None or hasattr(trend_figure, "to_dict")
    assert distribution_figure is None or hasattr(distribution_figure, "to_dict")
