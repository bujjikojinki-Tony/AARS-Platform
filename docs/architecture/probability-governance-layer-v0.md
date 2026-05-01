# Probability_Governance_Layer_v0

## 1. Layer 定位

Probability Governance Layer v0

它不是单个概率模型，而是一个治理层：

WeatherView
→ Probability Engine Registry
→ Primary / Shadow Engine Runs
→ Probability Comparison
→ Calibration Metrics
→ Promotion Gate
→ Active Probability Decision

它回答的问题是：

当前用于交易判断的 `model_probability` 是否来自被允许的 active engine？
shadow engine 的结果是否被记录但不驱动交易？
不同概率引擎之间是否存在明显分歧？
市场结算后，概率预测是否被校准评估？
模型是否具备晋升为 primary 的证据？

## 2. 在整体系统中的位置

### 2.1 PWB-01 / PWB-02 / PWB-03 关系

PWB-01 — Execution Core
market scan → signal → candidate → risk gate → simulation

PWB-02 — Weather Intelligence
question → evidence → weather view → gaussian probability

PWB-03 — Probability Governance
gaussian + shadow engines → comparison → calibration → promotion decision

### 2.2 调用位置

MarketSnapshot
  ↓
WeatherProbabilityProvider
  ↓
WeatherView
  ↓
ProbabilityGovernanceLayer
  ↓
ProbabilityComparisonView
  ↓
Active probability remains gaussian_v0 in PWB-03

## 3. 核心原则

### 3.1 Active / Shadow 分离

PRIMARY engine 可以驱动 active_probability。
SHADOW engine 只能记录和比较，不能驱动交易。
DISABLED engine 不运行。

PWB-03 默认：

gaussian_v0 = PRIMARY
deb_shadow_v0 = SHADOW
emos_shadow_v0 = SHADOW

### 3.2 不改变 PWB-02 active behavior

PWB-02 已接受：

WeatherView → GaussianProbabilityEngine → ProbabilityView

PWB-03 增加治理与比较，但不改变默认执行链：

active_probability = gaussian_v0

也就是说：

PWB-03 可以显示 shadow probability
但不能让 shadow probability 直接触发交易信号

### 3.3 证据不足不晋升

任何 shadow engine 在证据不足时都必须保持 shadow：

evidence_count < minimum_evidence_count
→ NEEDS_MORE_DATA

### 3.4 晋升不自动执行

即便 promotion gate 输出 PROMOTE，PWB-03 也只记录决策，不自动修改 engine config。

`PromotionDecision` ≠ `EngineConfig` mutation

## 4. Layer 内部结构

L1 — Engine Registry
L2 — Engine Runner
L3 — Comparison Builder
L4 — Calibration Metrics
L5 — Outcome Handling
L6 — Promotion Gate
L7 — Governance API / UI

## 5. L1 — Engine Registry

### 5.1 目标

统一管理概率引擎。

engine_id
engine_type
enabled
can_be_primary
version
default_params
description

### 5.2 默认引擎

gaussian_v0
  type = PRIMARY
  enabled = true
  can_be_primary = true

deb_shadow_v0
  type = SHADOW
  enabled = true
  can_be_primary = false

emos_shadow_v0
  type = SHADOW
  enabled = true
  can_be_primary = false

### 5.3 Registry 输出

get_enabled_engines()
get_primary_engine()
get_shadow_engines()
get_engine_config(engine_id)

### 5.4 禁止行为

shadow engine 不可作为 active engine
disabled engine 不可运行
can_be_primary=false 不可晋升为 primary

## 6. L2 — Engine Runner

### 6.1 输入

WeatherView

### 6.2 输出

ProbabilityEngineRun[]

### 6.3 运行逻辑

1. 从 Registry 读取 enabled engines
2. 对 WeatherView 运行 gaussian_v0
3. 对 WeatherView 运行 deb_shadow_v0
4. 对 WeatherView 运行 emos_shadow_v0
5. 每个结果写入 `ProbabilityEngineRun`
6. 保存到 SQLite

### 6.4 ProbabilityEngineRun

run_id
market_id
weather_view_id
engine_id
engine_type
model_probability
expected_value
sigma
threshold
direction
params
warnings
created_at

### 6.5 强约束

EngineRunner 不生成 `StrategySignal`
EngineRunner 不触发 Execution
EngineRunner 不改变 active engine

## 7. L3 — Comparison Builder

### 7.1 输入

`ProbabilityEngineRun[]`

### 7.2 输出

`ProbabilityComparisonView`

### 7.3 逻辑

active run = PRIMARY engine run
active_probability = primary run probability
spread = max(probabilities) - min(probabilities)
disagreement_level = based on spread

### 7.4 Disagreement Level

NONE   spread < 0.03
LOW    spread < 0.08
MEDIUM spread < 0.15
HIGH   spread >= 0.15

### 7.5 ProbabilityComparisonView

comparison_id
market_id
weather_view_id
active_engine_id
active_probability
engine_runs
spread_between_engines
disagreement_level
selection_reason
warnings
created_at

### 7.6 解释规则

示例：

Selection reason:
gaussian_v0 selected because it is the only PRIMARY engine accepted in PWB-03.

Warning:
shadow engines are for comparison only and do not drive trading.

## 8. L4 — Calibration Metrics

### 8.1 输入

`predicted_probability`
`actual_outcome`

### 8.2 Brier Score

brier = (predicted_probability - actual_outcome)^2

示例：

predicted_probability = 0.7
actual_outcome = 1
brier = 0.09

### 8.3 Absolute Error

absolute_error = abs(predicted_probability - actual_outcome)

示例：

predicted_probability = 0.7
actual_outcome = 1
absolute_error = 0.3

### 8.4 Probability Bucket

0.0-0.2
0.2-0.4
0.4-0.6
0.6-0.8
0.8-1.0

## 9. L5 — Outcome Handling

### 9.1 MarketOutcome

PWB-03 只支持手动录入 outcome。

market_id
resolved_value
resolved_direction_hit
official_source
resolved_at
status
notes

### 9.2 Outcome Status

PENDING
RESOLVED
DISPUTED
UNKNOWN

### 9.3 Calibration 触发条件

只有 status = RESOLVED
且 resolved_direction_hit 非空
才允许生成 CalibrationResult

## 10. L6 — Promotion Gate

### 10.1 输入

engine_id
engine_config
calibration_results

### 10.2 默认门槛

minimum_evidence_count = 30
max_avg_brier_score = 0.20
max_avg_absolute_error = 0.35

### 10.3 输出

`EnginePromotionDecision`

### 10.4 决策类型

PROMOTE
KEEP_SHADOW
DISABLE
NEEDS_MORE_DATA
KEEP_PRIMARY

### 10.5 决策规则

if engine is PRIMARY:
  KEEP_PRIMARY

if evidence_count < minimum_evidence_count:
  NEEDS_MORE_DATA

if can_be_primary = false:
  KEEP_SHADOW

if avg_brier_score > max_avg_brier_score:
  KEEP_SHADOW

if avg_absolute_error > max_avg_absolute_error:
  KEEP_SHADOW

else:
  PROMOTE

### 10.6 PWB-03 默认预期

gaussian_v0 → KEEP_PRIMARY
deb_shadow_v0 → NEEDS_MORE_DATA 或 KEEP_SHADOW
emos_shadow_v0 → NEEDS_MORE_DATA 或 KEEP_SHADOW

## 11. L7 — Governance API / UI

### 11.1 API

GET  /api/probability/engines
POST /api/probability/compare/{market_id}
GET  /api/probability/comparison/{market_id}
POST /api/probability/outcomes
GET  /api/probability/outcomes/{market_id}
POST /api/probability/calibrate/{market_id}
GET  /api/probability/calibration/{engine_id}
POST /api/probability/promotion/{engine_id}
GET  /api/probability/promotion/{engine_id}

### 11.2 Workstation UI

新增：

Probability Comparison Panel

展示：

active_engine_id
active_probability
gaussian_v0 probability
deb_shadow_v0 probability
emos_shadow_v0 probability
spread_between_engines
disagreement_level
selection_reason
warnings

### 11.3 History UI

新增：

Calibration History Panel

展示：

market_id
engine_id
predicted_probability
actual_outcome
brier_score
absolute_error
bucket
created_at

### 11.4 Settings UI

新增：

Probability Engine Registry

展示：

engine_id
engine_type
enabled
can_be_primary
version
description

## 12. PWB-03 与交易执行的关系

### 12.1 可以做

记录多个概率引擎输出
比较 active/shadow 概率
显示 disagreement level
给人类审查参考
记录校准结果
生成 promotion decision

### 12.2 不可以做

用 shadow probability 生成交易信号
用 shadow probability 绕过 RiskManager
自动把 shadow engine 升为 primary
触发 live execution
改变 position sizing

## 13. 稳定接口

### 13.1 输入接口

`WeatherView`

来自 PWB-02。

### 13.2 输出接口

`ProbabilityComparisonView`
`CalibrationResult`
`EnginePromotionDecision`

### 13.3 向 PWB-01/PWB-02 保持兼容

PWB-01 / PWB-02 已有路径：

ProbabilityView.model_probability
→ WeatherEdgeStrategy
→ StrategySignal
→ OpportunityCandidate

PWB-03 不替换该路径，只在旁路增加治理信息：

`ProbabilityComparisonView`
`CalibrationResult`
`PromotionDecision`

## 14. 数据库表

PWB-03 接受新增表：

probability_engine_configs
probability_engine_runs
probability_comparisons
market_outcomes
calibration_results
engine_promotion_decisions

## 15. 关键审查问题

代码 review 时必须检查：

1. gaussian_v0 是否仍是唯一 primary？
2. shadow engines 是否不能驱动 StrategySignal？
3. comparison 是否只选择 primary active probability？
4. promotion gate 是否只生成 decision，不直接改 config？
5. calibration 是否只在 RESOLVED outcome 后执行？
6. LIVE_EXECUTE 是否仍被拒绝？

## 16. PWB-03 验收基线

验收通过需满足：

1. 默认 engine configs 初始化完成。
2. Registry 返回 primary + shadow engines。
3. Runner 可生成 engine runs。
4. Comparison 可生成 active probability + disagreement level。
5. Calibration metrics 可计算。
6. Market outcome 可手动录入。
7. Calibration service 可生成 CalibrationResult。
8. Promotion gate 可生成 EnginePromotionDecision。
9. Workstation 可展示 probability comparison。
10. Settings 可展示 engine registry。
11. History 可展示 calibration history。
12. Shadow engines 不驱动交易。
13. LIVE_EXECUTE 仍被拒绝。

## 17. 不纳入本层 v0

real DEB
real EMOS
LGBM
online learning
automatic engine promotion
real settlement resolver
profit-based model ranking
portfolio optimization
live execution

## 18. 下一轮入口

PWB-03 完成后，后续可以进入：

PWB-04 — Real Calibration Data & Backtest Memory

或：

PWB-04A — Real DEB Implementation
PWB-04B — EMOS Shadow Evaluation

但 PWB-03 本身应在 governance layer 跑通后停止。

## 19. Obsidian 放置位置

03_Projects/Polymarket_Bot/Architecture/
  Probability_Governance_Layer_v0.md

## 20. Repo 放置位置

docs/architecture/
  probability-governance-layer-v0.md

下一步建议进入：

PWB-03 Phase A/B — Models + SQLite schema + Repository methods
