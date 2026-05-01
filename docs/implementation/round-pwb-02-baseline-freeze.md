# Round PWB-02 Baseline Freeze

Freeze Status: ACTIVE
Freeze Date: 2026-04-29
Baseline: Round PWB-02 Weather Intelligence v0

Frozen scope:
- Weather market parsing and resolving
- Weather data models and SQLite schema
- Weather source registry and mock/placeholder sources
- Source health checking
- Evidence pack builder
- Weather view builder
- Gaussian probability engine
- Weather probability provider
- Weather edge strategy integration
- Weather APIs
- Evidence APIs
- Workstation API
- Evidence / Raw page
- Workstation page v0
- Pipeline weather nodes
- PWB-02 acceptance tests

Explicitly not included in this baseline:
- Real weather intelligence promotion beyond Gaussian v0
- Real Polymarket connector
- Real NOAA connector
- DEB
- EMOS
- LGBM
- Calibration promotion
- Subscription or payment features
- Telegram bot integration
- Live trading

Freeze rule:
Only defects required to preserve PWB-02 acceptance may be fixed after this note.
No feature expansion is allowed under the PWB-02 freeze line.
