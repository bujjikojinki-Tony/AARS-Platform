from __future__ import annotations

from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market import adapters
from aars_market.api import make_handler
from aars_market.models import Candle, FundingRate
from aars_market.service import DashboardRequest, DashboardService
from aars_market.simulation import ReplayEngine, StrategyAction
from aars_market.storage import MarketStore


def _candles(symbol: str = "SOLUSDT", n: int = 181) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [
        Candle(symbol, "1h", start + timedelta(hours=i), 100.0, 101.0, 99.0, 100.0, 1000.0 + i)
        for i in range(n)
    ]


def test_public_funding_adapter_paginates_by_timestamp(monkeypatch):
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    first = [
        {"symbol": "SOLUSDT", "fundingRate": "0.0001", "fundingTime": int((start + timedelta(hours=i)).timestamp() * 1000), "markPrice": "100", "rateType": "Regular"}
        for i in range(1000)
    ]
    second = [{"symbol": "SOLUSDT", "fundingRate": "-0.0002", "fundingTime": int((start + timedelta(hours=1000)).timestamp() * 1000), "markPrice": "101"}]
    calls: list[dict[str, object]] = []

    def fake_request(params: dict[str, object], _timeout: float):
        calls.append(params)
        return first if len(calls) == 1 else second

    monkeypatch.setattr(adapters, "_request_funding", fake_request)
    rates = adapters.fetch_binance_funding_history("solusdt", start, max_pages=3)

    assert len(rates) == 1001
    assert rates[-1].funding_rate == -0.0002
    assert calls[1]["startTime"] == first[-1]["fundingTime"] + 1


def test_funding_store_and_stable_archive_are_idempotent(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    rate = FundingRate("SOLUSDT", datetime(2026, 1, 2, tzinfo=timezone.utc), 0.0001, 100.0)
    store.upsert_funding_rates([rate], "test")
    store.upsert_funding_rates([rate], "test")
    assert store.count_funding_rates("SOLUSDT") == 1
    assert store.load_funding_rates("SOLUSDT") == [rate]

    payload = {"schema_version": "test", "market": {"symbol": "SOLUSDT", "timeframe": "1h"}, "latest_stable_view": {"as_of": rate.funding_time.isoformat()}}
    first = store.archive_latest_stable_view(payload, replay_window="30d", created_at=rate.funding_time)
    second = store.archive_latest_stable_view(payload, replay_window="30d", created_at=rate.funding_time)
    assert first == second
    assert len(store.list_latest_stable_views()) == 1
    assert store.get_latest_stable_view(first) == payload

    newer_generation = {**payload, "generated_at": datetime(2026, 1, 3, tzinfo=timezone.utc).isoformat()}
    assert store.archive_latest_stable_view(newer_generation, replay_window="30d") == first


class _LongFundingStrategy:
    name = "LONG_FUNDING_TEST"
    max_leverage = 1.0
    uses_funding = True

    def reset(self) -> None:
        self.entered = False

    def actions_for_bar(self, index: int, candles: list[Candle]):
        if self.entered:
            return []
        self.entered = True
        return [StrategyAction(1.0, candles[index].close, "test entry")]


def test_timestamped_funding_has_no_lookahead():
    candles = _candles(n=62)
    event = FundingRate("SOLUSDT", candles[61].open_time, 0.01, 100.0)
    engine = ReplayEngine(fee_rate=0.0, slippage_rate=0.0, funding_rates=[event])

    before = engine.run(candles[:61], _LongFundingStrategy(), warmup_bars=60)
    after = engine.run(candles, _LongFundingStrategy(), warmup_bars=60)

    assert before.funding == 0.0
    assert after.funding == pytest.approx(10.0)
    assert after.final_equity == pytest.approx(990.0)


def test_dashboard_service_selects_market_window_and_archives(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    candles = _candles("BTCUSDT")
    store.upsert_candles(candles, "test")
    now = candles[-1].open_time + timedelta(hours=1)
    store.upsert_funding_rates([FundingRate("BTCUSDT", candles[-8].open_time, 0.0001, 100.0)], "test")
    service = DashboardService(store)

    payload = service.build(DashboardRequest("btcusdt", "1h", "30d"), now=now)

    assert payload["schema_version"] == "mil3.dashboard.v2"
    assert payload["selection"] == {"symbol": "BTCUSDT", "timeframe": "1h", "replay_window": "30d"}
    assert payload["funding"]["events"] == 1
    assert payload["latest_stable_view_archive"]["immutable"] is True
    assert len(store.list_latest_stable_views("BTCUSDT", "1h")) == 1


def test_api_routes_are_read_only_without_binding_a_port(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    service = DashboardService(store)
    handler_type = make_handler(service, tmp_path)
    handler = object.__new__(handler_type)
    handler.path = "/api/v1/health"
    status, payload = handler._api_payload()
    assert status == HTTPStatus.OK
    assert payload == {"status": "ok", "execution_mode": "PAPER_ONLY", "read_only": True}

    captured: list[tuple[int, object]] = []
    handler._json = lambda status, payload, **_kwargs: captured.append((status, payload))
    handler.do_POST()
    assert captured == [(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "read-only API"})]


def test_dashboard_get_does_not_write_an_archive(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    store.upsert_candles(_candles(), "test")
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)
    handler.path = "/api/v1/dashboard?symbol=SOLUSDT&interval=1h&window=30d"

    status, payload = handler._api_payload()

    assert status == HTTPStatus.OK
    assert payload["latest_stable_view_archive"] is None
    assert store.list_latest_stable_views() == []
