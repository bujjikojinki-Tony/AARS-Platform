# MIL-3.19 Human Forward Review and Evidence Export

MIL-3.19 adds an immutable human governance layer to extended PAPER_ONLY
observation. It can pause, restart, acknowledge or permanently terminate a
candidate's observation lifecycle. It cannot apply strategy parameters,
promote a candidate or authorize live execution.

## Lifecycle

```text
OBSERVING --ACKNOWLEDGE_FOR_PAPER_CONTINUATION--> OBSERVING_ACKNOWLEDGED
OBSERVING / OBSERVING_ACKNOWLEDGED --PAUSE_PAPER_OBSERVATION--> PAUSED
PAUSED --RESTART_PAPER_OBSERVATION--> OBSERVING
any non-terminal state --TERMINATE_PAPER_OBSERVATION--> TERMINATED
```

- Acknowledgement requires `EXTENDED_OBSERVATION_CONFIRMED` evidence.
- Pause is rejected when current evidence requires a hard stop.
- Restart requires current non-stopped, non-deferred stability evidence.
- Termination is irreversible. Resuming research requires a new governed
  proposal and trial lifecycle.

The forward monitor emits `PAUSED` or `TERMINATED` and does not build another
checkpoint while either hold applies. An acknowledged candidate continues
PAPER_ONLY observation; acknowledgement is not parameter authority.

## Immutable review command

Human review is intentionally available only through an explicit local CLI:

```bash
python run_forward_review.py \
  --db mil3_market.sqlite \
  --trial-id <trial_id> \
  --action PAUSE_PAPER_OBSERVATION \
  --reviewer local-owner \
  --note "Pause while risk evidence is reviewed."
```

Supported actions are:

- `ACKNOWLEDGE_FOR_PAPER_CONTINUATION`
- `PAUSE_PAPER_OBSERVATION`
- `TERMINATE_PAPER_OBSERVATION`
- `RESTART_PAPER_OBSERVATION`

Every event records its predecessor review, latest observation identity and
input hash, derived stability disposition and hash, checkpoint count, warning
codes, reviewer, note and resulting state. Storage rebuilds and rechecks the
current evidence immediately before insertion. A stale source, changed lineage,
non-advancing review time or invalid transition fails closed.

## Self-verifying evidence export

Export the complete evidence chain to a new file:

```bash
python run_forward_evidence_export.py \
  --db mil3_market.sqlite \
  --trial-id <trial_id> \
  --output evidence/<trial_id>.json
```

The exporter includes the archived trial, every forward checkpoint, freshly
derived stability evidence and every human review. The manifest contains a
SHA-256 hash for each component and one combined SHA-256. Verification also
checks the permanent authority locks. The command refuses to overwrite an
existing file.

## Read-only inspection

The localhost API adds:

```text
GET /api/v1/forward-lifecycle?trial_id={trial_id}
GET /api/v1/forward-reviews/{review_id}
GET /api/v1/forward-evidence-manifest?trial_id={trial_id}
```

The manifest endpoint exposes hashes and counts, not the complete evidence
payload. The console performs only GET requests and has no acknowledge, pause,
restart, terminate, parameter-apply or execution button.

All review, lifecycle, manifest and export responses preserve:

```text
execution_mode=PAPER_ONLY
review_action_applies_parameters=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```

