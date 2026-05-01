# Round_PWB-04D_Baseline_Freeze

## 1. Freeze Decision
Round PWB-04D - Polymarket Read-Only Connector v0 is frozen.

Status:
```text
ACCEPTED BASELINE
```

## 2. Freeze Scope

The accepted baseline includes:
- read-only Polymarket connector models
- default MOCK_ONLY config
- read-only Gamma / CLOB clients
- market normalization and weather filtering
- connector health
- read-only market source
- app/services integration
- Polymarket cache tables and repository methods
- read-only `/api/polymarket/*`
- Settings connector panel in the `weather-dashboard` shell
- PWB-04D acceptance and regression tests

## 3. Stable Rules

- `allow_polymarket_network` defaults to `false`.
- `market_source_mode` defaults to `MOCK_ONLY`.
- Clients refuse network access when disabled.
- Only GET-style read methods exist.
- No `post_order`, `cancel_order`, or `sign` methods exist.
- No wallet/private key/signature fields exist.
- HYBRID mode falls back to mock markets when network is disabled.
- POLYMARKET_ONLY remains read-only and returns safely even when network access is disabled.
- `source-mode` changes market input only and does not change execution mode.
- `sync-weather-markets` does not create candidates, signals, simulations, or execution.
- `LIVE_EXECUTE` remains rejected.

## 4. Stable Safety Boundary

This freeze does not add:
- trading logic
- authenticated Polymarket endpoints
- live execution
- order submission
- order cancellation
- wallet handling
- frontend trading controls

Freeze statement:
PWB-04D is accepted as a read-only market discovery connector.
It introduces Polymarket public market data ingestion, weather market filtering, MarketSnapshot mapping, connector health, source mode, cache, read-only APIs, Settings visibility, and hybrid fallback.
It does not introduce wallet, signing, order placement, cancellation, position reading, live execution, or auto trading.
Default mode remains MOCK_ONLY and allow_polymarket_network remains False.

## 5. Freeze Rule

Only defects required to preserve PWB-04D read-only acceptance may be fixed after this note.
No new connector or trading behavior belongs to PWB-04D after freeze.

## 6. Verification Snapshot

- `python -m pytest polymarket-bot/tests/test_pwb04d_polymarket_read_only_connector.py -q` -> `31 passed`
- PWB-04D backend regression subset -> `54 passed`
- `python -m pytest weather-dashboard/tests/test_polymarket_connector_panel.py -q` -> `4 passed`
