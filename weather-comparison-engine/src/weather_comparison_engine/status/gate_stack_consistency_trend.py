from __future__ import annotations


def build_initial_trend() -> dict:
    return {
        "schema_version": "gate_stack_contract_consistency_trend.v1",
        "total_cycles": 0,
        "mismatch_cycles": 0,
        "bucket_totals": {
            "schema_drift": 0,
            "source_drift": 0,
            "reason_drift": 0,
            "other_drift": 0,
        },
        "recent_cycles": [],
    }


def update_consistency_trend(
    trend: dict | None,
    *,
    report: dict,
    cycle: int,
    timestamp: str,
    history_limit: int = 50,
) -> dict:
    payload = trend if isinstance(trend, dict) else build_initial_trend()
    bucket_totals = payload.get("bucket_totals")
    if not isinstance(bucket_totals, dict):
        bucket_totals = build_initial_trend()["bucket_totals"]
    counts = ((report.get("mismatch_buckets") or {}).get("counts") or {})
    for key in ("schema_drift", "source_drift", "reason_drift", "other_drift"):
        bucket_totals[key] = int(bucket_totals.get(key) or 0) + int(counts.get(key) or 0)

    payload["schema_version"] = "gate_stack_contract_consistency_trend.v1"
    payload["total_cycles"] = int(payload.get("total_cycles") or 0) + 1
    if not bool(report.get("passed")):
        payload["mismatch_cycles"] = int(payload.get("mismatch_cycles") or 0) + 1
    else:
        payload["mismatch_cycles"] = int(payload.get("mismatch_cycles") or 0)
    payload["bucket_totals"] = bucket_totals

    recent_cycles = payload.get("recent_cycles")
    if not isinstance(recent_cycles, list):
        recent_cycles = []
    recent_cycles.append(
        {
            "cycle": cycle,
            "timestamp": timestamp,
            "passed": bool(report.get("passed")),
            "mismatch_count": int(report.get("mismatch_count") or 0),
            "bucket_counts": {
                "schema_drift": int(counts.get("schema_drift") or 0),
                "source_drift": int(counts.get("source_drift") or 0),
                "reason_drift": int(counts.get("reason_drift") or 0),
                "other_drift": int(counts.get("other_drift") or 0),
            },
        }
    )
    if len(recent_cycles) > history_limit:
        recent_cycles = recent_cycles[-history_limit:]
    payload["recent_cycles"] = recent_cycles
    return payload
