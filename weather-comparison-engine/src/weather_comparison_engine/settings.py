from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "inputs"
OUTPUT_DIR = DATA_DIR / "outputs"
REGISTRIES_DIR = DATA_DIR / "registries"
MEASUREMENT_REGISTRY_DIR = REGISTRIES_DIR / "measurement_registry"
OPPORTUNITY_POLICY_REGISTRY_DIR = REGISTRIES_DIR / "opportunity_policy_registry"
VALIDATION_OUTPUT_DIR = Path(
    os.getenv(
        "VALIDATION_OUTPUT_DIR",
        str(OUTPUT_DIR / "validation"),
    )
)
ADVANCED_ANOMALY_OUTPUT_DIR = Path(
    os.getenv(
        "ADVANCED_ANOMALY_OUTPUT_DIR",
        str(OUTPUT_DIR / "anomaly"),
    )
)
SCANNER_OUTPUT_DIR = Path(
    os.getenv(
        "SCANNER_OUTPUT_DIR",
        str(OUTPUT_DIR / "scanner"),
    )
)
ALERTS_OUTPUT_DIR = Path(
    os.getenv(
        "ALERTS_OUTPUT_DIR",
        str(OUTPUT_DIR / "alerts"),
    )
)
SCAN_QUEUE_STATUS_JSON = Path(
    os.getenv(
        "SCAN_QUEUE_STATUS_JSON",
        str(ALERTS_OUTPUT_DIR / "alert_queue_status.json"),
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

for path in [DATA_DIR, INPUT_DIR, OUTPUT_DIR, REGISTRIES_DIR, MEASUREMENT_REGISTRY_DIR, OPPORTUNITY_POLICY_REGISTRY_DIR]:
    path.mkdir(parents=True, exist_ok=True)
for path in [VALIDATION_OUTPUT_DIR, ADVANCED_ANOMALY_OUTPUT_DIR]:
    path.mkdir(parents=True, exist_ok=True)

REALTIME_MARKET_JSON = Path(
    os.getenv(
        "REALTIME_MARKET_JSON",
        "../polymarket-weather-ingest/data/outputs/market_realtime_simple.json",
    )
)

REALTIME_FORECAST_JSON = Path(
    os.getenv(
        "REALTIME_FORECAST_JSON",
        "../weather-rules-research/data/outputs/forecast_realtime_snapshot.json",
    )
)

REALTIME_FORECAST_SNAPSHOTS_GLOB = os.getenv(
    "REALTIME_FORECAST_SNAPSHOTS_GLOB",
    "../weather-rules-research/data/outputs/forecast_realtime_snapshots/forecast_realtime_snapshot_*.json",
)

COMPARISON_HISTORY_JSON = Path(
    os.getenv(
        "COMPARISON_HISTORY_JSON",
        str(OUTPUT_DIR / "comparison_history.json"),
    )
)

LATEST_DASHBOARD_ROWS_JSON = Path(
    os.getenv(
        "LATEST_DASHBOARD_ROWS_JSON",
        str(OUTPUT_DIR / "latest_dashboard_rows.json"),
    )
)
OPPORTUNITY_BOARD_VIEW_JSON = Path(
    os.getenv(
        "OPPORTUNITY_BOARD_VIEW_JSON",
        str(OUTPUT_DIR / "opportunity_board_view.json"),
    )
)
OPPORTUNITY_BOARD_OUTPUT_DIR = Path(
    os.getenv(
        "OPPORTUNITY_BOARD_OUTPUT_DIR",
        str(OUTPUT_DIR / "opportunity_board"),
    )
)
OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON = Path(
    os.getenv(
        "OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON",
        str(OPPORTUNITY_BOARD_OUTPUT_DIR / "opportunity_board_view.json"),
    )
)
OPPORTUNITY_BOARD_SUMMARY_JSON = Path(
    os.getenv(
        "OPPORTUNITY_BOARD_SUMMARY_JSON",
        str(OPPORTUNITY_BOARD_OUTPUT_DIR / "opportunity_board_summary.json"),
    )
)
OPPORTUNITY_BOARD_EXPLANATIONS_JSON = Path(
    os.getenv(
        "OPPORTUNITY_BOARD_EXPLANATIONS_JSON",
        str(OUTPUT_DIR / "opportunity_board_explanations.json"),
    )
)
OPPORTUNITY_BOARD_CANONICAL_EXPLANATIONS_JSON = Path(
    os.getenv(
        "OPPORTUNITY_BOARD_CANONICAL_EXPLANATIONS_JSON",
        str(OPPORTUNITY_BOARD_OUTPUT_DIR / "opportunity_explanations.json"),
    )
)
OPPORTUNITY_BOARD_FEATURE_ROWS_JSON = Path(
    os.getenv(
        "OPPORTUNITY_BOARD_FEATURE_ROWS_JSON",
        str(OUTPUT_DIR / "opportunity_board_feature_rows.json"),
    )
)
OPPORTUNITY_BOARD_CANONICAL_FEATURE_ROWS_JSON = Path(
    os.getenv(
        "OPPORTUNITY_BOARD_CANONICAL_FEATURE_ROWS_JSON",
        str(OPPORTUNITY_BOARD_OUTPUT_DIR / "opportunity_feature_rows.json"),
    )
)
OPPORTUNITY_BOARD_CITY_DIR = Path(
    os.getenv(
        "OPPORTUNITY_BOARD_CITY_DIR",
        str(OUTPUT_DIR / "opportunity_board_cities"),
    )
)
OPPORTUNITY_SEED_LIST_JSON = Path(
    os.getenv(
        "OPPORTUNITY_SEED_LIST_JSON",
        str(INPUT_DIR / "opportunity_seeds" / "opportunity_seed_list.json"),
    )
)
OPPORTUNITY_SCORING_POLICY_JSON = Path(
    os.getenv(
        "OPPORTUNITY_SCORING_POLICY_JSON",
        str(OPPORTUNITY_POLICY_REGISTRY_DIR / "opportunity_scoring_policy.json"),
    )
)
DIFFICULTY_SCORING_POLICY_JSON = Path(
    os.getenv(
        "DIFFICULTY_SCORING_POLICY_JSON",
        str(OPPORTUNITY_POLICY_REGISTRY_DIR / "difficulty_scoring_policy.json"),
    )
)
MODEL_RECOMMENDATION_POLICY_JSON = Path(
    os.getenv(
        "MODEL_RECOMMENDATION_POLICY_JSON",
        str(OPPORTUNITY_POLICY_REGISTRY_DIR / "model_recommendation_policy.json"),
    )
)
ACTION_MAPPING_POLICY_JSON = Path(
    os.getenv(
        "ACTION_MAPPING_POLICY_JSON",
        str(OPPORTUNITY_POLICY_REGISTRY_DIR / "action_mapping_policy.json"),
    )
)
FRESHNESS_MAPPING_POLICY_JSON = Path(
    os.getenv(
        "FRESHNESS_MAPPING_POLICY_JSON",
        str(OPPORTUNITY_POLICY_REGISTRY_DIR / "freshness_mapping_policy.json"),
    )
)
SOURCE_PRECISION_POLICY_JSON = Path(
    os.getenv(
        "SOURCE_PRECISION_POLICY_JSON",
        str(OPPORTUNITY_POLICY_REGISTRY_DIR / "source_precision_policy.json"),
    )
)
BUY_SELL_DECISION_POLICY_JSON = Path(
    os.getenv(
        "BUY_SELL_DECISION_POLICY_JSON",
        str(OPPORTUNITY_POLICY_REGISTRY_DIR / "buy_sell_decision_policy.json"),
    )
)

SCHEMA_VALIDATION_REPORT_JSON = Path(
    os.getenv(
        "SCHEMA_VALIDATION_REPORT_JSON",
        str(OUTPUT_DIR / "schema_validation_report.json"),
    )
)

RESOLVER_REPORT_JSON = Path(
    os.getenv(
        "RESOLVER_REPORT_JSON",
        "../weather-rules-research/data/outputs/resolver_report.json",
    )
)
MARKET_ALERT_EVENTS_DIR = Path(
    os.getenv(
        "MARKET_ALERT_EVENTS_DIR",
        str(OUTPUT_DIR / "market_alert_events"),
    )
)
FAMILY_SCAN_REPORTS_DIR = Path(
    os.getenv(
        "FAMILY_SCAN_REPORTS_DIR",
        str(OUTPUT_DIR / "family_scan_reports"),
    )
)
MARKET_ANOMALY_EVENTS_DIR = Path(
    os.getenv(
        "MARKET_ANOMALY_EVENTS_DIR",
        str(OUTPUT_DIR / "market_anomaly_events"),
    )
)
SOURCE_POLICY_REGISTRY_JSON = Path(
    os.getenv(
        "SOURCE_POLICY_REGISTRY_JSON",
        str(REGISTRIES_DIR / "source_policy_registry.json"),
    )
)
UNIT_REGISTRY_JSON = Path(
    os.getenv(
        "UNIT_REGISTRY_JSON",
        str(MEASUREMENT_REGISTRY_DIR / "unit_registry.json"),
    )
)
PRECISION_POLICY_REGISTRY_JSON = Path(
    os.getenv(
        "PRECISION_POLICY_REGISTRY_JSON",
        str(MEASUREMENT_REGISTRY_DIR / "precision_policy_registry.json"),
    )
)
ROUNDING_POLICY_REGISTRY_JSON = Path(
    os.getenv(
        "ROUNDING_POLICY_REGISTRY_JSON",
        str(MEASUREMENT_REGISTRY_DIR / "rounding_policy_registry.json"),
    )
)
BAND_MAPPING_POLICY_REGISTRY_JSON = Path(
    os.getenv(
        "BAND_MAPPING_POLICY_REGISTRY_JSON",
        str(MEASUREMENT_REGISTRY_DIR / "band_mapping_policy_registry.json"),
    )
)
SOURCE_POLICY_STATUS_JSON = Path(
    os.getenv(
        "SOURCE_POLICY_STATUS_JSON",
        str(OUTPUT_DIR / "source_policy_status.json"),
    )
)

PROBABILITY_STATES_DIR = Path(
    os.getenv(
        "PROBABILITY_STATES_DIR",
        str(OUTPUT_DIR / "probability_states"),
    )
)

PROBABILITY_SHADOW_REPORT_JSON = Path(
    os.getenv(
        "PROBABILITY_SHADOW_REPORT_JSON",
        str(OUTPUT_DIR / "probability_shadow_report.json"),
    )
)

FEATURE_STORE_TRAINING_SAMPLES_JSONL = Path(
    os.getenv(
        "FEATURE_STORE_TRAINING_SAMPLES_JSONL",
        str(OUTPUT_DIR / "training_samples.jsonl"),
    )
)

FEATURE_STORE_SUMMARY_JSON = Path(
    os.getenv(
        "FEATURE_STORE_SUMMARY_JSON",
        str(OUTPUT_DIR / "feature_store_summary.json"),
    )
)

CALIBRATION_REPORT_JSON = Path(
    os.getenv(
        "CALIBRATION_REPORT_JSON",
        str(OUTPUT_DIR / "calibration_report.json"),
    )
)

BACKTEST_REPORT_JSON = Path(
    os.getenv(
        "BACKTEST_REPORT_JSON",
        str(OUTPUT_DIR / "backtest_report.json"),
    )
)

MODEL_VALIDATION_REPORT_JSON = Path(
    os.getenv(
        "MODEL_VALIDATION_REPORT_JSON",
        str(OUTPUT_DIR / "model_validation_report.json"),
    )
)
VALIDATION_ASSIMILATION_REPORT_JSON = Path(
    os.getenv(
        "VALIDATION_ASSIMILATION_REPORT_JSON",
        str(OUTPUT_DIR / "validation_assimilation_report.json"),
    )
)
VALIDATION_FRESHNESS_STATUS_JSON = Path(
    os.getenv(
        "VALIDATION_FRESHNESS_STATUS_JSON",
        str(OUTPUT_DIR / "validation_freshness_status.json"),
    )
)
LABEL_COVERAGE_REPORT_JSON = Path(
    os.getenv(
        "LABEL_COVERAGE_REPORT_JSON",
        str(OUTPUT_DIR / "label_coverage_report.json"),
    )
)
UNIFIED_STATUS_JSON = Path(
    os.getenv(
        "UNIFIED_STATUS_JSON",
        str(OUTPUT_DIR / "unified_status.json"),
    )
)
GATE_STACK_API_JSON = Path(
    os.getenv(
        "GATE_STACK_API_JSON",
        str(OUTPUT_DIR / "gate_stack_api.json"),
    )
)
GATE_STACK_AUTOMATION_SUMMARY_JSON = Path(
    os.getenv(
        "GATE_STACK_AUTOMATION_SUMMARY_JSON",
        str(OUTPUT_DIR / "gate_stack_automation_summary.json"),
    )
)
GATE_STACK_CONTRACT_CONSISTENCY_JSON = Path(
    os.getenv(
        "GATE_STACK_CONTRACT_CONSISTENCY_JSON",
        str(OUTPUT_DIR / "gate_stack_contract_consistency.json"),
    )
)
GATE_STACK_CONTRACT_CONSISTENCY_TREND_JSON = Path(
    os.getenv(
        "GATE_STACK_CONTRACT_CONSISTENCY_TREND_JSON",
        str(OUTPUT_DIR / "gate_stack_contract_consistency_trend.json"),
    )
)
TELEGRAM_GATE_RUNTIME_SNAPSHOT_JSON = Path(
    os.getenv(
        "TELEGRAM_GATE_RUNTIME_SNAPSHOT_JSON",
        str(BASE_DIR.parent / "weather-telegram-console" / "data" / "outputs" / "telegram_gate_runtime_snapshot.json"),
    )
)
GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON = Path(
    os.getenv(
        "GATEWAY_GATE_RUNTIME_SNAPSHOT_JSON",
        str(BASE_DIR.parent / "weather-execution-gateway" / "data" / "outputs" / "gateway_gate_runtime_snapshot.json"),
    )
)
GATE_STACK_OPS_ALERTS_JSONL = Path(
    os.getenv(
        "GATE_STACK_OPS_ALERTS_JSONL",
        str(OUTPUT_DIR / "gate_stack_ops_alerts.jsonl"),
    )
)
MARKET_WORKSTATION_OUTPUT_DIR = Path(
    os.getenv(
        "MARKET_WORKSTATION_OUTPUT_DIR",
        str(OUTPUT_DIR / "market_workstation"),
    )
)
OPERATIONS_MONITOR_OUTPUT_DIR = Path(
    os.getenv(
        "OPERATIONS_MONITOR_OUTPUT_DIR",
        str(OUTPUT_DIR / "operations_monitor"),
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
MONITORING_STATUS_JSON = Path(
    os.getenv(
        "MONITORING_STATUS_JSON",
        str(OUTPUT_DIR / "monitoring_status.json"),
    )
)
SOURCE_POLICY_MONITOR_STALE_AFTER_SECONDS = int(
    os.getenv("SOURCE_POLICY_MONITOR_STALE_AFTER_SECONDS", "1800")
)
EXECUTION_GATEWAY_PRODUCTION_READINESS_JSON = Path(
    os.getenv(
        "EXECUTION_GATEWAY_PRODUCTION_READINESS_JSON",
        "../weather-execution-gateway/data/outputs/production_readiness_report.json",
    )
)

OFFICIAL_RECORDS_GLOB = os.getenv(
    "OFFICIAL_RECORDS_GLOB",
    "../weather-rules-research/data/outputs/official_records/*.json",
)

OFFICIAL_HISTORY_JSONL = Path(
    os.getenv(
        "OFFICIAL_HISTORY_JSONL",
        "../weather-rules-research/data/outputs/official_history.jsonl",
    )
)

REALTIME_MARKET_SNAPSHOTS_GLOB = os.getenv(
    "REALTIME_MARKET_SNAPSHOTS_GLOB",
    "../polymarket-weather-ingest/data/outputs/market_realtime_simple*.json",
)

COMPARISON_LOOP_INTERVAL_SECONDS = int(
    os.getenv("COMPARISON_LOOP_INTERVAL_SECONDS", "15")
)

FEATURE_STORE_REFRESH_INTERVAL_SECONDS = int(
    os.getenv("FEATURE_STORE_REFRESH_INTERVAL_SECONDS", "1800")
)

FEATURE_STORE_MAX_CYCLES = int(
    os.getenv("FEATURE_STORE_MAX_CYCLES", "0")
)

MODEL_VALIDATION_BUCKET_COUNT = int(
    os.getenv("MODEL_VALIDATION_BUCKET_COUNT", "10")
)

BACKTEST_EDGE_THRESHOLD = float(
    os.getenv("BACKTEST_EDGE_THRESHOLD", "0.05")
)

MODEL_VALIDATION_REFRESH_INTERVAL_SECONDS = int(
    os.getenv("MODEL_VALIDATION_REFRESH_INTERVAL_SECONDS", "1800")
)

MODEL_VALIDATION_MAX_CYCLES = int(
    os.getenv("MODEL_VALIDATION_MAX_CYCLES", "0")
)
MARKET_MONITOR_STALE_AFTER_SECONDS = int(
    os.getenv("MARKET_MONITOR_STALE_AFTER_SECONDS", "300")
)
FORECAST_MONITOR_STALE_AFTER_SECONDS = int(
    os.getenv("FORECAST_MONITOR_STALE_AFTER_SECONDS", "1800")
)
RESOLVER_MONITOR_STALE_AFTER_SECONDS = int(
    os.getenv("RESOLVER_MONITOR_STALE_AFTER_SECONDS", "21600")
)
PROBABILITY_MONITOR_STALE_AFTER_SECONDS = int(
    os.getenv("PROBABILITY_MONITOR_STALE_AFTER_SECONDS", "3600")
)
COMPARISON_MONITOR_STALE_AFTER_SECONDS = int(
    os.getenv("COMPARISON_MONITOR_STALE_AFTER_SECONDS", "900")
)
GATEWAY_MONITOR_STALE_AFTER_SECONDS = int(
    os.getenv("GATEWAY_MONITOR_STALE_AFTER_SECONDS", "3600")
)
VALIDATION_MONITOR_STALE_AFTER_SECONDS = int(
    os.getenv(
        "VALIDATION_MONITOR_STALE_AFTER_SECONDS",
        str(max(MODEL_VALIDATION_REFRESH_INTERVAL_SECONDS * 3, 3600)),
    )
)
VALIDATION_FRESHNESS_WARNING_AFTER_SECONDS = int(
    os.getenv(
        "VALIDATION_FRESHNESS_WARNING_AFTER_SECONDS",
        str(max(MODEL_VALIDATION_REFRESH_INTERVAL_SECONDS * 2, 1800)),
    )
)
PROBABILITY_CANDIDATE_MIN_LABELED_SAMPLES = int(
    os.getenv("PROBABILITY_CANDIDATE_MIN_LABELED_SAMPLES", "25")
)
PROBABILITY_CANDIDATE_MAX_CALIBRATION_ERROR = float(
    os.getenv("PROBABILITY_CANDIDATE_MAX_CALIBRATION_ERROR", "0.18")
)
PROBABILITY_CANDIDATE_MIN_RESOLVER_MATCH_RATE = float(
    os.getenv("PROBABILITY_CANDIDATE_MIN_RESOLVER_MATCH_RATE", "0.60")
)
PROBABILITY_LIVE_MIN_LABELED_SAMPLES = int(
    os.getenv("PROBABILITY_LIVE_MIN_LABELED_SAMPLES", "200")
)
PROBABILITY_LIVE_MAX_CALIBRATION_ERROR = float(
    os.getenv("PROBABILITY_LIVE_MAX_CALIBRATION_ERROR", "0.08")
)
PROBABILITY_LIVE_MAX_BRIER_SCORE = float(
    os.getenv("PROBABILITY_LIVE_MAX_BRIER_SCORE", "0.20")
)
PROBABILITY_LIVE_MIN_RESOLVER_MATCH_RATE = float(
    os.getenv("PROBABILITY_LIVE_MIN_RESOLVER_MATCH_RATE", "0.90")
)
PROBABILITY_LIVE_MIN_BACKTEST_ROI = float(
    os.getenv("PROBABILITY_LIVE_MIN_BACKTEST_ROI", "0.00")
)
VALIDATION_LABEL_COVERAGE_MIN_LABELED_ROWS = int(
    os.getenv(
        "VALIDATION_LABEL_COVERAGE_MIN_LABELED_ROWS",
        str(PROBABILITY_CANDIDATE_MIN_LABELED_SAMPLES),
    )
)
VALIDATION_LABEL_COVERAGE_MIN_RATIO = float(
    os.getenv("VALIDATION_LABEL_COVERAGE_MIN_RATIO", "0.20")
)
VALIDATION_LABEL_COVERAGE_MIN_FAMILY_LABELED_ROWS = int(
    os.getenv("VALIDATION_LABEL_COVERAGE_MIN_FAMILY_LABELED_ROWS", "3")
)
GATE_AUTOMATION_CHECK_INTERVAL_SECONDS = int(
    os.getenv("GATE_AUTOMATION_CHECK_INTERVAL_SECONDS", "300")
)
GATE_AUTOMATION_CHECK_MAX_CYCLES = int(
    os.getenv("GATE_AUTOMATION_CHECK_MAX_CYCLES", "0")
)
GATE_AUTOMATION_FAIL_ON_SIGNAL = str(
    os.getenv("GATE_AUTOMATION_FAIL_ON_SIGNAL", "red")
).strip().lower()
GATE_AUTOMATION_RETRY_BACKOFF_SECONDS = tuple(
    int(item.strip())
    for item in os.getenv("GATE_AUTOMATION_RETRY_BACKOFF_SECONDS", "5,15,30").split(",")
    if item.strip()
)
