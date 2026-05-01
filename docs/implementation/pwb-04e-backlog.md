# PWB-04E Backlog

Status: Draft
Date: 2026-04-30
Scope: Market Data Cache & Snapshot Archive v0

## Objective
Build a read-only market snapshot archive layer on top of PWB-04D so the system can persist time-indexed `MarketSnapshot` history for later calibration, backtest memory, and market drift analysis.

PWB-04E answers:

```text
How do we preserve the market state that the system saw at a given time?
```

## Non-Goals
- No live trading
- No auto trading
- No wallet integration
- No signing or auth expansion
- No order placement
- No order cancellation
- No user position or portfolio reads
- No settlement resolver
- No real DEB implementation
- No real EMOS implementation
- No PnL backtest engine
- No position sizing or portfolio risk work

## Execution Order

### 1. Archive Model and SQLite Foundation
Create the archive data model and persistence table first so later steps can write snapshot history safely.

Deliverables:
- `backend/models/snapshot_archive.py`
- `MarketSnapshotArchiveRecord`
- `MarketSnapshotSeries`
- `SnapshotArchiveSummary`
- `market_snapshot_archive` SQLite table
- recommended indexes on `market_id`, `archived_at`, and `source`

Acceptance:
- Archive models serialize cleanly
- `init_db()` creates the archive table and indexes
- Existing PWB-01/PWB-02/PWB-03/PWB-04D tables still initialize normally

### 2. Repository Archive Methods
Add repository helpers for writing and reading archive rows without changing execution behavior.

Deliverables:
- `save_market_snapshot_archive_record(...)`
- `save_market_snapshot_archive_records(...)`
- `list_market_snapshot_archive(...)`
- `get_market_snapshot_series(...)`
- `get_market_snapshot_archive_summary(...)`

Behavior:
- Persist archive rows only
- Do not trigger scan
- Do not trigger simulation
- Do not trigger execution

Acceptance:
- One snapshot can be saved and read back
- Multiple snapshots for one market can be returned as a time series
- Summary returns totals, unique markets, source distribution, reason distribution, and latest archive timestamp

### 3. Archive Service
Introduce a dedicated archive service that converts runtime `MarketSnapshot` objects into historical archive records.

Deliverables:
- `backend/archive/market_snapshot_archive_service.py`
- `archive_snapshot(...)`
- `archive_snapshots(...)`
- summary and series pass-through helpers

Inputs:
- `MarketSnapshot`
- `market_source_mode`
- `archive_reason`
- optional `raw_ref`
- optional `metadata`

Accepted archive reasons:
- `SCAN_CAPTURE`
- `SYNC_CAPTURE`
- `MANUAL_CAPTURE`
- `PREVIEW_CAPTURE`

Acceptance:
- Single snapshot archive works
- Batch archive works
- Archived records preserve the original market prices, liquidity, spread, and timestamps

### 4. Capture Integration
Attach snapshot archiving to accepted read-only and post-scan capture points.

Accepted capture points:
- `POST /api/polymarket/sync-weather-markets`
- `POST /api/opportunities/scan`
- manual snapshot archive API
- current-source archive API

Rules:
- Sync capture archives only and does not run strategy/simulation/execution
- Scan capture may archive the snapshots already used by scan, but archiving must not trigger scan
- Current-source capture archives snapshots returned by the current market source only

Suggested default:
- `archive_on_scan = true` for local/mock/hybrid research

Acceptance:
- Archiving from current source does not create candidates
- Sync capture can archive snapshots without changing read-only behavior
- Existing scan behavior still works

### 5. Snapshot Archive API
Expose archive history through dedicated read/write endpoints that remain read-only with respect to trading.

Planned routes:
- `GET /api/snapshots/archive`
- `GET /api/snapshots/archive/summary`
- `GET /api/snapshots/archive/market/{market_id}`
- `POST /api/snapshots/archive`
- `POST /api/snapshots/archive/current-source`

Query support:
- `limit`
- `source`
- `archive_reason`

Acceptance:
- Recent archive rows can be listed
- Summary can be queried
- Market series can be queried by `market_id`
- Manual archive works
- Current-source archive works
- No route enables trading or execution

### 6. UI Surface
Expose snapshot archive visibility in the existing UI shell without adding trading controls.

Target shell:
- current dashboard shell in `weather-dashboard`

Planned panel behavior:
- show total snapshots
- show unique markets
- show latest archived timestamp
- show source distribution
- show archive reason distribution
- show recent snapshot rows
- allow market series lookup
- allow current-source archive trigger

Forbidden UI:
- Trade
- Execute
- Simulate
- Auto Trade
- Go Live
- Wallet / key / signing controls

Acceptance:
- History or Settings surface can inspect archive summary and recent rows
- Current-source archive action is read-only
- UI does not expose trading controls

### 7. Verification
Add focused acceptance coverage for archive storage, API behavior, and safety boundaries.

Planned test file:
- `tests/test_pwb04e_market_snapshot_archive.py`

Acceptance targets:
- snapshot archive model serialization
- snapshot archive table creation
- archive single snapshot
- archive multiple snapshots
- list recent snapshots
- market snapshot series
- snapshot archive summary
- archive current source API
- archive current source does not create candidates
- sync-weather-markets archive optional path
- snapshot archive UI/API path
- `LIVE_EXECUTE` still rejected

### 8. Freeze
Freeze the round once archive model, storage, service, capture integration, API, UI, and tests are all green.

Freeze must state:
- PWB-04E is a read-only snapshot archive round
- No wallet, signing, order placement, cancellation, positions, or live execution were introduced
- Archive behavior does not create trading side effects

## Stop Condition
Stop once `MarketSnapshotArchiveRecord`, the archive table, repository methods, archive service, accepted capture paths, archive APIs, UI surface, and PWB-04E acceptance tests are all working and explicitly frozen.
