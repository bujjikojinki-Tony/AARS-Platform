from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from weather_comparison_engine.settings import (
    GATE_AUTOMATION_CHECK_INTERVAL_SECONDS,
    GATE_AUTOMATION_CHECK_MAX_CYCLES,
    GATE_AUTOMATION_FAIL_ON_SIGNAL,
    GATE_AUTOMATION_RETRY_BACKOFF_SECONDS,
    GATE_STACK_API_JSON,
    GATE_STACK_AUTOMATION_SUMMARY_JSON,
    GATE_STACK_CONTRACT_CONSISTENCY_JSON,
    GATE_STACK_CONTRACT_CONSISTENCY_TREND_JSON,
    GATE_STACK_OPS_ALERTS_JSONL,
    GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON,
    LATEST_DASHBOARD_ROWS_JSON,
    TELEGRAM_GATE_RUNTIME_SNAPSHOT_JSON,
    UNIFIED_STATUS_JSON,
)
from weather_comparison_engine.status import (
    GateStackAPIBuilder,
    append_ops_alert,
    build_automation_summary,
    build_gate_stack_contract_consistency_report,
    build_initial_trend,
    build_ops_alert_event,
    load_optional_json,
    resolve_exit_code,
    should_emit_ops_alert,
    update_consistency_trend,
    write_automation_summary,
)


def _run_once(*, cycle: int) -> dict:
    unified_status = load_optional_json(UNIFIED_STATUS_JSON)
    latest_dashboard_rows = load_optional_json(LATEST_DASHBOARD_ROWS_JSON)
    gate_stack_api = GateStackAPIBuilder().build(
        unified_status if isinstance(unified_status, dict) else {},
        latest_dashboard_rows=latest_dashboard_rows if isinstance(latest_dashboard_rows, list) else [],
    )
    GATE_STACK_API_JSON.write_text(json.dumps(gate_stack_api, indent=2, ensure_ascii=False), encoding="utf-8")

    summary = build_automation_summary(gate_stack_api)
    write_automation_summary(GATE_STACK_AUTOMATION_SUMMARY_JSON, summary)
    consistency_report = build_gate_stack_contract_consistency_report(
        gate_stack_api,
        summary,
        market_id=str(summary.get("market_id") or gate_stack_api.get("market_id") or ""),
        telegram_runtime_snapshot=load_optional_json(TELEGRAM_GATE_RUNTIME_SNAPSHOT_JSON),
        gateway_runtime_snapshot=load_optional_json(GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON),
    )
    GATE_STACK_CONTRACT_CONSISTENCY_JSON.write_text(
        json.dumps(consistency_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    trend_payload = update_consistency_trend(
        load_optional_json(GATE_STACK_CONTRACT_CONSISTENCY_TREND_JSON) or build_initial_trend(),
        report=consistency_report,
        cycle=cycle,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    GATE_STACK_CONTRACT_CONSISTENCY_TREND_JSON.write_text(
        json.dumps(trend_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    exit_code = resolve_exit_code(summary, fail_on_signal=GATE_AUTOMATION_FAIL_ON_SIGNAL)

    alert_written = False
    if should_emit_ops_alert(summary, exit_code=exit_code):
        alert = build_ops_alert_event(
            summary=summary,
            fail_on_signal=GATE_AUTOMATION_FAIL_ON_SIGNAL,
            exit_code=exit_code,
            cycle=cycle,
        )
        append_ops_alert(GATE_STACK_OPS_ALERTS_JSONL, alert)
        alert_written = True

    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "cycle": cycle,
        "automation_signal": summary.get("automation_signal"),
        "severity": summary.get("severity"),
        "recommended_operator_action": summary.get("recommended_operator_action"),
        "primary_block_reason": summary.get("primary_block_reason"),
        "consistency_passed": consistency_report.get("passed"),
        "consistency_mismatch_count": consistency_report.get("mismatch_count"),
        "consistency_bucket_counts": (consistency_report.get("mismatch_buckets") or {}).get("counts") or {},
        "exit_code": exit_code,
        "alert_written": alert_written,
        "gate_stack_api_path": str(GATE_STACK_API_JSON),
        "automation_summary_path": str(GATE_STACK_AUTOMATION_SUMMARY_JSON),
        "consistency_report_path": str(GATE_STACK_CONTRACT_CONSISTENCY_JSON),
        "consistency_trend_path": str(GATE_STACK_CONTRACT_CONSISTENCY_TREND_JSON),
        "ops_alerts_path": str(GATE_STACK_OPS_ALERTS_JSONL),
    }
    print(json.dumps(payload, ensure_ascii=False))
    return payload


async def main() -> None:
    print("=" * 80)
    print("STARTING GATE STACK AUTOMATION REALTIME WORKER")
    print(f"Interval seconds : {GATE_AUTOMATION_CHECK_INTERVAL_SECONDS}")
    print(f"Max cycles       : {GATE_AUTOMATION_CHECK_MAX_CYCLES or 'infinite'}")
    print(f"Fail on signal   : {GATE_AUTOMATION_FAIL_ON_SIGNAL}")
    print(f"Retry backoff    : {GATE_AUTOMATION_RETRY_BACKOFF_SECONDS}")
    print("=" * 80)

    cycle = 0
    while True:
        cycle += 1
        success = False
        for attempt, backoff in enumerate((0, *GATE_AUTOMATION_RETRY_BACKOFF_SECONDS), start=1):
            if backoff > 0:
                await asyncio.sleep(backoff)
            try:
                _run_once(cycle=cycle)
                success = True
                break
            except Exception as exc:
                print(
                    json.dumps(
                        {
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "cycle": cycle,
                            "attempt": attempt,
                            "error": str(exc),
                            "status": "retrying" if attempt <= len(GATE_AUTOMATION_RETRY_BACKOFF_SECONDS) else "failed",
                        },
                        ensure_ascii=False,
                    )
                )
        if not success:
            raise RuntimeError("gate stack automation realtime worker failed after retries")

        if GATE_AUTOMATION_CHECK_MAX_CYCLES and cycle >= GATE_AUTOMATION_CHECK_MAX_CYCLES:
            break
        await asyncio.sleep(GATE_AUTOMATION_CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
