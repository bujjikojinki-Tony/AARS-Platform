# Polymarket Bot Architecture Refinement v1

## 1. Current Conclusion

After the current comparison and runtime review, the Polymarket Bot should not be positioned as a simple "auto trading bot".

It should be positioned as a:

**Governed Weather-Market Research & Execution Gateway**

That means the system flow becomes:

weather evidence collection  
→ probability calibration  
→ market mispricing detection  
→ opportunity workstation analysis  
→ governed command approval  
→ simulation / small-size execution  
→ replay history and rule updates

After comparing the two reference GitHub projects, the absorption path is:

| Project | What to absorb | What not to absorb directly |
|---|---|---|
| `hcharper/polyBot-Weather` | strategy runner, simulation/live modes, risk manager, SQLite, edge/z-score/Kelly, paper trading | weather evidence layer is too thin to become the final weather-intelligence architecture |
| `yangyuan-zhen/PolyWeather` | multi-source weather evidence, DEB, calibrated probability buckets, TAF/METAR, city decision cards, monitoring, prewarm, ops | subscriptions, payments, points, and commercialization growth modules should not be absorbed for now |

`hcharper/polyBot-Weather` is clearly oriented toward a multi-strategy Polymarket bot with weather arbitrage, crypto prediction, and binary arbitrage. Its edge comes from better probability estimation rather than millisecond-scale speed. Its weather strategy uses NOAA, Gaussian distribution, RMSE, edge, z-score, and Kelly sizing.

`PolyWeather` is a more complete production-grade weather intelligence stack with 52 cities, multi-source weather aggregation, DEB dynamic error balancing, calibrated probability buckets, Polymarket quote mapping, city decision cards, TAF/METAR, ops dashboard, SQLite, and system health / status / metrics.

## 2. New System Positioning

### 2.1 What this system should not do

At the current stage, it should not:

1. act as a fully automatic large-size trading robot
2. act as a commercial subscription platform
3. implement a full SaaS payment system
4. behave as a high-frequency arbitrage system
5. depend on an unexplainable black-box prediction system

### 2.2 What this system should do

At the current stage, it should:

1. provide an explainable weather-market analysis system
2. provide a Polymarket weather-market mispricing scanner
3. enforce simulation-first and small-size approval execution
4. maintain a workstation with traceable evidence chains
5. support replay, calibration, and governed strategy research

## 3. Seven-Layer Architecture v1

The refined architecture is:

1. Source Layer
2. Evidence Normalization Layer
3. Weather Intelligence Layer
4. Probability Governance Layer
5. Market Divergence Layer
6. Governance & Execution Layer
7. Product / Ops Layer

## 4. Layer 1 — Source Layer

### Goal

Unify access to market data, weather data, observation data, and future expandable sources.

### Initial sources

**Market Sources**
- Polymarket CLOB / API
- Polymarket market metadata
- Polymarket price / liquidity / spread

**Weather Sources**
- Open-Meteo
- NOAA
- METAR
- TAF
- JMA AMeDAS
- KMA
- HKO
- CWA
- CMA / NMC
- MGM

**Optional Future Sources**
- Pyth
- Kalshi
- crypto price feeds
- social / news / event feeds

`hcharper` already contains connectors for Polymarket, NOAA, Pyth, and related market inputs, while `PolyWeather` covers a broader weather source stack including Open-Meteo, METAR, TAF, JMA, KMA, HKO, CWA, and NOAA.

### Output object

`SourceRecord`

- `source_id`
- `source_type`
- `fetched_at`
- `location`
- `valid_time`
- `raw_payload`
- `freshness_status`
- `trust_level`

## 5. Layer 2 — Evidence Normalization Layer

### Goal

Convert market questions and weather evidence into a unified object model, resolving the mismatch between "market language" and "weather language".

### Core modules

- `market_question_parser.py`
- `settlement_source_mapper.py`
- `station_resolver.py`
- `bucket_parser.py`
- `unit_normalizer.py`
- `raw_evidence_archiver.py`

### Responsibilities

1. parse Polymarket questions
2. identify city, date, threshold, direction, and temperature units
3. map settlement sources
4. map observation stations
5. normalize °F / °C
6. archive raw evidence
7. flag stale / missing / conflicting evidence

### Standard output

`EvidencePack`

- `market_id`
- `question`
- `city`
- `date`
- `bucket_type`
- `threshold`
- `direction`
- `settlement_source`
- `station_candidates`
- `weather_sources`
- `raw_links`
- `normalized_values`
- `evidence_freshness`
- `evidence_conflict_level`

## 6. Layer 3 — Weather Intelligence Layer

### Goal

Convert weather data into tradable market-oriented weather judgments.

### v1 capabilities

1. multi-model weather forecasting
2. official observation source confirmation
3. METAR / TAF assisted judgment
4. daily high center estimation
5. peak-window identification
6. evidence chain generation
7. invalidation / confirmation rule generation

### Modules

- `weather_source_registry.py`
- `multi_model_collector.py`
- `deb_blender.py`
- `observation_trend_analyzer.py`
- `taf_signal_parser.py`
- `official_station_reconciler.py`
- `weather_intelligence_summary.py`

### DEB reference

`PolyWeather`'s DEB is an important reference. It is not a simple voting mechanism. It blends multi-model highs and outputs settlement-oriented calibrated probability buckets. Its production notes treat DEB, calibrated probability buckets, TAF timing, and official nearby-network support as core capabilities.

### Output object

`WeatherView`

- `city`
- `date`
- `expected_high_center`
- `expected_high_range`
- `deb_blended_high`
- `model_cluster`
- `official_observation_status`
- `taf_confirmation`
- `peak_window`
- `confidence`
- `evidence_chain`
- `invalidation_rules`
- `confirmation_rules`

## 7. Layer 4 — Probability Governance Layer

### Goal

Convert `WeatherView` into market bucket probabilities while governing the usage boundary of each probability engine.

### Engine layers

- `Engine 0` — Gaussian v0
- `Engine 1` — DEB bucket probability
- `Engine 2` — Calibrated probability
- `Engine 3` — EMOS shadow
- `Engine 4` — LGBM auxiliary point forecast

### v1 principles

1. Gaussian can serve as the minimum viable baseline
2. DEB should serve as the primary weather judgment input
3. calibrated probability should be the final production candidate
4. EMOS remains shadow-only at first
5. LGBM acts only as an auxiliary point forecast, not a weather-model replacement

`PolyWeather` already uses calibrated model probability as the primary production panel while keeping EMOS / LGBM in evaluation or shadow modes until offline evaluation and rollout approval are complete.

### Output object

`ProbabilityView`

- `market_id`
- `bucket`
- `model_probability`
- `gaussian_probability`
- `deb_probability`
- `calibrated_probability`
- `active_engine`
- `shadow_engine_outputs`
- `brier_score_history`
- `crps_history`
- `calibration_status`
- `promotion_status`

## 8. Layer 5 — Market Divergence Layer

### Goal

Measure the divergence between weather-model probability and market-implied probability.

### Core metrics

- `market_implied_probability`
- `model_probability`
- `model_market_difference`
- `edge_percent`
- `z_score`
- `liquidity_score`
- `spread_score`
- `slippage_estimate`
- `confidence_tier`

`hcharper`'s weather strategy uses thresholds such as edge above 10% and z-score ≥ 1.5 as trade triggers, and uses Kelly Criterion for sizing. It also stores trades, signals, and market snapshots in SQLite for replay and backtesting.

### Output object

`OpportunityCandidate`

- `market_id`
- `question`
- `city`
- `date`
- `bucket`
- `market_probability`
- `model_probability`
- `edge_percent`
- `z_score`
- `liquidity`
- `spread`
- `slippage`
- `confidence_tier`
- `action_candidate`
- `reject_reason`

## 9. Layer 6 — Governance & Execution Layer

### Goal

Turn opportunity candidates into governed actions rather than direct autonomous trades.

### Execution modes

- `Mode 0` — Observe Only
- `Mode 1` — Simulation
- `Mode 2` — Paper Trade
- `Mode 3` — Approve Small
- `Mode 4` — Live Execute
- `Mode 5` — Blocked

### Governance gates

**Evidence Gate**
- evidence freshness valid
- settlement source mapped
- no unresolved source conflict

**Probability Gate**
- active engine approved
- shadow engine not directly used
- calibration status acceptable

**Market Gate**
- edge above threshold
- z-score above threshold
- liquidity sufficient
- spread acceptable

**Risk Gate**
- max position not exceeded
- max daily loss not exceeded
- circuit breaker inactive
- exposure concentration acceptable

**Approval Gate**
- approval required for live trade
- approval validity window active
- action reason recorded

`hcharper` already contains simulation mode and explicit live mode switching through a `--live` style boundary, plus core risk manager, simulation, and datastore components. This is a strong implementation reference for our governance and execution layer.

### Output object

`ExecutionDecision`

- `decision_id`
- `candidate_id`
- `mode`
- `action`
- `approved_by`
- `approval_valid_until`
- `position_size`
- `risk_status`
- `execution_status`
- `rollback_available`
- `audit_log`

## 10. Layer 7 — Product / Ops Layer

### Page inventory

1. Opportunity Board
2. Workstation
3. Pipeline
4. Market
5. Charts
6. History
7. Evidence / Raw
8. Command
9. Settings
   - Alerts & Rules
   - Data & Source
   - System

## 11. Page Synchronization Design

### 11.1 Opportunity Board

**New positioning**

`Opportunity Board = model-market divergence scanner`

**Table fields**

- Market
- City
- Date
- Bucket
- Market Probability
- Model Probability
- Model-Market Difference
- Edge %
- Z-score
- Liquidity
- Spread
- Evidence Freshness
- Confidence Tier
- Risk Gate
- Action Status

**Row states**

- Candidate
- Watch
- Simulate
- Approve Small
- Blocked
- Executed
- Expired

**Primary buttons**

- Open Workstation
- Refresh Evidence
- Simulate
- Approve Small
- Block Market
- Export Evidence Pack

### 11.2 Workstation

**New positioning**

`Workstation = single-market deep analysis console`

**Page sections**

A. Market Header  
B. Weather Evidence Panel  
C. Probability Panel  
D. Market Divergence Panel  
E. Decision Panel  
F. Execution Panel  
G. Raw Evidence Drawer

**Decision outputs**

- BUY YES
- BUY NO
- WAIT
- BLOCKED
- SIMULATE ONLY
- NEEDS MORE EVIDENCE

**Must display**

1. settlement source
2. observation station
3. weather model center value
4. probability engine source
5. market price
6. model-market difference
7. invalidation rule
8. confirmation rule
9. action gate status

### 11.3 Pipeline

**New positioning**

`Pipeline = evidence-to-execution trace map`

**Flow**

Market Discovery  
→ Question Parsing  
→ Source Fetch  
→ Evidence Normalization  
→ Weather Intelligence  
→ Probability Governance  
→ Market Divergence  
→ Risk Gate  
→ Approval Gate  
→ Execution / Simulation  
→ History / Calibration

**Node states**

- Idle
- Running
- Success
- Warning
- Blocked
- Failed
- Stale

### 11.4 Command

**New positioning**

`Command = governed action console`

**Command types**

- `/run scan`
- `/refresh evidence <market_id>`
- `/simulate <candidate_id>`
- `/approve_small <candidate_id>`
- `/block <market_id>`
- `/export_evidence <market_id>`
- `/set_mode simulation`
- `/set_mode observe_only`
- `/promote_engine <engine_id>`

**Command path**

Command Parse  
→ Intent Resolution  
→ Gate Check  
→ Approval Window  
→ Execution Mode Check  
→ Audit Log

### 11.5 Evidence / Raw

**New positioning**

`Evidence / Raw = source trace and audit surface`

**Displayed content**

- raw Polymarket metadata
- raw weather API payload
- parsed market question
- station mapping
- settlement source mapping
- forecast model outputs
- METAR
- TAF
- official observation
- evidence freshness
- evidence conflict

### 11.6 History

**New positioning**

`History = replay, calibration, and performance memory`

**Tables**

- `market_snapshots`
- `weather_snapshots`
- `signals`
- `opportunity_candidates`
- `execution_decisions`
- `paper_trades`
- `live_trades`
- `daily_performance`
- `calibration_results`
- `blocked_markets`

`hcharper` already stores snapshots, trades, signals, arbitrage opportunities, and daily performance to SQLite. This maps naturally to our replay and backtesting memory layer.

### 11.7 Settings / Alerts & Rules

**New positioning**

`Settings / Alerts & Rules = strategy and governance rule registry`

**Configuration areas**

**Trading Rules**
- `min_edge_percent`
- `min_z_score`
- `max_position_percent`
- `max_daily_loss`
- `max_slippage`
- `max_open_positions`

**Weather Rules**
- `stale_evidence_timeout`
- `settlement_source_required`
- `taf_required_for_airport_contract`
- `official_station_priority`
- `source_conflict_threshold`

**Probability Rules**
- `active_engine`
- `allow_shadow_engine`
- `promotion_metric_required`
- `min_brier_improvement`
- `min_crps_improvement`

**Alert Rules**
- `edge_cross_threshold`
- `source_stale`
- `source_failure`
- `circuit_breaker_triggered`
- `model_market_difference_jump`

### 11.8 Settings / Data & Source

**New positioning**

`Settings / Data & Source = source registry and trust control`

**Fields**

- Source Name
- Source Type
- Enabled
- Trust Level
- Refresh Interval
- Last Success
- Last Failure
- Latency
- Freshness
- Fallback Source
- Shadow Only

### 11.9 Settings / System

**New positioning**

`Settings / System = runtime health and operations surface`

**Metrics**

- `scanner_status`
- `runner_status`
- `db_status`
- `cache_hit_rate`
- `prewarm_status`
- `queue_length`
- `execution_mode`
- `alert_relay_status`
- `healthz`
- `metrics`
- `last_error`

`PolyWeather` already exposes `/healthz`, `/api/system/status`, `/metrics`, prewarm worker status, ops dashboard signals, and cache hit/miss runtime signals. These are strong references for the System page.

## 12. Backend Module Proposal

### 12.1 Directory structure

```text
polymarket-bot/
  backend/
    app.py
    sources/
      polymarket_source.py
      open_meteo_source.py
      noaa_source.py
      metar_source.py
      taf_source.py
      jma_source.py
      hko_source.py
      kma_source.py
      cwa_source.py
    normalization/
      market_question_parser.py
      bucket_parser.py
      station_resolver.py
      settlement_source_mapper.py
      unit_normalizer.py
    weather/
      weather_source_registry.py
      multi_model_collector.py
      deb_blender.py
      observation_trend_analyzer.py
      taf_signal_parser.py
      weather_view_builder.py
    probability/
      probability_engine_registry.py
      gaussian_engine.py
      deb_probability_engine.py
      calibrated_probability_engine.py
      emos_shadow_engine.py
      calibration_metrics.py
    market/
      market_probability.py
      divergence_scanner.py
      opportunity_ranker.py
    execution/
      strategy_runner.py
      risk_manager.py
      simulator.py
      paper_trader.py
      live_executor.py
      approval_gate.py
      circuit_breaker.py
    governance/
      rule_registry.py
      action_policy.py
      evidence_gate.py
      probability_gate.py
      market_gate.py
      audit_log.py
    storage/
      db.py
      models.py
      repositories.py
    api/
      routes_opportunities.py
      routes_workstation.py
      routes_pipeline.py
      routes_command.py
      routes_settings.py
      routes_history.py
      routes_system.py
```

### 12.2 Frontend structure

```text
frontend/
  pages/
    OpportunityBoardPage.tsx
    WorkstationPage.tsx
    PipelinePage.tsx
    MarketPage.tsx
    ChartsPage.tsx
    HistoryPage.tsx
    EvidenceRawPage.tsx
    CommandPage.tsx
    SettingsPage.tsx
  components/
    MarketHeader.tsx
    EvidenceChainPanel.tsx
    ProbabilityPanel.tsx
    DivergencePanel.tsx
    DecisionGatePanel.tsx
    ExecutionControlPanel.tsx
    SourceHealthTable.tsx
    RuleRegistryTable.tsx
    SystemStatusPanel.tsx
```

## 13. MVP Implementation Rounds

### Round PWB-01 — Execution Core v0

**Goal**

First make the system able to scan, generate signals, simulate, and record decisions.

**Backend**

- `strategy_runner.py`
- `risk_manager.py`
- `simulator.py`
- `datastore.py`
- `weather_edge_strategy.py`
- `binary_arb_strategy.py`

**Frontend**

- Opportunity Board
- History
- Command
- Settings / Alerts & Rules

**Acceptance**

1. can scan markets
2. can generate `OpportunityCandidate`
3. can paper trade
4. can write to SQLite
5. must not default to live trading

### Round PWB-02 — Weather Intelligence v0

**Goal**

Upgrade weather-market analysis from simple forecasting to an evidence pack.

**Backend**

- `market_question_parser.py`
- `settlement_source_mapper.py`
- `weather_source_registry.py`
- `multi_model_collector.py`
- `gaussian_probability_v0.py`
- `evidence_pack.py`

**Frontend**

- Workstation
- Evidence / Raw
- Pipeline
- Data & Source

**Acceptance**

Each weather market must be parsable into:

- `city`
- `date`
- `bucket`
- `threshold`
- `direction`
- `settlement_source`
- `weather_sources`
- `model_probability`
- `market_probability`
- `evidence_chain`

### Round PWB-03 — Probability Governance v0

**Goal**

Introduce probability engine registration, shadow mode, and calibration evaluation.

**Backend**

- `probability_engine_registry.py`
- `gaussian_engine.py`
- `deb_engine.py`
- `emos_shadow_engine.py`
- `calibration_metrics.py`
- `model_promotion_gate.py`

**Frontend**

- Workstation Probability Panel
- Charts
- History
- System

**Acceptance**

The same market must be able to show:

- Gaussian probability
- DEB probability
- Calibrated probability
- Shadow probability
- Brier / CRPS / hit-rate history

## 14. Recommended Obsidian Location

```text
03_Projects/Polymarket_Bot/Architecture/
  Polymarket_Bot_Architecture_Refinement_v1.md
```

Related companion documents:

```text
03_Projects/Polymarket_Bot/Research/
  polyBot_Weather_Review_v0.md
  PolyWeather_Review_v0.md
  GitHub_Comparison_Summary_v0.md
03_Projects/Polymarket_Bot/Design/
  Opportunity_Board_Update_v1.md
  Workstation_Update_v1.md
  Command_Page_Update_v1.md
  Settings_Update_v1.md
03_Projects/Polymarket_Bot/Governance/
  Execution_Gate_Rules_v0.md
  Probability_Engine_Governance_v0.md
  Evidence_Gate_Rules_v0.md
```

## 15. Recommended Repo Location

```text
docs/
  architecture/
    polymarket-bot-architecture-refinement-v1.md
    weather-intelligence-layer-v0.md
    probability-governance-layer-v0.md
    execution-core-v0.md
  research/
    polybot-weather-review-v0.md
    polyweather-review-v0.md
    github-comparison-summary-v0.md
  ui/
    opportunity-board-update-v1.md
    workstation-update-v1.md
    command-page-update-v1.md
    settings-update-v1.md
  governance/
    evidence-gate-rules-v0.md
    probability-engine-governance-v0.md
    execution-gate-rules-v0.md
```

## 16. Current Latest Stable View

**Latest Stable View — Polymarket Bot Research**

Current accepted direction:

The system should become a governed weather-market research and execution gateway.

Accepted external references:

1. `hcharper/polyBot-Weather` for execution core, simulation, risk manager, SQLite, and strategy runner
2. `yangyuan-zhen/PolyWeather` for weather intelligence, DEB, calibrated probability, evidence chain, monitoring, and city decision cards

Accepted internal architecture:

Seven-layer architecture:

- Source
- Evidence Normalization
- Weather Intelligence
- Probability Governance
- Market Divergence
- Governance & Execution
- Product / Ops

Accepted UI surfaces:

- Opportunity Board
- Workstation
- Pipeline
- Market
- Charts
- History
- Evidence / Raw
- Command
- Settings

Next bounded task:

Create the first implementation package for **Round PWB-01 — Execution Core v0**.

## Next Recommended Step

The next recommended document is:

`Round_PWB-01_Execution_Core_v0_Implementation_Charter.md`
