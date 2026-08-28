from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

from aars_market.api import make_handler
from aars_market.bot_orchestrator import BOT_ORDER, verify_shadow_bot_fleet
from aars_market.isolated_runtime import (
    IsolatedRuntimeSettings,
    acquire_isolated_runtime,
    run_isolated_runtime_cycle,
)
from aars_market.models import Candle
from aars_market.runtime_ledger import verify_runtime_paper_ledger
from aars_market.service import DashboardService
from aars_market.simulation import ReplayEngine, RiskStopPolicy, StrategyAction
from tests.test_mil323 import RUNTIME_AT, TOKEN, _ledger_ready_store


class _LeveragedOnce:
    name = "TEST_LEVERAGED_ONCE"
    max_leverage = 5.0
    uses_funding = False

    def __init__(self) -> None:
        self.entered = False

    def reset(self) -> None:
        self.entered = False

    def actions_for_bar(self, index, candles):
        if self.entered:
            return []
        self.entered = True
        return [StrategyAction(5.0, candles[index].close, "test leveraged entry", "entry")]


def _risk_candles(drop_close: float = 90.0) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    rows = []
    for index in range(63):
        close = 100.0 if index < 60 else drop_close
        rows.append(Candle(
            "BTCUSDT",
            "1h",
            start + timedelta(hours=index),
            100.0 if index == 60 else close,
            100.0 if index == 60 else close + 0.1,
            drop_close if index == 60 else close - 0.1,
            close,
            1000.0,
        ))
    return rows


def _run_fleet(store):
    acquired = acquire_isolated_runtime(
        store,
        "paper-sandbox",
        worker_id="mil324-fleet-worker",
        settings=IsolatedRuntimeSettings(
            lease_seconds=120, heartbeat_interval_seconds=30, max_cycles=1
        ),
        now=RUNTIME_AT + timedelta(minutes=4),
        token_factory=lambda: TOKEN,
    )
    return run_isolated_runtime_cycle(
        store,
        acquired["session_id"],
        TOKEN,
        lease_seconds=120,
        now=RUNTIME_AT + timedelta(minutes=4, seconds=10),
    )["paper_cycle"]


def test_four_shadow_bots_share_snapshot_but_keep_independent_accounts(
    tmp_path: Path, monkeypatch
):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    paper = _run_fleet(store)
    ledger = paper["result"]
    fleet = ledger["bot_fleet"]
    assert ledger["schema_version"] == "mil3.isolated-paper-ledger-result.v2"
    assert verify_runtime_paper_ledger(ledger) is True
    assert verify_shadow_bot_fleet(fleet) is True
    assert tuple(item["bot_id"] for item in fleet["bots"]) == BOT_ORDER
    assert fleet["snapshot_sha256"] == ledger["snapshot_sha256"]
    assert len({item["account_id"] for item in fleet["bots"]}) == 4
    assert all(item["aggregate"]["initial_equity"] == 2000.0 for item in fleet["bots"])
    assert all(len(item["per_asset"]) == 2 for item in fleet["bots"])
    assert all(
        asset["account"]["fill_evidence"]["simulated_fill_count"] > 0
        for bot in fleet["bots"]
        for asset in bot["per_asset"]
    )
    futures = fleet["bots"][2]
    assert futures["configuration"]["exchange_leverage_parameter"] == 10.0
    assert fleet["authority"]["simulated_order_intents_only"] is True
    assert fleet["authority"]["external_order_requests_created"] is False
    assert fleet["authority"]["order_path_present"] is False
    assert fleet["authority"]["live_execution_allowed"] is False


def test_bot_fleet_identity_is_deterministic_and_tamper_evident(
    tmp_path: Path, monkeypatch
):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    first = _run_fleet(store)
    fleet_id = first["result"]["bot_fleet"]["fleet_id"]
    session = store.list_isolated_paper_runtime_sessions("paper-sandbox", limit=1)[0]
    duplicate = run_isolated_runtime_cycle(
        store,
        session["session_id"],
        TOKEN,
        lease_seconds=120,
        now=RUNTIME_AT + timedelta(minutes=4, seconds=20),
    )["paper_cycle"]
    assert duplicate["status"] == "REUSED_COMMITTED"
    assert duplicate["result"]["bot_fleet"]["fleet_id"] == fleet_id
    assert duplicate["duplicate_application_prevented"] is True

    tampered = copy.deepcopy(first["result"])
    tampered["bot_fleet"]["bots"][2]["aggregate"]["fees"] = 0.0
    assert verify_shadow_bot_fleet(tampered["bot_fleet"]) is False
    assert verify_runtime_paper_ledger(tampered) is False


def test_runtime_risk_stop_flattens_and_freezes_only_the_virtual_account():
    result = ReplayEngine(
        initial_equity=1000.0,
        fee_rate=0.0,
        slippage_rate=0.0,
    ).run_detailed(
        _risk_candles(),
        _LeveragedOnce(),
        warmup_bars=60,
        risk_stop_policy=RiskStopPolicy(
            max_drawdown=0.20,
            max_liquidation_risk=1.0,
        ),
    )
    assert result.risk_state == "FROZEN"
    assert result.risk_stop_reasons == ("MAX_DRAWDOWN_LIMIT_EXCEEDED",)
    assert result.risk_stopped_at is not None
    assert result.trace[-1].position_qty == 0.0
    assert [fill.category for fill in result.fills] == ["entry", "risk_stop"]


def test_insolvent_paper_account_freezes_without_inventing_a_flatten_fill():
    result = ReplayEngine(
        initial_equity=1000.0,
        fee_rate=0.0,
        slippage_rate=0.0,
    ).run_detailed(
        _risk_candles(75.0),
        _LeveragedOnce(),
        warmup_bars=60,
        risk_stop_policy=RiskStopPolicy(
            max_drawdown=0.20,
            max_liquidation_risk=0.10,
        ),
    )
    assert result.risk_state == "FROZEN"
    assert "LIQUIDATION_APPROXIMATION_BREACH" in result.risk_stop_reasons
    assert result.trace[-1].equity <= 0
    assert [fill.category for fill in result.fills] == ["entry"]


def test_bot_fleet_is_exposed_by_read_only_ledger_api(tmp_path: Path, monkeypatch):
    store, *_ = _ledger_ready_store(tmp_path, monkeypatch)
    paper = _run_fleet(store)
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)
    handler.path = f"/api/v1/isolated-paper-ledger-results/{paper['result_id']}"
    status, envelope = handler._api_payload()
    assert status == HTTPStatus.OK
    assert len(envelope["result"]["bot_fleet"]["bots"]) == 4
    assert envelope["read_only"] is True
    assert envelope["order_path_present"] is False
    assert envelope["live_execution_allowed"] is False


def test_mil324_ui_exposes_four_bot_accounts_without_browser_controls():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    css = (ui_root / "styles.css").read_text(encoding="utf-8")
    assert "AARS // 03.25" in html
    assert 'id="runtime-bot-fleet"' in html
    assert "FOUR ISOLATED SHADOW BOTS" in html
    assert 'const expectedBots = ["BUY_HOLD", "SPOT_GRID", "FUTURES_LONG_GRID", "AARS_DYNAMIC"]' in javascript
    assert "simulated_fill_count" in javascript
    assert "Independent virtual account remains inside approved risk limits." in javascript
    assert ".runtime-bot-fleet" in css
    assert 'type="button">START BOT<' not in html
    assert 'type="button">STOP BOT<' not in html
