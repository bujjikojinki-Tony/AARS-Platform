# Snapshot_Archive_Safety_Rules_v0

## 1. 文件目的

本文件定义：

`PWB-04E — Market Data Cache & Snapshot Archive v0`

的安全规则。

PWB-04E 只允许做：

- `MarketSnapshot` 归档
- snapshot 查询
- snapshot summary
- market series 查询
- current-source preview archive
- sync capture archive
- scan input capture archive

不允许做：

- 交易
- 执行
- 下单
- 撤单
- 钱包
- 签名
- 仓位
- 收益回测
- 自动策略运行

## 2. 核心安全原则

### 2.1 Archive is passive

Snapshot Archive 是被动记录层：

```text
MarketSnapshot → MarketSnapshotArchiveRecord → SQLite
```

它不是：

- signal generator
- candidate generator
- simulator
- executor
- trading engine

### 2.2 Archive must not drive action

归档行为不得触发：

- `StrategyRunner`
- `StrategySignal`
- `OpportunityCandidate`
- `RiskManager`
- `Simulator`
- `Execution`
- `PromotionGate`

唯一例外是：

`SCAN_CAPTURE`

但 `SCAN_CAPTURE` 只能在 scan 已经发生后记录 scan input，不能反过来触发 scan。

### 2.3 Archive is evidence, not decision

Archive 记录的是：

```text
当时系统看到的市场输入状态
```

它可以成为后续 calibration / backtest 的证据，但不能直接变成：

- 交易信号
- 下单依据
- 模型晋升依据
- 资金分配依据

## 3. 允许能力

PWB-04E 允许以下能力。

### 3.1 Single snapshot archive

允许：

`POST /api/snapshots/archive`

保存一个手动提交的 `MarketSnapshot`。

用途：

- 测试
- 补录
- 调试
- 数据对齐

### 3.2 Batch snapshot archive

允许：

`MarketSnapshotArchiveService.archive_snapshots(...)`

保存多个 snapshots。

用途：

- current-source capture
- sync capture
- scan input capture

### 3.3 Current source archive

允许：

`POST /api/snapshots/archive/current-source`

行为：

```text
services.market_source.fetch_markets()
→ archive snapshots
```

强约束：

- 不调用 `StrategyRunner`
- 不生成 `StrategySignal`
- 不生成 `OpportunityCandidate`
- 不调用 `Simulator`
- 不调用 `Execution`

### 3.4 Sync capture archive

允许在：

`POST /api/polymarket/sync-weather-markets`

中增加：

```json
{
  "archive": true
}
```

行为：

```text
read-only weather records
→ MarketSnapshot[]
→ archive
```

强约束：

- 不运行 strategy
- 不生成 candidate
- 不 simulation
- 不 execution

### 3.5 Scan input capture

允许在：

`POST /api/opportunities/scan`

之后记录 scan input：

`MarketSnapshot[] → archive_reason = SCAN_CAPTURE`

强约束：

- archive failure must not fail scan
- archive must not change candidates
- archive must not change risk gate
- archive must not trigger simulation

### 3.6 Query archive

允许：

- `GET /api/snapshots/archive`
- `GET /api/snapshots/archive/summary`
- `GET /api/snapshots/archive/market/{market_id}`

用途：

- History UI
- debug
- calibration preparation
- backtest preparation

## 4. 禁止能力

PWB-04E 禁止以下能力。

### 4.1 Trading

禁止任何：

- `trade`
- `trading`
- `buy`
- `sell`
- `place_order`
- `post_order`
- `submit_order`
- `cancel_order`
- `execute_trade`
- `live_execute`
- `auto_trade`

### 4.2 Wallet / auth

禁止任何：

- `wallet`
- `private_key`
- `signature`
- `signing`
- `api_key`
- `api_secret`
- `passphrase`
- `funder`
- `allowance`
- `deposit`
- `withdraw`

### 4.3 Portfolio / position

禁止任何：

- `position`
- `positions`
- `portfolio`
- `balance`
- `pnl`
- `holdings`
- `user_orders`
- `open_orders`
- `fills`

### 4.4 Strategy generation

Archive API 禁止调用：

- `StrategyRunner.run_once`
- `WeatherEdgeStrategy`
- `BinaryArbStrategy`
- `RiskManager.evaluate`
- `Simulator.simulate`

Archive API 只能调用：

- `market_source.fetch_markets`
- repository save/list
- `MarketSnapshotArchiveService`

### 4.5 Model promotion

Archive 不得直接调用：

- `ModelPromotionGate`
- `CalibrationService`
- `ProbabilityComparisonBuilder`
- `ProbabilityEngineRunner`

后续 PWB-05 可以读取 archive 作为输入，但 PWB-04E 不做 calibration/backtest。

## 5. API 安全规则

### 5.1 允许 API

PWB-04E 只允许新增：

- `GET  /api/snapshots/archive`
- `GET  /api/snapshots/archive/summary`
- `GET  /api/snapshots/archive/market/{market_id}`
- `POST /api/snapshots/archive`
- `POST /api/snapshots/archive/current-source`

### 5.2 禁止 API

禁止新增任何：

- `/api/snapshots/trade`
- `/api/snapshots/execute`
- `/api/snapshots/simulate`
- `/api/snapshots/backtest`
- `/api/snapshots/promote`
- `/api/snapshots/order`
- `/api/snapshots/wallet`
- `/api/snapshots/position`

### 5.3 archive-current-source rule

`POST /api/snapshots/archive/current-source` 必须只做：

- `services.market_source.fetch_markets()`
- archive returned snapshots
- return archived records

不得做：

- `services.strategy_runner.run_once()`
- `services.simulator`
- `services.risk_manager`
- execution
- promotion

### 5.4 manual archive rule

`POST /api/snapshots/archive` 必须只接受 snapshot payload 并保存。

不得根据 snapshot 自动：

- 生成 signal
- 生成 candidate
- 触发 weather probability
- 触发 probability comparison
- 触发 calibration
- 触发 simulation

## 6. Repository 安全规则

Repository methods 只能做 CRUD。

允许：

- `save_market_snapshot_archive_record`
- `list_market_snapshot_archive`
- `get_market_snapshot_series`
- `get_market_snapshot_archive_summary`

禁止 repository 中出现：

- `strategy`
- `simulate`
- `execute`
- `trade`
- `order`
- `wallet`
- `promote`
- `calibrate`

Repository 不做业务判断。

## 7. Archive Service 安全规则

`MarketSnapshotArchiveService` 只能调用：

- `repository.save_market_snapshot_archive_record`
- `repository.save_market_snapshot_archive_records`
- `repository.list_market_snapshot_archive`
- `repository.get_market_snapshot_series`
- `repository.get_market_snapshot_archive_summary`

不得调用：

- `StrategyRunner`
- `Simulator`
- `RiskManager`
- `WeatherProbabilityProvider`
- `ProbabilityEngineRunner`
- `ProbabilityComparisonBuilder`
- `CalibrationService`
- `ModelPromotionGate`
- `Execution`

## 8. Source Mode 安全规则

Archive 可以读取当前 market source：

- `MOCK_ONLY`
- `POLYMARKET_ONLY`
- `HYBRID`

但不得改变 source mode。

也不得改变：

- `execution_mode`
- `allow_network`
- `allow_polymarket_network`
- `risk rules`
- `active probability engine`

## 9. Scan Capture 安全规则

如果实现 `archive_on_scan`：

### 9.1 允许

```text
scan already fetched markets
→ archive those market snapshots
```

### 9.2 禁止

- archive triggers scan
- archive changes scan result
- archive changes candidate count
- archive changes risk status
- archive triggers simulation
- archive triggers execution

### 9.3 Failure rule

archive failure must be converted into warning

scan response remains based on scan result

## 10. Sync Capture 安全规则

如果实现：

```json
{
  "archive": true
}
```

则：

```text
sync-weather-markets
→ read-only weather records
→ MarketSnapshot[]
→ archive
```

不得：

- run `StrategyRunner`
- generate candidates
- simulate
- execute
- alter execution mode

## 11. UI 安全规则

### 11.1 允许 UI

允许在 History 页面展示：

- summary cards
- recent snapshots
- market series lookup
- archive current source
- raw JSON viewer

### 11.2 禁止 UI

禁止出现：

- `Trade`
- `Execute`
- `Simulate`
- `Backtest Now`
- `Promote Model`
- `Connect Wallet`
- `Place Order`
- `Cancel Order`
- `Buy`
- `Sell`
- `Auto Trade`
- `Go Live`
- `Position Size`
- `Portfolio`
- `Balance`

### 11.3 Archive Current Source button

按钮只能调用：

`POST /api/snapshots/archive/current-source`

不得调用：

- `POST /api/opportunities/scan`
- `POST /api/command`
- `POST /api/settings/mode`
- 任何 simulation / execution endpoint

## 12. Test 安全规则

PWB-04E 测试必须覆盖：

- snapshot archive model serializes
- archive table created
- single snapshot archive
- multiple snapshot archive
- recent list
- market series
- summary
- manual archive API
- archive-current-source API
- archive-current-source does not create candidates
- sync archive optional
- scan capture optional
- `LIVE_EXECUTE` still rejected

### 12.1 Required negative tests

必须有测试确认：

- `archive-current-source` 不生成 candidates
- `archive-current-source` 不调用 `StrategyRunner`
- `sync-weather-markets archive=true` 不生成 candidates
- source-mode 不被 archive 修改
- `LIVE_EXECUTE` 仍被拒绝

## 13. 命名红线

PWB-04E 实现代码中不得出现以下方法或 endpoint 命名，除非是在安全测试的 forbidden list 或文档字符串中：

- `trade`
- `execute`
- `order`
- `cancel`
- `wallet`
- `private_key`
- `signature`
- `position`
- `portfolio`
- `balance`
- `pnl`
- `promote`
- `calibrate`
- `simulate`
- `auto_trade`
- `live_execute`

注意：

archive API 中不应出现 `simulate/backtest/promote/calibrate` 动词。

如果未来需要 backtest，应进入：

`PWB-05 — Real Calibration Data & Backtest Memory v0`

而不是在 PWB-04E 中扩展。

## 14. Audit / Warning 规则

Archive 失败时应返回 warning：

- `archive failed`
- `invalid snapshot payload`
- `current source returned no snapshots`
- `archive-current-source partial failure`
- `sync archive partial failure`
- `scan capture archive warning`

但不得：

- 切换 `execution_mode`
- 触发 fallback trading
- 自动重试无限次
- 启用 live execution

## 15. 验收阻断条件

出现以下任一情况，PWB-04E 不可冻结：

1. `archive-current-source` 调用 `StrategyRunner.run_once`
2. archive API 生成 `OpportunityCandidate`
3. archive API 触发 `Simulator`
4. archive API 修改 `execution_mode`
5. archive API 调用 `CalibrationService` 或 `ModelPromotionGate`
6. sync archive 触发 scan/simulation/execution
7. UI 出现 `Trade/Execute/Go Live/Wallet/Order` 按钮
8. `LIVE_EXECUTE` 不再被拒绝
9. 新增 wallet/private key/signing/order/cancel 代码
10. repository 中出现业务执行逻辑

## 16. PWB-04E Freeze 声明模板

PWB-04E freeze 时必须包含：

```text
PWB-04E is accepted as a read-only Market Snapshot Archive baseline.
It persists MarketSnapshot records into a time-indexed archive for later calibration and backtest preparation.
It does not generate signals, candidates, simulations, executions, trades, orders, model promotions, or calibration results.
Archive-current-source reads the current market source and archives snapshots only.
LIVE_EXECUTE remains rejected.
```
