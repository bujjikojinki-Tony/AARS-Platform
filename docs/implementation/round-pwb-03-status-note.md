# Round_PWB-03_Status_Note

## 1. Round
Round PWB-03 - Probability Governance & Calibration v0

## 2. Status
Accepted for baseline freeze.

## 3. Purpose
PWB-03 extends PWB-02 Weather Intelligence by adding a governed probability comparison and calibration layer.

PWB-01 answered:
```text
How do we scan, gate, simulate, and record opportunities?
```

PWB-02 answered:
```text
Where does weather market model_probability come from?
```

PWB-03 answers:
```text
How do we govern, compare, evaluate, and promote probability engines?
```

## 4. Accepted Scope

PWB-03 accepts the following bounded governance chain:

```text
WeatherView
  -> ProbabilityEngineRegistry
  -> ProbabilityEngineRunner
  -> Primary + Shadow Engine Runs
  -> ProbabilityComparisonBuilder
  -> ProbabilityComparisonView
  -> Manual MarketOutcome
  -> CalibrationService
  -> CalibrationResult
  -> ModelPromotionGate
  -> EnginePromotionDecision
```

## 5. Accepted Capabilities

### 5.1 Probability Engine Registry

Accepted default engine configs:

```text
gaussian_v0      PRIMARY
deb_shadow_v0    SHADOW
emos_shadow_v0   SHADOW
```

Accepted rules:
- `gaussian_v0` is the only accepted PRIMARY engine.
- `deb_shadow_v0` and `emos_shadow_v0` are enabled but SHADOW only.
- shadow engines cannot drive trading.
- shadow engines cannot become active in PWB-03.

### 5.2 Shadow Engines

Accepted shadow placeholders:
- `DebShadowEngine`
- `EmosShadowEngine`

Accepted behavior:
- DEB shadow v0 is a placeholder transformation over Gaussian probability.
- EMOS shadow v0 is a conservative placeholder transformation over Gaussian probability.
- Both return probability plus warning.
- Both are for comparison only.

Not accepted:
- real DEB
- real EMOS
- LGBM
- production calibration model

### 5.3 Probability Engine Runs

Accepted object:
- `ProbabilityEngineRun`

Accepted fields:
- `run_id`
- `market_id`
- `weather_view_id`
- `engine_id`
- `engine_type`
- `model_probability`
- `expected_value`
- `sigma`
- `threshold`
- `direction`
- `params`
- `warnings`
- `created_at`

Accepted behavior:
- Each enabled engine produces a `ProbabilityEngineRun`.
- Runs are persisted.
- Runs are auditable.
- Runs do not directly create `StrategySignal`.

### 5.4 Probability Comparison

Accepted object:
- `ProbabilityComparisonView`

Accepted behavior:
- `active_engine_id = gaussian_v0`
- `active_probability = gaussian_v0` run probability
- shadow probabilities are displayed but not used for trading
- `spread_between_engines` is computed
- `disagreement_level` is computed
- `selection_reason` is recorded
- `warnings` are recorded

Accepted disagreement thresholds:

```text
NONE   spread < 0.03
LOW    spread < 0.08
MEDIUM spread < 0.15
HIGH   spread >= 0.15
```

### 5.5 Active Engine Policy

Accepted rules:
- Only PRIMARY engine can be active.
- `enabled` must be true.
- `can_be_primary` must be true.
- SHADOW engines are rejected as active.
- DISABLED engines are rejected as active.

PWB-03 accepted active engine:
- `gaussian_v0`

### 5.6 Manual Market Outcome

Accepted object:
- `MarketOutcome`

Accepted statuses:
- `PENDING`
- `RESOLVED`
- `DISPUTED`
- `UNKNOWN`

Accepted behavior:
- Outcome is manually recorded.
- No production settlement resolver is accepted.
- Calibration requires `status = RESOLVED`.
- Calibration requires `resolved_direction_hit` is not null.

### 5.7 Calibration Metrics

Accepted metrics:
- Brier score
- absolute error
- probability bucket

Accepted formulas:
- `brier_score = (predicted_probability - actual_outcome)^2`
- `absolute_error = abs(predicted_probability - actual_outcome)`

Accepted buckets:
- `0.0-0.2`
- `0.2-0.4`
- `0.4-0.6`
- `0.6-0.8`
- `0.8-1.0`

### 5.8 Calibration Service

Accepted behavior:
- Read latest `RESOLVED` `MarketOutcome`.
- Read `ProbabilityEngineRun` records for the market.
- Generate `CalibrationResult` for each engine run.
- Persist `CalibrationResult`.

Accepted object:
- `CalibrationResult`

### 5.9 Model Promotion Gate

Accepted object:
- `EnginePromotionDecision`

Accepted default thresholds:
- `minimum_evidence_count = 30`
- `max_avg_brier_score = 0.20`
- `max_avg_absolute_error = 0.35`

Accepted decisions:
- `PROMOTE`
- `KEEP_SHADOW`
- `DISABLE`
- `NEEDS_MORE_DATA`
- `KEEP_PRIMARY`

Accepted PWB-03 behavior:
- `gaussian_v0 -> KEEP_PRIMARY`
- `deb_shadow_v0 -> NEEDS_MORE_DATA or KEEP_SHADOW`
- `emos_shadow_v0 -> NEEDS_MORE_DATA or KEEP_SHADOW`

Important boundary:
- Promotion gate only records decision.
- It does not mutate engine config.
- It does not automatically promote an engine.

### 5.10 Probability Governance APIs

Accepted APIs:
- `GET /api/probability/engines`
- `POST /api/probability/compare/{market_id}`
- `GET /api/probability/comparison/{market_id}`
- `POST /api/probability/outcomes`
- `GET /api/probability/outcomes/{market_id}`
- `POST /api/probability/calibrate/{market_id}`
- `GET /api/probability/calibration/{engine_id}`
- `GET /api/probability/calibration/market/{market_id}`
- `POST /api/probability/promotion/{engine_id}`
- `GET /api/probability/promotion/{engine_id}`

### 5.11 Workstation Integration

Accepted addition to Workstation API:
- `probability_comparison`
- `market_outcome`

Accepted frontend panels:
- `ProbabilityComparisonPanel`
- `CalibrationHistoryPanel`
- `ProbabilityEngineRegistryTable`

## 6. Accepted Safety Boundary

PWB-03 preserves all previous safety constraints:
- live execution remains disabled.
- `LIVE_EXECUTE` remains rejected.
- shadow engines do not drive trading.
- promotion gate does not auto-promote.
- manual outcome only.
- no real settlement resolver.
- no real DEB/EMOS/LGBM.

## 7. Not Accepted in PWB-03

The following are explicitly excluded:
- real DEB implementation
- real EMOS implementation
- LGBM model
- automatic engine promotion
- automatic engine config mutation
- production settlement-source resolver
- profit-based model ranking
- real Polymarket execution
- auto trading
- portfolio-level position sizing
- subscription/payment
- Telegram operations bot

## 8. Tests

Accepted PWB-03 test coverage includes:
- `test_default_engine_configs_exist`
- `test_registry_returns_primary_and_shadow_engines`
- `test_shadow_engines_output_probabilities`
- `test_probability_engine_runner_creates_runs`
- `test_probability_comparison_builder`
- `test_probability_comparison_persistence`
- `test_active_engine_policy_accepts_primary_and_rejects_shadow`
- `test_calibration_metrics`
- `test_calibration_metrics_reject_invalid_values`
- `test_market_outcome_service_records_resolved_outcome`
- `test_market_outcome_pending_is_not_calibratable`
- `test_calibration_service_creates_results`
- `test_calibration_service_rejects_unresolved_outcome`
- `test_model_promotion_gate_needs_more_data`
- `test_model_promotion_gate_keeps_primary`
- `test_probability_governance_api_engines`
- `test_probability_governance_api_compare`
- `test_probability_governance_api_outcome_and_calibrate`
- `test_probability_governance_api_promotion`
- `test_workstation_includes_probability_comparison`
- `test_live_execute_still_rejected`

## 9. Current Latest Stable View

Latest Stable View - PWB-03

The Polymarket Bot now has a bounded Probability Governance & Calibration v0 layer.

Accepted chain:
```text
WeatherView
  -> primary/shadow engine runs
  -> probability comparison
  -> manual outcome
  -> calibration result
  -> promotion decision
```

Active engine remains `gaussian_v0`.
Shadow engines are visible and recorded, but do not drive trading.
PWB-03 is accepted as a probability governance baseline, not a model-accuracy baseline.

## 10. Next Entry

Do not continue expanding PWB-03.

Next possible round:

```text
Round PWB-04 - Real Calibration Data & Backtest Memory v0
```

Alternative bounded rounds:
- `Round PWB-04A - Real DEB Shadow Implementation`
- `Round PWB-04B - EMOS Shadow Evaluation`
- `Round PWB-04C - Test Isolation & App Factory Hardening`
