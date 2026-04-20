from polymarket_weather_ingest.discovery.weather_filter import WeatherFilter


def test_weather_filter_detects_weather_keyword():
    weather_filter = WeatherFilter()
    event = {"title": "Highest temperature in Central Park on Apr 12?"}
    assert weather_filter.is_weather_event(event) is True


def test_weather_filter_rejects_non_weather_event():
    weather_filter = WeatherFilter()
    event = {"title": "Will candidate X win?"}
    assert weather_filter.is_weather_event(event) is False


def test_weather_filter_rejects_geopolitical_event():
    weather_filter = WeatherFilter()
    event = {"title": "Will Russia capture Sumy by March 31, 2027?"}
    assert weather_filter.is_weather_event(event) is False
