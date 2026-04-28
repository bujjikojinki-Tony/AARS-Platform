# AARS Polymarket Weather Trading Test Report

版本：v0.3  
日期：2026-04-21  
关联文档：

- [AARS_Polymarket_Weather_Trading_Functional_Requirements.md](./AARS_Polymarket_Weather_Trading_Functional_Requirements.md)
- [AARS_Polymarket_Weather_Trading_Architecture.md](./AARS_Polymarket_Weather_Trading_Architecture.md)
- [AARS_Polymarket_Weather_Trading_Detailed_Design.md](./AARS_Polymarket_Weather_Trading_Detailed_Design.md)
- [AARS_Polymarket_Weather_Trading_Monitoring_Collection_And_Indicator_Governance.md](./AARS_Polymarket_Weather_Trading_Monitoring_Collection_And_Indicator_Governance.md)
- [AARS_Polymarket_Weather_Trading_Signal_Design.md](./AARS_Polymarket_Weather_Trading_Signal_Design.md)
- [AARS_Polymarket_Weather_Trading_Console_Development_Report.md](./AARS_Polymarket_Weather_Trading_Console_Development_Report.md)

---

## 1. 文档目的

本文档用于给出 AARS Polymarket Weather Trading Console 的测试验证方案、测试用例设计与当前验证结论。

与旧版“阶段性测试记录”相比，本版报告重点补齐：

1. 基于需求分析文档的功能回溯。
2. 基于架构设计文档的层级验证。
3. 基于详细设计与信号设计文档的数据契约验证。
4. 面向评审和验收的测试用例矩阵。

---

## 2. 测试范围

本报告覆盖以下系统范围：

- 市场发现与 Watchlist
- 实时盘口快照
- resolver 与 source contract
- weather adapter / forecast snapshot
- probability / comparison / decision
- XAI / dashboard / telegram
- authorization / approval / execution dry-run
- feature store / label store / validation
- unified status / monitoring / freshness gate

不在本轮范围内：

- 私钥签名与真实 live order placement
- 外部交易所真实成交验收
- 完整生产环境容量与灾备测试

---

## 3. 测试依据

### 3.1 需求依据

需求依据来自功能需求文档中的 FR-01 至 FR-19：

| 需求编号 | 主题 |
|---|---|
| FR-01 | 市场发现与 Watchlist |
| FR-02 | Polymarket 实时盘口采集 |
| FR-03 | Market Resolver |
| FR-04 | Weather Data Adapters |
| FR-05 | Probability Layer |
| FR-06 | Comparison Layer |
| FR-07 | Decision Layer |
| FR-08 | XAI Layer |
| FR-09 | Authorization Layer |
| FR-10 | Execution Layer |
| FR-11 | Dashboard |
| FR-12 | Telegram Console |
| FR-13 | Feature Store |
| FR-14 | Label Store |
| FR-15 | Training / Validation |
| FR-16 | Model Registry |
| FR-17 | Monitoring |
| FR-18 | Gate Stack External Contract / Automation Summary |
| FR-19 | Ops Alert Bridge / Queue Lifecycle |
| FR-20 | Top Parameter Surface |
| FR-21 | 上游数据流水线治理 |
| FR-22 | 监测采集层与异常发现 |
| Phase 21 | Contract / Registry / Gate Systematization |
| Phase 22 | Gate Stack External API / Automation Consumption |
| Phase 23 | Automation Runtime Gate Check |

### 3.2 架构依据

架构验证的核心依据包括：

- 实时决策闭环
- 证据论证闭环
- 训练验证闭环
- 八层业务架构边界

### 3.3 详细设计与信号契约依据

重点验证以下契约是否稳定且跨模块一致：

- `MarketSnapshot`
- `MarketRule`
- `ForecastSnapshot`
- `ProbabilityState`
- `ComparisonPoint`
- `TradeDecision`
- `AuthorizationState`
- `ExecutionIntent`
- `ExecutionResult`
- `TopParameterView`
- `monitoring_status.json`
- `unified_status.json`
- `gate_stack_api.json`
- `gate_stack_automation_summary.json`
- `gate_stack_ops_alerts.jsonl`
- `market_alert_event.v1`
- `market_anomaly_event.v1`
- `indicator_registry`
- `probability_mode / execution_constraint`
- `resolver source contract`

---

## 4. 测试策略

本系统采用四层测试策略：

| 层级 | 目标 | 主要手段 |
|---|---|---|
| L1 单元测试 | 验证单个函数、状态机、builder、formatter 正确性 | `pytest` |
| L2 模块集成测试 | 验证跨对象契约和关键模块协作 | `pytest` + JSON 样例 |
| L3 端到端链路验证 | 验证主链路输出文件与 UI/Telegram 消费一致性 | 脚本运行 + 手工检查 |
| L4 操作台手动验证 | 验证 dashboard/telegram 的 operator 体验与 block reason 可读性 | 手动操作验证 |

关键原则：

1. 优先验证 contract，不只验证页面是否能显示。
2. 优先验证降级与 blocker，不只验证 happy path。
3. 对 heuristic / manual advisory / dry-run / live_approved 必须分别覆盖。
4. 测试结果必须能回溯到 FR、架构层和设计对象。

---

## 5. 需求-架构-测试回溯矩阵

| 测试主题 | 需求编号 | 架构层 | 设计对象 / 契约 | 测试用例编号 |
|---|---|---|---|---|
| 市场搜索与 Watchlist | FR-01, FR-11 | 01_market_layer, presentation | `MarketSnapshot`, WatchlistProjection | TC-01 ~ TC-04 |
| 实时盘口采集 | FR-02 | 01_market_layer | `MarketSnapshot` | TC-05 ~ TC-06 |
| resolver 与 source contract | FR-03 | 02_resolver_layer | `MarketRule`, `ResolverSourceContract` | TC-07 ~ TC-10 |
| weather adapter / forecast snapshot | FR-04 | weather_data_adapters | `ForecastSnapshot` | TC-11 ~ TC-12 |
| probability contract | FR-05, FR-16 | 03_probability_layer | `ProbabilityState`, contract policy | TC-13 ~ TC-15 |
| comparison / history | FR-06 | 04_comparison_layer | `ComparisonPoint`, history outputs | TC-16 ~ TC-18 |
| decision / heuristic output | FR-07 | 05_decision_layer | `TradeDecision` | TC-19 ~ TC-20 |
| XAI / evidence closure | FR-08, FR-11 | 06_xai_layer, presentation | evidence bundle / operator closure | TC-21 ~ TC-22 |
| authorization gate | FR-09 | 07_authorization_layer | `AuthorizationState`, gate summary | TC-23 ~ TC-25 |
| execution gateway | FR-10 | 08_execution_layer | `ExecutionIntent`, `ExecutionResult` | TC-26 ~ TC-28 |
| dashboard operator surface | FR-11 | presentation | command/pipeline/markets/history/validation | TC-29 ~ TC-32 |
| telegram status / approval | FR-12 | notification channel | status card / signal card / approval flow | TC-33 ~ TC-35 |
| feature store / label store | FR-13, FR-14 | offline data layer | training samples / official labels | TC-36 ~ TC-38 |
| training / validation | FR-15, FR-16 | training_validation_layer | calibration/backtest/model validation | TC-39 ~ TC-41 |
| monitoring / unified status | FR-17 | monitoring | `monitoring_status.json`, `unified_status.json` | TC-42 ~ TC-45 |
| Phase 20 operator control surface | FR-08, FR-11, FR-12, FR-17 | presentation, notification channel, execution boundary | evidence chart / operator context / read-only exposure / mode badge | TC-46 ~ TC-52 |
| Phase 21 contract/gate hardening | FR-05, FR-10, FR-12, FR-17, Phase 21 | probability_layer, presentation, notification channel, execution_layer | `probability_contract.v1`, `execution_intent.v1`, unified status freshness gate, gateway contract gates | TC-53 ~ TC-62 |

---

## 6. 测试用例设计

### 6.1 市场发现与 Watchlist

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-01 | Gamma 搜索返回天气市场 | FR-01 | Gamma 或本地 fallback 可用 | 输入 `Shanghai temperature` 进行搜索 | 返回相关 market，或显示本地 fallback 结果 |
| TC-02 | Add to list 持久化 | FR-01 | 搜索结果存在 | 点击 `Add to list`，刷新页面 | 市场仍在 watchlist 中 |
| TC-03 | Remove 持久化隐藏 | FR-01 | watchlist 中已有市场 | 点击 `Remove`，刷新页面 | 市场不再显示 |
| TC-04 | Pin / Unpin / Recent 一致 | FR-01, FR-11 | 存在多个市场 | 依次 pin、unpin、切换 recent | 当前选中市场与 recent/pin 状态一致 |

### 6.2 实时盘口与 resolver

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-05 | realtime market snapshot 字段完整 | FR-02, 详细设计 4.1 | 市场 worker 已运行 | 检查 `market_realtime_simple.json` | 包含 `yes_price/no_price/favored_side/market_probability/updated_at` |
| TC-06 | 市场 stale 时 UI 不空白 | FR-02, FR-11 | 模拟 market worker 停止或旧快照 | 打开 dashboard | 页面显示 stale/degraded，而不是空白 |
| TC-07 | 上海温度市场 resolver 精确匹配 | FR-03 | 样例市场存在 | 运行 resolver | 输出 `official` + `exact_station` + `ZSPD` |
| TC-08 | 全球 hottest year 市场 family-level 解析 | FR-03 | 全球温度指数市场存在 | 运行 resolver | 输出 `proxy/family_exact`，不得伪装为 exact station |
| TC-09 | sea ice family 规则解析 | FR-03 | sea ice 市场存在 | 运行 resolver | 输出对应 official source contract |
| TC-10 | unmatched market 明确降级 | FR-03 | 输入不支持市场 | 运行 resolver 并查看 gate | `resolver_status=unmatched` 且 gate/UI 明确降级 |

### 6.3 forecast / probability / comparison

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-11 | forecast snapshot 不阻塞首屏 | FR-04, 设计原则 6 | 外部源可慢或不可用 | 打开 dashboard 首屏 | 页面仍能加载，forecast 部分显示可解释状态 |
| TC-12 | forecast mismatch 不被当成当前市场证据 | FR-04, FR-11 | 选择与 forecast 不同 market | 打开 Live Status | 显示 mismatch warning，不静默当成有效证据 |
| TC-13 | heuristic_not_calibrated 明确标注 | FR-05, Signal Design | validation 不达标 | 运行 probability shadow | `probability_mode=heuristic_not_calibrated` |
| TC-14 | candidate/live 阈值判断正确 | FR-05, FR-16 | 提供不同 validation report 样例 | 执行 contract policy 测试 | mode 与 `execution_constraint` 按阈值切换 |
| TC-15 | resolver unmatched 时不输出误导性 fair value | FR-05 | unmatched resolver | 运行 probability layer | 输出 blocked/unknown，而非伪装 fair value |
| TC-16 | comparison 计算 edge 与 band distance | FR-06 | market + forecast 快照存在 | 运行 comparison once | 输出 `edge/band_distance/comparison_status` |
| TC-17 | comparison history 去重与追加 | FR-06 | 连续多次运行比较 | 查看 `comparison_history.json` | 重复点不无限增长，新的状态变化可追加 |
| TC-18 | selected market 与 comparison row 对齐 | FR-06, FR-11 | 切换 selected market | 打开 dashboard | Data Alignment Audit 给出一致结果 |

### 6.4 decision / XAI / authorization / execution

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-19 | decision 输出 side / action_hint / reason | FR-07 | comparison 可用 | 运行 decision scaffold | 输出候选动作，不绕过 gate |
| TC-20 | heuristic decision 不伪装为 calibrated execution model | FR-07, Signal Design | heuristic mode | 查看 dashboard / signal | 显示 heuristic/manual advisory 语义 |
| TC-21 | XAI 证据闭环可回答五个核心问题 | FR-08 | dashboard 可运行 | 查看 Command tab | 可回答 market / odds / evidence / divergence / BOT 能否行动 |
| TC-22 | Evidence Chart 同轴展示关键证据 | FR-08, FR-11 | training sample 与 advisory audit 存在 | 打开 History tab | 同时展示 market odds、model、official value、approval marker |
| TC-23 | authorization gate 在数据不一致时阻断 | FR-09 | forecast/resolver/probability mismatch | 查看 gate 或调用 builder | blocker 被正确追加 |
| TC-24 | validation freshness / coverage 进入 gate | FR-09, FR-17 | freshness=warning 或 coverage=blocked | 查看 gate | `validation_freshness_*` / `label_coverage_*` 成为 blocker |
| TC-25 | resolver source 非 exact 时执行降级 | FR-09 | `family_only` 或 `fallback` | 查看 gate | 追加 `resolver_source_not_exact` |
| TC-26 | dashboard 写出 pending intent | FR-10 | gate 可写 intent | 点击 `Write Pending Intent` | 写入 intent preview 与 pending intent 文件 |
| TC-27 | gateway dry-run 不消费真实交易 | FR-10 | pending intent 存在 | 执行 dry-run-intent-file | 返回 risk/readiness 结果，无真实下单 |
| TC-28 | manual fill reconciliation 可追踪 | FR-10 | manual advisory 与 fill 样例存在 | 查看 reconciliation panel / report | 能看到 fill feedback 与 coverage check |

### 6.5 Dashboard / Telegram / Offline

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-29 | dashboard 主 tab 可正常打开 | FR-11 | Streamlit 可运行 | 打开 Command/Pipeline/Markets/History/Validation | 页面无 runtime error，主面板可见 |
| TC-30 | compact gate stack 摘要正确 | FR-11 | selected market 可用 | 查看 Command tab | alignment/probability/validation/coverage 状态一致 |
| TC-31 | unified status strip 与 execution gate 语义一致 | FR-11, FR-17 | unified status 已生成 | 对比 strip 与 gate | `can_bot_trade`、block reasons、constraint 一致 |
| TC-32 | dev-only 控件不应污染正式语义 | FR-11, Phase 20 | 非 dev mode 设计目标 | 查看 gate / mode badge | DEV harness 与正式 gate 语义分离 |
| TC-33 | Telegram `/status` 消费 unified status | FR-12, FR-17 | unified status 存在 | 调用 `/status` | 返回 overall/probability/execution/block reasons |
| TC-34 | Telegram approval 与 intent 绑定 | FR-12 | approval signal 与 intent 存在 | 审批 approve_small | approval 记录绑定到具体 intent_id |
| TC-35 | Telegram manual advisory acknowledgement 写入 audit | FR-12, Signal Design | manual advisory signal 存在 | 审批后查看 audit | 生成 operator_acknowledged_manual_advisory |
| TC-36 | training samples 记录 point-in-time features | FR-13 | comparison + probability 可运行 | 查看 `training_samples.jsonl` | 包含 market/probability/comparison/official label 字段 |
| TC-37 | official label store 能记录 labeled/unlabeled 状态 | FR-14 | official records/labels 可用 | 查看 label report | labeled_rows、ratio、family coverage 正确 |
| TC-38 | label coverage 缺口可见 | FR-14, FR-17 | labeled coverage 不足 | 查看 report / gate | `labeled_rows_below_min` 等 blocker 可见 |
| TC-39 | validation report 输出关键指标 | FR-15 | validation 脚本可运行 | 运行 model validation | 输出 brier/calibration/ROI/sample_count |
| TC-40 | stale validation 自动回退 probability_mode | FR-15, Signal Design | 过期 validation report | 执行 contract policy | 从 candidate/live 回退 |
| TC-41 | approved_for_live 仅影响概率层，不直接绕过 gateway | FR-15, FR-16 | `approved_for_live=true` | 查看 unified status/gateway | 仍需通过 readiness / approval / whitelist |
| TC-42 | monitoring status 正确聚合 worker 健康 | FR-17 | 各 worker 输出存在 | 构建 monitoring status | 返回 `healthy/warning/degraded` 与 counts |
| TC-43 | unified status 聚合 block reasons | FR-17 | monitoring/probability/execution/validation 存在 | 构建 unified status | 生成统一 block reason 列表 |
| TC-44 | validation freshness status 输出 aging/stale | FR-17 | validation report 存在或缺失 | 构建 freshness status | 产生 `healthy/warning/blocked/missing` |
| TC-45 | label coverage 按 family 给出覆盖状态 | FR-17 | training sample 存在 | 构建 label coverage report | family 维度 coverage 与 blockers 正确 |

### 6.6 Phase 20 Operator Control Surface Hardening

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-46 | Operator Market Context 写出并被 Telegram 默认读取 | FR-11, FR-12, Phase 20 | dashboard 已选中 market | 打开 dashboard 后调用 Telegram `/market` 无参数 | Telegram 默认 market 与 dashboard operator context 一致 |
| TC-47 | Operator Context Badge 可解释当前默认市场 | FR-11, Phase 20 | `operator_market_context.json` 存在 | 查看 Command tab | 显示 market_id、source、family、comparison、action、probability mode |
| TC-48 | Pipeline Sync 对齐摘要暴露错位 | FR-11, Phase 20 | selected / context / last sync 可构造 | 查看 Pipeline Sync 面板 | 可见 selected、Telegram default、last sync 是否 aligned/synced |
| TC-49 | Read-only Account Exposure 显示账户与市场 exposure | FR-10, FR-11, Phase 20 | `position_snapshot.json` 存在 | 查看 Command tab read-only account panel | 显示余额、总 exposure、当前市场 exposure，且不提供自动交易入口 |
| TC-50 | Exposure limit usage 与 readiness limits 联动 | FR-10, FR-17, Phase 20 | readiness report 有 exposure limits | 构造 within/near/over 样例 | usage 与提示分别显示 within_limit / near_limit / over_limit |
| TC-51 | Telegram `/market` 与 `/timeline` drill-down 可用 | FR-12, Phase 20 | latest dashboard rows 与 history 存在 | 调用 `/market [id]`、`/timeline [id]` | 返回市场摘要、snapshot refs、history timeline 与缺失数据提示 |
| TC-52 | Mode badge 与 dev-only 控件隔离 | FR-11, FR-17, Phase 20 | `operator_mode=dry_run_guarded` | 查看 unified status strip 与 gate | mode badge 显示 guarded，DEV harness 隐藏；仅 dev_local_harness 时显示 dev 控件 |

### 6.7 Phase 21 Contract / Registry / Gate Systematization

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-53 | ProbabilityState 内嵌 `probability_contract.v1` | FR-05, Phase 21 | 构造 ProbabilityState | 调用 schema / serialization 测试 | 输出包含 `contract_version` 与嵌套 `probability_contract` |
| TC-54 | Dashboard intent / Telegram signal 携带 ProbabilityContract | FR-10, FR-12, Phase 21 | execution gate 可生成 intent | 调用 intent 与 approval signal builder | `OrderIntent` 与 approval signal 均包含 `probability_contract` |
| TC-55 | Unified Status probability section 输出 contract | FR-17, Phase 21 | probability state 存在 | 构建 unified status | `probability.contract_version=probability_contract.v1`，并保留嵌套 contract |
| TC-56 | Gateway live gate 强制消费 ProbabilityContract | FR-10, Phase 21 | gateway `execution_enabled=true` | 分别输入 heuristic 与 live_approved contract | heuristic 被 `probability_contract_blocks_live_execution` 阻断；live_approved 通过 probability gate |
| TC-57 | Gateway freshness gate：`overall_status=degraded` 阻断执行 | FR-17, Phase 21 | 输入 unified status | 传入 degraded unified status 执行 gate | 返回 `unified_status_degraded` |
| TC-58 | Gateway freshness gate：worker `stale` 阻断执行 | FR-17, Phase 21 | 输入 monitoring workers | 构造一个 stale worker 执行 gate | 返回 `stale_worker` |
| TC-59 | Dashboard 写出的 ExecutionIntent 固化 contract 字段 | FR-10, FR-11, Phase 21 | execution gate 可写 intent | 调用 dashboard intent builder | 包含 `schema_version=execution_intent.v1`、`decision_ref`、`authorization_ref` |
| TC-60 | Telegram 生成并审批 intent 后回填 authorization_ref | FR-12, FR-10, Phase 21 | signal + approval callback 可用 | approve callback 后读取 pending intent | `authorization_ref=approval_id`，并保留 execution contract 字段 |
| TC-61 | Gateway 阻断不完整 ExecutionIntent contract | FR-10, Phase 21 | gateway risk gate 可调用 | 构造缺失 `decision_ref` 或 `authorization_ref` 的 intent | 返回 `execution_intent_contract_invalid` |
| TC-62 | 完整 ExecutionIntent 在 pending consume 路径可通过 contract gate | FR-10, FR-12, Phase 21 | pending intent + approval 记录存在 | consume first pending | approval 可消费，intent 进入 consumed 目录 |
| TC-63 | Contract/Gate skeleton 模块输出统一 gate 语义 | FR-10, FR-17, Phase 21 | `aars_weather_trading/gates` 可导入 | 调用 probability/freshness/compact gate stack | 返回稳定的 pass/blocked 与 block_reasons 汇总 |
| TC-64 | Band Scheme Registry 驱动 taxonomy 分类 | FR-03, Phase 21 | registry 可加载 | 分类 temperature/global index 问题 | `band_scheme` 与 registry 配置一致 |
| TC-65 | Source Registry profile 驱动 resolver contract 输出 | FR-03, Phase 21 | source profiles 可读取 | 构建 station/global/sea-ice resolver contract | `required_sources/source_match_grade/settlement_source_type` 与 profile 一致 |
| TC-66 | Resolver registry-first 改造后核心路径无回归 | FR-03, FR-04, Phase 21 | sample rulebook 可用 | 执行 resolver/live taxonomy/report 回归 | 关键 resolver 用例全部通过 |
| TC-67 | Resolver Gate 统一阻断语义 | FR-03, FR-17, Phase 21 | resolver gate 可调用 | 输入 unmatched + low confidence + family_only | 返回 `resolver_not_matched/resolver_confidence_low/resolver_source_not_exact` |
| TC-68 | Dashboard/Telegram compact gate stack 展示 resolver gate 一致 | FR-11, FR-12, Phase 21 | compact gate summary + market summary 可构建 | 分别渲染 dashboard compact panel 与 telegram market card | 两端均展示 `resolver_gate` 与一致 blocker 语义 |
| TC-69 | Unified Status 输出统一 gate_stack contract | FR-17, Phase 21 | unified status builder 可调用 | 构建 unified status | 输出 `gate_stack` 含 resolver/probability/freshness/authorization/execution gate 与 reasons |
| TC-70 | Dashboard/Telegram 优先消费 unified gate_stack | FR-11, FR-12, FR-17, Phase 21 | unified_status 中存在当前市场 gate_stack | 构建 compact summary 与 market summary | 两端均优先展示 unified gate_stack 结果 |
| TC-71 | Gateway 优先消费 unified gate_stack 前置阻断 | FR-10, FR-17, Phase 21 | unified_status 含 blocked gate | 执行 risk gate evaluate | 返回 gate_stack 首要 blocker（如 `resolver_not_matched`） |
| TC-72 | Telegram `/status` 自动补齐并展示 gate_stack contract | FR-12, FR-17, Phase 21 | unified/fallback status 可读取 | 调用 StatusAPI + status card 渲染 | `gate_stack` 存在且卡片显示 data/resolver/probability/freshness/authorization/execution |

### 6.8 Phase 22 Gate Stack External API / Automation Consumption（Batch 1）

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-73 | `build-unified-status` 自动输出 `gate_stack_api.v1` | FR-17, Phase 22 | comparison-engine status 输入齐备 | 执行 `build-unified-status` | 同时生成 `unified_status.json` 与 `gate_stack_api.json`，且 API `schema_version=gate_stack_api.v1` |
| TC-74 | Telegram `/status` 在 unified 缺失时可直接消费 gate stack API | FR-12, FR-17, Phase 22 | 仅有 `gate_stack_api.json` | 调用 `StatusAPI.load_latest_status()` | 返回统一状态对象并包含 gate_stack，`contracts.gate_stack_api_version=gate_stack_api.v1` |
| TC-75 | Gateway unified 缺失时回退消费 gate stack API 阻断执行 | FR-10, FR-17, Phase 22 | unified 缺失且 gate stack API 含 blocked gate | 调用 `_run_dry_run_for_intent` | risk reason 命中 gate stack blocker（如 `resolver_not_matched`），执行保持 blocked |
| TC-76 | gate stack API 输出多市场 `market_gate_views` 合同 | FR-11, FR-12, FR-17, Phase 22 | latest dashboard rows 含多个 market | 构建 gate stack API | 输出 `market_count`、`market_gate_views[*].market_id` 与每市场 gate 状态 |
| TC-77 | gate stack API 输出 automation hints | FR-10, FR-12, FR-17, Phase 22 | gate stack 含 blocker | 构建 gate stack API 并读取 payload | 含 `severity`、`recommended_operator_action`、`primary_block_reason` |
| TC-78 | Dashboard Compact Gate Stack 展示 gate source + severity/action | FR-11, FR-17, Phase 22 | 同时可构造 local / unified / gate API 路径 | 构建 compact summary | `gate_source` 正确（local/unified/api），并显示 severity/action |
| TC-79 | Automation consumer 输出 `gate_stack_automation_summary.v1` | FR-17, Phase 22 | `gate_stack_api.v1` 可读取 | 调用 automation summary builder | 输出 `can_execute/severity/recommended_operator_action/automation_signal` |
| TC-80 | `build-gate-stack-automation-summary` CLI 写出产物 | FR-17, Phase 22 | comparison-engine CLI 可运行 | 执行 CLI 命令并读取输出文件 | 生成 `gate_stack_automation_summary.json`，`schema_version=gate_stack_automation_summary.v1` |

### 6.9 Phase 23 Automation Runtime Gate Check（Batch 1）

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-81 | runtime check 的 fail-on-signal 退出码语义正确 | FR-17, Phase 23 | summary 可构造不同 signal | 调用 `resolve_exit_code` | `red/amber/never` 分别按策略返回 `0/2` |
| TC-82 | `run-gate-stack-automation-check` 在 red 阈值下返回非零 | FR-17, Phase 23 | unified status 与 dashboard rows 可读取 | 执行命令 `--fail-on-signal red` | 生成 API+summary 文件，且命令退出码为 `2` |
| TC-83 | runtime check 命中 red 时写入 ops alert bridge 事件 | FR-17, Phase 23 | runtime command 命中 red | 执行 runtime command 后读取 `gate_stack_ops_alerts.jsonl` | 存在 `gate_stack_ops_alert.v1` 事件且含 block reason/action |
| TC-84 | ops alert bridge 仅在 red + non-zero 时触发 | FR-17, Phase 23 | 构造 red/amber + exit_code 组合 | 调用 `should_emit_ops_alert` | 仅 `red + exit_code!=0` 返回 true |
| TC-85 | Telegram ops bridge 将 red alert 转为通知队列对象 | FR-12, FR-17, Phase 23 | `gate_stack_ops_alerts.jsonl` 存在 | 运行 bridge sync | 产出 `telegram_ops_notification.v1` 到 `telegram_ops_notifications.jsonl` |
| TC-86 | Telegram ops bridge 对同一 alert 去重 | FR-12, FR-17, Phase 23 | 重复 alert 输入 | 连续执行两次 sync | 第一次 queued>0，第二次 queued=0；state 记录 processed keys |
| TC-87 | Telegram ops queue lifecycle: dispatch 将 pending 标记 sent | FR-12, Phase 23 | `telegram_ops_notifications.jsonl` 含 pending | 调用 dispatch | `status=sent`，写入 `telegram_ops_delivery_log.jsonl` sent 事件 |
| TC-88 | Telegram ops queue lifecycle: ack 将 sent 标记 acked | FR-12, Phase 23 | queue 含 sent notification | 调用 ack | `status=acked`，写入 delivery log acked 事件 |
| TC-89 | Telegram bot `/opsqueue` 命令可分发 pending 队列并回写 sent | FR-12, Phase 23 | queue 含 pending 通知 | 调用 `opsqueue_handler` | 发送告警消息并回写 `status=sent` |
| TC-90 | Telegram bot `/opsack` 命令可确认已发送通知为 acked | FR-12, Phase 23 | queue 含 sent 通知 | 调用 `opsack_handler` | 目标通知回写 `status=acked` |
| TC-91 | 非管理员执行 `/opsqueue` 与 `/opsack` 被阻断 | FR-12, Phase 23 | 用户不在 admin 列表 | 调用 handler | 返回权限拒绝文案且不发生队列状态写入 |
| TC-92 | Dashboard compact gate stack 在 API 与 unified 同时存在时优先消费 API | FR-11, FR-17, Phase 24 | unified 与 gate stack API 同时存在且语义冲突 | 构建 compact gate summary | gate 状态与 blocker 以 API 为准，`gate_source=api` |
| TC-93 | Telegram `/market` compact gate stack 在 API 存在时优先消费 API | FR-12, FR-17, Phase 24 | unified 与 gate stack API 同时存在且语义冲突 | 调用 `MarketAPI.load_market_summary` | compact gate stack 以 API 为准，`source=api` |
| TC-94 | Gateway dry-run 风险门控在 unified 与 API 同时存在时优先消费 API | FR-10, FR-17, Phase 24 | unified 放行、API 阻断 | 调用 `_run_dry_run_for_intent` | risk reason 按 API blocker 返回，执行保持 blocked |
| TC-95 | Gateway 在 `gate_source=api` 时不重复执行 unified freshness 派生阻断 | FR-10, FR-17, Phase 24 | gate stack 已由 API 明确给出 pass，unified monitoring 为 stale | 调用 `RiskGateEngine.evaluate` | 风险判定不被 unified freshness 二次覆盖 |
| TC-96 | automation summary 透传 `gate_source` 字段 | FR-17, Phase 24 | gate stack API 可读取 | 构建 `gate_stack_automation_summary.v1` | 输出包含 `gate_source` 且值在统一枚举内 |
| TC-97 | contract consistency CLI 可产出 `gate_stack_contract_consistency.v1` | FR-17, Phase 24 | API 与 automation summary 产物存在 | 执行 `check-gate-stack-contract-consistency` | 生成一致性报告并输出 mismatch 统计 |
| TC-98 | Telegram runtime snapshot CLI 可导出 `telegram_gate_runtime_snapshot.v1` | FR-12, FR-17, Phase 24 | gate stack API/unified 可读取 | 执行 `weather-telegram-runtime-snapshot` | 生成快照且包含 `gate_source` 与 `source_schema_version` |
| TC-99 | Gateway runtime snapshot CLI 可导出 `gateway_gate_runtime_snapshot.v1` | FR-10, FR-17, Phase 24 | gate stack API 可读取 | 执行 `export-gate-runtime-snapshot` | 生成快照且 `gate_source=api` |
| TC-100 | consistency report 包含 schema 分级与 fallback 统计 | FR-17, Phase 24 | API/summary/runtime snapshots 可读取 | 构建 consistency report | 输出 `schema_health` 与 `fallback_stats`，并给出 issue_count |
| TC-101 | consistency report 输出 mismatch 分桶统计 | FR-17, Phase 24 | 构造多类 mismatch | 构建 consistency report | `mismatch_buckets` 输出 `schema/source/reason/other` 分桶计数 |
| TC-102 | realtime worker 每轮写出 consistency trend artifact | FR-17, Phase 24 | realtime worker 可运行 | 执行 `run_gate_stack_automation_realtime.py` 单轮 | 生成 `gate_stack_contract_consistency_trend.v1` 并记录 cycle 样本 |
| TC-103 | consistency trend 可累计 mismatch 周期与分桶总量 | FR-17, Phase 24 | 连续多轮 consistency 输入 | 调用 trend 更新逻辑 | `total_cycles`、`mismatch_cycles`、`bucket_totals` 按预期累计 |

### 6.10 Phase 25 Automation Ops Contract Closure

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-104 | `gate_stack_ops_alert.v1` 包含 cooldown / suppression / dedupe 字段 | FR-17, Phase 25 | ops alert builder 可调用 | 构建 alert contract | 输出 `dedupe_key`、`delivery_state`、`suppressed_count`、`cooldown_until`、`last_sent_at` |
| TC-105 | 同 market + same reason 在 cooldown 内进入 suppressed | FR-17, Phase 25 | 同一 alert 连续触发 | 连续执行 alert emission | 首次 `sent`，后续 `suppressed` |
| TC-106 | `/opsqueue` 与 `/opsack` 幂等 | FR-12, FR-17, Phase 25 | queue 中存在 pending/sent | 重复调用 queue/ack handler | 状态不重复推进，重复调用无副作用 |
| TC-107 | runtime / queue / telegram 三端字段一致 | FR-12, FR-17, Phase 25 | alert、queue、delivery log 可读 | 比对三端记录 | `market_id`、`primary_block_reason`、`delivery_state`、`dedupe_key` 一致 |
| TC-108 | deterministic exit code matrix 与 automation signal 一致 | FR-17, Phase 25 | runtime check 可运行 | 构造 red/amber/green 场景 | 退出码与文档矩阵一致，且可回归 |

### 6.11 Phase 26 Promotion Policy Auto-Closure

| 用例编号 | 用例名称 | 依据 | 前置条件 | 测试步骤 | 预期结果 |
|---|---|---|---|---|---|
| TC-109 | stale validation 自动降级 probability_mode | FR-05, FR-17, Phase 26 | validation freshness report stale | 执行 promotion policy | 从 live/candidate 回退到 shadow/heuristic |
| TC-110 | label coverage 不足自动回落 execution_constraint | FR-05, FR-17, Phase 26 | label coverage 低于阈值 | 执行 promotion policy | `execution_constraint` 回到 `manual_advisory_only` 或 `dry_run_only` |
| TC-111 | approved_for_live=true 但 resolver precision 不足仍阻断 live | FR-03, FR-17, Phase 26 | resolver/source precision 低 | 执行 promotion policy 与 gate | 不允许 live，保留 blocker 理由 |
| TC-112 | promotion_reason / demotion_reason 在三端一致显示 | FR-12, FR-17, Phase 26 | policy 输出可读 | 查看 dashboard / telegram / gateway | 三端展示同一 reason 字段和语义 |
| TC-113 | gate stack 自动消费 promotion 结果而不自行推断 | FR-10, FR-17, Phase 26 | policy 输出存在 | 调用 gate stack 评估 | gate 只消费 policy 输出，不额外推断晋级逻辑 |
| TC-114 | 历史回放同输入同输出 | FR-17, Phase 26 | 历史输入记录可读 | 重放相同 validation/resolver inputs | 结果与原始 policy 输出一致 |
| TC-115 | 比较历史与 history relationship panel 复用同一份 TopParameterView | FR-11, FR-17, Phase 24.5 | comparison history 含 `top_parameter_view` | 打开 history relationship panel 并检查 summary | 历史图顶部摘要显示与历史点一致的 `market_id`、`forecast_value`、`source_match_grade`、`can_execute` |
| TC-116 | comparison table / evidence chart / timeline 复用同一份 TopParameterView | FR-11, FR-17, Phase 24.5 | 比较表、证据图和时间线可读取历史点或顶层视图 | 打开 comparison table、market evidence chart、timeline panel | 三个输出都展示一致的 `market_family`、`forecast_value`、`source_match_grade`、`can_execute` |
| TC-117 | 同一 market_id 的 market / forecast / comparison 共享同一事实链 | FR-20, Phase 24.5 | market snapshot、forecast snapshot、comparison point 均存在 | 对比三份快照中的 source ref 与 market_id | 三者可回指同一条事实链，不能出现互相矛盾的当前事实 |
| TC-118 | TopParameterView 只做聚合不改写事实 | FR-20, Phase 24.5 | 顶层视图与原始快照同时存在 | 对比 TopParameterView 与上游 market / rule / forecast / comparison 字段 | 顶层字段应能追溯到上游，且不会把空字段伪装成事实 |
| TC-119 | 市场研究 / 录入输出唯一主快照 | FR-21, Phase 24.5 | Gamma / watchlist / 人工选择输入可用 | 检查 market snapshot 写出与市场选择结果 | 只存在一个可追溯主快照，且优先保留有价格市场 |
| TC-120 | resolver 输出回指唯一 market_id | FR-21, Phase 24.5 | market snapshot 与规则库存在 | 运行 resolver 并对比结果 | resolver / source / band 均回指同一 `market_id` |
| TC-121 | forecast / observation 与 target_date 和 station mapping 对齐 | FR-21, Phase 24.5 | market rule 与站点映射存在 | 生成 forecast / observation 快照 | 目标日期、站点、source_mode 可对齐且可追溯 |
| TC-122 | comparison / probability 只做派生不改写事实 | FR-21, Phase 24.5 | 上游四类快照存在 | 生成 comparison / probability / TopParameterView | market_probability / fair_value / edge 可回指上游，不产生新事实 |
| TC-123 | 展示层只消费统一事实链 | FR-21, Phase 24.5 | Dashboard / Telegram / Gateway 视图可构建 | 查看三端首屏 | 三端只消费同一条链路，空字段折叠，非适用字段隐藏 |
| TC-124 | 上游流水线各阶段责任边界清晰 | FR-21, Phase 24.5 | market / resolver / forecast / comparison / display 均有产物 | 对照责任归属表与对应输出 | 每段只承担自己的输入输出，不跨层改写事实 |
| TC-125 | 单市场 observation alert 可回放且 contract 可追溯 | FR-22 | ObservationSnapshot / MarketRule / ProbabilityState 可用 | 检查 `market_alert_event.v1` 输出 | observation shock / forecast divergence / reaction gap 可回指上游快照与阈值版本 |
| TC-126 | family anomaly 可按 family / 日期 / 变量聚合 | FR-22 | 同 family 的 market snapshots 与 comparison points 可用 | 执行 family scan | 输出 price velocity / edge dislocation / evidence mismatch / microstructure stress / peer anomaly |
| TC-127 | 监测采集结果不得改写 gate 语义 | FR-22, FR-18 | alert / anomaly 产物可用 | 对比 alert 输出与 gate_stack_api | 监测产物只能消费 gate 语义，不能替代 authorization / execution gate |
| TC-128 | indicator registry 与 threshold policy 可版本化加载 | FR-22, Phase 27 | registry JSON 可读 | 加载 indicator registry 与 threshold policy | `indicator_name` / `formula` / `policy_version` 可解析且可校验 |
| TC-129 | observation alert 在 source mismatch 时自动降级 | FR-22, Phase 27 | `source_match_grade != exact_station` | 构造非 exact station 输入 | 预警只能输出 review-only / advisory，不得升级为强告警 |
| TC-130 | family scanner 可输出可回放的 anomaly report | FR-22, Phase 27 | 同 family 输入可用 | 执行 family scan | 输出 `market_anomaly_event.v1` 与 `family_scan_report.v1`，并可回指输入快照 |
| TC-131 | monitoring 输出在 dashboard / telegram 仅消费不重算 | FR-22, Phase 27 | monitoring 事件可读 | 打开 dashboard / telegram monitoring 入口 | 页面只显示指标产物，不在展示层重算指标 |
| TC-132 | monitoring 输出与 gate 语义边界清晰 | FR-22, FR-18, Phase 27 | alert / anomaly / gate_stack_api 都可读 | 对比 monitoring 事件与 gate contract | monitoring 只能描述异常，不得替代 gate 判定 |
| TC-133 | observation alert 脚本可基于当前 outputs 生成事件 | FR-22, Phase 27 | 当前 observation / market / forecast outputs 可用 | 执行 `run_observation_alert_once.py` | 输出 `market_alert_event.v1`，并写入 `market_alert_events/` |
| TC-134 | family scan 脚本可基于当前 outputs 生成报告 | FR-22, Phase 27 | current dashboard rows / comparison history / probability states 可用 | 执行 `run_family_anomaly_scan_once.py` | 输出 `family_scan_report.v1` 与 `market_anomaly_event.v1`，并写入对应 outputs |
| TC-135 | threshold cross 支持显式 numeric threshold | FR-22, Phase 27 | observation / previous observation / threshold policy 可用 | 构造 threshold_cross_value 与前后观测值 | `threshold_cross_event`、`threshold_cross_direction` 与 `threshold_cross_value` 可回放 |
| TC-136 | dashboard monitoring overview 可直接消费最新 alert / anomaly / family scan | FR-22, Phase 27 | monitoring outputs 可用 | 打开 dashboard Evidence 页面 | `Monitoring Signals` 面板显示最新告警、家族扫描与异常摘要 |
| TC-137 | Telegram `/monitoring` 与导航按钮可消费 monitoring outputs | FR-22, Phase 27 | monitoring outputs 可用 | 发送 `/monitoring` 或点导航按钮 | Telegram 输出 monitoring summary 卡片，不重算监测指标 |
| TC-138 | monitoring trend summary 可按最新 outputs 汇总 severity / anomaly 分布 | FR-22, Phase 27 | monitoring outputs 可用 | 打开 dashboard / Telegram monitoring 入口 | trend summary 输出最近窗口的 severity counts、recent alerts、recent anomalies |
| TC-139 | source / measurement registry 可在 rules-research 侧加载并通过校验 | FR-21, Phase 27.1 | registry 文件已落盘 | 执行 `validate-registry` / registry loader 测试 | `source_policy` 与 `measurement_registry` 可读取，`validate-registry` 输出 `ok=true` |
| TC-140 | source / measurement registry 可在 comparison-engine 侧加载并通过校验 | FR-21, Phase 27.1 | registry 文件已落盘 | 执行 `validate-registry` / registry loader 测试 | `source_policy` 与 `measurement_registry` 可读取，`validate-registry` 输出 `ok=true` |
| TC-141 | resolver contract 输出 policy refs | FR-21, Phase 27.1 | rules-research registry 可读取 | 构造 station / climate contract | contract 返回 `source_policy_ref`、`unit_policy_ref`、`precision_policy_ref`、`rounding_policy_ref`、`band_mapping_policy_ref` |
| TC-142 | ResolvedMarketRule 输出 policy refs | FR-21, Phase 27.1 | resolver report 可构造 | 生成 Shanghai / precipitation / wind / sea ice / global index resolved rule | resolved rule 输出与 family/variable 对应的 policy refs |
| TC-143 | monitoring freshness 由 source policy registry 驱动 | FR-21, Phase 27.1 | source policy registry 可读取 | 构造 custom source policy registry 并运行 monitoring status CLI | `stale_after_seconds` 随 registry 变化，monitoring status 使用 registry 阈值而非硬编码常量 |
| TC-144 | TopParameterView 可消费 canonical/display measurement hooks | FR-21, Phase 27.1 | measurement registry 与 top parameter builder 可用 | 构造 raw measurement 输入并调用 canonical hook | `get_canonical_value` / `get_display_value` 可返回规范化值，`TopParameterView` 保持可读输出 |
| TC-145 | Dashboard monitoring signals 展示 source policy fallback 概要 | FR-21, Phase 27.1 | source policy status 含 sources / fallback_policy | 渲染 monitoring_signals_panel | `Fallback Policies` 可见，且按 source / priority / fallback_policy 摘要展示 |
| TC-146 | Telegram top parameter / monitoring 卡片展示 policy-aware 只读字段 | FR-21, Phase 27.1 | top parameter view 含 canonical unit / source priority / fallback mode | 渲染 status / market / monitoring 卡片 | 卡片显示 `Canonical Unit`、`Source Priority`、`Fallback Mode` 和 `Fallback Policies`，且不做本地转换 |
| TC-147 | rules-research forecast snapshot 输出 normalization metadata | FR-21, Phase 27.2 | forecast stub / poller 可用 | 生成 forecast snapshot / poller latest payload | 输出 `raw_value` / `canonical_value` / `display_value` / `policy refs` / `normalization_version` |
| TC-148 | forecast extractor 与 poller 均通过 registry-first normalization | FR-21, Phase 27.2 | measurement registry 可读 | 运行 extractor 与 poller 回归 | `normalize_measurement`、`get_canonical_value`、`get_display_value` 与 `ForecastPoller.latest` 结果一致 |

---

## 7. 当前自动化验证结果

### 7.1 已记录自动化测试基线

| 模块 | 结果 |
|---|---|
| `weather-comparison-engine` | `42 passed` |
| `weather-dashboard` | `48 passed` |
| `weather-execution-gateway` | `35 passed` |
| `weather-telegram-console` | `13 passed` |
| `weather-rules-research` | `88 passed` |
| `polymarket-weather-ingest` | `14 passed` |

### 7.2 本轮补充回归

本轮围绕 dashboard 稳定性、Phase 20 控制面完成、Phase 21 contract 收口，以及 Phase 22 gate stack API baseline 落地执行了针对性回归：

```bash
pytest weather-dashboard/tests/test_execution_gate_panel.py
pytest weather-dashboard/tests/test_data_alignment_panel.py
pytest weather-dashboard/tests/test_market_evidence_chart.py
pytest weather-dashboard/tests/test_compact_gate_stack_panel.py
pytest weather-dashboard/tests/test_operator_context_badge.py
pytest weather-dashboard/tests/test_pipeline_sync_context.py
pytest weather-dashboard/tests/test_read_only_account_panel.py
pytest weather-dashboard/tests/test_unified_status_strip.py
pytest weather-telegram-console/tests/test_market_api.py
pytest weather-telegram-console/tests/test_market_card.py
pytest weather-telegram-console/tests/test_timeline_card.py
pytest weather-telegram-console/tests/test_market_handler.py
pytest weather-telegram-console/tests/test_timeline_handler.py
pytest weather-telegram-console/tests/test_status_card.py
pytest weather-comparison-engine/tests/test_unified_status_builder.py
pytest weather-comparison-engine/tests/test_gate_stack_api_builder.py
pytest weather-comparison-engine/tests/test_probability_contract_schema.py
pytest weather-comparison-engine/tests/test_probability_contract_policy.py
pytest weather-comparison-engine/tests/test_shadow_probability_engine.py
pytest weather-execution-gateway/tests/test_gates.py
pytest weather-execution-gateway/tests/test_position_exposure.py
pytest weather-execution-gateway/tests/test_clob_execution.py
pytest weather-execution-gateway/tests/test_planner.py
pytest weather-execution-gateway/tests/test_pending_intents.py
pytest weather-execution-gateway/tests/test_contract_gates.py
pytest weather-telegram-console/tests/test_intent_writer.py
pytest weather-telegram-console/tests/test_approval_handler.py
pytest weather-telegram-console/tests/test_status_handler.py
cd weather-rules-research && pytest tests/test_registry_contracts.py tests/test_live_market_resolver.py tests/test_resolver_contract_registry.py tests/test_market_resolution_registry.py tests/test_resolver_report.py
```

结果：

- Phase 20 dashboard operator surface targeted regression：`22 passed`
- Phase 20 Telegram market/timeline targeted regression：`11 passed`
- Unified status mode contract targeted regression：`2 passed`
- Phase 21 contract/gate hardening targeted regression：comparison-engine `10 passed`, gateway `19 passed`, dashboard `11 passed`, telegram `8 passed`
- Phase 21 resolver registry-first targeted regression：weather-rules-research `25 passed`
- Phase 21 resolver gate targeted regression：gateway contract gates `12 passed`
- Phase 21 resolver gate multi-surface regression：dashboard `12 passed`, telegram market surface `7 passed`
- Phase 21 unified gate stack contract regression：comparison-engine `2 passed`, dashboard `13 passed`, telegram market surface `8 passed`
- Phase 21 unified gate stack gateway-consumption regression：gateway gates `13 passed`
- Phase 21 unified gate stack status-surface regression：telegram status surface `3 passed`
- Phase 21 收口验收结论：contract/registry/gate 三件套目标用例（TC-53 ~ TC-72）已通过并完成基线固化
- Phase 22 gate stack API baseline regression：comparison-engine `4 passed`, telegram status `4 passed`, gateway risk/execution `13 passed`
- Phase 22 Batch 1 验收结论：外部稳定 gate contract 目标用例（TC-73 ~ TC-75）已通过
- Phase 22 Batch 2 regression：comparison-engine `5 passed`, dashboard compact gate `3 passed`, telegram status `5 passed`, gateway risk/execution `12 passed`
- Phase 22 Batch 3 regression：comparison-engine automation consumer `7 passed`
- Phase 22 收口验收结论：Batch 1 + Batch 2 + Batch 3（TC-73 ~ TC-80）已通过，Phase 22 完成
- Phase 23 Batch 1 regression：comparison-engine runtime check `9 passed`
- Phase 23 阶段结论：runtime gate check（TC-81 ~ TC-82）已通过
- Phase 23 Batch 2 regression：comparison-engine runtime worker/alert bridge `10 passed`
- Phase 23 进度结论：Batch 1 + Batch 2（TC-81 ~ TC-84）已通过
- Phase 23 Batch 3 regression：telegram-console ops bridge `7 passed`
- Phase 23 进度结论：Batch 1 + Batch 2 + Batch 3（TC-81 ~ TC-86）已通过
- Phase 23 Batch 4 regression：telegram-console lifecycle bridge `9 passed`
- Phase 23 进度结论：Batch 1 + Batch 2 + Batch 3 + Batch 4（TC-81 ~ TC-88）已通过
- Phase 23 Batch 5 regression：telegram-console bot ops handlers `8 passed`
- Phase 23 进度结论：Batch 1 + Batch 2 + Batch 3 + Batch 4 + Batch 5（TC-81 ~ TC-91）已通过
- Phase 24 Batch 1 regression：dashboard compact gate `4 passed`，telegram market surface `9 passed`，gateway risk/exposure `13 passed`
- Phase 24 进度结论：API-first single-source hardening（TC-92 ~ TC-94）已通过
- Phase 24 Batch 2+3 regression：comparison-engine automation/consistency `9 passed`，gateway risk/exposure `14 passed`
- Phase 24 进度结论：single-source hardening + source traceability + consistency check（TC-92 ~ TC-97）已通过
- Phase 24 Batch 4 regression：comparison-engine automation/consistency `10 passed`，telegram runtime snapshot `4 passed`，gateway risk/exposure `15 passed`
- Phase 24 进度结论：cross-process runtime consistency + schema/fallback observability（TC-92 ~ TC-100）已通过
- Phase 24 Batch 5 regression：comparison-engine automation/consistency/trend `11 passed`，telegram runtime snapshot/status `4 passed`，gateway risk/exposure `15 passed`
- Phase 24 进度结论：periodic drift monitoring + mismatch buckets/trend aggregation（TC-92 ~ TC-103）已通过
- Phase 25 Batch 1 regression：comparison-engine alert contract `11 passed`，telegram ops bridge `7 passed`
- Phase 25 进度结论：ops alert contract expansion + cooldown / suppression + queue lifecycle（TC-104 ~ TC-106）已通过
- Phase 25 Batch 2 regression：comparison-engine exit code matrix `11 passed`
- Phase 25 进度结论：deterministic exit code matrix + summary contract exposure（TC-108）已通过
- Phase 25 Batch 3 regression：telegram ops bridge / dispatcher `7 passed`
- Phase 25 进度结论：queue consistency summary + delivery log alignment（TC-107）已通过
- Phase 25 Batch 4 regression：telegram ops queue status CLI `8 passed`
- Phase 25 进度结论：queue status CLI + ops queue observability 已通过
- Phase 25 Batch 5 regression：dashboard ops panel `6 passed`
- Phase 25 进度结论：dashboard ops alert / queue summary panel 已通过
- Phase 26 Batch 1 regression：comparison-engine promotion policy / unified status `11 passed`，dashboard top parameter / model validation `8 passed`
- Phase 26 进度结论：promotion policy auto-closure 首批收口已通过，validation freshness / label coverage / resolver precision blocker 进入统一 contract
- Phase 26 Batch 2 regression：telegram status / market `11 passed`，gateway runtime snapshot `1 passed`
- Phase 26 进度结论：promotion state 已贯通 Telegram / gateway read-only 输出，三端 operator 语义继续收口
- Phase 26 Batch 3 regression：dashboard compact gate / trade decision / model validation `7 passed`
- Phase 26 进度结论：promotion state 已贯通 dashboard gate / trade / validation 摘要，三端 operator 语义对齐进一步收口
- Phase 26 Batch 4 regression：dashboard execution gate / probability shadow / operator focus `13 passed`
- Phase 26 进度结论：promotion state 已贯通 execution / probability / operator focus 摘要，dashboard operator surface 收口更完整
- Phase 26 Batch 5 regression：dashboard unified status strip / compact gate / operator focus `6 passed`
- Phase 26 进度结论：promotion state 已贯通 unified status strip 首屏摘要，三端 operator 语义进一步统一
- Phase 24.5 进度结论：TopParameterView 首屏合同、空字段折叠、family-specific 标签与 comparison history reuse 已通过

### 7.3 当前已覆盖的代表性自动化测试

| 测试文件 | 对应用例/主题 |
|---|---|
| `weather-rules-research/tests/test_resolver_contract_registry.py` | TC-07 ~ TC-10 |
| `weather-comparison-engine/tests/test_probability_contract_policy.py` | TC-13 ~ TC-15, TC-40 |
| `weather-dashboard/tests/test_top_parameter_ribbon.py` | TC-115 ~ TC-124 |
| `weather-comparison-engine/tests/test_probability_contract_schema.py` | TC-53 |
| `weather-comparison-engine/tests/test_unified_status_builder.py` | TC-41 ~ TC-43, TC-55 |
| `weather-comparison-engine/tests/test_gate_stack_api_builder.py` | TC-73, TC-76, TC-77 |
| `weather-comparison-engine/tests/test_gate_stack_automation_consumer.py` | TC-79, TC-80, TC-81, TC-82, TC-83, TC-84 |
| `weather-comparison-engine/tests/test_validation_quality_reports.py` | TC-44 ~ TC-45 |
| `weather-dashboard/tests/test_execution_gate_panel.py` | TC-23 ~ TC-28, TC-54, TC-59 |
| `weather-dashboard/tests/test_data_alignment_panel.py` | TC-18, TC-24, TC-25 |
| `weather-dashboard/tests/test_compact_gate_stack_panel.py` | TC-30, TC-68, TC-70, TC-78 |
| `weather-dashboard/tests/test_market_evidence_chart.py` | TC-22 |
| `weather-dashboard/tests/test_operator_context_badge.py` | TC-46 ~ TC-47 |
| `weather-dashboard/tests/test_pipeline_sync_context.py` | TC-48 |
| `weather-dashboard/tests/test_read_only_account_panel.py` | TC-49 ~ TC-50 |
| `weather-dashboard/tests/test_resolver_status_panel.py` | TC-07 ~ TC-10 |
| `weather-dashboard/tests/test_unified_status_strip.py` | TC-31, TC-52 |
| `weather-telegram-console/tests/test_status_card.py` | TC-33 |
| `weather-telegram-console/tests/test_status_handler.py` | TC-33 |
| `weather-telegram-console/tests/test_market_api.py` | TC-46, TC-51 |
| `weather-telegram-console/tests/test_market_card.py` | TC-51 |
| `weather-telegram-console/tests/test_timeline_card.py` | TC-51 |
| `weather-telegram-console/tests/test_market_handler.py` | TC-51 |
| `weather-telegram-console/tests/test_timeline_handler.py` | TC-51 |
| `weather-execution-gateway/tests/test_gates.py` | TC-56 ~ TC-58, TC-61, TC-71 |
| `weather-execution-gateway/tests/test_pending_intents.py` | TC-62 |
| `weather-execution-gateway/tests/test_contract_gates.py` | TC-63, TC-67 |
| `weather-rules-research/tests/test_registry_contracts.py` | TC-64 ~ TC-65 |
| `weather-rules-research/tests/test_live_market_resolver.py` | TC-66 |
| `weather-rules-research/tests/test_resolver_contract_registry.py` | TC-65 ~ TC-66 |
| `weather-rules-research/tests/test_market_resolution_registry.py` | TC-66 |
| `weather-rules-research/tests/test_resolver_report.py` | TC-66 |
| `weather-telegram-console/tests/test_market_api.py` | TC-68, TC-70 |
| `weather-telegram-console/tests/test_market_card.py` | TC-68 |
| `weather-comparison-engine/tests/test_unified_status_builder.py` | TC-69 |
| `weather-telegram-console/tests/test_status_api.py` | TC-72, TC-74, TC-77 |
| `weather-telegram-console/tests/test_ops_alert_bridge.py` | TC-85, TC-86, TC-87, TC-88 |
| `weather-telegram-console/tests/test_ops_alert_handlers.py` | TC-89, TC-90, TC-91 |
| `weather-telegram-console/tests/test_ops_alert_bridge.py` | TC-104 ~ TC-106 |
| `weather-telegram-console/tests/test_ops_alert_handlers.py` | TC-106 ~ TC-107 |
| `weather-telegram-console/tests/test_ops_alert_bridge.py` | TC-107 |
| `weather-dashboard/tests/test_compact_gate_stack_panel.py` | TC-92 |
| `weather-telegram-console/tests/test_market_api.py` | TC-93 |
| `weather-execution-gateway/tests/test_position_exposure.py` | TC-94 |
| `weather-execution-gateway/tests/test_gates.py` | TC-95 |
| `weather-comparison-engine/tests/test_gate_stack_automation_consumer.py` | TC-96, TC-97 |
| `weather-telegram-console/tests/test_runtime_snapshot_cli.py` | TC-98 |
| `weather-execution-gateway/tests/test_position_exposure.py` | TC-99 |
| `weather-comparison-engine/tests/test_gate_stack_automation_consumer.py` | TC-100 |
| `weather-comparison-engine/tests/test_gate_stack_automation_consumer.py` | TC-101, TC-103 |
| `weather-telegram-console/tests/test_status_card.py` | TC-72 |
| `weather-telegram-console/tests/test_status_handler.py` | TC-72 |
| `weather-execution-gateway/tests/test_position_exposure.py` | TC-75, TC-76 |

---

## 8. 关键手动验证记录

### 8.1 Monitoring / Unified Status

已执行：

```bash
cd weather-comparison-engine
PYTHONPATH=src python -m weather_comparison_engine.main build-monitoring-status
PYTHONPATH=src python -m weather_comparison_engine.main build-validation-quality
PYTHONPATH=src python -m weather_comparison_engine.main build-unified-status
```

验证结果：

- 成功生成 `monitoring_status.json`
- 成功生成 `validation_freshness_status.json`
- 成功生成 `label_coverage_report.json`
- 成功生成 `unified_status.json`
- 当前样例环境下可见 `heuristic_not_calibrated` 与 `manual_advisory_only`
- Phase 27.1 Batch 1 registry-first 回归已通过：
  - `weather-rules-research/tests/test_governance_registry.py` `2 passed`
  - `weather-comparison-engine/tests/test_governance_registry.py` `2 passed`
  - 两端 `validate-registry` CLI 均输出 `ok=true`
- Phase 27.1 Batch 2 policy-ref resolver 回归已通过：
  - `weather-rules-research/tests/test_resolver_contract_registry.py`
  - `weather-rules-research/tests/test_resolver_report.py`
  - `weather-rules-research/tests/test_live_market_resolver.py`
  - `weather-rules-research/tests/test_market_resolution_registry.py`
  - 合计 `23 passed`
- Phase 27.1 Batch 3 registry-driven freshness / canonical hooks 回归已通过：
  - `weather-comparison-engine/tests/test_governance_registry.py`
  - `weather-comparison-engine/tests/test_monitoring_status_builder.py`
  - `weather-comparison-engine/tests/test_top_parameter_view.py`
  - 合计 `8 passed`
- Phase 27.1 Batch 4 policy-aware read-only display 回归已通过：
  - `weather-dashboard/tests/test_top_parameter_ribbon.py`
  - `weather-dashboard/tests/test_monitoring_signals_panel.py`
  - `weather-telegram-console/tests/test_status_card.py`
  - `weather-telegram-console/tests/test_market_card.py`
  - `weather-telegram-console/tests/test_monitoring_card.py`
  - 合计 `8 passed`
- Phase 27.2 normalization-aware forecast snapshot 回归已通过：
  - `weather-rules-research/tests/test_governance_registry.py`
  - `weather-rules-research/tests/test_normalization_schema.py`
  - `weather-rules-research/tests/test_joiner.py`
  - 合计 `7 passed`
- Phase 27.2 normalization-aware forecast / comparison / read-only surface 回归已通过：
  - `weather-comparison-engine/tests/test_top_parameter_view.py`
  - `weather-comparison-engine/tests/test_monitoring_status_builder.py`
  - `weather-comparison-engine/tests/test_governance_registry.py`
  - `weather-dashboard/tests/test_top_parameter_ribbon.py`
  - `weather-dashboard/tests/test_monitoring_signals_panel.py`
  - `weather-telegram-console/tests/test_market_card.py`
  - `weather-telegram-console/tests/test_status_card.py`
  - `weather-telegram-console/tests/test_monitoring_card.py`
  - `weather-telegram-console/tests/test_text_commands.py`
  - 合计 `19 passed`
- Phase 27.3 Batch 1 canonical-only observation alert 回归已通过：
  - `weather-comparison-engine/tests/test_monitoring_layer.py`
  - `weather-comparison-engine/tests/test_monitoring_runners.py`
  - 合计 `5 passed`
- Phase 27.3 Batch 2 canonical-only family scanner 回归已通过：
  - `weather-comparison-engine/tests/test_monitoring_layer.py`
  - `weather-comparison-engine/tests/test_monitoring_runners.py`
  - 合计 `5 passed`
- Phase 27.3 Batch 3 alert / anomaly / gate layered display 回归已通过：
  - `weather-dashboard/tests/test_monitoring_signals_panel.py`
  - `weather-telegram-console/tests/test_monitoring_api.py`
  - `weather-telegram-console/tests/test_monitoring_card.py`
  - `weather-telegram-console/tests/test_monitoring_handler.py`
  - 合计 `5 passed`
- Phase 27.3 Batch 4 gateway review context 回归已通过：
  - `weather-execution-gateway/tests/test_position_exposure.py`
  - 合计 `5 passed`

### 8.2 Dashboard Operator Surface

已验证：

- Command / Pipeline / Markets / History / Validation 主视图可运行
- `Market Evidence Chart` 可展示 market/model/official/advisory 证据
- `Operator Market Context` badge 可显示 Telegram 默认跟随市场
- `Pipeline Sync` 可显示 selected / Telegram default / last sync 对齐摘要
- `Read-only Account Exposure` 可显示 position snapshot、当前市场 exposure 与 readiness limit usage
- gate blockers 能显示 validation freshness、coverage、resolver source contract 问题
- 运行时问题修复后，页面已恢复可打开状态

### 8.3 Telegram Status / Approval

已验证：

- Telegram `/status` 已消费 unified status contract
- Telegram `/market [market_id]` 已消费 latest dashboard rows 与 operator market context
- Telegram `/timeline [market_id]` 已消费 comparison history 与 operator market context
- approval 记录会绑定具体 `intent_id`
- manual advisory acknowledgement 会写入 audit 事件

---

## 9. 当前结论

### 9.1 已验证通过的核心能力

当前可以认为已经验证通过的能力包括：

- market -> resolver -> probability -> comparison -> dashboard 主链路
- source contract 与 resolver mismatch 降级
- probability contract 三态与回退逻辑
- validation freshness / label coverage gate
- unified status 聚合
- manual advisory / pending intent / gateway dry-run
- dashboard 与 telegram 对关键 contract 的一致消费
- Phase 20 operator control surface：evidence chart、operator context、pipeline sync alignment、read-only exposure、Telegram market/timeline

### 9.2 Phase 27 验收结论

Phase 27 — Monitoring Collection / Indicator Governance 已完成并建议作为新基线收口。

已验收的核心增量包括：

- source governance：source cadence、freshness、priority、fallback 形成统一 registry-first 策略。
- measurement governance：canonical unit、precision、rounding、band mapping、normalization-aware schema 形成统一标准。
- monitoring collection：单市场 alert 与 family anomaly 已具备可运行、可审计、可回放的 MVP 闭环。
- surface consumption：dashboard / Telegram / gateway 已按 alert / anomaly / gate 分层消费，不再混淆执行许可与监测异常。

### 9.3 当前仍需补强的验证点

以下用例已经设计，但仍建议在后续版本继续补强或扩展：

- TC-12：跨市场 forecast mismatch 的更多真实样例
- TC-37 ~ TC-45：随着 label coverage 与 family 覆盖增加，补充更多真实数据回归

### 9.4 Phase 28 建议入口

Phase 28 已完成并作为正式基线收口。Phase 29 建议优先从 family rollout / calibration feedback / coverage expansion 入手，在 Phase 28 的 validation / backtest / monitoring 基线上继续扩大 family 覆盖、校准反馈与多 family rollout 视图。Phase 29.1 进一步聚焦 family coverage、calibration drift 与 rollout summary 的仓库级落点：`weather-comparison-engine` 负责 drift 与 coverage 生成，`weather-rules-research` 负责新增 family resolver / normalization 对齐，`weather-dashboard` / `weather-telegram-console` 负责 rollout summary 只读展示，`weather-execution-gateway` 继续保持只读审查边界。Phase 29.1 Batch 1 已完成，validation / backtest / calibration reports 已开始输出 family coverage、calibration drift、drift bucket 与 rollout completion summary。Phase 29.1 Batch 2 已完成，dashboard / Telegram 的 validation 面板已补齐 family rollout 摘要，validation / backtest 反馈闭环开始在只读消费面可见。Phase 29.1 Batch 3 已完成，dashboard 的统一状态条与 Telegram 的 status card 也已补齐 family rollout 摘要首屏，validation / backtest 反馈闭环开始在更多 operator 入口可见。Phase 29.1 Batch 4 已完成，回归测试与文档同步已收尾，Phase 29.1 可作为完成态继续进入下一阶段。Phase 29.2 建议直接转向 coverage trend / family expansion / calibration drift backfill，在 Phase 28 的 canonical-only 口径上继续补齐更多 family 的 resolver 覆盖和趋势回放视图。Phase 29.2 Batch 1 已完成，`weather-comparison-engine` 已开始输出 family_rollout_trend_summary.v1，覆盖趋势与 drift movement 进入 validation / backtest / calibration 报告。Phase 29.2 Batch 2 已完成，dashboard / Telegram 的只读消费面已接入 coverage trend / drift movement 摘要，趋势回放开始可见。Phase 29.2 Batch 3 已完成，dashboard 的 family rollout trend 与 Telegram 的 /status validation trend 摘要已经稳定可见，operator 可以更早看到 coverage / ready / drift movement。Phase 29.2 Batch 4 已完成，回归测试与文档同步已收尾，Phase 29.2 可作为完成态继续进入下一阶段。Phase 29.3 建议顺势转向 coverage stall / drift watchlist / expansion backlog，在 Phase 29.2 的 trend history 上继续把“趋势”收敛成“该优先补哪几个 family”。Batch 1 + Batch 2 + Batch 3 + Batch 4 已完成，`weather-comparison-engine` 已开始输出 `family_rollout_watchlist.v1`，并将 watchlist history 接入 dashboard / Telegram 的只读消费面，可识别 stalled family、drift spike family 与 expansion backlog family；Batch 3 / Batch 4 已完成 dashboard / Telegram watchlist view 与回归 / 文档收口。这样可以保证离线验证、回测、校准与在线 canonical-only 链路同口径，同时逐步提升多 family 适配能力。

### 9.5 Phase 28.1 Batch 1 / Batch 2 / Batch 3 / Batch 4 状态

Phase 28.1 Batch 1 + Batch 2 + Batch 3 + Batch 4 已完成，`weather-comparison-engine` 的 feature store / validation loader 已开始吸收 canonical-only schema，validation report / backtest report / calibration report 也已开始纳入 source / normalization governance 摘要与 policy refs，dashboard / Telegram 的只读验证摘要展示也已接入，回归测试与文档同步已完成。Phase 28.1 Batch 1 还新增了 Opportunity Board 的实现骨架：`opportunity_board_view.v1` 已可由 `weather-comparison-engine` 生成，`opportunity_explanations.json` 与 `opportunity_feature_rows.json` 也已纳入文件输出约定，dashboard 已新增 Opportunity Board 一级 tab，Telegram 也已新增 `/opportunities` 与 `/opportunity <city>` 入口。Phase 28 Batch 2 已完成，dashboard 侧 Opportunity Board 已补齐更完整的过滤维度、row preview、score breakdown 与 model/difficulty explainability，Opportunity Board 现在可作为一级入口完成市场初筛与 drill-down。Phase 28 Batch 3 已完成，Telegram 侧 `/opportunities` 与 `/opportunity <city>` 已开始优先消费 city-level payload，并在机会卡片中补齐 `/market <id>` 下一步提示、城市 detail 和轻量机会 drill-down。Phase 28 Batch 4 已完成，dashboard 侧 preview 已补齐 `Open Workstation` 联动，会复用现有 pinned/focus 选择链路把目标 market 推入单市场工作台；同时 best model reason / recommended action reason 的解释断言、机会板 primary market 选择断言和相关回归也已通过。Phase 28 的 repo 级实现清单已经细化为 comparison-engine / rules-research / dashboard / telegram / gateway 五仓库分工，并明确了 opportunity_score、difficulty_score、best_model / best_source_stack 的 rule-based 起步口径与分数解释字段。
Phase 30 已完成并正式收口：`validation_assimilation_summary.v1` 已落在 `model_validation_report` 中，`validation_assimilation_report.json` 已独立落盘，dashboard / Telegram 的验证面板已显示 assimilation status、feature store ready、label store ready 与 validation watchlist 的只读摘要。历史 feature store 中缺失 `model_probability` 的旧样本已可安全降级，不再阻塞 validation / backtest / calibration 产出。
Phase 28 seed 输入回归已补齐：`opportunity_seed_list.v1` 可作为 cold-start prior 生成 seeded opportunity rows，seed row 会显式标记 `seeded_from_manual_research=true`、`recommended_action=watch_seed` 且不携带 market / gate / alert / anomaly refs；当同一 `city × family` 已有真实系统 row 时，seed 不会重复覆盖系统评分。
Phase 28 opportunity policy registry 回归已补齐：`opportunity_score_builder.py`、`difficulty_score_builder.py`、`best_model_recommender.py`、`recommended_action_mapper.py` 已开始读取 `opportunity_policy_registry` 下 6 个 policy JSON，`opportunity_board_view.v1`、`opportunity_explanation.v1` 与 `opportunity_feature_rows.json` 均会输出 policy refs。相关 opportunity surface 回归 `12 passed`，`compileall` 通过，实际 `build-opportunity-board` 已重新生成带 policy refs 的机会板输出。
本轮审核回归追加：`scoring_policy_ref` 已作为规范字段进入 row / explanation / feature rows；`source_precision_policy` 已按组合映射验证，`exact_station + proxy` 会稳定输出 `0.8`，不再被 resolver confidence 微调污染。相关 opportunity 回归 `10 passed`，`compileall` 通过，并已重新生成 `opportunity_board_view.json`。

### 9.6 Phase 28.2 状态

Phase 28.2 已开始收口 family anomaly 高阶解释层。`family_scan_report.v1` 与 `market_anomaly_event.v1` 已补齐 `signal_summary`、`anomaly_bucket` 和 `feature_breakdown`，dashboard / Telegram 的 family anomaly 区块也已开始显示高阶信号汇总，相关回归已通过。

### 9.7 Phase 28.3 状态

Phase 28.3 已开始收口 monitoring / ops / alert 联动展示。dashboard / Telegram 已新增 operator summary，把 market alert、family anomaly 和 gate block 合成为 operator-facing 结论，帮助 operator 更快判断当前该看什么、为什么不能动，相关回归已通过。

### 9.8 Phase 29 测试入口

Phase 29 建议进入 Single Market Workstation 测试矩阵。测试重点不再是新增事实计算，而是验证单市场页面是否能稳定聚合并分层展示已有合同：

- `market_workstation_view.v1` contract test：结构完整、upstream refs 可回指、不成为新事实源。
- Top Parameter Ribbon test：只消费 `TopParameterView.v2`，不做本地单位转换或 band 映射。
- Evidence Timeline test：market / forecast / observation / alert / anomaly / gate markers 可同屏聚合。
- Rule / Source / Model Panel test：source contract、best model、difficulty explainability 可读。
- Gate / Advisory / Dry-run Panel test：advisory / dry-run 与 gate 语义清晰，不把 anomaly 误接成 execution allow。
- Telegram `/market` consistency test：与 dashboard 对同一 selected market 的 alert / anomaly / gate / validation 摘要保持同口径。

Phase 29 Batch 1 已新增并通过最小回归：`weather-comparison-engine/tests/test_market_workstation_view.py` 覆盖合同边界，`weather-dashboard/tests/test_market_workstation_page.py` 覆盖 Opportunity Board 上下文匹配、Workstation contract、Evidence Timeline 占位与 `gate_stack_api.v1_only` execution boundary。

Phase 29 Batch 2 已新增并通过最小回归：`evidence_timeline.v1` 开始覆盖 market probability / forecast / observation / events 四轨摘要，dashboard 会按 selected market 读取 latest alert / anomaly 并作为 marker 进入工作台；测试覆盖 ready timeline、forecast / observation latest point、market history point count、alert / anomaly / gate marker，以及 monitoring event file 的 market_id 过滤读取。

Phase 29 Batch 3 已新增并通过最小回归：`validation_compare_panel.v1` 覆盖 promotion state、primary blocker、validation freshness、label coverage 与 governance coverage；`opportunity_workstation_linkage.v1` 覆盖 Opportunity Board row、recommended action、best model/source stack 与 upstream refs，确保机会板进入工作台后上下文不丢失，且不转化为 execution permission。

Phase 29 Batch 4 已新增并通过最小回归：Telegram `/market` 已增加 `telegram_market_workstation_context.v1`，覆盖 market alert、family anomaly、gate boundary、validation / coverage 与 opportunity entry 五块轻量工作台摘要；测试覆盖 `MarketAPI` 文件读取、market_id 过滤、formatter 输出，以及 `gate_stack_api.v1_only` execution boundary 不被机会/异常替代。

Phase 29 文件化输出回归也已补齐：`write_market_workstation_artifacts` 覆盖 `market_workstation_<market_id>.json`、`evidence_timeline_<market_id>.json`、`validation_compare_<market_id>.json` 写出；`scripts/run_market_workstation_once.py 397991` 已在当前样例数据上成功生成三类 artifact。

Phase 29 数据模型输出清单已对齐：`write_market_workstation_artifacts` 现在覆盖主文件、`rule_source_model_panel_<market_id>.json`、`evidence_timeline_<market_id>.json`、`validation_compare_<market_id>.json`、`gate_advisory_panel_<market_id>.json` 与 `market_workstation_summary_<market_id>.json`；contract test 覆盖 `entry_context.v1` 与 6 类 artifact 名称。

### 9.9 Phase 30 验证收口

Phase 30 已完成并作为正式基线收口。validation assimilation 已通过 `validation_assimilation_summary.v1` 与 `validation_assimilation_report.json` 接入 validation / backtest / calibration 链路，dashboard / Telegram 的验证面已展示 assimilation status、feature store ready、label store ready 与 family scan / advanced anomaly 摘要。Opportunity Board 与 Single Market Workstation 也已将 family anomaly summary 回灌到只读消费面；Telegram `/opportunities`、`/market` 与 `/status` 的轻量工作台语义已与 dashboard 对齐，同时仍保持 alert / anomaly / opportunity 不替代 gate 语义。

---

## 10. 残余风险

| 风险 | 影响 |
|---|---|
| validation report stale | probability contract 容易保守回退 |
| labeled coverage 偏低 | 难以稳定进入 candidate/live |
| resolver family 覆盖仍在扩展 | 某些市场仍处于 unmatched/family-only |
| operator mode 后续仍需治理 | dev / guarded / production_read_only 已形成 Phase 20 契约，但后续真实生产流程仍需治理和审批 |
| 当前 execution 仍以 dry-run/manual advisory 为主 | 不适合宣称生产自动交易已通过验收 |

---

## 11. 验收建议

建议后续评审按以下层次验收：

1. 先验 contract：resolver source contract、probability contract、unified status 是否稳定。
2. 再验流程：market -> evidence -> gate -> intent -> dry-run 是否可闭环。
3. 再验 UI/Telegram：operator 是否能一眼判断“当前看哪个市场、能不能动、为什么不能动”。
4. 最后验数据质量：validation freshness、label coverage、resolver match rate 是否达到晋级门槛。

---



## 12. 总结

本次更新后的测试报告已经把系统测试从“模块通过若干 pytest”提升为“可回溯到需求、架构和详细设计的测试矩阵”。

当前测试结论是：

- 系统已经达到研究控制台、manual advisory 控制台、dry-run 执行控制台的验证水平。
- 系统尚未达到 production autonomous trading platform 的最终验收水平。
- 后续测试重点应从 Phase 20 控制面硬化转向更多真实 market family、主动通知 workflow、validation 数据质量和更长期回归。
- Phase 30 已完成并作为正式基线收口，validation assimilation 与 advanced anomaly 的只读消费面已经和 dashboard / Telegram / workstation 对齐。
- Phase 31 已完成并作为正式基线收口，market discovery scanner、evidence scanner、scanner status、market alert router、family anomaly router 与 scanner ops alert 的只读消费面已经和 dashboard / Telegram / workstation 对齐。
