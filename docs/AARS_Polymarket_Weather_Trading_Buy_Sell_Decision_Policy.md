# AARS Polymarket Weather Trading Buy/Sell Decision Policy

## Purpose
This document defines which governed fields are suitable for buy/sell research decisions in the AARS weather trading console.

The policy is intentionally narrower than execution logic:
- It helps determine whether the research direction leans toward `YES`, `NO`, or `NO TRADE`.
- It does not grant execution permission.
- Execution permission remains owned by `gate_stack_api.v1`.

## Suitable Data For Buy/Sell Judgment
Use these fields together:

1. Market probability
- `market_implied_probability`
- `yes_price`
- `no_price`

2. System-estimated fair probability
- `fair_value`
- `probability_mode`

3. Directional edge
- `edge`

4. Evidence quality
- `freshness_status`
- `source_precision_score`
- `validation_coverage`
- `source_match_grade`

5. Execution boundary context
- `can_execute`
- `primary_block_reason`
- `execution_constraint`

## Unsuitable Standalone Inputs
The following fields must not be used alone to justify a buy or sell decision:

- `opportunity_score`
- `recommended_action`
- `latest_alert_severity`
- `latest_anomaly_score`
- raw weather values without canonical normalization

These fields may increase review priority, but they do not define trade direction and do not define execution permission.

## Decision Logic
### Step 1: Require probability inputs
If `market_implied_probability`, `fair_value`, `edge`, or `probability_mode` is missing, the outcome is:

- `refresh_inputs`

### Step 2: Require acceptable evidence quality
If `freshness_status` is `blocked` or `unavailable`, the outcome is:

- `refresh_inputs`

If `validation_coverage < 0.8` or `source_precision_score < 0.7`, the outcome is:

- `review_evidence`

### Step 3: Require meaningful edge
If `abs(edge) <= 0.03`, the outcome is:

- `watch_only`

### Step 4: Determine research direction
If `edge >= 0.05`, the research direction is:

- `research_buy_yes`

If `edge <= -0.05`, the research direction is:

- `research_buy_no`

## Operational Interpretation
The practical interpretation is:

- `fair_value > market_implied_probability` means the system believes `YES` is underpriced.
- `fair_value < market_implied_probability` means the system believes `NO` is underpriced.
- Small edge means there is no actionable mispricing.

## Execution Boundary
Even if the outcome is `research_buy_yes` or `research_buy_no`, execution still requires:

- `can_execute = yes`
- no blocking gate condition
- valid authorization and configured execution mode

This preserves the existing control boundary:

- opportunity is not gate
- alert is not gate
- anomaly is not gate
- research direction is not execution permission

## Registry File
The machine-readable policy lives at:

- `/Users/maolei/AARS-Platform/weather-comparison-engine/data/registries/opportunity_policy_registry/buy_sell_decision_policy.json`
