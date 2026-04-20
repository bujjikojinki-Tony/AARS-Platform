# weather-dashboard

Streamlit dashboard for weather-model signals vs Polymarket weather market states.

## Purpose

This dashboard visualizes:
- dashboard rows from the comparison engine
- latest signal payload
- latest market bundle payload
- manual advisory / human fill reconciliation status
- worker health / freshness strip
- probability contract state (`probability_mode`, `execution_constraint`)

## First MVP

The first MVP shows:
- overview metrics
- comparison table
- latest signal panel
- latest market panel

## Inputs

Expected files:
- `data/outputs/sample_dashboard_rows.json`
- `data/outputs/sample_signal_event.json`
- `data/outputs/sample_weather_bundles.json`
- `../weather-execution-gateway/data/outputs/human_fill_reconciliation_report.json`
- `../weather-comparison-engine/data/outputs/monitoring_status.json`

## Run

```bash
streamlit run src/weather_dashboard/app.py
```
