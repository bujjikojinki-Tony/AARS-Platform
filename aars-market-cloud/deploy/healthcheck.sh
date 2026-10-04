#!/bin/sh
set -eu
# shellcheck disable=SC2086
exec python run_healthcheck.py --db "${AARS_DB:-/data/mil3_market.sqlite}" --interval "${AARS_INTERVAL:-1h}" --symbols ${AARS_SYMBOLS:-BTCUSDT ETHUSDT SOLUSDT}
