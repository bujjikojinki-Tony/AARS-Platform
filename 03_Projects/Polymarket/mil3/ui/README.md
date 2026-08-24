# MIL-3.9 Shadow Strategy Console HMI Design v2

## 1. Page Purpose

Provide one read-only surface for deciding whether a PAPER_ONLY shadow strategy deserves further research. It must not be interpreted as a trading terminal.

## 2. User Role and Scenario

The user is a research operator comparing Buy & Hold, Spot Grid, Leveraged Futures Long Grid and AARS Dynamic on the same replay window. The primary scenario is risk-adjusted comparison, followed by investigation of leverage, drawdown, data freshness and evidence.

## 3. Task Model

1. Confirm execution authority and data trust.
2. Identify the highest current replay risk.
3. Compare the four strategy summaries.
4. Inspect equity/drawdown or liquidation/leverage traces.
5. Switch BTC/ETH/SOL and replay windows without changing execution authority.
6. Review current or archived Latest Stable View evidence.
7. Review combined BTC/ETH/SOL exposure and the asset driving highest risk.
8. Compare two Stable View archives for semantic change.
9. Resolve open risk objects before accepting a shadow strategy.
10. Distinguish the cadence used by the replay from Binance's latest observed funding cadence.

## 4. Information Architecture

- Top: PAPER_ONLY authority, freshness, highest risk, payload time and read-only view selectors.
- Left: four-strategy comparison set.
- Center: selected strategy metrics, traces and common-ledger table.
- Right: liquidation-risk priority and actionable risk queue.
- Lower deck: Latest Stable View, P&L attribution, cross-asset portfolio risk and Stable View differences.

## 5. Layout Design

The desktop layout follows a flight-recorder/control-desk pattern with a persistent status header and three operational columns. Below 1250 px the risk rail moves below the center analysis; below 900 px the page becomes a single-column inspection sequence. No horizontal page overflow is permitted.

## 6. Component List

- `SystemStatusBar`
- `DegradedModeBanner`
- `StrategyComparisonRail`
- `SituationSummaryPanel`
- `ReplayTracePanel`
- `CommonLedgerTable`
- `LiquidationRiskDial`
- `AlertActionCard`
- `LatestStableViewCard`
- `EvidenceTracePanel`
- `PaperLedgerAttribution`
- `ParameterProvenanceDrawer`
- `MarketAndWindowSelector`
- `StableViewArchiveSelector`
- `FundingHistoryStatus`
- `FundingCoverageAlert`
- `CrossAssetPortfolioRiskPanel`
- `StableViewDiffPanel`
- `FundingCadenceProvenance`

## 7. Data Model

The page consumes `mil3.dashboard.v2`, `mil3.portfolio.v1`, `mil3.stable-view-diff.v1` and `mil3.funding-cadence.v1`, while keeping display compatibility with v1 static dashboard payloads. The client rejects any execution mode other than `PAPER_ONLY`.

## 8. Alarm and Risk Design

Risk items expose severity, object, trigger, impact, recommended next step, status and closure condition. Highest liquidation risk remains in the main view. Funding gaps explicitly warn that futures costs may be understated and state the effective cadence/provenance. Current Binance cadence and replay cadence remain visibly distinct. Portfolio degradation names affected assets and never implies cross-margin netting.

## 9. Automation / AI Design

AARS output is presented as a recommendation with state, confidence, Bull/Base/Bear probabilities, supporting evidence, counter evidence and the transparent decision reason. It has no execution authority or action control.

## 10. Degraded Mode and Recovery

Missing, stale or unconfirmed data produces a prominent degraded banner. The screen states what remains permitted (inspect stable replay), what is blocked (treating the view as current) and how to recover (refresh candles and regenerate the payload). The embedded demonstration payload is always degraded.

## 11. User Actions and Gates

Available actions only change the inspected market, replay window, archive, strategy, trace or diff baseline. There are no order, credential, live-mode or execution controls. A failed switch preserves the last displayed stable evidence and raises the degraded banner.

## 12. HMI Review Gate

- G1 Task Fit: Accept
- G2 Situation Visibility: Accept
- G3 Risk Visibility: Accept
- G4 Action Clarity: Accept
- G5 Action Gate: Accept; no execution actions exist
- G6 Alarm Actionability: Accept
- G7 Data Trust: Accept
- G8 Automation Transparency: Accept
- G9 Recovery: Accept
- G10 Evidence: Accept with Minor Issues; formal usability validation remains future work

Overall disposition: **Accept with Minor Issues for PAPER_ONLY research use**.

## 13. Run and Regenerate

From `03_Projects/Polymarket/mil3`:

```bash
python run_ingest.py --db mil3_market.sqlite --days 365
python run_funding_ingest.py --db mil3_market.sqlite --days 365
python run_scheduler.py --db mil3_market.sqlite --poll-seconds 3600 --max-cycles 1
python run_archive.py --db mil3_market.sqlite --symbol SOLUSDT --window 90d
python run_api.py --db mil3_market.sqlite --port 8765
```

Open `http://127.0.0.1:8765/`. The server binds to localhost by default and exposes a GET/HEAD/OPTIONS-only API.

For a no-server preview, open `ui/index.html` directly. Direct-file mode uses the degraded demonstration payload; market/window/archive controls require the read-only local API.
