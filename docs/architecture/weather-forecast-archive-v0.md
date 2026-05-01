# Weather_Forecast_Archive_v0

## 1. Architecture Position

Weather Forecast Archive v0 is the weather-side evidence archive layer.

It sits after the existing weather intelligence flow:

```text
WeatherProbabilityProvider / WeatherView Builder
        ↓
WeatherView / EvidencePack / Forecast Observation
        ↓
WeatherForecastArchiveService
        ↓
weather_forecast_archive
weather_evidence_archive
weather_view_archive
```

It does not generate new forecasts, does not recompute probability, does not run backtests, and does not execute trading behavior.

It only preserves weather-side inputs that the system already observed or already constructed.

## 2. Problem It Solves

PWB-04E already preserves the market-side state:

- market price
- market spread
- market liquidity
- market question
- market source
- market timestamp

That still does not explain why the model produced a weather probability.

Later calibration and backtest work also needs to know:

- which weather source was used
- what the forecast expected value was
- what threshold was used
- whether the direction was `ABOVE` or `BELOW`
- what sigma was used
- what evidence pack existed
- how the `WeatherView` was structured

PWB-04F preserves:

```text
the weather-side evidence the system saw at that time
```

## 3. Relationship to Other Rounds

```text
PWB-01 - Execution Core
  scan / candidate / simulation / audit
PWB-02 - Weather Intelligence
  descriptor / evidence / weather view / Gaussian probability
PWB-03 - Probability Governance
  engine registry / comparison / calibration / promotion decision
PWB-04D - Polymarket Read-Only Connector
  read-only market discovery
PWB-04E - Market Snapshot Archive
  time-indexed market input archive
PWB-04F - Weather Forecast Archive
  time-indexed weather input archive
```

PWB-04F does not replace PWB-02. It only persists weather-side objects that PWB-02 already produces.

## 4. Core Objects

### 4.1 WeatherForecastArchiveRecord

Represents one archived forecast/source observation record.

Fields:

- `forecast_archive_id`
- `market_id`
- `weather_view_id`
- `evidence_pack_id`
- `city`
- `target_date`
- `source_id`
- `source_type`
- `metric`
- `unit`
- `expected_value`
- `expected_range_low`
- `expected_range_high`
- `sigma`
- `fetched_at`
- `archived_at`
- `raw_payload`
- `metadata`
- `archive_reason`

Purpose:

- preserve the source-level numeric weather input seen by the system

### 4.2 WeatherEvidenceArchiveRecord

Represents one archived evidence-pack record.

Fields:

- `evidence_archive_id`
- `market_id`
- `evidence_pack_id`
- `source_ids`
- `evidence_summary`
- `invalidation_rules`
- `confirmation_rules`
- `archived_at`
- `raw_payload`
- `metadata`
- `archive_reason`

Purpose:

- preserve the evidence and rule context that supported the weather-side interpretation

### 4.3 WeatherViewArchiveRecord

Represents one archived `WeatherView`.

Fields:

- `weather_view_archive_id`
- `market_id`
- `weather_view_id`
- `evidence_pack_id`
- `city`
- `target_date`
- `expected_value`
- `expected_range_low`
- `expected_range_high`
- `sigma`
- `threshold`
- `direction`
- `unit`
- `confidence`
- `archived_at`
- `raw_payload`
- `metadata`
- `archive_reason`

Purpose:

- preserve the structured weather-side input that later probability calculation depended on

### 4.4 WeatherArchiveSummary

Represents overall archive state.

Fields:

- `forecast_records`
- `evidence_records`
- `weather_view_records`
- `unique_markets`
- `by_source_type`
- `by_archive_reason`
- `latest_archived_at`

Purpose:

- power History UI
- judge archive volume
- judge whether later calibration sampling has enough weather-side inputs

### 4.5 WeatherArchiveBundle

Represents one market’s weather-side archive bundle.

Fields:

- `market_id`
- `forecasts`
- `evidence`
- `weather_views`

Purpose:

- align weather-side archive rows with market-side archive rows by `market_id`

## 5. Archive Reasons

PWB-04F accepts these archive reasons:

- `WEATHER_VIEW_CAPTURE`
- `PROBABILITY_BUILD_CAPTURE`
- `MANUAL_CAPTURE`
- `SCAN_CAPTURE`

### 5.1 WEATHER_VIEW_CAPTURE

Used when an API or operator explicitly asks to archive existing weather-side records.

### 5.2 PROBABILITY_BUILD_CAPTURE

Used after `WeatherProbabilityProvider.build_probability_view(...)`.

Rules:

- archive failure must not fail probability build
- archive must not change `model_probability`
- archive must not change `WeatherView`

### 5.3 MANUAL_CAPTURE

Used by manual archive endpoints.

### 5.4 SCAN_CAPTURE

Used when weather-side probability build occurs during scan and the weather-side objects are archived as a passive sidecar.

Rules:

- archive must not change candidate results
- archive failure must not fail scan

## 6. SQLite Tables

### 6.1 weather_forecast_archive

```sql
CREATE TABLE IF NOT EXISTS weather_forecast_archive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  forecast_archive_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  weather_view_id TEXT,
  evidence_pack_id TEXT,
  city TEXT,
  target_date TEXT,
  source_id TEXT NOT NULL,
  source_type TEXT NOT NULL,
  metric TEXT NOT NULL,
  unit TEXT NOT NULL,
  expected_value REAL,
  expected_range_low REAL,
  expected_range_high REAL,
  sigma REAL,
  fetched_at TEXT,
  archived_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT,
  archive_reason TEXT NOT NULL
);
```

### 6.2 weather_evidence_archive

```sql
CREATE TABLE IF NOT EXISTS weather_evidence_archive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  evidence_archive_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  evidence_pack_id TEXT NOT NULL,
  source_ids_json TEXT,
  evidence_summary_json TEXT,
  invalidation_rules_json TEXT,
  confirmation_rules_json TEXT,
  archived_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT,
  archive_reason TEXT NOT NULL
);
```

### 6.3 weather_view_archive

```sql
CREATE TABLE IF NOT EXISTS weather_view_archive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  weather_view_archive_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  weather_view_id TEXT NOT NULL,
  evidence_pack_id TEXT,
  city TEXT,
  target_date TEXT,
  expected_value REAL,
  expected_range_low REAL,
  expected_range_high REAL,
  sigma REAL,
  threshold REAL,
  direction TEXT NOT NULL,
  unit TEXT NOT NULL,
  confidence TEXT NOT NULL,
  archived_at TEXT NOT NULL,
  raw_payload_json TEXT,
  metadata_json TEXT,
  archive_reason TEXT NOT NULL
);
```

### 6.4 Indexes

Current accepted indexes include:

```sql
CREATE INDEX IF NOT EXISTS idx_weather_forecast_archive_market_id
ON weather_forecast_archive(market_id);
CREATE INDEX IF NOT EXISTS idx_weather_forecast_archive_weather_view_id
ON weather_forecast_archive(weather_view_id);
CREATE INDEX IF NOT EXISTS idx_weather_forecast_archive_archived_at
ON weather_forecast_archive(archived_at);
CREATE INDEX IF NOT EXISTS idx_weather_evidence_archive_market_id
ON weather_evidence_archive(market_id);
CREATE INDEX IF NOT EXISTS idx_weather_evidence_archive_evidence_pack_id
ON weather_evidence_archive(evidence_pack_id);
CREATE INDEX IF NOT EXISTS idx_weather_view_archive_market_id
ON weather_view_archive(market_id);
CREATE INDEX IF NOT EXISTS idx_weather_view_archive_weather_view_id
ON weather_view_archive(weather_view_id);
```

Future reason/source-type indexes are compatible extensions if query volume requires them.

## 7. Archive Service

### 7.1 Location

`backend/archive/weather_forecast_archive_service.py`

### 7.2 Responsibilities

- archive forecast records
- archive evidence records
- archive weather-view records
- archive existing latest weather-side bundle from repository state
- list recent forecasts
- list recent evidence
- list recent weather views
- return market bundle
- return summary

### 7.3 Hard Boundary

`WeatherForecastArchiveService` must not call:

- `WeatherProbabilityProvider`
- `StrategyRunner`
- `Simulator`
- `RiskManager`
- `Execution`
- `CalibrationService`
- `ModelPromotionGate`

It may only use repository save/list/query methods.

## 8. API Design

Accepted archive APIs:

- `GET /api/weather-archive/summary`
- `GET /api/weather-archive/views`
- `GET /api/weather-archive/forecasts`
- `GET /api/weather-archive/evidence`
- `GET /api/weather-archive/market/{market_id}`
- `POST /api/weather-archive/view`
- `POST /api/weather-archive/forecast`
- `POST /api/weather-archive/evidence`
- `POST /api/weather-archive/latest/{market_id}`

### 8.1 GET /api/weather-archive/summary

Purpose:

- view overall weather archive state

### 8.2 GET /api/weather-archive/market/{market_id}

Purpose:

- view one market’s weather-side archive bundle

### 8.3 POST /api/weather-archive/latest/{market_id}

Purpose:

- archive the repository’s already-available latest weather-side records for one market

Hard boundary:

- no weather fetch
- no `WeatherProbabilityProvider` call
- no `StrategyRunner`
- no candidate creation
- no simulation
- no execution

### 8.4 POST /api/weather-archive/view

Purpose:

- manually archive one weather-view record

### 8.5 POST /api/weather-archive/forecast

Purpose:

- manually archive one forecast/source record

### 8.6 POST /api/weather-archive/evidence

Purpose:

- manually archive one evidence record

## 9. Capture Hooks

### 9.1 Probability Build Hook

Passive optional hook inside:

`WeatherProbabilityProvider.build_probability_view(...)`

Behavior:

- after normal weather-side objects are built and saved, archive may persist them
- archive failure must not fail probability build
- archive must not change `model_probability`
- archive must not change downstream strategy semantics

### 9.2 Weather API Hook

Weather-side APIs may later expose explicit archive switches for weather-view capture.

### 9.3 Scan Capture Hook

If scan triggers the normal weather probability flow, weather-side archiving may happen as a passive sidecar through the probability-build hook.

Rules:

- archive failure must not fail scan
- archive must not change candidate count
- archive must not re-run weather logic

## 10. UI Design

In this workspace, the actual UI shell is the Streamlit `weather-dashboard`, not a React `frontend/...` app.

Target panel responsibilities:

- weather archive summary
- recent forecasts
- recent evidence
- recent weather views
- market weather bundle lookup
- archive latest weather view action

Allowed actions:

- Load Summary
- Load Recent Forecasts
- Load Recent Evidence
- Load Recent Weather Views
- Archive Latest Weather View
- Load Market Weather Bundle

Forbidden actions:

- Trade
- Execute
- Simulate
- Backtest Now
- Promote Model
- Auto Calibrate
- Go Live
- Connect Wallet
- Place Order
- Cancel Order

## 11. Relationship to PWB-05 Calibration / Backtest

PWB-04F does not compute calibration itself.

It prepares the weather-side half of a future sample:

```text
MarketSnapshotArchiveRecord
+ WeatherForecastArchiveRecord
+ WeatherViewArchiveRecord
+ ProbabilityEngineRun
+ MarketOutcome
= CalibrationSample
```

This later lets the system ask:

- what was the market price?
- what was the forecast value?
- what was the model probability?
- what was the outcome?
- was the model closer than the market?

## 12. Relationship to DEB / EMOS

PWB-04F is a prerequisite, not the full DEB or EMOS implementation.

It preserves inputs such as:

- `source_id`
- `source_type`
- `metric`
- `unit`
- `expected_value`
- `sigma`
- `target_date`
- `archived_at`

Later rounds still need:

- actual weather outcome
- error computation
- bias windows
- broader probabilistic calibration sampling

## 13. Safety Boundary

PWB-04F must remain:

- read-only weather archive
- no trading
- no wallet
- no order
- no cancel
- no execution
- no auto calibration
- no model promotion

Weather archive behavior must not trigger:

- `StrategyRunner`
- `Simulator`
- `Execution`
- `CalibrationService`
- `ModelPromotionGate`

The only accepted exception is passive post-build or post-scan sidecar recording, which must not alter the original flow result.

## 14. Failure Handling

On archive failure:

- return structured warning where appropriate
- do not fail scan
- do not fail probability build
- do not change `model_probability`
- do not change execution mode
- do not retry indefinitely

For archive-latest:

- if latest weather-side state does not exist, return warning/empty archive result
- do not trigger new weather fetch

## 15. Acceptance Baseline

PWB-04F passes if:

1. weather archive models serialize
2. all three weather archive tables exist
3. repository can save/query forecast archive
4. repository can save/query evidence archive
5. repository can save/query weather-view archive
6. summary works
7. market bundle works
8. archive service can archive forecast/evidence/view
9. archive-latest archives existing latest weather-side state
10. archive-latest does not fetch weather, run strategy, simulate, or execute
11. optional probability-build archive path works
12. scan candidate count is unchanged
13. `LIVE_EXECUTE` remains rejected

## 16. Not Included in v0

Not included:

- real weather outcome resolver
- real calibration engine
- real backtest engine
- forecast performance metrics
- source bias estimation
- DEB implementation
- EMOS implementation
- ensemble member archive
- automatic model promotion
- trading execution
- portfolio PnL

## 17. Recommended Next Path

Recommended next round:

- `PWB-04G - Outcome Resolver Read-Only v0`

Alternative:

- `PWB-05 - Real Calibration Data & Backtest Memory v0`

Suggested sequence:

```text
PWB-04E Market Snapshot Archive
-> PWB-04F Weather Forecast Archive
-> PWB-04G Outcome Resolver Read-Only
-> PWB-05 Real Calibration Data & Backtest Memory
-> PWB-05A Real DEB Shadow
-> PWB-05B EMOS Evaluation
```
