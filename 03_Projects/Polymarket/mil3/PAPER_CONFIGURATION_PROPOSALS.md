# MIL-3.15 Governed Paper Configuration Proposals

MIL-3.15 turns a fully passing MIL-3.14 `PROMOTION_CANDIDATE` into an immutable,
human-reviewable PAPER_ONLY proposal. It does not apply parameters, change the
monitored portfolio, submit orders, store exchange credentials, or authorize
live execution.

## Proposal rule

Proposal generation reads up to 90 archived daily shadow snapshots and uses the
same MIL-3.14 governance policy. It fails closed unless every promotion check
passes. The proposed candidate is the mode of the latest fold selection across
assets; candidate ID ascending is the deterministic tie-break.

The packet records:

- source shadow snapshot and governance evidence time;
- selection rule and each asset's latest selected candidate;
- fixed existing paper baseline and proposed candidate parameters;
- before/after values plus absolute and relative deltas;
- observed excess return, drawdown, liquidation risk and liquidation events;
- rationale, paper-trial stop condition and authority boundary.

Expected risk impact is explicitly `NOT_FORECAST`. The packet repeats observed
out-of-sample evidence and requires a separately configured paper trial.

## Explicit local archive commands

Create a proposal only after governance reports `PROMOTION_CANDIDATE`:

```bash
python run_paper_proposal.py \
  --db mil3_market.sqlite \
  --strategy AARS_DYNAMIC \
  --history-limit 90
```

Record one terminal human disposition:

```bash
python run_paper_review.py \
  --db mil3_market.sqlite \
  --proposal-id <proposal_id> \
  --disposition ACKNOWLEDGED_FOR_PAPER_TRIAL \
  --reviewer local-owner \
  --note "Consider only through a separately configured paper trial."
```

The alternative terminal disposition is `DECLINED`. A proposal can have only
one terminal review. Repeating the identical record is idempotent; a conflicting
second record is rejected. Acknowledgement never applies the parameters.

## Read-only API

```text
GET /api/v1/paper-proposals?strategy=AARS_DYNAMIC&limit=30
GET /api/v1/paper-proposals/{proposal_id}
```

The index and detail envelope explicitly state:

```text
proposal_application_allowed=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```

HTTP remains GET/HEAD/OPTIONS only. Proposal and review writes exist only in the
explicit local commands above.

## Review meaning

- `PENDING_HUMAN_REVIEW`: no terminal human record exists.
- `ACKNOWLEDGED_FOR_PAPER_TRIAL`: a person considers the proposal suitable for
  a separately configured PAPER_ONLY trial; nothing was applied.
- `DECLINED`: the proposal will not advance to a paper trial.

The console presents the packet as read-only evidence and deliberately contains
no approve, apply, order, credential or live-mode control.

An acknowledged proposal may feed one isolated MIL-3.16 same-window trial. See
`PAPER_TRIALS.md`. Trial creation still does not apply the proposal.
