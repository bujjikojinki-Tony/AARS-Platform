# Round PWB-01 Baseline Freeze Note

Freeze Status: ACTIVE
Freeze Date: 2026-04-28
Baseline: Round PWB-01 Execution Core v0

Frozen scope:
- Core data models
- SQLite schema and repositories
- Mock market source
- Placeholder probability provider
- Weather edge strategy v0
- Binary arbitrage strategy v0
- Risk manager
- Strategy runner
- Simulator
- Command parser
- Opportunity routes
- Command routes
- History routes
- Settings routes

Explicitly not included in this baseline:
- PWB-02 weather intelligence
- Real Polymarket connector
- Real weather evidence chain
- Live trading
- Workstation implementation for Polymarket bot
- Charts implementation for Polymarket bot

Freeze rule:
Only defects required to preserve PWB-01 acceptance may be fixed after this note.
No feature expansion is allowed under the PWB-01 freeze line.
