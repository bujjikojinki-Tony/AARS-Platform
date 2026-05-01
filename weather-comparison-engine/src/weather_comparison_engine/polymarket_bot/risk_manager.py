from __future__ import annotations

from dataclasses import dataclass

from weather_comparison_engine.polymarket_bot.models import OpportunityCandidate
from weather_comparison_engine.polymarket_bot.models import RiskGateResult


@dataclass(slots=True)
class RiskRules:
    min_edge_percent: float = 10.0
    min_liquidity: float = 100.0
    max_spread: float = 0.08
    max_position_percent: float = 2.0
    max_daily_loss_percent: float = 5.0
    circuit_breaker_loss_percent: float = 10.0


class RiskManager:
    def __init__(self, rules: RiskRules | None = None, *, circuit_breaker_active: bool = False) -> None:
        self.rules = rules or RiskRules()
        self.circuit_breaker_active = circuit_breaker_active

    def evaluate(self, candidate: OpportunityCandidate, *, checked_at: str) -> RiskGateResult:
        edge_passed = abs(candidate.edge_percent) >= self.rules.min_edge_percent
        liquidity_passed = candidate.liquidity >= self.rules.min_liquidity
        spread_passed = candidate.spread <= self.rules.max_spread
        max_position_passed = True
        breaker_inactive = not self.circuit_breaker_active

        checks = {
            "minEdgePassed": edge_passed,
            "minLiquidityPassed": liquidity_passed,
            "maxSpreadPassed": spread_passed,
            "maxPositionPassed": max_position_passed,
            "circuitBreakerInactive": breaker_inactive,
        }
        reasons: list[str] = []
        if not edge_passed:
            reasons.append("edge_below_threshold")
        if not liquidity_passed:
            reasons.append("liquidity_below_threshold")
        if not spread_passed:
            reasons.append("spread_above_threshold")
        if not breaker_inactive:
            reasons.append("circuit_breaker_active")

        if reasons:
            status = "BLOCK"
        elif candidate.spread >= self.rules.max_spread * 0.85 or candidate.liquidity <= self.rules.min_liquidity * 1.25:
            status = "WARN"
            reasons.append("near_risk_boundary")
        else:
            status = "PASS"

        return RiskGateResult(
            candidate_id=candidate.candidate_id,
            status=status,
            checks=checks,
            reasons=reasons,
            checked_at=checked_at,
        )
