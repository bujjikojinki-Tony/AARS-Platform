# MIL-4.7 72-Hour Acceptance Gate

No new cognitive feature is introduced. Preflight: `docker compose exec cognitive-trial sh deploy/preflight-cognitive.sh`. After 72h: `docker compose exec cognitive-trial sh deploy/observation-gate-72h.sh`.

PASS requires trial age >=72h, forecasts, matured outcomes, and scorecard. FAIL/WARN never mutates prompts, models, strategies, leverage, exposure, or execution state. Human review is required.
