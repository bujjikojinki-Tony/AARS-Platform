from __future__ import annotations

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


def _build_runtime(tmp_path):
    conn = init_db(tmp_path / "phase_c.sqlite")
    repos = PolymarketBotRepositories(conn)
    risk_manager = RiskManager(RiskRules(min_edge_percent=10.0, min_liquidity=100.0, max_spread=0.08))
    settings_routes = SettingsRoutes(repositories=repos, risk_manager=risk_manager)
    runner = StrategyRunner(
        market_source=MockMarketSource(),
        strategies=[WeatherEdgeStrategy(PlaceholderProbabilityProvider(), min_edge_percent=10.0)],
        risk_manager=risk_manager,
        repositories=repos,
    )
    opportunity_routes = OpportunityRoutes(repositories=repos, strategy_runner=runner)
    history_routes = HistoryRoutes(repositories=repos)
    simulator = Simulator(repositories=repos)
    command_routes = CommandRoutes(
        repositories=repos,
        opportunity_routes=opportunity_routes,
        simulator=simulator,
        settings_routes=settings_routes,
    )
    return repos, settings_routes, opportunity_routes, history_routes, command_routes


def test_post_scan_and_get_opportunities_work(tmp_path) -> None:
    _, _, opportunity_routes, _, _ = _build_runtime(tmp_path)

    scan_response = opportunity_routes.post_scan()
    list_response = opportunity_routes.get_opportunities()

    assert scan_response["ok"] is True
    assert scan_response["candidate_count"] >= 1
    assert list_response["ok"] is True
    assert list_response["count"] >= 1


def test_command_routes_support_required_commands(tmp_path) -> None:
    _, settings_routes, _, _, command_routes = _build_runtime(tmp_path)

    scan_response = command_routes.post_command("/run scan")
    candidate_id = scan_response["candidates"][0]["candidate_id"]
    rules_response = command_routes.post_command("/show rules")
    mode_response = command_routes.post_command("/set mode simulation")
    simulate_response = command_routes.post_command(f"/simulate {candidate_id}")

    assert scan_response["ok"] is True
    assert rules_response["ok"] is True
    assert "min_edge_percent" in rules_response["rules"]
    assert mode_response == {"ok": True, "mode": "SIMULATION"}
    assert settings_routes.get_mode()["mode"] == "SIMULATION"
    assert simulate_response["ok"] is True
    assert simulate_response["simulation"]["result_status"] == "COMPLETED"


def test_history_endpoints_return_persisted_data(tmp_path) -> None:
    _, _, _, history_routes, command_routes = _build_runtime(tmp_path)

    scan_response = command_routes.post_command("/run scan")
    candidate_id = scan_response["candidates"][0]["candidate_id"]
    command_routes.post_command(f"/simulate {candidate_id}")

    signals = history_routes.get_signals()
    candidates = history_routes.get_candidates()
    simulations = history_routes.get_simulations()
    audit = history_routes.get_audit()

    assert signals["count"] >= 1
    assert candidates["count"] >= 1
    assert simulations["count"] >= 1
    assert audit["count"] >= 2


def test_settings_endpoints_return_and_update_rules(tmp_path) -> None:
    _, settings_routes, _, _, _ = _build_runtime(tmp_path)

    before = settings_routes.get_rules()
    after = settings_routes.post_rules({"min_edge_percent": 12.5, "max_spread": 0.05})

    assert before["ok"] is True
    assert after["ok"] is True
    assert after["rules"]["min_edge_percent"] == 12.5
    assert after["rules"]["max_spread"] == 0.05


def test_command_rejects_live_and_auto_trade_commands(tmp_path) -> None:
    _, _, _, _, command_routes = _build_runtime(tmp_path)

    live_response = command_routes.post_command("/live execute cand-1")
    auto_response = command_routes.post_command("/auto trade on")

    assert live_response["ok"] is False
    assert auto_response["ok"] is False
