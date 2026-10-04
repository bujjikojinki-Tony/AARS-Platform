from __future__ import annotations

from dataclasses import dataclass

from .models import MarketState, MarketStateAssessment, OutcomeProbabilities


@dataclass(frozen=True)
class ExposureDecision:
    target_exposure: float
    reason: str


def decide_target_exposure(
    assessment: MarketStateAssessment,
    probabilities: OutcomeProbabilities,
    *,
    max_abs_exposure: float = 1.0,
) -> ExposureDecision:
    """Translate state + probability evidence into a bounded paper exposure.

    This is a transparent baseline policy, not an optimized trading strategy.
    The probability edge modulates a state prior and never bypasses the cap.
    """
    if max_abs_exposure <= 0:
        raise ValueError("max_abs_exposure must be positive")

    state_prior = {
        MarketState.ACCUMULATION: 0.20,
        MarketState.RECOVERY: 0.35,
        MarketState.RANGE: 0.00,
        MarketState.BREAKOUT: 0.70,
        MarketState.TREND_EXPANSION: 0.60,
        MarketState.DISTRIBUTION: -0.15,
        MarketState.BREAKDOWN: -0.45,
    }[assessment.state]

    directional_edge = probabilities.bull - probabilities.bear
    raw = state_prior + 0.50 * directional_edge
    confidence_scaled = raw * (0.5 + 0.5 * assessment.confidence)
    target = max(-max_abs_exposure, min(max_abs_exposure, confidence_scaled))

    return ExposureDecision(
        target_exposure=target,
        reason=(
            f"state={assessment.state.value}; state_prior={state_prior:.2f}; "
            f"bull={probabilities.bull:.3f}; bear={probabilities.bear:.3f}; "
            f"confidence={assessment.confidence:.2f}"
        ),
    )
