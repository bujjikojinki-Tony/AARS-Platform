"""AARS MIL-3 market intelligence primitives."""

from .models import Candle, FeatureSnapshot, MarketStateAssessment, OutcomeProbabilities
from .features import compute_features
from .state_engine import classify_market_state
from .probability import estimate_outcome_probabilities
from .dashboard import DASHBOARD_SCHEMA_VERSION, build_dashboard_payload, write_dashboard_payload
from .simulation import (
    EXECUTION_MODE,
    AarsDeadbandStrategy,
    AarsDynamicStrategy,
    BuyAndHoldStrategy,
    LeveragedFuturesLongGridStrategy,
    ReplayResult,
    ReplayEngine,
    SpotGridStrategy,
    compare_shadow_strategies,
    compare_shadow_strategy_results,
)

__all__ = [
    "Candle",
    "FeatureSnapshot",
    "MarketStateAssessment",
    "OutcomeProbabilities",
    "compute_features",
    "classify_market_state",
    "estimate_outcome_probabilities",
    "DASHBOARD_SCHEMA_VERSION",
    "build_dashboard_payload",
    "write_dashboard_payload",
    "EXECUTION_MODE",
    "ReplayEngine",
    "ReplayResult",
    "BuyAndHoldStrategy",
    "SpotGridStrategy",
    "LeveragedFuturesLongGridStrategy",
    "AarsDynamicStrategy",
    "AarsDeadbandStrategy",
    "compare_shadow_strategies",
    "compare_shadow_strategy_results",
]
