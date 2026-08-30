# MIL-3.24 PAPER_ONLY Shadow Strategy Bot Orchestrator

MIL-3.24 turns one committed synchronized market snapshot into four isolated,
content-addressed shadow-bot accounts. It reuses the common `ReplayEngine`; it
does not add an exchange client, authenticated request, external order object or
live execution route.

## Fixed fleet

Every new ledger v2 result contains these bots in a fixed order:

1. `BUY_HOLD` — one-time unleveraged benchmark entry;
2. `SPOT_GRID` — parameterized spot grid;
3. `FUTURES_LONG_GRID` — parameterized long grid, including the approved 10x
   exchange-leverage parameter and optional Tactical Hedge;
4. `AARS_DYNAMIC` — Long / Flat / Tactical Short exposure from the AARS state,
   probability and policy engines.

All four bots consume the same candle, funding and funding-cadence hashes. Each
has an independent virtual account and equal-capital per-asset buckets. A bot
cannot transfer equity, margin, fills or risk state to another bot. Account IDs
remain stable for the immutable configuration and bot identity across cycles.

## Approved parameters only

The fleet derives every strategy and accounting parameter from the activated
immutable PAPER_ONLY configuration:

- initial virtual equity per asset;
- fee and slippage rates;
- maintenance-margin approximation;
- grid spacing and level count;
- futures leverage and Tactical Hedge setting;
- AARS maximum absolute exposure;
- maximum drawdown and liquidation-risk stop thresholds.

Because Futures Grid and AARS Dynamic consume funding, every fleet snapshot
requires COMPLETE funding coverage for every asset even when the originally
selected trial candidate was a non-funding strategy. Missing coverage returns
`BLOCKED`; the runtime never assumes a zero rate.

## Deterministic virtual account and fill evidence

Each bot/asset account records:

- final equity, position quantity and average entry;
- realized and inventory unrealized P&L;
- separately attributed realized grid P&L;
- fees, slippage and funding;
- net exposure, effective leverage and margin buffer;
- liquidation-risk approximation and breach count;
- simulated fill count, fill categories and latest simulated fill.

Fills are immediate deterministic ReplayEngine paper fills based on the existing
conservative cost model. They are evidence, not exchange orders. MIL-3.24 does
not claim exchange queue position, partial-fill probability, rejection behavior
or exact venue liquidation tiers.

## Risk stop

Risk policy is opt-in at the fleet calculation boundary and does not change
ordinary historical comparison behavior. When an account exceeds approved
maximum drawdown or liquidation risk, or records any liquidation approximation
breach, ReplayEngine:

1. records the triggering evidence;
2. creates one simulated `risk_stop` flattening fill while equity remains
   positive; an already insolvent approximation is frozen without inventing an
   executable flatten fill;
3. marks only that virtual account `FROZEN`;
4. suppresses later strategy actions for that account.

The risk stop cannot arm or clear the sandbox kill switch, alter a strategy,
change a registry pointer or affect any external account.

## Atomicity, recovery and compatibility

The bot fleet is embedded in `mil3.isolated-paper-ledger-result.v2`. Its own
SHA-256 binds the cycle, market snapshot, configuration, capital model, risk
limits and all four results. The parent ledger hash binds the complete fleet.
The existing RESERVED/RECOVER/COMMIT transaction therefore persists the fleet
and checkpoint atomically.

Duplicate boundaries reuse the committed result and fleet ID. Crash recovery
recalculates against the snapshot boundary rather than wall-clock retry time.
Previously committed MIL-3.23 ledger v1 results remain verifiable and read-only;
they correctly show no four-bot fleet.

## Local operation and inspection

The existing bounded command runs one governed fleet cycle:

```bash
python run_isolated_paper_runtime.py \
  --db mil3_market.sqlite \
  --action RUN \
  --sandbox-id aars-paper-sandbox \
  --worker-id aars-local-paper-worker \
  --lease-seconds 120 \
  --heartbeat-interval-seconds 30 \
  --max-cycles 1
```

The committed ledger, including `bot_fleet`, is inspected through:

```text
GET /api/v1/isolated-paper-ledger-results/{result_id}
```

The API and console are read-only. They expose no start, stop, order, approval,
parameter-change or kill-switch control.

## Permanent authority boundary

```text
execution_mode=PAPER_ONLY
independent_virtual_accounts=true
simulated_order_intents_only=true
risk_stop_can_freeze_paper_accounts_only=true
external_order_requests_created=false
order_path_present=false
automatic_strategy_change_allowed=false
live_execution_allowed=false
```
