from __future__ import annotations

from typing import NotRequired, TypedDict


class WeatherDescriptor(TypedDict):
    market_id: str
    question: str
    city: str
    region: NotRequired[str | None]
    country: NotRequired[str | None]
    target_date: str
    metric: str
    threshold: NotRequired[float | None]
    upper_threshold: NotRequired[float | None]
    unit: str
    direction: str
    confidence: str
    parse_warnings: NotRequired[list[str]]


class WeatherSourceRecord(TypedDict):
    source_id: str
    market_id: str
    source_name: str
    source_type: str
    city: str
    target_date: str
    fetched_at: str
    valid_time: NotRequired[str | None]
    normalized_value: NotRequired[float | None]
    unit: str
    freshness_status: str
    trust_level: str
    raw_payload: NotRequired[dict[str, object]]


class EvidencePack(TypedDict):
    evidence_pack_id: str
    market_id: str
    descriptor: NotRequired[WeatherDescriptor]
    sources: NotRequired[list[WeatherSourceRecord]]
    evidence_freshness: str
    evidence_conflict_level: str
    raw_refs: NotRequired[list[str]]
    created_at: str


class WeatherView(TypedDict):
    weather_view_id: str
    evidence_pack_id: str
    market_id: str
    city: str
    target_date: str
    expected_value: float
    expected_range_low: float
    expected_range_high: float
    sigma: float
    threshold: NotRequired[float | None]
    direction: str
    unit: str
    confidence: str
    evidence_summary: NotRequired[list[str]]
    invalidation_rules: NotRequired[list[str]]
    confirmation_rules: NotRequired[list[str]]
    created_at: str


class ProbabilityView(TypedDict):
    probability_view_id: str
    weather_view_id: str
    market_id: str
    engine_id: str
    model_probability: float
    threshold: NotRequired[float | None]
    expected_value: float
    sigma: float
    direction: str
    confidence: str
    warnings: NotRequired[list[str]]
    created_at: str


class ProbabilityEngineRun(TypedDict):
    run_id: str
    market_id: str
    weather_view_id: str
    engine_id: str
    engine_type: str
    model_probability: float
    expected_value: NotRequired[float | None]
    sigma: NotRequired[float | None]
    threshold: NotRequired[float | None]
    direction: NotRequired[str | None]
    params: NotRequired[dict[str, object]]
    warnings: NotRequired[list[str]]
    created_at: str


class ProbabilityComparison(TypedDict):
    comparison_id: str
    market_id: str
    weather_view_id: str
    active_engine_id: str
    active_probability: float
    engine_runs: list[ProbabilityEngineRun]
    spread_between_engines: float
    disagreement_level: str
    selection_reason: str
    warnings: NotRequired[list[str]]
    created_at: str


class MarketOutcome(TypedDict):
    outcome_id: str
    market_id: str
    resolved_value: NotRequired[float | None]
    resolved_direction_hit: NotRequired[bool | None]
    official_source: NotRequired[str | None]
    resolved_at: str
    status: str
    notes: NotRequired[str | None]


class CalibrationResult(TypedDict):
    calibration_id: str
    market_id: str
    engine_id: str
    run_id: str
    outcome_id: str
    predicted_probability: float
    actual_outcome: int
    brier_score: float
    absolute_error: float
    bucket: NotRequired[str | None]
    created_at: str


class ProbabilityEngineConfig(TypedDict):
    engine_id: str
    engine_name: str
    engine_type: str
    version: str
    enabled: bool
    can_be_primary: bool
    description: NotRequired[str]
    default_params: NotRequired[dict[str, object]]
    created_at: str
    updated_at: str


class Candidate(TypedDict):
    candidate_id: str
    market_id: str
    question: str
    side: str
    market_probability: float
    model_probability: float
    edge_percent: float
    liquidity: float
    spread: float
    confidence_tier: str
    risk_status: str
    action_status: str
    created_at: str


class WorkstationPayload(TypedDict, total=False):
    status: str
    market_id: str
    candidate: Candidate | None
    descriptor: WeatherDescriptor | None
    evidence_pack: EvidencePack | None
    sources: list[WeatherSourceRecord]
    weather_view: WeatherView | None
    probability_view: ProbabilityView | None
    probability_comparison: ProbabilityComparison | None
    market_outcome: MarketOutcome | None


class PolymarketConnectorMode(TypedDict):
    status: str
    market_source_mode: str
    allow_polymarket_network: bool
    live_execution: NotRequired[bool]
    message: NotRequired[str]


class PolymarketConnectorHealth(TypedDict):
    connector_id: str
    gamma_reachable: bool
    clob_reachable: bool
    last_gamma_status: NotRequired[int | None]
    last_clob_status: NotRequired[int | None]
    last_checked_at: str
    mode: str
    warnings: list[str]


class PolymarketConnectorConfig(TypedDict):
    market_source_mode: str
    allow_polymarket_network: bool
    gamma_base_url: str
    clob_base_url: str
    request_timeout_seconds: int
    max_markets: int
    weather_keywords: list[str]


class PolymarketMarketCacheItem(TypedDict):
    polymarket_market_id: str
    question: str
    fetched_at: str
    active: bool
    outcomes: list[str]
    outcome_prices: list[float]
    clob_token_ids: list[str]
    id: NotRequired[int]
    condition_id: NotRequired[str | None]
    slug: NotRequired[str | None]
    category: NotRequired[str | None]
    closed: NotRequired[bool | None]
    archived: NotRequired[bool | None]
    end_date: NotRequired[str | None]
    resolution_source: NotRequired[str | None]
    liquidity: NotRequired[float | None]
    volume: NotRequired[float | None]
    raw_payload: NotRequired[dict[str, object]]


class PolymarketPreviewSnapshot(TypedDict):
    market_id: str
    question: str
    yes_price: float
    no_price: float
    liquidity: float
    spread: float
    source: str
    fetched_at: NotRequired[str]


class MarketSnapshotArchiveRecord(TypedDict):
    snapshot_archive_id: str
    market_id: str
    source: str
    question: str
    yes_price: float
    no_price: float
    liquidity: float
    spread: float
    archived_at: str
    market_source_mode: str
    archive_reason: str
    fetched_at: NotRequired[str | None]
    raw_ref: NotRequired[str | None]
    metadata: NotRequired[dict[str, object]]


class MarketSnapshotSeries(TypedDict):
    market_id: str
    count: int
    snapshots: list[MarketSnapshotArchiveRecord]
    first_archived_at: NotRequired[str | None]
    last_archived_at: NotRequired[str | None]


class SnapshotArchiveSummary(TypedDict):
    total_snapshots: int
    unique_markets: int
    by_source: dict[str, int]
    by_archive_reason: dict[str, int]
    latest_archived_at: NotRequired[str | None]


class WeatherForecastArchiveRecord(TypedDict):
    forecast_archive_id: str
    market_id: str
    source_id: str
    source_type: str
    metric: str
    unit: str
    archived_at: str
    archive_reason: str
    weather_view_id: NotRequired[str | None]
    evidence_pack_id: NotRequired[str | None]
    city: NotRequired[str | None]
    target_date: NotRequired[str | None]
    expected_value: NotRequired[float | None]
    expected_range_low: NotRequired[float | None]
    expected_range_high: NotRequired[float | None]
    sigma: NotRequired[float | None]
    fetched_at: NotRequired[str | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class WeatherEvidenceArchiveRecord(TypedDict):
    evidence_archive_id: str
    market_id: str
    evidence_pack_id: str
    archived_at: str
    archive_reason: str
    source_ids: NotRequired[list[str]]
    evidence_summary: NotRequired[list[str]]
    invalidation_rules: NotRequired[list[str]]
    confirmation_rules: NotRequired[list[str]]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class WeatherViewArchiveRecord(TypedDict):
    weather_view_archive_id: str
    market_id: str
    weather_view_id: str
    archived_at: str
    archive_reason: str
    evidence_pack_id: NotRequired[str | None]
    city: NotRequired[str | None]
    target_date: NotRequired[str | None]
    expected_value: NotRequired[float | None]
    expected_range_low: NotRequired[float | None]
    expected_range_high: NotRequired[float | None]
    sigma: NotRequired[float | None]
    threshold: NotRequired[float | None]
    direction: NotRequired[str]
    unit: NotRequired[str]
    confidence: NotRequired[str]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class WeatherArchiveSummary(TypedDict):
    forecast_records: int
    evidence_records: int
    weather_view_records: int
    unique_markets: int
    by_source_type: dict[str, int]
    by_archive_reason: dict[str, int]
    latest_archived_at: NotRequired[str | None]


class WeatherArchiveBundle(TypedDict):
    market_id: str
    forecasts: list[WeatherForecastArchiveRecord]
    evidence: list[WeatherEvidenceArchiveRecord]
    weather_views: list[WeatherViewArchiveRecord]


class MarketOutcomeRecordV2(TypedDict):
    market_outcome_id: str
    market_id: str
    source: str
    resolved_outcome: str
    resolution_status: str
    resolved_at: str
    question: NotRequired[str | None]
    resolved_value: NotRequired[float | None]
    notes: NotRequired[str | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class WeatherActualRecordV2(TypedDict):
    weather_actual_id: str
    market_id: str
    source: str
    metric: str
    unit: str
    observed_at: str
    city: NotRequired[str | None]
    target_date: NotRequired[str | None]
    actual_value: NotRequired[float | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class OutcomeResolutionRecordV2(TypedDict):
    outcome_resolution_id: str
    market_id: str
    direction: str
    resolved_outcome: str
    resolution_status: str
    resolution_source: str
    resolved_at: str
    market_outcome_id: NotRequired[str | None]
    weather_actual_id: NotRequired[str | None]
    weather_view_id: NotRequired[str | None]
    threshold: NotRequired[float | None]
    actual_value: NotRequired[float | None]
    notes: NotRequired[str | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class OutcomeBundle(TypedDict):
    market_id: str
    markets: list[MarketOutcomeRecordV2]
    weather_actuals: list[WeatherActualRecordV2]
    resolutions: list[OutcomeResolutionRecordV2]


class OutcomeArchiveSummary(TypedDict):
    market_outcome_records: int
    weather_actual_records: int
    outcome_resolution_records: int
    unique_markets: int
    by_resolution_status: dict[str, int]
    by_resolved_outcome: dict[str, int]
    latest_resolved_at: NotRequired[str | None]


class CalibrationSample(TypedDict):
    calibration_sample_id: str
    market_id: str
    resolved_outcome: str
    sample_eligibility: str
    sample_status: str
    sampled_at: str
    snapshot_archive_id: NotRequired[str | None]
    weather_view_archive_id: NotRequired[str | None]
    weather_forecast_archive_id: NotRequired[str | None]
    probability_run_id: NotRequired[str | None]
    outcome_resolution_id: NotRequired[str | None]
    engine_id: NotRequired[str | None]
    market_probability: NotRequired[float | None]
    model_probability: NotRequired[float | None]
    actual_outcome_value: NotRequired[float | None]
    model_brier_score: NotRequired[float | None]
    market_brier_score: NotRequired[float | None]
    model_absolute_error: NotRequired[float | None]
    market_absolute_error: NotRequired[float | None]
    model_beats_market: NotRequired[bool | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class BacktestMemoryRecord(TypedDict):
    backtest_memory_id: str
    market_id: str
    hypothetical_action: str
    hypothetical_result: str
    sample_eligibility: str
    backtest_status: str
    sampled_at: str
    snapshot_archive_id: NotRequired[str | None]
    weather_view_archive_id: NotRequired[str | None]
    weather_forecast_archive_id: NotRequired[str | None]
    probability_run_id: NotRequired[str | None]
    outcome_resolution_id: NotRequired[str | None]
    engine_id: NotRequired[str | None]
    market_probability: NotRequired[float | None]
    model_probability: NotRequired[float | None]
    actual_outcome_value: NotRequired[float | None]
    edge: NotRequired[float | None]
    edge_threshold: NotRequired[float | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class CalibrationMemorySummary(TypedDict):
    calibration_samples: int
    backtest_memory_records: int
    unique_markets: int
    by_sample_status: dict[str, int]
    by_backtest_status: dict[str, int]
    by_eligibility: dict[str, int]
    latest_sampled_at: NotRequired[str | None]


class CalibrationMemoryBundle(TypedDict):
    market_id: str
    calibration_samples: list[CalibrationSample]
    backtest_memory_records: list[BacktestMemoryRecord]


class DebShadowRunRecord(TypedDict):
    deb_shadow_run_id: str
    market_id: str
    engine_id: str
    run_status: str
    created_at: str
    calibration_sample_id: NotRequired[str | None]
    base_probability: NotRequired[float | None]
    deb_probability: NotRequired[float | None]
    bias_adjustment: NotRequired[float | None]
    calibration_gap: NotRequired[float | None]
    sample_count: NotRequired[int]
    warnings: NotRequired[list[str]]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class DebShadowDiagnosticRecord(TypedDict):
    deb_shadow_diagnostic_id: str
    deb_shadow_run_id: str
    market_id: str
    created_at: str
    calibration_sample_id: NotRequired[str | None]
    sample_count: NotRequired[int]
    avg_model_brier_score: NotRequired[float | None]
    avg_market_brier_score: NotRequired[float | None]
    avg_model_edge: NotRequired[float | None]
    avg_probability_error: NotRequired[float | None]
    adjustment_weight: NotRequired[float | None]
    notes: NotRequired[str | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class DebShadowSummary(TypedDict):
    total_runs: int
    total_diagnostics: int
    unique_markets: int
    by_run_status: dict[str, int]
    latest_created_at: NotRequired[str | None]


class DebShadowMarketBundle(TypedDict):
    market_id: str
    runs: list[DebShadowRunRecord]
    diagnostics: list[DebShadowDiagnosticRecord]


class EmosShadowRunRecord(TypedDict):
    emos_shadow_run_id: str
    market_id: str
    engine_id: str
    run_status: str
    created_at: str
    calibration_sample_id: NotRequired[str | None]
    base_probability: NotRequired[float | None]
    emos_probability: NotRequired[float | None]
    location_adjustment: NotRequired[float | None]
    scale_adjustment: NotRequired[float | None]
    sample_count: NotRequired[int]
    warnings: NotRequired[list[str]]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class EmosShadowDiagnosticRecord(TypedDict):
    emos_shadow_diagnostic_id: str
    emos_shadow_run_id: str
    market_id: str
    created_at: str
    calibration_sample_id: NotRequired[str | None]
    sample_count: NotRequired[int]
    avg_model_brier_score: NotRequired[float | None]
    avg_market_brier_score: NotRequired[float | None]
    avg_probability_error: NotRequired[float | None]
    avg_absolute_error: NotRequired[float | None]
    location_weight: NotRequired[float | None]
    scale_weight: NotRequired[float | None]
    notes: NotRequired[str | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class EmosShadowSummary(TypedDict):
    total_runs: int
    total_diagnostics: int
    unique_markets: int
    by_run_status: dict[str, int]
    latest_created_at: NotRequired[str | None]


class EmosShadowMarketBundle(TypedDict):
    market_id: str
    runs: list[EmosShadowRunRecord]
    diagnostics: list[EmosShadowDiagnosticRecord]


class ShadowEngineEvaluationRecord(TypedDict):
    shadow_evaluation_id: str
    market_id: str
    best_engine: str
    evaluation_status: str
    created_at: str
    calibration_sample_id: NotRequired[str | None]
    outcome_resolution_id: NotRequired[str | None]
    primary_engine_id: NotRequired[str]
    deb_engine_id: NotRequired[str]
    emos_engine_id: NotRequired[str]
    primary_probability: NotRequired[float | None]
    deb_probability: NotRequired[float | None]
    emos_probability: NotRequired[float | None]
    actual_outcome_value: NotRequired[float | None]
    primary_brier_score: NotRequired[float | None]
    deb_brier_score: NotRequired[float | None]
    emos_brier_score: NotRequired[float | None]
    primary_absolute_error: NotRequired[float | None]
    deb_absolute_error: NotRequired[float | None]
    emos_absolute_error: NotRequired[float | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class ShadowEngineEvaluationSummary(TypedDict):
    total_evaluations: int
    unique_markets: int
    by_status: dict[str, int]
    by_best_engine: dict[str, int]
    latest_created_at: NotRequired[str | None]


class ShadowEngineEvaluationBundle(TypedDict):
    market_id: str
    evaluations: list[ShadowEngineEvaluationRecord]


class CommandReviewRecord(TypedDict):
    command_review_id: str
    market_id: str
    command_name: str
    source_page: str
    target_page: NotRequired[str | None]
    command_path: NotRequired[str | None]
    review_status: str
    approval_status: str
    recommendation: str
    gate_status: str
    active_engine_id: NotRequired[str | None]
    execution_mode: NotRequired[str | None]
    risk_status: NotRequired[str | None]
    approval_window_valid: NotRequired[bool | None]
    approval_valid_until: NotRequired[str | None]
    market_snapshot_archive_id: NotRequired[str | None]
    weather_view_archive_id: NotRequired[str | None]
    weather_forecast_archive_id: NotRequired[str | None]
    probability_run_id: NotRequired[str | None]
    outcome_resolution_id: NotRequired[str | None]
    calibration_sample_id: NotRequired[str | None]
    backtest_memory_id: NotRequired[str | None]
    deb_shadow_run_id: NotRequired[str | None]
    emos_shadow_run_id: NotRequired[str | None]
    shadow_evaluation_id: NotRequired[str | None]
    reviewed_at: str
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class CommandReviewSummary(TypedDict):
    command_reviews: int
    unique_markets: int
    by_review_status: dict[str, int]
    by_approval_status: dict[str, int]
    by_gate_status: dict[str, int]
    latest_reviewed_at: NotRequired[str | None]


class CommandReviewBundle(TypedDict):
    market_id: str
    command_reviews: list[CommandReviewRecord]


class ExecutionDecisionReviewRecord(TypedDict):
    execution_decision_review_id: str
    market_id: str
    decision_id: str
    candidate_id: str
    command_review_id: NotRequired[str | None]
    shadow_evaluation_id: NotRequired[str | None]
    execution_mode: NotRequired[str | None]
    action: NotRequired[str | None]
    position_size: NotRequired[float | None]
    expected_cost: NotRequired[float | None]
    risk_status: NotRequired[str | None]
    execution_status: NotRequired[str | None]
    review_status: str
    approval_status: str
    gate_status: str
    recommendation: str
    approval_window_valid: NotRequired[bool | None]
    approval_valid_until: NotRequired[str | None]
    reviewed_at: str
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class ExecutionDecisionReviewSummary(TypedDict):
    execution_decision_reviews: int
    unique_markets: int
    by_review_status: dict[str, int]
    by_approval_status: dict[str, int]
    by_gate_status: dict[str, int]
    by_execution_status: dict[str, int]
    by_execution_mode: dict[str, int]
    latest_reviewed_at: NotRequired[str | None]


class ExecutionDecisionReviewBundle(TypedDict):
    market_id: str
    execution_decision_reviews: list[ExecutionDecisionReviewRecord]


class ExecutionQueueReviewRecord(TypedDict):
    execution_queue_review_id: str
    market_id: str
    decision_id: str
    candidate_id: str
    command_review_id: NotRequired[str | None]
    execution_decision_review_id: NotRequired[str | None]
    shadow_evaluation_id: NotRequired[str | None]
    execution_mode: NotRequired[str | None]
    action: NotRequired[str | None]
    position_size: NotRequired[float | None]
    expected_cost: NotRequired[float | None]
    risk_status: NotRequired[str | None]
    execution_status: NotRequired[str | None]
    review_status: str
    approval_status: str
    gate_status: str
    recommendation: str
    approval_window_valid: NotRequired[bool | None]
    approval_valid_until: NotRequired[str | None]
    reviewed_at: str
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class ExecutionQueueReviewSummary(TypedDict):
    execution_queue_reviews: int
    unique_markets: int
    by_review_status: dict[str, int]
    by_approval_status: dict[str, int]
    by_gate_status: dict[str, int]
    by_execution_status: dict[str, int]
    by_execution_mode: dict[str, int]
    latest_reviewed_at: NotRequired[str | None]


class ExecutionQueueReviewBundle(TypedDict):
    market_id: str
    execution_queue_reviews: list[ExecutionQueueReviewRecord]


class ApprovalWindowReviewRecord(TypedDict):
    approval_window_review_id: str
    market_id: str
    decision_id: str
    candidate_id: str
    review_status: str
    window_state: str
    recommendation: str
    reviewed_at: str
    command_review_id: NotRequired[str | None]
    execution_decision_review_id: NotRequired[str | None]
    execution_queue_review_id: NotRequired[str | None]
    approval_status: NotRequired[str | None]
    approval_window_valid: NotRequired[bool | None]
    approval_valid_until: NotRequired[str | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class ApprovalWindowReviewSummary(TypedDict):
    approval_window_reviews: int
    unique_markets: int
    by_review_status: dict[str, int]
    by_window_state: dict[str, int]
    by_approval_status: dict[str, int]
    latest_reviewed_at: NotRequired[str | None]


class ApprovalWindowReviewBundle(TypedDict):
    market_id: str
    approval_window_reviews: list[ApprovalWindowReviewRecord]


class ActivationReadinessReviewRecord(TypedDict):
    activation_readiness_review_id: str
    market_id: str
    decision_id: str
    candidate_id: str
    readiness_status: str
    recommendation: str
    reviewed_at: str
    command_review_id: NotRequired[str | None]
    execution_decision_review_id: NotRequired[str | None]
    execution_queue_review_id: NotRequired[str | None]
    approval_window_review_id: NotRequired[str | None]
    approval_status: NotRequired[str | None]
    window_state: NotRequired[str | None]
    review_status: NotRequired[str | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class ActivationReadinessReviewSummary(TypedDict):
    activation_readiness_reviews: int
    unique_markets: int
    by_readiness_status: dict[str, int]
    by_recommendation: dict[str, int]
    by_approval_status: dict[str, int]
    latest_reviewed_at: NotRequired[str | None]


class ActivationReadinessReviewBundle(TypedDict):
    market_id: str
    activation_readiness_reviews: list[ActivationReadinessReviewRecord]


class ActivationAuthorizationReviewRecord(TypedDict):
    activation_authorization_review_id: str
    market_id: str
    decision_id: str
    candidate_id: str
    authorization_status: str
    recommendation: str
    reviewed_at: str
    command_review_id: NotRequired[str | None]
    execution_decision_review_id: NotRequired[str | None]
    execution_queue_review_id: NotRequired[str | None]
    approval_window_review_id: NotRequired[str | None]
    activation_readiness_review_id: NotRequired[str | None]
    approval_status: NotRequired[str | None]
    window_state: NotRequired[str | None]
    readiness_status: NotRequired[str | None]
    raw_payload: NotRequired[dict[str, object]]
    metadata: NotRequired[dict[str, object]]


class ActivationAuthorizationReviewSummary(TypedDict):
    activation_authorization_reviews: int
    unique_markets: int
    by_authorization_status: dict[str, int]
    by_recommendation: dict[str, int]
    by_approval_status: dict[str, int]
    latest_reviewed_at: NotRequired[str | None]


class ActivationAuthorizationReviewBundle(TypedDict):
    market_id: str
    activation_authorization_reviews: list[ActivationAuthorizationReviewRecord]
