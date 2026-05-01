from __future__ import annotations

from weather_comparison_engine.polymarket_bot import AuditLog
from weather_comparison_engine.polymarket_bot import ExecutionDecision
from weather_comparison_engine.polymarket_bot import MarketSnapshot
from weather_comparison_engine.polymarket_bot import MockMarketSource
from weather_comparison_engine.polymarket_bot import OpportunityCandidate
from weather_comparison_engine.polymarket_bot import PlaceholderProbabilityProvider
from weather_comparison_engine.polymarket_bot import PolymarketBotRepositories
from weather_comparison_engine.polymarket_bot import SimulationResult
from weather_comparison_engine.polymarket_bot import StrategySignal
from weather_comparison_engine.polymarket_bot import init_db


def test_init_db_creates_phase_a_tables(tmp_path) -> None:
    db_path = tmp_path / "phase_a.sqlite"

    conn = init_db(db_path)

    table_names = {
        row["name"]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    }
    assert {
        "market_snapshots",
        "strategy_signals",
        "opportunity_candidates",
        "execution_decisions",
        "simulation_results",
        "audit_logs",
    }.issubset(table_names)


def test_repositories_can_save_and_list_core_objects(tmp_path) -> None:
    conn = init_db(tmp_path / "repos.sqlite")
    repos = PolymarketBotRepositories(conn)

    market = MarketSnapshot(
        market_id="m1",
        question="Will rainfall exceed 50mm in New York on 2026-04-29?",
        slug="new-york-rain-50mm",
        category="weather",
        yes_price=0.41,
        no_price=0.59,
        liquidity=120000.0,
        spread=0.03,
        fetched_at="2026-04-28T10:00:00Z",
    )
    signal = StrategySignal(
        signal_id="sig-1",
        market_id="m1",
        strategy_id="weather_edge_v0",
        side="YES",
        model_probability=0.55,
        market_probability=0.41,
        edge_percent=14.0,
        z_score=1.6,
        confidence="LOW",
        reason="placeholder divergence",
        created_at="2026-04-28T10:01:00Z",
    )
    candidate = OpportunityCandidate(
        candidate_id="cand-1",
        signal_id="sig-1",
        market_id="m1",
        question=market.question,
        side="YES",
        market_probability=0.41,
        model_probability=0.55,
        edge_percent=14.0,
        z_score=1.6,
        liquidity=120000.0,
        spread=0.03,
        confidence_tier="MEDIUM",
        risk_status="PASS",
        action_status="SIMULATE",
        created_at="2026-04-28T10:01:01Z",
        expires_at="2026-04-28T12:01:01Z",
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
    simulation = SimulationResult(
        simulation_id="sim-1",
        decision_id="dec-1",
        candidate_id="cand-1",
        side="YES",
        entry_price=0.41,
        position_size=25.0,
        simulated_cost=10.25,
        expected_probability=0.55,
        expected_value=3.5,
        max_loss=10.25,
        max_gain=14.75,
        result_status="CREATED",
        created_at="2026-04-28T10:03:00Z",
    )
    audit = AuditLog(
        event_id="audit-1",
        event_type="CANDIDATE_CREATED",
        object_type="OpportunityCandidate",
        object_id="cand-1",
        payload_json='{"risk_status": "PASS"}',
        created_at="2026-04-28T10:03:10Z",
    )

    repos.market_snapshots.save(market)
    repos.strategy_signals.save(signal)
    repos.opportunity_candidates.save(candidate)
    repos.execution_decisions.save(decision)
    repos.simulation_results.save(simulation)
    repos.audit_logs.save(audit)

    assert repos.market_snapshots.list_all()[0].market_id == "m1"
    assert repos.strategy_signals.list_all()[0].signal_id == "sig-1"
    assert repos.opportunity_candidates.list_all()[0].candidate_id == "cand-1"
    assert repos.execution_decisions.list_all()[0].decision_id == "dec-1"
    assert repos.simulation_results.list_all()[0].simulation_id == "sim-1"
    assert repos.audit_logs.list_all()[0].event_id == "audit-1"


def test_mock_market_source_returns_at_least_five_markets() -> None:
    markets = MockMarketSource().fetch_markets()

    assert len(markets) >= 5
    assert all(isinstance(market, MarketSnapshot) for market in markets)
    assert all(market.source == "mock" for market in markets)


def test_placeholder_probability_provider_is_deterministic() -> None:
    provider = PlaceholderProbabilityProvider()
    market = MarketSnapshot(
        market_id="m1",
        question="Will rainfall exceed 50mm in New York on 2026-04-29?",
        yes_price=0.41,
        no_price=0.59,
        liquidity=120000.0,
        spread=0.03,
        fetched_at="2026-04-28T10:00:00Z",
    )

    probability_one = provider.estimate(market)
    probability_two = provider.estimate(market)

    assert probability_one == probability_two
    assert 0.30 <= probability_one <= 0.70
