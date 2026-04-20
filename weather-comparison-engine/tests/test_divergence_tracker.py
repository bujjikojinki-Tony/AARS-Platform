from weather_comparison_engine.compare.divergence_tracker import DivergenceTracker


def test_divergence_classify():
    tracker = DivergenceTracker()
    assert tracker.classify(0) == "aligned"
    assert tracker.classify(1) == "mild_divergence"
    assert tracker.classify(2) == "strong_divergence"
