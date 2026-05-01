from __future__ import annotations

from dataclasses import dataclass

from backend.connectors.polymarket_config import PolymarketConnectorConfig
from backend.connectors.polymarket_read_only_market_source import PolymarketReadOnlyMarketSource
from backend.execution.risk_manager import RiskManager
from backend.execution.simulator import Simulator
from backend.execution.strategy_runner import StrategyRunner
from backend.governance.rule_registry import RuleRegistry
from backend.models.polymarket import MarketSourceMode
from backend.probability.weather_probability_provider import WeatherProbabilityProvider
from backend.sources.mock_market_source import MockMarketSource
from backend.storage.db import init_db
from backend.storage.repositories import Repository
from backend.strategies.binary_arb_strategy import BinaryArbStrategy
from backend.strategies.weather_edge_strategy import WeatherEdgeStrategy


@dataclass(slots=True)
class AppServices:
    db_path: str
    allow_network: bool
    allow_polymarket_network: bool
    market_source_mode: MarketSourceMode
    default_year: int
    default_sigma: float
    archive_weather_on_probability_build: bool
    repository: Repository
    polymarket_config: PolymarketConnectorConfig
    mock_market_source: MockMarketSource
    market_source: object
    probability_provider: WeatherProbabilityProvider
    risk_manager: RiskManager
    strategies: list
    strategy_runner: StrategyRunner
    simulator: Simulator
    rule_registry: RuleRegistry


def _normalize_market_source_mode(value: str | MarketSourceMode) -> MarketSourceMode:
    if isinstance(value, MarketSourceMode):
        return value
    return MarketSourceMode(str(value))


def create_market_source(
    polymarket_config: PolymarketConnectorConfig,
    mock_source: MockMarketSource,
):
    if polymarket_config.market_source_mode == MarketSourceMode.MOCK_ONLY:
        return mock_source
    return PolymarketReadOnlyMarketSource(
        config=polymarket_config,
        mock_source=mock_source,
    )


def create_services(
    db_path: str,
    *,
    allow_network: bool = False,
    allow_polymarket_network: bool = False,
    market_source_mode: MarketSourceMode | str = MarketSourceMode.MOCK_ONLY,
    default_year: int = 2026,
    default_sigma: float = 2.5,
    archive_weather_on_probability_build: bool = False,
) -> AppServices:
    init_db(db_path)
    repository = Repository(db_path)
    resolved_market_source_mode = _normalize_market_source_mode(market_source_mode)
    mock_market_source = MockMarketSource()
    probability_provider = WeatherProbabilityProvider(
        repository=repository,
        default_year=default_year,
        allow_network=allow_network,
        default_sigma=default_sigma,
        archive_weather_on_probability_build=archive_weather_on_probability_build,
    )
    polymarket_config = PolymarketConnectorConfig(
        market_source_mode=resolved_market_source_mode,
        allow_polymarket_network=allow_polymarket_network,
    )
    polymarket_config.validate_safe_defaults()
    market_source = create_market_source(
        polymarket_config=polymarket_config,
        mock_source=mock_market_source,
    )
    risk_manager = RiskManager()
    strategies = [
        WeatherEdgeStrategy(probability_provider),
        BinaryArbStrategy(),
    ]
    strategy_runner = StrategyRunner(
        market_source=market_source,
        strategies=strategies,
        risk_manager=risk_manager,
        repository=repository,
    )
    simulator = Simulator(repository)
    rule_registry = RuleRegistry(repository)
    return AppServices(
        db_path=db_path,
        allow_network=allow_network,
        allow_polymarket_network=allow_polymarket_network,
        market_source_mode=resolved_market_source_mode,
        default_year=default_year,
        default_sigma=default_sigma,
        archive_weather_on_probability_build=archive_weather_on_probability_build,
        repository=repository,
        polymarket_config=polymarket_config,
        mock_market_source=mock_market_source,
        market_source=market_source,
        probability_provider=probability_provider,
        risk_manager=risk_manager,
        strategies=strategies,
        strategy_runner=strategy_runner,
        simulator=simulator,
        rule_registry=rule_registry,
    )
