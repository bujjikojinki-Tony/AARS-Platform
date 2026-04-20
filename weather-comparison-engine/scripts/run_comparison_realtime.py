from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from weather_comparison_engine.compare.realtime_comparison_adapter import RealtimeComparisonAdapter
from weather_comparison_engine.ingest.realtime_forecast_loader import RealtimeForecastLoader
from weather_comparison_engine.ingest.realtime_market_loader import RealtimeMarketLoader
from weather_comparison_engine.monitoring import MonitoringStatusBuilder
from weather_comparison_engine.outputs.history_appender import ComparisonHistoryAppender
from weather_comparison_engine.probability import build_probability_shadow_outputs
from weather_comparison_engine.settings import (
    COMPARISON_HISTORY_JSON,
    COMPARISON_LOOP_INTERVAL_SECONDS,
    COMPARISON_MONITOR_STALE_AFTER_SECONDS,
    EXECUTION_GATEWAY_PRODUCTION_READINESS_JSON,
    FORECAST_MONITOR_STALE_AFTER_SECONDS,
    GATEWAY_MONITOR_STALE_AFTER_SECONDS,
    LATEST_DASHBOARD_ROWS_JSON,
    MARKET_MONITOR_STALE_AFTER_SECONDS,
    LABEL_COVERAGE_REPORT_JSON,
    MODEL_VALIDATION_REPORT_JSON,
    MONITORING_STATUS_JSON,
    PROBABILITY_MONITOR_STALE_AFTER_SECONDS,
    PROBABILITY_SHADOW_REPORT_JSON,
    REALTIME_FORECAST_JSON,
    REALTIME_FORECAST_SNAPSHOTS_GLOB,
    REALTIME_MARKET_JSON,
    RESOLVER_MONITOR_STALE_AFTER_SECONDS,
    RESOLVER_REPORT_JSON,
    UNIFIED_STATUS_JSON,
    VALIDATION_FRESHNESS_STATUS_JSON,
    VALIDATION_MONITOR_STALE_AFTER_SECONDS,
    FEATURE_STORE_TRAINING_SAMPLES_JSONL,
    OFFICIAL_HISTORY_JSONL,
    OFFICIAL_RECORDS_GLOB,
)
from weather_comparison_engine.status import UnifiedStatusBuilder, load_optional_json
from weather_comparison_engine.validation import ValidationQualityReportBuilder, load_training_samples_jsonl
from weather_comparison_engine.features import load_optional_json_records


def compute_band_distance_from_status(status: str) -> int:
    if status == "aligned":
        return 0
    if status == "mild_divergence":
        return 1
    if status == "strong_divergence":
        return 2
    if status in {"unmatched_rule", "market_mismatch"}:
        return 999
    return 999


def _load_matching_forecast_snapshot(
    forecast_loader: RealtimeForecastLoader,
    market_id: str,
) -> dict:
    try:
        snapshots = forecast_loader.load_many(REALTIME_FORECAST_SNAPSHOTS_GLOB)
    except Exception:
        snapshots = []

    for snapshot in snapshots:
        if str(snapshot.get("market_id") or "") == str(market_id):
            return snapshot

    if not REALTIME_FORECAST_JSON.exists():
        raise FileNotFoundError(f"Missing realtime forecast snapshot: {REALTIME_FORECAST_JSON}")

    return forecast_loader.load(REALTIME_FORECAST_JSON)


async def run_once() -> dict:
    if not REALTIME_MARKET_JSON.exists():
        raise FileNotFoundError(f"Missing realtime market snapshot: {REALTIME_MARKET_JSON}")

    market_loader = RealtimeMarketLoader()
    forecast_loader = RealtimeForecastLoader()
    adapter = RealtimeComparisonAdapter()
    appender = ComparisonHistoryAppender(
        path=str(COMPARISON_HISTORY_JSON),
        max_rows_per_market=300,
    )

    market_snapshot = market_loader.load(REALTIME_MARKET_JSON)
    forecast_snapshot = _load_matching_forecast_snapshot(
        forecast_loader,
        str(market_snapshot["market_id"]),
    )

    point = adapter.build_comparison_point(
        market_snapshot=market_snapshot,
        forecast_snapshot=forecast_snapshot,
        market_id=market_snapshot["market_id"],
        market_band=market_snapshot.get("market_band"),
        confidence_score=float(forecast_snapshot.get("confidence_score", 0.0)),
        action_hint="watch",
    )

    appended = appender.append(point)

    latest_row = {
        "market_id": market_snapshot["market_id"],
        "market_question": market_snapshot.get("market_question"),
        "location_name": market_snapshot.get("location_name", "UNKNOWN"),
        "target_date": forecast_snapshot.get("target_date"),
        "variable_name": forecast_snapshot.get("variable_name"),
        "market_probability": market_snapshot.get("market_probability"),
        "favored_side": market_snapshot.get("favored_side"),
        "yes_price": market_snapshot.get("yes_price"),
        "no_price": market_snapshot.get("no_price"),
        "model_value": point.get("model_value"),
        "model_band": point.get("model_band"),
        "market_band": point.get("market_band"),
        "band_scheme": point.get("band_scheme"),
        "market_band_scheme": point.get("market_band_scheme"),
        "forecast_market_id": forecast_snapshot.get("market_id"),
        "rule_status": point.get("rule_status"),
        "rule_market_id": point.get("rule_market_id"),
        "market_family": point.get("market_family"),
        "resolution_scope": point.get("resolution_scope"),
        "supported_by_current_pipeline": point.get("supported_by_current_pipeline"),
        "required_data_source": point.get("required_data_source"),
        "band_distance": compute_band_distance_from_status(
            point.get("comparison_status", "unknown")
        ),
        "confidence_score": point.get("confidence_score"),
        "confidence_adjusted_gap": point.get("confidence_adjusted_gap"),
        "comparison_status": point.get("comparison_status"),
        "action_hint": point.get("action_hint"),
        "market_snapshot_ref": point.get("market_snapshot_ref"),
        "forecast_snapshot_ref": point.get("forecast_snapshot_ref"),
        "comparison_reason": point.get("comparison_reason"),
    }

    appender.overwrite_latest_dashboard_rows(
        [latest_row],
        str(LATEST_DASHBOARD_ROWS_JSON),
    )

    probability_outputs = build_probability_shadow_outputs()
    _write_validation_quality()
    _write_monitoring_status()
    _write_unified_status()

    if appended:
        print("[comparison] appended new history point")
    else:
        print("[comparison] skipped duplicate history point")

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_id": latest_row["market_id"],
        "model_band": latest_row["model_band"],
        "market_band": latest_row["market_band"],
        "band_scheme": latest_row.get("band_scheme"),
        "comparison_status": latest_row["comparison_status"],
        "confidence_adjusted_gap": latest_row["confidence_adjusted_gap"],
        "history_appended": appended,
        "probability_mode": probability_outputs["contract"].get("probability_mode"),
        "execution_constraint": probability_outputs["contract"].get("execution_constraint"),
    }


def _write_monitoring_status() -> None:
    worker_specs = [
        {
            "worker": "market_realtime",
            "label": "Market",
            "layer": "market_layer",
            "path": REALTIME_MARKET_JSON,
            "stale_after_seconds": MARKET_MONITOR_STALE_AFTER_SECONDS,
        },
        {
            "worker": "forecast_realtime",
            "label": "Forecast",
            "layer": "resolver_layer",
            "path": REALTIME_FORECAST_JSON,
            "stale_after_seconds": FORECAST_MONITOR_STALE_AFTER_SECONDS,
        },
        {
            "worker": "resolver_report",
            "label": "Resolver",
            "layer": "resolver_layer",
            "path": RESOLVER_REPORT_JSON,
            "stale_after_seconds": RESOLVER_MONITOR_STALE_AFTER_SECONDS,
        },
        {
            "worker": "probability_shadow",
            "label": "Probability",
            "layer": "probability_layer",
            "path": PROBABILITY_SHADOW_REPORT_JSON,
            "stale_after_seconds": PROBABILITY_MONITOR_STALE_AFTER_SECONDS,
        },
        {
            "worker": "comparison_output",
            "label": "Comparison",
            "layer": "comparison_layer",
            "path": LATEST_DASHBOARD_ROWS_JSON,
            "stale_after_seconds": COMPARISON_MONITOR_STALE_AFTER_SECONDS,
        },
        {
            "worker": "execution_gateway",
            "label": "Gateway",
            "layer": "authorization_execution_layer",
            "path": EXECUTION_GATEWAY_PRODUCTION_READINESS_JSON,
            "stale_after_seconds": GATEWAY_MONITOR_STALE_AFTER_SECONDS,
        },
        {
            "worker": "model_validation",
            "label": "Validation",
            "layer": "validation_layer",
            "path": MODEL_VALIDATION_REPORT_JSON,
            "stale_after_seconds": VALIDATION_MONITOR_STALE_AFTER_SECONDS,
        },
        {
            "worker": "validation_freshness",
            "label": "Validation Freshness",
            "layer": "validation_layer",
            "path": VALIDATION_FRESHNESS_STATUS_JSON,
            "stale_after_seconds": VALIDATION_MONITOR_STALE_AFTER_SECONDS,
        },
        {
            "worker": "label_coverage",
            "label": "Label Coverage",
            "layer": "validation_layer",
            "path": LABEL_COVERAGE_REPORT_JSON,
            "stale_after_seconds": VALIDATION_MONITOR_STALE_AFTER_SECONDS,
        },
    ]
    MonitoringStatusBuilder().write(MONITORING_STATUS_JSON, worker_specs)


def _write_validation_quality() -> None:
    if not FEATURE_STORE_TRAINING_SAMPLES_JSONL.exists():
        return
    samples = load_training_samples_jsonl(FEATURE_STORE_TRAINING_SAMPLES_JSONL)
    validation_report = load_optional_json(MODEL_VALIDATION_REPORT_JSON)
    official_records = (
        load_optional_json_records(OFFICIAL_HISTORY_JSONL)
        if OFFICIAL_HISTORY_JSONL.exists()
        else load_optional_json_records(OFFICIAL_RECORDS_GLOB)
    )
    builder = ValidationQualityReportBuilder()
    freshness = builder.build_validation_freshness_status(
        validation_report if isinstance(validation_report, dict) else None
    )
    coverage = builder.build_label_coverage_report(
        samples,
        validation_report=validation_report if isinstance(validation_report, dict) else None,
        official_records=official_records,
    )
    builder.write(VALIDATION_FRESHNESS_STATUS_JSON, freshness)
    builder.write(LABEL_COVERAGE_REPORT_JSON, coverage)


def _write_unified_status() -> None:
    monitoring_report = load_optional_json(MONITORING_STATUS_JSON)
    latest_dashboard_rows = load_optional_json(LATEST_DASHBOARD_ROWS_JSON)
    probability_shadow_report = load_optional_json(PROBABILITY_SHADOW_REPORT_JSON)
    production_readiness_report = load_optional_json(EXECUTION_GATEWAY_PRODUCTION_READINESS_JSON)
    validation_freshness_status = load_optional_json(VALIDATION_FRESHNESS_STATUS_JSON)
    label_coverage_report = load_optional_json(LABEL_COVERAGE_REPORT_JSON)

    UnifiedStatusBuilder().write(
        UNIFIED_STATUS_JSON,
        monitoring_report=monitoring_report if isinstance(monitoring_report, dict) else {},
        latest_dashboard_rows=latest_dashboard_rows if isinstance(latest_dashboard_rows, list) else [],
        probability_shadow_report=(
            probability_shadow_report if isinstance(probability_shadow_report, dict) else {}
        ),
        production_readiness_report=(
            production_readiness_report if isinstance(production_readiness_report, dict) else {}
        ),
        validation_freshness_status=(
            validation_freshness_status if isinstance(validation_freshness_status, dict) else {}
        ),
        label_coverage_report=(
            label_coverage_report if isinstance(label_coverage_report, dict) else {}
        ),
    )


async def main() -> None:
    print("=" * 80)
    print("STARTING COMPARISON REALTIME WORKER")
    print(f"Market input     : {REALTIME_MARKET_JSON}")
    print(f"Forecast input   : {REALTIME_FORECAST_JSON}")
    print(f"History output   : {COMPARISON_HISTORY_JSON}")
    print(f"Dashboard output : {LATEST_DASHBOARD_ROWS_JSON}")
    print(f"Loop interval    : {COMPARISON_LOOP_INTERVAL_SECONDS}s")
    print("=" * 80)

    while True:
        try:
            result = await run_once()
            print(
                f"[{result['timestamp']}] "
                f"market_id={result['market_id']} "
                f"model_band={result['model_band']} "
                f"market_band={result['market_band']} "
                f"scheme={result.get('band_scheme')} "
                f"status={result['comparison_status']} "
                f"gap={result['confidence_adjusted_gap']} "
                f"appended={result['history_appended']} "
                f"probability_mode={result.get('probability_mode')} "
                f"constraint={result.get('execution_constraint')}"
            )
        except Exception as e:
            print(f"[comparison-realtime] error: {e}")

        await asyncio.sleep(COMPARISON_LOOP_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
