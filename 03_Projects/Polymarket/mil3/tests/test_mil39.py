from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from http import HTTPStatus

from aars_market import adapters
from aars_market.api import make_handler
from aars_market.coverage import analyze_funding_coverage
from aars_market.ingestion import IncrementalIngestor
from aars_market.models import Candle, FundingCadenceObservation, FundingRate
from aars_market.service import DashboardRequest, DashboardService
from aars_market.storage import MarketStore


START = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _candles(symbol: str, n: int = 181) -> list[Candle]:
    return [
        Candle(
            symbol=symbol,
            timeframe="1h",
            open_time=START + timedelta(hours=index),
            open=100.0 + index * 0.01,
            high=101.0 + index * 0.01,
            low=99.0 + index * 0.01,
            close=100.0 + index * 0.01,
            volume=1000.0,
        )
        for index in range(n)
    ]


def test_public_funding_info_adapter_decodes_adjusted_interval(monkeypatch):
    monkeypatch.setattr(
        adapters,
        "_request_funding_info",
        lambda _timeout: [
            {
                "symbol": "SOLUSDT",
                "adjustedFundingRateCap": "0.02000000",
                "adjustedFundingRateFloor": "-0.02000000",
                "fundingIntervalHours": 4,
                "disclaimer": False,
            }
        ],
    )

    observations = adapters.fetch_binance_funding_info(observed_at=START)

    assert observations == [
        FundingCadenceObservation(
            "SOLUSDT", START, 4, 0.02, -0.02, False, "ADJUSTED"
        )
    ]


def test_cadence_store_is_idempotent_and_includes_prior_observation(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    observations = [
        FundingCadenceObservation("SOLUSDT", START, 8, source_status="DEFAULT_ABSENT"),
        FundingCadenceObservation("SOLUSDT", START + timedelta(hours=12), 4),
    ]
    store.upsert_funding_cadence_observations(observations, "test")
    store.upsert_funding_cadence_observations(observations, "test")

    loaded = store.load_funding_cadence_observations(
        "SOLUSDT",
        start=START + timedelta(hours=10),
        end=START + timedelta(hours=20),
        include_previous=True,
    )
    assert loaded == observations


def test_incremental_cycle_fetches_one_snapshot_and_records_explicit_defaults(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    calls = 0

    def funding_info(**_kwargs):
        nonlocal calls
        calls += 1
        return [FundingCadenceObservation("SOLUSDT", START, 4)]

    summary = IncrementalIngestor(
        store,
        candle_fetcher=lambda *_args: [],
        funding_fetcher=lambda *_args: [],
        funding_info_fetcher=funding_info,
    ).run_cycle(now=START)

    assert calls == 1
    assert summary["status"] == "SUCCESS"
    cadence = {
        symbol: store.load_funding_cadence_observations(symbol)[0]
        for symbol in ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    }
    assert cadence["SOLUSDT"].interval_hours == 4
    assert cadence["SOLUSDT"].source_status == "ADJUSTED"
    assert cadence["BTCUSDT"].interval_hours == 8
    assert cadence["BTCUSDT"].source_status == "DEFAULT_ABSENT"
    info_record = next(item for item in summary["resources"] if item["resource"] == "funding_info")
    assert info_record["details"]["SOLUSDT"]["interval_hours"] == 4


def test_failed_snapshot_does_not_invent_default_observations(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()

    def unavailable(**_kwargs):
        raise RuntimeError("snapshot unavailable")

    summary = IncrementalIngestor(
        store,
        symbols=["SOLUSDT"],
        candle_fetcher=lambda *_args: [],
        funding_fetcher=lambda *_args: [],
        funding_info_fetcher=unavailable,
    ).run_cycle(now=START)

    assert summary["status"] == "PARTIAL"
    assert store.load_funding_cadence_observations("SOLUSDT") == []


def test_dynamic_4h_cadence_detects_gap_that_8h_model_would_miss():
    observation = FundingCadenceObservation("SOLUSDT", START + timedelta(hours=8), 4)
    rates = [
        FundingRate("SOLUSDT", START + timedelta(hours=hour), 0.0001)
        for hour in (0, 8, 12, 20, 24)
    ]

    dynamic = analyze_funding_coverage(
        rates,
        START,
        START + timedelta(hours=24),
        cadence_observations=[observation],
    )
    fixed = analyze_funding_coverage(rates, START, START + timedelta(hours=24))

    assert dynamic.status == "GAPPED"
    assert dynamic.estimated_missing_events == 1
    assert dynamic.cadence_hours == 4
    assert dynamic.cadence_source == "ADJUSTED"
    assert fixed.status == "COMPLETE"


def test_no_cadence_observation_uses_explicit_8h_fallback():
    rates = [
        FundingRate("SOLUSDT", START + timedelta(hours=hour), 0.0001)
        for hour in (0, 8, 16, 24)
    ]
    coverage = analyze_funding_coverage(rates, START, START + timedelta(hours=24))
    assert coverage.status == "COMPLETE"
    assert coverage.cadence_hours == 8
    assert coverage.cadence_source == "DEFAULT_8H_FALLBACK"
    assert coverage.cadence_observed_at is None


def test_temporary_4h_adjustment_returns_to_observed_8h_default():
    rates = [
        FundingRate("SOLUSDT", START + timedelta(hours=hour), 0.0001)
        for hour in (0, 8, 12, 16, 20, 28)
    ]
    observations = [
        FundingCadenceObservation("SOLUSDT", START + timedelta(hours=8), 4),
        FundingCadenceObservation(
            "SOLUSDT",
            START + timedelta(hours=20),
            8,
            source_status="DEFAULT_ABSENT",
        ),
    ]

    coverage = analyze_funding_coverage(
        rates,
        START,
        START + timedelta(hours=28),
        cadence_observations=observations,
    )

    assert coverage.status == "COMPLETE"
    assert coverage.cadence_hours == 8
    assert coverage.cadence_source == "DEFAULT_ABSENT"
    assert [period.interval_hours for period in coverage.cadence_schedule] == [8, 4, 8]


def test_dashboard_uses_persisted_dynamic_cadence_and_exposes_provenance(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    candles = _candles("SOLUSDT")
    store.upsert_candles(candles, "test")
    store.upsert_funding_cadence_observations(
        [FundingCadenceObservation("SOLUSDT", candles[127].open_time, 4)],
        "test",
    )
    store.upsert_funding_rates(
        [
            FundingRate("SOLUSDT", candles[index].open_time, 0.0001, candles[index].close)
            for index in (119, 127, 131, 139, 143, 147, 151, 155, 159, 163, 167, 171, 175, 179)
        ],
        "test",
    )

    payload = DashboardService(store).build(
        DashboardRequest("SOLUSDT", "1h", "30d"),
        now=candles[-1].open_time + timedelta(hours=1),
        archive=False,
    )

    coverage = payload["funding"]["coverage"]
    assert coverage["status"] == "GAPPED"
    assert coverage["cadence_hours"] == 4
    assert coverage["cadence_source"] == "ADJUSTED"
    assert coverage["cadence_observed_at"] == candles[127].open_time.isoformat()
    assert any(alert["id"] == "FUNDING_COVERAGE_GAP" for alert in payload["alerts"])


def test_read_only_api_exposes_current_cadence_and_observation_history(tmp_path: Path):
    store = MarketStore(tmp_path / "market.sqlite")
    store.init_db()
    store.upsert_funding_cadence_observations(
        [FundingCadenceObservation("SOLUSDT", START, 4, 0.02, -0.02)],
        "test",
    )
    handler_type = make_handler(DashboardService(store), tmp_path)
    handler = object.__new__(handler_type)
    handler.path = "/api/v1/funding-cadence?symbol=SOLUSDT"

    status, payload = handler._api_payload()

    assert status == HTTPStatus.OK
    assert payload["execution_mode"] == "PAPER_ONLY"
    assert payload["current"]["interval_hours"] == 4
    assert payload["current"]["source_status"] == "ADJUSTED"
    assert len(payload["observations"]) == 1
