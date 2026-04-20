from weather_comparison_engine.compare.confidence_compare import ConfidenceCompare


def test_adjusted_gap():
    cmp = ConfidenceCompare()
    assert cmp.adjusted_gap(1, 0.8) == 0.8
    assert cmp.adjusted_gap(2, 0.5) == 1.0
