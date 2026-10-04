#!/bin/sh
set -eu
# shellcheck disable=SC2086
exec python run_scheduler.py --db "${AARS_DB:-/data/mil3_market.sqlite}" --interval "${AARS_INTERVAL:-1h}" --poll-seconds "${AARS_POLL_SECONDS:-3600}" --bootstrap-days "${AARS_BOOTSTRAP_DAYS:-120}" --symbols ${AARS_SYMBOLS:-BTCUSDT ETHUSDT SOLUSDT}
