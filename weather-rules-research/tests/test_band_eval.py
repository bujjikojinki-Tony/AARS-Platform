from weather_rules_research.backtest.band_eval import BandEvaluator, TemperatureBand


def build_evaluator() -> BandEvaluator:
    bands = [
        TemperatureBand(label="26_or_below", upper=26.0),
        TemperatureBand(label="27", lower=26.0, upper=27.0, lower_inclusive=False),
        TemperatureBand(label="28", lower=27.0, upper=28.0, lower_inclusive=False),
        TemperatureBand(label="29_plus", lower=28.0, lower_inclusive=False, upper=None),
    ]
    return BandEvaluator(bands)


def test_band_classification() -> None:
    evaluator = build_evaluator()

    assert evaluator.classify(25.8) == "26_or_below"
    assert evaluator.classify(27.0) == "27"
    assert evaluator.classify(28.0) == "28"
    assert evaluator.classify(29.3) == "29_plus"


def test_band_hit() -> None:
    evaluator = build_evaluator()
    assert evaluator.hit(27.2, 27.8) is False
    assert evaluator.hit(27.2, 27.0) is True


def test_adjacent_hit() -> None:
    evaluator = build_evaluator()
    assert evaluator.adjacent_hit(27.2, 28.0) is True


def test_extreme_miss() -> None:
    evaluator = build_evaluator()
    assert evaluator.extreme_miss(25.5, 29.4) is True
