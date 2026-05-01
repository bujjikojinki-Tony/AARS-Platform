from __future__ import annotations

from weather_comparison_engine.polymarket_bot import ExecutionDecision
from weather_comparison_engine.polymarket_bot import MockMarketSource
from weather_comparison_engine.polymarket_bot import OpportunityCandidate
from weather_comparison_engine.polymarket_bot import PlaceholderProbabilityProvider
from weather_comparison_engine.polymarket_bot import PolymarketBotRepositories
from weather_comparison_engine.polymarket_bot import RiskManager
from weather_comparison_engine.polymarket_bot import RiskRules
from weather_comparison_engine.polymarket_bot import Simulator
from weather_comparison_engine.polymarket_bot import StrategyRunner
from weather_comparison_engine.polymarket_bot import WeatherEdgeStrategy
from weather_comparison_engine.polymarket_bot import init_db


def test_run_once_creates_snapshots_signals_candidates_and_audit_logs(tmp_path) -> None:
    conn = init_db(tmp_path / "phase_b.sqlite")
    repos = PolymarketBotRepositories(conn)
    runner = StrategyRunner(
        market_source=MockMarketSource(),
        strategies=[WeatherEdgeStrategy(PlaceholderProbabilityProvider(), min_edge_percent=10.0)],
        risk_manager=RiskManager(RiskRules(min_edge_percent=10.0, min_liquidity=100.0, max_spread=0.08)),
        repositories=repos,
    )

    candidates = runner.run_once()

    assert len(repos.market_snapshots.list_all()) >= 5
    assert len(repos.strategy_signals.list_all()) >= 1
    assert len(repos.opportunity_candidates.list_all()) >= 1
    assert len(repos.audit_logs.list_all()) >= 1
    assert len(candidates) >= 1
    assert all(candidate.signal_id for candidate in candidates)


def test_risk_manager_blocks_weak_low_liquidity_and_high_spread_candidates() -> None:
    manager = RiskManager(RiskRules(min_edge_percent=10.0, min_liquidity=100.0, max_spread=0.08))

    weak_candidate = OpportunityCandidate(
        candidate_id="cand-weak",
        signal_id="sig-weak",
        market_id="m-weak",
        question="weak edge",
        side="YES",
        market_probability=0.45,
        model_probability=0.50,
        edge_percent=5.0,
        z_score=None,
        liquidity=500.0,
        spread=0.02,
        confidence_tier="LOW",
        risk_status="WARN",
        action_status="WATCH",
        created_at="2026-04-28T10:00:00Z",
    )
    low_liquidity_candidate = OpportunityCandidate(
        candidate_id="cand-liq",
        signal_id="sig-liq",
        market_id="m-liq",
        question="low liquidity",
        side="YES",
        market_probability=0.40,
        model_probability=0.55,
        edge_percent=15.0,
        z_score=None,
        liquidity=80.0,
        spread=0.02,
        confidence_tier="LOW",
        risk_status="WARN",
        action_status="WATCH",
        created_at="2026-04-28T10:00:00Z",
    )
    high_spread_candidate = OpportunityCandidate(
        candidate_id="cand-spread",
        signal_id="sig-spread",
        market_id="m-spread",
        question="high spread",
        side="NO",
        market_probability=0.60,
        model_probability=0.45,
        edge_percent=-15.0,
        z_score=None,
        liquidity=500.0,
        spread=0.12,
        confidence_tier="LOW",
        risk_status="WARN",
        action_status="WATCH",
        created_at="2026-04-28T10:00:00Z",
    )

    assert manager.evaluate(weak_candidate, checked_at="2026-04-28T10:01:00Z").status == "BLOCK"
    assert manager.evaluate(low_liquidity_candidate, checked_at="2026-04-28T10:01:00Z").status == "BLOCK"
    assert manager.evaluate(high_spread_candidate, checked_at="2026-04-28T10:01:00Z").status == "BLOCK"


def test_simulator_creates_result_and_never_calls_live_execution(tmp_path) -> None:
    conn = init_db(tmp_path / "simulate.sqlite")
    repos = PolymarketBotRepositories(conn)
    simulator = Simulator(repositories=repos)

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
    live_call_count = {"count": 0}

    def fake_live_executor(*args, **kwargs):
        live_call_count["count"] += 1
        raise AssertionError("live executor should not be called")

    result = simulator.simulate(decision, candidate, live_executor=fake_live_executor)

    assert result.result_status == "COMPLETED"
    assert repos.simulation_results.list_all()[0].decision_id == "dec-1"
    assert repos.audit_logs.list_all()[0].event_type == "SIMULATION_CREATED"
    assert live_call_count["count"] == 0
