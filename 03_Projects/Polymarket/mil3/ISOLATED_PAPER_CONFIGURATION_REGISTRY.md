# MIL-3.21 Isolated PAPER_ONLY Configuration Registry

MIL-3.21 consumes a current MIL-3.20 approval into an immutable configuration
registry and governs one named local sandbox pointer. It does not start a
strategy process, change shared defaults, submit an order or authorize live
execution.

## Data layers

```text
Immutable activation approval
          ↓ one-time consumption
Immutable configuration registry entry
          ↓ explicit local atomic command
Versioned sandbox stored pointer
          ↓ read-only validity resolution
Effective configuration or fail-safe NONE
```

The stored pointer and effective configuration are deliberately separate. An
expired or revoked approval immediately produces a null effective configuration
even before a reconciliation event clears the stored pointer.

## Register an approved configuration

```bash
python run_isolated_paper_config.py \
  --db mil3_market.sqlite \
  --action REGISTER \
  --trial-id <trial_id>
```

Registration requires the trial's latest isolated-activation state to be a
current, unexpired `APPROVED` decision. The database independently verifies the
approval ID, sandbox, expiry, target strategy, full configuration, configuration
SHA-256 and source evidence. A uniqueness constraint permits one configuration
entry per approval. The entry is inert after registration.

## Atomically activate the isolated pointer

```bash
python run_isolated_paper_config.py \
  --db mil3_market.sqlite \
  --action ACTIVATE \
  --configuration-id <configuration_id> \
  --sandbox-id aars-paper-sandbox \
  --operator local-owner \
  --note "Select this configuration in the isolated registry only."
```

Inside one `BEGIN IMMEDIATE` transaction, activation verifies:

- expected sandbox state version;
- previous pointer and previous event ID;
- configuration identity and sandbox ownership;
- current approval lineage and revocation state;
- approval expiry at event time;
- monotonic event time;
- permanent PAPER_ONLY authority locks.

The transaction updates the pointer, increments its version and appends the
activation event together. Failure rolls back all three effects.

Activation means registry selection only:

```text
starts_strategy_process=false
shared_configuration_change_allowed=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```

## Atomic rollback

```bash
python run_isolated_paper_config.py \
  --db mil3_market.sqlite \
  --action ROLLBACK \
  --sandbox-id aars-paper-sandbox \
  --operator local-owner \
  --note "Rollback the latest isolated pointer activation."
```

Rollback consumes the latest unrolled activation exactly once. Its recorded
previous configuration is revalidated at rollback time. If that target is
expired, revoked, missing or otherwise unsafe, rollback clears the sandbox to
the empty baseline instead of restoring it.

## Approval expiry and revocation

Every read resolves current authority before returning an effective
configuration:

- `ACTIVE` — stored pointer is current and effective;
- `EMPTY` — no stored pointer;
- `EXPIRED_FAIL_SAFE` — stored pointer remains for audit but is ineffective;
- `REVOKED_FAIL_SAFE` — approval was revoked and the pointer is ineffective;
- `APPROVAL_MISMATCH_FAIL_SAFE` — approval lineage changed;
- `CONFIGURATION_MISSING_FAIL_SAFE` — registry integrity is degraded.

This resolution is immediate and read-only. Persist the already-effective
invalidation with:

```bash
python run_isolated_paper_config.py \
  --db mil3_market.sqlite \
  --action RECONCILE
```

Reconciliation appends an immutable invalidation event and atomically clears the
stored pointer. Safety does not depend on reconciliation running: consumers
must use `effective_configuration`, never the raw stored pointer.

## Read-only API

```text
GET /api/v1/isolated-configurations?sandbox_id={sandbox_id}
GET /api/v1/isolated-configurations/{configuration_id}
GET /api/v1/isolated-sandbox?sandbox_id={sandbox_id}
GET /api/v1/isolated-sandbox-events?sandbox_id={sandbox_id}
GET /api/v1/isolated-sandbox-events/{event_id}
```

The console shows stored versus effective identity, state version, current
blocking reason, immutable configuration evidence, safe rollback target and the
atomic event trail. It has no register, activate, rollback or execution button.

The only runtime consumer permitted after this registry is the fenced
MIL-3.22 PAPER_ONLY layer described in
`GOVERNED_ISOLATED_PAPER_RUNTIME.md`. It must consume
`effective_configuration`, never the raw stored pointer.
