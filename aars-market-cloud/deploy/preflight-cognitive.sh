#!/bin/sh
set -eu
if [ -z "${OPENAI_API_KEY:-}" ]; then echo "FAIL: OPENAI_API_KEY is not configured" >&2; exit 2; fi
test -f "${AARS_DB:-/data/mil3_market.sqlite}" || { echo "FAIL: market DB missing" >&2; exit 2; }
python -c "import aars_market.asset_forecast,aars_market.forecast_memory,aars_market.forward_cognitive_trial"
echo "PASS: cognitive trial preflight; PAPER_ONLY"
