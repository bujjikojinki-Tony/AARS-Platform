import json
import ssl
from urllib.error import URLError

import certifi

from weather_dashboard.loaders.gamma_search_loader import GammaSearchLoader


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def test_gamma_search_loader_normalizes_results(monkeypatch):
    payload = {
        "results": [
            {
                "id": "123",
                "title": "Will 2026 be the third-hottest year on record?",
                "category": "Weather",
                "slug": "third-hottest-year-2026",
                "updatedAt": "2026-04-13T00:00:00Z",
            }
        ]
    }

    monkeypatch.setattr(
        "weather_dashboard.loaders.gamma_search_loader.urlopen",
        lambda request, timeout=15: FakeResponse(payload),
    )

    loader = GammaSearchLoader(base_url="https://gamma-api.polymarket.com")
    results = loader.search("third hottest year", limit=10)

    assert len(results) == 1
    assert results[0]["market_id"] == "123"
    assert results[0]["market_question"] == "Will 2026 be the third-hottest year on record?"
    assert results[0]["market_family"] == "Weather"
    assert results[0]["search_source"] == "gamma"


def test_gamma_search_loader_insecure_ssl_fallback_is_opt_in(monkeypatch):
    payload = {
        "results": [
            {
                "id": "456",
                "title": "Shanghai temperature market",
                "category": "Weather",
            }
        ]
    }
    calls = []

    def fake_urlopen(request, timeout=15, context=None):
        calls.append(context)
        if context is None:
            raise URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))
        return FakeResponse(payload)

    monkeypatch.setenv("GAMMA_SEARCH_ALLOW_INSECURE_SSL", "1")
    monkeypatch.setattr("weather_dashboard.loaders.gamma_search_loader.urlopen", fake_urlopen)

    loader = GammaSearchLoader(base_url="https://gamma-api.polymarket.com")
    results = loader.search("shanghai", limit=10)

    assert len(calls) == 2
    assert calls[0] is None
    assert calls[1] is not None
    assert results[0]["market_id"] == "456"


def test_gamma_search_loader_prefers_certifi_ca_bundle(monkeypatch):
    payload = {
        "results": [
            {
                "id": "789",
                "title": "Shanghai weather market",
                "category": "Weather",
            }
        ]
    }
    calls = []
    def fake_urlopen(request, timeout=15, context=None):
        calls.append(context)
        if context is None:
            raise URLError(ssl.SSLCertVerificationError("CERTIFICATE_VERIFY_FAILED"))
        return FakeResponse(payload)

    monkeypatch.setenv("GAMMA_SEARCH_CA_BUNDLE", certifi.where())
    monkeypatch.setattr("weather_dashboard.loaders.gamma_search_loader.urlopen", fake_urlopen)

    loader = GammaSearchLoader(base_url="https://gamma-api.polymarket.com")
    results = loader.search("shanghai", limit=10)

    assert len(calls) == 2
    assert calls[0] is None
    assert calls[1] is not None
    assert results[0]["market_id"] == "789"
