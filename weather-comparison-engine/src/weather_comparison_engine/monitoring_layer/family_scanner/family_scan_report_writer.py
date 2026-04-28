from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.monitoring_layer.family_scanner.anomaly_feature_builder import build_anomaly_features
from weather_comparison_engine.monitoring_layer.family_scanner.market_anomaly_event_writer import (
    build_market_anomaly_event,
    write_market_anomaly_events,
)


def build_family_scan_report(
    *,
    market_rows: list[dict],
    comparison_history: list[dict],
    probability_states: dict[str, dict] | None = None,
    source_policy_status: dict | None = None,
    now: datetime | None = None,
) -> dict:
    timestamp = now or datetime.now(timezone.utc)
    probability_states = probability_states or {}
    source_policy_status = source_policy_status or {}
    feature_rows = [
        build_anomaly_features(
            market_row=row,
            comparison_history=comparison_history,
            probability_state=probability_states.get(str(row.get("market_id") or "")),
        )
        for row in market_rows
    ]
    anomaly_events = [
        build_market_anomaly_event(
            feature_row=feature_row,
            source_policy_status=source_policy_status,
            now=timestamp,
        )
        for feature_row in feature_rows
    ]
    family_groups: dict[str, list[dict]] = defaultdict(list)
    for feature_row in feature_rows:
        family_groups[str(feature_row.get("market_family") or "-")].append(feature_row)

    family_summaries = [
        {
            "market_family": family,
            "market_count": len(rows),
            "average_intervention_like_score": round(sum(row["intervention_like_score"] for row in rows) / len(rows), 4) if rows else 0.0,
            "max_intervention_like_score": max((row["intervention_like_score"] for row in rows), default=0.0),
            "outlier_count": sum(1 for row in rows if row.get("peer_outlier_flag")),
            "signal_summary": _signal_summary(rows),
        }
        for family, rows in sorted(family_groups.items())
    ]
    signal_summary = _signal_summary(feature_rows)
    anomaly_bucket_counts = _anomaly_bucket_counts(feature_rows)

    top_anomalies = sorted(
        feature_rows,
        key=lambda row: (
            -(row.get("intervention_like_score", 0.0) or 0.0),
            str(row.get("market_id") or ""),
        ),
    )[:10]
    return {
        "schema_version": "family_scan_report.v1",
        "generated_at": timestamp.isoformat(),
        "market_count": len(market_rows),
        "family_count": len(family_groups),
        "input_mode": "canonical_only",
        "source_policy": {
            "schema_version": str(source_policy_status.get("schema_version") or "source_policy_status.v1"),
            "overall_status": str(source_policy_status.get("overall_status") or "unknown"),
            "fresh_count": int((source_policy_status.get("counts") or {}).get("fresh") or 0),
            "stale_count": int((source_policy_status.get("counts") or {}).get("stale") or 0),
            "unavailable_count": int((source_policy_status.get("counts") or {}).get("unavailable") or 0),
        },
        "signal_summary": signal_summary,
        "anomaly_bucket_counts": anomaly_bucket_counts,
        "family_summaries": family_summaries,
        "top_anomalies": top_anomalies,
        "feature_rows": feature_rows,
        "anomaly_events": anomaly_events,
    }


def write_family_scan_report(path: str | Path, report: dict) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _signal_summary(rows: list[dict]) -> dict:
    if not rows:
        return {
            "price_velocity_high_count": 0,
            "edge_dislocation_high_count": 0,
            "evidence_mismatch_count": 0,
            "microstructure_stress_high_count": 0,
            "peer_outlier_count": 0,
            "intervention_like_high_count": 0,
            "average_intervention_like_score": 0.0,
        }
    return {
        "price_velocity_high_count": sum(1 for row in rows if (row.get("price_velocity") or 0.0) >= 0.05),
        "edge_dislocation_high_count": sum(1 for row in rows if (row.get("edge_dislocation") or 0.0) >= 0.1),
        "evidence_mismatch_count": sum(1 for row in rows if row.get("evidence_mismatch")),
        "microstructure_stress_high_count": sum(1 for row in rows if (row.get("microstructure_stress_score") or 0.0) >= 0.7),
        "peer_outlier_count": sum(1 for row in rows if row.get("peer_outlier_flag")),
        "intervention_like_high_count": sum(1 for row in rows if (row.get("intervention_like_score") or 0.0) >= 0.8),
        "average_intervention_like_score": round(sum((row.get("intervention_like_score") or 0.0) for row in rows) / len(rows), 4),
    }


def _anomaly_bucket_counts(rows: list[dict]) -> dict:
    buckets = {"high": 0, "medium": 0, "low": 0}
    for row in rows:
        bucket = str(row.get("anomaly_bucket") or "low").lower()
        if bucket not in buckets:
            bucket = "low"
        buckets[bucket] += 1
    return buckets
