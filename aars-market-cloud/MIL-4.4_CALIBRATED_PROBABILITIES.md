# MIL-4.4 Calibrated Cognitive Probabilities

Primary and Challenger now emit explicit Bull/Base/Bear distributions. Values are validated and normalized before persistence.

Example:
```json
{"bull":0.52,"base":0.31,"bear":0.17}
```

This enables later Brier/calibration comparison against the deterministic Quant prior. Probability output is research evidence, not an order signal.

Run:
```bash
python run_calibrated_cognitive_cycle.py --db /data/mil3_market.sqlite --memory-db /data/cognitive_memory.sqlite --horizon 24
```

Invariants: PAPER_ONLY, RESEARCH_ONLY, execution_authority=NONE.
