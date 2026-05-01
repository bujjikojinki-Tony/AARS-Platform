# Market_Snapshot_Archive_v0

## 1. 架构定位

Market Snapshot Archive v0

它是一个 只读市场快照归档层，位于：

```text
MarketSource
  ↓
MarketSnapshot[]
  ↓
MarketSnapshotArchiveService
  ↓
market_snapshot_archive
```

它不参与交易，只负责保存系统在某个时间点看到的市场输入状态。

## 2. 它解决什么问题

PWB-04D 已经能发现和读取市场：

```text
Polymarket public market data
→ weather filter
→ MarketSnapshot[]
```

但如果不归档，每次读取都是瞬时的，后续无法回答：

1. 当时 YES / NO 价格是多少？
2. 当时 liquidity / spread 是多少？
3. 当时系统基于哪个 market input 产生候选？
4. 某个 probability run 对应的市场价格是什么？
5. outcome 出来后，如何回看当时的市场状态？
6. 后续做 calibration / backtest 时，用哪一帧市场数据？

PWB-04E 引入 archive 层，目的就是保留：

```text
当时系统看到的市场状态
```

## 3. 与 PWB 各轮关系

```text
PWB-01 — Execution Core
  scan / candidate / simulation / audit
PWB-02 — Weather Intelligence
  weather descriptor / evidence / weather view / probability view
PWB-03 — Probability Governance
  engine runs / comparison / calibration result / promotion decision
PWB-04C — App Factory Hardening
  create_app / isolated db / safe runtime config
PWB-04D — Polymarket Read-Only Connector
  read-only market source / weather market filter / MarketSnapshot
PWB-04E — Market Snapshot Archive
  time-indexed MarketSnapshot persistence
```

PWB-04E 不替换 PWB-01/02/03/04D，只增加一个归档层。

## 4. 核心对象

### 4.1 MarketSnapshot

PWB-01 已使用的运行时输入对象：

`MarketSnapshot`

包含：

- `market_id`
- `question`
- `yes_price`
- `no_price`
- `liquidity`
- `spread`
- `source`
- `fetched_at`

它代表：

```text
当前这一次 scan / source fetch 看到的市场状态
```

### 4.2 MarketSnapshotArchiveRecord

PWB-04E 新增对象：

`MarketSnapshotArchiveRecord`

它代表：

```text
已持久化的一帧市场快照
```

字段：

- `snapshot_archive_id`
- `market_id`
- `source`
- `question`
- `yes_price`
- `no_price`
- `liquidity`
- `spread`
- `fetched_at`
- `archived_at`
- `market_source_mode`
- `raw_ref`
- `metadata`
- `archive_reason`

### 4.3 MarketSnapshotSeries

表示某个 market 的时间序列：

`MarketSnapshotSeries`

字段：

- `market_id`
- `count`
- `first_archived_at`
- `last_archived_at`
- `snapshots`

用途：

查看同一个市场随时间的 `yes_price / no_price / spread / liquidity` 变化。

### 4.4 SnapshotArchiveSummary

表示归档层整体状态：

`SnapshotArchiveSummary`

字段：

- `total_snapshots`
- `unique_markets`
- `by_source`
- `by_archive_reason`
- `latest_archived_at`

用途：

- History 页面摘要
- 系统健康检查
- 后续回测数据量判断

## 5. Archive Reason

PWB-04E 接受四类归档原因：

- `SCAN_CAPTURE`
- `SYNC_CAPTURE`
- `MANUAL_CAPTURE`
- `PREVIEW_CAPTURE`

### 5.1 SCAN_CAPTURE

来自：

`POST /api/opportunities/scan`

含义：

本快照是 scan 输入市场的一部分。

注意：

- archive 发生在 scan 已经读取 market source 后
- archive 不驱动 scan
- archive 不改变 candidate 结果

### 5.2 SYNC_CAPTURE

来自：

`POST /api/polymarket/sync-weather-markets?archive=true`

含义：

本快照来自只读 market sync。

注意：

- sync archive 不触发 strategy
- sync archive 不触发 simulation
- sync archive 不触发 execution

### 5.3 MANUAL_CAPTURE

来自：

`POST /api/snapshots/archive`

含义：

用户或测试手动提交一个 `MarketSnapshot` 并归档。

用途：

- 测试
- 补录
- 调试
- 构造 calibration sample

### 5.4 PREVIEW_CAPTURE

来自：

`POST /api/snapshots/archive/current-source`

含义：

从当前 market source 读取快照并归档，但不运行 strategy。

用途：

- 市场采样
- source 检查
- UI preview 归档

## 6. SQLite 表

```sql
CREATE TABLE IF NOT EXISTS market_snapshot_archive (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  snapshot_archive_id TEXT NOT NULL,
  market_id TEXT NOT NULL,
  source TEXT NOT NULL,
  question TEXT NOT NULL,
  yes_price REAL NOT NULL,
  no_price REAL NOT NULL,
  liquidity REAL NOT NULL,
  spread REAL NOT NULL,
  fetched_at TEXT,
  archived_at TEXT NOT NULL,
  market_source_mode TEXT NOT NULL,
  raw_ref TEXT,
  metadata_json TEXT,
  archive_reason TEXT NOT NULL
);
```

索引：

```sql
CREATE INDEX IF NOT EXISTS idx_market_snapshot_archive_market_id
ON market_snapshot_archive(market_id);
CREATE INDEX IF NOT EXISTS idx_market_snapshot_archive_archived_at
ON market_snapshot_archive(archived_at);
CREATE INDEX IF NOT EXISTS idx_market_snapshot_archive_source
ON market_snapshot_archive(source);
CREATE INDEX IF NOT EXISTS idx_market_snapshot_archive_reason
ON market_snapshot_archive(archive_reason);
```

## 7. Archive Service

### 7.1 位置

`backend/archive/market_snapshot_archive_service.py`

### 7.2 职责

1. 接收 `MarketSnapshot`
2. 生成 `MarketSnapshotArchiveRecord`
3. 保存到 repository
4. 批量归档 snapshots
5. 查询 recent snapshots
6. 查询 market series
7. 查询 archive summary

### 7.3 强约束

ArchiveService 不允许调用：

- `StrategyRunner`
- `Simulator`
- `RiskManager`
- `Execution`
- `PromotionGate`

ArchiveService 只能做：

```text
MarketSnapshot → MarketSnapshotArchiveRecord → repository.save
```

## 8. API 设计

- `GET  /api/snapshots/archive`
- `GET  /api/snapshots/archive/summary`
- `GET  /api/snapshots/archive/market/{market_id}`
- `POST /api/snapshots/archive`
- `POST /api/snapshots/archive/current-source`

### 8.1 GET /api/snapshots/archive

用途：

查询最近归档快照。

可支持：

- `limit`
- `source`
- `archive_reason`

### 8.2 GET /api/snapshots/archive/summary

用途：

查询归档层摘要。

返回：

- `total_snapshots`
- `unique_markets`
- `by_source`
- `by_archive_reason`
- `latest_archived_at`

### 8.3 GET /api/snapshots/archive/market/{market_id}

用途：

查询单个 market 的快照时间序列。

### 8.4 POST /api/snapshots/archive

用途：

手动归档一个 `MarketSnapshot`。

这是人工/测试入口，不触发 scan。

### 8.5 POST /api/snapshots/archive/current-source

用途：

读取当前 market source 并归档 `MarketSnapshot[]`。

强约束：

- 不调用 `StrategyRunner`
- 不生成 `StrategySignal`
- 不生成 `OpportunityCandidate`
- 不调用 `Simulator`
- 不执行交易

## 9. Capture Hooks

### 9.1 Sync hook

在：

`POST /api/polymarket/sync-weather-markets`

增加可选：

```json
{
  "archive": true
}
```

当 `archive=true`：

```text
weather_records
→ MarketSnapshot[]
→ MarketSnapshotArchiveService.archive_snapshots(...)
→ archive_reason = SYNC_CAPTURE
```

不改变：

- connector health
- sync cache behavior
- execution mode
- strategy
- simulation

### 9.2 Scan hook

在：

`POST /api/opportunities/scan`

可选归档 scan 输入：

`archive_reason = SCAN_CAPTURE`

推荐实现方式：

- `StrategyRunner` 记录 `last_market_snapshots`
- `routes_opportunities` 在 `run_once` 后读取 `last_market_snapshots` 并归档

强约束：

- archive failure must not fail scan
- archive must not change candidates
- archive must not change risk status
- archive must not trigger simulation

## 10. UI 设计

新增组件：

当前实现位于 `weather-dashboard` 的 History 页 archive panel。

### 10.1 Summary Cards

展示：

- `total snapshots`
- `unique markets`
- `latest archived at`
- `source distribution`
- `archive reason distribution`

### 10.2 Recent Snapshot Table

展示：

- `market_id`
- `question`
- `yes_price`
- `no_price`
- `spread`
- `liquidity`
- `source`
- `archive_reason`
- `archived_at`

### 10.3 Market Series Lookup

输入：

`market_id`

展示：

- `count`
- `first_archived_at`
- `last_archived_at`
- `snapshots`

### 10.4 Actions

允许按钮：

- `Load Summary`
- `Load Recent Snapshots`
- `Archive Current Source`
- `Load Market Series`

禁止按钮：

- `Trade`
- `Execute`
- `Simulate`
- `Auto Trade`
- `Go Live`
- `Connect Wallet`
- `Place Order`
- `Cancel Order`

## 11. 与 Calibration 的关系

PWB-04E 不执行 calibration，但为 PWB-05 提供样本基础。

后续 calibration sample 可以由以下对象组成：

```text
MarketSnapshotArchiveRecord
+ ProbabilityView / ProbabilityEngineRun
+ MarketOutcome
```

用来回答：

- 当市场价格为 `0.52` 时，模型概率是多少？
- 模型概率是否比市场价格更接近最终 outcome？
- 某个 engine 在历史样本上的 Brier score 如何？

## 12. 与 Backtest Memory 的关系

PWB-04E 不做 backtest，但为 backtest memory 提供输入。

后续 backtest record 可引用：

- `snapshot_archive_id`
- `candidate_id`
- `simulation_id`
- `probability_comparison_id`
- `outcome_id`

这样系统能重建：

- 当时市场价格
- 当时模型概率
- 当时 signal edge
- 当时 risk gate
- 当时如果 simulation，会发生什么

## 13. 与 DEB / EMOS 的关系

真实 DEB / EMOS 需要历史样本。

PWB-04E 提供：

- market price history
- market spread history
- market liquidity history
- market source mode history

但 DEB / EMOS 还需要：

- forecast history
- actual weather outcomes
- source error history
- ensemble forecast samples

所以 PWB-04E 是必要但不充分条件。

## 14. 安全边界

PWB-04E 必须保持：

- read-only archive
- no wallet
- no private key
- no signing
- no order
- no cancel
- no position
- no live execution
- no auto trading

Archive 行为不得触发：

- `StrategyRunner`
- `Simulator`
- `RiskManager`
- `Execution`
- `PromotionGate`

唯一例外：

`SCAN_CAPTURE` 是 scan 后的旁路记录。

它不能改变 scan 行为。

## 15. 失败处理

Archive 失败时：

- return structured warning
- do not crash app unless manual archive payload is invalid
- do not change execution mode
- do not retry indefinitely
- do not trigger fallback trading behavior

在 scan hook 中：

`archive failure must not fail scan`

在 sync hook 中：

`archive failure should not prevent connector health from being recorded`

## 16. 验收基线

PWB-04E 通过条件：

1. `MarketSnapshotArchiveRecord` 可序列化。
2. `market_snapshot_archive` 表存在。
3. repository 可保存 / 查询 archive records。
4. service 可归档单个 snapshot。
5. service 可批量归档 snapshots。
6. recent snapshots 可查询。
7. market series 可查询。
8. summary 可统计 `total / unique / bySource / byReason`。
9. `archive-current-source` 可归档当前 source。
10. `archive-current-source` 不生成 candidates。
11. `sync archive=true` 可选写入 archive。
12. `scan capture` 可选写入 archive。
13. History UI 可查看 `summary / recent / series`。
14. `LIVE_EXECUTE` 仍被拒绝。

## 17. 不纳入 v0

- real backtest engine
- settlement resolver
- forecast archive
- weather outcome archive
- probability performance dashboard
- automatic model retraining
- DEB implementation
- EMOS implementation
- trading execution
- portfolio PnL

## 18. 推荐后续路径

PWB-04E 完成后，推荐进入：

`PWB-05 — Real Calibration Data & Backtest Memory v0`

或者如果还想继续稳数据层：

- `PWB-04F — Weather Forecast Archive v0`
- `PWB-04G — Outcome Resolver Read-Only v0`

建议顺序：

```text
PWB-04E Market Snapshot Archive
→ PWB-04F Weather Forecast Archive
→ PWB-04G Outcome Resolver Read-Only
→ PWB-05 Real Calibration Data & Backtest Memory
→ PWB-05A Real DEB Shadow
→ PWB-05B EMOS Evaluation
```
