from aars_weather_trading.gates.gate_result import GateResult

_BLOCKING_WORKER_STATES = {"stale", "degraded", "missing", "error", "unknown"}


def evaluate_freshness_gate(unified_status: dict | None) -> GateResult:
    if not isinstance(unified_status, dict) or not unified_status:
        return GateResult(passed=True, status="pass", block_reasons=[])

    overall_status = str(unified_status.get("overall_status") or "").lower()
    if overall_status in {"degraded", "missing"}:
        return GateResult(
            passed=False,
            status="blocked",
            block_reasons=["unified_status_degraded"],
        )

    monitoring = unified_status.get("monitoring")
    if not isinstance(monitoring, dict):
        return GateResult(passed=True, status="pass", block_reasons=[])

    workers = monitoring.get("workers")
    if not isinstance(workers, list):
        return GateResult(passed=True, status="pass", block_reasons=[])

    for worker in workers:
        if not isinstance(worker, dict):
            continue
        status = str(worker.get("status") or "").lower()
        if status in _BLOCKING_WORKER_STATES:
            return GateResult(
                passed=False,
                status="blocked",
                block_reasons=["stale_worker"],
            )

    return GateResult(passed=True, status="pass", block_reasons=[])

