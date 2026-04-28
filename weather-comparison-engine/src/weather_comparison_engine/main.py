import json
from pathlib import Path
from typing import Optional

import typer

from weather_comparison_engine.governance import (
    load_measurement_registry_bundle,
    get_source_policy_threshold_seconds,
    load_source_policy_registry,
    validate_registry_bundle,
)
from weather_comparison_engine.compare.realtime_comparison_adapter import RealtimeComparisonAdapter
from weather_comparison_engine.features import (
    HistoricalFeatureStoreBuilder,
    load_comparison_history,
    load_optional_json_records,
)
from weather_comparison_engine.ingest.realtime_market_loader import RealtimeMarketLoader
from weather_comparison_engine.monitoring import MonitoringStatusBuilder
from weather_comparison_engine.monitoring_layer.runners import (
    run_alert_router_once,
    run_evidence_scan_once,
    run_market_discovery_scan_once,
    run_family_anomaly_scan_once,
    run_observation_alert_once,
    run_scanner_status_once,
)
from weather_comparison_engine.source_policy import SourcePolicyStatusBuilder
from weather_comparison_engine.ingest.realtime_forecast_loader import RealtimeForecastLoader
from weather_comparison_engine.outputs.dashboard_row_builder import build_latest_dashboard_row
from weather_comparison_engine.advanced_anomaly import write_advanced_anomaly_artifacts
from weather_comparison_engine.outputs.history_appender import ComparisonHistoryAppender
from weather_comparison_engine.opportunity_board import build_opportunity_board_view
from weather_comparison_engine.opportunity_board import load_opportunity_policy_bundle
from weather_comparison_engine.opportunity_board import write_opportunity_board_artifacts
from weather_comparison_engine.opportunity_board import write_opportunity_board_view
from weather_comparison_engine.operations_monitor import (
    build_operations_monitor_view_from_files,
    write_operations_monitor_artifacts,
)
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
    OPPORTUNITY_BOARD_CANONICAL_EXPLANATIONS_JSON,
    OPPORTUNITY_BOARD_CANONICAL_FEATURE_ROWS_JSON,
    OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
    OPPORTUNITY_BOARD_CITY_DIR,
    OPPORTUNITY_BOARD_EXPLANATIONS_JSON,
    OPPORTUNITY_BOARD_FEATURE_ROWS_JSON,
    OPPORTUNITY_BOARD_SUMMARY_JSON,
    OPPORTUNITY_SEED_LIST_JSON,
    MARKET_ANOMALY_EVENTS_DIR,
    MARKET_WORKSTATION_OUTPUT_DIR,
    OPERATIONS_MONITOR_SUMMARY_JSON,
    OPERATIONS_MONITOR_VIEW_JSON,
    LATEST_DASHBOARD_ROWS_JSON,
    OPPORTUNITY_BOARD_VIEW_JSON,
    MARKET_MONITOR_STALE_AFTER_SECONDS,
    MODEL_VALIDATION_BUCKET_COUNT,
    MODEL_VALIDATION_REPORT_JSON,
    LABEL_COVERAGE_REPORT_JSON,
    MONITORING_STATUS_JSON,
    OFFICIAL_HISTORY_JSONL,
    OFFICIAL_RECORDS_GLOB,
    MARKET_ALERT_EVENTS_JSON,
    MARKET_UNIVERSE_SNAPSHOT_JSON,
    EVIDENCE_SCAN_SNAPSHOT_JSON,
    SCANNER_STATUS_JSON,
    SCAN_QUEUE_STATUS_JSON,
    SCANNER_OPS_ALERTS_JSON,
    FAMILY_ANOMALY_SUMMARY_JSON,
    PROBABILITY_SHADOW_REPORT_JSON,
    PROBABILITY_MONITOR_STALE_AFTER_SECONDS,
    REALTIME_FORECAST_JSON,
    REALTIME_FORECAST_SNAPSHOTS_GLOB,
    REALTIME_MARKET_JSON,
    RESOLVER_MONITOR_STALE_AFTER_SECONDS,
    RESOLVER_REPORT_JSON,
    SOURCE_POLICY_MONITOR_STALE_AFTER_SECONDS,
    SOURCE_POLICY_REGISTRY_JSON,
    SOURCE_POLICY_STATUS_JSON,
    PROBABILITY_STATES_DIR,
    UNIFIED_STATUS_JSON,
    VALIDATION_ASSIMILATION_REPORT_JSON,
    VALIDATION_FRESHNESS_STATUS_JSON,
    VALIDATION_MONITOR_STALE_AFTER_SECONDS,
    VALIDATION_OUTPUT_DIR,
    ADVANCED_ANOMALY_OUTPUT_DIR,
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
from weather_comparison_engine.status.top_parameter_view import build_top_parameter_view
from weather_comparison_engine.validation import (
    ValidationQualityReportBuilder,
    build_model_validation_report,
    load_training_samples_jsonl,
)
from weather_comparison_engine.validation_assimilation import (
    build_validation_assimilation_artifacts_from_files,
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
    top_parameter_view = build_top_parameter_view(
        current_market=market_snapshot,
        forecast_snapshot=forecast_snapshot,
        comparison_point=point,
    )
    point["top_parameter_view"] = top_parameter_view

    appender.append(point)

    latest_row = build_latest_dashboard_row(
        market_snapshot=market_snapshot,
        forecast_snapshot=forecast_snapshot,
        point={**point, "top_parameter_view": top_parameter_view},
    )

    appender.overwrite_latest_dashboard_rows(
        [latest_row],
        str(LATEST_DASHBOARD_ROWS_JSON),
    )

    typer.echo(f"Realtime comparison appended to {COMPARISON_HISTORY_JSON}")
    typer.echo(f"Latest dashboard row exported to {LATEST_DASHBOARD_ROWS_JSON}")


@app.command("validate-registry")
def validate_registry_command() -> None:
    source_registry = load_source_policy_registry()
    measurement_bundle = load_measurement_registry_bundle()
    errors = validate_registry_bundle(
        source_registry=source_registry,
        measurement_bundle=measurement_bundle,
    )
    summary = {
        "ok": not errors,
        "source_policy_sources": len(source_registry.get("sources") or []),
        "measurement_registry_keys": sorted(
            key for key in measurement_bundle.keys() if key.endswith("_registry")
        ),
        "error_count": len(errors),
        "errors": errors,
    }
    typer.echo(json.dumps(summary, indent=2, ensure_ascii=False))
    if errors:
        raise typer.Exit(code=1)


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
    assimilation_report = validation_report.get("validation_assimilation_summary") or {}

    CALIBRATION_REPORT_JSON.write_text(json.dumps(calibration_report, indent=2, ensure_ascii=False), encoding="utf-8")
    BACKTEST_REPORT_JSON.write_text(json.dumps(backtest_report, indent=2, ensure_ascii=False), encoding="utf-8")
    MODEL_VALIDATION_REPORT_JSON.write_text(
        json.dumps(validation_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    VALIDATION_ASSIMILATION_REPORT_JSON.write_text(
        json.dumps(assimilation_report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    typer.echo(f"Calibration report exported to {CALIBRATION_REPORT_JSON}")
    typer.echo(f"Backtest report exported to {BACKTEST_REPORT_JSON}")
    typer.echo(f"Model validation report exported to {MODEL_VALIDATION_REPORT_JSON}")
    typer.echo(f"Validation assimilation report exported to {VALIDATION_ASSIMILATION_REPORT_JSON}")


@app.command("build-validation-summary")
def build_validation_summary_command(
    scope_type: str = typer.Option(default="family", help="Scope type: market, city_family, family."),
    scope_id: str = typer.Option(default="all", help="Scope identifier."),
) -> None:
    artifacts = build_validation_assimilation_artifacts_from_files(
        scope_type=scope_type,
        scope_id=scope_id,
        validation_report_path=MODEL_VALIDATION_REPORT_JSON if MODEL_VALIDATION_REPORT_JSON.exists() else None,
        validation_freshness_path=VALIDATION_FRESHNESS_STATUS_JSON if VALIDATION_FRESHNESS_STATUS_JSON.exists() else None,
        label_coverage_path=LABEL_COVERAGE_REPORT_JSON if LABEL_COVERAGE_REPORT_JSON.exists() else None,
        feature_store_summary_path=FEATURE_STORE_SUMMARY_JSON if FEATURE_STORE_SUMMARY_JSON.exists() else None,
        output_dir=VALIDATION_OUTPUT_DIR,
        policy_refs={
            "source_policy_ref": str(SOURCE_POLICY_REGISTRY_JSON),
            "measurement_policy_ref": str(UNIT_REGISTRY_JSON),
            "validation_policy_ref": str(MODEL_VALIDATION_REPORT_JSON),
            "promotion_policy_ref": str(VALIDATION_FRESHNESS_STATUS_JSON),
        },
        upstream_refs={
            "feature_store_ref": str(FEATURE_STORE_TRAINING_SAMPLES_JSONL),
            "label_store_ref": str(OFFICIAL_HISTORY_JSONL),
            "coverage_summary_ref": str(LABEL_COVERAGE_REPORT_JSON),
            "model_validation_compare_ref": str(MODEL_VALIDATION_REPORT_JSON),
        },
    )
    typer.echo(json.dumps(artifacts, indent=2, ensure_ascii=False))
    typer.echo(f"Validation artifacts exported to {VALIDATION_OUTPUT_DIR}")


@app.command("build-market-universe")
def build_market_universe_command() -> None:
    result = run_market_discovery_scan_once(
        opportunity_seed_path=OPPORTUNITY_SEED_LIST_JSON if OPPORTUNITY_SEED_LIST_JSON.exists() else None,
        opportunity_board_path=OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON if OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON.exists() else None,
        latest_dashboard_rows_path=LATEST_DASHBOARD_ROWS_JSON if LATEST_DASHBOARD_ROWS_JSON.exists() else None,
        market_realtime_path=REALTIME_MARKET_JSON if REALTIME_MARKET_JSON.exists() else None,
        output_path=MARKET_UNIVERSE_SNAPSHOT_JSON,
    )
    typer.echo(json.dumps(result["snapshot"], indent=2, ensure_ascii=False))
    typer.echo(f"Market universe exported to {result['output_path']}")


@app.command("build-evidence-scan")
def build_evidence_scan_command() -> None:
    universe = load_optional_json(MARKET_UNIVERSE_SNAPSHOT_JSON)
    result = run_evidence_scan_once(
        market_universe_snapshot=universe if isinstance(universe, dict) else {},
        output_path=EVIDENCE_SCAN_SNAPSHOT_JSON,
    )
    typer.echo(json.dumps(result["snapshot"], indent=2, ensure_ascii=False))
    typer.echo(f"Evidence scan exported to {result['output_path']}")


@app.command("build-scanner-status")
def build_scanner_status_command() -> None:
    universe = load_optional_json(MARKET_UNIVERSE_SNAPSHOT_JSON)
    evidence = load_optional_json(EVIDENCE_SCAN_SNAPSHOT_JSON)
    alerts = _load_jsonl_records(MARKET_ALERT_EVENTS_JSON)
    result = run_scanner_status_once(
        market_universe_snapshot=universe if isinstance(universe, dict) else {},
        evidence_scan_snapshot=evidence if isinstance(evidence, dict) else {},
        alert_events=alerts,
        output_path=SCANNER_STATUS_JSON,
    )
    typer.echo(json.dumps(result["status"], indent=2, ensure_ascii=False))
    typer.echo(f"Scanner status exported to {result['output_path']}")


@app.command("run-scan-pipeline")
def run_scan_pipeline_command() -> None:
    universe_result = run_market_discovery_scan_once(
        opportunity_seed_path=OPPORTUNITY_SEED_LIST_JSON if OPPORTUNITY_SEED_LIST_JSON.exists() else None,
        opportunity_board_path=OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON if OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON.exists() else None,
        latest_dashboard_rows_path=LATEST_DASHBOARD_ROWS_JSON if LATEST_DASHBOARD_ROWS_JSON.exists() else None,
        market_realtime_path=REALTIME_MARKET_JSON if REALTIME_MARKET_JSON.exists() else None,
        output_path=MARKET_UNIVERSE_SNAPSHOT_JSON,
    )
    evidence_result = run_evidence_scan_once(
        market_universe_snapshot=universe_result["snapshot"],
        output_path=EVIDENCE_SCAN_SNAPSHOT_JSON,
    )
    for market in universe_result["snapshot"].get("markets") or []:
        market_id = str(market.get("market_id") or "").strip()
        if not market_id:
            continue
        try:
            run_observation_alert_once(
                market_row=market,
                source_policy_status=load_optional_json(SOURCE_POLICY_STATUS_JSON) if SOURCE_POLICY_STATUS_JSON.exists() else {},
                market_alert_events_dir=MARKET_ALERT_EVENTS_JSON.parent,
            )
        except Exception:
            continue
    family_result = run_family_anomaly_scan_once(
        market_rows=(universe_result["snapshot"].get("markets") or []),
        comparison_history=load_optional_json(COMPARISON_HISTORY_JSON) if COMPARISON_HISTORY_JSON.exists() else [],
    )
    route_result = run_alert_router_once(
        market_alert_events=_load_jsonl_records(MARKET_ALERT_EVENTS_JSON),
        family_anomaly_report=family_result["report"],
        scanner_ops_alerts=[],
    )
    status_result = run_scanner_status_once(
        market_universe_snapshot=universe_result["snapshot"],
        evidence_scan_snapshot=evidence_result["snapshot"],
        alert_events=_load_jsonl_records(MARKET_ALERT_EVENTS_JSON),
        output_path=SCANNER_STATUS_JSON,
    )
    operations_monitor_payload = build_operations_monitor_view_from_files(
        scanner_status_path=SCANNER_STATUS_JSON,
        scan_queue_status_path=SCAN_QUEUE_STATUS_JSON,
        market_universe_snapshot_path=MARKET_UNIVERSE_SNAPSHOT_JSON,
        evidence_scan_snapshot_path=EVIDENCE_SCAN_SNAPSHOT_JSON,
        opportunity_board_path=OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
        source_policy_status_path=SOURCE_POLICY_STATUS_JSON,
        gate_stack_api_path=GATE_STACK_API_JSON,
        unified_status_path=UNIFIED_STATUS_JSON,
        family_anomaly_summary_path=FAMILY_ANOMALY_SUMMARY_JSON,
        market_alert_events_dir=MARKET_ALERT_EVENTS_JSON.parent,
        market_anomaly_events_dir=MARKET_ANOMALY_EVENTS_DIR,
        market_workstation_dir=MARKET_WORKSTATION_OUTPUT_DIR,
        scanner_ops_alerts_path=SCANNER_OPS_ALERTS_JSON,
    )
    operations_monitor_artifacts = write_operations_monitor_artifacts(
        view_path=OPERATIONS_MONITOR_VIEW_JSON,
        summary_path=OPERATIONS_MONITOR_SUMMARY_JSON,
        payload=operations_monitor_payload,
    )
    typer.echo(
        json.dumps(
            {
                "market_universe": universe_result["output_path"],
                "evidence_scan": evidence_result["output_path"],
                "family_scan": family_result["report_path"],
                "routing": route_result,
                "scanner_status": status_result["output_path"],
                "operations_monitor": str(operations_monitor_artifacts["view"]),
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    typer.echo(f"Operations monitor exported to {operations_monitor_artifacts['view']}")


@app.command()
def build_monitoring_status() -> None:
    _write_source_policy_status()
    worker_specs = [
        {
            "worker": "market_realtime",
            "label": "Market",
            "layer": "market_layer",
            "path": REALTIME_MARKET_JSON,
            "source_policy_name": "polymarket_clob",
            "stale_after_seconds": _monitoring_stale_after_seconds("polymarket_clob", MARKET_MONITOR_STALE_AFTER_SECONDS),
        },
        {
            "worker": "forecast_realtime",
            "label": "Forecast",
            "layer": "resolver_layer",
            "path": REALTIME_FORECAST_JSON,
            "source_policy_name": "ecmwf",
            "stale_after_seconds": _monitoring_stale_after_seconds("ecmwf", FORECAST_MONITOR_STALE_AFTER_SECONDS),
        },
        {
            "worker": "resolver_report",
            "label": "Resolver",
            "layer": "resolver_layer",
            "path": RESOLVER_REPORT_JSON,
            "source_policy_name": "resolver_registry",
            "stale_after_seconds": _monitoring_stale_after_seconds("resolver_registry", RESOLVER_MONITOR_STALE_AFTER_SECONDS),
        },
        {
            "worker": "probability_shadow",
            "label": "Probability",
            "layer": "probability_layer",
            "path": PROBABILITY_SHADOW_REPORT_JSON,
            "source_policy_name": "comparison_engine",
            "stale_after_seconds": _monitoring_stale_after_seconds("comparison_engine", PROBABILITY_MONITOR_STALE_AFTER_SECONDS),
        },
        {
            "worker": "comparison_output",
            "label": "Comparison",
            "layer": "comparison_layer",
            "path": LATEST_DASHBOARD_ROWS_JSON,
            "source_policy_name": "comparison_engine",
            "stale_after_seconds": _monitoring_stale_after_seconds("comparison_engine", COMPARISON_MONITOR_STALE_AFTER_SECONDS),
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
            "worker": "source_policy_status",
            "label": "Source Policy",
            "layer": "governance_layer",
            "path": SOURCE_POLICY_STATUS_JSON,
            "source_policy_name": "resolver_registry",
            "stale_after_seconds": _monitoring_stale_after_seconds("resolver_registry", SOURCE_POLICY_MONITOR_STALE_AFTER_SECONDS),
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
def build_observation_alert() -> None:
    result = run_observation_alert_once()
    typer.echo(json.dumps({k: v for k, v in result.items() if k != "event"}, indent=2, ensure_ascii=False))
    typer.echo(f"Observation alert exported to {result['output_path']}")


@app.command()
def build_family_anomaly_scan() -> None:
    result = run_family_anomaly_scan_once()
    typer.echo(json.dumps({k: v for k, v in result.items() if k != "report"}, indent=2, ensure_ascii=False))
    typer.echo(f"Family scan report exported to {result['report_path']}")
    typer.echo(f"Family anomaly events exported to {result['anomaly_events_path']}")


@app.command("build-advanced-anomaly")
def build_advanced_anomaly_command() -> None:
    market_rows = load_optional_json(LATEST_DASHBOARD_ROWS_JSON)
    comparison_history = load_optional_json(COMPARISON_HISTORY_JSON)
    source_policy_status = load_optional_json(SOURCE_POLICY_STATUS_JSON) if SOURCE_POLICY_STATUS_JSON.exists() else {}
    artifacts = write_advanced_anomaly_artifacts(
        output_dir=ADVANCED_ANOMALY_OUTPUT_DIR,
        market_rows=market_rows if isinstance(market_rows, list) else [],
        comparison_history=comparison_history if isinstance(comparison_history, list) else [],
        probability_states=_load_probability_states(),
        source_policy_status=source_policy_status if isinstance(source_policy_status, dict) else {},
        policy_refs={
            "anomaly_policy_ref": "threshold_policy.intervention_like_score.default.v1",
            "source_policy_ref": str(SOURCE_POLICY_STATUS_JSON),
        },
    )
    typer.echo(json.dumps({key: str(value) for key, value in artifacts.items()}, indent=2, ensure_ascii=False))
    typer.echo(f"Advanced anomaly artifacts exported to {ADVANCED_ANOMALY_OUTPUT_DIR}")


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
    _write_source_policy_status()
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
        source_policy_status=(
            load_optional_json(SOURCE_POLICY_STATUS_JSON)
            if SOURCE_POLICY_STATUS_JSON.exists()
            else {}
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
def build_source_policy_status() -> None:
    out = _write_source_policy_status()
    typer.echo(out.read_text(encoding="utf-8"))
    typer.echo(f"Source policy status exported to {out}")


@app.command("build-opportunity-board")
def build_opportunity_board() -> None:
    context = {
        "model_validation_report": load_optional_json(MODEL_VALIDATION_REPORT_JSON)
        if MODEL_VALIDATION_REPORT_JSON.exists()
        else {},
        "source_policy_status": load_optional_json(SOURCE_POLICY_STATUS_JSON)
        if SOURCE_POLICY_STATUS_JSON.exists()
        else {},
        "opportunity_seed_list": load_optional_json(OPPORTUNITY_SEED_LIST_JSON)
        if OPPORTUNITY_SEED_LIST_JSON.exists()
        else {},
        "opportunity_policy_bundle": load_opportunity_policy_bundle(),
    }
    payload = build_opportunity_board_view(
        latest_dashboard_rows=load_optional_json(LATEST_DASHBOARD_ROWS_JSON) or [],
        context=context,
    )
    artifacts = write_opportunity_board_artifacts(
        board_path=OPPORTUNITY_BOARD_VIEW_JSON,
        explanation_path=OPPORTUNITY_BOARD_EXPLANATIONS_JSON,
        feature_rows_path=OPPORTUNITY_BOARD_FEATURE_ROWS_JSON,
        city_dir=OPPORTUNITY_BOARD_CITY_DIR,
        payload=payload,
        summary_path=OPPORTUNITY_BOARD_SUMMARY_JSON,
        canonical_board_path=OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
        canonical_explanation_path=OPPORTUNITY_BOARD_CANONICAL_EXPLANATIONS_JSON,
        canonical_feature_rows_path=OPPORTUNITY_BOARD_CANONICAL_FEATURE_ROWS_JSON,
    )
    typer.echo(artifacts["board"].read_text(encoding="utf-8"))
    typer.echo(f"Opportunity board exported to {artifacts['board']}")
    typer.echo(f"Opportunity explanations exported to {artifacts['explanations']}")
    typer.echo(f"Opportunity feature rows exported to {artifacts['feature_rows']}")
    if "summary" in artifacts:
        typer.echo(f"Opportunity board summary exported to {artifacts['summary']}")


@app.command("build-operations-monitor")
def build_operations_monitor_command() -> None:
    payload = build_operations_monitor_view_from_files(
        scanner_status_path=SCANNER_STATUS_JSON,
        scan_queue_status_path=SCAN_QUEUE_STATUS_JSON,
        market_universe_snapshot_path=MARKET_UNIVERSE_SNAPSHOT_JSON,
        evidence_scan_snapshot_path=EVIDENCE_SCAN_SNAPSHOT_JSON,
        opportunity_board_path=OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
        source_policy_status_path=SOURCE_POLICY_STATUS_JSON,
        gate_stack_api_path=GATE_STACK_API_JSON,
        unified_status_path=UNIFIED_STATUS_JSON,
        family_anomaly_summary_path=FAMILY_ANOMALY_SUMMARY_JSON,
        market_alert_events_dir=MARKET_ALERT_EVENTS_JSON.parent,
        market_anomaly_events_dir=MARKET_ANOMALY_EVENTS_DIR,
        market_workstation_dir=MARKET_WORKSTATION_OUTPUT_DIR,
        scanner_ops_alerts_path=SCANNER_OPS_ALERTS_JSON,
    )
    artifacts = write_operations_monitor_artifacts(
        view_path=OPERATIONS_MONITOR_VIEW_JSON,
        summary_path=OPERATIONS_MONITOR_SUMMARY_JSON,
        payload=payload,
    )
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    typer.echo(f"Operations monitor exported to {artifacts['view']}")
    typer.echo(f"Operations monitor summary exported to {artifacts['summary']}")


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


def _write_source_policy_status() -> Path:
    builder = SourcePolicyStatusBuilder()
    return builder.write(SOURCE_POLICY_STATUS_JSON)


def _load_probability_states() -> dict[str, dict]:
    states: dict[str, dict] = {}
    if PROBABILITY_STATES_DIR.exists():
        for path in PROBABILITY_STATES_DIR.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            market_id = str(payload.get("market_id") or "").strip()
            if market_id:
                states[market_id] = payload
    return states


def _load_jsonl_records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception:
        return []
    records: list[dict] = []
    for line in lines:
        try:
            payload = json.loads(line)
        except Exception:
            continue
        if isinstance(payload, dict):
            records.append(payload)
    return records


def _monitoring_stale_after_seconds(source_name: str, fallback_seconds: int) -> int:
    source_threshold = get_source_policy_threshold_seconds(
        source_name,
        path=SOURCE_POLICY_REGISTRY_JSON,
    )
    if source_threshold is None:
        return fallback_seconds
    return max(int(source_threshold), 1)


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
