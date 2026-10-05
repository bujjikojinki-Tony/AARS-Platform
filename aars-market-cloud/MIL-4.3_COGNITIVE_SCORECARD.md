# MIL-4.3 Cognitive Model Scorecard

Purpose: measure whether the cognitive layer adds information instead of assuming that it does.

Current metrics:
- multiclass Brier score for Bull/Base/Bear;
- 24h and 72h outcome alignment;
- asset, market-state and horizon segmentation;
- minimum-sample gate.

Important limitation: MIL-4.2 LLM reviews are qualitative. MIL-4.3 therefore does **not** invent class probabilities from prose. Until the LLM schema emits explicit calibrated Bull/Base/Bear probabilities, Primary and Challenger inherit the quant prior for scoring and `llm_incremental_value` remains `NOT_YET_MEASURABLE`.

This is deliberate: no claim of LLM alpha or profitability without measurable evidence.

Run:
```bash
python run_cognitive_scorecard.py --memory-db /data/cognitive_memory.sqlite --output /data/cognitive_scorecard.json
```

Authority is ANALYTICS_ONLY. No strategy, leverage, exposure or execution state is modified.
