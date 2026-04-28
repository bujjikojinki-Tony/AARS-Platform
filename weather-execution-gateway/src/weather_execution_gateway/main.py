from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import typer

from weather_execution_gateway.advisory.manual_advisory import (
    ManualAdvisoryAuditStore,
    build_human_fill_record,
)
from weather_execution_gateway.advisory.fill_reconciliation import HumanFillReconciler
from weather_execution_gateway.audit.logger import AuditLogger
from weather_execution_gateway.execution.approval_reader import ApprovalReader
from weather_execution_gateway.execution.executor import DryRunExecutor
from weather_execution_gateway.execution.intent_loader import IntentLoader
from weather_execution_gateway.execution.planner import ExecutionPlanner
from weather_execution_gateway.models.audit_event import AuditEvent
from weather_execution_gateway.models.execution_result import ExecutionResult
from weather_execution_gateway.models.order_intent import OrderIntent
from weather_execution_gateway.models.risk_state import RiskState
from weather_execution_gateway.polymarket.clob_execution import is_clob_adapter_ready
from weather_execution_gateway.polymarket.position_snapshot_producer import PositionSnapshotProducer
from weather_execution_gateway.polymarket.user_activity import PolymarketUserActivityReader
from weather_execution_gateway.risk.approval_gate import ApprovalGate
from weather_execution_gateway.risk.exposure_limits import ExposureLimits
from weather_execution_gateway.risk.gates import RiskGateEngine
from weather_execution_gateway.risk.kill_switch import KillSwitch
from weather_execution_gateway.risk.position_exposure import PositionExposureReader
from weather_execution_gateway.risk.production_readiness import (
    ProductionReadinessChecker,
    load_latest_approval_probe,
    load_optional_json,
)
from weather_execution_gateway.storage.repositories import ExecutionResultRepository
from weather_execution_gateway.storage.sqlite import SQLiteStore

app = typer.Typer(help="weather-execution-gateway CLI")

BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "config"
OUTPUT_DIR = BASE_DIR / "data" / "outputs"
WORKSPACE_DIR = BASE_DIR.parent
PENDING_INTENTS_DIR = (
    WORKSPACE_DIR / "weather-telegram-console" / "data" / "outputs" / "pending_intents"
)
APPROVAL_DB_PATH = (
    WORKSPACE_DIR / "weather-telegram-console" / "data" / "outputs" / "weather_telegram_console.db"
)

RISK_LIMITS_PATH = CONFIG_DIR / "risk_limits.yaml"
WHITELIST_PATH = CONFIG_DIR / "whitelist_markets.yaml"
EXECUTION_MODES_PATH = Path(
    os.getenv("EXECUTION_MODES_YAML", str(CONFIG_DIR / "execution_modes.yaml"))
)
CLOB_ADAPTER_PATH = Path(
    os.getenv("CLOB_ADAPTER_YAML", str(CONFIG_DIR / "clob_adapter.yaml"))
)
LIVE_MODE_POLICY_PATH = Path(
    os.getenv("LIVE_MODE_POLICY_YAML", str(CONFIG_DIR / "live_mode_policy.yaml"))
)
POSITION_SNAPSHOT_PATH = Path(
    os.getenv("POSITION_SNAPSHOT_JSON", str(OUTPUT_DIR / "position_snapshot.json"))
)
POSITION_SOURCE_PATH = Path(
    os.getenv("POSITION_SOURCE_JSON", str(OUTPUT_DIR / "sample_account_positions.json"))
)
MANUAL_ADVISORY_AUDIT_PATH = Path(
    os.getenv("MANUAL_ADVISORY_AUDIT_JSONL", str(OUTPUT_DIR / "manual_advisory_audit.jsonl"))
)
HUMAN_FILLS_PATH = Path(
    os.getenv("HUMAN_FILLS_JSONL", str(OUTPUT_DIR / "human_fills.jsonl"))
)
HUMAN_FILL_RECONCILIATION_REPORT_PATH = Path(
    os.getenv(
        "HUMAN_FILL_RECONCILIATION_REPORT_JSON",
        str(OUTPUT_DIR / "human_fill_reconciliation_report.json"),
    )
)
DASHBOARD_INTENT_PREVIEW_PATH = Path(
    os.getenv("DASHBOARD_INTENT_PREVIEW_JSON", str(OUTPUT_DIR / "dashboard_intent_preview.json"))
)
SAMPLE_INTENT_PATH = OUTPUT_DIR / "sample_intent.json"
SAMPLE_RESULT_PATH = OUTPUT_DIR / "sample_execution_result.json"
PRODUCTION_READINESS_REPORT_PATH = Path(
    os.getenv(
        "PRODUCTION_READINESS_REPORT_JSON",
        str(OUTPUT_DIR / "production_readiness_report.json"),
    )
)
MODEL_VALIDATION_REPORT_PATH = (
    Path(
        os.getenv(
            "MODEL_VALIDATION_REPORT_JSON",
            str(
                WORKSPACE_DIR
                / "weather-comparison-engine"
                / "data"
                / "outputs"
                / "model_validation_report.json"
            ),
        )
    )
)
UNIFIED_STATUS_PATH = Path(
    os.getenv(
        "UNIFIED_STATUS_JSON",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "unified_status.json"),
    )
)
GATE_STACK_API_PATH = Path(
    os.getenv(
        "GATE_STACK_API_JSON",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "gate_stack_api.json"),
    )
)
GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON = Path(
    os.getenv(
        "GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON",
        str(OUTPUT_DIR / "gateway_gate_runtime_snapshot.json"),
    )
)
COMPARISON_ENGINE_OUTPUT_DIR = WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs"
MARKET_ALERT_EVENTS_DIR = COMPARISON_ENGINE_OUTPUT_DIR / "market_alert_events"
FAMILY_SCAN_REPORTS_DIR = COMPARISON_ENGINE_OUTPUT_DIR / "family_scan_reports"
MARKET_ANOMALY_EVENTS_DIR = COMPARISON_ENGINE_OUTPUT_DIR / "market_anomaly_events"
SOURCE_POLICY_STATUS_PATH = COMPARISON_ENGINE_OUTPUT_DIR / "source_policy_status.json"


def load_yaml(path: Path) -> dict:
    import yaml

    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _build_risk_gate(risk_cfg: dict, whitelist_cfg: dict) -> RiskGateEngine:
    whitelist_markets = set(whitelist_cfg.get("markets", []))
    execution_enabled = bool(risk_cfg.get("execution", {}).get("enabled", False))

    return RiskGateEngine(
        whitelist_markets=whitelist_markets,
        execution_enabled=execution_enabled,
        kill_switch=KillSwitch(active=False),
        exposure_limits=ExposureLimits(
            max_notional_per_market=float(
                risk_cfg.get("exposure", {}).get("max_notional_per_market", 100)
            ),
            max_total_notional=float(risk_cfg.get("exposure", {}).get("max_total_notional", 500)),
        ),
    )


def _run_dry_run_for_intent(
    intent: OrderIntent,
    risk_cfg: dict,
    whitelist_cfg: dict,
    approval_valid: bool = False,
    position_snapshot_path: Path | None = None,
    unified_status_path: Path | None = None,
    gate_stack_api_path: Path | None = None,
) -> tuple[ExecutionResult, RiskState]:
    gate = _build_risk_gate(risk_cfg, whitelist_cfg)
    exposure = PositionExposureReader(
        position_snapshot_path or POSITION_SNAPSHOT_PATH
    ).exposure_for_market(intent.market_id)
    unified_status = _build_risk_status_payload(
        unified_status_path=unified_status_path,
        gate_stack_api_path=gate_stack_api_path,
        market_id=intent.market_id,
    )

    risk_state = gate.evaluate(
        intent=intent,
        market_notional=float(exposure.get("market_notional") or 0.0),
        total_notional=float(exposure.get("total_notional") or 0.0),
        approval_valid=approval_valid,
        unified_status=unified_status,
    )

    planner = ExecutionPlanner()
    planned = planner.plan(intent, risk_state, mode="dry_run")

    executor = DryRunExecutor()
    executed = executor.execute(planned)
    return executed, risk_state


def _load_gate_stack_status(path: Path | None, *, market_id: str | None = None) -> dict:
    if path is None:
        return {}
    payload = load_optional_json(path)
    if not isinstance(payload, dict):
        return {}
    schema_version_checked = str(payload.get("schema_version") or "")
    if schema_version_checked != "gate_stack_api.v1":
        return {}
    gate_stack = _select_gate_stack_from_api(payload, market_id=market_id)
    if not isinstance(gate_stack, dict):
        return {}
    block_reasons = gate_stack.get("block_reasons")
    if not isinstance(block_reasons, list):
        block_reasons = payload.get("block_reasons") or []
    return {
        "schema_version": "unified_status.v1",
        "generated_at": payload.get("generated_at"),
        "overall_status": payload.get("overall_status"),
        "current_market": {"market_id": market_id or payload.get("market_id")},
        "gate_stack": gate_stack,
        "block_reasons": [str(item) for item in block_reasons],
        "promotion_state": _extract_promotion_state(payload, gate_stack=gate_stack),
        "contracts": {
            "gate_source": "api",
            "gate_stack_api_version": "gate_stack_api.v1",
            "gate_stack_source_schema_version": str(payload.get("source_schema_version") or "unknown"),
            "schema_version_checked": schema_version_checked,
        },
        "gate_source": "api",
        "gate_stack_api_version": "gate_stack_api.v1",
        "gate_stack_source_schema_version": str(payload.get("source_schema_version") or "unknown"),
        "gate_stack_generated_at": str(payload.get("generated_at") or ""),
        "schema_version_checked": schema_version_checked,
    }


def _select_gate_stack_from_api(payload: dict, *, market_id: str | None = None) -> dict | None:
    if market_id:
        views = payload.get("market_gate_views")
        if isinstance(views, list):
            for view in views:
                if not isinstance(view, dict):
                    continue
                if str(view.get("market_id") or "") == str(market_id):
                    return view
    gate_stack = payload.get("gate_stack")
    return gate_stack if isinstance(gate_stack, dict) else None


def _build_risk_status_payload(
    *,
    unified_status_path: Path | None,
    gate_stack_api_path: Path | None,
    market_id: str | None,
) -> dict:
    gate_stack_status = _load_gate_stack_status(gate_stack_api_path, market_id=market_id)
    if isinstance(gate_stack_status, dict) and isinstance(gate_stack_status.get("gate_stack"), dict):
        return gate_stack_status

    unified_status = load_optional_json(unified_status_path) if unified_status_path is not None else {}
    if not isinstance(unified_status, dict):
        return {}

    if isinstance(unified_status.get("gate_stack"), dict):
        contracts = unified_status.get("contracts")
        contracts_payload = contracts if isinstance(contracts, dict) else {}
        schema_version_checked = str(unified_status.get("schema_version") or "")
        promotion_state = _extract_promotion_state(unified_status)
        return {
            **unified_status,
            "promotion_state": promotion_state,
            "contracts": {
                **contracts_payload,
                "gate_source": "unified_fallback",
                "schema_version_checked": schema_version_checked,
            },
            "gate_source": "unified_fallback",
            "schema_version_checked": schema_version_checked,
        }

    return unified_status


def _build_gateway_gate_runtime_snapshot(*, market_id: str | None = None) -> dict:
    status_payload = _build_risk_status_payload(
        unified_status_path=UNIFIED_STATUS_PATH,
        gate_stack_api_path=GATE_STACK_API_PATH,
        market_id=market_id,
    )
    contracts = status_payload.get("contracts") if isinstance(status_payload.get("contracts"), dict) else {}
    gate_source = str(contracts.get("gate_source") or "local_fallback")
    promotion_state = _extract_promotion_state(status_payload)
    current_market = status_payload.get("current_market") if isinstance(status_payload.get("current_market"), dict) else {}
    probability = status_payload.get("probability") if isinstance(status_payload.get("probability"), dict) else {}
    gate_stack = status_payload.get("gate_stack") if isinstance(status_payload.get("gate_stack"), dict) else {}
    review_context = _build_review_context(market_id=market_id)
    return {
        "schema_version": "gateway_gate_runtime_snapshot.v1",
        "generated_at": str(status_payload.get("generated_at") or datetime.now(timezone.utc).isoformat()),
        "market_id": ((status_payload.get("current_market") or {}).get("market_id")),
        "gate_stack": status_payload.get("gate_stack") if isinstance(status_payload.get("gate_stack"), dict) else {},
        "block_reasons": [str(item) for item in status_payload.get("block_reasons") or []],
        "promotion_state": promotion_state,
        "review_context": review_context,
        "top_parameter_view": _build_top_parameter_view(
            current_market=current_market,
            probability=probability,
            gate_stack=gate_stack,
        ),
        "gate_source": gate_source,
        "source_schema_version": str(
            contracts.get("gate_stack_source_schema_version") or status_payload.get("schema_version") or "unknown"
        ),
        "schema_version_checked": str(contracts.get("schema_version_checked") or status_payload.get("schema_version") or "unknown"),
        "gate_stack_generated_at": str(status_payload.get("gate_stack_generated_at") or status_payload.get("generated_at") or ""),
    }


def _build_review_context(*, market_id: str | None = None) -> dict:
    latest_alert = _load_latest_json(MARKET_ALERT_EVENTS_DIR, suffix=".json")
    latest_anomaly = _load_latest_jsonl(MARKET_ANOMALY_EVENTS_DIR)
    latest_family_scan = _load_latest_json(FAMILY_SCAN_REPORTS_DIR, suffix=".json")
    source_policy = load_optional_json(SOURCE_POLICY_STATUS_PATH)
    if not isinstance(source_policy, dict):
        source_policy = {}
    return {
        "schema_version": "gateway_review_context.v1",
        "market_id": market_id,
        "latest_market_alert": latest_alert if isinstance(latest_alert, dict) else {},
        "latest_family_scan_report": latest_family_scan if isinstance(latest_family_scan, dict) else {},
        "latest_anomaly_event": latest_anomaly if isinstance(latest_anomaly, dict) else {},
        "latest_source_policy_status": source_policy,
        "monitoring_context": {
            "alert_severity": latest_alert.get("severity") if isinstance(latest_alert, dict) else None,
            "anomaly_score": latest_anomaly.get("anomaly_score") if isinstance(latest_anomaly, dict) else None,
            "source_policy_status": source_policy.get("overall_status"),
        },
        "review_summary": _summarize_review_context(latest_alert, latest_anomaly, source_policy),
    }


def _extract_promotion_state(*payloads: dict | None, gate_stack: dict | None = None) -> dict:
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        candidate = payload.get("promotion_state")
        if isinstance(candidate, dict):
            return candidate
        probability = payload.get("probability")
        if isinstance(probability, dict):
            candidate = probability.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
        validation = payload.get("validation")
        if isinstance(validation, dict):
            candidate = validation.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
    if isinstance(gate_stack, dict):
        candidate = gate_stack.get("promotion_state")
        if isinstance(candidate, dict):
            return candidate
    return {}


def _build_top_parameter_view(
    *,
    current_market: dict | None,
    probability: dict | None,
    gate_stack: dict | None,
) -> dict:
    current_market = current_market or {}
    probability = probability or {}
    gate_stack = gate_stack or {}
    market_family = str(current_market.get("market_family") or "-")
    return {
        "schema_version": "top_parameter_view.v1",
        "market_id": current_market.get("market_id"),
        "market_family": market_family,
        "market_question": current_market.get("market_question"),
        "location_name": current_market.get("location_name"),
        "target_date": current_market.get("target_date"),
        "variable_name": current_market.get("variable_name"),
        "polymarket": {
            "yes_price": current_market.get("yes_price"),
            "no_price": current_market.get("no_price"),
            "market_implied_probability": current_market.get("market_probability")
            or probability.get("market_probability"),
            "favored_side": current_market.get("favored_side"),
            "market_band": current_market.get("market_band"),
        },
        "weather": {
            "observation_value": current_market.get("observation_value"),
            "forecast_value": current_market.get("forecast_value") or current_market.get("value"),
            "unit": current_market.get("unit") or _infer_unit(market_family),
            "model_band": current_market.get("model_band"),
            "official_band": current_market.get("official_band"),
            "station_name": current_market.get("station_name"),
            "station_id": current_market.get("station_id"),
            "observed_at": current_market.get("observed_at"),
            "forecast_timestamp": current_market.get("forecast_timestamp"),
        },
        "source_contract": {
            "settlement_source_type": current_market.get("settlement_source_type"),
            "official_vs_proxy_source": current_market.get("official_vs_proxy_source"),
            "source_match_grade": current_market.get("source_match_grade"),
            "required_sources": current_market.get("required_sources"),
            "official_source_url": current_market.get("official_source_url"),
            "freshness_status": gate_stack.get("validation_freshness_status")
            or gate_stack.get("freshness_gate"),
        },
        "decision": {
            "fair_value": probability.get("fair_value"),
            "edge": probability.get("confidence_adjusted_edge") or probability.get("edge"),
            "probability_mode": probability.get("probability_mode"),
            "execution_constraint": probability.get("execution_constraint"),
            "can_execute": str(gate_stack.get("execution_gate") or "").lower() == "pass",
            "primary_block_reason": (
                [str(item) for item in gate_stack.get("block_reasons") or [] if item][0]
                if isinstance(gate_stack.get("block_reasons"), list) and gate_stack.get("block_reasons")
                else "none"
            ),
            "recommended_operator_action": gate_stack.get("recommended_operator_action"),
            "comparison_status": current_market.get("comparison_status"),
        },
    }


def _infer_unit(market_family: str) -> str:
    family = str(market_family or "").lower()
    if "temperature" in family:
        return "celsius"
    if "precipitation" in family:
        return "mm"
    if "wind" in family:
        return "m/s"
    if "snow" in family:
        return "cm"
    if "sea_ice" in family:
        return "km²"
    return "-"


def _load_latest_json(directory: Path, *, suffix: str) -> dict:
    if not directory.exists():
        return {}
    candidates = sorted(directory.glob(f"*{suffix}"), key=_sort_key, reverse=True)
    if not candidates:
        return {}
    try:
        return json.loads(candidates[0].read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_latest_jsonl(directory: Path) -> dict:
    if not directory.exists():
        return {}
    candidates = sorted(directory.glob("*.jsonl"), key=_sort_key, reverse=True)
    if not candidates:
        return {}
    try:
        lines = [line.strip() for line in candidates[0].read_text(encoding="utf-8").splitlines() if line.strip()]
    except Exception:
        return {}
    if not lines:
        return {}
    try:
        return json.loads(lines[-1])
    except Exception:
        return {}


def _summarize_review_context(
    latest_alert: dict | None,
    latest_anomaly: dict | None,
    source_policy: dict | None,
) -> str:
    alert_reason = str((latest_alert or {}).get("primary_reason") or "-")
    anomaly_reason = str((latest_anomaly or {}).get("primary_reason") or "-")
    source_status = str((source_policy or {}).get("overall_status") or "-")
    return f"alert={alert_reason}; anomaly={anomaly_reason}; source_policy={source_status}"


def _sort_key(path: Path) -> datetime:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _persist_execution_result(
    intent: OrderIntent,
    executed: ExecutionResult,
    risk_state: RiskState,
    *,
    approval_valid: bool,
    approval_reason: str | None,
    approval_record=None,
    event_type: str = "consume_pending_dry_run",
) -> Path:
    store = SQLiteStore()
    repo = ExecutionResultRepository(store)
    repo.save(executed)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    result_path = OUTPUT_DIR / f"{intent.intent_id}_execution_result.json"
    result_path.write_text(
        json.dumps(executed.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    payload: dict[str, object] = {
        "intent": intent.model_dump(),
        "approval_valid": approval_valid,
        "approval_reason": approval_reason,
        "risk_state": risk_state.model_dump(),
        "execution_result": executed.model_dump(),
    }
    if approval_record is not None:
        payload["approval_id"] = approval_record.approval_id
        payload["approval"] = {
            "approval_id": approval_record.approval_id,
            "signal_id": approval_record.signal_id,
            "operator_user_id": approval_record.operator_user_id,
            "decision": approval_record.decision,
            "expires_at": approval_record.expires_at,
            "created_at": approval_record.created_at,
            "intent_id": approval_record.intent_id,
            "is_consumed": approval_record.is_consumed,
        }

    logger = AuditLogger()
    logger.log(
        AuditEvent(
            event_id=f"audit_{intent.intent_id}",
            intent_id=intent.intent_id,
            event_type=event_type,
            payload_json=json.dumps(payload, ensure_ascii=False),
        )
    )

    return result_path


def _consume_single_pending_file(
    intent_path: Path,
    loader: IntentLoader,
) -> tuple[ExecutionResult, Path, bool]:
    payload = json.loads(intent_path.read_text(encoding="utf-8"))
    intent = OrderIntent(**payload)

    risk_cfg = load_yaml(RISK_LIMITS_PATH)
    whitelist_cfg = load_yaml(WHITELIST_PATH)

    approval_reader = ApprovalReader(db_path=APPROVAL_DB_PATH)
    approval_gate = ApprovalGate(approval_reader)
    approval_valid, approval_reason, approval_record = approval_gate.validate(intent)

    executed, risk_state = _run_dry_run_for_intent(
        intent=intent,
        risk_cfg=risk_cfg,
        whitelist_cfg=whitelist_cfg,
        approval_valid=approval_valid,
        unified_status_path=UNIFIED_STATUS_PATH,
        gate_stack_api_path=GATE_STACK_API_PATH,
    )

    if not approval_valid and risk_state.reason == "approval_invalid_or_expired":
        risk_state.reason = approval_reason or risk_state.reason

    result_path = _persist_execution_result(
        intent=intent,
        executed=executed,
        risk_state=risk_state,
        approval_valid=approval_valid,
        approval_reason=approval_reason,
        approval_record=approval_record,
    )

    if executed.accepted and approval_record is not None:
        approval_reader.mark_consumed(approval_record.approval_id)

    loader.mark_consumed(intent_path)
    return executed, result_path, approval_valid


def _consume_pending_directory(loader: IntentLoader) -> None:
    pending_files = loader.list_pending_files()
    if not pending_files:
        typer.echo(f"No pending intents found in: {loader.pending_dir}")
        return

    for intent_path in pending_files:
        executed, result_path, approval_valid = _consume_single_pending_file(intent_path, loader)
        typer.echo(f"Consumed {intent_path.name} -> {result_path.name}")
        typer.echo(f"Approval valid: {approval_valid}")
        typer.echo(f"Result: {executed.status}")


@app.command()
def dry_run_intent_file(intent_path: str) -> None:
    """Run gateway dry-run validation for one intent file without consuming it."""
    path = Path(intent_path)
    if not path.exists():
        raise FileNotFoundError(f"Missing intent file: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    intent = OrderIntent(**payload)

    risk_cfg = load_yaml(RISK_LIMITS_PATH)
    whitelist_cfg = load_yaml(WHITELIST_PATH)

    approval_reader = ApprovalReader(db_path=APPROVAL_DB_PATH)
    approval_gate = ApprovalGate(approval_reader)
    approval_valid, approval_reason, approval_record = approval_gate.validate(intent)

    executed, risk_state = _run_dry_run_for_intent(
        intent=intent,
        risk_cfg=risk_cfg,
        whitelist_cfg=whitelist_cfg,
        approval_valid=approval_valid,
        unified_status_path=UNIFIED_STATUS_PATH,
        gate_stack_api_path=GATE_STACK_API_PATH,
    )

    if not approval_valid and risk_state.reason == "approval_invalid_or_expired":
        risk_state.reason = approval_reason or risk_state.reason

    result_path = _persist_execution_result(
        intent=intent,
        executed=executed,
        risk_state=risk_state,
        approval_valid=approval_valid,
        approval_reason=approval_reason,
        approval_record=approval_record,
        event_type="dashboard_intent_file_dry_run",
    )

    typer.echo(json.dumps(
        {
            "intent_path": str(path),
            "result_path": str(result_path),
            "approval_valid": approval_valid,
            "approval_reason": approval_reason,
            "risk_state": risk_state.model_dump(),
            "execution_result": executed.model_dump(),
        },
        indent=2,
        ensure_ascii=False,
    ))


@app.command()
def consume_first_pending() -> None:
    loader = IntentLoader(pending_dir=str(PENDING_INTENTS_DIR))
    files = loader.list_pending_files()
    if not files:
        typer.echo("No pending intents found.")
        return

    first_file = files[0]
    executed, _, approval_valid = _consume_single_pending_file(first_file, loader)
    typer.echo(f"Consumed: {first_file.stem}")
    typer.echo(f"Approval valid: {approval_valid}")
    typer.echo(f"Result: {executed.status}")


@app.command()
def consume_pending_intents() -> None:
    """Scan pending intent files and run dry-runs for each."""
    loader = IntentLoader(pending_dir=str(PENDING_INTENTS_DIR))
    _consume_pending_directory(loader)


@app.command()
def dry_run_sample() -> None:
    """Run one sample dry-run execution."""
    if not SAMPLE_INTENT_PATH.exists():
        raise FileNotFoundError(f"Missing sample intent file: {SAMPLE_INTENT_PATH}")

    if not RISK_LIMITS_PATH.exists():
        raise FileNotFoundError(f"Missing risk config: {RISK_LIMITS_PATH}")

    if not WHITELIST_PATH.exists():
        raise FileNotFoundError(f"Missing whitelist config: {WHITELIST_PATH}")

    risk_cfg = load_yaml(RISK_LIMITS_PATH)
    whitelist_cfg = load_yaml(WHITELIST_PATH)
    payload = json.loads(SAMPLE_INTENT_PATH.read_text(encoding="utf-8"))
    intent = OrderIntent(**payload)
    executed, risk_state = _run_dry_run_for_intent(
        intent,
        risk_cfg,
        whitelist_cfg,
        unified_status_path=UNIFIED_STATUS_PATH,
    )
    result_path = _persist_execution_result(
        intent=intent,
        executed=executed,
        risk_state=risk_state,
        approval_valid=True,
        approval_reason=None,
    )
    SAMPLE_RESULT_PATH.write_text(
        result_path.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    typer.echo("Dry-run completed.")
    typer.echo(f"Intent ID: {intent.intent_id}")
    typer.echo(f"Result   : {executed.status}")
    typer.echo(f"Output   : {SAMPLE_RESULT_PATH}")


@app.command()
def record_human_fill(
    intent_id: str,
    market_id: str,
    side: str,
    price: float,
    size: float,
    signal_id: str = "",
    operator_user_id: int = 0,
    notes: str = "",
) -> None:
    """Record a manually placed fill. This never submits an order."""
    fill = build_human_fill_record(
        intent_id=intent_id,
        signal_id=signal_id,
        market_id=market_id,
        side=side,
        price=price,
        size=size,
        operator_user_id=operator_user_id,
        notes=notes,
    )
    fills_path, audit_path = ManualAdvisoryAuditStore(
        audit_path=MANUAL_ADVISORY_AUDIT_PATH,
        fills_path=HUMAN_FILLS_PATH,
    ).record_human_fill(fill)

    typer.echo(json.dumps(fill, indent=2, ensure_ascii=False))
    typer.echo(f"Human fill recorded to {fills_path}")
    typer.echo(f"Manual advisory audit written to {audit_path}")


@app.command()
def reconcile_human_fills() -> None:
    """Reconcile manually reported fills against the latest position snapshot."""
    report_path = HumanFillReconciler(
        fills_path=HUMAN_FILLS_PATH,
        position_snapshot_path=POSITION_SNAPSHOT_PATH,
        intent_preview_path=DASHBOARD_INTENT_PREVIEW_PATH,
    ).write_report(HUMAN_FILL_RECONCILIATION_REPORT_PATH)
    report = json.loads(report_path.read_text(encoding="utf-8"))

    typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
    typer.echo(f"Human fill reconciliation report written to {report_path}")


@app.command()
def build_position_snapshot(source_path: str = "") -> None:
    """Build a position exposure snapshot from a local read-only account positions file."""
    src = Path(source_path) if source_path.strip() else POSITION_SOURCE_PATH
    reader = PolymarketUserActivityReader(source_path=src)
    producer = PositionSnapshotProducer(reader)
    out = producer.write_snapshot(POSITION_SNAPSHOT_PATH)
    snapshot = json.loads(out.read_text(encoding="utf-8"))

    typer.echo(json.dumps(snapshot, indent=2, ensure_ascii=False))
    typer.echo(f"Position snapshot written to {out}")


@app.command()
def check_production_readiness() -> None:
    """Build a production-readiness report. This never enables live trading."""
    risk_cfg = load_yaml(RISK_LIMITS_PATH)
    whitelist_cfg = load_yaml(WHITELIST_PATH)
    execution_modes = load_yaml(EXECUTION_MODES_PATH) if EXECUTION_MODES_PATH.exists() else {}
    clob_adapter_cfg = load_yaml(CLOB_ADAPTER_PATH) if CLOB_ADAPTER_PATH.exists() else {}
    live_mode_policy = load_yaml(LIVE_MODE_POLICY_PATH) if LIVE_MODE_POLICY_PATH.exists() else {}
    model_validation = load_optional_json(MODEL_VALIDATION_REPORT_PATH)
    approval_probe = load_latest_approval_probe(APPROVAL_DB_PATH)
    position_exposure = PositionExposureReader(POSITION_SNAPSHOT_PATH).exposure_for_market(
        market_id="__portfolio__"
    )

    report = ProductionReadinessChecker().evaluate(
        risk_config=risk_cfg,
        execution_modes=execution_modes,
        whitelist_config=whitelist_cfg,
        model_validation_report=model_validation,
        approval_probe=approval_probe,
        live_mode_policy=live_mode_policy,
        position_exposure=position_exposure,
        clob_adapter_ready=is_clob_adapter_ready(clob_adapter_cfg),
    )

    PRODUCTION_READINESS_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PRODUCTION_READINESS_REPORT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    typer.echo(json.dumps(report, indent=2, ensure_ascii=False))
    typer.echo(f"Production readiness report written to {PRODUCTION_READINESS_REPORT_PATH}")


@app.command()
def export_gate_runtime_snapshot(market_id: str = "") -> None:
    """Export gateway runtime gate snapshot for cross-surface consistency checks."""
    selected_market_id = market_id.strip() or None
    payload = _build_gateway_gate_runtime_snapshot(market_id=selected_market_id)
    GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON.parent.mkdir(parents=True, exist_ok=True)
    GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    typer.echo(json.dumps(payload, indent=2, ensure_ascii=False))
    typer.echo(f"Gateway gate runtime snapshot written to {GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON}")


if __name__ == "__main__":
    app()
