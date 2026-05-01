from backend.execution.risk_manager import RiskManager
from backend.execution.strategy_runner import StrategyRunner
from backend.probability.weather_probability_provider import WeatherProbabilityProvider
from backend.sources.mock_market_source import MockMarketSource
from backend.storage.db import init_db
from backend.storage.repositories import Repository
from backend.strategies.binary_arb_strategy import BinaryArbStrategy
from backend.strategies.weather_edge_strategy import WeatherEdgeStrategy


def test_weather_probability_provider_persists_intermediates(tmp_path) -> None:
    db_path = str(tmp_path / "weather_probability.sqlite")
    init_db(db_path)
    repository = Repository(db_path)
    provider = WeatherProbabilityProvider(
        repository=repository,
        default_year=2026,
        allow_network=False,
        default_sigma=2.5,
    )
    market = next(
        item for item in MockMarketSource().fetch_markets() if item.market_id == "mock_weather_strong_yes"
    )

    probability_view = provider.build_probability_view(market)

    assert 0.67 < probability_view.model_probability < 0.70
    assert repository.list_weather_descriptors()
    assert repository.get_latest_evidence_pack(market.market_id) is not None
    assert repository.get_latest_weather_view(market.market_id) is not None
    assert repository.get_latest_probability_view(market.market_id) is not None


def test_strategy_runner_uses_weather_probability_provider(tmp_path) -> None:
    db_path = str(tmp_path / "runner_weather_probability.sqlite")
    init_db(db_path)
    repository = Repository(db_path)
    provider = WeatherProbabilityProvider(
        repository=repository,
        default_year=2026,
        allow_network=False,
        default_sigma=2.5,
    )
    runner = StrategyRunner(
        market_source=MockMarketSource(),
        strategies=[
            WeatherEdgeStrategy(provider),
            BinaryArbStrategy(),
        ],
        risk_manager=RiskManager(),
        repository=repository,
    )

    candidates = runner.run_once()

    assert candidates
    strong_yes = next(
        item for item in candidates if item.market_id == "mock_weather_strong_yes"
    )
    assert 0.67 < strong_yes.model_probability < 0.70
    assert strong_yes.action_status.value == "SIMULATE"
    assert repository.get_latest_probability_view("mock_weather_strong_yes") is not None
    assert any(
        row["event_type"] == "SIMULATION_CREATED"
        for row in repository.list_table("audit_logs")
    ) is False
