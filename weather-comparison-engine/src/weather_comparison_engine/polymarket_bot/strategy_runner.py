from __future__ import annotations

from datetime import UTC
from datetime import datetime
from uuid import uuid4

from weather_comparison_engine.polymarket_bot.models import AuditLog
from weather_comparison_engine.polymarket_bot.models import MarketSnapshot
from weather_comparison_engine.polymarket_bot.models import OpportunityCandidate


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class StrategyRunner:
    def __init__(self, market_source, strategies, risk_manager, repositories) -> None:
        self.market_source = market_source
        self.strategies = list(strategies)
        self.risk_manager = risk_manager
        self.repositories = repositories

    def run_once(self) -> list[OpportunityCandidate]:
        candidates: list[OpportunityCandidate] = []
        markets = self.market_source.fetch_markets()
        for market in markets:
            self.repositories.market_snapshots.save(market)
            for strategy in self.strategies:
                signal = strategy.evaluate(
                    market,
                    signal_id=_make_id("sig"),
                    created_at=_now_iso(),
                )
                if signal is None:
                    continue
                self.repositories.strategy_signals.save(signal)

                candidate = self._to_candidate(signal=signal, market=market)
                risk_result = self.risk_manager.evaluate(candidate, checked_at=_now_iso())
                candidate.risk_status = risk_result.status
                candidate.action_status = self.resolve_action_status(risk_result.status)
                self.repositories.opportunity_candidates.save(candidate)
                self.repositories.audit_logs.save(
                    AuditLog(
                        event_id=_make_id("audit"),
                        event_type="CANDIDATE_CREATED",
                        object_type="OpportunityCandidate",
                        object_id=candidate.candidate_id,
                        payload_json=(
                            "{"
                            f"\"signal_id\":\"{signal.signal_id}\","
                            f"\"risk_status\":\"{risk_result.status}\","
                            f"\"strategy_id\":\"{signal.strategy_id}\""
                            "}"
                        ),
                        created_at=_now_iso(),
                    )
                )
                candidates.append(candidate)
        return candidates

    @staticmethod
    def resolve_action_status(risk_status: str) -> str:
        if risk_status == "PASS":
            return "SIMULATE"
        if risk_status == "WARN":
            return "WATCH"
        return "BLOCKED"

    @staticmethod
    def _to_candidate(*, signal, market: MarketSnapshot) -> OpportunityCandidate:
        confidence_tier = signal.confidence if signal.confidence in {"LOW", "MEDIUM", "HIGH"} else "LOW"
        return OpportunityCandidate(
            candidate_id=_make_id("cand"),
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
            confidence_tier=confidence_tier,
            risk_status="WARN",
            action_status="WATCH",
            created_at=_now_iso(),
            expires_at=None,
        )
