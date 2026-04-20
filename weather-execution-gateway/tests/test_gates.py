from weather_execution_gateway.models.order_intent import OrderIntent
from weather_execution_gateway.risk.exposure_limits import ExposureLimits
from weather_execution_gateway.risk.gates import RiskGateEngine
from weather_execution_gateway.risk.kill_switch import KillSwitch


def _build_intent(intent_id: str, **overrides) -> OrderIntent:
    payload = {
        "schema_version": "execution_intent.v1",
        "intent_id": intent_id,
        "market_id": "sample_market_001",
        "signal_id": f"sig_{intent_id}",
        "decision_ref": f"decision_{intent_id}",
        "authorization_ref": f"approval_{intent_id}",
        "side": "buy",
        "price": 0.4,
        "size": 10,
        "approved": True,
    }
    payload.update(overrides)
    return OrderIntent(**payload)


def test_gate_blocks_unapproved_order():
    gate = RiskGateEngine(
        whitelist_markets={"sample_market_001"},
        execution_enabled=False,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=100,
            max_total_notional=500,
        ),
    )

    intent = _build_intent("i1", approved=False)

    risk = gate.evaluate(intent, approval_valid=False)
    assert risk.reason == "approval_invalid_or_expired"


def test_gate_allows_dry_run_when_approved_and_whitelisted():
    gate = RiskGateEngine(
        whitelist_markets={"sample_market_001"},
        execution_enabled=False,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=100,
            max_total_notional=500,
        ),
    )

    intent = _build_intent("i2")

    risk = gate.evaluate(intent, approval_valid=True)
    assert risk.reason == "execution_disabled_dry_run_only"


def test_gate_blocks_when_approval_invalid():
    gate = RiskGateEngine(
        whitelist_markets={"sample_market_001"},
        execution_enabled=False,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=100,
            max_total_notional=500,
        ),
    )

    intent = _build_intent("i3")

    risk = gate.evaluate(intent, approval_valid=False)
    assert risk.reason == "approval_invalid_or_expired"


def test_gate_blocks_live_execution_when_probability_contract_is_not_live():
    gate = RiskGateEngine(
        whitelist_markets={"sample_market_001"},
        execution_enabled=True,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=100,
            max_total_notional=500,
        ),
    )

    intent = _build_intent(
        "i4",
        probability_contract={
            "contract_version": "probability_contract.v1",
            "probability_mode": "heuristic_not_calibrated",
            "calibration_status": "not_calibrated",
            "execution_constraint": "manual_advisory_only",
        },
    )

    risk = gate.evaluate(intent, approval_valid=True)

    assert risk.reason == "probability_contract_blocks_live_execution"


def test_gate_allows_live_execution_when_probability_contract_is_live_approved():
    gate = RiskGateEngine(
        whitelist_markets={"sample_market_001"},
        execution_enabled=True,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=100,
            max_total_notional=500,
        ),
    )

    intent = _build_intent(
        "i5",
        probability_contract={
            "contract_version": "probability_contract.v1",
            "probability_mode": "live_approved",
            "calibration_status": "calibrated",
            "execution_constraint": "live_execution_allowed",
        },
    )

    risk = gate.evaluate(intent, approval_valid=True)

    assert risk.reason is None


def test_gate_blocks_when_unified_status_overall_is_degraded():
    gate = RiskGateEngine(
        whitelist_markets={"sample_market_001"},
        execution_enabled=False,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=100,
            max_total_notional=500,
        ),
    )

    intent = _build_intent("i6")

    risk = gate.evaluate(
        intent,
        approval_valid=True,
        unified_status={
            "schema_version": "unified_status.v1",
            "overall_status": "degraded",
        },
    )

    assert risk.reason == "unified_status_degraded"


def test_gate_blocks_when_any_worker_is_stale():
    gate = RiskGateEngine(
        whitelist_markets={"sample_market_001"},
        execution_enabled=False,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=100,
            max_total_notional=500,
        ),
    )

    intent = _build_intent("i7")

    risk = gate.evaluate(
        intent,
        approval_valid=True,
        unified_status={
            "schema_version": "unified_status.v1",
            "overall_status": "warning",
            "monitoring": {
                "workers": [
                    {"label": "market_worker", "status": "healthy"},
                    {"label": "forecast_worker", "status": "stale"},
                ]
            },
        },
    )

    assert risk.reason == "stale_worker"


def test_gate_blocks_when_execution_intent_contract_is_incomplete():
    gate = RiskGateEngine(
        whitelist_markets={"sample_market_001"},
        execution_enabled=False,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=100,
            max_total_notional=500,
        ),
    )

    intent = _build_intent("i8", decision_ref=None)

    risk = gate.evaluate(intent, approval_valid=True)

    assert risk.reason == "execution_intent_contract_invalid"


def test_gate_prefers_unified_gate_stack_contract_when_present():
    gate = RiskGateEngine(
        whitelist_markets={"sample_market_001"},
        execution_enabled=False,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=100,
            max_total_notional=500,
        ),
    )

    intent = _build_intent("i9")
    risk = gate.evaluate(
        intent,
        approval_valid=True,
        unified_status={
            "schema_version": "unified_status.v1",
            "gate_stack": {
                "authorization_gate": "blocked",
                "authorization_gate_reasons": ["resolver_not_matched"],
                "resolver_gate": "blocked",
                "resolver_gate_reasons": ["resolver_not_matched"],
                "probability_gate": "blocked",
                "probability_gate_reasons": ["probability_not_live_approved"],
            },
            "monitoring": {
                "workers": [{"label": "forecast_worker", "status": "healthy"}],
            },
            "overall_status": "healthy",
        },
    )
    assert risk.reason == "resolver_not_matched"


def test_gate_skips_unified_freshness_when_gate_source_is_api():
    gate = RiskGateEngine(
        whitelist_markets={"sample_market_001"},
        execution_enabled=False,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=100,
            max_total_notional=500,
        ),
    )

    intent = _build_intent("i10")
    risk = gate.evaluate(
        intent,
        approval_valid=True,
        unified_status={
            "schema_version": "unified_status.v1",
            "overall_status": "degraded",
            "contracts": {"gate_source": "api"},
            "gate_stack": {
                "data_gate": "pass",
                "resolver_gate": "pass",
                "probability_gate": "pass",
                "freshness_gate": "pass",
                "authorization_gate": "pass",
                "execution_gate": "pass",
                "block_reasons": [],
            },
            "monitoring": {
                "workers": [{"label": "forecast_worker", "status": "stale"}],
            },
        },
    )
    assert risk.reason == "execution_disabled_dry_run_only"
