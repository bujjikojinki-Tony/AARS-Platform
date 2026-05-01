from backend.execution.risk_manager import RiskManager
from backend.execution.strategy_runner import StrategyRunner
from backend.probability.weather_probability_provider import WeatherProbabilityProvider
from backend.sources.mock_market_source import MockMarketSource
from backend.storage.db import init_db
from backend.storage.repositories import Repository
from backend.strategies.binary_arb_strategy import BinaryArbStrategy
from backend.strategies.weather_edge_strategy import WeatherEdgeStrategy


DB = "tmp_pwb02_runner.sqlite"
init_db(DB)
repo = Repository(DB)
probability_provider = WeatherProbabilityProvider(
    repository=repo,
    default_year=2026,
    allow_network=False,
    default_sigma=2.5,
)
runner = StrategyRunner(
    market_source=MockMarketSource(),
    strategies=[
        WeatherEdgeStrategy(probability_provider),
        BinaryArbStrategy(),
    ],
    risk_manager=RiskManager(),
    repository=repo,
)

candidates = runner.run_once()
print("candidates_count:", len(candidates))
for candidate in candidates:
    print(candidate.model_dump())

print("\nweather descriptors:")
print(repo.list_weather_descriptors())
print("\nlatest probability for strong yes:")
print(repo.get_latest_probability_view("mock_weather_strong_yes"))
