from __future__ import annotations

from dataclasses import dataclass
from statistics import fmean
from typing import Sequence

from .features import compute_features
from .models import Candle, MarketState, OutcomeProbabilities
from .probability import estimate_outcome_probabilities
from .state_engine import classify_market_state


@dataclass(frozen=True)
class ReplayRecord:
    symbol: str
    timeframe: str
    index: int
    state: MarketState
    confidence: float
    probabilities: OutcomeProbabilities
    entry_price: float
    exit_price: float
    forward_return: float
    observed_outcome: str
    brier_score: float


@dataclass(frozen=True)
class ReplaySummary:
    records: int
    bull_rate: float
    base_rate: float
    bear_rate: float
    mean_brier_score: float
    mean_forward_return: float


def _outcome(forward_return: float, threshold: float) -> str:
    if forward_return >= threshold:
        return "bull"
    if forward_return <= -threshold:
        return "bear"
    return "base"


def _brier(probabilities: OutcomeProbabilities, observed: str) -> float:
    predicted = {
        "bull": probabilities.bull,
        "base": probabilities.base,
        "bear": probabilities.bear,
    }
    return sum((probability - (1.0 if key == observed else 0.0)) ** 2 for key, probability in predicted.items())


def walk_forward_replay(
    candles: Sequence[Candle],
    *,
    horizon_bars: int = 24,
    warmup_bars: int = 120,
    outcome_threshold: float = 0.02,
) -> list[ReplayRecord]:
    """Replay AARS decisions without look-ahead.

    Features at index i only see candles <= i. The observed label is computed
    from i to i+horizon_bars and is never fed back into the current prediction.
    """
    if horizon_bars <= 0:
        raise ValueError("horizon_bars must be positive")
    if warmup_bars < 60:
        raise ValueError("warmup_bars must be at least 60")
    if outcome_threshold <= 0:
        raise ValueError("outcome_threshold must be positive")
    if len(candles) < warmup_bars + horizon_bars + 1:
        return []

    records: list[ReplayRecord] = []
    final_index = len(candles) - horizon_bars
    for i in range(warmup_bars - 1, final_index):
        window = candles[: i + 1]
        features = compute_features(window)
        assessment = classify_market_state(features)
        probabilities = estimate_outcome_probabilities(assessment, horizon_bars=horizon_bars)
        entry = candles[i].close
        exit_price = candles[i + horizon_bars].close
        forward_return = exit_price / entry - 1.0
        observed = _outcome(forward_return, outcome_threshold)
        records.append(
            ReplayRecord(
                symbol=candles[i].symbol,
                timeframe=candles[i].timeframe,
                index=i,
                state=assessment.state,
                confidence=assessment.confidence,
                probabilities=probabilities,
                entry_price=entry,
                exit_price=exit_price,
                forward_return=forward_return,
                observed_outcome=observed,
                brier_score=_brier(probabilities, observed),
            )
        )
    return records


def summarize_replay(records: Sequence[ReplayRecord]) -> ReplaySummary:
    if not records:
        return ReplaySummary(0, 0.0, 0.0, 0.0, 0.0, 0.0)
    n = len(records)
    return ReplaySummary(
        records=n,
        bull_rate=sum(r.observed_outcome == "bull" for r in records) / n,
        base_rate=sum(r.observed_outcome == "base" for r in records) / n,
        bear_rate=sum(r.observed_outcome == "bear" for r in records) / n,
        mean_brier_score=fmean(r.brier_score for r in records),
        mean_forward_return=fmean(r.forward_return for r in records),
    )
