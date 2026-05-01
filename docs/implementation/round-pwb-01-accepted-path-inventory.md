# Round PWB-01 Accepted Path Inventory

Accepted implementation path for PWB-01:

1. Mock market scan
   - `MockMarketSource.fetch_markets()`
   - `StrategyRunner.run_once()`

2. Strategy evaluation
   - `WeatherEdgeStrategy.evaluate()`
   - `BinaryArbitrageStrategy.evaluate()`

3. Candidate persistence
   - `PolymarketBotRepositories`
   - SQLite tables:
     - `market_snapshots`
     - `strategy_signals`
     - `opportunity_candidates`
     - `execution_decisions`
     - `simulation_results`
     - `audit_logs`

4. Risk gating
   - `RiskManager.evaluate()`
   - default rules from `RiskRules`

5. Command and settings control
   - `CommandRoutes.post_command()`
   - `SettingsRoutes.get_rules()`
   - `SettingsRoutes.post_rules()`
   - `SettingsRoutes.get_mode()`
   - `SettingsRoutes.post_mode()`

6. Simulation only execution
   - `Simulator.simulate()`
   - live execution remains disabled

7. Persisted history retrieval
   - `HistoryRoutes.get_signals()`
   - `HistoryRoutes.get_candidates()`
   - `HistoryRoutes.get_simulations()`
   - `HistoryRoutes.get_audit()`
