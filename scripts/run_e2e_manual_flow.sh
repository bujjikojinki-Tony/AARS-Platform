#!/usr/bin/env bash
set -e

echo "============================================================"
echo "STEP 1: Run weather-rules-research sample chain"
echo "============================================================"
cd weather-rules-research
PYTHONPATH=src python3 scripts/run_sample_market_001.py
cd ..

echo "============================================================"
echo "STEP 2: Run weather-signal-engine emit_sample"
echo "============================================================"
cd weather-signal-engine
PYTHONPATH=src python3 -m weather_signal_engine.main emit-sample
cd ..

echo "============================================================"
echo "STEP 3: Start weather-telegram-console"
echo "============================================================"
echo "Open another terminal and run:"
echo "cd weather-telegram-console"
echo 'export TELEGRAM_BOT_TOKEN="YOUR_TOKEN"'
echo 'export TELEGRAM_ADMIN_USER_IDS="YOUR_USER_ID"'
echo 'export SIGNAL_JSON_PATH="data/outputs/sample_signal_event.json"'
echo "weather-telegram-console"
echo
echo "Then in Telegram send:"
echo "/start"
echo "/status"
echo "/signals"
echo
echo "After manual review, continue to STEP 4."

echo "============================================================"
echo "STEP 4: Run weather-execution-gateway dry-run"
echo "============================================================"
cd weather-execution-gateway
PYTHONPATH=src python3 -m weather_execution_gateway.main
cd ..

echo "============================================================"
echo "DONE"
echo "============================================================"
