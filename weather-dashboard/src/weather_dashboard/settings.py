from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]
WORKSPACE_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = DATA_DIR / "outputs"
WATCHLIST_OVERRIDES_JSON = Path(
    os.getenv(
        "WATCHLIST_OVERRIDES_JSON",
        str(OUTPUT_DIR / "market_watchlist_overrides.json"),
    )
)
PINNED_MARKET_OVERRIDE_JSON = Path(
    os.getenv(
        "PINNED_MARKET_OVERRIDE_JSON",
        str(OUTPUT_DIR / "pinned_market_override.json"),
    )
)
RECENT_MARKETS_JSON = Path(
    os.getenv(
        "RECENT_MARKETS_JSON",
        str(OUTPUT_DIR / "recent_markets.json"),
    )
)
WATCHLIST_REMOVED_JSON = Path(
    os.getenv(
        "WATCHLIST_REMOVED_JSON",
        str(OUTPUT_DIR / "market_watchlist_removed.json"),
    )
)
EXECUTION_PENDING_INTENTS_DIR = Path(
    os.getenv(
        "EXECUTION_PENDING_INTENTS_DIR",
        str(WORKSPACE_DIR / "weather-telegram-console" / "data" / "outputs" / "pending_intents"),
    )
)
EXECUTION_DASHBOARD_INTENT_JSON = Path(
    os.getenv(
        "EXECUTION_DASHBOARD_INTENT_JSON",
        str(WORKSPACE_DIR / "weather-execution-gateway" / "data" / "outputs" / "dashboard_intent_preview.json"),
    )
)
EXECUTION_PRODUCTION_READINESS_JSON = Path(
    os.getenv(
        "EXECUTION_PRODUCTION_READINESS_JSON",
        str(WORKSPACE_DIR / "weather-execution-gateway" / "data" / "outputs" / "production_readiness_report.json"),
    )
)
HUMAN_FILL_RECONCILIATION_REPORT_JSON = Path(
    os.getenv(
        "HUMAN_FILL_RECONCILIATION_REPORT_JSON",
        str(
            WORKSPACE_DIR
            / "weather-execution-gateway"
            / "data"
            / "outputs"
            / "human_fill_reconciliation_report.json"
        ),
    )
)
POSITION_SNAPSHOT_JSON = Path(
    os.getenv(
        "POSITION_SNAPSHOT_JSON",
        str(WORKSPACE_DIR / "weather-execution-gateway" / "data" / "outputs" / "position_snapshot.json"),
    )
)
GATE_STACK_OPS_ALERTS_JSONL = Path(
    os.getenv(
        "GATE_STACK_OPS_ALERTS_JSONL",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "gate_stack_ops_alerts.jsonl"
        ),
    )
)
MARKET_ALERT_EVENTS_DIR = Path(
    os.getenv(
        "MARKET_ALERT_EVENTS_DIR",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "market_alert_events"
        ),
    )
)
FAMILY_SCAN_REPORTS_DIR = Path(
    os.getenv(
        "FAMILY_SCAN_REPORTS_DIR",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "family_scan_reports"
        ),
    )
)
MARKET_ANOMALY_EVENTS_DIR = Path(
    os.getenv(
        "MARKET_ANOMALY_EVENTS_DIR",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "market_anomaly_events"
        ),
    )
)
SCANNER_OUTPUT_DIR = Path(
    os.getenv(
        "SCANNER_OUTPUT_DIR",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "scanner"),
    )
)
ALERTS_OUTPUT_DIR = Path(
    os.getenv(
        "ALERTS_OUTPUT_DIR",
        str(WORKSPACE_DIR / "weather-comparison-engine" / "data" / "outputs" / "alerts"),
    )
)
MARKET_UNIVERSE_SNAPSHOT_JSON = Path(
    os.getenv(
        "MARKET_UNIVERSE_SNAPSHOT_JSON",
        str(SCANNER_OUTPUT_DIR / "market_universe_snapshot.json"),
    )
)
EVIDENCE_SCAN_SNAPSHOT_JSON = Path(
    os.getenv(
        "EVIDENCE_SCAN_SNAPSHOT_JSON",
        str(SCANNER_OUTPUT_DIR / "evidence_scan_snapshot.json"),
    )
)
SCANNER_STATUS_JSON = Path(
    os.getenv(
        "SCANNER_STATUS_JSON",
        str(SCANNER_OUTPUT_DIR / "scanner_status.json"),
    )
)
SCAN_QUEUE_STATUS_JSON = Path(
    os.getenv(
        "SCAN_QUEUE_STATUS_JSON",
        str(ALERTS_OUTPUT_DIR / "alert_queue_status.json"),
    )
)
MARKET_ALERT_EVENTS_JSON = Path(
    os.getenv(
        "MARKET_ALERT_EVENTS_JSON",
        str(ALERTS_OUTPUT_DIR / "market_alert_events.json"),
    )
)
FAMILY_ANOMALY_SUMMARY_JSON = Path(
    os.getenv(
        "FAMILY_ANOMALY_SUMMARY_JSON",
        str(ALERTS_OUTPUT_DIR / "family_anomaly_summary.json"),
    )
)
SCANNER_OPS_ALERTS_JSON = Path(
    os.getenv(
        "SCANNER_OPS_ALERTS_JSON",
        str(ALERTS_OUTPUT_DIR / "scanner_ops_alerts.json"),
    )
)
SOURCE_POLICY_STATUS_JSON = Path(
    os.getenv(
        "SOURCE_POLICY_STATUS_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "source_policy_status.json"
        ),
    )
)
TELEGRAM_OPS_NOTIFICATIONS_JSONL = Path(
    os.getenv(
        "TELEGRAM_OPS_NOTIFICATIONS_JSONL",
        str(
            WORKSPACE_DIR
            / "weather-telegram-console"
            / "data"
            / "outputs"
            / "telegram_ops_notifications.jsonl"
        ),
    )
)
TELEGRAM_OPS_DELIVERY_LOG_JSONL = Path(
    os.getenv(
        "TELEGRAM_OPS_DELIVERY_LOG_JSONL",
        str(
            WORKSPACE_DIR
            / "weather-telegram-console"
            / "data"
            / "outputs"
            / "telegram_ops_delivery_log.jsonl"
        ),
    )
)
MANUAL_ADVISORY_AUDIT_JSONL = Path(
    os.getenv(
        "MANUAL_ADVISORY_AUDIT_JSONL",
        str(WORKSPACE_DIR / "weather-execution-gateway" / "data" / "outputs" / "manual_advisory_audit.jsonl"),
    )
)
TELEGRAM_APPROVAL_SIGNAL_JSON = Path(
    os.getenv(
        "TELEGRAM_APPROVAL_SIGNAL_JSON",
        str(WORKSPACE_DIR / "weather-telegram-console" / "data" / "outputs" / "dashboard_approval_signal.json"),
    )
)
EXECUTION_WHITELIST_YAML = Path(
    os.getenv(
        "EXECUTION_WHITELIST_YAML",
        str(WORKSPACE_DIR / "weather-execution-gateway" / "config" / "whitelist_markets.yaml"),
    )
)
EXECUTION_GATEWAY_DIR = Path(
    os.getenv(
        "EXECUTION_GATEWAY_DIR",
        str(WORKSPACE_DIR / "weather-execution-gateway"),
    )
)
EXECUTION_APPROVAL_DB_PATH = Path(
    os.getenv(
        "EXECUTION_APPROVAL_DB_PATH",
        str(WORKSPACE_DIR / "weather-telegram-console" / "data" / "outputs" / "weather_telegram_console.db"),
    )
)

# live-first defaults
DASHBOARD_ROWS_JSON = Path(
    os.getenv(
        "DASHBOARD_ROWS_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "latest_dashboard_rows.json"
        ),
    )
)
OPPORTUNITY_BOARD_VIEW_JSON = Path(
    os.getenv(
        "OPPORTUNITY_BOARD_VIEW_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "opportunity_board_view.json"
        ),
    )
)
OPERATIONS_MONITOR_OUTPUT_DIR = Path(
    os.getenv(
        "OPERATIONS_MONITOR_OUTPUT_DIR",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "operations_monitor",
        ),
    )
)
OPERATIONS_MONITOR_VIEW_JSON = Path(
    os.getenv(
        "OPERATIONS_MONITOR_VIEW_JSON",
        str(OPERATIONS_MONITOR_OUTPUT_DIR / "operations_monitor_view.json"),
    )
)
OPERATIONS_MONITOR_SUMMARY_JSON = Path(
    os.getenv(
        "OPERATIONS_MONITOR_SUMMARY_JSON",
        str(OPERATIONS_MONITOR_OUTPUT_DIR / "operations_monitor_summary.json"),
    )
)
VALIDATION_OUTPUT_DIR = Path(
    os.getenv(
        "VALIDATION_OUTPUT_DIR",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "validation",
        ),
    )
)
ADVANCED_ANOMALY_OUTPUT_DIR = Path(
    os.getenv(
        "ADVANCED_ANOMALY_OUTPUT_DIR",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "anomaly",
        ),
    )
)

SIGNAL_JSON = Path(
    os.getenv(
        "SIGNAL_JSON",
        str(
            WORKSPACE_DIR
            / "weather-signal-engine"
            / "data"
            / "outputs"
            / "sample_signal_event.json"
        ),
    )
)

MARKET_BUNDLES_JSON = Path(
    os.getenv(
        "MARKET_BUNDLES_JSON",
        str(
            WORKSPACE_DIR
            / "polymarket-weather-ingest"
            / "data"
            / "outputs"
            / "weather_realtime_bundles.json"
        ),
    )
)

TIMESERIES_JSON = Path(
    os.getenv("TIMESERIES_JSON", str(OUTPUT_DIR / "sample_timeseries.json"))
)

RULEBOOK_JSON = Path(
    os.getenv(
        "RULEBOOK_JSON",
        str(
            WORKSPACE_DIR
            / "weather-rules-research"
            / "data"
            / "outputs"
            / "sample_rulebook.json"
        ),
    )
)

BIAS_REPORT_CSV = Path(
    os.getenv(
        "BIAS_REPORT_CSV",
        str(
            WORKSPACE_DIR
            / "weather-rules-research"
            / "data"
            / "outputs"
            / "sample_forecast_bias_summary.csv"
        ),
    )
)

COMPARISON_HISTORY_JSON = Path(
    os.getenv(
        "COMPARISON_HISTORY_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "comparison_history.json"
        ),
    )
)
MONITORING_STATUS_JSON = Path(
    os.getenv(
        "MONITORING_STATUS_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "monitoring_status.json"
        ),
    )
)
UNIFIED_STATUS_JSON = Path(
    os.getenv(
        "UNIFIED_STATUS_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "unified_status.json"
        ),
    )
)
GATE_STACK_API_JSON = Path(
    os.getenv(
        "GATE_STACK_API_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "gate_stack_api.json"
        ),
    )
)
OPERATOR_MARKET_CONTEXT_JSON = Path(
    os.getenv(
        "OPERATOR_MARKET_CONTEXT_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "operator_market_context.json"
        ),
    )
)
PAGE_CONTEXT_JSON = Path(
    os.getenv(
        "PAGE_CONTEXT_JSON",
        str(
            WORKSPACE_DIR
            / "weather-dashboard"
            / "data"
            / "outputs"
            / "page_context.json"
        ),
    )
)
UI_ACTION_VISIBILITY_POLICY_JSON = Path(
    os.getenv(
        "UI_ACTION_VISIBILITY_POLICY_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "registries"
            / "ui_policy_registry"
            / "action_visibility_policy.json"
        ),
    )
)

REALTIME_MARKET_JSON = Path(
    os.getenv(
        "REALTIME_MARKET_JSON",
        str(
            WORKSPACE_DIR
            / "polymarket-weather-ingest"
            / "data"
            / "outputs"
            / "market_realtime_simple.json"
        ),
    )
)

REALTIME_MARKET_SNAPSHOTS_GLOB = os.getenv(
    "REALTIME_MARKET_SNAPSHOTS_GLOB",
    str(
        WORKSPACE_DIR
        / "polymarket-weather-ingest"
        / "data"
        / "outputs"
        / "market_realtime_simple_*.json"
    ),
)

PINNED_MARKET_ID = os.getenv("PINNED_MARKET_ID") or None

REALTIME_FORECAST_JSON = Path(
    os.getenv(
        "REALTIME_FORECAST_JSON",
        str(
            WORKSPACE_DIR
            / "weather-rules-research"
            / "data"
            / "outputs"
            / "forecast_realtime_snapshot.json"
        ),
    )
)

REALTIME_FORECAST_SNAPSHOTS_GLOB = os.getenv(
    "REALTIME_FORECAST_SNAPSHOTS_GLOB",
    str(
        WORKSPACE_DIR
        / "weather-rules-research"
        / "data"
        / "outputs"
        / "forecast_realtime_snapshots"
        / "forecast_realtime_snapshot_*.json"
    ),
)

SHANGHAI_JOINED_HISTORY_JSON = Path(
    os.getenv(
        "SHANGHAI_JOINED_HISTORY_JSON",
        str(
            WORKSPACE_DIR
            / "weather-rules-research"
            / "data"
            / "outputs"
            / "sample_joined_shanghai.json"
        ),
    )
)

WUNDERGROUND_SHANGHAI_CACHE_JSON = Path(
    os.getenv(
        "WUNDERGROUND_SHANGHAI_CACHE_JSON",
        str(OUTPUT_DIR / "wunderground_shanghai_snapshot.json"),
    )
)

RESOLVER_REPORT_JSON = Path(
    os.getenv(
        "RESOLVER_REPORT_JSON",
        str(
            WORKSPACE_DIR
            / "weather-rules-research"
            / "data"
            / "outputs"
            / "resolver_report.json"
        ),
    )
)

PROBABILITY_STATES_DIR = Path(
    os.getenv(
        "PROBABILITY_STATES_DIR",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "probability_states"
        ),
    )
)

CALIBRATION_REPORT_JSON = Path(
    os.getenv(
        "CALIBRATION_REPORT_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "calibration_report.json"
        ),
    )
)

BACKTEST_REPORT_JSON = Path(
    os.getenv(
        "BACKTEST_REPORT_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "backtest_report.json"
        ),
    )
)

MODEL_VALIDATION_REPORT_JSON = Path(
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
VALIDATION_FRESHNESS_STATUS_JSON = Path(
    os.getenv(
        "VALIDATION_FRESHNESS_STATUS_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "validation_freshness_status.json"
        ),
    )
)
LABEL_COVERAGE_REPORT_JSON = Path(
    os.getenv(
        "LABEL_COVERAGE_REPORT_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "label_coverage_report.json"
        ),
    )
)
TRAINING_SAMPLES_JSONL = Path(
    os.getenv(
        "TRAINING_SAMPLES_JSONL",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "training_samples.jsonl"
        ),
    )
)

PROBABILITY_SHADOW_REPORT_JSON = Path(
    os.getenv(
        "PROBABILITY_SHADOW_REPORT_JSON",
        str(
            WORKSPACE_DIR
            / "weather-comparison-engine"
            / "data"
            / "outputs"
            / "probability_shadow_report.json"
        ),
    )
)

GAMMA_API_BASE_URL = os.getenv(
    "GAMMA_API_BASE_URL",
    "https://gamma-api.polymarket.com",
)

GAMMA_SEARCH_LIMIT = int(os.getenv("GAMMA_SEARCH_LIMIT", "20"))
