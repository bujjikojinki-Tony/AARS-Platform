from __future__ import annotations

from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from pathlib import Path

import pytest

from aars_market.coverage import analyze_funding_coverage
from aars_market.api import make_handler
from aars_market.dashboard import build_dashboard_payload
from aars_market.ingestion import IncrementalIngestor, run_scheduler
from aars_market.models import Candle, FundingRate
from aars_market.portfolio import build_portfolio_payload
from aars_market.service import DashboardService
from aars_market.stable_diff import compare_stable_views
from aars_market.storage import MarketStore


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _candle(symbol: str, hour: int, close: float = 100.0) -> Candle:
    return Candle(
        symbol=symbol,
        timeframe="1h",
        open_time=START + timedelta(hours=hour),
        open=close,
        high=close + 1,
        low=close - 1,
        close=close,
        volume=1000.0,
    )


def test_incremental_ingestion_overlaps_cursors_and_audits_partial_failure(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    store.upsert_candles([_candle("SOLUSDT", 10)], "seed")
    seed_rate = FundingRate("SOLUSDT", START + timedelta(hours=8), 0.0001, 100.0)
    store.upsert_funding_rates([seed_rate], "seed")
    starts: dict[str, datetime] = {}

    def candles(symbol: str, _interval: str, start: datetime, _end: datetime):
        starts["candles"] = start
        return [_candle(symbol, 10), _candle(symbol, 11)]

    def funding(_symbol: str, start: datetime, _end: datetime):
        starts["funding"] = start
        raise RuntimeError("deterministic outage")

    summary = IncrementalIngestor(
        store,
        symbols=["SOLUSDT"],
        candle_overlap=timedelta(hours=2),
        funding_overlap=timedelta(hours=8),
        candle_fetcher=candles,
        funding_fetcher=funding,
        funding_info_fetcher=lambda **_kwargs: [],
    ).run_cycle(now=START + timedelta(hours=12))

    assert starts == {"candles": START + timedelta(hours=8), "funding": START}
    assert summary["execution_mode"] == "PAPER_ONLY"
    assert summary["status"] == "PARTIAL"
    assert store.count_candles("SOLUSDT", "1h") == 2
    assert store.count_funding_rates("SOLUSDT") == 1
    cadence = store.load_funding_cadence_observations("SOLUSDT")
    assert cadence[0].interval_hours == 8
    assert cadence[0].source_status == "DEFAULT_ABSENT"
    assert store.list_ingestion_cycles()[0]["cycle_id"] == summary["cycle_id"]


def test_scheduler_is_bounded_and_observable():
    class StubIngestor:
        def __init__(self):
            self.calls = 0

        def run_cycle(self, *, now: datetime):
            self.calls += 1
            return {"cycle": self.calls, "now": now.isoformat()}

    ingestor = StubIngestor()
    sleeps: list[float] = []
    observed: list[dict[str, object]] = []
    result = run_scheduler(
        ingestor,  # type: ignore[arg-type]
        interval_seconds=30,
        max_cycles=2,
        clock=lambda: START,
        sleeper=sleeps.append,
        on_cycle=observed.append,
    )

    assert result == observed
    assert len(result) == 2
    assert sleeps == [30]


def test_funding_coverage_detects_cadence_gap_and_not_required_state():
    complete = [FundingRate("SOLUSDT", START + timedelta(hours=hour), 0.0001) for hour in (0, 8, 16, 24)]
    coverage = analyze_funding_coverage(complete, START, START + timedelta(hours=24))
    assert coverage.status == "COMPLETE"
    assert coverage.coverage_ratio == 1.0

    gapped = analyze_funding_coverage(
        [complete[0], complete[2], complete[3]], START, START + timedelta(hours=24)
    )
    assert gapped.status == "GAPPED"
    assert gapped.estimated_missing_events == 1
    assert gapped.largest_gap_hours == 16.0

    optional = analyze_funding_coverage([], START, START + timedelta(hours=24), required=False)
    assert optional.status == "NOT_REQUIRED"
    assert optional.coverage_ratio == 1.0


def test_missing_funding_adds_actionable_alert_and_defers_review():
    payload = build_dashboard_payload(
        [_candle("SOLUSDT", hour, 100.0 + hour * 0.01) for hour in range(181)],
        warmup_bars=120,
        data_fresh=True,
        generated_at=START + timedelta(hours=181),
    )
    alert = next(item for item in payload["alerts"] if item["id"] == "FUNDING_COVERAGE_GAP")
    assert alert["severity"] == "HIGH"
    assert "incremental funding ingestion" in alert["recommended_action"]
    assert payload["funding"]["coverage"]["status"] == "MISSING"
    assert payload["review_gate"]["disposition"] == "DEFER"


def _asset_payload(symbol: str, final_equity: float, exposure: float, risk: float):
    return {
        "market": {"symbol": symbol, "freshness_status": "CURRENT"},
        "funding": {"coverage": {"status": "COMPLETE"}},
        "strategies": [
            {
                "id": "AARS_DYNAMIC",
                "summary": {
                    "initial_equity": 1000.0,
                    "total_return": final_equity / 1000 - 1,
                    "final_net_exposure": exposure,
                    "max_effective_leverage": abs(exposure),
                    "max_liquidation_risk": risk,
                    "liquidation_events": 0,
                },
                "trace": [
                    {"as_of": "2026-01-01T00:00:00+00:00", "equity": 1000.0, "net_exposure": 0.0, "effective_leverage": 0.0, "margin_buffer_pct": 1.0, "liquidation_risk": 0.0},
                    {"as_of": "2026-01-02T00:00:00+00:00", "equity": final_equity, "net_exposure": exposure, "effective_leverage": abs(exposure), "margin_buffer_pct": 0.5, "liquidation_risk": risk},
                ],
            }
        ],
    }


def test_cross_asset_portfolio_aggregates_net_gross_and_risk():
    payload = build_portfolio_payload(
        [_asset_payload("BTCUSDT", 1100, 0.6, 0.02), _asset_payload("ETHUSDT", 900, -0.2, 0.08)],
        generated_at=START,
    )

    assert payload["execution_mode"] == "PAPER_ONLY"
    assert payload["summary"]["total_return"] == pytest.approx(0.0)
    assert payload["summary"]["final_net_exposure"] == pytest.approx(0.2)
    assert payload["summary"]["final_gross_exposure"] == pytest.approx(0.4)
    assert payload["summary"]["max_liquidation_risk"] == pytest.approx(0.08)
    assert "no exchange margin netting" in payload["capital_model"]


def test_stable_view_diff_ignores_generation_time_and_trace_noise():
    before = {
        "generated_at": "2026-01-01T00:00:00+00:00",
        "market": {"symbol": "SOLUSDT", "timeframe": "1h", "latest_candle_at": "a", "freshness_status": "CURRENT", "degraded": False},
        "funding": {"coverage": {"status": "COMPLETE"}},
        "highest_risk": {"liquidation_risk": 0.1},
        "latest_stable_view": {"state": "RANGE"},
        "strategies": [{"id": "AARS_DYNAMIC", "summary": {"total_return": 0.1}, "trace": [{"equity": 1}]}],
        "review_gate": {"disposition": "ACCEPT_WITH_MONITORING", "reasons": [], "live_execution_allowed": False},
    }
    same = {**before, "generated_at": "2026-01-02T00:00:00+00:00"}
    same["strategies"] = [{**before["strategies"][0], "trace": [{"equity": 999}]}]
    assert compare_stable_views(before, same)["summary"]["status"] == "UNCHANGED"

    changed = {**same, "latest_stable_view": {"state": "BREAKDOWN"}}
    diff = compare_stable_views(before, changed)
    assert diff["summary"]["status"] == "MATERIAL_CHANGE"
    assert any(item["path"] == "latest_stable_view.state" for item in diff["changes"])


def test_portfolio_api_get_is_paper_only_and_does_not_archive(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT"):
        candles = [_candle(symbol, hour, 100.0 + hour * 0.01) for hour in range(181)]
        store.upsert_candles(candles, "test")
        store.upsert_funding_rates(
            [FundingRate(symbol, START + timedelta(hours=hour), 0.0001, 100.0) for hour in range(119, 181, 8)],
            "test",
        )
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)
    handler.path = "/api/v1/portfolio?symbols=BTCUSDT,ETHUSDT,SOLUSDT&window=30d&strategy=AARS_DYNAMIC"

    status, payload = handler._api_payload()

    assert status == HTTPStatus.OK
    assert payload["schema_version"] == "mil3.portfolio.v1"
    assert payload["execution_mode"] == "PAPER_ONLY"
    assert len(payload["assets"]) == 3
    assert store.list_latest_stable_views() == []


def test_mil38_static_console_exposes_portfolio_and_diff_without_execution_controls():
    ui_root = Path(__file__).parents[1] / "ui"
    html = (ui_root / "index.html").read_text(encoding="utf-8")
    javascript = (ui_root / "app.js").read_text(encoding="utf-8")
    assert 'id="portfolio-metrics"' in html
    assert 'id="diff-before"' in html and 'id="diff-after"' in html
    assert "/api/v1/portfolio" in javascript
    assert "/api/v1/stable-view-diff" in javascript
    assert "NO LIVE EXECUTION" in html
