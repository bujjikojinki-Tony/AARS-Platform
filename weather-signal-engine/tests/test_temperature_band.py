from weather_signal_engine.features.temperature_band import classify_temperature_band


def test_temperature_band():
    assert classify_temperature_band(25.8) == "26_or_below"
    assert classify_temperature_band(27.1) == "27"
    assert classify_temperature_band(28.3) == "28"
    assert classify_temperature_band(29.4) == "29_plus"
