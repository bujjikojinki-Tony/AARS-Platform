from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import sys

from weather_dashboard.settings import WORKSPACE_DIR


ENGINE_SRC_DIR = WORKSPACE_DIR / "weather-comparison-engine" / "src"
PWB01_DB_PATH = WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "polymarket_bot_pwb01.sqlite"


if str(ENGINE_SRC_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_SRC_DIR))

from weather_comparison_engine.polymarket_bot import CommandRoutes
from weather_comparison_engine.polymarket_bot import HistoryRoutes
from weather_comparison_engine.polymarket_bot import MockMarketSource
from weather_comparison_engine.polymarket_bot import OpportunityRoutes
from weather_comparison_engine.polymarket_bot import PlaceholderProbabilityProvider
from weather_comparison_engine.polymarket_bot import PolymarketBotRepositories
from weather_comparison_engine.polymarket_bot import RiskManager
from weather_comparison_engine.polymarket_bot import RiskRules
from weather_comparison_engine.polymarket_bot import SettingsRoutes
from weather_comparison_engine.polymarket_bot import Simulator
from weather_comparison_engine.polymarket_bot import StrategyRunner
from weather_comparison_engine.polymarket_bot import WeatherEdgeStrategy
from weather_comparison_engine.polymarket_bot import init_db


@dataclass(slots=True)
class PWB01Runtime:
    repositories: object
    opportunity_routes: OpportunityRoutes
    command_routes: CommandRoutes
    history_routes: HistoryRoutes
    settings_routes: SettingsRoutes


@lru_cache(maxsize=1)
def get_pwb01_runtime() -> PWB01Runtime:
    conn = init_db(PWB01_DB_PATH)
    repositories = PolymarketBotRepositories(conn)
    risk_manager = RiskManager(RiskRules())
    settings_routes = SettingsRoutes(repositories=repositories, risk_manager=risk_manager)
    strategy_runner = StrategyRunner(
        market_source=MockMarketSource(),
        strategies=[
            WeatherEdgeStrategy(PlaceholderProbabilityProvider(), min_edge_percent=10.0),
        ],
        risk_manager=risk_manager,
        repositories=repositories,
    )
    opportunity_routes = OpportunityRoutes(repositories=repositories, strategy_runner=strategy_runner)
    history_routes = HistoryRoutes(repositories=repositories)
    simulator = Simulator(repositories=repositories)
    command_routes = CommandRoutes(
        repositories=repositories,
        opportunity_routes=opportunity_routes,
        simulator=simulator,
        settings_routes=settings_routes,
    )
    return PWB01Runtime(
        repositories=repositories,
        opportunity_routes=opportunity_routes,
        command_routes=command_routes,
        history_routes=history_routes,
        settings_routes=settings_routes,
    )
