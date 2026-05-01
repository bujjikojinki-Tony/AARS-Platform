# Round_PWB-04E_Accepted_Path_Inventory

## 1. Purpose
This document freezes the accepted implementation paths for:

```text
Round PWB-04E - Market Data Cache & Snapshot Archive v0
```

## 2. Accepted Backend Model Files

- `backend/models/snapshot_archive.py`

Accepted objects:
- `SnapshotArchiveReason`
- `MarketSnapshotArchiveRecord`
- `MarketSnapshotSeries`
- `SnapshotArchiveSummary`

## 3. Accepted Archive and Storage Files

- `backend/archive/market_snapshot_archive_service.py`
- `backend/storage/db.py`
- `backend/storage/repositories.py`

Accepted responsibilities:

| File | Responsibility |
| --- | --- |
| `market_snapshot_archive_service.py` | Archive one or many `MarketSnapshot` records and expose summary/series helpers |
| `db.py` | Create `market_snapshot_archive` table and indexes |
| `repositories.py` | Persist archive rows and return recent rows, market series, and summary |

## 4. Accepted API and Integration Files

- `backend/api/routes_snapshot_archive.py`
- `backend/api/routes_polymarket.py`
- `backend/api/routes_opportunities.py`
- `backend/execution/strategy_runner.py`
- `backend/app_factory.py`

Accepted responsibilities:

| File | Responsibility |
| --- | --- |
| `routes_snapshot_archive.py` | Read-only archive APIs and current-source archive capture |
| `routes_polymarket.py` | Optional `archive=true` capture for sync-weather-markets |
| `routes_opportunities.py` | Optional post-scan archive capture |
| `strategy_runner.py` | Preserve last scan input snapshots for safe post-scan archiving |
| `app_factory.py` | Register snapshot archive router and expose `PWB-04E` in health rounds |

## 5. Accepted Dashboard Files

- `weather-dashboard/src/weather_dashboard/types/weather.py`
- `weather-dashboard/src/weather_dashboard/ui/market_snapshot_archive_panel.py`
- `weather-dashboard/src/weather_dashboard/ui/r5_pages.py`

Accepted behavior:
- show archive summary
- show recent snapshots
- show market series lookup
- allow current-source archive trigger
- remain read-only

## 6. Accepted Tests

- `polymarket-bot/tests/test_pwb04e_market_snapshot_archive.py`
- `weather-dashboard/tests/test_market_snapshot_archive_panel.py`

Accepted checks:
- archive model serialization
- archive table creation
- archive single and multiple snapshots
- market series query
- archive summary query
- archive current source API
- archive current source does not create candidates
- sync archive optional path
- archive UI/API surface
- `LIVE_EXECUTE` rejection

## 7. Accepted Defaults

```text
archive remains read-only
archive-current-source does not create candidates
sync archive is optional
LIVE_EXECUTE remains rejected
```

## 8. Not Accepted Paths

- trade / execute / wallet / order / cancel controls
- archive-triggered simulation
- archive-triggered execution
- archive-triggered promotion

## 9. Inventory Status

PWB-04E accepted path inventory is complete.
