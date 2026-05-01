# Round_PWB-03_Accepted_Path_Inventory

## 1. Purpose
This document freezes the accepted files and implementation paths for:

```text
Round PWB-03 - Probability Governance & Calibration v0
```

It records what is now part of the accepted baseline.

## 2. Accepted Backend Model Files

`backend/models/probability_governance.py`

Accepted objects:
- `ProbabilityEngineConfig`
- `ProbabilityEngineRun`
- `ProbabilityComparisonView`
- `MarketOutcome`
- `CalibrationResult`
- `EnginePromotionDecision`

Accepted enums:
- `ProbabilityEngineType`
- `DisagreementLevel`
- `OutcomeStatus`
- `PromotionDecisionType`

## 3. Accepted Probability Governance Files

`backend/probability/probability_engine_registry.py`
`backend/probability/deb_shadow_engine.py`
`backend/probability/emos_shadow_engine.py`
These are shadow placeholder engines only.
`backend/probability/probability_engine_runner.py`
`backend/probability/probability_comparison_builder.py`
`backend/probability/active_engine_policy.py`
`backend/probability/calibration_metrics.py`
`backend/probability/market_outcome_service.py`
`backend/probability/calibration_service.py`
`backend/probability/model_promotion_gate.py`

Accepted Responsibilities:

| File | Accepted Responsibility |
| --- | --- |
| `probability_engine_registry.py` | Load primary/shadow/disabled probability engine configs |
| `deb_shadow_engine.py` | Placeholder DEB shadow probability transformation |
| `emos_shadow_engine.py` | Placeholder EMOS shadow probability transformation |
| `probability_engine_runner.py` | Run enabled engines against WeatherView and persist runs |
| `probability_comparison_builder.py` | Build active/shadow comparison view |
| `active_engine_policy.py` | Enforce active engine eligibility |
| `calibration_metrics.py` | Brier score, absolute error, probability bucket |
| `market_outcome_service.py` | Manual market outcome recording |
| `calibration_service.py` | Generate `CalibrationResult` from outcome and engine runs |
| `model_promotion_gate.py` | Generate `EnginePromotionDecision` without mutating config |

## 4. Accepted Storage Extensions

Accepted schema additions:
- `probability_engine_configs`
- `probability_engine_runs`
- `probability_comparisons`
- `market_outcomes`
- `calibration_results`
- `engine_promotion_decisions`

Accepted default engine configs:

```text
gaussian_v0:
  engine_type = PRIMARY
  enabled = true
  can_be_primary = true
deb_shadow_v0:
  engine_type = SHADOW
  enabled = true
  can_be_primary = false
emos_shadow_v0:
  engine_type = SHADOW
  enabled = true
  can_be_primary = false
```

Accepted repository methods:
- `save_probability_engine_config`
- `list_probability_engine_configs`
- `get_probability_engine_config`
- `save_probability_engine_run`
- `list_probability_engine_runs_for_market`
- `list_probability_engine_runs_for_engine`
- `save_probability_comparison`
- `get_latest_probability_comparison`
- `save_market_outcome`
- `get_latest_market_outcome`
- `save_calibration_result`
- `list_calibration_results_for_engine`
- `list_calibration_results_for_market`
- `save_engine_promotion_decision`
- `get_latest_engine_promotion_decision`

## 5. Accepted API Files

`backend/api/routes_probability_governance.py`

Accepted endpoints:
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

## 6. Accepted Workstation API Update

Accepted update:
- `backend/api/routes_workstation.py`

Accepted additional fields:
- `probability_comparison`
- `market_outcome`

## 7. Accepted Frontend Components

`frontend/components/ProbabilityComparisonPanel.tsx`
`frontend/components/CalibrationHistoryPanel.tsx`
`frontend/components/ProbabilityEngineRegistryTable.tsx`

Accepted Responsibilities:

| Component | Purpose |
| --- | --- |
| `ProbabilityComparisonPanel.tsx` | Show active + shadow probability runs and disagreement |
| `CalibrationHistoryPanel.tsx` | Show calibration results and allow manual outcome/calibration workflow |
| `ProbabilityEngineRegistryTable.tsx` | Show engine registry and promotion decision action |

## 8. Accepted Frontend Page Updates

`frontend/pages/WorkstationPage.tsx`
`frontend/pages/HistoryPage.tsx`
`frontend/pages/SettingsPage.tsx`

Accepted updates:
- `WorkstationPage` shows `ProbabilityComparisonPanel`.
- `HistoryPage` shows `CalibrationHistoryPanel`.
- `SettingsPage` shows `ProbabilityEngineRegistryTable`.

## 9. Accepted Type Extensions

`frontend/types/weather.ts`

Accepted frontend types:
- `ProbabilityEngineRun`
- `ProbabilityComparison`
- `MarketOutcome`
- `CalibrationResult`
- `ProbabilityEngineConfig`

Accepted update to `WorkstationPayload`:
- `probability_comparison`
- `market_outcome`

## 10. Accepted Test File

`tests/test_pwb03_probability_governance.py`

Accepted test groups:
- engine configs
- engine registry
- shadow engines
- engine runner
- comparison builder
- comparison persistence
- active engine policy
- calibration metrics
- market outcome
- calibration service
- model promotion gate
- probability governance APIs
- workstation probability comparison
- live execution safety

## 11. Accepted Runtime Defaults

```text
active_engine_id = gaussian_v0
primary_engine = gaussian_v0
shadow_engines = deb_shadow_v0, emos_shadow_v0
minimum_evidence_count = 30
max_avg_brier_score = 0.20
max_avg_absolute_error = 0.35
LIVE_EXECUTE = rejected
live execution remains disabled
```

## 12. Accepted Example Baseline

Using market:

```text
market_id = mock_weather_strong_yes
question = Will Tokyo high temperature exceed 30C on June 1?
```

Accepted comparison behavior:

```text
gaussian_v0 probability ~= 0.684
deb_shadow_v0 probability ~= 0.675
emos_shadow_v0 probability ~= 0.656
active_engine_id = gaussian_v0
active_probability ~= 0.684
shadow engines do not drive trading
```

Accepted calibration behavior after manual positive outcome:

```text
actual_outcome = 1
CalibrationResult generated for:
- gaussian_v0
- deb_shadow_v0
- emos_shadow_v0
```

Accepted promotion behavior:

```text
gaussian_v0 -> KEEP_PRIMARY
deb_shadow_v0 -> NEEDS_MORE_DATA or KEEP_SHADOW
emos_shadow_v0 -> NEEDS_MORE_DATA or KEEP_SHADOW
```

## 13. Not Accepted Paths

The following are not accepted in PWB-03:
- `backend/probability/real_deb_engine.py`
- `backend/probability/real_emos_engine.py`
- `backend/probability/lgbm_engine.py`
- `backend/probability/online_calibrator.py`
- `backend/probability/automatic_engine_promoter.py`
- `backend/connectors/settlement_resolver.py`
- `backend/execution/live_executor.py`
- `backend/execution/auto_trader.py`

These may be introduced only in later rounds if explicitly chartered.

## 14. Inventory Status

PWB-03 accepted path inventory is complete.
