from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from aars_market.dashboard import DASHBOARD_SCHEMA_VERSION, build_dashboard_payload, write_dashboard_payload
from aars_market.models import Candle
from aars_market.storage import MarketStore


def _candles(n: int = 180) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    candles: list[Candle] = []
    for index in range(n):
        trend = index * 0.035
        oscillation = 1.8 if index % 2 else -1.8
        close = 100.0 + trend + oscillation
        candles.append(
            Candle(
                symbol="SOLUSDT",
                timeframe="1h",
                open_time=start + timedelta(hours=index),
                open=100.0 + trend,
                high=close + 2.0,
                low=close - 2.0,
                close=close,
                volume=1000.0 + index,
            )
        )
    return candles


def test_dashboard_payload_contract_is_deterministic_and_paper_only():
    generated_at = datetime(2026, 8, 24, 8, 0, tzinfo=timezone.utc)
    payload = build_dashboard_payload(
        _candles(),
        warmup_bars=120,
        futures_leverage=10.0,
        data_fresh=False,
        generated_at=generated_at,
        max_trace_points=20,
    )

    assert payload["schema_version"] == DASHBOARD_SCHEMA_VERSION
    assert payload["execution_mode"] == "PAPER_ONLY"
    assert payload["generated_at"] == generated_at.isoformat()
    assert payload["market"]["freshness_status"] == "STALE"
    assert payload["market"]["degraded"] is True
    assert payload["review_gate"]["live_execution_allowed"] is False
    assert payload["latest_stable_view"]["status"] == "DEGRADED"
    assert [item["id"] for item in payload["strategies"]] == [
        "BUY_HOLD",
        "SPOT_GRID",
        "FUTURES_LONG_GRID_10X",
        "AARS_DYNAMIC",
    ]
    assert all(len(item["trace"]) <= 21 for item in payload["strategies"])
    assert any(alert["id"] == "DATA_FRESHNESS" for alert in payload["alerts"])


def test_dashboard_payload_writes_strict_json(tmp_path: Path):
    payload = build_dashboard_payload(
        _candles(),
        warmup_bars=120,
        data_fresh=True,
        generated_at=datetime(2026, 8, 24, tzinfo=timezone.utc),
    )
    target = write_dashboard_payload(tmp_path / "ui" / "dashboard_payload.json", payload)
    loaded = json.loads(target.read_text(encoding="utf-8"))

    assert loaded["schema_version"] == DASHBOARD_SCHEMA_VERSION
    assert loaded["market"]["freshness_status"] == "CURRENT"
    assert loaded["latest_stable_view"]["status"] == "STABLE"
    assert "NaN" not in target.read_text(encoding="utf-8")
    assert "Infinity" not in target.read_text(encoding="utf-8")


def test_static_console_exposes_hmi_safety_surfaces_without_order_control():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")

    assert (ui_root / "index.html").is_file()
    assert "PAPER_ONLY" in html
    assert "DEGRADED VIEW" in html
    assert "LATEST STABLE VIEW" in html
    assert "LIQUIDATION" in html
    assert 'id="market-select"' in html
    assert 'id="window-select"' in html
    assert 'id="archive-select"' in html
    assert "mil3.dashboard.v2" in javascript
    assert "Created By Deerflow" in html
    assert "mil3.dashboard.v1" in javascript
    assert "unsafe execution mode rejected" in javascript
    assert not re.search(r"<button[^>]*>\s*(place|submit|execute)\s+order", html, re.IGNORECASE)


def test_compare_cli_exports_dashboard_payload_from_same_replay(tmp_path: Path):
    mil3_root = Path(__file__).parents[1]
    database = tmp_path / "market.sqlite"
    output = tmp_path / "dashboard_payload.json"
    store = MarketStore(database)
    store.init_db()
    store.upsert_candles(_candles(), source="DETERMINISTIC_TEST")

    completed = subprocess.run(
        [
            sys.executable,
            str(mil3_root / "run_compare.py"),
            "--db",
            str(database),
            "--symbol",
            "SOLUSDT",
            "--warmup",
            "120",
            "--output-json",
            str(output),
        ],
        cwd=mil3_root,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert "execution_mode=PAPER_ONLY" in completed.stdout
    assert f"dashboard_payload={output}" in completed.stdout
    assert payload["execution_mode"] == "PAPER_ONLY"
    assert len(payload["strategies"]) == 4
