import ssl
from urllib.error import URLError

from weather_dashboard.loaders.wunderground_loader import WundergroundShanghaiLoader


def test_extract_embedded_urls() -> None:
    html = """
    <html><body>
    <script>
    {"url":"https://api.weather.com/v3/wx/forecast/daily/5day?apiKey=abc&geocode=31.15%2C121.803&units=e"}
    {"url":"https://api.weather.com/v3/wx/observations/current?apiKey=abc&icaoCode=ZSPD&units=e"}
    </script>
    </body></html>
    """

    forecast_url = WundergroundShanghaiLoader.extract_forecast_url(html)
    current_url = WundergroundShanghaiLoader.extract_current_url(html)

    assert forecast_url is not None
    assert "forecast/daily/5day" in forecast_url
    assert current_url is not None
    assert "observations/current" in current_url


def test_normalize_target_date() -> None:
    assert (
        WundergroundShanghaiLoader._normalize_target_date("Apr 14", default_year=2026)
        == "2026-04-14"
    )


def test_select_forecast_index() -> None:
    payload = {
        "validTimeLocal": [
            "2026-04-14T07:00:00+0800",
            "2026-04-15T07:00:00+0800",
        ],
        "temperatureMax": [64, 67],
    }

    assert WundergroundShanghaiLoader._select_forecast_index(payload, "Apr 14") == 0


def test_fahrenheit_to_celsius() -> None:
    assert WundergroundShanghaiLoader._fahrenheit_to_celsius(68) == 20.0


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return self.text.encode("utf-8")


def test_fetch_text_insecure_ssl_fallback_is_opt_in(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout=20, context=None):
        calls.append(context)
        if context is None:
            raise URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))
        return FakeResponse("ok")

    monkeypatch.setenv("WUNDERGROUND_ALLOW_INSECURE_SSL", "1")
    monkeypatch.setattr("weather_dashboard.loaders.wunderground_loader.urlopen", fake_urlopen)

    assert WundergroundShanghaiLoader._fetch_text("https://example.test") == "ok"
    assert len(calls) == 2
    assert calls[0] is None
    assert calls[1] is not None
