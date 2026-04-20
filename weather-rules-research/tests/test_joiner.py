from datetime import date

import pytest

from weather_rules_research.backtest import (
    evaluate_bias,
    join_forecasts_to_settlements,
    summarize_bias_metrics,
)
from weather_rules_research.models import ForecastSnapshot, SettlementRecord


def test_join_forecasts_to_settlements_matches_on_station_and_date() -> None:
    forecasts = [
        ForecastSnapshot(
            market_id="market-1",
            station_id="KPHX",
            market_type="daily_high_temperature",
            target_date=date(2026, 6, 1),
            issued_at="2026-05-31T18:00:00Z",
            predicted_temperature_c=38.1,
        )
    ]
    settlements = [
        SettlementRecord(
            station_id="KPHX",
            target_date="2026-06-01",
            variable_name="daily_max_temperature",
            official_value=37.3,
            unit="C",
            source="official_obs",
            source_url="https://example.test/source",
            raw_payload_ref="official-obs://example",
        )
    ]

    joined = join_forecasts_to_settlements(forecasts=forecasts, settlements=settlements)

    assert len(joined) == 1
    assert joined[0].predicted_temperature_c == 38.1
    assert joined[0].settled_temperature_c == 37.3
    assert joined[0].settlement_unit == "C"


def test_summarize_bias_metrics_returns_mean_error_mae_rmse_and_band_hit_rate() -> None:
    joined = [
        join_forecasts_to_settlements(
            forecasts=[
                ForecastSnapshot(
                    market_id="market-1",
                    station_id="KPHX",
                    market_type="daily_high_temperature",
                    target_date=date(2026, 6, 1),
                    issued_at="2026-05-31T18:00:00Z",
                    predicted_temperature_c=38.0,
                ),
                ForecastSnapshot(
                    market_id="market-2",
                    station_id="KNYC",
                    market_type="daily_low_temperature",
                    target_date=date(2026, 1, 15),
                    issued_at="2026-01-14T18:00:00Z",
                    predicted_temperature_c=10.0,
                ),
            ],
            settlements=[
                SettlementRecord(
                    station_id="KPHX",
                    target_date="2026-06-01",
                    variable_name="daily_max_temperature",
                    official_value=37.0,
                    unit="C",
                    source="official_obs",
                ),
                SettlementRecord(
                    station_id="KNYC",
                    target_date="2026-01-15",
                    variable_name="daily_min_temperature",
                    official_value=12.0,
                    unit="C",
                    source="official_obs",
                ),
            ],
        )
    ][0]

    rows = evaluate_bias(joined, band_c=1.5)
    summary = summarize_bias_metrics(rows, band_c=1.5)

    assert summary.mean_error_c == pytest.approx(-0.5)
    assert summary.mae_c == pytest.approx(1.5)
    assert summary.rmse_c == pytest.approx(1.581, abs=0.001)
    assert summary.band_hit_rate == pytest.approx(0.5)
