from weather_rules_research.backtest.drift_eval import DriftEvaluator, ForecastDriftRow


def build_rows() -> list[ForecastDriftRow]:
    return [
        ForecastDriftRow(
            forecast_issued_date="2026-04-05",
            target_date="2026-04-12",
            lead_days=7,
            forecast_value=29.0,
            official_value=27.0,
        ),
        ForecastDriftRow(
            forecast_issued_date="2026-04-07",
            target_date="2026-04-12",
            lead_days=5,
            forecast_value=28.5,
            official_value=27.0,
        ),
        ForecastDriftRow(
            forecast_issued_date="2026-04-09",
            target_date="2026-04-12",
            lead_days=3,
            forecast_value=27.8,
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


def test_mean_error_by_lead() -> None:
    evaluator = DriftEvaluator()
    rows = build_rows()

    result = evaluator.mean_error_by_lead(rows)

    assert result[7] == 2.0
    assert result[1] == 0.2


def test_mae_by_lead() -> None:
    evaluator = DriftEvaluator()
    rows = build_rows()

    result = evaluator.mae_by_lead(rows)

    assert result[5] == 1.5
    assert result[3] == 0.8


def test_forecast_trend_for_target() -> None:
    evaluator = DriftEvaluator()
    rows = build_rows()

    trend = evaluator.forecast_trend_for_target(rows, "2026-04-12")

    assert len(trend) == 4
    assert trend[0].lead_days == 7
    assert trend[-1].lead_days == 1


def test_drift_span_for_target() -> None:
    evaluator = DriftEvaluator()
    rows = build_rows()

    span = evaluator.drift_span_for_target(rows, "2026-04-12")

    assert span == 1.8
