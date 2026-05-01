from backend.probability.weather_probability_provider import WeatherProbabilityProvider
from backend.sources.mock_market_source import MockMarketSource
from backend.storage.db import init_db
from backend.storage.repositories import Repository


DB = "tmp_weather_probability_provider.sqlite"
init_db(DB)
repo = Repository(DB)
provider = WeatherProbabilityProvider(
    repository=repo,
    default_year=2026,
    allow_network=False,
    default_sigma=2.5,
)

markets = MockMarketSource().fetch_markets()
for market in markets:
    if "weather" not in market.market_id:
        continue
    probability_view = provider.build_probability_view(market)
    print("\n---")
    print(market.market_id)
    print("question:", market.question)
    print("model_probability:", probability_view.model_probability)
    print("probability_view:", probability_view.model_dump())

print("\nlatest evidence:")
print(repo.get_latest_evidence_pack("mock_weather_strong_yes"))
print("\nlatest weather view:")
print(repo.get_latest_weather_view("mock_weather_strong_yes"))
print("\nlatest probability view:")
print(repo.get_latest_probability_view("mock_weather_strong_yes"))
