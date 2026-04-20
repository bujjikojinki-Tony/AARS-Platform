from pathlib import Path
from tempfile import TemporaryDirectory

from weather_rules_research.backtest.band_eval import BandEvaluator, TemperatureBand
from weather_rules_research.backtest.drift_eval import ForecastDriftRow
from weather_rules_research.backtest.joiner import JoinedForecastSettlement
from weather_rules_research.backtest.stability_eval import StabilityRow
from weather_rules_research.outputs.export_bias_report import BiasReportExporter


def build_band_evaluator() -> BandEvaluator:
    return BandEvaluator(
        [
            TemperatureBand(label="26_or_below", upper=26.0),
            TemperatureBand(label="27", lower=26.0, upper=27.0, lower_inclusive=False),
            TemperatureBand(label="28", lower=27.0, upper=28.0, lower_inclusive=False),
            TemperatureBand(label="29_plus", lower=28.0, lower_inclusive=False, upper=None),
        ]
    )


def test_export_summary_report_creates_csv() -> None:
    exporter = BiasReportExporter(band_evaluator=build_band_evaluator())

    joined_rows = [
        JoinedForecastSettlement(
            target_date="2026-04-12",
            variable_name="daily_max_temperature",
            forecast_value=27.3,
            official_value=27.0,
            error=0.3,
        ),
        JoinedForecastSettlement(
            target_date="2026-04-13",
            variable_name="daily_max_temperature",
            forecast_value=28.2,
            official_value=28.0,
            error=0.2,
        ),
    ]

    drift_rows = [
        ForecastDriftRow(
            forecast_issued_date="2026-04-09",
            target_date="2026-04-12",
            lead_days=3,
            forecast_value=27.5,
            official_value=27.0,
        ),
        ForecastDriftRow(
            forecast_issued_date="2026-04-11",
            target_date="2026-04-12",
            lead_days=1,
            forecast_value=27.2,
            official_value=27.0,
        ),
    ]

    stability_rows = [
        StabilityRow(group_key="CentralPark-Apr", forecast_value=27.3, official_value=27.0),
        StabilityRow(group_key="CentralPark-Apr", forecast_value=28.2, official_value=28.0),
    ]

    with TemporaryDirectory() as tmpdir:
        out = Path(tmpdir) / "summary.csv"
        exporter.export_summary_report(
            path=out,
            joined_rows=joined_rows,
            drift_rows=drift_rows,
            stability_rows=stability_rows,
        )

        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "mae" in content
        assert "band_hit_rate" in content
        assert "avg_drift_span" in content
