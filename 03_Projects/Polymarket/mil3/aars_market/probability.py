from __future__ import annotations

from .models import MarketState, MarketStateAssessment, OutcomeProbabilities


_PRIORS: dict[MarketState, tuple[float, float, float]] = {
    MarketState.ACCUMULATION: (0.40, 0.42, 0.18),
    MarketState.RECOVERY: (0.48, 0.37, 0.15),
    MarketState.RANGE: (0.30, 0.50, 0.20),
    MarketState.BREAKOUT: (0.58, 0.29, 0.13),
    MarketState.TREND_EXPANSION: (0.55, 0.31, 0.14),
    MarketState.DISTRIBUTION: (0.20, 0.42, 0.38),
    MarketState.BREAKDOWN: (0.13, 0.27, 0.60),
}


def estimate_outcome_probabilities(
    assessment: MarketStateAssessment,
    horizon_bars: int = 24,
) -> OutcomeProbabilities:
    """Return an explicit baseline prior to be calibrated by walk-forward data.

    Confidence shrinks the state prior toward a neutral 30/50/20 distribution.
    This is intentionally not presented as a trained forecasting model.
    """
    if horizon_bars <= 0:
        raise ValueError("horizon_bars must be positive")
    prior = _PRIORS[assessment.state]
    neutral = (0.30, 0.50, 0.20)
    w = assessment.confidence
    raw = tuple(w * p + (1.0 - w) * n for p, n in zip(prior, neutral))
    total = sum(raw)
    bull, base, bear = (x / total for x in raw)
    return OutcomeProbabilities(bull=bull, base=base, bear=bear, horizon_bars=horizon_bars)
