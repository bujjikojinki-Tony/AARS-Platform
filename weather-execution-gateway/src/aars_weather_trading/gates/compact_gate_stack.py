from aars_weather_trading.gates.gate_result import GateResult


def build_compact_gate_stack(
    *,
    data_gate: GateResult,
    probability_gate: GateResult,
    resolver_gate: GateResult | None = None,
    authorization_gate: GateResult,
    execution_gate: GateResult,
) -> dict:
    resolved_resolver_gate = resolver_gate or GateResult(passed=True, status="pass", block_reasons=[])
    block_reasons: list[str] = []
    for gate in (
        data_gate,
        probability_gate,
        resolved_resolver_gate,
        authorization_gate,
        execution_gate,
    ):
        for reason in gate.block_reasons:
            if reason not in block_reasons:
                block_reasons.append(reason)
    return {
        "data_gate": data_gate.status,
        "probability_gate": probability_gate.status,
        "resolver_gate": resolved_resolver_gate.status,
        "authorization_gate": authorization_gate.status,
        "execution_gate": execution_gate.status,
        "block_reasons": block_reasons,
    }
