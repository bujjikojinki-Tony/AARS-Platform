from weather_execution_gateway.execution.planner import ExecutionPlanner
from weather_execution_gateway.models.order_intent import OrderIntent
from weather_execution_gateway.models.risk_state import RiskState


def test_planner_blocks_when_risk_reason_present():
    planner = ExecutionPlanner()
    intent = OrderIntent(
        schema_version="execution_intent.v1",
        intent_id="i1",
        market_id="sample_market_001",
        signal_id="sig_i1",
        decision_ref="decision_i1",
        authorization_ref="approval_i1",
        side="buy",
        price=0.4,
        size=10,
        approved=True,
    )

    risk_state = RiskState(
        market_allowed=False,
        approval_present=True,
        kill_switch_active=False,
        notional_allowed=False,
        execution_enabled=False,
        reason="market_not_whitelisted",
    )

    result = planner.plan(intent, risk_state, mode="dry_run")
    assert result.accepted is False
    assert result.status == "blocked"


def test_planner_accepts_when_no_risk_reason():
    planner = ExecutionPlanner()
    intent = OrderIntent(
        schema_version="execution_intent.v1",
        intent_id="i2",
        market_id="sample_market_001",
        signal_id="sig_i2",
        decision_ref="decision_i2",
        authorization_ref="approval_i2",
        side="buy",
        price=0.4,
        size=10,
        approved=True,
    )

    risk_state = RiskState(
        market_allowed=True,
        approval_present=True,
        kill_switch_active=False,
        notional_allowed=True,
        execution_enabled=True,
        reason=None,
    )

    result = planner.plan(intent, risk_state, mode="dry_run")
    assert result.accepted is True
    assert result.status == "planned"
