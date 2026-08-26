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
