# Round PWB-02 Accepted Path Inventory

Accepted implementation path for PWB-02:

1. Question parsing and resolving
   - `MarketQuestionParser.parse()`
   - `WeatherMarketResolver.resolve()`

2. Weather source selection and fetch
   - `WeatherSourceRegistry.select_sources()`
   - `OpenMeteoSource.fetch()`
   - `NoaaPlaceholderSource.fetch()`
   - `SourceHealthChecker.check()`

3. Evidence and weather views
   - `EvidencePackBuilder.build()`
   - `WeatherViewBuilder.build()`
   - SQLite tables:
     - `weather_descriptors`
     - `weather_sources`
     - `evidence_packs`
     - `weather_views`
     - `probability_views`

4. Probability generation
   - `GaussianProbabilityEngine.compute()`
   - `ProbabilityViewBuilder.build()`
   - `WeatherProbabilityProvider.build_probability_view()`

5. Strategy integration
   - `WeatherEdgeStrategy.evaluate()`
   - `StrategyRunner.run_once()`

6. API exposure
   - `POST /api/weather/resolve`
   - `POST /api/weather/probability`
   - `GET /api/weather/descriptor/{market_id}`
   - `GET /api/weather/evidence/{market_id}`
   - `GET /api/weather/view/{market_id}`
   - `GET /api/weather/probability/{market_id}`
   - `GET /api/evidence/packs`
   - `GET /api/evidence/market/{market_id}`
   - `GET /api/workstation/{market_id}`

7. Dashboard surfaces
   - `Evidence / Raw`
   - `Workstation`
   - `Pipeline`
   - PWB-02 runtime profile selection in the Streamlit shell

8. Acceptance and safety
   - `tests/test_pwb02_weather_intelligence.py`
   - `tests/test_pwb02_dashboard_phase_h.py`
   - live execution remains rejected
