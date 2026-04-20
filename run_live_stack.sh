#!/usr/bin/env bash
set -e

ROOT_DIR="$(pwd)"

echo "============================================================"
echo "LIVE STACK BOOT"
echo "============================================================"

# 1. Start weather realtime backfill worker
echo
echo "[1/4] Starting weather realtime backfill worker..."
(
  cd "$ROOT_DIR/weather-rules-research"
  PYTHONPATH=src python scripts/run_weather_backfill_realtime.py
) &
WEATHER_PID=$!

# 2. Start Polymarket realtime worker
echo
echo "[2/4] Starting Polymarket realtime worker..."
(
  cd "$ROOT_DIR/polymarket-weather-ingest"
  PYTHONPATH=src python scripts/run_polymarket_realtime.py
) &
POLY_PID=$!

# 3. Start comparison realtime worker
echo
echo "[3/4] Starting comparison realtime worker..."
(
  cd "$ROOT_DIR/weather-comparison-engine"
  PYTHONPATH=src python scripts/run_comparison_realtime.py
) &
COMPARE_PID=$!

# 4. Start Streamlit dashboard
echo
echo "[4/4] Starting dashboard..."
(
  cd "$ROOT_DIR/weather-dashboard"
  PYTHONPATH=src streamlit run src/weather_dashboard/app.py
) &
DASHBOARD_PID=$!

echo
echo "============================================================"
echo "STACK STARTED"
echo "============================================================"
echo "Weather Poller PID   : $WEATHER_PID"
echo "Polymarket Worker PID: $POLY_PID"
echo "Compare Loop PID     : $COMPARE_PID"
echo "Dashboard PID        : $DASHBOARD_PID"
echo
echo "Press Ctrl+C to stop all."
echo "============================================================"

cleanup() {
  echo
  echo "Stopping live stack..."
  kill $WEATHER_PID 2>/dev/null || true
  kill $POLY_PID 2>/dev/null || true
  kill $COMPARE_PID 2>/dev/null || true
  kill $DASHBOARD_PID 2>/dev/null || true
  echo "All processes stopped."
}

trap cleanup EXIT INT TERM

wait
