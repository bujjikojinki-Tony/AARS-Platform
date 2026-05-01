from uuid import uuid4

from backend.models.core import AuditLogEvent
from backend.models.core import OpportunityCandidate
from backend.models.enums import ActionStatus
from backend.models.enums import RiskStatus


class StrategyRunner:
    def __init__(self, market_source, strategies, risk_manager, repository):
        self.market_source = market_source
        self.strategies = strategies
        self.risk_manager = risk_manager
        self.repository = repository
        self.last_market_snapshots = []

    def run_once(self) -> list[OpportunityCandidate]:
        markets = self.market_source.fetch_markets()
        self.last_market_snapshots = list(markets)
        if not markets:
            self.repository.save_audit_log(
                AuditLogEvent(
                    event_id=f"evt_{uuid4().hex[:10]}",
                    event_type="SCAN_EMPTY",
                    object_type="MarketSource",
                    object_id="market_source",
                    payload={"message": "No markets returned by market source."},
                )
            )
            return []
        candidates = []
        for market in markets:
            self.repository.save_market_snapshot(market)
            for strategy in self.strategies:
                signal = strategy.evaluate(market)
                if signal is None:
                    continue
                self.repository.save_strategy_signal(signal)
                candidate = OpportunityCandidate(
                    candidate_id=f"cand_{uuid4().hex[:10]}",
                    signal_id=signal.signal_id,
                    market_id=market.market_id,
                    question=market.question,
                    side=signal.side,
                    market_probability=signal.market_probability,
                    model_probability=signal.model_probability,
                    edge_percent=signal.edge_percent,
                    z_score=signal.z_score,
                    liquidity=market.liquidity,
                    spread=market.spread,
                    confidence_tier=signal.confidence,
                )
                risk = self.risk_manager.evaluate(candidate)
                candidate.risk_status = risk.status
                candidate.action_status = (
                    ActionStatus.SIMULATE
                    if risk.status == RiskStatus.PASS_
                    else ActionStatus.BLOCKED
                )
                self.repository.save_opportunity_candidate(candidate)
                self.repository.save_audit_log(
                    AuditLogEvent(
                        event_id=f"evt_{uuid4().hex[:10]}",
                        event_type="CANDIDATE_CREATED",
                        object_type="OpportunityCandidate",
                        object_id=candidate.candidate_id,
                        payload={
                            "market_id": candidate.market_id,
                            "signal_id": candidate.signal_id,
                            "risk_status": candidate.risk_status.value,
                            "action_status": candidate.action_status.value,
                        },
                    )
                )
                candidates.append(candidate)
        return candidates
