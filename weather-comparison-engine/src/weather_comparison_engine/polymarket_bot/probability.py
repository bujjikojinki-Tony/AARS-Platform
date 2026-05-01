from __future__ import annotations

from hashlib import sha256

from weather_comparison_engine.polymarket_bot.models import MarketSnapshot


class PlaceholderProbabilityProvider:
    """Deterministic placeholder engine for Execution Core v0.

    This provider intentionally does not use weather intelligence. It only
    produces stable pseudo-probabilities from market identifiers so Phase A can
    validate the execution-chain storage and signal plumbing.
    """

    def estimate(self, market: MarketSnapshot) -> float:
        digest = sha256(f"{market.market_id}|{market.question}".encode("utf-8")).hexdigest()
        basis_points = int(digest[:8], 16) % 4001
        probability = 0.30 + (basis_points / 10000.0)
        return round(min(max(probability, 0.30), 0.7000), 4)
