# polymarket-weather-ingest

Metadata and market-state ingestion layer for Polymarket weather markets.

## Purpose

This repository discovers and loads weather-related market content from Polymarket.

It does:
- discover weather markets
- load event / market metadata
- normalize market content
- build market snapshots for downstream comparison

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

## Output Objects

- `MarketContent`
- `MarketPriceState`
- `WeatherMarketBundle`

## Suggested Flow

```text
Gamma API discovery
→ weather filtering
→ normalized market content
→ market snapshot export
```
