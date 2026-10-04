from __future__ import annotations

import json
from dataclasses import asdict

from aars_market.adapters import fetch_binance_spot_candles
from aars_market.features import compute_features
from aars_market.probability import estimate_outcome_probabilities
from aars_market.state_engine import classify_market_state


def snapshot(symbol: str) -> dict:
    candles = fetch_binance_spot_candles(symbol, "1h", 200)
    features = compute_features(candles)
    assessment = classify_market_state(features)
    probabilities = estimate_outcome_probabilities(assessment, horizon_bars=24)
    return {
        "symbol": symbol,
        "execution_mode": "PAPER_ONLY",
        "features": asdict(features),
        "market_state": assessment.state.value,
        "confidence": assessment.confidence,
        "evidence": list(assessment.evidence),
        "counter_evidence": list(assessment.counter_evidence),
        "probabilities": asdict(probabilities),
    }


if __name__ == "__main__":
    print(json.dumps([snapshot(s) for s in ("BTCUSDT", "ETHUSDT", "SOLUSDT")], indent=2, default=str))
