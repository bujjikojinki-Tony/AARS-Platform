from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

from aars_market.api import make_handler
from aars_market.diagnostics import build_strategy_diagnostics
from aars_market.models import Candle
from aars_market.service import DashboardService
from aars_market.simulation import AarsDynamicStrategy, ReplayEngine
from aars_market.storage import MarketStore


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _candles(symbol: str, bars: int = 181) -> list[Candle]:
    rows = []
    price = 100.0
    for index in range(bars):
        drift = (0.45 if (index // 24) % 2 == 0 else -0.30) + ((index % 7) - 3) * 0.03
        close = max(20.0, price + drift)
        rows.append(
            Candle(
                symbol,
                "1h",
                START + timedelta(hours=index),
                price,
                max(price, close) + 0.4,
                min(price, close) - 0.4,
                close,
                1000.0 + index * 3,
            )
        )
        price = close
    return rows


def _ready_store(tmp_path: Path) -> tuple[MarketStore, str, dict]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    candles = _candles("BTCUSDT")
    store.upsert_candles(candles, "mil327-test")
    result = ReplayEngine().run_detailed(
        candles, AarsDynamicStrategy(), warmup_bars=120
    )
    as_of = candles[-1].open_time
    observed_at = as_of + timedelta(hours=1, minutes=1)
    payload = {
        "schema_version": "mil3.shadow-daily.v2",
        "execution_mode": "PAPER_ONLY",
        "generated_at": observed_at.isoformat(),
        "as_of": as_of.isoformat(),
        "observation_date": as_of.date().isoformat(),
        "evidence_boundary": {
            "observed_at": observed_at.isoformat(),
            "synchronized_closed_open_time": as_of.isoformat(),
            "per_asset_closed_open_time": {"BTCUSDT": as_of.isoformat()},
            "timeframe_duration_seconds": 3600.0,
            "fully_closed": True,
        },
        "symbols": ["BTCUSDT"],
        "evidence_as_of": {"BTCUSDT": as_of.isoformat()},
        "configuration": {
            "validation_strategy": "AARS_DYNAMIC",
            "portfolio_strategy": "AARS_DYNAMIC",
            "timeframe": "1h",
            "replay_window": "all",
            "warmup_bars": 120,
            "train_bars": 120,
            "test_bars": 24,
            "step_bars": 24,
            "candidate_ids": ["baseline"],
            "portfolio_parameter_policy": "fixed_existing_strategy_defaults",
        },
        "validation": {"markets": []},
        "portfolio": {
            "capital_model": "independent equal-weight capital buckets; no exchange margin netting",
            "weights": {"BTCUSDT": 1.0},
            "summary": {"degraded": False},
            "assets": [
                {
                    "symbol": "BTCUSDT",
                    "total_return": result.summary.total_return,
                }
            ],
            "trace": [
                {
                    "as_of": point.as_of,
                    "equity_index": point.equity / result.summary.initial_equity,
                    "net_exposure": point.net_exposure,
                }
                for point in result.trace
            ],
        },
        "review_gate": {
            "disposition": "DEFER",
            "live_execution_allowed": False,
        },
    }
    snapshot_id = store.archive_shadow_daily_snapshot(payload, created_at=observed_at)
    return store, snapshot_id, payload


def test_diagnostics_reconcile_costs_directions_and_stable_source(tmp_path: Path):
    store, snapshot_id, _ = _ready_store(tmp_path)

    payload = build_strategy_diagnostics(store)

    assert payload["schema_version"] == "mil3.strategy-diagnostics.v1"
    assert payload["execution_mode"] == "PAPER_ONLY"
    assert payload["status"] == "READY"
    assert payload["data_trust"]["status"] == "VERIFIED"
    assert payload["data_trust"]["source_snapshot_id"] == snapshot_id
    assert payload["authority"] == {
        "automatic_strategy_change_allowed": False,
        "paper_configuration_activation_allowed": False,
        "live_execution_allowed": False,
    }
    asset = payload["assets"][0]
    assert asset["source_verification"]["absolute_error"] == 0.0
    assert abs(
        sum(row["equity_change"] for row in asset["direction_attribution"])
        - (
            asset["performance"]["aars_total_return"] * 1000.0
        )
    ) < 1e-8
    assert abs(
        asset["costs"]["total_modeled_cost"]
        - asset["costs"]["fees"]
        - asset["costs"]["slippage"]
        - asset["costs"]["funding"]
    ) < 1e-10
    assert asset["costs"]["counterfactual_kind"] == (
        "ACCOUNTING_ADD_BACK_NOT_EXECUTION_FORECAST"
    )
    assert any(item["kind"] == "HYPOTHESIS" for item in payload["findings"])
    assert all(
        item["requires_challenger_test"]
        for item in payload["findings"]
        if item["kind"] == "HYPOTHESIS"
    )
    json.dumps(payload, allow_nan=False)


def test_diagnostics_fail_closed_on_ineligible_or_replay_mismatch(tmp_path: Path):
    empty = MarketStore(tmp_path / "empty.sqlite")
    empty.init_db()
    assert build_strategy_diagnostics(empty)["data_trust"]["reason"] == (
        "NO_ELIGIBLE_V2_STABLE_SNAPSHOT"
    )
    assert build_strategy_diagnostics(
        empty, snapshot_id="missing"
    )["data_trust"]["reason"] == "SNAPSHOT_NOT_FOUND"

    store, snapshot_id, _ = _ready_store(tmp_path / "mismatch")
    with store.connect() as conn:
        row = conn.execute(
            "SELECT payload_json FROM shadow_daily_snapshots WHERE snapshot_id=?",
            (snapshot_id,),
        ).fetchone()
        tampered = json.loads(row["payload_json"])
        tampered["portfolio"]["assets"][0]["total_return"] += 0.01
        conn.execute(
            "UPDATE shadow_daily_snapshots SET payload_json=? WHERE snapshot_id=?",
            (json.dumps(tampered, sort_keys=True), snapshot_id),
        )

    degraded = build_strategy_diagnostics(store, snapshot_id=snapshot_id)
    assert degraded["status"] == "DEGRADED"
    assert "ARCHIVED_RETURN_MISMATCH" in degraded["data_trust"]["reason"]
    assert degraded["attribution"] is None
    assert degraded["authority"]["live_execution_allowed"] is False


def test_strategy_diagnostics_api_is_get_only_and_ui_is_task_centered(tmp_path: Path):
    store, snapshot_id, _ = _ready_store(tmp_path)
    service = DashboardService(store)
    handler_type = make_handler(service, Path(__file__).parents[1] / "ui")
    handler = object.__new__(handler_type)
    handler.path = f"/api/v1/strategy-diagnostics?snapshot_id={snapshot_id}"

    status, payload = handler._api_payload()

    assert status == HTTPStatus.OK
    assert payload["read_only"] is True
    assert payload["authority"]["automatic_strategy_change_allowed"] is False

    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert 'id="diagnostic-status"' in html
    assert 'id="diagnostic-highest-drag"' in html
    assert 'id="diagnostic-assets"' in html
    assert 'id="diagnostic-findings"' in html
    assert "ACCOUNTING ADD-BACK · NOT A FORECAST" in html
    assert "/api/v1/strategy-diagnostics" in javascript
    assert "automatic_strategy_change_allowed !== false" in javascript
    assert ".diagnostic-workspace" in css
