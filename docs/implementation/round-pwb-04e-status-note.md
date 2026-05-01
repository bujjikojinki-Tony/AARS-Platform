# Round_PWB-04E_Status_Note

## 1. Round
Round PWB-04E - Market Data Cache & Snapshot Archive v0

## 2. Status
Accepted for baseline freeze.

## 3. Purpose
PWB-04E adds a read-only market snapshot archive layer on top of PWB-04D.

It preserves the market state that the system saw at a given time so later rounds can use stable historical inputs for calibration, replay, backtest memory, and market drift analysis.

## 4. Accepted Scope

Accepted archive chain:
```text
MarketSnapshot
  -> MarketSnapshotArchiveRecord
  -> market_snapshot_archive SQLite table
  -> repository archive methods
  -> MarketSnapshotArchiveService
  -> snapshot archive APIs
  -> optional read-only capture hooks
  -> History archive panel
```

## 5. Accepted Behavior

- `market_snapshot_archive` is created by `init_db()`.
- Repository can save, list, summarize, and group archive records by market.
- `MarketSnapshotArchiveService` can archive single and multiple snapshots.
- `GET /api/snapshots/archive` works.
- `GET /api/snapshots/archive/summary` works.
- `GET /api/snapshots/archive/market/{market_id}` works.
- `POST /api/snapshots/archive` works.
- `POST /api/snapshots/archive/current-source` archives current `MarketSnapshot[]` without creating candidates.
- `POST /api/polymarket/sync-weather-markets` supports optional `archive=true`.
- Scan supports post-scan archive capture without changing strategy behavior.
- Archive failures do not fail scan or sync.
- `LIVE_EXECUTE` remains rejected.

## 6. Not Accepted

PWB-04E does not add:
- trading logic
- wallet handling
- signing
- order placement
- order cancellation
- user positions
- portfolio reads
- live execution
- auto trading
- settlement resolver behavior

## 7. Freeze Boundary

PWB-04E is a read-only and non-executing archive round.
Archive behavior may persist market history, but it must not trigger strategy, simulation, execution, or promotion behavior.

## 8. Verification

Accepted verification at freeze time:
- `polymarket-bot/tests/test_pwb04e_market_snapshot_archive.py` -> `15 passed`
- `weather-dashboard/tests/test_market_snapshot_archive_panel.py` -> `3 passed`
