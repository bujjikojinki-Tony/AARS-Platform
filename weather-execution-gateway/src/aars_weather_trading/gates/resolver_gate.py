from aars_weather_trading.gates.gate_result import GateResult


def evaluate_resolver_gate(
    *,
    resolver_status: str | None,
    resolver_confidence: float | None = None,
    source_match_grade: str | None = None,
    min_confidence: float = 0.7,
) -> GateResult:
    status = str(resolver_status or "").strip().lower()
    confidence = float(resolver_confidence or 0.0)
    source_grade = str(source_match_grade or "").strip().lower()

    reasons: list[str] = []
    if status != "matched":
        reasons.append("resolver_not_matched")
    if confidence < float(min_confidence):
        reasons.append("resolver_confidence_low")
    if source_grade in {"", "unmatched", "family_only"}:
        reasons.append("resolver_source_not_exact")

    if reasons:
        return GateResult(passed=False, status="blocked", block_reasons=reasons)
    return GateResult(passed=True, status="pass", block_reasons=[])

