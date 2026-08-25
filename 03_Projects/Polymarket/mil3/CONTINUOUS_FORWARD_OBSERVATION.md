# MIL-3.18 Continuous Forward Observation Governance

MIL-3.18 advances eligible MIL-3.17 trials through a sequence of immutable
forward-only checkpoints and derives persistence, decay and risk evidence from
that sequence. It does not change ingestion, strategy configuration or
execution authority.

## Separate local monitor

The forward monitor is deliberately separate from the public-market-data
ingestion scheduler. An observation replay or funding-coverage failure cannot
interrupt candle/funding ingestion, and ingestion retains its truthful
`PUBLIC_MARKET_DATA_ONLY` scope.

One cycle:

1. lists archived trials with
   `ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION`;
2. permanently skips a trial whose latest checkpoint triggered a hard stop;
3. builds at most one checkpoint at the latest synchronized market endpoint;
4. reuses the existing checkpoint when no new endpoint exists;
5. reports `WAITING` for insufficient new history;
6. reports `DEGRADED` for funding, lineage, boundary or archive failures;
7. never applies a proposal or calls an exchange order path.

Run one acceptance cycle:

```bash
python run_forward_monitor.py \
  --db mil3_market.sqlite \
  --poll-seconds 3600 \
  --max-cycles 1
```

Run continuously in the foreground:

```bash
python run_forward_monitor.py \
  --db mil3_market.sqlite \
  --poll-seconds 3600
```

Mac mini LaunchAgent activation remains deferred until the target machine is
ready. MIL-3.18 does not install or start a background service.

## Persistence policy

The default read-only stability policy evaluates the latest 30 checkpoints and
requires:

- at least 720 measured 1h forward bars (30 days);
- at least three consecutive qualifying checkpoints;
- non-negative proposed-minus-baseline risk-adjusted score;
- non-negative proposed-minus-baseline return;
- zero liquidation approximation breaches;
- intact predecessor observation and input-hash lineage;
- no checkpoint gap greater than 48 hours.

A qualifying sequence is reset whenever a checkpoint fails one of the
performance or risk conditions. This prevents a single favorable checkpoint
from being treated as persistent evidence.

## Evidence alarms

The derived stability view can emit:

- `CHECKPOINT_LINEAGE_BROKEN` — high severity and governance deferral;
- `CHECKPOINT_CADENCE_GAP` — evidence continuity is incomplete and review is
  deferred;
- `PROPOSED_EDGE_DECAY` — current score advantage has fallen materially from
  its observed peak;
- `PROPOSED_EDGE_REVERSAL` — latest score advantage turned negative after
  earlier non-negative evidence;
- `LIQUIDATION_RISK_RISING` — liquidation-risk approximation rose across three
  checkpoints beyond tolerance;
- `FORWARD_STOP_TRIGGERED` — critical terminal stop for the current trial.

Each alarm includes its trigger, impact, recommended response and closure
condition. Alarms are evidence objects; there is no acknowledge, dismiss or
execution control in the read-only console.

## Advisory outcomes

- `CONTINUE_EXTENDED_OBSERVATION`
- `DEFER_EXTENDED_OBSERVATION`
- `EXTENDED_OBSERVATION_CONFIRMED`
- `STOP_EXTENDED_OBSERVATION`

Even `EXTENDED_OBSERVATION_CONFIRMED` means only that policy evidence is ready
for a separate human paper review. It does not apply parameters and does not
authorize live execution.

## Read-only API

```text
GET /api/v1/forward-stability?trial_id={trial_id}&limit=90
```

The response carries:

```text
observation_application_allowed=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```
