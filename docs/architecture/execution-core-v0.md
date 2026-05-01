# Execution Core v0

## 1. 文档定位

Execution Core v0 — Implementation Architecture

本文件定义：

- PWB-01 的代码结构
- 模块职责边界
- 调用链路
- 依赖方向
- 最小可运行执行闭环

## 2. 总体架构（Implementation View）

### 2.1 模块结构

```text
backend/
  models/
  storage/
  sources/
  probability/
  strategies/
  execution/
  governance/
  api/
frontend/
  pages/
  components/
```

### 2.2 调用主链路

```text
[MockMarketSource]
        ↓
[StrategyRunner]
        ↓
[Strategy (Weather / Arb)]
        ↓
[StrategySignal]
        ↓
[OpportunityCandidate]
        ↓
[RiskManager]
        ↓
[Repository]
        ↓
[API Layer]
        ↓
[Frontend Pages]
```

### 2.3 执行链（含模拟）

```text
Command/API
    ↓
StrategyRunner.run_once()
    ↓
Candidates persisted
    ↓
Command: /simulate
    ↓
Simulator
    ↓
SimulationResult persisted
```

### 2.4 当前 repo 实现映射

上面的 `backend/...` 结构是概念实现视图。

当前 repo 中，PWB-01 实际落地在单一 Python 包：

```text
weather-comparison-engine/
  src/weather_comparison_engine/polymarket_bot/
```

当前概念模块与现有实现文件的映射如下：

| Conceptual Module | Current File |
|---|---|
| `models/` | `weather_comparison_engine/polymarket_bot/models.py` |
| `storage/db.py` | `weather_comparison_engine/polymarket_bot/storage.py` |
| `storage/repositories.py` | `weather_comparison_engine/polymarket_bot/repositories.py` |
| `sources/mock_market_source.py` | `weather_comparison_engine/polymarket_bot/sources.py` |
| `probability/placeholder_probability_provider.py` | `weather_comparison_engine/polymarket_bot/probability.py` |
| `strategies/weather_edge_strategy.py` | `weather_comparison_engine/polymarket_bot/weather_edge_strategy.py` |
| `strategies/binary_arb_strategy.py` | `weather_comparison_engine/polymarket_bot/binary_arb_strategy.py` |
| `execution/strategy_runner.py` | `weather_comparison_engine/polymarket_bot/strategy_runner.py` |
| `execution/risk_manager.py` | `weather_comparison_engine/polymarket_bot/risk_manager.py` |
| `execution/simulator.py` | `weather_comparison_engine/polymarket_bot/simulator.py` |
| `api/command_parser.py` | `weather_comparison_engine/polymarket_bot/command_parser.py` |
| `api/routes_opportunities.py` | `weather_comparison_engine/polymarket_bot/routes_opportunities.py` |
| `api/routes_command.py` | `weather_comparison_engine/polymarket_bot/routes_command.py` |
| `api/routes_history.py` | `weather_comparison_engine/polymarket_bot/routes_history.py` |
| `api/routes_settings.py` | `weather_comparison_engine/polymarket_bot/routes_settings.py` |

解释：

- PWB-01 采用了“单包收口”的最小实现方式，以保证 deterministic、可测试、冻结边界清晰。
- 在进入后续真正 `backend/` 多目录拆分之前，不要求当前代码强行迁移到概念目录结构。
- 只要模块职责边界与依赖方向保持一致，当前实现被视为符合 `Execution Core v0`。

## 3. 依赖原则（非常关键）

### 3.1 单向依赖

```text
sources → strategies → execution → api
            ↓
         storage
            ↓
         models
```

禁止：

- strategy 直接调用 API
- repository 调用 strategy
- simulator 调用 API
- frontend 直接访问数据库

### 3.2 核心原则

1. 所有状态必须进入 SQLite（通过 repository）
2. 所有副作用必须写 `audit_logs`
3. execution 层不能调用外部 API
4. 本轮不允许 live trading

## 4. 模块详细设计

### 4.1 `models/`

职责：

定义所有核心数据结构（纯数据，无逻辑）

文件：

- `models/core.py`
- `models/enums.py`

内容：

- `MarketSnapshot`
- `StrategySignal`
- `OpportunityCandidate`
- `RiskGateResult`
- `ExecutionDecision`
- `SimulationResult`
- `AuditLogEvent`
- `RuleConfig`
- `SystemState`

### 4.2 `storage/`

职责：

SQLite 持久化

文件：

- `storage/db.py`
- `storage/schema.sql`
- `storage/repositories.py`

#### 4.2.1 `db.py`

```python
def init_db(db_path: str):
    # create tables
```

#### 4.2.2 `repositories.py`

原则：

只做 CRUD，不做业务判断

示例：

```python
class Repository:
    def save_market_snapshot(self, snapshot): ...
    def save_strategy_signal(self, signal): ...
    def save_opportunity_candidate(self, candidate): ...
    def save_simulation_result(self, result): ...
    def save_audit_log(self, event): ...
    def list_opportunity_candidates(self, limit=100): ...
    def get_candidate(self, candidate_id): ...
```

### 4.3 `sources/`

职责：

提供 market 数据

文件：

- `sources/mock_market_source.py`

接口：

```python
class MarketSource:
    def fetch_markets(self) -> list[MarketSnapshot]:
        ...
```

v0 实现：

- `MockMarketSource`（唯一实现）

### 4.4 `probability/`

职责：

提供 model probability（占位）

文件：

- `probability/placeholder_probability_provider.py`

接口：

```python
class ProbabilityProvider:
    def estimate(self, market: MarketSnapshot) -> float:
        ...
```

### 4.5 `strategies/`

职责：

生成 `StrategySignal`

文件：

- `strategies/weather_edge_strategy.py`
- `strategies/binary_arb_strategy.py`

接口：

```python
class Strategy:
    def evaluate(self, market: MarketSnapshot) -> StrategySignal | None:
        ...
```

约束：

1. 不访问数据库
2. 不访问 API
3. 只依赖输入 market

### 4.6 `execution/`

职责：

执行链核心

文件：

- `execution/strategy_runner.py`
- `execution/risk_manager.py`
- `execution/simulator.py`

#### 4.6.1 `StrategyRunner`

职责：

驱动整个扫描流程

伪代码：

```python
def run_once():
    markets = source.fetch_markets()
    for market in markets:
        save(snapshot)
        for strategy in strategies:
            signal = strategy.evaluate(market)
            if not signal:
                continue
            save(signal)
            candidate = to_candidate(signal)
            risk = risk_manager.evaluate(candidate)
            candidate.risk_status = risk.status
            candidate.action_status = resolve_action(risk)
            save(candidate)
            audit("CANDIDATE_CREATED")
```

#### 4.6.2 `RiskManager`

输入：

- `OpportunityCandidate`

输出：

- `RiskGateResult`

#### 4.6.3 `Simulator`

输入：

- `candidate_id`
- `position_size`

输出：

- `SimulationResult`

强约束：

- 不允许调用 live execution
- 不允许调用交易 API

### 4.7 `governance/`

职责：

规则与安全边界

文件：

- `governance/rule_registry.py`
- `governance/risk_gate.py`

内容：

- 默认规则
- 规则更新
- 规则读取

### 4.8 `api/`

职责：

HTTP 接口层

文件：

- `api/routes_opportunities.py`
- `api/routes_command.py`
- `api/routes_history.py`
- `api/routes_settings.py`
- `api/command_parser.py`

原则：

1. API 只 orchestrate
2. 不写核心逻辑
3. 调用 execution / repository

## 5. 关键数据流

### 5.1 Scan Flow

```text
POST /api/opportunities/scan
        ↓
StrategyRunner.run_once()
        ↓
markets → signals → candidates
        ↓
repository.save(...)
        ↓
audit_logs
        ↓
response
```

### 5.2 Simulation Flow

```text
POST /api/command "/simulate id"
        ↓
CommandParser
        ↓
Simulator.simulate()
        ↓
SimulationResult
        ↓
repository.save(...)
        ↓
audit_logs
```

### 5.3 Settings Flow

```text
POST /api/settings/rules
        ↓
rule_registry.update()
        ↓
repository.save(rule)
        ↓
audit_logs
```

## 6. Execution Mode 控制

定义：

- `OBSERVE_ONLY` (default)
- `SIMULATION`
- `PAPER_TRADE` (not implemented)
- `LIVE_EXECUTE` (forbidden in PWB-01)

规则：

1. default = `OBSERVE_ONLY`
2. `SIMULATION` 允许
3. `PAPER_TRADE` 不执行
4. `LIVE_EXECUTE` 禁止

enforcement：

- `Simulator` 不读取 mode（始终 simulation）
- API 拒绝 `LIVE_EXECUTE`
- Settings API 拒绝设置 `LIVE_EXECUTE`

## 7. Audit Logging（强制）

所有关键动作必须记录：

- `CANDIDATE_CREATED`
- `SIMULATION_CREATED`
- `SIMULATION_REJECTED`
- `COMMAND_EXECUTED`
- `COMMAND_REJECTED`
- `RULE_UPDATED`
- `MODE_CHANGED`
- `MODE_CHANGE_REJECTED`

示例：

```python
repository.save_audit_log({
    "event_type": "SIMULATION_CREATED",
    "object_id": simulation_id,
    "payload": {...}
})
```

## 8. 错误处理策略

原则：

1. 不抛未捕获异常
2. 返回结构化错误
3. 写 `audit_logs`

示例：

```json
{
  "status": "error",
  "code": "SIMULATION_BLOCKED",
  "message": "candidate risk_status = BLOCK"
}
```

## 9. 最小可运行闭环

当以下条件满足，即认为 Execution Core v0 完成：

1. mock markets 可读取
2. strategy 可生成 signals
3. candidates 可生成
4. risk gate 生效
5. simulation 可运行
6. SQLite 持久化正常
7. audit logs 完整
8. API 可触发 scan 与 simulation
9. frontend 可显示 candidates
10. 无 live execution

## 10. 不在本轮实现

- real Polymarket API
- weather data ingestion
- DEB / calibration
- portfolio management
- auto trading
- live execution
- multi-exchange
- alerts / subscription

## 11. PWB-02 接口预留

后续扩展点：

- `ProbabilityProvider` → Weather Intelligence Layer
- `MarketSource` → real Polymarket connector
- `Strategy` → multi-factor strategies
- `RiskManager` → portfolio-level risk
- `Simulator` → backtesting engine
- `Execution` → paper trading engine

## 12. Repo 结构建议

```text
backend/
  models/
  storage/
  sources/
  probability/
  strategies/
  execution/
  governance/
  api/
frontend/
  pages/
  components/
docs/
  implementation/
  architecture/
```

### 12.1 当前冻结基线结构

PWB-01 freeze 基线采用如下实际结构：

```text
weather-comparison-engine/
  src/weather_comparison_engine/polymarket_bot/
    __init__.py
    models.py
    storage.py
    repositories.py
    sources.py
    probability.py
    weather_edge_strategy.py
    binary_arb_strategy.py
    risk_manager.py
    strategy_runner.py
    simulator.py
    command_parser.py
    routes_opportunities.py
    routes_command.py
    routes_history.py
    routes_settings.py
```

这套结构在 PWB-01 冻结线内被接受，不要求再做目录重构。

## 13. Codex 实施提示

Implement Execution Core v0 exactly as defined.

Strict rules:

- Use SQLite only
- Use mock market source only
- Use placeholder probability only
- Do NOT connect to Polymarket
- Do NOT enable live trading
- Do NOT add new features
- Do NOT skip audit logging

Focus on:

- clean module boundaries
- deterministic behavior
- testability

## 14. Obsidian 放置位置

```text
03_Projects/Polymarket_Bot/Architecture/
  Execution_Core_v0.md
```

## 15. Repo 放置位置

```text
docs/architecture/
  execution-core-v0.md
```

## 16. 下一步（关键）

到这里，你其实已经具备：

- 完整架构（Execution Core）
- 完整 backlog（可执行）
- 完整验收测试（停止条件）
- 清晰分阶段 Codex prompt

下一步有两个分支，你需要选一个：

### A. 进入“真实开发落地”

可以直接生成：

backend skeleton（完整目录 + 文件 + 初始代码）

这是可以直接复制到 repo 开始跑的版本。

### B. 进入 PWB-02（Weather Intelligence）

开始接：

PolyWeather + DEB + calibration + source health

建议：

不要跳 PWB-02 之前的收口。

先把 PWB-01 跑通（哪怕很简陋），否则会出现：

- 架构越来越复杂
- 但系统始终跑不起来

如果进入 `go codebase`，下一步目标应是：

一整套可运行的 backend skeleton（含 FastAPI + SQLite + runner）。
