from __future__ import annotations

from datetime import UTC
from datetime import datetime
from uuid import uuid4

from weather_comparison_engine.polymarket_bot.models import AuditLog
from weather_comparison_engine.polymarket_bot.models import ExecutionDecision
from weather_comparison_engine.polymarket_bot.models import OpportunityCandidate
from weather_comparison_engine.polymarket_bot.models import SimulationResult


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _make_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class Simulator:
    def __init__(self, repositories) -> None:
        self.repositories = repositories

    def simulate(
        self,
        decision: ExecutionDecision,
        candidate: OpportunityCandidate,
        *,
        live_executor=None,
    ) -> SimulationResult:
        if decision.mode == "LIVE_EXECUTE":
            raise ValueError("live execution is disabled in Round PWB-01 Phase B")

        entry_price = candidate.market_probability if decision.action == "BUY_YES" else 1.0 - candidate.market_probability
        position_size = decision.position_size
        simulated_cost = round(entry_price * position_size, 4)
        expected_probability = candidate.model_probability
        max_loss = round(simulated_cost, 4)
        max_gain = round(max(position_size - simulated_cost, 0.0), 4)
        expected_value = round(
            expected_probability * max_gain - (1.0 - expected_probability) * max_loss,
            4,
        )

        result = SimulationResult(
            simulation_id=_make_id("sim"),
            decision_id=decision.decision_id,
            candidate_id=candidate.candidate_id,
            side="YES" if decision.action == "BUY_YES" else "NO",
            entry_price=round(entry_price, 4),
            position_size=position_size,
            simulated_cost=simulated_cost,
            expected_probability=expected_probability,
            expected_value=expected_value,
            max_loss=max_loss,
            max_gain=max_gain,
            result_status="COMPLETED",
            created_at=_now_iso(),
        )
        self.repositories.simulation_results.save(result)
        self.repositories.audit_logs.save(
            AuditLog(
                event_id=_make_id("audit"),
                event_type="SIMULATION_CREATED",
                object_type="SimulationResult",
                object_id=result.simulation_id,
                payload_json=(
                    "{"
                    f"\"decision_id\":\"{decision.decision_id}\","
                    f"\"candidate_id\":\"{candidate.candidate_id}\""
                    "}"
                ),
                created_at=_now_iso(),
            )
        )

        return result
