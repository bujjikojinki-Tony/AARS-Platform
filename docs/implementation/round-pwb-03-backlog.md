# Round PWB-03 Backlog

Status: Draft
Date: 2026-04-29
Scope: Probability Governance & Calibration v0

## Objective
Build a governance layer that can run multiple probability engines on the same `WeatherView`, compare their outputs, persist calibration evidence, and keep `gaussian_v0` as the active primary unless a promotion gate approves a change.

## Non-Goals
- No live trading
- No auto trading
- No real DEB implementation
- No real EMOS implementation
- No LGBM training
- No production outcome resolver
- No portfolio-level risk expansion
- No subscription, payment, or Telegram expansion

## Execution Order

### 1. Backend Model and Storage Foundation
Create the governance data model and SQLite tables first so later steps can persist comparison and calibration history.

Deliverables:
- `ProbabilityEngineConfig`
- `ProbabilityEngineRun`
- `ProbabilityComparisonView`
- `MarketOutcome`
- `CalibrationResult`
- `EnginePromotionDecision`
- SQLite tables for engine configs, runs, comparisons, outcomes, calibration results, and promotion decisions
- Repository read/write helpers for each entity

Acceptance:
- Tables initialize cleanly in the existing local database
- Repository methods can save and fetch one record for each entity

### 2. Engine Registry and Active Policy
Register the supported engines and define what can be active.

Initial registry:
- `gaussian_v0` as `PRIMARY`
- `deb_shadow_v0` as `SHADOW`
- `emos_shadow_v0` as `SHADOW`

Rules:
- Only `can_be_primary = true` engines may become active
- Disabled engines do not run
- Shadow engines can run for comparison, but cannot drive strategy output
- Promotion must flow through the promotion gate

Acceptance:
- Registry lists all three engines
- `gaussian_v0` is the default active primary
- Shadow engines are present but non-primary

### 3. Shadow Engines v0
Add deterministic placeholders that exercise the governance pipeline without claiming real modeling value.

Behavior:
- `deb_shadow_v0 = clamp(gaussian_probability * 0.95 + 0.025)`
- `emos_shadow_v0 = clamp(0.5 + (gaussian_probability - 0.5) * 0.85)`

Acceptance:
- Both shadow engines run on the same `WeatherView`
- Both produce stable, explainable outputs
- Neither engine can be selected as active primary by default

### 4. Comparison and Calibration
Build the comparison view and calibration metrics that sit on top of engine runs.

Deliverables:
- `ProbabilityEngineRunner`
- `ProbabilityComparisonBuilder`
- `CalibrationMetrics`
- `CalibrationRepository`
- `ModelPromotionGate`

Metrics:
- Brier score
- Absolute error
- Probability buckets
- Disagreement spread across engines

Acceptance:
- A single `WeatherView` produces a comparison view with active plus shadow runs
- Calibration records can be written once outcomes are available
- Promotion gate returns a deterministic decision for each engine

### 5. Governance API
Expose the registry, comparison, calibration, outcome, and promotion surfaces through backend routes.

Planned routes:
- `GET /api/probability/engines`
- `POST /api/probability/compare/{market_id}`
- `GET /api/probability/comparison/{market_id}`
- `POST /api/probability/outcomes`
- `GET /api/probability/outcomes/{market_id}`
- `POST /api/probability/calibrate/{market_id}`
- `GET /api/probability/calibration/{engine_id}`
- `POST /api/probability/promotion/{engine_id}`
- `GET /api/probability/promotion/{engine_id}`

Acceptance:
- API can list engines
- API can create and fetch comparison views
- API can record and query outcomes
- API can create and query calibration results
- API can return a promotion decision

### 6. UI Surfaces
Expose the governance layer in the existing dashboard without changing the shell.

Planned UI sections:
- Workstation probability comparison panel
- Settings probability engine registry section
- History calibration panel

Acceptance:
- Workstation shows active engine, shadow runs, spread, disagreement, and selection reason
- Settings shows registry status for each engine
- History shows calibration rows by engine and market

### 7. Verification and Freeze
Lock the round with focused acceptance tests and explicit non-goals.

Acceptance targets:
- `ProbabilityEngineRegistry`
- `ProbabilityEngineRun`
- `ProbabilityComparisonView`
- `MarketOutcome`
- `CalibrationResult`
- `EnginePromotionDecision`
- Probability governance API
- Probability comparison panel
- LIVE_EXECUTE remains rejected

Stop condition:
Once the registry, shadow runs, comparison view, calibration records, promotion gate, API, and comparison panel are all passing, freeze PWB-03 and do not expand into real DEB, real EMOS, LGBM, or live execution.
