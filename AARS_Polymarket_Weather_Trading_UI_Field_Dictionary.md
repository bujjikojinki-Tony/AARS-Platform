# AARS Polymarket Weather Trading UI Field Dictionary

Version: `dashboard_ui_field_dictionary.v1`

本字典用于统一 dashboard / Telegram / gateway / worker 文档中的 UI 术语，尤其覆盖近期 Command、Trade Decision、Compact Gate Stack、Live Status、Validation 信息降噪重构后新增或显性化的字段。

原则：

- 同一个字段在不同页面必须使用同一含义。
- UI 显示名可以短，但文档字段名必须稳定。
- 操作页默认展示关键字段；诊断页可以展示完整 contract。
- `Status` 不单独使用，必须带上下文，例如 `Gate Status`、`Coverage Status`、`Rule Status`。

---

## 1. Execution / Gate 字段

| 字段名 | 统一显示名 | 定义 | 允许值 / 格式 | 主要来源 | 默认展示位置 |
|---|---|---|---|---|---|
| `gate_status` | Gate Status | 当前市场顶层执行就绪状态。回答“现在整体能不能进入执行链”。 | `READY` / `DRY_RUN_INTENT_READY` / `BLOCKED` | compact gate stack / execution gate | Page Focus、Command.Execution、Compact Gate Stack |
| `execution_gate` | Execution Gate | 执行层最终 gate，消费上游 data/probability/freshness/authorization 后给出执行是否放行。 | `pass` / `blocked` | `gate_stack_api.v1` 或 local gate builder | Command.Execution、Compact Gate Stack internals |
| `authorization_gate` | Authorization Gate | operator 授权与策略 gate。回答“BOT 是否被授权动作”。 | `pass` / `blocked` | authorization layer / gate stack | Command.Execution |
| `primary_blocker` | Primary Blocker | 第一条最需要 operator 处理的阻断原因。 | block reason token / `none` | gate blockers | Command.Execution、Compact Gate Stack |
| `block_reasons` | Block Reasons | 所有阻断原因列表，用于审计和诊断。 | list of tokens | gate stack / unified status | Page Focus、diagnostics |
| `recommended_operator_action` | Next Action | 由 blocker 推导出的下一步操作建议。 | `hold_execution_and_review` / `refresh_pipeline_inputs` / `review_resolver_contract` / `allow_live_execution` 等 | gate stack API / compact gate stack | Page Focus、Command.Telegram、Compact Gate Stack |
| `gate_source` | Gate Source | 当前 gate 摘要来自哪里。 | `api` / `unified_fallback` / `local_fallback` | dashboard gate consumer | Page Focus、Pipeline、Evidence |
| `severity` | Severity | gate 或 alert 的严重程度。 | `low` / `medium` / `high` / `critical` | gate stack API / alert contract | Page Focus |

---

## 2. Probability 字段

| 字段名 | 统一显示名 | 定义 | 允许值 / 格式 | 主要来源 | 默认展示位置 |
|---|---|---|---|---|---|
| `probability_mode` | Probability Mode | 概率层可信度和 promotion 状态。它不等于交易许可，只说明概率层处在哪个阶段。 | `heuristic_not_calibrated` / `shadow_calibrated_candidate` / `live_approved` | `probability_contract.v1` | Page Focus、Command.Probability、Validation |
| `execution_constraint` | Execution Constraint | probability contract 允许的最高执行级别。 | `manual_advisory_only` / `dry_run_only` / `live_execution_allowed` | `probability_contract.v1` | Page Focus、Command.Probability、Trade Decision.Constraint |
| `edge` / `confidence_adjusted_edge` | Edge | 置信度调整后的模型观点与市场隐含概率差。正值通常表示模型相对市场更看好 favored side。 | decimal probability difference | probability state | Command.Probability、Trade Decision |
| `market_probability` | Market Probability | Polymarket 当前 favored side 的市场隐含概率。 | `0.00-1.00` | market snapshot | Command.Probability、Trade Decision、Live Status |
| `calibration_status` | Calibration Status | 概率模型校准状态，是 probability promotion 的输入。 | `not_calibrated` / `calibrated` / `stale` / `live_approved` | validation report / probability contract | Validation.Promotion |

---

## 3. Evidence / Comparison 字段

| 字段名 | 统一显示名 | 定义 | 允许值 / 格式 | 主要来源 | 默认展示位置 |
|---|---|---|---|---|---|
| `comparison_status` | Comparison Status | 市场 band 与 forecast/model band 的一致性状态。 | `aligned` / `mild_divergence` / `strong_divergence` / `unmatched_rule` / `market_mismatch` | comparison engine | Command.Evidence、Trade Decision.Evidence |
| `confidence_adjusted_gap` | Adjusted Gap | 经置信度调整后的 forecast/market 差距。 | numeric gap | comparison row | Page Focus、Command.Evidence、History |
| `resolver_gate` | Resolver Gate | resolver contract 是否 matched 且足够精确。 | `pass` / `blocked` | resolver contract / gate stack | Command.Evidence、Pipeline |
| `freshness_gate` | Freshness Gate | market / forecast / comparison / validation 等输入是否足够新鲜。 | `pass` / `blocked` | unified status / gate stack | Command.Evidence、Pipeline、Validation |
| `band_distance` | Band Distance | market band 与 model band 的离散距离。 | number / `-` | comparison row | Trade Decision details |
| `model_band` | Model Band | forecast 计算出的模型 band。 | band label | forecast snapshot | Live Status、Trade Decision details |
| `market_band` | Market Band | Polymarket 市场隐含或解析出的 band。 | band label | market snapshot | Trade Decision details |

---

## 4. Account / Exposure 字段

| 字段名 | 统一显示名 | 定义 | 允许值 / 格式 | 主要来源 | 默认展示位置 |
|---|---|---|---|---|---|
| `exposure_limit_status` | Exposure Status | 当前账户 exposure 是否在配置限额内。 | `within_limit` / `near_limit` / `over_limit` / `missing_snapshot` / `unknown` | read-only account snapshot / production readiness | Command.Account |
| `market_notional` | Market Exposure | 当前选中市场的 position notional + open order notional。 | currency amount | read-only account snapshot | Command.Account |
| `market_limit_usage` | Market Usage | 当前市场 exposure 占单市场限额比例。 | percentage | account snapshot + readiness limits | Command.Account |
| `total_limit_usage` | Total Usage | 全账户 exposure 占总限额比例。 | percentage | account snapshot + readiness limits | Command.Account |
| `manual_order_only` | Manual Order Only | 账户快照是否只允许人工观察，不开放自动私钥执行。 | boolean | account snapshot | Account diagnostics |

---

## 5. Telegram / Operator Context 字段

| 字段名 | 统一显示名 | 定义 | 允许值 / 格式 | 主要来源 | 默认展示位置 |
|---|---|---|---|---|---|
| `market_id` | Market ID | 当前 UI / Telegram / gate 共同指向的 Polymarket 市场 ID。 | string | market snapshot / operator context | Page Focus、Command.Telegram、Live Status |
| `selection_source` | Selection Source | 当前 operator market context 是如何选中的。 | `watchlist` / `pinned` / `search` / `telegram` / `local` 等 | operator market context | Command.Telegram |
| `action_hint` | Action Hint | 对当前市场的轻量操作提示。 | `review` / `wait` / `refresh` / `approve_dry_run` / `hold` 等 | operator context / comparison row | Command.Telegram diagnostics |
| `generated_at` | Generated At | contract、context 或报告生成时间。 | ISO-8601 timestamp | contract payload | Command.Telegram、Evidence |

---

## 6. Live Status 字段

| 字段名 | 统一显示名 | 定义 | 允许值 / 格式 | 主要来源 | 默认展示位置 |
|---|---|---|---|---|---|
| `value` | Forecast Value | 当前 forecast/resolver 输出的核心数值。 | numeric / string | forecast snapshot | Live Status.Forecast |
| `rule_status` | Rule Status | forecast resolver rule 是否匹配当前市场。 | `matched` / `matched_index` / `matched_snapshot` / `unmatched` / `unknown` | forecast / resolver snapshot | Live Status.Forecast |
| `target_date` | Target Date | 市场对应的天气目标日期或结算目标日期。 | date / market-specific date | market / forecast snapshot | Live Status.Forecast |
| `comparison_hint` | Comparison Hint | resolver 指导 comparison layer 如何比较 forecast value 与 market band。 | threshold/band hint | resolution snapshot | Live Status.Resolver |
| `expected_band` | Expected Band | resolver 预期 band，供 comparison layer 使用。 | band label | resolution snapshot | Live Status.Resolver |
| `resolution_scope` | Resolution Scope | resolver 匹配粒度。 | station / location / family / global 等 | forecast snapshot | Live Status.Resolver |
| `required_data_source` | Required Source | resolver 要求的数据源。 | source id | resolver source contract | Live Status.Resolver |

---

## 7. Trade Decision 字段

| 字段名 | 统一显示名 | 定义 | 允许值 / 格式 | 主要来源 | 默认展示位置 |
|---|---|---|---|---|---|
| `favored_side` | Favored Side | 当前市场价格隐含更可能的一侧。 | `yes` / `no` / market-specific | market snapshot | Trade Decision.Market Price |
| `yes_price` | YES Price | YES token 当前价格。 | decimal price | market snapshot | Trade Decision.Market Price |
| `no_price` | NO Price | NO token 当前价格。 | decimal price | market snapshot | Trade Decision.Market Price |
| `recommended_side` | Recommended Side | heuristic decision aid 给出的推荐方向。 | `yes` / `no` / `contrarian` / `-` | dashboard decision helper | Trade Decision.Decision |
| `heuristic_choice_probability` | Heuristic Choice | heuristic decision aid 的选择概率。不是 calibrated probability。 | `0.00-1.00` | dashboard decision helper | Trade Decision.Decision |
| `support_score` | Forecast Support | forecast 与市场方向的一致支持度。 | `0.00-1.00` | dashboard decision helper | Trade Decision.Decision |
| `confidence_score` | Forecast Confidence | forecast snapshot 的置信度。 | `0.00-1.00` | forecast / comparison row | Trade Decision.Decision |
| `contrarian_probability` | Counter Probability | 与 heuristic choice 相反方向的概率提示。 | `0.00-1.00` | dashboard decision helper | Trade Decision details |
| `can_live` | Can Live | probability constraint 是否允许 live execution。 | `yes` / `no` | derived from `execution_constraint` | Trade Decision.Constraint |

---

## 8. Validation 字段

| 字段名 | 统一显示名 | 定义 | 允许值 / 格式 | 主要来源 | 默认展示位置 |
|---|---|---|---|---|---|
| `approved_for_live` | Approved For Live | validation policy 是否允许 live promotion。 | boolean | model validation report | Validation.Promotion |
| `deployment_mode` | Deployment Mode | 当前 probability/model 部署模式。 | `manual_advisory` / `shadow` / `dry_run` / `live` | model validation report | Validation.Promotion |
| `labeled_sample_count` | Labeled Samples | 已具备 official label 的样本数量。 | integer | validation / label coverage | Validation.Coverage |
| `labeled_ratio` | Labeled Ratio | tracked samples 中已标注样本占比。 | `0.00-1.00` | label coverage report | Validation.Coverage |
| `minimum_labeled_rows` | Minimum Labeled Rows | promotion policy 要求的最低 labeled sample 数量。 | integer | label coverage report | Validation.Coverage |
| `validation_freshness_status` | Validation Freshness | validation report 是否足够新鲜。 | `healthy` / `warning` / `blocked` / `stale` | validation freshness report | Validation.Freshness |
| `freshness_seconds` | Freshness Age | report 或 worker 输出距当前时间的秒数。 | integer seconds | freshness report / monitoring status | Validation.Freshness |
| `sample_count` | Samples | validation 样本总数。 | integer | model validation report | Validation.Freshness |
| `brier_score` | Brier Score | 概率预测均方误差，越低越好。 | number | model validation report | Validation.Model Quality |
| `calibration_error` | Calibration Error | 预测概率与实际频率偏差，越低越好。 | number | model validation report | Validation.Model Quality |
| `hit_rate` | Hit Rate | 回测/验证命中率。 | `0.00-1.00` | validation / backtest report | Validation.Model Quality |
| `roi_backtest` | Backtest ROI | 回测 ROI。 | decimal return | validation / backtest report | Validation.Model Quality |
| `resolver_match_rate` | Resolver Match Rate | validation 样本中 resolver matched 的比例。 | `0.00-1.00` | resolver quality report | Validation.Resolver |
| `unmatched_count` | Unmatched Count | resolver 未匹配的样本或市场数量。 | integer | resolver quality report | Validation.Resolver |
| `backtest_trade_count` | Backtest Trades | 回测中触发交易样本数。 | integer | backtest report | Validation.Resolver |
| `backtest_roi` | Backtest ROI | backtest report 直接输出的 ROI。 | decimal return | backtest report | Validation.Resolver |

---

## 9. UI 卡片命名规范

| 卡片 | 用途 | 禁止事项 |
|---|---|---|
| `Execution` | 只回答能不能执行和第一阻断原因 | 不展示完整 blocker list |
| `Probability` | 只回答 probability contract 允许到哪一步 | 不把 heuristic 当作 live probability |
| `Evidence` | 只回答 forecast/market/resolver 是否支持当前判断 | 不展示 raw rows |
| `Account` | 只回答 exposure 是否安全 | 不展示完整 account id 和所有 positions |
| `Telegram` | 只回答远程 operator context 是否一致 | 不展示完整 context payload |
| `Trade Decision` | 只作为 decision aid | 不宣称 calibrated model 或 live permission |
| `Live Status` | 只展示 market/forecast/resolver 当前状态 | 不默认展示 raw resolver JSON |
| `Validation` | 只回答能否 promotion 以及卡在哪里 | 不默认展示 curve/decile/raw report |

---

## 10. 禁用/避免的模糊术语

| 避免使用 | 替代术语 | 原因 |
|---|---|---|
| `Status` | `Gate Status` / `Rule Status` / `Coverage Status` | 单独的 status 缺少上下文 |
| `Probability` | `Probability Mode` / `Market Probability` / `Model Probability` | probability 有 contract、市场价、模型值三种含义 |
| `Ready` | `Gate Status=READY` / `Can Live=yes` / `Can Promote=yes` | ready 必须说明是哪一层 ready |
| `Blocked` | `Primary Blocker` + `Block Reasons` | blocked 必须给出原因 |
| `Action` | `Next Action` / `Action Hint` | action 要区分 gate 推荐与市场上下文提示 |
| `Freshness` | `Freshness Gate` / `Validation Freshness` / `Freshness Age` | freshness 可能指 gate、validation 或 worker age |

