# MIL-4.2 Cognitive Memory + Outcome Feedback

Every cognitive review is stored as immutable research evidence keyed by packet_id. Later, when closed candles exist, the evaluator records 24h/72h realized outcomes.

This layer is OBSERVATION_ONLY:
- no strategy mutation;
- no automatic prompt/model promotion;
- no exposure or leverage change;
- no execution authority.

Run:
```bash
python run_cognitive_cycle_v2.py --db /data/mil3_market.sqlite --memory-db /data/cognitive_memory.sqlite
python run_outcome_feedback.py PACKET_ID --db /data/mil3_market.sqlite --memory-db /data/cognitive_memory.sqlite
```

The next analytics layer can calculate calibration and conditional accuracy by market state/model, but model or policy changes must remain separately reviewed.
