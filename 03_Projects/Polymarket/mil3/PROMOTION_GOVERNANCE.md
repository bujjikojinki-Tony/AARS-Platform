# MIL-3.14 Strategy Promotion Governance

MIL-3.14 evaluates whether immutable PAPER_ONLY shadow evidence supports further
human promotion review. It never changes a strategy configuration, promotes a
candidate automatically, submits an order, or authorizes live execution.

## Outcomes

- `CONTINUE_OBSERVATION`: evidence is missing, too short, degraded, unstable,
  or outside a candidate threshold without reaching a material rejection band.
- `PROMOTION_CANDIDATE`: every conservative candidate check passes. This is
  permission for a separate human paper-only review, not automatic promotion.
- `REJECT_PROMOTION`: material performance or risk evidence makes the current
  configuration unsuitable for promotion.

Every decision explicitly sets both `automatic_strategy_change_allowed` and
`live_execution_allowed` to `false`.

## Default candidate policy

The latest 30 archived daily snapshots are evaluated. Candidacy requires:

- at least 30 immutable snapshots in total;
- at least 7 consecutive `READY_FOR_SHADOW_REVIEW` snapshots;
- a ready latest Review Gate and non-degraded latest portfolio;
- parameter changes in no more than 10% of evaluated transitions;
- mean fold selection stability of at least 70%;
- mean out-of-sample return at least equal to Buy & Hold after modeled costs;
- maximum portfolio drawdown no greater than 20%;
- maximum liquidation-risk approximation no greater than 10%;
- zero liquidation approximation breaches;
- each high-risk warning recurring in no more than 10% of evaluated snapshots.

The high-risk warning set includes baseline underperformance, missing funding
history, insufficient folds, liquidation approximation breach and material
train/test score decay.

## Material rejection bands

Governance rejects promotion when any evaluated evidence reaches:

- mean excess return versus Buy & Hold at or below -5%;
- portfolio drawdown at or above 35%;
- liquidation-risk approximation at or above 25%;
- one or more liquidation approximation breaches.

Values between a candidate threshold and a rejection band produce
`CONTINUE_OBSERVATION`, preserving the distinction between inconclusive and
materially adverse evidence.

## Read-only API

```text
GET /api/v1/promotion-governance?strategy=AARS_DYNAMIC&limit=90
```

The response contains the policy, evidence window, observed aggregate values,
every check with observed/required values, impact and recovery condition, and
the final advisory decision. It is derived from archived stability evidence and
does not write to SQLite.

## Console interpretation

The MIL-3.14 governance card remains next to the Latest Stable Snapshot. Failed
checks appear before passing checks. `BLOCK` items explain what must be observed
or repaired; `REJECT` items identify material adverse evidence. The permanent
authority labels state that automatic strategy changes are locked and live
execution is disallowed, including while the API is unavailable.

## Review cadence

Run the explicit daily snapshot command after ingestion, then revisit governance:

```bash
python run_shadow_daily.py --db mil3_market.sqlite --validation-strategy AARS_DYNAMIC
python run_api.py --db mil3_market.sqlite --port 8765
```

Governance is recalculated on read after each immutable daily snapshot. No
separate decision row is persisted and no parameter is promoted by this flow.

When the result is `PROMOTION_CANDIDATE`, MIL-3.15 can create a separate
immutable human-review packet through an explicit local command. See
`PAPER_CONFIGURATION_PROPOSALS.md`. Creating or acknowledging that packet still
does not apply parameters or authorize live execution.
