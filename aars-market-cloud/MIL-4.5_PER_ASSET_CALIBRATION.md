# MIL-4.5 Per-Asset / Per-Horizon Calibration

MIL-4.5 fixes the unit of prediction. A forecast belongs to exactly one symbol and one horizon.

Default matrix: BTCUSDT/ETHUSDT/SOLUSDT x 24h/72h = six independent forecasts per evidence cycle.

Each forecast has a deterministic forecast_id derived from packet_id + symbol + horizon. Outcomes can only attach to that forecast_id.

Run:
```bash
python run_asset_forecasts.py --db /data/mil3_market.sqlite --memory-db /data/cognitive_memory.sqlite
python run_forecast_outcomes.py --db /data/mil3_market.sqlite --memory-db /data/cognitive_memory.sqlite
```

This layer remains PAPER_ONLY / RESEARCH_ONLY / OBSERVATION_ONLY. It does not adapt strategies from outcomes.
