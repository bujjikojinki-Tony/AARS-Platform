from uuid import uuid4

from backend.models.core import AuditLogEvent
from backend.models.core import ExecutionDecision
from backend.models.core import SimulationResult
from backend.models.enums import ExecutionMode
from backend.models.enums import ExecutionStatus
from backend.models.enums import RiskStatus
from backend.models.enums import Side


class Simulator:
    def __init__(self, repository):
        self.repository = repository

    def simulate(
        self,
        candidate_id: str,
        position_size: float = 10,
        allow_blocked_simulation: bool = False,
    ) -> SimulationResult:
        candidate = self.repository.get_candidate(candidate_id)
        if not candidate:
            raise ValueError("candidate not found")
        if candidate["risk_status"] == RiskStatus.BLOCK.value and not allow_blocked_simulation:
            self.repository.save_audit_log(
                AuditLogEvent(
                    event_id=f"evt_{uuid4().hex[:10]}",
                    event_type="SIMULATION_REJECTED",
                    object_type="OpportunityCandidate",
                    object_id=candidate_id,
                    payload={"reason": "candidate risk_status = BLOCK"},
                )
            )
            raise ValueError("candidate risk_status = BLOCK")
        side = Side(candidate["side"])
        entry_price = (
            candidate["market_probability"]
            if side == Side.YES
            else 1 - candidate["market_probability"]
        )
        simulated_cost = entry_price * position_size
        max_loss = simulated_cost
        max_gain = position_size - simulated_cost
        expected_probability = candidate["model_probability"]
        expected_value = expected_probability * max_gain - (1 - expected_probability) * max_loss
        decision = ExecutionDecision(
            decision_id=f"dec_{uuid4().hex[:10]}",
            candidate_id=candidate_id,
            mode=ExecutionMode.SIMULATION,
            action=f"BUY_{side.value}",
            position_size=position_size,
            expected_cost=simulated_cost,
            risk_status=RiskStatus(candidate["risk_status"]),
            execution_status=ExecutionStatus.SIMULATED,
        )
        result = SimulationResult(
            simulation_id=f"sim_{uuid4().hex[:10]}",
            decision_id=decision.decision_id,
            candidate_id=candidate_id,
            side=side,
            entry_price=entry_price,
            position_size=position_size,
            simulated_cost=simulated_cost,
            expected_probability=expected_probability,
            expected_value=expected_value,
            max_loss=max_loss,
            max_gain=max_gain,
        )
        self.repository.save_execution_decision(decision)
        self.repository.save_simulation_result(result)
        self.repository.save_audit_log(
            AuditLogEvent(
                event_id=f"evt_{uuid4().hex[:10]}",
                event_type="SIMULATION_CREATED",
                object_type="SimulationResult",
                object_id=result.simulation_id,
                payload={
                    "candidate_id": candidate_id,
                    "decision_id": decision.decision_id,
                    "position_size": position_size,
                    "live_execution": False,
                },
            )
        )
        return result
