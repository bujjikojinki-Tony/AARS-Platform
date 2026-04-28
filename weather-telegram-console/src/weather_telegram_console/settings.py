from __future__ import annotations

import os
from urllib.parse import urlsplit, urlunsplit
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "outputs"
DEFAULT_SIGNAL_JSON_PATH = (
    WORKSPACE_DIR / "weather-signal-engine" / "data" / "outputs" / "sample_signal_event.json"
)
DEFAULT_DASHBOARD_APPROVAL_SIGNAL_JSON_PATH = OUTPUT_DIR / "dashboard_approval_signal.json"

for path in [DATA_DIR, OUTPUT_DIR]:
    path.mkdir(parents=True, exist_ok=True)


def get_bot_token() -> str:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN")
    return token


def _first_env(*names: str) -> str | None:
    for name in names:
        raw = os.getenv(name)
        if raw and raw.strip():
            return raw.strip()
    return None


def _redact_url(raw_url: str | None) -> str:
    if not raw_url:
        return "-"
    parts = urlsplit(raw_url)
    if not parts.scheme or not parts.netloc:
        return raw_url
    netloc = parts.hostname or ""
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, parts.query, parts.fragment))


def get_telegram_api_base_url() -> str | None:
    return _first_env("TELEGRAM_API_BASE_URL", "TELEGRAM_BOT_API_BASE_URL")


def get_telegram_proxy() -> str | None:
    return _first_env("TELEGRAM_PROXY", "HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy")


def get_telegram_get_updates_proxy() -> str | None:
    return _first_env("TELEGRAM_GET_UPDATES_PROXY") or get_telegram_proxy()


def describe_telegram_network_settings() -> dict[str, str]:
    base_url = get_telegram_api_base_url()
    proxy = get_telegram_proxy()
    updates_proxy = get_telegram_get_updates_proxy()
    return {
        "base_url": base_url or "default",
        "proxy": _redact_url(proxy),
        "get_updates_proxy": _redact_url(updates_proxy),
    }


def get_admin_allowlist() -> tuple[set[int], set[str]]:
    raw = os.getenv("TELEGRAM_ADMIN_USER_IDS", "")
    if not raw.strip():
        return set(), set()

    admin_user_ids: set[int] = set()
    admin_usernames: set[str] = set()
    for value in raw.split(","):
        token = value.strip()
        if not token:
            continue
        if token.lstrip("-").isdigit():
            admin_user_ids.add(int(token))
            continue
        admin_usernames.add(token.lstrip("@").lower())

    return admin_user_ids, admin_usernames


def get_signal_json_path() -> Path:
    raw = os.getenv("SIGNAL_JSON_PATH")
    if raw:
        configured = Path(raw)
        if not configured.is_absolute():
            configured = BASE_DIR / configured
        if configured.exists():
            return configured

    dashboard_raw = os.getenv("DASHBOARD_APPROVAL_SIGNAL_JSON_PATH")
    dashboard_path = Path(dashboard_raw) if dashboard_raw else DEFAULT_DASHBOARD_APPROVAL_SIGNAL_JSON_PATH
    if not dashboard_path.is_absolute():
        dashboard_path = BASE_DIR / dashboard_path
    if dashboard_path.exists():
        return dashboard_path

    if DEFAULT_SIGNAL_JSON_PATH.exists():
        return DEFAULT_SIGNAL_JSON_PATH

    return OUTPUT_DIR / "sample_signal_event.json"


def get_execution_intent_path() -> Path:
    raw = os.getenv(
        "EXECUTION_INTENT_PATH",
        str(WORKSPACE_DIR / "weather-execution-gateway" / "data" / "outputs" / "sample_intent.json"),
    )
    return Path(raw)


def get_pending_intents_dir() -> Path:
    raw = os.getenv(
        "PENDING_INTENTS_DIR",
        str(OUTPUT_DIR / "pending_intents"),
    )
    return Path(raw)


def get_dashboard_intent_preview_path() -> Path:
    raw = os.getenv(
        "DASHBOARD_INTENT_PREVIEW_PATH",
        str(WORKSPACE_DIR / "weather-execution-gateway" / "data" / "outputs" / "dashboard_intent_preview.json"),
    )
    return Path(raw)


def get_manual_advisory_audit_path() -> Path:
    raw = os.getenv(
        "MANUAL_ADVISORY_AUDIT_JSONL",
        str(
            WORKSPACE_DIR
            / "weather-execution-gateway"
            / "data"
            / "outputs"
            / "manual_advisory_audit.jsonl"
        ),
    )
    return Path(raw)


def get_execution_gateway_dir() -> Path:
    raw = os.getenv(
        "EXECUTION_GATEWAY_DIR",
        str(WORKSPACE_DIR / "weather-execution-gateway"),
    )
    return Path(raw)


def get_execution_result_path() -> Path:
    raw = os.getenv(
        "EXECUTION_RESULT_PATH",
        str(WORKSPACE_DIR / "weather-execution-gateway" / "data" / "outputs" / "sample_execution_result.json"),
    )
    return Path(raw)


def get_unified_status_path() -> Path:
    raw = os.getenv(
        "UNIFIED_STATUS_JSON_PATH",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "unified_status.json"),
    )
    return Path(raw)


def get_gate_stack_api_path() -> Path:
    raw = os.getenv(
        "GATE_STACK_API_JSON_PATH",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "gate_stack_api.json"),
    )
    return Path(raw)


def get_operator_market_context_path() -> Path:
    raw = os.getenv(
        "OPERATOR_MARKET_CONTEXT_JSON",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "operator_market_context.json"),
    )
    return Path(raw)


def get_monitoring_status_path() -> Path:
    raw = os.getenv(
        "MONITORING_STATUS_JSON_PATH",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "monitoring_status.json"),
    )
    return Path(raw)


def get_production_readiness_path() -> Path:
    raw = os.getenv(
        "PRODUCTION_READINESS_JSON_PATH",
        str(WORKSPACE_DIR / "weather-execution-gateway" / "data" / "outputs" / "production_readiness_report.json"),
    )
    return Path(raw)


def get_latest_dashboard_rows_path() -> Path:
    raw = os.getenv(
        "LATEST_DASHBOARD_ROWS_JSON_PATH",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "latest_dashboard_rows.json"),
    )
    return Path(raw)


def get_opportunity_board_view_path() -> Path:
    raw = os.getenv(
        "OPPORTUNITY_BOARD_VIEW_JSON_PATH",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "opportunity_board_view.json"),
    )
    return Path(raw)


def get_operations_monitor_output_dir() -> Path:
    raw = os.getenv(
        "OPERATIONS_MONITOR_OUTPUT_DIR",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "operations_monitor"),
    )
    return Path(raw)


def get_operations_monitor_view_path() -> Path:
    raw = os.getenv(
        "OPERATIONS_MONITOR_VIEW_JSON",
        str(get_operations_monitor_output_dir() / "operations_monitor_view.json"),
    )
    return Path(raw)


def get_operations_monitor_summary_path() -> Path:
    raw = os.getenv(
        "OPERATIONS_MONITOR_SUMMARY_JSON",
        str(get_operations_monitor_output_dir() / "operations_monitor_summary.json"),
    )
    return Path(raw)


def get_model_validation_report_path() -> Path:
    raw = os.getenv(
        "MODEL_VALIDATION_REPORT_JSON",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "model_validation_report.json"),
    )
    return Path(raw)


def get_label_coverage_report_path() -> Path:
    raw = os.getenv(
        "LABEL_COVERAGE_REPORT_JSON",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "label_coverage_report.json"),
    )
    return Path(raw)


def get_validation_freshness_status_path() -> Path:
    raw = os.getenv(
        "VALIDATION_FRESHNESS_STATUS_JSON",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "validation_freshness_status.json"),
    )
    return Path(raw)


def get_opportunity_board_city_dir_path() -> Path:
    raw = os.getenv(
        "OPPORTUNITY_BOARD_CITY_DIR_PATH",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "opportunity_board_cities"),
    )
    return Path(raw)


def get_validation_output_dir() -> Path:
    raw = os.getenv(
        "VALIDATION_OUTPUT_DIR",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "validation"),
    )
    return Path(raw)


def get_advanced_anomaly_output_dir() -> Path:
    raw = os.getenv(
        "ADVANCED_ANOMALY_OUTPUT_DIR",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "anomaly"),
    )
    return Path(raw)


def get_scanner_output_dir() -> Path:
    raw = os.getenv(
        "SCANNER_OUTPUT_DIR",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "scanner"),
    )
    return Path(raw)


def get_alerts_output_dir() -> Path:
    raw = os.getenv(
        "ALERTS_OUTPUT_DIR",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "alerts"),
    )
    return Path(raw)


def get_market_universe_snapshot_path() -> Path:
    raw = os.getenv(
        "MARKET_UNIVERSE_SNAPSHOT_JSON",
        str(get_scanner_output_dir() / "market_universe_snapshot.json"),
    )
    return Path(raw)


def get_evidence_scan_snapshot_path() -> Path:
    raw = os.getenv(
        "EVIDENCE_SCAN_SNAPSHOT_JSON",
        str(get_scanner_output_dir() / "evidence_scan_snapshot.json"),
    )
    return Path(raw)


def get_scanner_status_path() -> Path:
    raw = os.getenv(
        "SCANNER_STATUS_JSON",
        str(get_scanner_output_dir() / "scanner_status.json"),
    )
    return Path(raw)


def get_scan_queue_status_path() -> Path:
    raw = os.getenv(
        "SCAN_QUEUE_STATUS_JSON",
        str(get_alerts_output_dir() / "alert_queue_status.json"),
    )
    return Path(raw)


def get_market_alert_events_path() -> Path:
    raw = os.getenv(
        "MARKET_ALERT_EVENTS_JSON",
        str(get_alerts_output_dir() / "market_alert_events.json"),
    )
    return Path(raw)


def get_family_anomaly_summary_path() -> Path:
    raw = os.getenv(
        "FAMILY_ANOMALY_SUMMARY_JSON",
        str(get_alerts_output_dir() / "family_anomaly_summary.json"),
    )
    return Path(raw)


def get_scanner_ops_alerts_path() -> Path:
    raw = os.getenv(
        "SCANNER_OPS_ALERTS_JSON",
        str(get_alerts_output_dir() / "scanner_ops_alerts.json"),
    )
    return Path(raw)


def get_comparison_history_path() -> Path:
    raw = os.getenv(
        "COMPARISON_HISTORY_JSON_PATH",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "comparison_history.json"),
    )
    return Path(raw)


def get_approval_ttl_minutes() -> int:
    raw = os.getenv("APPROVAL_TTL_MINUTES", "15")
    return int(raw)


def get_gate_stack_ops_alerts_path() -> Path:
    raw = os.getenv(
        "GATE_STACK_OPS_ALERTS_JSONL",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "gate_stack_ops_alerts.jsonl"),
    )
    return Path(raw)


def get_market_alert_events_dir() -> Path:
    raw = os.getenv(
        "MARKET_ALERT_EVENTS_DIR",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "market_alert_events"),
    )
    return Path(raw)


def get_family_scan_reports_dir() -> Path:
    raw = os.getenv(
        "FAMILY_SCAN_REPORTS_DIR",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "family_scan_reports"),
    )
    return Path(raw)


def get_market_anomaly_events_dir() -> Path:
    raw = os.getenv(
        "MARKET_ANOMALY_EVENTS_DIR",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "market_anomaly_events"),
    )
    return Path(raw)


def get_source_policy_status_path() -> Path:
    raw = os.getenv(
        "SOURCE_POLICY_STATUS_JSON",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "source_policy_status.json"),
    )
    return Path(raw)


def get_ops_alert_bridge_state_path() -> Path:
    raw = os.getenv(
        "OPS_ALERT_BRIDGE_STATE_JSON",
        str(OUTPUT_DIR / "ops_alert_bridge_state.json"),
    )
    return Path(raw)


def get_telegram_ops_notifications_path() -> Path:
    raw = os.getenv(
        "TELEGRAM_OPS_NOTIFICATIONS_JSONL",
        str(OUTPUT_DIR / "telegram_ops_notifications.jsonl"),
    )
    return Path(raw)


def get_ops_alert_bridge_max_batch() -> int:
    raw = os.getenv("OPS_ALERT_BRIDGE_MAX_BATCH", "50")
    return int(raw)


def get_telegram_ops_delivery_log_path() -> Path:
    raw = os.getenv(
        "TELEGRAM_OPS_DELIVERY_LOG_JSONL",
        str(OUTPUT_DIR / "telegram_ops_delivery_log.jsonl"),
    )
    return Path(raw)


def get_ops_dispatch_max_batch() -> int:
    raw = os.getenv("OPS_DISPATCH_MAX_BATCH", "20")
    return int(raw)


def get_telegram_gate_runtime_snapshot_path() -> Path:
    raw = os.getenv(
        "TELEGRAM_GATE_RUNTIME_SNAPSHOT_JSON",
        str(OUTPUT_DIR / "telegram_gate_runtime_snapshot.json"),
    )
    return Path(raw)
