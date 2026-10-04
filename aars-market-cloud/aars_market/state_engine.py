from __future__ import annotations

from .models import FeatureSnapshot, MarketState, MarketStateAssessment


def classify_market_state(f: FeatureSnapshot) -> MarketStateAssessment:
    """Explainable baseline classifier; thresholds are hypotheses to validate."""
    evidence: list[str] = []
    counter: list[str] = []

    bullish_stack = f.close > f.ema20 > f.ema60 and f.ema5 > f.ema10
    bearish_stack = f.close < f.ema20 < f.ema60 and f.ema5 < f.ema10
    high_volume = f.volume_ratio20 >= 1.25
    low_volatility = f.atr14 / f.close <= 0.025

    if bullish_stack and f.close >= f.boll_upper and high_volume:
        state, confidence = MarketState.BREAKOUT, 0.78
        evidence += ["price_above_ema20_ema60", "fast_ema_bullish", "bollinger_upper_break", "volume_confirmation"]
    elif bullish_stack and f.rsi14 >= 55:
        state, confidence = MarketState.TREND_EXPANSION, 0.72
        evidence += ["price_above_ema20_ema60", "fast_ema_bullish", "rsi_supports_uptrend"]
    elif bearish_stack and f.close <= f.boll_lower and high_volume:
        state, confidence = MarketState.BREAKDOWN, 0.80
        evidence += ["price_below_ema20_ema60", "fast_ema_bearish", "bollinger_lower_break", "volume_confirmation"]
    elif bearish_stack:
        state, confidence = MarketState.DISTRIBUTION, 0.64
        evidence += ["price_below_ema20_ema60", "fast_ema_bearish"]
    elif f.close > f.ema20 and f.ema5 > f.ema10 and f.rsi14 >= 50:
        state, confidence = MarketState.RECOVERY, 0.64
        evidence += ["price_reclaimed_ema20", "fast_ema_bullish", "rsi_above_50"]
    elif low_volatility and 42 <= f.rsi14 <= 58:
        state, confidence = MarketState.RANGE, 0.66
        evidence += ["compressed_atr", "neutral_rsi"]
    elif f.close <= f.boll_mid and f.rsi14 <= 45:
        state, confidence = MarketState.ACCUMULATION, 0.55
        evidence += ["price_lower_half_bollinger", "weak_rsi_possible_accumulation"]
    else:
        state, confidence = MarketState.RANGE, 0.50
        evidence.append("mixed_evidence_default_range")

    if f.volume_ratio20 < 0.8:
        counter.append("weak_volume_confirmation")
    if state in {MarketState.BREAKOUT, MarketState.TREND_EXPANSION, MarketState.RECOVERY} and f.rsi14 > 75:
        counter.append("rsi_overheated")
    if state in {MarketState.BREAKDOWN, MarketState.DISTRIBUTION} and f.rsi14 < 25:
        counter.append("rsi_oversold_reversal_risk")

    confidence = max(0.0, min(1.0, confidence - 0.04 * len(counter)))
    return MarketStateAssessment(state, confidence, tuple(evidence), tuple(counter))
