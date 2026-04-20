# AARS Polymarket Weather Trading Test Report

版本：v0.2  
日期：2026-04-18  
关联文档：

- [AARS_Polymarket_Weather_Trading_Functional_Requirements.md](./AARS_Polymarket_Weather_Trading_Functional_Requirements.md)
- [AARS_Polymarket_Weather_Trading_Architecture.md](./AARS_Polymarket_Weather_Trading_Architecture.md)
- [AARS_Polymarket_Weather_Trading_Detailed_Design.md](./AARS_Polymarket_Weather_Trading_Detailed_Design.md)
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

需求依据来自功能需求文档中的 FR-01 至 FR-17：

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
- `monitoring_status.json`
- `unified_status.json`
- `gate_stack_api.json`
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

### 7.3 当前已覆盖的代表性自动化测试

| 测试文件 | 对应用例/主题 |
|---|---|
| `weather-rules-research/tests/test_resolver_contract_registry.py` | TC-07 ~ TC-10 |
| `weather-comparison-engine/tests/test_probability_contract_policy.py` | TC-13 ~ TC-15, TC-40 |
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

### 9.2 当前仍需补强的验证点

以下用例已经设计，但仍建议在后续版本继续补强或扩展：

- TC-12：跨市场 forecast mismatch 的更多真实样例
- TC-37 ~ TC-45：随着 label coverage 与 family 覆盖增加，补充更多真实数据回归

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
| `weather-telegram-console/tests/test_intent_writer.py` | TC-60 |
| `weather-telegram-console/tests/test_approval_handler.py` | TC-60 |
