from weather_signal_engine.features.run_to_run_change import compute_run_to_run_change


def test_run_to_run_change():
    assert compute_run_to_run_change(27.1, 27.8) == 0.7
    assert compute_run_to_run_change(None, 27.8) is None
