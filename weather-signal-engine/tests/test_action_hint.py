from weather_signal_engine.scoring.action_hint import choose_action_hint


def test_action_hint():
    assert choose_action_hint(0.0, 0.9) == "watch"
    assert choose_action_hint(1.0, 0.85) == "approve_small"
    assert choose_action_hint(1.0, 0.4) == "ignore"
