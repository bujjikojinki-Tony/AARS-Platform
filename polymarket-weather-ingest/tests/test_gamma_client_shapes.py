from polymarket_weather_ingest.ingest.gamma_client import GammaClient


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params=None):
        return FakeResponse(self.payload)


def test_fetch_active_events_sync_shape(monkeypatch) -> None:
    payload = [{"title": "Weather", "markets": []}]

    monkeypatch.setattr(
        "polymarket_weather_ingest.ingest.gamma_client.httpx.Client",
        lambda timeout=20: FakeClient(payload),
    )

    client = GammaClient()
    events = client.fetch_active_events_sync(limit=2)

    assert len(events) >= 1
    assert "title" in events[0]
    assert "markets" in events[0]
    assert isinstance(events[0]["markets"], list)
