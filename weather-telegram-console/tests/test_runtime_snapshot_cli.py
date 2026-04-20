from __future__ import annotations

import json

from typer.testing import CliRunner

from weather_telegram_console.runtime_snapshot_cli import app


def test_export_status_runtime_snapshot(monkeypatch, tmp_path) -> None:
    unified_path = tmp_path / "unified_status.json"
    gate_stack_api_path = tmp_path / "gate_stack_api.json"
    out_path = tmp_path / "telegram_gate_runtime_snapshot.json"

    unified_path.write_text(
        json.dumps(
            {
                "schema_version": "unified_status.v1",
                "generated_at": "2026-04-19T10:00:00+00:00",
                "current_market": {"market_id": "m-1"},
                "gate_stack": {"resolver_gate": "pass", "block_reasons": []},
                "block_reasons": [],
            }
        ),
        encoding="utf-8",
    )
    gate_stack_api_path.write_text(
        json.dumps(
            {
                "schema_version": "gate_stack_api.v1",
                "source_schema_version": "unified_status.v1",
                "market_id": "m-1",
                "gate_stack": {"resolver_gate": "blocked", "block_reasons": ["resolver_not_matched"]},
                "block_reasons": ["resolver_not_matched"],
                "severity": "high",
                "recommended_operator_action": "review_resolver_contract",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("UNIFIED_STATUS_JSON_PATH", str(unified_path))
    monkeypatch.setenv("GATE_STACK_API_JSON_PATH", str(gate_stack_api_path))
    monkeypatch.setenv("TELEGRAM_GATE_RUNTIME_SNAPSHOT_JSON", str(out_path))

    result = CliRunner().invoke(app, [])
    assert result.exit_code == 0
    payload = json.loads(out_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "telegram_gate_runtime_snapshot.v1"
    assert payload["gate_source"] == "api"
    assert payload["source_schema_version"] == "unified_status.v1"
