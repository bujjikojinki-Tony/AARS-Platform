from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class MarketState(str, Enum):
    ACCUMULATION = "ACCUMULATION"
    RECOVERY = "RECOVERY"
    RANGE = "RANGE"
    BREAKOUT = "BREAKOUT"
    TREND_EXPANSION = "TREND_EXPANSION"
    DISTRIBUTION = "DISTRIBUTION"
    BREAKDOWN = "BREAKDOWN"


@dataclass(frozen=True)
class Candle:
    symbol: str
    timeframe: str
    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class FeatureSnapshot:
    symbol: str
    timeframe: str
    as_of: datetime
    close: float
    ema5: float
    ema10: float
    ema20: float
    ema30: float
    ema60: float
    rsi14: float
    atr14: float
    boll_mid: float
    boll_upper: float
    boll_lower: float
    volume_ratio20: float


@dataclass(frozen=True)
class MarketStateAssessment:
    state: MarketState
    confidence: float
    evidence: tuple[str, ...]
    counter_evidence: tuple[str, ...]


@dataclass(frozen=True)
class OutcomeProbabilities:
    bull: float
    base: float
    bear: float
    horizon_bars: int

    def __post_init__(self) -> None:
        total = self.bull + self.base + self.bear
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"probabilities must sum to 1.0, got {total}")
        if min(self.bull, self.base, self.bear) < 0:
            raise ValueError("probabilities must be non-negative")
