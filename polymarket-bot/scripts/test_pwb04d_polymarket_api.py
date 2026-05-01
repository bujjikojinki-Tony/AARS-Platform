from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from backend.app_factory import create_app


def show(title, value):
    print("\n---")
    print(title)
    print(value)


app = create_app(
    db_path="tmp_pwb04d_api.sqlite",
    allow_network=False,
    allow_polymarket_network=False,
    market_source_mode="MOCK_ONLY",
)
client = TestClient(app)

healthz = client.get("/healthz").json()
show("healthz", healthz)
assert healthz["market_source_mode"] == "MOCK_ONLY"
assert healthz["allow_polymarket_network"] is False
assert healthz["live_execution"] is False

pm_health = client.get("/api/polymarket/health").json()
show("polymarket health", pm_health)
assert pm_health["status"] == "ok"
assert pm_health["health"]["gamma_reachable"] is False
assert pm_health["health"]["clob_reachable"] is False
assert any("network access disabled" in warning for warning in pm_health["health"]["warnings"])

source_mode = client.get("/api/polymarket/source-mode").json()
show("source mode", source_mode)
assert source_mode["status"] == "ok"
assert source_mode["market_source_mode"] == "MOCK_ONLY"
assert source_mode["allow_polymarket_network"] is False

markets = client.get("/api/polymarket/markets").json()
show("cached markets", markets)
assert markets["status"] == "ok"
assert isinstance(markets["items"], list)

weather_markets = client.get("/api/polymarket/weather-markets").json()
show("weather markets", weather_markets)
assert weather_markets["status"] == "ok"

sync = client.post("/api/polymarket/sync-weather-markets", json={"limit": 10}).json()
show("sync weather markets", sync)
assert sync["status"] == "ok"
assert sync["saved_count"] == 0
assert any("MOCK_ONLY" in warning for warning in sync["warnings"])

switch = client.post(
    "/api/polymarket/source-mode",
    json={
        "market_source_mode": "HYBRID",
        "allow_polymarket_network": False,
    },
).json()
show("switch source mode", switch)
assert switch["status"] == "ok"
assert switch["market_source_mode"] == "HYBRID"
assert switch["allow_polymarket_network"] is False
assert switch["live_execution"] is False

scan = client.post("/api/opportunities/scan").json()
show("scan after HYBRID switch", scan)
assert scan["status"] == "ok"
assert scan["candidates_count"] >= 1

live = client.post(
    "/api/settings/mode",
    json={"mode": "LIVE_EXECUTE"},
).json()
show("live execute attempt", live)
assert live["status"] == "error"
assert "LIVE_EXECUTE" in live["message"]

print("\nPWB-04D Phase G Polymarket API smoke test passed.")
