#!/bin/sh
set -eu
[ -f .env ] || cp .env.example .env
docker compose up -d --build
echo "AARS PAPER_ONLY started on http://localhost:${AARS_PORT:-8765}/"
