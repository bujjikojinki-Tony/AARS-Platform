from weather_rules_research.backtest.stability_eval import StabilityEvaluator, StabilityRow


def build_rows() -> list[StabilityRow]:
    return [
        StabilityRow(group_key="CentralPark-Apr", forecast_value=27.2, official_value=27.0),
        StabilityRow(group_key="CentralPark-Apr", forecast_value=28.1, official_value=28.0),
        StabilityRow(group_key="CentralPark-Apr", forecast_value=26.8, official_value=27.0),
        StabilityRow(group_key="Singapore-Apr", forecast_value=33.5, official_value=32.0),
        StabilityRow(group_key="Singapore-Apr", forecast_value=34.0, official_value=32.2),
        StabilityRow(group_key="Singapore-Apr", forecast_value=31.0, official_value=32.0),
    ]


def test_mean_error_by_group() -> None:
    evaluator = StabilityEvaluator()
    rows = build_rows()

    result = evaluator.mean_error_by_group(rows)

    assert round(result["CentralPark-Apr"], 4) == 0.0333
    assert round(result["Singapore-Apr"], 4) == 0.7667


def test_mae_by_group() -> None:
    evaluator = StabilityEvaluator()
    rows = build_rows()

    result = evaluator.mae_by_group(rows)

    assert round(result["CentralPark-Apr"], 4) == 0.1667
    assert round(result["Singapore-Apr"], 4) == 1.4333


def test_error_range_by_group() -> None:
    evaluator = StabilityEvaluator()
    rows = build_rows()

    result = evaluator.error_range_by_group(rows)

    assert result["CentralPark-Apr"] == 0.4
    assert result["Singapore-Apr"] == 2.8


def test_stable_groups() -> None:
    evaluator = StabilityEvaluator()
    rows = build_rows()

    stable = evaluator.stable_groups(
        rows=rows,
        max_mae=0.3,
        max_error_range=0.5,
    )

    assert "CentralPark-Apr" in stable
    assert "Singapore-Apr" not in stable
