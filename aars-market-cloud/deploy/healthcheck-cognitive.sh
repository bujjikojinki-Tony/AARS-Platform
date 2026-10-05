#!/bin/sh
set -eu
test -f "${AARS_DB:-/data/mil3_market.sqlite}"
if [ -f /data/cognitive_trial_state.json ]; then python -c 'import json;json.load(open("/data/cognitive_trial_state.json"))'; fi
echo "AARS MIL-4.7 observation stack healthy; PAPER_ONLY"
