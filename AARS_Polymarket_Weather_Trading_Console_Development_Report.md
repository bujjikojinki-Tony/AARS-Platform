# AARS Polymarket Weather Trading Console Development Report

版本：v0.3  
日期：2026-04-21  
关联文档：

- [AARS_Polymarket_Weather_Trading_Functional_Requirements.md](./AARS_Polymarket_Weather_Trading_Functional_Requirements.md)
- [AARS_Polymarket_Weather_Trading_Architecture.md](./AARS_Polymarket_Weather_Trading_Architecture.md)
- [AARS_Polymarket_Weather_Trading_Detailed_Design.md](./AARS_Polymarket_Weather_Trading_Detailed_Design.md)
- [AARS_Polymarket_Weather_Trading_Implementation_Plan_Status.md](./AARS_Polymarket_Weather_Trading_Implementation_Plan_Status.md)
- [AARS_Polymarket_Weather_Trading_Test_Report.md](./AARS_Polymarket_Weather_Trading_Test_Report.md)
- [AARS_Polymarket_Weather_Trading_Monitoring_Collection_And_Indicator_Governance.md](./AARS_Polymarket_Weather_Trading_Monitoring_Collection_And_Indicator_Governance.md)

---

## 1. 文档目的

本文档用于对 AARS Polymarket Weather Trading Console 的当前开发状态进行阶段性归档，面向以下目的：

1. 说明系统已经落地的核心能力与代码归属。
2. 说明当前阶段完成度、质量状态与可运行边界。
3. 为 Phase 24 / 25 / 26 的持续收口、阶段验收和测试回归提供统一上下文。

---

## 2. 当前结论

截至 2026-04-21，系统已经从早期“实时天气市场看板”演进为一个具备主链路闭环的 **Polymarket 天气/气候交易研究与执行控制台 MVP**。

当前已经完成并打通的主链路为：

```text
Polymarket market discovery
-> realtime market snapshot
-> market resolver / source contract
-> forecast snapshot / weather adapter
-> probability shadow + validation contract
-> comparison + history
-> dashboard / telegram unified status
-> authorization / approval
-> execution gateway dry-run / manual advisory
```

当前统一收口的首屏与 operator surface 还包括：

- `TopParameterView` 作为 dashboard / Telegram / gateway / comparison-engine 的首屏参数面。
- 顶层优先显示非空字段，空字段自动折叠，避免非温度 market 把整屏占位符铺开。
- `market_realtime_simple*.json` 启动时优先保留有价格的市场，避免 metadata-only 空壳覆盖主快照。
- `TopParameterView` 已延伸到 comparison history、history relationship、comparison table、market evidence chart 与 timeline panel。
- 更上游的市场发现、市场录入、resolver、forecast 与 comparison 也必须共享唯一数据源，避免前后端在不同页面各自“长出不同事实”。

Phase 27 监测采集 / 指标治理已经完成并进入正式基线：

- source governance、measurement governance、normalization-aware schema、canonical-only alert/anomaly contracts 已经落盘。
- `ForecastSnapshot.v2` / `ObservationSnapshot.v2` / `TopParameterView.v2` 已形成统一的 raw / canonical / display 语义链路。
- `market_alert_event.v1` / `market_anomaly_event.v1` / `family_scan_report.v1` 已形成可运行、可审计、可回放的监测采集闭环。
- dashboard / Telegram / gateway 继续只读消费监测结果，并与 gate / execution 语义分层。

仓库速查表：

| 仓库 | 负责链路 | 主要产物 |
|---|---|---|
| `polymarket-weather-ingest` | 市场发现 / 录入 / 价格优先主快照 | `market_realtime_simple*.json` |
| `weather-rules-research` | resolver / station / forecast / observation | `resolved_market_rules/*.json`、`forecast_realtime_snapshot.json` |
| `weather-comparison-engine` | comparison / probability / top parameter 聚合 | `latest_dashboard_rows.json`、`TopParameterView`、`unified_status.json` |
| `weather-dashboard` | 首屏展示 / operator surface | `TopParameterView` ribbon、history / evidence panels |
| `weather-telegram-console` | status / market / timeline 消费面 | Telegram cards、runtime snapshot |
| `weather-execution-gateway` | dry-run / risk gate / exposure | `ExecutionIntent`、`production_readiness_report.json` |

建议把后续验证统一按以下治理清单执行：

1. 同一 `market_id` 的 market snapshot / market rule / forecast snapshot / comparison point 是否可回指。
2. `TopParameterView` 是否只做聚合，不改写事实。
3. 非适用 family 字段是否折叠或隐藏。
4. `market_probability` 是否可由显式字段或 yes/no price 算出。
5. dashboard、Telegram、gateway 是否消费同一条上游链路。

建议把上游事实链拆成五段来推进：

1. 市场研究 / 市场录入，确保价格市场是唯一主快照。
2. resolver 解析，确保 market_rule 回指唯一 `market_id`。
3. forecast / observation，确保站点映射与 target_date 对齐。
4. comparison / probability，确保所有展示字段都是派生而非重写。
5. 展示 / operator surface，确保 Dashboard、Telegram、Gateway 只消费统一合同。

系统当前适合用于：

- 市场研究与行情跟踪
- resolver / source contract 审查
- heuristic probability / fair value 辅助判断
- manual advisory / dry-run 操作台
- validation / monitoring / readiness 状态观察
- 首屏参数面与历史证据面的语义一致性审查

系统当前不应被视为：

- 无人值守的生产自动交易平台
- 已经完成 live private-key execution 的交易系统
- 已完成全量 market family 覆盖的统一概率平台

---

## 3. 架构与代码落地概览

| 逻辑层 | 当前仓库/模块 | 当前职责 | 状态 |
|---|---|---|---|
| 01 Market Layer | `polymarket-weather-ingest` | Gamma 搜索、CLOB 聚合、市场快照、watchlist 输入 | Done |
| 02 Resolver Layer | `weather-rules-research` | market family 解析、station/source contract、resolver report | Done |
| Weather Data Adapters | `weather-rules-research` | forecast / station / index snapshot、cache-first 取数 | Done / Partial |
| 03 Probability Layer | `weather-comparison-engine` | shadow probability、ProbabilityContract、contract policy、validation-driven mode | Done |
| 04 Comparison Layer | `weather-comparison-engine` | band compare、edge、history、dashboard row 输出 | Done |
| 05 Decision Layer | `weather-comparison-engine` | action hint、trade decision scaffold | Done / Heuristic |
| 06 XAI / Presentation | `weather-dashboard` | evidence panels、operator closure、history/evidence chart | Done / In Progress |
| 07 Authorization Layer | `weather-dashboard` + `weather-telegram-console` | BOT authorization、approval context、manual advisory signaling | Done / Guarded |
| 08 Execution Layer | `weather-execution-gateway` | pending intent、risk gate、dry-run、manual reconciliation | Done / Dry-run |
| 09 Feature Store | `weather-comparison-engine` | training samples、history append、feature export | Done |
| 10 Label Store | `weather-comparison-engine` | official records、settlement label aggregation | Done / Partial coverage |
| 11 Training / Validation | `weather-comparison-engine` | backtest、calibration、validation report | Done |
| 12 Monitoring / Registry | `weather-comparison-engine` | monitoring status、unified status、contract promotion logic | Done |

---

## 4. 与需求和设计文档的对齐状态

### 4.1 功能需求对齐摘要

| 需求 | 需求主题 | 当前状态 | 说明 |
|---|---|---|---|
| FR-01 | 市场发现与 Watchlist | Done | 支持搜索、Add/Remove、Pin/Unpin、Recent、filter bar |
| FR-02 | 实时盘口采集 | Done | CLOB/Gamma 输出市场快照并供 dashboard 消费 |
| FR-03 | Market Resolver | Done | 支持 source contract、official/proxy/fallback 区分 |
| FR-04 | Weather Data Adapters | Done / Partial | cache-first 与手动刷新可用，部分 family 仍需扩展 |
| FR-05 | Probability Layer | Done / Heuristic + Contract | 已实现 `probability_contract.v1`、probability_mode、calibration_status、execution_constraint |
| FR-06 | Comparison Layer | Done | 已输出 history、gap、band distance、dashboard rows |
| FR-07 | Decision Layer | Done / Heuristic | 已有 action_hint 与 decision scaffold，非 calibrated sizing |
| FR-08 | XAI Layer | Done / UI-oriented | Command Center、Operator Closure、evidence drill-down 已可用 |
| FR-09 | Authorization Layer | Done / Guarded | BOT authorization、approval context、manual advisory 信号已接通 |
| FR-10 | Execution Layer | Done / Dry-run | pending intent、gateway check、risk/readiness、manual reconciliation |
| FR-11 | Dashboard | Done / 持续收口 | Command/Pipeline/Markets/History/Validation 主视图已形成 |
| FR-12 | Telegram Console | Done | `/status`、`/market`、`/timeline`、approval flow 与 operator context 默认市场已接入 |
| FR-13 | Feature Store | Done | training sample 层与历史沉淀已形成 |
| FR-14 | Label Store | Done / Partial coverage | official label / settlement records 已有，但覆盖率仍不足 |
| FR-15 | Training / Validation | Done | calibration/backtest/validation report 已实现 |
| FR-16 | Model Registry | Partial / Contract-first | deployment_mode、approved_for_live 已纳入 contract，其中 approved_for_live 仅作为 validation 候选输入；live 状态由 probability_mode=live_approved 表示，registry 仍轻量 |
| FR-17 | Monitoring | Done | monitoring status、unified status、validation freshness 已接入 |

### 4.2 架构设计对齐摘要

与架构设计文档中的三条闭环对齐情况如下：

| 闭环 | 当前状态 | 说明 |
|---|---|---|
| 实时决策闭环 | Done / Guarded | 已形成 market -> resolver -> probability -> comparison -> authorization -> gateway dry-run |
| 证据论证闭环 | Done / UI可用 | resolver source contract、probability contract、history/evidence、XAI 面板可用于 operator 审查 |
| 训练验证闭环 | Done / 数据质量待提升 | feature store、label store、backtest、validation、promotion policy 已形成，但 labeled coverage 仍不足 |

---

## 5. 已完成的关键开发里程碑

### 5.1 Phase 1-6：实时主链路与 resolver 扩展

已完成：

- live schema validator
- resolver report
- weather / climate family 规则匹配
- probability shadow
- comparison history
- dashboard live alignment
- execution gate dry-run
- sea ice / precipitation / snowfall / wind 等 family 扩展

阶段价值：

- 解决“当前市场是什么、问的是什么、拿什么源、是否能比”的基础问题。

### 5.2 Phase 7-12：历史样本、validation 与人工闭环

已完成：

- training sample feature store
- official history / settlement label
- calibration report / backtest report / model validation report
- Telegram human-in-loop approval
- position snapshot / manual advisory audit
- manual fill reconciliation

阶段价值：

- 解决“历史上怎么学、怎么验证、怎么人工闭环确认”的问题。

### 5.3 Phase 13-19：状态契约、统一状态模型、validation gate

已完成：

- monitoring status / worker health
- probability / calibration status contract
- unified status model
- probability mode promotion / rollback
- resolver registry / official source contract
- validation freshness / label coverage gate
- compact gate stack

阶段价值：

- 解决“为什么现在不能动、是哪一层挡住了、contract 到底是什么”的问题。

### 5.4 Phase 20：Operator Control Surface Hardening

当前状态：Done

本轮已完成：

- `Market Evidence Chart` 已进入 History tab
- dashboard 多处运行时错误已完成修复并通过回归
- execution gate 多实例 key 冲突已修复
- nested expander 问题已排查并修复
- Telegram `/market <id>`、`/timeline <id>` 已接入
- dashboard / Telegram 缺失数据提示语开始统一为 operator-facing contract
- dashboard 已输出 `operator_market_context.json`，Telegram 默认市场选择优先使用该 operator context
- dashboard Command tab 已展示 operator market context badge，用于确认 Telegram 默认市场跟随关系
- dashboard Command tab 已新增 read-only account exposure 面板，展示 position snapshot、余额、总 exposure 与当前市场 exposure
- read-only account exposure 面板已接入 readiness exposure limits，显示 market / total limit usage 与 near / over limit 提示
- Pipeline Sync 面板已增加 selected market / Telegram default / last sync 对齐摘要，减少 operator context 与 pipeline input 错位

完成结论：

- Phase 20 原定 5 个拆分任务已经完成：evidence chart、Pipeline/Markets sync 收口、Telegram 控制面扩展、mode badge、read-only account panel。
- 当前 dashboard / Telegram / unified status 已形成一致的 operator-facing 控制面语义。
- 系统仍保持 manual advisory / dry-run / production_read_only 边界，不引入 private-key 自动交易。

### 5.5 Phase 21：Contract / Registry / Gate Systematization

当前状态：Done

本轮已启动：

- 新增 `ProbabilityContract` / `probability_contract.v1`
- `ProbabilityState` 已内嵌 `probability_contract`
- dashboard `OrderIntent` 与 Telegram approval signal 已携带 `probability_contract`
- `unified_status.json` probability section 已输出 `contract_version` 与 `probability_contract`
- Telegram `/status` 已展示 probability contract version
- gateway live-enabled risk gate 已强制消费 `ProbabilityContract`
- gateway risk gate 已接入 `unified_status` 作为 freshness gate 输入（不再仅展示 monitoring 状态）
- gateway 主流程已显式从 comparison-engine 输出读取 `unified_status.json` 并传入 risk gate
- `ExecutionIntent` contract 已收口：`schema_version=execution_intent.v1` + `decision_ref` + `authorization_ref`
- dashboard / Telegram intent writer 均已输出 execution intent contract 字段
- Telegram approval callback 已在审批后把 `authorization_ref` 回填为真实 `approval_id`
- gateway risk gate 已新增 execution intent contract 校验（缺失字段会返回 `execution_intent_contract_invalid`）
- 已新增 `aars_weather_trading` 治理骨架（gateway-first）：
  - `contracts/`：probability / unified_status / execution_intent contract dataclass
  - `registries/`：source / station registry
  - `gates/`：probability / freshness / compact gate stack
- gateway risk gate 已改为消费统一 gate 模块（`evaluate_probability_gate`、`evaluate_freshness_gate`）

当前结论（Phase 21 收口完成）：

- `probability_mode / calibration_status / execution_constraint` 已从散字段升级为跨 comparison-engine / dashboard / telegram / gateway 的统一 contract。
- UnifiedStatus 已进入 gateway 执行门禁，`degraded/missing` 或 worker `stale/degraded/missing/error/unknown` 可直接阻断执行。
- ExecutionIntent 已从“可选字段集合”升级为 gateway 可执行前置合同，dashboard / telegram / gateway 语义已统一。
- contract/registry/gate 三件套最小骨架已经具备可扩展入口，后续可以从 gateway-first 逐步推广到 dashboard / telegram / resolver。
- resolver 层已开始 registry-first 收口：新增 `band_scheme_registry`、`source_registry`，并接入 taxonomy 与 resolver contract builder。
- 已新增统一 `resolver_gate`，并将其并入 compact gate stack 语义维度，供后续 dashboard/telegram 对齐消费。
- dashboard compact gate stack 与 Telegram `/market` 卡片已接入 `resolver_gate` 与标准化 resolver blockers 展示。
- `unified_status.json` 已新增 `gate_stack` 统一结构（resolver/probability/freshness/execution gate + reasons + block_reasons）。
- dashboard compact gate stack 与 Telegram `/market` 已改为优先消费 unified gate stack（市场匹配时），避免多端各自重算 gate 语义。
- `gate_stack` 已补齐 `authorization_gate` 维度；gateway risk gate 已优先消费 unified gate stack，执行前置判断不再依赖单端局部推导。
- Telegram `/status` 也已切到统一 gate_stack contract（缺失时由 StatusAPI 自动补齐），状态展示语义与 dashboard/gateway 对齐。
- Phase 21 已达到“统一 contract / 统一 registry / 统一 gate”基线，可作为后续迭代稳定底座。

### 5.6 Phase 22：Gate Stack External API / Automation Consumption

当前状态：Done

本轮新增交付：

- comparison-engine 新增 `gate_stack_api.v1` 生成器，输出 `weather-comparison-engine/data/outputs/gate_stack_api.json`。
- `build-unified-status` 已自动联动导出 gate stack API，并补充独立命令 `build-gate-stack-api`。
- Telegram `StatusAPI` 已支持 API-first 读取：
  - 有 unified status 时：优先用 gate stack API 覆盖 gate contract；
  - 无 unified status 时：可直接用 gate stack API 构造 `/status` 输出。
- gateway dry-run 在 unified status 缺失时可回退消费 gate stack API，确保执行前阻断语义不丢失。
- 新增 targeted regression，覆盖 comparison-engine / telegram / gateway 的 API 生成与消费链路。

阶段性结论：

- Phase 22 已完成第一批“外部稳定 gate contract”落地，`gate_stack_api.v1` 已成为 automation-friendly 的统一消费入口。
- 当前仍需继续推进 Phase 22 后半程（多市场 API 视图、dashboard source badge、automation action hints）。

Batch 2（本轮完成）：

- `gate_stack_api.v1` 已扩展 `market_gate_views` 与 `market_count`，支持多市场 gate contract 输出。
- API 已输出 automation hints：`severity`、`recommended_operator_action`、`primary_block_reason`（顶层与 market view）。
- Telegram `/status` 在 API 路径已切换 market-specific consumption（按 current market_id 匹配 market view）。
- gateway unified status 缺失时已按 intent market_id 读取 gate stack API market view，避免跨市场误判。
- dashboard Compact Gate Stack 已显示 `gate_source`（local/unified/api）与 severity/action，便于 operator 快速判读。

Batch 3（Final Closeout，本轮完成）：

- comparison-engine 已新增 automation consumer 输出：`gate_stack_automation_summary.v1`。
- 新增 CLI：`build-gate-stack-automation-summary`，可被 cron/worker 直接调用。
- 已新增 Gate Stack API 合同文档：`AARS_Polymarket_Weather_Trading_Gate_Stack_API_Contract.md`，覆盖 schema、消费规则、版本升级策略。
- comparison-engine 新增 automation consumer + CLI 写出测试并通过。

Phase 22 收口结论：

- `contract`：`gate_stack_api.v1` 与 `gate_stack_automation_summary.v1` 已形成稳定外部语义。
- `consumption`：dashboard / telegram / gateway 都已统一按 contract 消费，不再依赖散落推导。
- `operations`：automation 路径已有可运行 artifact + CLI + 文档，满足后续运营闭环接入。

### 5.7 Phase 23：Automation Runtime Gate Check（Batch 1）

当前状态：In Progress

本轮新增交付：

- comparison-engine 新增 runtime 命令：
  - `run-gate-stack-automation-check --fail-on-signal red|amber|never`
- 该命令会在单次运行中同步刷新：
  - `gate_stack_api.json`
  - `gate_stack_automation_summary.json`
- 新增统一退出码语义（cron/worker 可直接消费）：
  - `0`：未命中阈值
  - `2`：命中阈值（如 `fail-on-signal=red` 且 signal 为 red）
- 新增回归测试覆盖：
  - exit code 解析
  - runtime command 非零退出路径

阶段性结论：

- 系统已具备“contract 输出 + runtime gate check”闭环能力，可直接进入调度层接入。

Batch 2（本轮完成）：

- 新增 realtime worker：`weather-comparison-engine/scripts/run_gate_stack_automation_realtime.py`。
  - 支持 interval 调度、max cycles、retry backoff。
  - 每次循环自动刷新 gate API 与 automation summary。
- 新增 ops alert bridge：
  - `gate_stack_ops_alert.v1`
  - 输出路径：`weather-comparison-engine/data/outputs/gate_stack_ops_alerts.jsonl`
  - 当 runtime 检查命中 red 阈值时自动追加告警事件。
- `run-gate-stack-automation-check` 已接入 alert bridge（单次命令也可触发告警事件）。
- `AARS_Polymarket_Weather_Trading_Gate_Stack_API_Contract.md` 已补充 ops bridge 章节。

当前状态：

- Phase 23 Batch 1 + Batch 2 + Batch 3 + Batch 4 已完成，已具备“可调度检查 + 可桥接告警”的运行时治理骨架。

Batch 3（本轮完成）：

- 在 `weather-telegram-console` 新增 ops bridge：
  - `weather_telegram_console.integrations.ops_alert_bridge`
  - `weather_telegram_console.ops_bridge_cli`
- 新增 CLI 入口：
  - `weather-telegram-ops-bridge sync-gate-alerts --max-batch N`
- 功能语义：
  - 读取 comparison-engine `gate_stack_ops_alerts.jsonl`
  - 去重后写入 `telegram_ops_notifications.jsonl`
  - 维护 `ops_alert_bridge_state.json` 作为去重游标状态
- 该桥接为“通知分发前一跳”，将 runtime alert 转换为 Telegram 可消费队列对象。

当前进度：

- Phase 23 Batch 1 + 2 + 3 已完成。
- 下一步是把 queue 与 bot 发送链路打通（pending -> sent/acked）。

Batch 4（本轮完成）：

- 新增 notification queue lifecycle 模块：
  - `weather_telegram_console.integrations.ops_notification_dispatcher`
- 新增 CLI 命令：
  - `weather-telegram-ops-bridge dispatch-ops-queue --max-batch N`
  - `weather-telegram-ops-bridge ack-ops --notification-id <id> --acked-by <user>`
- 完成状态流转闭环：
  - `pending -> sent -> acked`
- 新增 delivery 事件日志：
  - `telegram_ops_delivery_log.jsonl`
- 相关 README 和环境变量文档已补齐。

当前进度：

- Phase 23 Batch 1 + 2 + 3 + 4 已完成。
- 下阶段重点是把 lifecycle 命令与 bot 主循环的真实发送/回执打通。

Batch 5（本轮完成）：

- 新增 bot handler：
  - `weather_telegram_console.bot.handlers.ops_alerts`
  - `/opsqueue [max]`：管理员触发 pending 队列分发并回写 `sent`
  - `/opsack <notification_id>`：管理员确认并回写 `acked`
- 新增主应用命令注册：
  - `weather_telegram_console.app` 注册 `opsqueue` 与 `opsack` handlers
- 权限约束：
  - 非管理员执行 `/opsqueue` 或 `/opsack` 会直接拒绝
- 增加 handler 回归测试：
  - `tests/test_ops_alert_handlers.py`
  - 覆盖 dispatch、ack、admin guard 三类路径

当前进度：

- Phase 23 Batch 1 + 2 + 3 + 4 + 5 已完成。
- 下一阶段聚焦 Batch 6：告警抑制窗口（同 market/reason cooldown）。

### 5.8 Phase 24：Gate Stack Single Source Hardening（Batch 1）

本轮新增交付：

- dashboard：
  - `weather_dashboard.ui.compact_gate_stack_panel` 已改为 API-first gate stack 消费。
  - gate source 语义统一为：`api` / `unified_fallback` / `local_fallback`。
- telegram：
  - `weather_telegram_console.integrations.market_api` 的 compact gate stack 已改为 API-first。
  - 仅在 API 缺失时才回退 unified，再回退本地 market row 推导。
- gateway：
  - `weather_execution_gateway.main._run_dry_run_for_intent` 改为 API-first 风险输入组装。
  - unified status 仅保留 fallback 路径，避免与 API 并行推导造成语义分叉。

本轮验证：

- `weather-dashboard/tests/test_compact_gate_stack_panel.py`：`4 passed`
- `weather-telegram-console/tests/test_market_api.py tests/test_market_card.py tests/test_market_handler.py`：`9 passed`
- `weather-execution-gateway/tests/test_position_exposure.py tests/test_gates.py`：`13 passed`

阶段性结论：

- Phase 24 Batch 1 已完成，dashboard / telegram / gateway 的 gate 消费优先级已对齐为 API-first。

Batch 2（本轮完成）：

- gateway 风险门控：
  - `RiskGateEngine` 在 `gate_source=api` 时跳过 unified freshness 派生判定，避免 API 与 unified 双重 gate 推导。
- automation summary：
  - `gate_stack_automation_summary.v1` 新增 `gate_source` 透传字段，增强运行面可观测性。

Batch 3（本轮完成）：

- ops alert bridge：
  - `gate_stack_ops_alert.v1` 事件新增 `gate_source` 字段。
  - `source_schema_version` 改为从 automation summary 的 `source_schema_version` 透传。
- consistency checker：
  - comparison-engine 新增 contract consistency 产物：
    - `gate_stack_contract_consistency.v1`
  - 新增 CLI：
    - `check-gate-stack-contract-consistency [--market-id <id>] [--fail-on-mismatch]`
- 新增回归测试通过：
  - automation consumer 字段透传
  - ops alert 事件字段透传
  - consistency report 构建与 CLI 写出

当前进度：

- Phase 24 Batch 1 + 2 + 3 已完成。
- 下一阶段重点是把 consistency checker 扩展到跨进程产物（telegram/gateway 运行时快照）一致性扫描。

Batch 4（本轮完成）：

- telegram runtime snapshot：
  - 新增 CLI：`weather-telegram-runtime-snapshot`
  - 导出产物：`telegram_gate_runtime_snapshot.v1`
- gateway runtime snapshot：
  - 新增 CLI：`weather-execution-gateway export-gate-runtime-snapshot`
  - 导出产物：`gateway_gate_runtime_snapshot.v1`
- comparison-engine consistency checker：
  - `check-gate-stack-contract-consistency` 已接入 telegram/gateway 跨进程快照对比。
  - 一致性报告新增：
    - `schema_health`（`ok|warning|critical`）
    - `fallback_stats`（`api|unified_fallback|local_fallback|unknown`）

本轮验证：

- `weather-comparison-engine/tests/test_gate_stack_automation_consumer.py`：`10 passed`
- `weather-telegram-console/tests/test_runtime_snapshot_cli.py tests/test_status_api.py`：`4 passed`
- `weather-execution-gateway/tests/test_position_exposure.py tests/test_gates.py`：`15 passed`

当前进度：

- Phase 24 Batch 1 + 2 + 3 + 4 已完成。
- 下阶段可进入 Batch 5：将 consistency check 纳入周期化 runtime 任务与漂移趋势追踪。

Batch 5（本轮完成）：

- automation realtime worker：
  - `scripts/run_gate_stack_automation_realtime.py` 每轮新增 consistency 计算与落盘。
  - 输出新增：
    - `gate_stack_contract_consistency.json`
    - `gate_stack_contract_consistency_trend.json`
- consistency report 增强：
  - 新增 `mismatch_buckets`：
    - `schema_drift`
    - `source_drift`
    - `reason_drift`
    - `other_drift`
- trend 聚合能力：
  - 累计字段：`total_cycles`、`mismatch_cycles`、`bucket_totals`
  - 最近周期样本：`recent_cycles`（含每轮分桶计数）

本轮验证：

- `weather-comparison-engine/tests/test_gate_stack_automation_consumer.py`：`11 passed`
- `weather-telegram-console/tests/test_runtime_snapshot_cli.py tests/test_status_api.py`：`4 passed`
- `weather-execution-gateway/tests/test_position_exposure.py tests/test_gates.py`：`15 passed`
- 手动运行验证：
  - `python scripts/run_gate_stack_automation_realtime.py`（`GATE_AUTOMATION_CHECK_MAX_CYCLES=1`）输出 consistency bucket 计数并成功写出 trend artifact。

当前进度：

- Phase 24 Batch 1 + 2 + 3 + 4 + 5 已完成。
- 下一阶段可进入 Batch 6：drift 告警阈值与跨周期触发策略。

---

## 6. 当前交付物清单

### 6.1 运行产物

| 类型 | 代表输出 |
|---|---|
| 市场快照 | `market_realtime_simple.json`, `weather_realtime_bundles.json` |
| resolver 输出 | `resolver_report.json`, `resolved_market_rules/*.json` |
| 概率输出 | `probability_state_*.json`, `probability_shadow_report.json` |
| 比较输出 | `comparison_history.json`, `latest_dashboard_rows.json` |
| validation 输出 | `calibration_report.json`, `backtest_report.json`, `model_validation_report.json` |
| 质量状态 | `validation_freshness_status.json`, `label_coverage_report.json` |
| 监控状态 | `monitoring_status.json`, `unified_status.json`, `gate_stack_api.json`, `gate_stack_automation_summary.json` |
| execution 输出 | `pending_intents/*.json`, `production_readiness_report.json`, `human_fill_reconciliation_report.json` |
| audit 输出 | `manual_advisory_audit.jsonl`, `audit_log.jsonl` |

### 6.2 UI / 控制台能力

当前 dashboard 已具备：

- Command tab：trade decision、compact gate stack、detailed execution gate
- Pipeline tab：pipeline flow、sync、data alignment、status panels
- Markets tab：search、watchlist、filter、pin/recent/remove
- History tab：divergence trend、timeline、history relationship、market evidence chart
- Validation tab：validation / calibration / backtest / quality report
- Evidence / Raw tab：bias、rule/station、raw payload

当前 Telegram 已具备：

- `/status`
- `/market [market_id]`
- `/timeline [market_id]`
- approval callback
- manual advisory operator acknowledgement

---

## 7. 当前质量状态

### 7.1 自动化测试基线

截至当前文档版本，已记录的自动化测试基线为：

| 模块 | 基线结果 |
|---|---|
| `weather-comparison-engine` | `42 passed` |
| `weather-dashboard` | `48 passed` |
| `weather-execution-gateway` | `35 passed` |
| `weather-telegram-console` | `13 passed` |
| `weather-rules-research` | `88 passed` |
| `polymarket-weather-ingest` | `14 passed` |

本轮新增修复后的针对性回归：

| 范围 | 结果 |
|---|---|
| `weather-dashboard` gate / alignment / evidence 相关测试 | `17 passed` |

### 7.2 当前质量结论

当前系统已经具备：

- 明确的 contract 字段
- 主链路可运行的 dry-run 能力
- dashboard / telegram / gateway 之间较稳定的状态语义
- 可定位的 block reason 与 validation freshness 信息

当前质量瓶颈主要不是“页面是否能展示”，而是：

- validation report 容易 stale
- labeled coverage 与 resolver match rate 仍偏低
- market family 覆盖尚未完整
- 生产模式与开发模式已有 Phase 20 契约，后续真实生产流程仍需治理和审批
- 非温度 family 的首屏字段需要按 family profile 动态裁剪，避免空字段干扰操作员判断
- 市场研究和录入层需要继续夯实数据治理，确保选中的市场、价格快照、站点映射和 forecast 快照来自同一条可追溯链路

下一步建议按 Phase 24 / 25 / 26 顺序推进：

- Phase 24 先把 gate stack 统一收口成唯一真源，避免 dashboard / telegram / gateway 再次分叉。
- Phase 24.5 将 `TopParameterView` 提升为首屏常态参数带，让天气参数和 Polymarket 参数并列显示，并延伸到 comparison history / history relationship panel。
- 同一份 `TopParameterView` 也已延伸到 comparison table、market evidence chart 与 timeline panel，让历史与比较输出共享一致的顶层合同。
- Phase 24.5 之后，首屏默认采用空字段折叠与 family-specific 标签，避免不同 market family 的视觉密度不一致。
- Phase 25 已完成五个 batch：automation ops 告警 contract、exit code matrix、队列状态流、queue consistency summary、queue status CLI 与 dashboard ops panel 已收口，下一步继续补更细的运维报表。
- Phase 26 已进入第五批收口：validation freshness、label coverage、resolver precision 进入统一 promotion state，并已贯通到 Telegram status / market、gateway runtime snapshot 以及 dashboard compact gate / trade decision / execution gate / probability shadow / operator focus / unified status strip 摘要。

---

## 10. 当前终态

当前控制台已经从“功能齐备的研究面板”收口为“统一事实源驱动的 operator surface”：

1. 上游市场发现、市场录入、resolver、forecast、comparison 必须共享同一条事实链。
2. `TopParameterView` 只负责把首屏参数面聚合出来，不负责改写事实。
3. dashboard / Telegram / gateway / comparison-engine 现在都围绕同一份上游快照与统一 contract 工作。
4. 非温度 market family 的空字段、非适用字段与内部实现名必须折叠或隐藏，不再以空占位干扰操作员。

后续开发的重点，已经不是继续铺新面板，而是继续夯实：

- 价格优先的市场主快照选取。
- forecast / observation / resolver 的同链回指。
- Phase 24 / 25 / 26 的 contract 终态化与回归稳定性。

## 11. 当前风险与限制

### 11.1 数据与模型风险

- 当前概率层仍以 heuristic/shadow contract 为主。
- validation freshness 与 label coverage 不足会主动触发降级。
- 部分 family 仍只有 family-level contract，不能假装 exact resolver。

### 11.2 运行与操作风险

- gateway 当前设计上仍以 dry-run / manual advisory 为主。
- dev harness 与正式 operator mode 已通过 `operator_mode` / `mode_badge` / `dev_controls_enabled` 拆开；真实 live execution 仍受 readiness 与人工审批治理。
- Telegram 控制台已形成基础 market drill-down 工作流；更复杂的交互式分页与主动推送可作为后续增强。

### 11.3 代码与维护风险

- Streamlit 页面复杂度提升后，组件 key、expander 结构、tab 复用等 UI 约束更容易引发运行时错误。
- 控制台层已经进入“需要持续做组件化收口”的阶段，不适合继续无约束堆面板。

---

## 12. 下一阶段建议

建议按照以下顺序继续推进：

1. 进入 Phase 24，优先收口 gate stack 单一真源和跨端 fallback 语义。
2. 继续推进 Phase 25 的后续 batch，把 automation ops contract、queue lifecycle、运维报表做成长期可运维闭环。
3. 继续推进 Phase 26，把 promotion policy 和 resolver/source precision blocker 做成跨表面统一 contract，并继续收口 Telegram / gateway / dashboard 的只读 operator surface。
4. Phase 27 已完成并成为正式基线，后续不再回头补基础治理；直接推进 Phase 28。Phase 28 的第一优先级是让 validation / backtest 吸收 source + measurement governance，然后再在此基础上增强 family anomaly 高阶特征与 monitoring / ops / alert 联动展示。Phase 28.1 的落点已经明确为 validation / backtest / calibration 吸收 canonical-only schema、source policy refs、measurement policy refs，并由 `weather-comparison-engine` 作为主实现仓库、`weather-rules-research` 作为稳定上游输入仓库、`weather-dashboard` / `weather-telegram-console` 作为只读验证消费面。Phase 28.1 Batch 1 已完成，`weather-comparison-engine` 已开始输出 `opportunity_board_view.v1`，并可生成 opportunity / difficulty / best model / source stack 的首版聚合行，同时已落盘 `opportunity_explanations.json` 与 `opportunity_feature_rows.json` 的文件输出约定；dashboard 与 Telegram 的 Opportunity Board 消费入口也已落地到实现骨架。Phase 28 Batch 2 已完成，dashboard 侧 Opportunity Board 已补齐更完整的过滤维度、row preview、score breakdown 与 model/difficulty explainability，Opportunity Board 现在可作为一级入口完成市场初筛与 drill-down。Phase 28 Batch 3 已完成，Telegram 侧 `/opportunities` 与 `/opportunity <city>` 已开始优先消费 city-level payload，并在机会卡片中补齐 `/market <id>` 下一步提示、城市 detail 和轻量机会 drill-down。Phase 28 Batch 4 已完成，dashboard 侧 preview 已补齐 `Open Workstation` 联动，会复用现有 pinned/focus 选择链路把目标 market 推入单市场工作台，同时补齐 best model / recommended action 解释和机会板相关回归。Phase 28 的 repo 级实现清单已细化到 `weather-comparison-engine` / `weather-rules-research` / `weather-dashboard` / `weather-telegram-console` / `weather-execution-gateway` 五个仓库，并明确了 opportunity_score、difficulty_score、best_model / best_source_stack 的 rule-based 起步口径。Phase 27.1 Batch 1 + 2 + 3 + 4 已完成，`source_policy` / `measurement_policy` registry-first 基础设施已在 `weather-rules-research` 与 `weather-comparison-engine` 落盘并通过 validate-registry，`weather-rules-research` 的 resolver 输出已开始携带 policy refs，而 `weather-comparison-engine` 的 monitoring freshness 与 top-parameter canonical hooks 也已接上 registry-first 读取，dashboard / Telegram 则补齐了 policy-aware 只读展示。Phase 27.2 Batch 1 + 2 + 3 + 4 也已完成，`weather-rules-research` 的 forecast / extractor / poller 链路已升级为 normalization-aware schema，`ForecastSnapshot.v2` / `ObservationSnapshot.v2` / `TopParameterView.v2` 已形成统一的 raw / canonical / display + policy refs 语义链路。Phase 27.3 Batch 1 + 2 + 3 + 4 已完成，Observation Alert Layer 已切到 canonical-only 输入检查，`market_alert_event.v1`、`market_anomaly_event.v1` 与 `family_scan_report.v1` 已补齐 canonical-only 审计语义，并将 dashboard / Telegram / gateway 的监测展示分层为 `alert / anomaly / gate`，其中 Gate / Runtime Block 继续只读展示 gate 语义，不与监测异常混用，gateway 也已补齐 review context 作为审查背景但不改变执行许可，family scanner MVP 也已完成可运行、可审计收口。Phase 28.1 Batch 2 + Batch 3 + Batch 4 已完成，`feature store / validation loader` 已开始吸收 canonical-only schema，validation report / backtest report / calibration report 也已开始纳入 source / normalization governance 摘要与 policy refs，dashboard / Telegram 的只读验证摘要展示也已接入。Phase 28.2 已开始收口 family anomaly 的高阶解释层，`family_scan_report.v1` 与 `market_anomaly_event.v1` 已补齐 `signal_summary`、`anomaly_bucket` 和 `feature_breakdown`，dashboard / Telegram 的 family anomaly 区块也已开始显示可解释汇总。Phase 28.3 已开始收口 monitoring / ops / alert 联动展示，dashboard / Telegram 已增加 operator summary，把 market alert、family anomaly 和 gate block 合成一条 operator-facing 结论，并补充 summary line / next step 作为首屏短句。Phase 29.1 Batch 1 已完成，继续扩大 family 覆盖与校准反馈视图的仓库级任务拆分已经进入实现态。Phase 29.1 Batch 2 + Batch 3 + Batch 4 已完成，dashboard / Telegram 的 validation 面板与统一状态条已补齐 family rollout 摘要首屏，validation / backtest 反馈闭环开始在只读消费面可见。Phase 29.2 建议直接转向 coverage trend / family expansion / calibration drift backfill，在 validation / backtest 的同一套 canonical-only 口径上继续补齐更多 family 的 resolver 覆盖和趋势回放视图。Phase 29.2 Batch 1 已完成，`weather-comparison-engine` 已开始输出 family_rollout_trend_summary.v1，覆盖趋势与 drift movement 进入 validation / backtest / calibration 报告。Phase 29.2 Batch 2 已完成，dashboard / Telegram 的只读消费面已接入 coverage trend / drift movement 摘要，趋势回放开始可见。Phase 29.2 Batch 3 已完成，dashboard 的 family rollout trend 与 Telegram 的 /status validation trend 摘要已经稳定可见，operator 可以更早看到 coverage / ready / drift movement。Phase 29.2 Batch 4 已完成，回归测试与文档同步已收尾，Phase 29.2 可作为完成态继续进入下一阶段。Phase 29.3 建议顺势转向 coverage stall / drift watchlist / expansion backlog，在 Phase 29.2 的 trend history 上继续把“趋势”收敛成“该优先补哪几个 family”。Batch 1 + Batch 2 + Batch 3 + Batch 4 已完成，`weather-comparison-engine` 已开始输出 `family_rollout_watchlist.v1`，并将 watchlist history 接入 dashboard / Telegram 的只读消费面，可识别 stalled family、drift spike family 与 expansion backlog family；Batch 3 / Batch 4 已完成 dashboard / Telegram watchlist view 与回归 / 文档收口。这样可以保证离线验证、回测、校准与在线 canonical-only 链路同口径，同时逐步提升多 family 适配能力。
5. 持续扩展测试用例与需求回溯矩阵，确保新增 market family 与 operator 控制面保持稳定回归。

---



## 13. 总结

当前 AARS Polymarket Weather Trading Console 已经不是单一页面原型，而是一个具备：

- 实时链路
- 证据链路
- validation/monitoring 契约
- manual advisory 与 dry-run 执行闭环

的完整研究控制台 MVP。

系统最关键的进展，在于把 “market / resolver / probability / comparison / authorization / execution” 这些原本容易分散失真的环节，收敛成了统一状态语义和 operator 可解释界面。

后续工作的重点，不再是补齐最基础链路或继续铺 UI，而是在 Phase 24 收口 gate 单一真源、Phase 25 收口 automation ops、Phase 26 收口 promotion policy 的基础上，继续巩固外部稳定 contract 与运营闭环能力，并让 Telegram / gateway / dashboard 的 operator 语义保持一致。

Phase 30 已完成并收口为正式基线：validation assimilation 已接入 `validation_assimilation_summary.v1` 与 `validation_assimilation_report.json`，dashboard / Telegram 的验证与异常消费面已与 Opportunity Board、Single Market Workstation 对齐，后续若继续扩展，应以新 family 覆盖、异常解释增强和 operator workflow 细化为主。

Phase 31 已完成并收口为正式基线：系统已补齐持续运行的 market discovery、evidence scan、alert routing 与 scanner ops 监测链路，`market_universe_snapshot.v1`、`evidence_scan_snapshot.v1`、`scanner_status.v1`、`scanner_ops_alert.v1`、`market_alert_event.v1`、`market_anomaly_event.v2` 与 `alert_queue_status.v1` 已纳入 dashboard、Opportunity Board、Single Market Workstation 与 Telegram 的只读消费面；后续若继续扩展，应以更细的 dedupe / cooldown / ack 政策与更广的 family 覆盖为主。
