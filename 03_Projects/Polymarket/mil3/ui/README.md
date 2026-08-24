# MIL-3.6 Shadow Strategy Console HMI Design v0

## 1. Page Purpose

Provide one read-only surface for deciding whether a PAPER_ONLY shadow strategy deserves further research. It must not be interpreted as a trading terminal.

## 2. User Role and Scenario

The user is a research operator comparing Buy & Hold, Spot Grid, Leveraged Futures Long Grid and AARS Dynamic on the same replay window. The primary scenario is risk-adjusted comparison, followed by investigation of leverage, drawdown, data freshness and evidence.

## 3. Task Model

1. Confirm execution authority and data trust.
2. Identify the highest current replay risk.
3. Compare the four strategy summaries.
4. Inspect equity/drawdown or liquidation/leverage traces.
5. Review the Latest Stable View and its evidence.
6. Resolve open risk objects before accepting a shadow strategy.

## 4. Information Architecture

- Top: PAPER_ONLY authority, freshness, highest risk and payload time.
- Left: four-strategy comparison set.
- Center: selected strategy metrics, traces and common-ledger table.
- Right: liquidation-risk priority and actionable risk queue.
- Lower deck: Latest Stable View, evidence, P&L attribution and replay assumptions.

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

## 7. Data Model

The page consumes `mil3.dashboard.v1`. Required top-level fields are `execution_mode`, `market`, `highest_risk`, `latest_stable_view`, `parameters`, `strategies`, `alerts` and `review_gate`. The client rejects any execution mode other than `PAPER_ONLY`.

## 8. Alarm and Risk Design

Risk items expose severity, object, trigger, impact, recommended next step, status and closure condition. Highest liquidation risk is always in the main view. Severity uses both text and color. Maintenance-margin breaches force a critical risk object and prevent an acceptance disposition.

## 9. Automation / AI Design

AARS output is presented as a recommendation with state, confidence, Bull/Base/Bear probabilities, supporting evidence, counter evidence and the transparent decision reason. It has no execution authority or action control.

## 10. Degraded Mode and Recovery

Missing, stale or unconfirmed data produces a prominent degraded banner. The screen states what remains permitted (inspect stable replay), what is blocked (treating the view as current) and how to recover (refresh candles and regenerate the payload). The embedded demonstration payload is always degraded.

## 11. User Actions and Gates

Available actions only change the inspected strategy or trace. There are no order, credential, live-mode or execution controls. The review gate is `DEFER` when freshness is degraded or a liquidation approximation is breached.

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
python run_compare.py \
  --db mil3_market.sqlite \
  --symbol SOLUSDT \
  --interval 1h \
  --futures-leverage 10 \
  --output-json ui/dashboard_payload.json

python -m http.server 8765 --directory ui
```

Open `http://127.0.0.1:8765/`. If `dashboard_payload.json` is absent or invalid, the console uses an explicit degraded demonstration payload.

For a no-server preview, open `ui/index.html` directly in a browser. Direct-file mode uses the degraded demonstration payload because browsers do not allow the page to fetch `dashboard_payload.json` from the local filesystem. Use the HTTP command above whenever real replay output is required.
