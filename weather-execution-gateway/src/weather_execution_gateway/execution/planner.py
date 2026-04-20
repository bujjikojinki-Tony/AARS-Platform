from weather_execution_gateway.models.execution_result import ExecutionResult
from weather_execution_gateway.models.order_intent import OrderIntent
from weather_execution_gateway.models.risk_state import RiskState


class ExecutionPlanner:
    def plan(self, intent: OrderIntent, risk_state: RiskState, mode: str = "dry_run") -> ExecutionResult:
        if risk_state.reason is not None:
            return ExecutionResult(
                intent_id=intent.intent_id,
                status="blocked",
                mode=mode,
                accepted=False,
                reason=risk_state.reason,
                simulated_order_id=None,
            )

        return ExecutionResult(
            intent_id=intent.intent_id,
            status="planned",
            mode=mode,
            accepted=True,
            reason=None,
            simulated_order_id=f"sim_{intent.intent_id}",
        )
