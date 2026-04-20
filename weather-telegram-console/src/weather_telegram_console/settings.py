from __future__ import annotations

import os
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
