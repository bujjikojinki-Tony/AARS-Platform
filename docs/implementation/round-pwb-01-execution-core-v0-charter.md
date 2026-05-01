# Round PWB-01 Execution Core v0 Implementation Charter

## 1. Round Positioning

**Round name**

Round PWB-01 — Execution Core v0

**Round goal**

Establish the minimum runnable execution core for the Polymarket Bot so the system can complete:

market scan  
→ signal generation  
→ risk gating  
→ simulation execution  
→ history recording  
→ page display

This round is not a full trading system, does not pursue complex weather forecasting, and does not enable live trading by default.

## 2. Current Latest Stable View

**Latest Stable View — Polymarket Bot Research**

Current system positioning:

Governed Weather-Market Research & Execution Gateway

Current accepted architecture:

1. Source Layer
2. Evidence Normalization Layer
3. Weather Intelligence Layer
4. Probability Governance Layer
5. Market Divergence Layer
6. Governance & Execution Layer
7. Product / Ops Layer

Current accepted pages:

1. Opportunity Board
2. Workstation
3. Pipeline
4. Market
5. Charts
6. History
7. Evidence / Raw
8. Command
9. Settings

Current external references:

1. `hcharper/polyBot-Weather`: execution core, simulation, risk manager, strategy runner, SQLite
2. `yangyuan-zhen/PolyWeather`: weather intelligence, DEB, calibrated probability, source health, monitoring

This round implements **Execution Core v0 only**.

## 3. Round Boundaries

### 3.1 In scope

This round implements only:

1. strategy runner
2. risk manager
3. simulator
4. datastore
5. opportunity candidate model
6. basic weather edge strategy
7. binary arbitrage strategy
8. command action skeleton
9. SQLite persistence
10. minimum interfaces required by Opportunity Board / History / Command / Settings

### 3.2 Out of scope

This round explicitly does not implement:

1. default-on live auto trading
2. complex DEB / EMOS / LGBM integration
3. full workstation weather evidence chain
4. subscriptions, billing, points, membership systems
5. high-frequency trading
6. large frontend redesign
7. Telegram bot integration
8. multi-exchange expansion
9. true automatic real-money execution
10. strategy return promises

## 4. Core Assumptions

H1. Polymarket market data may first enter the system through mock / fixture / read-only connectors.

H2. Weather probability may first be represented by placeholder / Gaussian v0 / fixed probability engines.

H3. The value of this round is execution-chain closure, not forecast quality.

H4. All trade actions default to simulation / paper modes.

H5. Live mode remains interface-only and disabled by default.

H6. Every signal, decision, and simulation must be recordable and replayable.

## 5. Deliverables

### 5.1 Backend deliverables

```text
backend/
  execution/
    strategy_runner.py
    risk_manager.py
    simulator.py
    paper_trader.py
    approval_gate.py
    circuit_breaker.py
  strategies/
    weather_edge_strategy.py
    binary_arb_strategy.py
  market/
    market_probability.py
    divergence_scanner.py
    opportunity_ranker.py
  storage/
    db.py
    models.py
    repositories.py
  governance/
    rule_registry.py
    market_gate.py
    risk_gate.py
    audit_log.py
  api/
    routes_opportunities.py
    routes_command.py
    routes_history.py
    routes_settings.py
```

### 5.2 Frontend deliverables

This round requires only minimum page integration, not advanced UI restyling.

```text
frontend/
  pages/
    OpportunityBoardPage.tsx
    HistoryPage.tsx
    CommandPage.tsx
    SettingsPage.tsx
  components/
    OpportunityTable.tsx
    RiskGateBadge.tsx
    CommandQueuePanel.tsx
    SimulationResultPanel.tsx
    RuleRegistryTable.tsx
```

### 5.3 Documentation deliverables

```text
docs/
  implementation/
    round-pwb-01-execution-core-v0-charter.md
    round-pwb-01-backlog.md
    round-pwb-01-acceptance-test.md
  architecture/
    execution-core-v0.md
  governance/
    execution-gate-rules-v0.md
    risk-manager-rules-v0.md
```

## 6. v0 Data Objects

### 6.1 MarketSnapshot

```ts
export type MarketSnapshot = {
  marketId: string;
  question: string;
  slug?: string;
  category?: string;
  yesPrice: number;
  noPrice: number;
  liquidity: number;
  spread: number;
  fetchedAt: string;
  source: "polymarket" | "mock";
};
```

### 6.2 StrategySignal

```ts
export type StrategySignal = {
  signalId: string;
  marketId: string;
  strategyId: string;
  side: "YES" | "NO" | "WAIT";
  modelProbability: number;
  marketProbability: number;
  edgePercent: number;
  zScore?: number;
  confidence: "LOW" | "MEDIUM" | "HIGH";
  reason: string;
  createdAt: string;
};
```

### 6.3 OpportunityCandidate

```ts
export type OpportunityCandidate = {
  candidateId: string;
  signalId: string;
  marketId: string;
  question: string;
  side: "YES" | "NO" | "WAIT";
  marketProbability: number;
  modelProbability: number;
  edgePercent: number;
  zScore?: number;
  liquidity: number;
  spread: number;
  confidenceTier: "LOW" | "MEDIUM" | "HIGH";
  riskStatus: "PASS" | "WARN" | "BLOCK";
  actionStatus: "WATCH" | "SIMULATE" | "APPROVE_SMALL" | "BLOCKED" | "EXECUTED" | "EXPIRED";
  createdAt: string;
  expiresAt?: string;
};
```

### 6.4 RiskGateResult

```ts
export type RiskGateResult = {
  candidateId: string;
  status: "PASS" | "WARN" | "BLOCK";
  checks: {
    minEdgePassed: boolean;
    minLiquidityPassed: boolean;
    maxSpreadPassed: boolean;
    maxPositionPassed: boolean;
    circuitBreakerInactive: boolean;
  };
  reasons: string[];
  checkedAt: string;
};
```

### 6.5 ExecutionDecision

```ts
export type ExecutionDecision = {
  decisionId: string;
  candidateId: string;
  mode: "OBSERVE_ONLY" | "SIMULATION" | "PAPER_TRADE" | "APPROVE_SMALL" | "LIVE_EXECUTE" | "BLOCKED";
  action: "BUY_YES" | "BUY_NO" | "WAIT" | "BLOCK";
  requestedBy?: string;
  approvedBy?: string;
  approvalRequired: boolean;
  approvalStatus: "NOT_REQUIRED" | "PENDING" | "APPROVED" | "REJECTED" | "EXPIRED";
  positionSize: number;
  expectedCost: number;
  riskStatus: "PASS" | "WARN" | "BLOCK";
  executionStatus: "QUEUED" | "SIMULATED" | "PAPER_EXECUTED" | "LIVE_EXECUTED" | "FAILED" | "CANCELLED";
  createdAt: string;
  executedAt?: string;
};
```

### 6.6 SimulationResult

```ts
export type SimulationResult = {
  simulationId: string;
  decisionId: string;
  candidateId: string;
  side: "YES" | "NO";
  entryPrice: number;
  positionSize: number;
  simulatedCost: number;
  expectedProbability: number;
  expectedValue: number;
  maxLoss: number;
  maxGain: number;
  resultStatus: "CREATED" | "RUNNING" | "COMPLETED" | "FAILED";
  createdAt: string;
};
```

## 7. SQLite Tables v0

```sql
CREATE TABLE market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  market_id TEXT NOT NULL,
  question TEXT NOT NULL,
  yes_price REAL NOT NULL,
  no_price REAL NOT NULL,
  liquidity REAL,
  spread REAL,
  source TEXT NOT NULL,
  fetched_at TEXT NOT NULL
);

CREATE TABLE strategy_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  signal_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  strategy_id TEXT NOT NULL,
  side TEXT NOT NULL,
  model_probability REAL NOT NULL,
  market_probability REAL NOT NULL,
  edge_percent REAL NOT NULL,
  z_score REAL,
  confidence TEXT NOT NULL,
  reason TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE opportunity_candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  candidate_id TEXT NOT NULL,
  signal_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  question TEXT NOT NULL,
  side TEXT NOT NULL,
  market_probability REAL NOT NULL,
  model_probability REAL NOT NULL,
  edge_percent REAL NOT NULL,
  z_score REAL,
  liquidity REAL,
  spread REAL,
  confidence_tier TEXT,
  risk_status TEXT,
  action_status TEXT,
  created_at TEXT NOT NULL,
  expires_at TEXT
);

CREATE TABLE execution_decisions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  decision_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  mode TEXT NOT NULL,
  action TEXT NOT NULL,
  approval_required INTEGER NOT NULL,
  approval_status TEXT NOT NULL,
  position_size REAL,
  expected_cost REAL,
  risk_status TEXT,
  execution_status TEXT,
  created_at TEXT NOT NULL,
  executed_at TEXT
);

CREATE TABLE simulation_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  simulation_id TEXT NOT NULL,
  decision_id TEXT NOT NULL,
  candidate_id TEXT NOT NULL,
  side TEXT NOT NULL,
  entry_price REAL NOT NULL,
  position_size REAL NOT NULL,
  simulated_cost REAL NOT NULL,
  expected_probability REAL,
  expected_value REAL,
  max_loss REAL,
  max_gain REAL,
  result_status TEXT,
  created_at TEXT NOT NULL
);

CREATE TABLE audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  object_type TEXT NOT NULL,
  object_id TEXT NOT NULL,
  payload_json TEXT,
  created_at TEXT NOT NULL
);
```

## 8. Strategy Runner v0

### 8.1 Responsibility

`StrategyRunner` is responsible for:

1. fetching market snapshots
2. evaluating strategies into `StrategySignal`
3. converting `StrategySignal` into `OpportunityCandidate`
4. invoking `RiskManager`
5. saving results
6. publishing results to Opportunity Board

### 8.2 Pseudocode

```python
class StrategyRunner:
    def __init__(self, market_source, strategies, risk_manager, repository):
        self.market_source = market_source
        self.strategies = strategies
        self.risk_manager = risk_manager
        self.repository = repository

    def run_once(self):
        markets = self.market_source.fetch_markets()
        candidates = []
        for market in markets:
            self.repository.save_market_snapshot(market)
            for strategy in self.strategies:
                signal = strategy.evaluate(market)
                if signal is None:
                    continue
                self.repository.save_signal(signal)
                candidate = self.to_candidate(signal, market)
                risk_result = self.risk_manager.evaluate(candidate)
                candidate.risk_status = risk_result.status
                candidate.action_status = self.resolve_action_status(risk_result)
                self.repository.save_candidate(candidate)
                self.repository.save_audit_log(
                    event_type="CANDIDATE_CREATED",
                    object_type="OpportunityCandidate",
                    object_id=candidate.candidate_id,
                    payload={
                        "signal_id": signal.signal_id,
                        "risk_status": risk_result.status
                    }
                )
                candidates.append(candidate)
        return candidates
```

## 9. Risk Manager v0

### 9.1 Default rules

- `min_edge_percent = 10`
- `min_liquidity = 100`
- `max_spread = 0.08`
- `max_position_percent = 2`
- `max_daily_loss_percent = 5`
- `circuit_breaker_loss_percent = 10`

### 9.2 Gating logic

**PASS**
- edge >= min_edge_percent
- liquidity >= min_liquidity
- spread <= max_spread
- circuit breaker inactive

**WARN**
- edge passed but liquidity is low
- spread is close to threshold
- confidence is medium

**BLOCK**
- edge below threshold
- spread too wide
- liquidity unavailable
- circuit breaker active

### 9.3 Output

`RiskGateResult`

## 10. Weather Edge Strategy v0

### 10.1 Simplification principle

This round does not implement complex weather modeling. It keeps only the strategy interface.

`WeatherEdgeStrategy v0 = market_probability + placeholder model_probability → edge`

Real weather evidence and the Weather Intelligence Layer are deferred to `PWB-02`.

### 10.2 Pseudocode

```python
class WeatherEdgeStrategy:
    strategy_id = "weather_edge_v0"

    def __init__(self, probability_provider, min_edge_percent=10):
        self.probability_provider = probability_provider
        self.min_edge_percent = min_edge_percent

    def evaluate(self, market):
        model_probability = self.probability_provider.estimate(market)
        market_probability = market.yes_price
        edge_percent = (model_probability - market_probability) * 100
        if abs(edge_percent) < self.min_edge_percent:
            return None
        side = "YES" if edge_percent > 0 else "NO"
        return StrategySignal(
            signal_id=make_id("sig"),
            market_id=market.market_id,
            strategy_id=self.strategy_id,
            side=side,
            model_probability=model_probability,
            market_probability=market_probability,
            edge_percent=edge_percent,
            confidence="LOW",
            reason="placeholder probability engine indicates model-market divergence",
            created_at=now_iso()
        )
```

## 11. Binary Arbitrage Strategy v0

### 11.1 Rule

If `YES price + NO price < 1 - fee_buffer`, then a binary arbitrage candidate exists.

### 11.2 Default parameters

- `fee_buffer = 0.02`
- `min_profit_percent = 1`

### 11.3 Output

`StrategySignal`

## 12. Simulator v0

### 12.1 Responsibility

1. receive `ExecutionDecision`
2. simulate an order at the current price
3. calculate cost, max loss, max gain, and expected value
4. write to `simulation_results`
5. never place a real trade

### 12.2 Expected Value

`EV = model_probability * max_gain - (1 - model_probability) * max_loss`

### 12.3 Output

`SimulationResult`

## 13. Command v0

### 13.1 Supported commands

- `/run scan`
- `/list opportunities`
- `/simulate <candidate_id>`
- `/block <candidate_id>`
- `/set mode observe_only`
- `/set mode simulation`
- `/show rules`
- `/show history`

### 13.2 Not yet supported

- `/live execute`
- `/approve large`
- `/auto trade`
- `/promote model`

## 14. API v0

### 14.1 Opportunity API

- `GET /api/opportunities`
- `POST /api/opportunities/scan`
- `GET /api/opportunities/{candidate_id}`
- `POST /api/opportunities/{candidate_id}/block`

### 14.2 Command API

- `POST /api/command`
- `GET /api/command/history`

### 14.3 Simulation API

- `POST /api/simulations`
- `GET /api/simulations/{simulation_id}`

### 14.4 Settings API

- `GET /api/settings/rules`
- `POST /api/settings/rules`
- `GET /api/settings/mode`
- `POST /api/settings/mode`

### 14.5 History API

- `GET /api/history/signals`
- `GET /api/history/candidates`
- `GET /api/history/simulations`
- `GET /api/history/audit`

## 15. Frontend v0 Page Requirements

### 15.1 Opportunity Board

Must display:

- `candidate_id`
- market question
- side
- market probability
- model probability
- edge
- risk status
- action status
- created at

Must support:

- scan
- simulate
- block
- open history

### 15.2 Command Page

Must support:

- command input
- command history
- command execution result
- current mode display
- risk gate result display

### 15.3 History Page

Must display:

- signals
- candidates
- simulations
- audit logs

### 15.4 Settings Page

Must support:

- view rules
- update `min_edge_percent`
- update `max_spread`
- update `min_liquidity`
- switch `observe_only / simulation`

## 16. Acceptance Tests

### Test 1 — Scan Creates Candidate

Given mock market data  
When `/run scan` is executed  
Then at least one `StrategySignal` is created  
And at least one `OpportunityCandidate` is created  
And both are saved to SQLite

### Test 2 — Risk Gate Blocks Weak Candidate

Given `candidate edge < min_edge_percent`  
When risk manager evaluates candidate  
Then `risk_status = BLOCK`  
And `action_status = BLOCKED`

### Test 3 — Simulation Does Not Trade Live

Given `candidate risk_status = PASS`  
When `/simulate <candidate_id>` is executed  
Then `SimulationResult` is created  
And no live trade is executed  
And audit log records `SIMULATION_CREATED`

### Test 4 — Mode Defaults to Observe Only

Given fresh system start  
When settings are loaded  
Then `execution_mode = OBSERVE_ONLY`  
And live execution is disabled

### Test 5 — Command Is Audited

Given user runs `/run scan`  
When command completes  
Then `audit_logs` contains `COMMAND_EXECUTED`  
And payload records command text and result summary

## 17. Stop Condition

This round is complete when:

1. mock market scan works
2. signals are generated
3. candidates are generated
4. risk gate works
5. simulation works
6. SQLite history works
7. Opportunity Board can display candidates
8. Command can trigger scan and simulation
9. Settings can show and update basic rules
10. no live trading occurs by default

After this stop condition, the project must not continue into complex weather modeling. Complex weather evidence begins in `PWB-02`.

## 18. Risks

| Risk | Description | Mitigation |
|---|---|---|
| Scope creep | pressure to build full weather intelligence immediately | defer to `PWB-02` |
| Live trading risk | accidental real trade execution | default `OBSERVE_ONLY`; live executor disabled |
| Poor probability | placeholder probability is weak | this round validates chain closure, not forecast quality |
| UI overbuild | pages become overdesigned | keep minimum tables and buttons |
| Data inconsistency | mock / real source mixing | source field must explicitly mark `mock` or `polymarket` |
| Rule ambiguity | risk rules are unclear | make defaults explicit in `rule_registry` |

## 19. Recommended Obsidian Location

```text
03_Projects/Polymarket_Bot/Implementation/
  Round_PWB-01_Execution_Core_v0_Implementation_Charter.md
```

Companion files:

```text
03_Projects/Polymarket_Bot/Implementation/
  Round_PWB-01_Backlog.md
  Round_PWB-01_Acceptance_Test.md
03_Projects/Polymarket_Bot/Architecture/
  Execution_Core_v0.md
03_Projects/Polymarket_Bot/Governance/
  Risk_Manager_Rules_v0.md
  Execution_Gate_Rules_v0.md
```

## 20. Recommended Repo Location

```text
docs/implementation/
  round-pwb-01-execution-core-v0-charter.md
  round-pwb-01-backlog.md
  round-pwb-01-acceptance-test.md
docs/architecture/
  execution-core-v0.md
docs/governance/
  risk-manager-rules-v0.md
  execution-gate-rules-v0.md
```

## 21. Next Step

The next document is:

`Round_PWB-01_Backlog.md`

Its purpose is to split this round into Codex-executable tasks:

- Task 01 — Define core data models
- Task 02 — Create SQLite schema
- Task 03 — Implement repository layer
- Task 04 — Implement mock market source
- Task 05 — Implement weather edge strategy v0
- Task 06 — Implement binary arbitrage strategy v0
- Task 07 — Implement risk manager
- Task 08 — Implement strategy runner
- Task 09 — Implement simulator
- Task 10 — Implement command API
- Task 11 — Implement opportunity API
- Task 12 — Implement history API
- Task 13 — Implement settings API
- Task 14 — Wire Opportunity Board
- Task 15 — Wire Command Page
- Task 16 — Wire History Page
- Task 17 — Wire Settings Page
- Task 18 — Run acceptance tests
