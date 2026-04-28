# Task Plan

## Goal
Implement the Phase 32 Operations Monitor as a first-class dashboard homepage and shared contract surface for multi-market operations, focus markets, scanner health, and quick market drill-down.

## Active Task (2026-04-23)
Design and implement `operations_monitor_view.v1`, the dashboard Operations Monitor page, and lightweight Telegram mappings for monitor / focus summaries.

## Steps
- [ ] Inventory existing scanner, opportunity, workstation, and alert sources for Operations Monitor reuse
- [ ] Define `operations_monitor_view.v1` and supporting market card / focus strip contracts
- [ ] Implement dashboard Operations Monitor homepage and drawer flow
- [ ] Add comparison-engine view builder and file outputs for Operations Monitor
- [ ] Add Telegram `/monitor` and `/focus` lightweight mappings
- [ ] Verify dashboard, Telegram, and writer outputs with tests

## Tracks

### Planning
- [completed] Define scope, user stories, capability boundaries, and risk controls for the Polymarket Telegram bot
- [completed] Research GitHub bot patterns, code capabilities, and reusable modules around Polymarket monitoring and execution
- [completed] Produce a recommendation report with phased roadmap, architecture, and build-vs-buy guidance
- [in_progress] Define Operations Monitor information architecture and contract boundaries

### Execution
- [completed] Map event ingestion sources, signal engine design, and Telegram decision workflow
- [completed] Define controlled execution layer with policy gates, approvals, kill-switches, and audit logging
- [completed] Specify optional maker-follow module and its safeguards
- [in_progress] Build Operations Monitor contracts and homepage wiring

### Verification
- [completed] Define backtesting, replay, paper-trading, and sandbox verification strategy
- [completed] Define operational monitoring, alerting, and incident response checkpoints
- [completed] Review legal, platform, and market-manipulation risk assumptions before any live deployment
- [pending] Add contract tests and UI regression for Operations Monitor

## Notes
- Keep `00_Inbox/` files untouched.
- Use only light structural cleanup; do not rewrite core content.
- Favor stable Obsidian-friendly naming in destination paths.
- This task focuses on dashboard / Telegram operational surfaces, not live execution.

## Working Assumptions
- This turn focuses on research and solution planning, not live trading enablement.
- Recommendations should prefer controlled automation with human-in-the-loop approval as the default operating mode.
- Any execution design must include explicit policy constraints, capital limits, and disable paths before discussing automation depth.
