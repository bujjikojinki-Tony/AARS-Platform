from __future__ import annotations

import json

from weather_telegram_console.integrations.signal_api import SignalAPI
from weather_telegram_console.settings import get_signal_json_path


def test_signal_api_load_latest_signal(monkeypatch, tmp_path) -> None:
    signal_path = tmp_path / "sample_signal_event.json"
    signal_path.write_text(
        json.dumps(
            {
                "signal_id": "sig_1",
                "market_id": "sample_market_001",
                "location_name": "Central Park",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SIGNAL_JSON_PATH", str(signal_path))

    payload = SignalAPI().load_latest_signal()

    assert payload["signal_id"] == "sig_1"
    assert payload["market_id"] == "sample_market_001"


def test_signal_path_prefers_dashboard_approval_signal(monkeypatch, tmp_path) -> None:
    dashboard_signal = tmp_path / "dashboard_approval_signal.json"
    dashboard_signal.write_text(
        json.dumps(
            {
                "signal_id": "dashboard_m1_123",
                "intent_id": "intent_dashboard_123",
                "market_id": "m1",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.delenv("SIGNAL_JSON_PATH", raising=False)
    monkeypatch.setenv("DASHBOARD_APPROVAL_SIGNAL_JSON_PATH", str(dashboard_signal))

    assert get_signal_json_path() == dashboard_signal
    payload = SignalAPI().load_latest_signal()
    assert payload["intent_id"] == "intent_dashboard_123"
