#!/bin/sh
set -eu
exec python run_api.py --db "${AARS_DB:-/data/mil3_market.sqlite}" --host "${AARS_HOST:-0.0.0.0}" --port "${AARS_PORT:-8765}"
