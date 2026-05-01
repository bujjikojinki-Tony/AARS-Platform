# Round_PWB-04D_Status_Note

## 1. Round
Round PWB-04D - Polymarket Read-Only Connector v0

## 2. Status
Accepted for baseline freeze.

## 3. Purpose
PWB-04D adds a read-only Polymarket connector boundary for discovery, normalization, cache, API inspection, source-mode control, and Settings visibility.

It is explicitly not a trading round.

## 4. Accepted Scope

Accepted read-only chain:
```text
PolymarketConnectorConfig
  -> read-only Gamma/CLOB clients
  -> market normalization
  -> weather filtering
  -> connector health
  -> read-only market source
  -> app/services integration
  -> cache tables + repository methods
  -> /api/polymarket/*
  -> Settings panel status, warnings, cached markets, preview snapshots
  -> acceptance tests
```

## 5. Accepted Behavior

- Connector config defaults to `MOCK_ONLY`.
- `allow_polymarket_network` defaults to `false`.
- Clients expose read-only GET methods only.
- Network access is refused when disabled.
- `MOCK_ONLY`, `POLYMARKET_ONLY`, and `HYBRID` are the only accepted source modes.
- `HYBRID` falls back to mock markets when the network is disabled or Polymarket data is unavailable.
- `POLYMARKET_ONLY` returns an empty result safely when the network is disabled.
- Cache writes are limited to Polymarket market metadata and connector health.
- `/api/polymarket/source-mode` changes market source runtime only and does not change execution mode.
- `/api/polymarket/sync-weather-markets` remains read-only and does not create candidates, signals, simulations, or execution.
- No wallet, private key, signature, auth, or order-placement fields exist.
- Settings shows connector status, warnings, cached market rows, preview snapshots, and raw connector state.
- `LIVE_EXECUTE` remains rejected.

## 6. Not Accepted

PWB-04D does not add:
- trading methods
- order placement
- order cancellation
- signing or wallet handling
- authenticated Polymarket endpoints
- live execution
- frontend trading controls
- real-network test dependence
- settlement resolver behavior

## 7. Freeze Boundary

Only defects required to preserve PWB-04D read-only acceptance may be fixed after this note.
No new connector or trading features belong to PWB-04D after freeze.

## 8. Verification

Accepted verification at freeze time:
- `polymarket-bot/tests/test_pwb04d_polymarket_read_only_connector.py` -> `31 passed`
- PWB-04D backend regression subset -> `54 passed`
- `weather-dashboard/tests/test_polymarket_connector_panel.py` -> `4 passed`
