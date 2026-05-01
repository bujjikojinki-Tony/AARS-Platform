# Round_PWB-04E_Baseline_Freeze

## 1. Freeze Decision
Round PWB-04E - Market Data Cache & Snapshot Archive v0 is frozen.

Status:
```text
ACCEPTED BASELINE
```

## 2. Freeze Scope

The accepted baseline includes:
- snapshot archive models
- archive SQLite table and indexes
- repository archive methods
- archive service
- read-only snapshot archive APIs
- optional sync and scan capture hooks
- History snapshot archive panel in the current dashboard shell
- PWB-04E archive tests

## 3. Stable Rules

- Archive is read-only.
- Archive does not trigger strategy, simulation, execution, or promotion behavior.
- `POST /api/snapshots/archive/current-source` archives current `MarketSnapshot[]` only.
- Optional sync archive capture archives snapshots only.
- Optional scan archive capture records scan input snapshots after scan.
- Archive failures do not fail scan or sync.
- `LIVE_EXECUTE` remains rejected.

## 4. Stable Safety Boundary

This freeze does not add:
- live trading
- auto trading
- wallet handling
- signing
- order submission
- order cancellation
- position reads
- portfolio logic

Freeze statement:
PWB-04E is accepted as a read-only and non-executing market snapshot archive baseline.
It introduces time-indexed `MarketSnapshot` persistence, summary queries, market series lookup, current-source archive capture, optional sync/scan capture hooks, and History visibility.
It does not introduce wallet, signing, order placement, cancellation, position reading, live execution, or auto trading.

## 5. Freeze Rule

Only defects required to preserve PWB-04E archive acceptance may be fixed after this note.
No trading or execution behavior belongs to PWB-04E after freeze.

## 6. Verification Snapshot

- `python -m pytest polymarket-bot/tests/test_pwb04e_market_snapshot_archive.py -q` -> `15 passed`
- `python -m pytest weather-dashboard/tests/test_market_snapshot_archive_panel.py -q` -> `3 passed`
