from backend.models.core import OpportunityCandidate
from backend.models.core import RiskGateResult
from backend.models.enums import RiskStatus


class RiskManager:
    def __init__(
        self,
        min_edge_percent: float = 10,
        min_liquidity: float = 100,
        max_spread: float = 0.08,
        circuit_breaker_active: bool = False,
    ):
        self.min_edge_percent = min_edge_percent
        self.min_liquidity = min_liquidity
        self.max_spread = max_spread
        self.circuit_breaker_active = circuit_breaker_active

    def evaluate(self, candidate: OpportunityCandidate) -> RiskGateResult:
        checks = {
            "minEdgePassed": abs(candidate.edge_percent) >= self.min_edge_percent,
            "minLiquidityPassed": candidate.liquidity >= self.min_liquidity,
            "maxSpreadPassed": candidate.spread <= self.max_spread,
            "circuitBreakerInactive": not self.circuit_breaker_active,
        }
        reasons = []
        if not checks["minEdgePassed"]:
            reasons.append("edge below threshold")
        if not checks["minLiquidityPassed"]:
            reasons.append("liquidity below threshold")
        if not checks["maxSpreadPassed"]:
            reasons.append("spread above threshold")
        if not checks["circuitBreakerInactive"]:
            reasons.append("circuit breaker active")
        status = RiskStatus.PASS_ if all(checks.values()) else RiskStatus.BLOCK
        return RiskGateResult(
            candidate_id=candidate.candidate_id,
            status=status,
            checks=checks,
            reasons=reasons,
        )
