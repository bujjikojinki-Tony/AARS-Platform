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
    db_path="tmp_pwb04d_default.sqlite",
    allow_network=False,
    allow_polymarket_network=False,
    market_source_mode="MOCK_ONLY",
)
client = TestClient(app)
health = client.get("/healthz").json()
show("Default healthz", health)
assert health["allow_polymarket_network"] is False
assert health["market_source_mode"] == "MOCK_ONLY"
assert health["live_execution"] is False
scan = client.post("/api/opportunities/scan").json()
show("Default scan", scan)
assert scan["status"] == "ok"
assert scan["candidates_count"] >= 1

app_hybrid = create_app(
    db_path="tmp_pwb04d_hybrid.sqlite",
    allow_network=False,
    allow_polymarket_network=False,
    market_source_mode="HYBRID",
)
client_hybrid = TestClient(app_hybrid)
health_hybrid = client_hybrid.get("/healthz").json()
show("HYBRID healthz", health_hybrid)
assert health_hybrid["market_source_mode"] == "HYBRID"
assert health_hybrid["allow_polymarket_network"] is False
scan_hybrid = client_hybrid.post("/api/opportunities/scan").json()
show("HYBRID scan", scan_hybrid)
assert scan_hybrid["status"] == "ok"
assert scan_hybrid["candidates_count"] >= 1

app_pm_only = create_app(
    db_path="tmp_pwb04d_pm_only.sqlite",
    allow_network=False,
    allow_polymarket_network=False,
    market_source_mode="POLYMARKET_ONLY",
)
client_pm_only = TestClient(app_pm_only)
health_pm_only = client_pm_only.get("/healthz").json()
show("POLYMARKET_ONLY healthz", health_pm_only)
assert health_pm_only["market_source_mode"] == "POLYMARKET_ONLY"
assert health_pm_only["allow_polymarket_network"] is False
scan_pm_only = client_pm_only.post("/api/opportunities/scan").json()
show("POLYMARKET_ONLY scan", scan_pm_only)
assert scan_pm_only["status"] == "ok"
assert scan_pm_only["candidates_count"] == 0

live = client.post(
    "/api/settings/mode",
    json={"mode": "LIVE_EXECUTE"},
).json()
show("LIVE_EXECUTE attempt", live)
assert live["status"] == "error"
assert "LIVE_EXECUTE" in live["message"]

print("\nPWB-04D Phase E app factory integration smoke test passed.")
