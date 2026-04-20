# AARS Polymarket Weather Trading Console 功能需求报告

版本：v0.1  
日期：2026-04-17  
关联文档：[AARS_Polymarket_Weather_Trading_Architecture.md](./AARS_Polymarket_Weather_Trading_Architecture.md)

---

## 1. 文档目的

本文档定义 AARS Polymarket Weather Trading Console 的功能需求、用户场景、核心业务流程、验收标准与非功能性要求。

系统目标是构建一个面向 Polymarket 天气 / 气候预测市场的实时交易研究与执行控制台，支持市场发现、规则解析、概率估计、盘口比较、交易建议、证据论证、BOT 授权、执行网关、训练验证和系统监控。

---

## 2. 业务目标

系统需要支撑以下核心业务目标：

1. 实时跟踪 Polymarket 天气 / 气候相关市场。
2. 自动解析市场规则，包括地点、气象站、变量、目标日期、结算规则和 band scheme。
3. 接入 ECMWF、HRRR、METAR、Wunderground、official obs 等天气 / 气候数据源。
4. 生成模型概率、fair value、forecast support score 和 confidence。
5. 比较市场隐含概率与模型 fair value，识别 edge、divergence 和历史变化。
6. 生成交易候选建议，包括 side、size、action_hint 和 reason_code。
7. 通过 XAI 证据链解释建议来源。
8. 通过 authorization gate 控制 BOT 自动执行权限。
9. 通过 execution gateway 输出 dry-run / order intent / order receipt。
10. 将实时数据沉淀为 feature store 和 label store，用于训练、回测、校准验证和模型注册。

---

## 3. 用户角色

### 3.1 操作员 Operator

职责：

- 查看当前市场状态。
- 搜索并固定关注市场。
- 审查 resolver、forecast、comparison 和 decision 证据。
- 授权或撤销 BOT 自动交易权限。
- 查看系统健康状态和执行记录。

### 3.2 研究员 Researcher

职责：

- 分析历史盘口与天气数据。
- 构建 feature / label 数据集。
- 回测 heuristic 和 trained model。
- 评估 calibration、ROI、drawdown 和 resolver coverage。

### 3.3 风控 / 审计 Risk Reviewer

职责：

- 检查 authorization gate 和 risk gate。
- 审查 decision / authorization / execution audit log。
- 确认自动执行是否满足策略、权限和数据新鲜度要求。

### 3.4 系统服务 Worker

职责：

- 采集 Polymarket 市场与盘口。
- 拉取天气 / 气候数据。
- 运行 resolver、probability、comparison、decision、monitoring 等后台任务。

---

## 4. 核心问题闭环

系统所有 UI 和后台链路必须持续回答五个问题：

1. 当前关注的是哪个市场？
2. 这个市场当前赔率和盘口状态是什么？
3. 模型 / resolver 对这个市场的支持证据是什么？
4. 市场赔率与模型判断是对齐还是背离，背离程度有多大？
5. 在当前证据和权限条件下，BOT 能不能自动执行？

---

## 5. 总体功能范围

```mermaid
flowchart TB
  A["01 Market Layer<br/>市场发现 / 盘口 / Watchlist"]
  B["02 Resolver Layer<br/>规则解析 / 气象站 / 变量"]
  C["03 Probability Layer<br/>fair value / model probability"]
  D["04 Comparison Layer<br/>edge / divergence / history"]
  E["05 Decision Layer<br/>side / size / action_hint"]
  F["06 XAI Layer<br/>证据论证 / 解释"]
  G["07 Authorization Layer<br/>BOT 授权 / 风控门禁"]
  H["08 Execution Layer<br/>dry-run / order intent"]
  I["09 Feature Store<br/>训练特征"]
  J["10 Label Store<br/>监督标签"]
  K["11 Training Validation<br/>回测 / 校准 / 训练"]
  L["12 Model Registry<br/>shadow / live 管理"]

  A --> B --> C --> D --> E --> F --> G --> H
  A --> I
  B --> I
  C --> I
  D --> I
  E --> I
  H --> I
  B --> J
  H --> J
  I --> K
  J --> K
  K --> L
  L --> C
  L --> E
```

---

## 6. 功能需求

### FR-01 市场发现与 Watchlist

系统应支持从 Polymarket Gamma API 和 CLOB 实时流中发现天气 / 气候市场。

功能要求：

- 支持 Gamma 搜索 Polymarket market。
- 支持模糊搜索 market question、market id、location、family。
- 支持将搜索结果加入 watchlist。
- 支持从 watchlist 删除市场。
- 支持 pin / unpin 当前市场。
- 支持 recent markets，记录最近选择时间和来源。
- 支持 watchlist 按 market family 分组和筛选。
- 支持 watchlist 按 resolver status、edge、freshness 进行联合筛选。
- 支持 fallback 到本地缓存，避免 Gamma 不可用时页面失效。

验收标准：

- 输入 “Shanghai temperature” 能返回或展示相关市场。
- 点击 Add to list 后，市场进入 watchlist，并刷新后仍然保留。
- 点击 Remove 后，市场从 watchlist 隐藏，并刷新后仍然不显示。
- Pin 状态可设置、取消和持久化。

---

### FR-02 Polymarket 实时盘口采集

系统应采集 Polymarket 实时盘口数据。

功能要求：

- 订阅 CLOB WebSocket asset ids。
- 维护 asset-level market state。
- 聚合 yes / no asset 为 market-level snapshot。
- 输出 market implied probability。
- 输出 yes_price、no_price、favored_side、spread、updated_at。
- 支持 market_realtime_snapshot 和 market_realtime_simple 输出。

验收标准：

- CLOB 更新后，market snapshot 文件更新时间变化。
- Dashboard 能显示最新 yes/no price 和 market probability。
- 当 CLOB 不可用时，系统显示 stale 或 unavailable，而不是页面空白。

---

### FR-03 Market Resolver

系统应解析 Polymarket market question，生成可计算的 MarketRule。

功能要求：

- 识别 market_family。
- 识别 location。
- 识别 target_date。
- 识别 variable_name。
- 匹配 station 或 official source。
- 输出 band_scheme。
- 输出 resolver_status 和 resolver_confidence。
- 输出 `required_sources`。
- 输出 `settlement_source_type`。
- 输出 `official_vs_proxy_source`。
- 输出 `source_match_grade`。
- 输出 `official_source_url`。
- 对 unmatched market 输出明确原因。

典型 market family：

- `temperature_daily_max`
- `temperature_daily_min`
- `precipitation_amount`
- `global_temperature_index`
- `sea_ice_extent`
- `hurricane_landfall`

验收标准：

- 上海温度市场应解析为 ZSPD / Shanghai Pudong Intl Airport / daily_max_temperature。
- 上海温度市场应输出 `official_vs_proxy_source=official`、`source_match_grade=exact_station`。
- 全球 hottest year 市场应解析为 global temperature index。
- 全球 hottest year 市场应输出 family-level resolver contract，而不是伪装成 exact station match。
- sea ice extent 市场应解析为对应 official sea ice extent 数据源。
- 未支持市场不得伪装为 matched，必须输出 `resolver_status=unmatched`。
- source 仅为 family-level 或 fallback 时，UI 和 gate 必须能识别并降级提示。

---

### FR-04 Weather Data Adapters

系统应根据 resolver 输出的数据需求拉取天气 / 气候数据。

功能要求：

- 支持 ECMWF / HRRR forecast adapter。
- 支持 METAR / official obs adapter。
- 支持 Wunderground station adapter。
- 支持 official climate index / sea ice dataset adapter。
- 所有外部请求不得阻塞 dashboard 首屏。
- 支持 cache-first、manual refresh 和 worker 异步刷新。

验收标准：

- 上海 ZSPD 数据可手动刷新并写入本地 cache。
- 页面首次加载不因 Wunderground / Gamma / weather API 卡住。
- 数据不可用时，UI 显示 source status 和 last_error。

---

### FR-05 Probability Layer

系统应生成模型概率和 fair value。

功能要求：

- 接收 MarketSnapshot、MarketRule、ForecastSnapshot、ObservationSnapshot。
- 输出 `model_probability`。
- 输出 `fair_value`。
- 输出 `forecast_support_score`。
- 输出 `confidence`。
- 标注 `calibration_status`。
- 支持 heuristic mode、shadow model mode、live model mode。

验收标准：

- 当前 heuristic 概率必须标注 `not_calibrated`。
- Fair value 必须与 market implied probability 区分显示。
- 若 resolver unmatched，则 probability layer 不得输出误导性 fair value。

---

### FR-06 Comparison Layer

系统应比较 market implied probability 与 model fair value。

功能要求：

- 计算 edge。
- 计算 confidence_adjusted_edge。
- 计算 band_distance。
- 判断 divergence_status。
- 追加 comparison history。
- 对相同 market 的重复点做去重。
- 限制每个 market 的历史点数量。
- 支持历史赔率 vs forecast / official value 可视化。

验收标准：

- Comparison history 按 market_id 独立去重。
- 同一 market 重复状态不会无限追加。
- Dashboard 能显示 edge / divergence / history trend。

---

### FR-07 Decision Layer

系统应生成交易候选建议。

功能要求：

- 输出 recommended side。
- 输出 size 建议。
- 输出 action_hint。
- 输出 reason_code。
- 输出 decision_status。
- 支持 heuristic decision。
- 支持 trained model shadow decision。
- 支持 decision audit log。

验收标准：

- Decision layer 不直接触发真实交易。
- UI 中必须显示“决策辅助，不是校准概率”。
- 当数据 stale、resolver unmatched、risk blocked 时，action_hint 应为 WAIT / BLOCK。

---

### FR-08 XAI Layer

系统应提供可解释证据链。

功能要求：

- 输出 EvidenceBundle。
- 输出 ArgumentTrace。
- 支持三层解释：结论、物理证据、孪生推演。
- 规程步应与证据层绑定。
- XAI 应解释 resolver、probability、comparison、decision 的来源。

验收标准：

- 操作员能看到“为什么建议 YES / NO / WAIT”。
- 操作员能看到 station、variable、target date、source、confidence。
- XAI 不应改变决策，只解释决策。

---

### FR-09 Authorization Layer

系统应支持 BOT 自动交易授权和风控门禁。

功能要求：

- 支持 operator authorize / revoke。
- 授权状态持久化。
- Risk gate 检查 resolver status、data freshness、liquidity、spread、confidence、execution gateway health。
- 输出 can_execute。
- 输出 block_reasons。
- 授权只代表允许 BOT 自动执行，不代表模型判断正确。

验收标准：

- 未授权时 BOT 不可执行。
- 已授权但 risk gate 不通过时 BOT 仍不可执行。
- UI 明确显示 block reason。

---

### FR-10 Execution Layer

系统应通过执行网关提交 dry-run 或真实订单意图。

功能要求：

- 支持 dry-run mode。
- 支持 order intent。
- 支持 order receipt。
- 支持 execution audit log。
- 执行层只消费通过 authorization gate 的动作。

验收标准：

- 默认执行模式为 dry-run。
- 未通过 gate 的决策不会产生 order intent。
- 每次执行动作必须可审计。

---

### FR-11 Dashboard

系统应提供交易台式 Dashboard。

功能要求：

- 顶部显示当前市场、盘口、resolver、forecast、comparison、BOT 状态。
- 主区域回答五个核心问题。
- Markets tab 支持搜索、watchlist、recent、pin、remove。
- Command tab 应提供 compact gate stack，聚合 alignment / probability contract / execution gate 状态。
- Detailed execution controls 应折叠或迁移到次级视图，避免首屏过长。
- Current Analysis tab 显示 comparison focus、trade decision、live status、history / forecast。
- Charts tab 显示 comparison table、divergence chart、timeseries。
- History tab 显示 timeline 和 odds vs forecast / official value。
- Evidence tab 显示 bias summary、rule station、raw JSON。
- 外部数据刷新应局部化，不应全页面阻塞。

验收标准：

- 页面首次打开不空白。
- 数据源不可用时显示 fallback / cache / stale，而不是崩溃。
- 操作员能在一个页面内掌握当前状态。
- 操作员能在 Markets tab 内通过 family / resolver / edge / freshness 快速缩小 watchlist。

---

### FR-12 Telegram Console

系统应支持 Telegram 作为通知和 human-in-loop 通道。

功能要求：

- 推送 market alert。
- 推送 divergence alert。
- 推送 BOT authorization request。
- 推送 execution dry-run / receipt。
- 支持 `/status` 展示 unified status 与 probability contract。
- 支持 `/market [market_id]` 展示市场摘要、snapshot refs 与 manual advisory 状态。
- 支持 `/timeline [market_id]` 展示比较历史。
- 支持人工确认或拒绝。

验收标准：

- Telegram 不直接绕过 authorization gate。
- Telegram 操作必须进入 audit log。
- Telegram 默认 market 应跟随 dashboard `operator_market_context.json`。
- Telegram 必须展示并传递 `probability_contract.v1`，但不得单独放开交易。

---

### FR-13 Feature Store

系统应沉淀训练特征。

功能要求：

- 存储 market_features。
- 存储 orderbook_features。
- 存储 resolver_features。
- 存储 weather_features。
- 存储 probability_features。
- 存储 comparison_features。
- 存储 decision_features。
- 存储 execution_features。
- 每条特征必须包含 feature_time、source、schema_version。

验收标准：

- 可以基于 feature store 构建 point-in-time safe dataset。
- 不允许训练样本使用未来数据。

---

### FR-14 Label Store

系统应沉淀监督标签。

功能要求：

- 支持 weather outcome label。
- 支持 market settlement label。
- 支持 price movement label。
- 支持 trade PnL label。
- 标签必须记录 label_time、source、resolved_at。

验收标准：

- Polymarket 盘口数据不得直接当作真实 outcome 标签。
- official obs / settlement value 必须与 market_id 或 rule_id 可关联。

---

### FR-15 Training / Validation

系统应支持训练、回测和验证。

功能要求：

- 构建 point-in-time safe dataset。
- 支持 heuristic 回测。
- 支持概率模型训练。
- 支持 calibration evaluation。
- 支持 strategy evaluation。
- 支持 shadow model 对比。
- 输出 validation report。

验收标准：

- 每个模型必须有 validation metrics。
- 未通过验证的模型不得 live。
- 回测报告必须包含 ROI、max drawdown、calibration error。

---

### FR-16 Model Registry

系统应支持模型注册和部署模式控制。

功能要求：

- 记录 model_id、model_type、features_version、training_range、validation_metrics。
- 支持 offline_only / shadow / live。
- 支持 approved_for_live 标记。
- 支持模型回滚。

验收标准：

- 只有 approved_for_live 的模型可以进入 live decision。
- Shadow model 不影响真实 BOT 执行。

---

### FR-17 Monitoring

系统应提供监视层。

功能要求：

- 输出 worker health。
- 输出 data freshness。
- 输出 source status。
- 输出 resolver coverage。
- 输出 comparison freshness。
- 输出 execution gateway health。
- Dashboard 顶部展示监控状态。

验收标准：

- 任一 worker 失效时，dashboard 显示 warning。
- 任一数据源 stale 时，dashboard 显示 freshness。
- 监控状态不得依赖 dashboard 才能生成。

---

### FR-18 Gate Stack External Contract / Automation Summary

系统应对外输出稳定的 gate contract 与 automation summary，供 dashboard / telegram / gateway / scheduler 统一消费。

功能要求：

- 输出 `gate_stack_api.v1`。
- 输出 `gate_stack_automation_summary.v1`。
- `gate_stack_api` 支持多市场视图（`market_gate_views`）。
- 输出 `severity`、`recommended_operator_action`、`primary_block_reason`。
- `run-gate-stack-automation-check` 支持 `fail-on-signal` 退出码策略。

验收标准：

- 无 unified status 直连时，telegram 与 gateway 仍可消费 gate API。
- scheduler 可仅根据退出码判断是否命中阻断阈值。
- 多市场情况下可按 market_id 定位 gate 结果。

### FR-19 Ops Alert Bridge / Queue Lifecycle

系统应支持把运行时 red 告警桥接到 Telegram 可消费队列，并维护发送与回执状态。

功能要求：

- comparison-engine 输出 `gate_stack_ops_alert.v1` JSONL 事件。
- telegram bridge 能把 alert 转换为 `telegram_ops_notification.v1` 队列。
- 支持去重状态文件，避免重复告警风暴。
- 支持 lifecycle 状态流转：`pending -> sent -> acked`。
- 记录 delivery log（sent/acked 事件）用于审计。

验收标准：

- 重复 alert 不应重复入队。
- 分发后通知状态应更新为 sent，并记录 sent 事件。
- 回执后通知状态应更新为 acked，并记录 acked 事件。

## 7. 非功能需求

### NFR-01 可用性

- Dashboard 首屏不得被外部请求阻塞。
- 外部 API 失败时必须降级显示。
- JSON / DB 文件缺失时应有 fallback 或明确提示。

### NFR-02 可审计性

- decision、authorization、execution 必须有 audit log。
- 每个模型输出应能追溯 model_id 和 feature version。
- 每个 resolver 输出应能追溯 rule version。

### NFR-03 可扩展性

- 新 market family 应通过 resolver plugin 接入。
- 新 weather source 应通过 adapter 接入。
- 新模型应通过 model registry 接入。

### NFR-04 安全性

- 真实 execution credentials 不得写入代码或普通 JSON。
- BOT 默认 dry-run。
- Authorization 和 risk gate 必须在 execution 前强制执行。

### NFR-05 性能

- Dashboard 首屏目标加载时间小于 3 秒。
- 局部刷新不应导致整页闪烁。
- 历史数据应分页或按 market_id 筛选加载。

### NFR-06 数据质量

- 所有 snapshot 应包含 timestamp。
- 所有实时数据应包含 freshness status。
- 训练数据必须 point-in-time safe。

---

## 8. MVP 验收清单

MVP 应至少满足：

- 能搜索并加入 Polymarket market。
- 能 pin / unpin / remove watchlist market。
- 能实时显示 market probability。
- 能解析至少三个 market family：Shanghai temperature、global temperature index、sea ice extent。
- 能输出 MarketRule。
- 能输出 ForecastSnapshot。
- 能输出 ProbabilityState。
- 能输出 ComparisonPoint。
- 能输出 TradeDecision。
- 能显示 XAI EvidenceBundle。
- 能显示 BOT 授权状态和 block reason。
- Execution 默认为 dry-run。
- 能输出 monitoring_status.json。
- 能沉淀 feature / label 基础表。
- 能生成一次 heuristic backtest report。

---

## 9. 范围外事项

当前阶段不承诺：

- 真实资金自动交易。
- 完全校准的概率模型。
- 所有 Polymarket 天气市场全覆盖。
- 所有官方气象数据源完整接入。
- 高频交易级别 order book 策略。
- 无人工审核的生产执行。

---

## 10. 风险与依赖

主要风险：

- Resolver coverage 不足。
- Weather source 数据延迟或不可用。
- Market liquidity 低导致 edge 不可交易。
- Heuristic probability 被误解为 calibrated probability。
- 训练数据存在 look-ahead bias。
- BOT 授权语义与真实执行混淆。

关键依赖：

- Polymarket Gamma API / CLOB。
- Weather / climate 数据源。
- Resolver rulebook。
- Feature / label store。
- Monitoring worker。
- Execution gateway。

---

## 11. 总结

本功能需求报告定义了从实时市场分析到模型训练验证、从 XAI 解释到 BOT 授权执行的完整功能范围。

系统应优先保证：

1. 市场与 resolver 对齐准确。
2. Dashboard 稳定可用。
3. Probability 与 decision 明确标注未校准状态。
4. BOT 执行必须经过 authorization gate 和 risk gate。
5. 实时数据必须沉淀为可训练、可验证、可审计的数据资产。
