from weather_execution_gateway.models.execution_result import ExecutionResult


class DryRunExecutor:
    def execute(self, result: ExecutionResult) -> ExecutionResult:
        if not result.accepted:
            return result

        return ExecutionResult(
            intent_id=result.intent_id,
            status="dry_run_executed",
            mode=result.mode,
            accepted=True,
            reason=result.reason,
            simulated_order_id=result.simulated_order_id,
        )
