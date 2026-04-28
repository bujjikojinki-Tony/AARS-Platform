# polymarket-weather-ingest

Metadata and market-state ingestion layer for Polymarket weather markets.

## Purpose

This repository discovers and loads weather-related market content from Polymarket.

It does:
- discover weather markets
- load event / market metadata
- normalize market content
- build market snapshots for downstream comparison
- prefer priceful markets when building the realtime primary snapshot

It does not:
- generate weather forecasts
- compare against weather models
- send Telegram alerts
- execute trades

## Data Sources

Primary source:
- Polymarket Gamma API

## First MVP Scope

Support:
- discovery of active weather markets
- search / filter workflows
- building one normalized weather market bundle
- exporting JSON for downstream comparison
- keeping `market_realtime_simple.json` populated with markets that have price data

## Output Objects

- `MarketContent`
- `MarketPriceState`
- `WeatherMarketBundle`
- `market_realtime_simple.json`
- `market_realtime_snapshot.json`

## Suggested Flow

```text
Gamma API discovery
→ weather filtering
→ normalized market content
→ select priceful primary market
→ market snapshot export
```

## Run

```bash
PYTHONPATH=src python scripts/run_polymarket_realtime.py
```
