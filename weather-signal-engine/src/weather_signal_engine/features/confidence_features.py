def confidence_from_components(
    parse_confidence: float,
    has_market_context: bool,
    run_to_run_delta: float | None,
) -> tuple[float, list[str]]:
    score = parse_confidence
    reasons: list[str] = []

    if has_market_context:
        score += 0.2
        reasons.append("market_context_available")

    if run_to_run_delta is not None and abs(run_to_run_delta) < 0.8:
        score += 0.1
        reasons.append("forecast_stable")

    return min(score, 0.99), reasons
