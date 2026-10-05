#!/bin/sh
set -eu
while true; do
 python run_forward_cognitive_trial.py --db "${AARS_DB:-/data/mil3_market.sqlite}" --memory-db "${AARS_COGNITIVE_DB:-/data/cognitive_memory.sqlite}" --days "${AARS_COGNITIVE_TRIAL_DAYS:-30}" --forecast-every-hours "${AARS_COGNITIVE_FORECAST_HOURS:-4}"
 sleep "${AARS_COGNITIVE_POLL_SECONDS:-3600}"
done
