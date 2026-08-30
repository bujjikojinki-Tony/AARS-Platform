# MIL-3.10 Mac mini Operations Guide

This deployment is for one-user, long-running **PAPER_ONLY** research. It uses
native Python and user LaunchAgents; it does not install Docker, a privileged
LaunchDaemon, exchange credentials or any order-submission path.

## Runtime layout

The default runtime root is `~/AARS-MIL3`:

```text
~/AARS-MIL3/
├── data/mil3_market.sqlite
├── logs/
└── backups/
```

Four exact user agents are installed in `~/Library/LaunchAgents`:

- `com.aars.mil3.scheduler` — public candle, funding and fundingInfo ingestion.
- `com.aars.mil3.api` — localhost-only read-only API/UI.
- `com.aars.mil3.health` — read-only health check every five minutes.
- `com.aars.mil3.maintenance` — verified backup and bounded log rotation at 02:15.

The scheduler is the only market database writer. API, health and backup use the
same local database but do not add market-data write paths.

## Install

From `03_Projects/Polymarket/mil3`:

```bash
python3 -m venv .venv
.venv/bin/python -m pytest -q
.venv/bin/python run_macos_service.py render --runtime-root "$HOME/AARS-MIL3"
.venv/bin/python run_macos_service.py install --runtime-root "$HOME/AARS-MIL3"
```

`render` creates the runtime directories, initializes the SQLite schema and
writes the four property lists without loading them. Inspect those property
lists before running `install`. All program, project, database and log paths are
resolved to absolute paths.

The API is available only on the Mac at `http://127.0.0.1:8765/`. Do not change
the bind address to `0.0.0.0`. Use an SSH tunnel or a private VPN if another
personal device needs access.

## Daily checks

```bash
.venv/bin/python run_macos_service.py status
.venv/bin/python run_healthcheck.py --db "$HOME/AARS-MIL3/data/mil3_market.sqlite"
tail -n 100 "$HOME/AARS-MIL3/logs/scheduler.log"
tail -n 100 "$HOME/AARS-MIL3/logs/health.log"
```

Health exit codes are:

- `0` — `HEALTHY`
- `1` — `DEGRADED`, including partial/stale ingestion or missing asset data
- `2` — `CRITICAL`, including missing/corrupt database or a failed latest cycle

The check opens SQLite in read-only mode, runs `PRAGMA quick_check`, inspects the
latest audited ingestion cycle and evaluates per-symbol candle freshness. It
does not initialize or modify the database.

## Backups and logs

The daily maintenance job uses SQLite's online backup API and verifies the copy
before publishing it. The default policy retains 30 days of backups. Only files
matching the active database's generated backup prefix are eligible for
retention deletion; unrelated files are ignored.

Run an additional backup manually with:

```bash
.venv/bin/python run_backup.py \
  --db "$HOME/AARS-MIL3/data/mil3_market.sqlite" \
  --backup-dir "$HOME/AARS-MIL3/backups" \
  --retention-days 30 \
  --log-dir "$HOME/AARS-MIL3/logs"
```

LaunchAgent logs are copy-and-truncate rotated after 10 MiB with seven retained
copies. Backups on the same internal SSD protect against software mistakes, not
disk loss. Replicate the `backups` directory to an external disk, NAS or private
object store.

Forward evidence uses a separate MIL-3.20 policy from the 30-day SQLite backup:
365 days with at least two verified copies per trial. After exporting a bundle,
verify it without SQLite and retain it to an encrypted external location:

```bash
.venv/bin/python run_forward_evidence_verify.py \
  --bundle "$HOME/AARS-MIL3/evidence/<trial_id>.json" \
  --report "$HOME/AARS-MIL3/evidence/<trial_id>.verification.json"
.venv/bin/python run_forward_evidence_retain.py \
  --bundle "$HOME/AARS-MIL3/evidence/<trial_id>.json" \
  --archive-dir "/Volumes/AARS-Evidence/forward" \
  --retention-days 365 \
  --minimum-copies 2
```

This is an explicit operator workflow and is not added to the existing
LaunchAgents. Confirm that the external volume is mounted and encrypted before
running it. The retention command never deletes unknown or unverifiable files.

MIL-3.21 sandbox resolution invalidates expired or revoked approvals immediately
on every read, without waiting for a job. Persist the corresponding pointer-clear
event during routine maintenance with:

```bash
.venv/bin/python run_isolated_paper_config.py \
  --db "$HOME/AARS-MIL3/data/mil3_market.sqlite" \
  --action RECONCILE
```

This command changes only the isolated registry pointer and starts no strategy
process. It is not installed into the existing LaunchAgents while Mac mini
deployment remains deferred. If later scheduled, keep it as a separate narrowly
scoped user agent; do not add it to public market-data ingestion.

MIL-3.22 runtime safety is also immediate on read: an expired lease, armed kill
switch, changed pointer, expired/revoked approval or configuration mismatch makes
a stored RUNNING session ineffective. Persist any derived stop during maintenance:

```bash
.venv/bin/python run_isolated_paper_runtime.py \
  --db "$HOME/AARS-MIL3/data/mil3_market.sqlite" \
  --action RECONCILE
```

Do not install the runtime worker as a LaunchAgent while deployment is deferred.
Before future scheduling, define a separate user-level job with a bounded lease,
an explicit kill-switch-clear procedure and no dependency on exchange credentials.
Never combine runtime control with public-data ingestion or the read-only API.

MIL-3.23 adds no new LaunchAgent. When the bounded runtime is invoked manually,
each heartbeat selects a synchronized local market boundary, reserves an
idempotent checkpoint and atomically commits a cumulative paper ledger. After a
process crash, do not edit checkpoint rows: let the old lease expire, verify the
kill switch and registry state, then run the same bounded command. The new
fenced session will recover the RESERVED cycle only after the previous owner is
ineffective. Preserve the database if source-drift validation blocks recovery.

MIL-3.24 also adds no LaunchAgent. The same bounded runtime command now commits
four isolated shadow-bot accounts inside ledger v2. Before every manual run,
confirm funding coverage for every configured asset: the fixed Futures Grid and
AARS bots make complete funding evidence mandatory even when the approved trial
target was spot-only. A bot `FROZEN` state is a local virtual-account risk stop;
it does not replace the sandbox kill switch or stop ingestion. Do not edit bot
results or checkpoint rows to restart it—activate a separately reviewed
configuration through the existing approval/registry lifecycle.

MIL-3.25 provides a separate forward-bot LaunchAgent renderer but intentionally
does not add that job to the four-job default install. Stage it outside
`~/Library/LaunchAgents`, inspect its absolute paths and run supervised STATUS/
WAKE cycles first. The job is one-shot (`RunAtLoad=false`, `KeepAlive=false`),
polls for a new synchronized closed bar and acquires a bounded lease only when
work is due. Do not load it until at least backup/restore, stale RESERVED,
kill-switch and notification drills have passed. See
`FORWARD_BOT_OPERATIONS.md` for the exact staging command and burn-in gates.

MIL-3.26 requires the daily shadow job to run only once per UTC observation
date, after ingestion and after the intended timeframe candle is fully closed.
The builder caps validation and portfolio replay to one synchronized closed
boundary. A changed same-day rerun fails closed, and legacy v1 snapshots remain
auditable but do not count toward the 30-day promotion window. Do not schedule
retries that attempt to manufacture additional same-day governance evidence.

MIL-3.27 diagnostics are read-only and may be generated after the canonical
daily v2 archive. They do not need a LaunchAgent. Keep the JSON report outside
the SQLite database if retained, record its source snapshot ID, and treat a
replay mismatch as an investigation stop rather than rebuilding or editing the
immutable snapshot.

MIL-3.28 challenger reports are also on-demand and need no LaunchAgent. Generate
them only after the canonical v2 snapshot and retain the source snapshot ID with
the report. Do not schedule parameter sweeps or rewrite the fixed first result;
the next step is independent walk-forward validation, not automatic activation.

## Upgrade

Stop the jobs before moving the repository or Python environment because the
property lists contain absolute paths:

```bash
.venv/bin/python run_macos_service.py uninstall
git pull --ff-only
.venv/bin/python -m pytest -q
.venv/bin/python run_macos_service.py install --runtime-root "$HOME/AARS-MIL3"
```

`uninstall` unloads and removes only the four exact AARS property lists. It does
not delete `~/AARS-MIL3`, the database, logs or backups.

## Restore

1. Uninstall/unload the four agents.
2. Keep the damaged database for investigation by renaming it.
3. Copy a verified `.sqlite` backup into
   `~/AARS-MIL3/data/mil3_market.sqlite`.
4. Run `run_healthcheck.py` against the restored file.
5. Reinstall the agents.

Never replace or copy only the live main SQLite file while WAL services are
active. Use `run_backup.py` for online backups.

## Mac mini operating conditions

- Use wired Ethernet and automatic network time synchronization.
- Disable automatic system sleep; the display may sleep.
- Use a UPS when practical.
- Keep FileVault enabled and store its recovery key safely.
- User LaunchAgents start after that user logs in. After a FileVault-protected
  reboot or power loss, one local login is required before AARS resumes.
- On supported Mac mini/macOS combinations, enable startup when power is
  restored, but retain the login requirement above.
- Apply macOS and Python security updates during a planned maintenance window,
  then run the full test suite and a manual health check.

## Safety boundary

All managed jobs remain `PAPER_ONLY`. The deployment contains no API key fields,
signed exchange requests, POST order route, live-mode switch or automatic trade
execution. A health failure reports degraded evidence; it never authorizes an
order or changes strategy authority.
