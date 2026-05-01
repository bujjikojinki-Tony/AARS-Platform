# Round_PWB-04D_Accepted_Path_Inventory

## 1. Purpose
This document freezes the accepted implementation paths for:

```text
Round PWB-04D - Polymarket Read-Only Connector v0
```

## 2. Accepted Backend Model Files

- `backend/models/polymarket.py`

Accepted objects:
- `PolymarketConnectorMode`
- `MarketSourceMode`
- `PolymarketMarketRecord`
- `PolymarketConnectorHealth`
- `PolymarketPriceRecord`

## 3. Accepted Connector Files

- `backend/connectors/polymarket_config.py`
- `backend/connectors/polymarket_errors.py`
- `backend/connectors/polymarket_gamma_client.py`
- `backend/connectors/polymarket_clob_read_client.py`
- `backend/connectors/polymarket_market_normalizer.py`
- `backend/connectors/polymarket_weather_filter.py`
- `backend/connectors/polymarket_connector_health.py`
- `backend/connectors/polymarket_read_only_market_source.py`

Accepted responsibilities:

| File | Responsibility |
| --- | --- |
| `polymarket_config.py` | Default connector mode and network guard |
| `polymarket_gamma_client.py` | Read-only Gamma-style GET methods with network guard |
| `polymarket_clob_read_client.py` | Read-only CLOB GET methods with network guard |
| `polymarket_market_normalizer.py` | Normalize raw markets into `PolymarketMarketRecord` |
| `polymarket_weather_filter.py` | Include weather markets, exclude non-weather / closed / non-binary markets |
| `polymarket_connector_health.py` | Build connector health and warnings |
| `polymarket_read_only_market_source.py` | Support `MOCK_ONLY`, `POLYMARKET_ONLY`, and `HYBRID` modes |

## 4. Accepted Integration Files

- `backend/services.py`
- `backend/app_factory.py`
- `backend/main.py`
- `backend/api/routes_polymarket.py`
- `backend/storage/db.py`
- `backend/storage/repositories.py`

Accepted responsibilities:

| File | Responsibility |
| --- | --- |
| `services.py` | Carry `allow_polymarket_network`, `market_source_mode`, `polymarket_config`, and select market source |
| `app_factory.py` | Include Polymarket router and expose health fields |
| `main.py` | Preserve safe defaults: `MOCK_ONLY`, offline, read-only |
| `routes_polymarket.py` | Read-only Polymarket health, cache, preview, sync, and source-mode endpoints |
| `db.py` | Create `polymarket_market_cache` and `polymarket_connector_health` tables |
| `repositories.py` | Persist/read connector cache and health history |

## 5. Accepted Dashboard Files

- `weather-dashboard/src/weather_dashboard/ui/polymarket_connector_panel.py`
- `weather-dashboard/src/weather_dashboard/ui/settings_pages.py`
- `weather-dashboard/src/weather_dashboard/types/weather.py`

Accepted behavior:
- show source mode and network gate
- show connector health
- show warnings
- show cached market rows
- show preview snapshots
- show raw connector state
- remain read-only

## 6. Accepted Tests

- `tests/test_pwb04d_polymarket_read_only_connector.py`
- `tests/test_pwb04d_polymarket_api.py`
- `tests/test_pwb04d_cache_repository.py`
- `tests/test_pwb04d_health_source.py`
- `tests/test_pwb04d_app_factory_integration.py`
- `weather-dashboard/tests/test_polymarket_connector_panel.py`

Accepted checks:
- default config values
- default config values
- no auth or trading fields
- read-only client network refusal
- normalizer output
- weather filtering
- connector health
- source mode behavior
- cache repository behavior
- Polymarket API behavior
- HYBRID fallback to mock when network disabled
- sync creates no candidates
- LIVE_EXECUTE rejection

## 7. Accepted Defaults

```text
mode = MOCK_ONLY
allow_polymarket_network = false
read_only = true
```

## 8. Not Accepted Paths

- wallet/private key/signature fields
- order placement / cancellation
- auth flows
- live trading
- network access by default

## 9. Inventory Status

PWB-04D accepted path inventory is complete.
