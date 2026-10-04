# AARS Market Cloud

Self-contained cloud package for the AARS MIL-3 calculation/research runtime.

## Start

```bash
cp .env.example .env
docker compose up -d --build
```

Open http://localhost:8765/ and check:

```bash
docker compose exec scheduler sh deploy/healthcheck.sh
```

The scheduler writes public BTC/ETH/SOL market/funding data to `data/mil3_market.sqlite`; the API/UI reads the same persistent volume.

This build is PAPER_ONLY. It contains no authenticated exchange order path and requires no exchange secret.

If you already have `mil3_market.sqlite`, put it in `data/` before startup. Otherwise the scheduler creates and bootstraps it.
