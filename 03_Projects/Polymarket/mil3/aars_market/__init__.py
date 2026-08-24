"""AARS MIL-3 market intelligence primitives."""

from .models import Candle, FeatureSnapshot, MarketStateAssessment, OutcomeProbabilities
from .features import compute_features
from .state_engine import classify_market_state
from .probability import estimate_outcome_probabilities
from .simulation import (
    EXECUTION_MODE,
    AarsDynamicStrategy,
    BuyAndHoldStrategy,
    LeveragedFuturesLongGridStrategy,
    ReplayEngine,
    SpotGridStrategy,
    compare_shadow_strategies,
)

__all__ = [
    "Candle",
    "FeatureSnapshot",
    "MarketStateAssessment",
    "OutcomeProbabilities",
    "compute_features",
    "classify_market_state",
    "estimate_outcome_probabilities",
    "EXECUTION_MODE",
    "ReplayEngine",
    "BuyAndHoldStrategy",
    "SpotGridStrategy",
    "LeveragedFuturesLongGridStrategy",
    "AarsDynamicStrategy",
    "compare_shadow_strategies",
]
