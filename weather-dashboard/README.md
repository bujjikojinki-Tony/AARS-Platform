# weather-dashboard

Streamlit dashboard for weather-model signals vs Polymarket weather market states.

## Purpose

This dashboard visualizes:
- the shared `TopParameterView` first-screen contract
- the same upstream market / resolver / forecast facts that comparison-engine and Telegram consume
- dashboard rows from the comparison engine
- latest signal payload
- latest market bundle payload
- manual advisory / human fill reconciliation status
- worker health / freshness strip
- probability contract state (`probability_mode`, `execution_constraint`)

## First MVP

The first MVP shows:
- top parameter surface
- overview metrics
- comparison table
- latest signal panel
- latest market panel

The dashboard should not invent market facts locally; it only renders the shared upstream snapshots and derived contracts.

## Phase 31 Scan Surfaces

The monitoring panel now consumes Phase 31 scanner artifacts in read-only mode:

- `data/outputs/scanner/market_universe_snapshot.json`
- `data/outputs/scanner/evidence_scan_snapshot.json`
- `data/outputs/scanner/scanner_status.json`
- `data/outputs/alerts/alert_queue_status.json`

It shows:

- Scanner Status
- Universe Snapshot
- Evidence Scan
- Alert Queue

These surfaces are informational only and do not change gate or execution semantics.

## Inputs

Expected files:
- `data/outputs/sample_dashboard_rows.json`
- `data/outputs/sample_signal_event.json`
- `data/outputs/sample_weather_bundles.json`
- `../weather-execution-gateway/data/outputs/human_fill_reconciliation_report.json`
- `../weather-comparison-engine/data/outputs/monitoring_status.json`

## Run

```bash
streamlit run src/weather_dashboard/app.py --server.port 8514 --server.address 127.0.0.1
```
