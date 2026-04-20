def estimate_model_vs_market_edge(model_band: str | None, market_band: str | None) -> tuple[str | None, float]:
    if model_band is None or market_band is None:
        return None, 0.0

    if model_band == market_band:
        return "neutral", 0.0

    return "divergent", 1.0
