# weather-rules-research

Rule-aware research foundation for Polymarket weather markets.

## Purpose

This repository builds the research base for a weather-market signal system.

It focuses on four things:

1. parsing and normalizing market rules,
2. mapping markets to official settlement stations,
3. collecting forecast and official observation data,
4. measuring forecast-vs-settlement bias over time.

Current research mode includes:

- structured question parsing for both daily high and daily low temperature markets
- review flags and parser confidence on normalized rules
- manual station mapping backed by JSON plus alias normalization
- bias summary metrics including mean error, MAE, RMSE, and band hit rate

This repo is **research-only**.
It does **not** execute trades.
It does **not** send Telegram alerts.

## First MVP Scope

Only support:

- one market family: `daily highest temperature`
- one city at a time
- one station mapping per market
- one simple bias report

## Planned Outputs

Primary exports:

- `rulebook.json`
- `station_map.json`
- `forecast_bias_report.csv`

These will later feed:

- `weather-signal-engine`
- `weather-telegram-console`
- `weather-execution-gateway`

## Suggested Workflow

### Step 1

Create a normalized `MarketRule`.

### Step 2

Map the market to an official station.

### Step 3

Fetch:

- Open-Meteo forecast / historical data
- official observation data

### Step 4

Join forecast and settlement records.

### Step 5

Export a bias report.

## Project Structure

```text
src/weather_rules_research/
  models/
  rules/
  stations/
  open_meteo/
  official_obs/
  backtest/
  outputs/
```

## Quick Start

Set upstream endpoints if needed:

```bash
export OPEN_METEO_BASE_URL=https://api.open-meteo.com
export NOAA_BASE_URL=https://www.ncei.noaa.gov
export NWS_BASE_URL=https://api.weather.gov
```

Create sample exports:

```bash
python -m weather_rules_research.main export-rulebook --output-dir outputs/demo
python -m weather_rules_research.main export-station-map --output-dir outputs/demo
python -m weather_rules_research.main run-bias-report --output-dir outputs/demo
```

These commands generate:

- `rulebook.json`
- `station_map.json`
- `forecast_bias_report.csv`
- `forecast_bias_summary.json`

Manual station mappings live in [data/processed/station_maps/manual_station_map.json](/Users/maolei/AARS-Platform/weather-rules-research/data/processed/station_maps/manual_station_map.json).

Common development commands:

```bash
make install
make test
make lint
make format
```

## Phase 7 Historical Labels

Station settlement labels now have a dedicated backfill step before they are merged
into the unified official label store.

Sample-mode backfill:

```bash
python scripts/run_station_settlement_backfill.py
python scripts/run_official_label_store.py
```

Continuous station backfill worker:

```bash
python scripts/run_station_settlement_backfill_realtime.py
```

Continuous official label worker:

```bash
python scripts/run_official_label_store_realtime.py
```

This writes:

- `data/outputs/station_settlement_records.json`
- `data/outputs/station_settlement_summary.json`
- `data/outputs/official_records/official_record_*.json`
- `data/outputs/official_history.jsonl`
- `data/outputs/official_label_summary.json`

To switch the station backfill toward real fetch mode, set:

```bash
export OFFICIAL_STATION_FETCH_ENABLED=1
export CDO_TOKEN=your_token_here
```

Optional worker controls:

```bash
export STATION_SETTLEMENT_REFRESH_INTERVAL_SECONDS=900
export STATION_SETTLEMENT_MAX_CYCLES=0
export OFFICIAL_LABEL_REFRESH_INTERVAL_SECONDS=1800
export OFFICIAL_LABEL_MAX_CYCLES=0
```

In fetch mode the backfill still keeps the same normalized output shape, so
`weather-comparison-engine` can continue consuming `official_history.jsonl`
without changing its feature-store join logic.
