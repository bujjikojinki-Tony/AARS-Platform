# Weather_Archive_Safety_Rules_v0

## 1. 文件目的

本文件定义：

`PWB-04F — Weather Forecast Archive v0`

的安全规则。

PWB-04F 只允许做：

- weather forecast archive
- weather evidence archive
- weather view archive
- weather archive summary
- market weather bundle query
- latest weather-side archive from existing repository state
- passive probability-build archive sidecar

不允许做：

- weather fetch from archive APIs
- strategy 触发
- candidate 生成
- simulation
- execution
- calibration
- model promotion
- trading
- wallet / order / cancel

## 2. 核心安全原则

### 2.1 Archive is passive

Weather Archive 是被动记录层：

```text
WeatherSourceRecord / EvidencePack / WeatherView
→ WeatherForecastArchiveService
→ SQLite
```

它不是：

- forecast generator
- probability engine
- signal generator
- candidate generator
- simulator
- executor
- promotion engine

### 2.2 Archive must not drive action

天气归档行为不得触发：

- `WeatherProbabilityProvider`
- `StrategyRunner`
- `StrategySignal`
- `OpportunityCandidate`
- `RiskManager`
- `Simulator`
- `Execution`
- `CalibrationService`
- `ModelPromotionGate`

唯一允许的旁路记录是：

- `PROBABILITY_BUILD_CAPTURE`
- `SCAN_CAPTURE`

但它们只能在已有流程完成或流程内部对象已产生后记录，不能反向驱动原流程。

### 2.3 Archive is evidence, not decision

Weather Archive 记录的是：

```text
当时系统看到或已经构造出的天气输入证据
```

它可以成为后续 calibration / backtest 的输入证据，但不能直接变成：

- 交易信号
- 候选生成依据
- 执行动作
- 校准结果
- 模型晋升依据

## 3. 允许能力

PWB-04F 允许以下能力。

### 3.1 Forecast archive

允许：

- `save_weather_forecast_archive_record`
- `POST /api/weather-archive/forecast`

用途：

- 保存某次 source-level forecast / observation 输入

### 3.2 Evidence archive

允许：

- `save_weather_evidence_archive_record`
- `POST /api/weather-archive/evidence`

用途：

- 保存 evidence pack 及其支持/反驳规则

### 3.3 Weather view archive

允许：

- `save_weather_view_archive_record`
- `POST /api/weather-archive/view`

用途：

- 保存结构化 weather view

### 3.4 Latest weather archive

允许：

`POST /api/weather-archive/latest/{market_id}`

行为：

```text
repository.get_latest_weather_view(market_id)
repository.get_latest_evidence_pack(market_id)
repository.list_weather_sources_for_market(market_id)
→ archive existing weather-side records only
```

强约束：

- 不触发新的 weather fetch
- 不调用 `WeatherProbabilityProvider`
- 不调用 `StrategyRunner`
- 不生成 `OpportunityCandidate`
- 不调用 `Simulator`
- 不调用 `Execution`

### 3.5 Probability build sidecar archive

允许在：

`WeatherProbabilityProvider.build_probability_view(...)`

之后做旁路记录：

- `WeatherViewArchiveRecord`
- `WeatherEvidenceArchiveRecord`
- `WeatherForecastArchiveRecord`

归档原因：

`PROBABILITY_BUILD_CAPTURE`

强约束：

- archive failure must not fail probability build
- archive must not change `model_probability`
- archive must not change `WeatherView`
- archive must not change downstream candidate count

### 3.6 Query weather archive

允许：

- `GET /api/weather-archive/summary`
- `GET /api/weather-archive/views`
- `GET /api/weather-archive/forecasts`
- `GET /api/weather-archive/evidence`
- `GET /api/weather-archive/market/{market_id}`

用途：

- History UI
- debug
- calibration preparation
- backtest preparation

## 4. 禁止能力

PWB-04F 禁止以下能力。

### 4.1 Weather fetch from archive

禁止 archive API 或 archive service 触发：

- `OpenMeteoSource.fetch`
- `NoaaPlaceholderSource.fetch`
- `WeatherSourceRegistry.select_sources`
- 任何新的 source pull

Archive 只能处理已有 repository state 或当前已在内存中的 weather-side objects。

### 4.2 Trading / execution

禁止任何：

- `trade`
- `execute`
- `live_execute`
- `buy`
- `sell`
- `place_order`
- `post_order`
- `cancel_order`
- `auto_trade`

### 4.3 Wallet / auth

禁止任何：

- `wallet`
- `private_key`
- `signature`
- `signing`
- `api_key`
- `api_secret`
- `passphrase`

### 4.4 Calibration / promotion

禁止任何：

- `calibrate`
- `backtest`
- `promote`
- `promotion`
- `CalibrationService`
- `ModelPromotionGate`

### 4.5 Strategy generation

Weather archive API 禁止调用：

- `StrategyRunner.run_once`
- `WeatherEdgeStrategy`
- `BinaryArbStrategy`
- `RiskManager.evaluate`
- `Simulator.simulate`

Weather archive API 只能调用：

- repository save/list/query methods
- `WeatherForecastArchiveService`

## 5. API 安全规则

### 5.1 允许 API

PWB-04F 只允许新增：

- `GET /api/weather-archive/summary`
- `GET /api/weather-archive/views`
- `GET /api/weather-archive/forecasts`
- `GET /api/weather-archive/evidence`
- `GET /api/weather-archive/market/{market_id}`
- `POST /api/weather-archive/view`
- `POST /api/weather-archive/forecast`
- `POST /api/weather-archive/evidence`
- `POST /api/weather-archive/latest/{market_id}`

### 5.2 禁止 API

禁止新增任何：

- `/api/weather-archive/fetch`
- `/api/weather-archive/execute`
- `/api/weather-archive/simulate`
- `/api/weather-archive/backtest`
- `/api/weather-archive/promote`
- `/api/weather-archive/trade`
- `/api/weather-archive/order`
- `/api/weather-archive/wallet`

### 5.3 archive-latest rule

`POST /api/weather-archive/latest/{market_id}` 必须只做：

```text
read latest weather-side records already stored
archive them
return archived records
```

不得做：

- weather fetch
- `WeatherProbabilityProvider.build_probability_view(...)`
- `StrategyRunner.run_once()`
- simulation
- execution

### 5.4 Manual archive rule

手动 weather archive API 只能接受 payload 并保存。

不得根据 payload 自动：

- 重新构造天气源
- 重新计算 probability
- 生成 signal
- 生成 candidate
- 触发 calibration
- 触发 simulation

## 6. Repository 安全规则

Repository methods 只能做 CRUD。

允许：

- `save_weather_forecast_archive_record`
- `save_weather_evidence_archive_record`
- `save_weather_view_archive_record`
- `list_weather_forecast_archive`
- `list_weather_evidence_archive`
- `list_weather_view_archive`
- `get_weather_archive_bundle`
- `get_weather_archive_summary`

禁止 repository 中出现：

- weather fetch
- strategy
- simulate
- execute
- trade
- calibrate
- promote

Repository 不做业务执行判断。

## 7. Archive Service 安全规则

`WeatherForecastArchiveService` 只能调用：

- repository save methods
- repository list/query methods

不得调用：

- `WeatherProbabilityProvider`
- `StrategyRunner`
- `Simulator`
- `RiskManager`
- `Execution`
- `CalibrationService`
- `ModelPromotionGate`

## 8. Probability Build Hook 安全规则

如果实现 `archive_weather_on_probability_build`：

### 8.1 允许

normal probability build completes
→ archive weather-side records as sidecar

### 8.2 禁止

- archive changes `model_probability`
- archive changes `WeatherView`
- archive changes candidate count
- archive changes scan result
- archive failure fails probability build

### 8.3 Failure rule

archive failure must be swallowed or converted into a warning path

probability build response remains based on the original accepted flow

## 9. Scan Safety Rules

如果 scan 间接触发 weather probability build：

### 9.1 允许

scan uses existing weather flow
→ optional passive weather archive sidecar runs

### 9.2 禁止

- archive-triggered scan
- archive-modified candidate count
- archive-modified risk state
- archive-triggered simulation
- archive-triggered execution

## 10. UI 安全规则

### 10.1 允许 UI

允许在 History / Evidence shell 展示：

- summary cards
- recent forecasts
- recent evidence
- recent weather views
- market weather bundle lookup
- archive latest weather view

### 10.2 禁止 UI

禁止出现：

- Trade
- Execute
- Simulate
- Backtest Now
- Promote Model
- Auto Calibrate
- Go Live
- Connect Wallet
- Place Order
- Cancel Order

### 10.3 Archive Latest button

按钮只能调用：

`POST /api/weather-archive/latest/{market_id}`

不得调用：

- weather fetch endpoints as a side effect
- scan endpoint
- settings mode endpoint
- simulation / execution endpoint

## 11. Test 安全规则

PWB-04F 测试必须覆盖：

- weather archive tables created
- archive service summary and bundle
- archive latest API
- archive latest does not create candidates
- archive latest does not fetch weather
- probability build archive optional
- scan candidate count unchanged
- `LIVE_EXECUTE` still rejected

### 11.1 Required negative tests

必须有测试确认：

- archive latest 不触发 weather fetch
- archive latest 不调用 `StrategyRunner`
- archive latest 不生成 candidates
- probability build archive 不改变 scan candidate count
- `LIVE_EXECUTE` 仍被拒绝

## 12. 命名红线

PWB-04F 实现代码中不得出现以下方法或 endpoint 命名，除非是在安全测试 forbidden list 或文档字符串中：

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
- `promote`
- `calibrate`
- `simulate`
- `auto_trade`
- `live_execute`

此外，archive API 中不应出现 `fetch weather` 类型行为。

## 13. Audit / Warning 规则

Archive 失败时应返回 warning 或安全空结果：

- latest weather view not found
- latest evidence pack not found
- probability-build weather archive failed safely
- archive latest partial failure

但不得：

- 改写 execution mode
- 触发 fallback trading
- 无限重试
- 启用 live execution

## 14. 验收阻断条件

出现以下任一情况，PWB-04F 不可冻结：

1. archive latest 触发 external weather fetch
2. weather archive API 调用 `WeatherProbabilityProvider` 来重新构造天气
3. weather archive API 调用 `StrategyRunner.run_once`
4. weather archive API 生成 `OpportunityCandidate`
5. weather archive API 触发 `Simulator`
6. weather archive API 修改 execution mode
7. probability-build archive 改变 `model_probability`
8. scan candidate count 因 weather archive 变化
9. UI 出现 Trade / Execute / Go Live / Wallet / Order 按钮
10. `LIVE_EXECUTE` 不再被拒绝

## 15. Freeze 声明模板

PWB-04F is accepted as a read-only Weather Forecast Archive baseline.
It persists time-indexed weather-side records for later calibration and backtest preparation.
It does not fetch external weather from archive APIs, and it does not generate signals, candidates, simulations, executions, trades, calibration results, or promotion decisions.
Archive-latest reads existing repository weather-side state and archives it only.
LIVE_EXECUTE remains rejected.
