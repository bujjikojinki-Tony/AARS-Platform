from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.models.polymarket import MarketSourceMode
from backend.models.polymarket import PolymarketConnectorHealth
from backend.models.polymarket import PolymarketMarketRecord
from backend.storage.db import init_db
from backend.storage.repositories import Repository


DB = "tmp_pwb04d_cache.sqlite"
init_db(DB)
repo = Repository(DB)

record = PolymarketMarketRecord(
    polymarket_market_id="pm_weather_1",
    condition_id="cond_weather_1",
    question="Will Tokyo high temperature exceed 30C on June 1?",
    slug="tokyo-high-temperature-june-1",
    category="weather",
    active=True,
    closed=False,
    archived=False,
    outcomes=["Yes", "No"],
    outcome_prices=[0.52, 0.49],
    clob_token_ids=["token_yes", "token_no"],
    liquidity=1000,
    volume=5000,
    raw_payload={"mock": True},
)
repo.save_polymarket_market_record(record)

health = PolymarketConnectorHealth(
    gamma_reachable=False,
    clob_reachable=False,
    mode=MarketSourceMode.MOCK_ONLY,
    warnings=["Polymarket network access disabled by config."],
)
repo.save_polymarket_connector_health(health)

print("\nMarket cache:")
print(repo.list_polymarket_market_cache())
print("\nWeather market cache:")
print(repo.list_polymarket_weather_market_cache())
print("\nLatest health:")
print(repo.get_latest_polymarket_connector_health())

assert len(repo.list_polymarket_market_cache()) == 1
assert len(repo.list_polymarket_weather_market_cache()) == 1
latest_health = repo.get_latest_polymarket_connector_health()
assert latest_health is not None
assert latest_health["gamma_reachable"] is False
assert latest_health["clob_reachable"] is False
assert latest_health["mode"] == "MOCK_ONLY"
assert "network access disabled" in latest_health["warnings"][0]

print("\nPWB-04D Phase F cache repository smoke test passed.")
