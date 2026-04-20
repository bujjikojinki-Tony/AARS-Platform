from aars_weather_trading.gates.compact_gate_stack import build_compact_gate_stack
from aars_weather_trading.gates.freshness_gate import evaluate_freshness_gate
from aars_weather_trading.gates.gate_result import GateResult
from aars_weather_trading.gates.probability_gate import evaluate_probability_gate
from aars_weather_trading.gates.resolver_gate import evaluate_resolver_gate


def test_probability_gate_blocks_heuristic_mode() -> None:
    result = evaluate_probability_gate("heuristic_not_calibrated")
    assert result.passed is False
    assert result.execution_constraint == "manual_advisory_only"
    assert "probability_not_calibrated" in result.block_reasons


def test_freshness_gate_blocks_stale_worker() -> None:
    result = evaluate_freshness_gate(
        {
            "overall_status": "warning",
            "monitoring": {
                "workers": [
                    {"label": "market_worker", "status": "healthy"},
                    {"label": "forecast_worker", "status": "stale"},
                ]
            },
        }
    )
    assert result.passed is False
    assert result.block_reasons == ["stale_worker"]


def test_compact_gate_stack_aggregates_reasons() -> None:
    stack = build_compact_gate_stack(
        data_gate=GateResult(passed=True, status="pass", block_reasons=[]),
        probability_gate=GateResult(
            passed=False,
            status="blocked",
            block_reasons=["probability_not_calibrated"],
        ),
        authorization_gate=GateResult(passed=True, status="pass", block_reasons=[]),
        execution_gate=GateResult(
            passed=False,
            status="blocked",
            block_reasons=["execution_intent_contract_invalid"],
        ),
    )
    assert stack["probability_gate"] == "blocked"
    assert stack["resolver_gate"] == "pass"
    assert stack["execution_gate"] == "blocked"
    assert stack["block_reasons"] == [
        "probability_not_calibrated",
        "execution_intent_contract_invalid",
    ]


def test_resolver_gate_blocks_unmatched_family_only_low_confidence() -> None:
    result = evaluate_resolver_gate(
        resolver_status="unmatched",
        resolver_confidence=0.45,
        source_match_grade="family_only",
    )
    assert result.passed is False
    assert result.block_reasons == [
        "resolver_not_matched",
        "resolver_confidence_low",
        "resolver_source_not_exact",
    ]
