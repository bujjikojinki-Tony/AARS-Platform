# weather-comparison-engine

Comparison engine for weather-model signals vs Polymarket weather market states.

## Purpose

This repository compares:
- model-derived weather signals,
- market-derived Polymarket weather states

and produces dashboard-ready rows.

## Inputs

Primary upstream inputs:
- SignalEvent JSON from `weather-signal-engine`
- WeatherMarketBundle JSON from `polymarket-weather-ingest`

## Outputs

Primary downstream outputs:
- ComparisonState
- DashboardRow
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
