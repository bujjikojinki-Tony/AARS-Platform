from __future__ import annotations

import math
from statistics import fmean, pstdev
from typing import Sequence

from .models import Candle, FeatureSnapshot


def _ema(values: Sequence[float], period: int) -> float:
    if len(values) < period:
        raise ValueError(f"need at least {period} values")
    alpha = 2.0 / (period + 1.0)
    result = fmean(values[:period])
    for value in values[period:]:
        result = alpha * value + (1.0 - alpha) * result
    return result


def _rsi(values: Sequence[float], period: int = 14) -> float:
    if len(values) < period + 1:
        raise ValueError("insufficient values for RSI")
    deltas = [b - a for a, b in zip(values[-(period + 1):-1], values[-period:])]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]
    avg_gain = fmean(gains)
    avg_loss = fmean(losses)
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _atr(candles: Sequence[Candle], period: int = 14) -> float:
    if len(candles) < period + 1:
        raise ValueError("insufficient candles for ATR")
    window = candles[-(period + 1):]
    trs: list[float] = []
    for previous, current in zip(window[:-1], window[1:]):
        trs.append(max(
            current.high - current.low,
            abs(current.high - previous.close),
            abs(current.low - previous.close),
        ))
    return fmean(trs)


def compute_features(candles: Sequence[Candle]) -> FeatureSnapshot:
    """Compute features using only candles at or before the latest candle.

    This function is deliberately dependency-light so the first MIL-3 baseline is
    deterministic, auditable and easy to replay without a TA library.
    """
    if len(candles) < 60:
        raise ValueError("MIL-3 feature engine requires at least 60 candles")
    symbol = candles[-1].symbol
    timeframe = candles[-1].timeframe
    if any(c.symbol != symbol or c.timeframe != timeframe for c in candles):
        raise ValueError("candles must share symbol and timeframe")

    closes = [c.close for c in candles]
    volumes = [c.volume for c in candles]
    boll_window = closes[-20:]
    mid = fmean(boll_window)
    sigma = pstdev(boll_window)
    volume_mean = fmean(volumes[-20:])
    volume_ratio = volumes[-1] / volume_mean if volume_mean > 0 else 1.0

    values = dict(
        symbol=symbol,
        timeframe=timeframe,
        as_of=candles[-1].open_time,
        close=closes[-1],
        ema5=_ema(closes, 5),
        ema10=_ema(closes, 10),
        ema20=_ema(closes, 20),
        ema30=_ema(closes, 30),
        ema60=_ema(closes, 60),
        rsi14=_rsi(closes, 14),
        atr14=_atr(candles, 14),
        boll_mid=mid,
        boll_upper=mid + 2.0 * sigma,
        boll_lower=mid - 2.0 * sigma,
        volume_ratio20=volume_ratio,
    )
    if not all(math.isfinite(v) for k, v in values.items() if isinstance(v, float)):
        raise ValueError("non-finite feature generated")
    return FeatureSnapshot(**values)
