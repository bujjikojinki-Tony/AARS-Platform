# Polymarket Bot PWB-01 Module Map

This package is the accepted PWB-01 freeze-line implementation for Execution Core v0.

It intentionally uses a single-package layout:

```text
weather_comparison_engine.polymarket_bot
```

instead of immediately splitting into:

```text
backend/models
backend/storage
backend/sources
backend/probability
backend/strategies
backend/execution
backend/governance
backend/api
```

The conceptual architecture still applies. The mapping is:

| Concept | Current File |
|---|---|
| models | `models.py` |
| storage db | `storage.py` |
| repositories | `repositories.py` |
| market source | `sources.py` |
| probability provider | `probability.py` |
| strategies | `weather_edge_strategy.py`, `binary_arb_strategy.py` |
| execution core | `risk_manager.py`, `strategy_runner.py`, `simulator.py` |
| command parsing | `command_parser.py` |
| route facades | `routes_opportunities.py`, `routes_command.py`, `routes_history.py`, `routes_settings.py` |

PWB-01 constraints:

- SQLite only
- mock market source only
- placeholder probability only
- no real Polymarket connectivity
- no live trading
- deterministic behavior
- audit logging required

This module is frozen under the PWB-01 baseline. Only acceptance-critical defect fixes should be made under this freeze line.
