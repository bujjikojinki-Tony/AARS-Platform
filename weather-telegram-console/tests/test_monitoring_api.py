from __future__ import annotations

from pathlib import Path

from weather_telegram_console.integrations.monitoring_api import MonitoringAPI


def test_monitoring_api_loads_trend(tmp_path: Path, monkeypatch) -> None:
    alert_dir = tmp_path / "market_alert_events"
    report_dir = tmp_path / "family_scan_reports"
    anomaly_dir = tmp_path / "market_anomaly_events"
    source_policy_path = tmp_path / "source_policy_status.json"
    gate_stack_api_path = tmp_path / "gate_stack_api.json"
    unified_status_path = tmp_path / "unified_status.json"
    scanner_status_path = tmp_path / "scanner_status.json"
    universe_path = tmp_path / "market_universe_snapshot.json"
    evidence_path = tmp_path / "evidence_scan_snapshot.json"
    queue_status_path = tmp_path / "alert_queue_status.json"
    alert_dir.mkdir()
    report_dir.mkdir()
    anomaly_dir.mkdir()

    (alert_dir / "a.json").write_text('{"market_id":"1","severity":"amber","primary_reason":"edge_dislocation"}', encoding="utf-8")
    (report_dir / "b.json").write_text('{"family_count":1,"market_count":1,"family_summaries":[{"market_family":"x","max_intervention_like_score":0.9}]}', encoding="utf-8")
    (anomaly_dir / "c.jsonl").write_text('{"market_id":"1","anomaly_score":0.4,"primary_reason":"edge_dislocation"}\n', encoding="utf-8")
    source_policy_path.write_text('{"schema_version":"source_policy_status.v1","overall_status":"healthy","counts":{"fresh":1,"stale":0,"unavailable":0},"priority_counts":{"high":1},"problem_sources":[]}', encoding="utf-8")
    gate_stack_api_path.write_text('{"schema_version":"gate_stack_api.v1","overall_status":"blocked","gate_status":"BLOCKED","can_execute":false,"primary_block_reason":"comparison_not_actionable","recommended_operator_action":"hold_execution_and_review","block_reasons":["comparison_not_actionable"]}', encoding="utf-8")
    unified_status_path.write_text('{"schema_version":"unified_status.v1","overall_status":"blocked","execution":{"status":"blocked","ready_for_live":false,"primary_block_reason":"comparison_not_actionable","recommended_operator_action":"hold_execution_and_review"},"gate_stack":{"execution_gate":"blocked","block_reasons":["comparison_not_actionable"]},"block_reasons":["comparison_not_actionable"]}', encoding="utf-8")
    scanner_status_path.write_text('{"schema_version":"scanner_status.v1","total_markets":2,"scanned_markets":1,"fresh_markets":1,"stale_markets":0,"unavailable_markets":0,"alert_markets":1,"backlog_count":1,"next_scan_eta":"5m"}', encoding="utf-8")
    universe_path.write_text('{"schema_version":"market_universe_snapshot.v1","market_count":2,"markets":[{"market_id":"1"},{"market_id":"2"}]}', encoding="utf-8")
    evidence_path.write_text('{"schema_version":"evidence_scan_snapshot.v1","market_count":1,"rows":[{"market_id":"1","freshness_status":"fresh"}]}', encoding="utf-8")
    queue_status_path.write_text('{"schema_version":"alert_queue_status.v1","accepted_count":1,"suppressed_count":0}', encoding="utf-8")

    monkeypatch.setattr("weather_telegram_console.integrations.monitoring_api.get_market_alert_events_dir", lambda: alert_dir)
    monkeypatch.setattr("weather_telegram_console.integrations.monitoring_api.get_family_scan_reports_dir", lambda: report_dir)
    monkeypatch.setattr("weather_telegram_console.integrations.monitoring_api.get_market_anomaly_events_dir", lambda: anomaly_dir)
    monkeypatch.setattr("weather_telegram_console.integrations.monitoring_api.get_source_policy_status_path", lambda: source_policy_path)
    monkeypatch.setattr("weather_telegram_console.integrations.monitoring_api.get_gate_stack_api_path", lambda: gate_stack_api_path)
    monkeypatch.setattr("weather_telegram_console.integrations.monitoring_api.get_unified_status_path", lambda: unified_status_path)
    monkeypatch.setattr("weather_telegram_console.integrations.monitoring_api.get_scanner_status_path", lambda: scanner_status_path)
    monkeypatch.setattr("weather_telegram_console.integrations.monitoring_api.get_market_universe_snapshot_path", lambda: universe_path)
    monkeypatch.setattr("weather_telegram_console.integrations.monitoring_api.get_evidence_scan_snapshot_path", lambda: evidence_path)
    monkeypatch.setattr("weather_telegram_console.integrations.monitoring_api.get_scan_queue_status_path", lambda: queue_status_path)

    payload = MonitoringAPI().load_latest_monitoring_signals()

    assert payload["alert_count"] == 1
    assert payload["trend"]["window"] == 5
    assert payload["trend"]["severity_counts"]["amber"] == 1
    assert payload["latest_source_policy_status"]["overall_status"] == "healthy"
    assert payload["latest_scanner_status"]["total_markets"] == 2
    assert payload["latest_market_universe_snapshot"]["market_count"] == 2
    assert payload["latest_evidence_scan_snapshot"]["market_count"] == 1
    assert payload["latest_scan_queue_status"]["accepted_count"] == 1
    assert payload["runtime_block"]["gate_status"] == "BLOCKED"
    assert payload["runtime_block"]["primary_block_reason"] == "comparison_not_actionable"
