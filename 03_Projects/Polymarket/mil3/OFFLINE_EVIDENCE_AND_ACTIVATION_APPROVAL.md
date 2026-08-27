# MIL-3.20 Offline Evidence and Isolated Activation Approval

MIL-3.20 separates evidence trust, retention and activation authorization into
three explicit stages. None of them submits orders, changes the shared strategy
configuration or enables live execution.

## 1. Verify without a database

```bash
python run_forward_evidence_verify.py \
  --bundle evidence/<trial_id>.json \
  --report evidence/<trial_id>.verification.json
```

The verifier reads only the selected JSON file. It rejects duplicate JSON keys,
recomputes every component and combined SHA-256, verifies bundle identity and
checks all PAPER_ONLY authority locks. It does not open SQLite. Reports are
created with non-overwrite semantics.

An `INVALID` result exits non-zero and cannot be retained or approved.

## 2. Retain a verified copy

```bash
python run_forward_evidence_retain.py \
  --bundle evidence/<trial_id>.json \
  --archive-dir /Volumes/AARS-Evidence/forward \
  --retention-days 365 \
  --minimum-copies 2
```

Default policy:

- retain for 365 days;
- preserve at least two verified copies per trial regardless of age;
- require source and archive to be separate directories;
- copy through a same-directory temporary file and publish without overwrite;
- verify the copied file and create an immutable verification sidecar;
- create an immutable inventory receipt for every retention run;
- prune only files matching the AARS evidence naming contract whose content and
  filename identity both verify;
- preserve unknown, malformed and lookalike files.

For a Mac mini, point `--archive-dir` at an encrypted external disk or other
separately backed-up location. The command verifies logical separation and file
integrity; it cannot prove that two paths reside on different physical media.

## 3. Review isolated PAPER_ONLY activation

Approval prerequisites are deliberately strict:

- the exported bundle passes offline verification;
- current forward stability is `EXTENDED_OBSERVATION_CONFIRMED`;
- the human forward lifecycle is `OBSERVING_ACKNOWLEDGED`;
- current stability warning codes are empty;
- bundle hashes and configuration exactly match the current SQLite archive.

Approve for a named isolated sandbox, with a maximum validity of 168 hours:

```bash
python run_isolated_activation_review.py \
  --db mil3_market.sqlite \
  --trial-id <trial_id> \
  --action APPROVE_ISOLATED_PAPER_ACTIVATION \
  --bundle evidence/<trial_id>.json \
  --sandbox-id aars-paper-sandbox \
  --validity-hours 24 \
  --reviewer local-owner \
  --note "Authorize isolated PAPER_ONLY configuration preparation."
```

Reject evidence that is not ready:

```bash
python run_isolated_activation_review.py \
  --db mil3_market.sqlite \
  --trial-id <trial_id> \
  --action REJECT_ISOLATED_PAPER_ACTIVATION \
  --bundle evidence/<trial_id>.json \
  --reviewer local-owner \
  --note "Evidence prerequisites are incomplete."
```

Revoke a current, unexpired approval:

```bash
python run_isolated_activation_review.py \
  --db mil3_market.sqlite \
  --trial-id <trial_id> \
  --action REVOKE_ISOLATED_PAPER_ACTIVATION \
  --reviewer local-owner \
  --note "Withdraw isolated sandbox authority."
```

States are `PENDING_HUMAN_APPROVAL`, `APPROVED`, `REJECTED`, `REVOKED` and
derived `EXPIRED`. Rejection and revocation are terminal for that trial evidence.
Expiry does not renew itself.

An approval sets only `isolated_paper_activation_allowed=true`. It always keeps:

```text
approval_applies_configuration=false
shared_configuration_change_allowed=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```

MIL-3.20 intentionally contains no configuration materialization or activation
runner. A later milestone must define the isolated sandbox itself before this
authorization can be consumed.

MIL-3.21 now defines that isolated registry and consumes the approval without
starting a process or changing shared configuration. See
`ISOLATED_PAPER_CONFIGURATION_REGISTRY.md`.

## Read-only inspection

```text
GET /api/v1/evidence-governance-policy
GET /api/v1/isolated-activation?trial_id={trial_id}
GET /api/v1/isolated-activation-reviews/{review_id}
```

The console shows prerequisite blocks, retention policy, current/expired state
and immutable review history. It has no approve, activate, revoke or execution
button.
