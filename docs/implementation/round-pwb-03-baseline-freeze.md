# Round_PWB-03_Baseline_Freeze

## 1. Freeze Decision
Round PWB-03 - Probability Governance & Calibration v0 is frozen.

Status:
```text
ACCEPTED BASELINE
```

## 2. Freeze Scope

The accepted baseline includes:
- Probability governance models
- Probability governance SQLite tables
- Default probability engine configs
- `ProbabilityEngineRegistry`
- `ActiveEnginePolicy`
- `DebShadowEngine` placeholder
- `EmosShadowEngine` placeholder
- shadow placeholder engines only
- shadow placeholder only
- `ProbabilityEngineRunner`
- `ProbabilityComparisonBuilder`
- `CalibrationMetrics`
- `MarketOutcomeService`
- `CalibrationService`
- `ModelPromotionGate`
- Probability Governance API
- Workstation probability comparison integration
- `ProbabilityComparisonPanel`
- `CalibrationHistoryPanel`
- `ProbabilityEngineRegistryTable`
- PWB-03 acceptance tests

## 3. Stable Architecture

Accepted PWB-03 architecture:

```text
WeatherView
  -> ProbabilityEngineRegistry
  -> ProbabilityEngineRunner
  -> ProbabilityEngineRun[]
  -> ProbabilityComparisonBuilder
  -> ProbabilityComparisonView
  -> Manual MarketOutcome
  -> CalibrationService
  -> CalibrationResult[]
  -> ModelPromotionGate
  -> EnginePromotionDecision
```

## 4. Stable Engine Roles

Accepted engine roles:

```text
gaussian_v0:
  role = PRIMARY
  active = true
  can drive active_probability = true
deb_shadow_v0:
  role = SHADOW
  active = false
  can drive trading = false
emos_shadow_v0:
  role = SHADOW
  active = false
  can drive trading = false
```

## 5. Stable Active Probability Rule

PWB-03 freezes this rule:

```text
active_probability must come from gaussian_v0.
```

Shadow engines may be:
- run
- recorded
- displayed
- calibrated
- evaluated

Shadow engines may not be:
- used to generate `StrategySignal`
- used to bypass `RiskManager`
- used to trigger simulation/execution
- automatically promoted

## 6. Stable Calibration Rule

Calibration is allowed only when:
- `MarketOutcome.status = RESOLVED`
- `resolved_direction_hit` is not null
- `ProbabilityEngineRun` exists

Calibration result is computed as:

```text
brier_score = (predicted_probability - actual_outcome)^2
absolute_error = abs(predicted_probability - actual_outcome)
```

## 7. Stable Promotion Rule

`ModelPromotionGate` may generate:
- `EnginePromotionDecision`

But it must not:
- mutate `ProbabilityEngineConfig`
- promote engine automatically
- change active engine
- enable live trading

Default promotion thresholds:
- `minimum_evidence_count = 30`
- `max_avg_brier_score = 0.20`
- `max_avg_absolute_error = 0.35`

## 8. Stable Safety Boundary

The following are frozen:
- live execution remains disabled.
- no live trading.
- `LIVE_EXECUTE` remains rejected.
- auto trading remains absent.
- shadow engines cannot drive trading.
- manual outcome only.
- no automatic settlement resolution.
- no real DEB.
- no real EMOS.
- no LGBM.

## 9. Baseline Acceptance Criteria

PWB-03 baseline is accepted if:
1. Default engine configs exist.
2. `gaussian_v0` is PRIMARY.
3. `deb_shadow_v0` and `emos_shadow_v0` are SHADOW.
4. Registry returns primary and shadow engines.
5. `ActiveEnginePolicy` accepts `gaussian_v0` and rejects shadow engines.
6. Shadow engines produce probabilities and warnings.
7. `ProbabilityEngineRunner` produces engine runs.
8. `ProbabilityComparisonBuilder` produces comparison.
9. `active_engine_id` remains `gaussian_v0`.
10. Manual outcome can be recorded.
11. `CalibrationService` creates calibration results.
12. `ModelPromotionGate` creates promotion decision.
13. Workstation API includes `probability_comparison`.
14. UI exposes comparison, calibration history, and registry.
15. `LIVE_EXECUTE` remains rejected.

## 10. Deferred to PWB-04

The following are explicitly deferred:
- real calibration data ingestion
- backtest memory
- historical market outcome archive
- settlement-source resolver
- calibration dashboards
- engine performance trend charts
- large-sample promotion evidence

## 11. Deferred to Model-Specific Future Rounds

The following require separate charters:
- real DEB implementation
- real EMOS implementation
- LGBM auxiliary model
- multi-model ensemble
- source weighting
- bias correction
- probability calibration curve

## 12. Deferred to Execution Future Rounds

The following are not part of PWB-03:
- live execution
- auto trading
- portfolio-level risk
- position sizing based on calibrated probability
- real fund management
- production Polymarket connector

## 13. No Further Expansion Rule

After this freeze:
- Do not add new PWB-03 features.
- Do not implement real DEB/EMOS inside PWB-03.
- Do not change active engine.
- Do not auto-promote shadow engines.
- Do not enable live trading.
- Do not add settlement resolver.

## 14. Next Round Entry

If continuing, open a new bounded round.

Recommended next round:

```text
Round PWB-04 - Real Calibration Data & Backtest Memory v0
```

Alternative next rounds:
- `Round PWB-04A - Real DEB Shadow Implementation`
- `Round PWB-04B - EMOS Shadow Evaluation`
- `Round PWB-04C - Test Isolation & App Factory Hardening`
- `Round PWB-04D - Polymarket Read-Only Connector v0`

## 15. Freeze Statement

PWB-03 is frozen as the first accepted Probability Governance baseline.
It establishes registry-based probability governance, shadow engine comparison, manual outcome calibration, and model promotion decisioning while preserving all no-live-execution safety boundaries.
