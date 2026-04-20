import json
from typing import Optional

import typer

from weather_comparison_engine.compare.realtime_comparison_adapter import RealtimeComparisonAdapter
from weather_comparison_engine.features import (
    HistoricalFeatureStoreBuilder,
    load_comparison_history,
    load_optional_json_records,
)
from weather_comparison_engine.ingest.realtime_market_loader import RealtimeMarketLoader
from weather_comparison_engine.monitoring import MonitoringStatusBuilder
from weather_comparison_engine.ingest.realtime_forecast_loader import RealtimeForecastLoader
from weather_comparison_engine.outputs.history_appender import ComparisonHistoryAppender
from weather_comparison_engine.settings import (
    BACKTEST_EDGE_THRESHOLD,
    BACKTEST_REPORT_JSON,
    CALIBRATION_REPORT_JSON,
    COMPARISON_HISTORY_JSON,
    COMPARISON_MONITOR_STALE_AFTER_SECONDS,
    EXECUTION_GATEWAY_PRODUCTION_READINESS_JSON,
    FEATURE_STORE_SUMMARY_JSON,
    FEATURE_STORE_TRAINING_SAMPLES_JSONL,
    FORECAST_MONITOR_STALE_AFTER_SECONDS,
    GATE_STACK_API_JSON,
    GATE_STACK_AUTOMATION_SUMMARY_JSON,
    GATE_STACK_CONTRACT_CONSISTENCY_JSON,
    GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON,
    GATE_STACK_OPS_ALERTS_JSONL,
    GATEWAY_MONITOR_STALE_AFTER_SECONDS,
    LATEST_DASHBOARD_ROWS_JSON,
    MARKET_MONITOR_STALE_AFTER_SECONDS,
    MODEL_VALIDATION_BUCKET_COUNT,
    MODEL_VALIDATION_REPORT_JSON,
    LABEL_COVERAGE_REPORT_JSON,
    MONITORING_STATUS_JSON,
    OFFICIAL_HISTORY_JSONL,
    OFFICIAL_RECORDS_GLOB,
    PROBABILITY_SHADOW_REPORT_JSON,
    PROBABILITY_MONITOR_STALE_AFTER_SECONDS,
    REALTIME_FORECAST_JSON,
    REALTIME_FORECAST_SNAPSHOTS_GLOB,
    REALTIME_MARKET_JSON,
    RESOLVER_MONITOR_STALE_AFTER_SECONDS,
    RESOLVER_REPORT_JSON,
    UNIFIED_STATUS_JSON,
    VALIDATION_FRESHNESS_STATUS_JSON,
    VALIDATION_MONITOR_STALE_AFTER_SECONDS,
    TELEGRAM_GATE_RUNTIME_SNAPSHOT_JSON,
)
from weather_comparison_engine.status import (
    GateStackAPIBuilder,
    UnifiedStatusBuilder,
    VALID_FAIL_ON_SIGNALS,
    append_ops_alert,
    build_automation_summary,
    build_gate_stack_contract_consistency_report,
    build_ops_alert_event,
    load_optional_json,
    resolve_exit_code,
    should_emit_ops_alert,
    write_automation_summary,
)
from weather_comparison_engine.validation import (
    ValidationQualityReportBuilder,
    build_model_validation_report,
    load_training_samples_jsonl,
)

app = typer.Typer(help="weather-comparison-engine CLI")


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


@app.command()
def build_realtime_comparison() -> None:
    if not REALTIME_MARKET_JSON.exists():
        raise FileNotFoundError(f"Missing realtime market snapshot: {REALTIME_MARKET_JSON}")

    market_loader = RealtimeMarketLoader()
    forecast_loader = RealtimeForecastLoader()
    adapter = RealtimeComparisonAdapter()
    appender = ComparisonHistoryAppender(str(COMPARISON_HISTORY_JSON))

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

    appender.append(point)

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
        "band_distance": 0 if point.get("comparison_status") == "aligned" else (
            1 if point.get("comparison_status") == "mild_divergence" else 2
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

    typer.echo(f"Realtime comparison appended to {COMPARISON_HISTORY_JSON}")
    typer.echo(f"Latest dashboard row exported to {LATEST_DASHBOARD_ROWS_JSON}")


@app.command()
def build_feature_store() -> None:
    if not COMPARISON_HISTORY_JSON.exists():
        raise FileNotFoundError(f"Missing comparison history: {COMPARISON_HISTORY_JSON}")

    comparison_rows = load_comparison_history(COMPARISON_HISTORY_JSON)
    resolver_report = None
    if RESOLVER_REPORT_JSON.exists():
        resolver_report = RealtimeForecastLoader().load(RESOLVER_REPORT_JSON)

    if OFFICIAL_HISTORY_JSONL.exists():
        official_records = load_optional_json_records(OFFICIAL_HISTORY_JSONL)
    else:
        official_records = load_optional_json_records(OFFICIAL_RECORDS_GLOB)
    builder = HistoricalFeatureStoreBuilder()
    samples = builder.build_samples(
        comparison_rows=comparison_rows,
        resolver_report=resolver_report,
        official_records=official_records,
    )
    summary = builder.build_summary(samples)

    builder.write_samples_jsonl(samples, FEATURE_STORE_TRAINING_SAMPLES_JSONL)
    builder.write_summary(summary, FEATURE_STORE_SUMMARY_JSON)

    typer.echo(f"Training samples exported to {FEATURE_STORE_TRAINING_SAMPLES_JSONL}")
    typer.echo(f"Feature store summary exported to {FEATURE_STORE_SUMMARY_JSON}")


@app.command()
def build_model_validation() -> None:
    samples = load_training_samples_jsonl(FEATURE_STORE_TRAINING_SAMPLES_JSONL)
    calibration_report, backtest_report, validation_report = build_model_validation_report(
        samples,
        calibration_bucket_count=MODEL_VALIDATION_BUCKET_COUNT,
        edge_threshold=BACKTEST_EDGE_THRESHOLD,
    )

    CALIBRATION_REPORT_JSON.write_text(json.dumps(calibration_report, indent=2, ensure_ascii=False), encoding="utf-8")
    BACKTEST_REPORT_JSON.write_text(json.dumps(backtest_report, indent=2, ensure_ascii=False), encoding="utf-8")
    MODEL_VALIDATION_REPORT_JSON.write_text(
        json.dumps(validation_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    typer.echo(f"Calibration report exported to {CALIBRATION_REPORT_JSON}")
    typer.echo(f"Backtest report exported to {BACKTEST_REPORT_JSON}")
    typer.echo(f"Model validation report exported to {MODEL_VALIDATION_REPORT_JSON}")


@app.command()
def build_monitoring_status() -> None:
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
    out = MonitoringStatusBuilder().write(MONITORING_STATUS_JSON, worker_specs)
    typer.echo(out.read_text(encoding="utf-8"))
    typer.echo(f"Monitoring status exported to {out}")


@app.command()
def build_validation_quality() -> None:
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
    typer.echo(f"Validation freshness exported to {VALIDATION_FRESHNESS_STATUS_JSON}")
    typer.echo(f"Label coverage exported to {LABEL_COVERAGE_REPORT_JSON}")


@app.command()
def build_unified_status() -> None:
    monitoring_report = load_optional_json(MONITORING_STATUS_JSON)
    latest_dashboard_rows = load_optional_json(LATEST_DASHBOARD_ROWS_JSON)
    probability_shadow_report = load_optional_json(PROBABILITY_SHADOW_REPORT_JSON)
    production_readiness_report = load_optional_json(EXECUTION_GATEWAY_PRODUCTION_READINESS_JSON)
    validation_freshness_status = load_optional_json(VALIDATION_FRESHNESS_STATUS_JSON)
    label_coverage_report = load_optional_json(LABEL_COVERAGE_REPORT_JSON)

    out = UnifiedStatusBuilder().write(
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
    unified_status_payload = load_optional_json(out)
    gate_stack_out = GateStackAPIBuilder().write(
        GATE_STACK_API_JSON,
        unified_status_payload if isinstance(unified_status_payload, dict) else {},
        latest_dashboard_rows=latest_dashboard_rows if isinstance(latest_dashboard_rows, list) else [],
    )
    typer.echo(out.read_text(encoding="utf-8"))
    typer.echo(f"Unified status exported to {out}")
    typer.echo(f"Gate stack API exported to {gate_stack_out}")


@app.command()
def build_gate_stack_api() -> None:
    unified_status = load_optional_json(UNIFIED_STATUS_JSON)
    out = GateStackAPIBuilder().write(
        GATE_STACK_API_JSON,
        unified_status if isinstance(unified_status, dict) else {},
        latest_dashboard_rows=load_optional_json(LATEST_DASHBOARD_ROWS_JSON),
    )
    typer.echo(out.read_text(encoding="utf-8"))
    typer.echo(f"Gate stack API exported to {out}")


@app.command()
def build_gate_stack_automation_summary(
    market_id: Optional[str] = typer.Option(
        default=None,
        help="Optional market_id for market-specific automation summary.",
    ),
) -> None:
    gate_stack_api = load_optional_json(GATE_STACK_API_JSON)
    summary = build_automation_summary(
        gate_stack_api if isinstance(gate_stack_api, dict) else {},
        market_id=market_id,
    )
    out = write_automation_summary(GATE_STACK_AUTOMATION_SUMMARY_JSON, summary)
    typer.echo(out.read_text(encoding="utf-8"))
    typer.echo(f"Gate stack automation summary exported to {out}")


@app.command()
def run_gate_stack_automation_check(
    market_id: Optional[str] = typer.Option(
        default=None,
        help="Optional market_id for market-specific automation summary.",
    ),
    fail_on_signal: str = typer.Option(
        default="red",
        help="One of: red, amber, never. Decides when command exits non-zero.",
    ),
) -> None:
    mode = str(fail_on_signal or "").strip().lower()
    if mode not in VALID_FAIL_ON_SIGNALS:
        raise typer.BadParameter(
            f"Unsupported fail_on_signal={fail_on_signal}. "
            f"Expected one of: {', '.join(sorted(VALID_FAIL_ON_SIGNALS))}."
        )

    unified_status = load_optional_json(UNIFIED_STATUS_JSON)
    latest_dashboard_rows = load_optional_json(LATEST_DASHBOARD_ROWS_JSON)
    gate_stack_api = GateStackAPIBuilder().build(
        unified_status if isinstance(unified_status, dict) else {},
        latest_dashboard_rows=latest_dashboard_rows if isinstance(latest_dashboard_rows, list) else [],
    )
    GATE_STACK_API_JSON.write_text(
        json.dumps(gate_stack_api, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    summary = build_automation_summary(gate_stack_api, market_id=market_id)
    write_automation_summary(GATE_STACK_AUTOMATION_SUMMARY_JSON, summary)
    typer.echo(json.dumps(summary, indent=2, ensure_ascii=False))
    typer.echo(f"Gate stack API exported to {GATE_STACK_API_JSON}")
    typer.echo(f"Gate stack automation summary exported to {GATE_STACK_AUTOMATION_SUMMARY_JSON}")

    exit_code = resolve_exit_code(summary, fail_on_signal=mode)
    if should_emit_ops_alert(summary, exit_code=exit_code):
        alert_event = build_ops_alert_event(
            summary=summary,
            fail_on_signal=mode,
            exit_code=exit_code,
            cycle=None,
        )
        append_ops_alert(GATE_STACK_OPS_ALERTS_JSONL, alert_event)
        typer.echo(f"Ops alert appended to {GATE_STACK_OPS_ALERTS_JSONL}")
    if exit_code != 0:
        raise typer.Exit(code=exit_code)


@app.command()
def check_gate_stack_contract_consistency(
    market_id: Optional[str] = typer.Option(
        default=None,
        help="Optional market_id for market-specific consistency check.",
    ),
    fail_on_mismatch: bool = typer.Option(
        default=False,
        help="Exit non-zero when mismatches are detected.",
    ),
) -> None:
    gate_stack_api = load_optional_json(GATE_STACK_API_JSON)
    automation_summary = load_optional_json(GATE_STACK_AUTOMATION_SUMMARY_JSON)
    report = build_gate_stack_contract_consistency_report(
        gate_stack_api if isinstance(gate_stack_api, dict) else {},
        automation_summary if isinstance(automation_summary, dict) else {},
        market_id=market_id,
        telegram_runtime_snapshot=load_optional_json(TELEGRAM_GATE_RUNTIME_SNAPSHOT_JSON),
        gateway_runtime_snapshot=load_optional_json(GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON),
    )
    GATE_STACK_CONTRACT_CONSISTENCY_JSON.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
    typer.echo(f"Gate stack contract consistency exported to {GATE_STACK_CONTRACT_CONSISTENCY_JSON}")
    if fail_on_mismatch and not bool(report.get("passed")):
        raise typer.Exit(code=3)


if __name__ == "__main__":
    app()
