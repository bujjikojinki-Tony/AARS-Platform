# Round_PWB-04F_Status_Note

## 1. Round
Round PWB-04F - Weather Forecast Archive v0

## 2. Status
Accepted for baseline freeze.

## 3. Purpose
PWB-04F adds a passive, time-indexed weather archive layer alongside the accepted PWB-04E market snapshot archive.

It preserves forecast-source records, evidence-pack state, and weather-view state so later rounds can align weather-side inputs with market-side archive records.

## 4. Accepted Scope

Accepted archive chain:
```text
WeatherSourceRecord / EvidencePack / WeatherView
  -> WeatherForecastArchiveService
  -> weather_forecast_archive / weather_evidence_archive / weather_view_archive
  -> repository archive methods
  -> weather archive APIs
  -> optional probability-build archive hook
  -> dashboard History archive panel
```

## 5. Accepted Behavior

- `init_db()` creates all weather archive tables.
- Repository can save, list, summarize, and bundle weather archive records by market.
- `WeatherForecastArchiveService` can archive weather views, evidence packs, and forecast records.
- `GET /api/weather-archive/summary` works.
- `GET /api/weather-archive/views` works.
- `GET /api/weather-archive/forecasts` works.
- `GET /api/weather-archive/evidence` works.
- `GET /api/weather-archive/market/{market_id}` works.
- `POST /api/weather-archive/view` works.
- `POST /api/weather-archive/forecast` works.
- `POST /api/weather-archive/evidence` works.
- `POST /api/weather-archive/latest/{market_id}` archives existing latest weather-side records only.
- Optional probability-build archiving may persist weather-side records after a normal probability build.
- Archive failures do not fail the probability build path.
- The current dashboard shell exposes summary, recent forecasts/evidence/views, market bundle lookup, and archive-latest actions without adding trade or execution controls.
- `LIVE_EXECUTE` remains rejected.

## 6. Not Accepted

PWB-04F does not add:
- external weather fetch from archive APIs
- strategy execution from archive APIs
- simulation
- execution
- calibration
- backtest
- model promotion
- wallet, order, or cancel behavior

## 7. Freeze Boundary

PWB-04F is a read-only and non-executing weather archive round.
Archive behavior may persist weather-side records, but it must not trigger strategy, simulation, execution, or promotion behavior.

## 8. Verification

Accepted verification at freeze time:
- `polymarket-bot/tests/test_pwb04f_weather_forecast_archive.py`
- `weather-dashboard/tests/test_weather_forecast_archive_panel.py`
- `archive latest` does not create candidates
- `archive latest` does not fetch weather
- optional probability-build archive path works
- scan candidate count remains unchanged
- `LIVE_EXECUTE` remains rejected
