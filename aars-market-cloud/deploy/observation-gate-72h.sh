#!/bin/sh
set -eu
exec python run_observation_gate.py --data-dir /data --min-hours 72
