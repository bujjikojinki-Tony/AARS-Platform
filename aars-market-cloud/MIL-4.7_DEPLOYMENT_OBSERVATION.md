# MIL-4.7 Deployment & Observation Console

This is the MIL-4 feature freeze point. Docker Compose runs scheduler, cognitive-trial, and read-only API against shared /data.

Artifacts: cognitive_trial_state.json, cognitive_scorecard.json, cognitive_memory.sqlite.

During the 30-day trial cognitive logic, prompts, thresholds, model promotion, strategy parameters, exposure and leverage remain frozen unless a human explicitly ends the trial and opens a reviewed change.

Start: `cp .env.example .env && docker compose up -d --build`

Health: `docker compose exec cognitive-trial sh deploy/healthcheck-cognitive.sh`
