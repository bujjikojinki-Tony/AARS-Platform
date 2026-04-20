from aars_weather_trading.gates.gate_result import GateResult


def evaluate_probability_gate(probability_mode: str) -> GateResult:
    mode = str(probability_mode or "").strip()
    if mode == "heuristic_not_calibrated":
        return GateResult(
            passed=False,
            status="blocked",
            block_reasons=["probability_not_calibrated"],
            execution_constraint="manual_advisory_only",
        )
    if mode == "shadow_calibrated_candidate":
        return GateResult(
            passed=False,
            status="blocked",
            block_reasons=["shadow_only"],
            execution_constraint="dry_run_only",
        )
    if mode == "live_approved":
        return GateResult(
            passed=True,
            status="pass",
            block_reasons=[],
            execution_constraint="live_execution_allowed",
        )
    return GateResult(
        passed=False,
        status="blocked",
        block_reasons=["unknown_probability_mode"],
        execution_constraint="manual_advisory_only",
    )

