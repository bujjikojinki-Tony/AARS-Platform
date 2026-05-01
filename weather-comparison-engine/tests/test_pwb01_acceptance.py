from __future__ import annotations

from weather_comparison_engine.polymarket_bot import CommandRoutes
from weather_comparison_engine.polymarket_bot import HistoryRoutes
from weather_comparison_engine.polymarket_bot import MockMarketSource
from weather_comparison_engine.polymarket_bot import OpportunityCandidate
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
from weather_comparison_engine.polymarket_bot.models import ExecutionDecision


def _build_acceptance_runtime(tmp_path):
    conn = init_db(tmp_path / "pwb01_acceptance.sqlite")
    repositories = PolymarketBotRepositories(conn)
    risk_manager = RiskManager(RiskRules(min_edge_percent=10.0, min_liquidity=100.0, max_spread=0.08))
    settings_routes = SettingsRoutes(repositories=repositories, risk_manager=risk_manager)
    strategy_runner = StrategyRunner(
        market_source=MockMarketSource(),
        strategies=[WeatherEdgeStrategy(PlaceholderProbabilityProvider(), min_edge_percent=10.0)],
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
    return repositories, risk_manager, settings_routes, opportunity_routes, history_routes, simulator, command_routes


def test_scan_creates_candidate(tmp_path) -> None:
    repositories, _, _, opportunity_routes, _, _, _ = _build_acceptance_runtime(tmp_path)

    response = opportunity_routes.post_scan()

    assert response["ok"] is True
    assert response["candidate_count"] >= 1
    assert len(repositories.strategy_signals.list_all()) >= 1
    assert len(repositories.opportunity_candidates.list_all()) >= 1


def test_risk_gate_blocks_weak_candidate() -> None:
    manager = RiskManager(RiskRules(min_edge_percent=10.0, min_liquidity=100.0, max_spread=0.08))
    weak_candidate = OpportunityCandidate(
        candidate_id="cand-weak",
        signal_id="sig-weak",
        market_id="m-weak",
        question="weak edge",
        side="YES",
        market_probability=0.48,
        model_probability=0.53,
        edge_percent=5.0,
        z_score=None,
        liquidity=500.0,
        spread=0.02,
        confidence_tier="LOW",
        risk_status="WARN",
        action_status="WATCH",
        created_at="2026-04-28T10:00:00Z",
    )

    result = manager.evaluate(weak_candidate, checked_at="2026-04-28T10:01:00Z")

    assert result.status == "BLOCK"
    assert "edge_below_threshold" in result.reasons


def test_simulation_does_not_trade_live(tmp_path) -> None:
    repositories, _, _, _, _, simulator, _ = _build_acceptance_runtime(tmp_path)
    candidate = OpportunityCandidate(
        candidate_id="cand-1",
        signal_id="sig-1",
        market_id="m1",
        question="simulate",
        side="YES",
        market_probability=0.41,
        model_probability=0.56,
        edge_percent=15.0,
        z_score=1.5,
        liquidity=1000.0,
        spread=0.03,
        confidence_tier="MEDIUM",
        risk_status="PASS",
        action_status="SIMULATE",
        created_at="2026-04-28T10:01:00Z",
    )
    decision = ExecutionDecision(
        decision_id="dec-1",
        candidate_id="cand-1",
        mode="SIMULATION",
        action="BUY_YES",
        requested_by="operator_local",
        approved_by=None,
        approval_required=False,
        approval_status="NOT_REQUIRED",
        position_size=25.0,
        expected_cost=10.25,
        risk_status="PASS",
        execution_status="QUEUED",
        created_at="2026-04-28T10:02:00Z",
        executed_at=None,
    )
    calls = {"live": 0}

    def fake_live_executor(*args, **kwargs):
        calls["live"] += 1
        raise AssertionError("live executor should not be called")

    result = simulator.simulate(decision, candidate, live_executor=fake_live_executor)

    assert result.result_status == "COMPLETED"
    assert calls["live"] == 0
    assert repositories.simulation_results.list_all()[0].simulation_id == result.simulation_id


def test_mode_defaults_to_observe_only(tmp_path) -> None:
    _, _, settings_routes, _, _, _, _ = _build_acceptance_runtime(tmp_path)

    mode = settings_routes.get_mode()

    assert mode == {"ok": True, "mode": "OBSERVE_ONLY"}


def test_command_is_audited(tmp_path) -> None:
    repositories, _, _, _, history_routes, _, command_routes = _build_acceptance_runtime(tmp_path)

    result = command_routes.post_command("/run scan")

    assert result["ok"] is True
    audit_rows = repositories.audit_logs.list_all()
    assert any(row.event_type == "COMMAND_EXECUTED" for row in audit_rows)
    audit_payloads = history_routes.get_audit()["items"]
    command_events = [item for item in audit_payloads if item["event_type"] == "COMMAND_EXECUTED"]
    assert command_events
    assert "/run scan" in command_events[0]["payload_json"]
