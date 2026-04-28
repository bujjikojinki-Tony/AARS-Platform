# weather-comparison-engine

Comparison engine for weather-model signals vs Polymarket weather market states.

## Purpose

This repository compares:
- model-derived weather signals,
- market-derived Polymarket weather states

and produces dashboard-ready rows.
It also writes the shared `TopParameterView` that dashboard / Telegram / gateway
consume as their first-screen contract.
The engine is the primary place where upstream market / resolver / forecast facts
are merged into one comparable, traceable row.

## Inputs

Primary upstream inputs:
- SignalEvent JSON from `weather-signal-engine`
- WeatherMarketBundle JSON from `polymarket-weather-ingest`

## Outputs

Primary downstream outputs:
- ComparisonState
- DashboardRow
- TopParameterView
- divergence metrics
- dashboard json / csv

## First MVP Scope

Support:
- one signal
- one market bundle
- band-level comparison
- confidence-adjusted gap
- one dashboard export

## Non-Goals

- no Telegram
- no order execution
- no live auto-refresh in MVP

## Phase 7 Historical Feature Store

One-shot feature store export:

```bash
python scripts/run_feature_store.py
```

Continuous feature store worker:

```bash
python scripts/run_feature_store_realtime.py
```

Phase 8 validation reports:

```bash
python scripts/run_model_validation.py
```

Continuous validation worker:

```bash
python scripts/run_model_validation_realtime.py
```

Useful env overrides:

```bash
export OFFICIAL_HISTORY_JSONL=../weather-rules-research/data/outputs/official_history.jsonl
export FEATURE_STORE_REFRESH_INTERVAL_SECONDS=1800
export FEATURE_STORE_MAX_CYCLES=0
export MODEL_VALIDATION_BUCKET_COUNT=10
export BACKTEST_EDGE_THRESHOLD=0.05
export MODEL_VALIDATION_REFRESH_INTERVAL_SECONDS=1800
export MODEL_VALIDATION_MAX_CYCLES=0
```

Phase 13 monitoring status:

```bash
PYTHONPATH=src python -m weather_comparison_engine.main build-monitoring-status
```

This writes:

```text
data/outputs/monitoring_status.json
```

Top parameter contract export:

```bash
PYTHONPATH=src python -m weather_comparison_engine.main build-unified-status
PYTHONPATH=src python -m weather_comparison_engine.main build-gate-stack-api
```

These commands refresh:

- `data/outputs/unified_status.json`
- `data/outputs/gate_stack_api.json`
- `data/outputs/latest_dashboard_rows.json`
- `data/outputs/top_parameter_view` embedded in the comparison outputs

Comparison rows should remain the single derivation point for downstream UI
surfaces; dashboard and Telegram should not invent alternative facts locally.

The monitoring file summarizes worker freshness for:
- market realtime
- forecast realtime
- resolver report
- probability shadow
- comparison output
- execution gateway readiness

Probability contract MVP:

- `probability_mode=heuristic_not_calibrated`
- `execution_constraint=manual_advisory_only`

These fields are exported with `ProbabilityState` and the shadow report so downstream dashboard / telegram / gateway layers can distinguish heuristic decision aids from future calibrated live-approved probabilities.

Phase 22 gate stack external API:

```bash
PYTHONPATH=src python -m weather_comparison_engine.main build-gate-stack-api
PYTHONPATH=src python -m weather_comparison_engine.main build-gate-stack-automation-summary
```

Outputs:

- `data/outputs/gate_stack_api.json` (`gate_stack_api.v1`)
- `data/outputs/gate_stack_automation_summary.json` (`gate_stack_automation_summary.v1`)

Automation gate check (cron/worker friendly):

```bash
PYTHONPATH=src python -m weather_comparison_engine.main run-gate-stack-automation-check --fail-on-signal red
```

Exit code policy:

- `0`: no red signal (or mode `never`)
- `2`: blocked at configured threshold (`red` or `amber`)

Realtime automation worker with retry/backoff:

```bash
PYTHONPATH=src python scripts/run_gate_stack_automation_realtime.py
```

Additional output:

- `data/outputs/gate_stack_ops_alerts.jsonl` (`gate_stack_ops_alert.v1`, emitted on red runtime alert)

## Phase 31 Runtime Runbook

Phase 31 adds the continuous market scanning and realtime alerting layer. The
main CLI entrypoint lives in `src/weather_comparison_engine/main.py`.

### 1) Build scanner artifacts

Run these one-shot commands from `weather-comparison-engine/`:

```bash
PYTHONPATH=src python -m weather_comparison_engine.main build-market-universe
PYTHONPATH=src python -m weather_comparison_engine.main build-evidence-scan
PYTHONPATH=src python -m weather_comparison_engine.main build-scanner-status
```

These refresh:

- `data/outputs/scanner/market_universe_snapshot.json`
- `data/outputs/scanner/evidence_scan_snapshot.json`
- `data/outputs/scanner/scanner_status.json`

### 2) Run the full scan pipeline

```bash
PYTHONPATH=src python -m weather_comparison_engine.main run-scan-pipeline
```

This runs, in order:

1. market discovery
2. evidence scan
3. single-market alert refresh
4. family anomaly refresh
5. alert routing
6. scanner status writeout

Additional outputs:

- `data/outputs/alerts/market_alert_events.json`
- `data/outputs/alerts/family_anomaly_summary.json`
- `data/outputs/alerts/scanner_ops_alerts.json`
- `data/outputs/alerts/alert_queue_status.json`

### 3) Minimal sanity check

After the run, verify that these files exist and are non-empty:

- `data/outputs/scanner/market_universe_snapshot.json`
- `data/outputs/scanner/evidence_scan_snapshot.json`
- `data/outputs/scanner/scanner_status.json`
- `data/outputs/alerts/alert_queue_status.json`

Then confirm Dashboard and Telegram are reading the same scan artifacts:

- Dashboard monitoring panel shows Scanner Status / Universe Snapshot /
  Evidence Scan / Alert Queue.
- Telegram `/scanstatus`, `/alerts`, and `/anomalies` use the same scan files.

### 4) Practical notes

- `build-market-universe` is the safest smoke test when you only want to verify
  the scanner pool.
- `run-scan-pipeline` is the end-to-end check when you want the full alerting
  chain.
- All scanner outputs remain read-only consumer inputs; they do not change gate
  or execution semantics.
