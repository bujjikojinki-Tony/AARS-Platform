# AARS Polymarket Weather Trading 指标定义与数据治理规范

版本：v0.1  
日期：2026-04-21  
定位：监测采集层、异常发现层、阈值策略层的统一指标口径与数据治理规范

关联文档：

- [AARS_Polymarket_Weather_Trading_Architecture.md](./AARS_Polymarket_Weather_Trading_Architecture.md)
- [AARS_Polymarket_Weather_Trading_Detailed_Design.md](./AARS_Polymarket_Weather_Trading_Detailed_Design.md)
- [AARS_Polymarket_Weather_Trading_Functional_Requirements.md](./AARS_Polymarket_Weather_Trading_Functional_Requirements.md)
- [AARS_Polymarket_Weather_Trading_Implementation_Plan_Status.md](./AARS_Polymarket_Weather_Trading_Implementation_Plan_Status.md)
- [AARS_Polymarket_Weather_Trading_Gate_Stack_API_Contract.md](./AARS_Polymarket_Weather_Trading_Gate_Stack_API_Contract.md)

---

## 1. 文档目的

本文档定义 AARS Polymarket Weather Trading Console 中两类监测能力的指标体系、数据契约与治理要求：

1. 单市场实时预警（Observation Alert）
2. Family 级异常发现（Family Anomaly Discovery）

本文档不是交易执行策略文档，也不替代 authorization gate、execution gate 或 live trading policy。其作用是为 alert、scanner、dashboard、telegram、gate、automation 提供统一指标口径、阈值治理和可回放的数据契约。

---

## 2. 适用范围

适用于以下系统层：

- `weather-rules-research`
- `weather-comparison-engine`
- `weather-dashboard`
- `weather-telegram-console`
- `weather-execution-gateway`
- `gate_stack_api.v1`
- automation / scanner / dashboard consumers

本规范不直接授权真实执行，不替代 execution policy。

---

## 3. 设计原则

1. 指标先于策略，策略只能消费指标，不得反向决定指标口径。
2. 指标先校验 contract，再参与比较或告警。
3. 指标与 gate 分离，指标负责描述异常，gate 负责执行许可。
4. 指标按 family 治理，阈值、单位、窗口、band 规则必须 family-specific。
5. 指标必须可回放、可追溯，支持基于历史 snapshot 重算。

---

## 4. 术语定义

### 4.1 Observation

来自 METAR、official observation、station settlement source 的近实时或结算观测值。

### 4.2 Forecast

来自 ECMWF、HRRR、Wunderground、官方指数或其他 adapter 的预测值或模型投影值。

### 4.3 Resolver Source Contract

由 resolver 输出的稳定 source 语义，包括：

- `required_sources`
- `settlement_source_type`
- `official_vs_proxy_source`
- `source_match_grade`
- `official_source_url`
- `source_note`

### 4.4 Observation Alert

围绕单个市场，对观测、forecast、market 之间的实时变化进行事件检测和分级预警。

### 4.5 Family Anomaly Discovery

围绕同一 market family 的所有市场进行批量扫描，识别异常波动、偏离和 intervention-like 特征。

### 4.6 Intervention-like Market

指在研究语义下具有强异常市场微结构与证据不一致特征的市场，不等同于法律意义上的操纵认定。

---

## 5. 适用 Market Family

第一批优先支持：

- `temperature_daily_max`
- `temperature_daily_min`
- `weather_metric.precipitation`
- `weather_metric.wind_speed`
- `weather_metric.snowfall`

第二批条件支持：

- `global_temperature_index`
- `sea_ice_extent`

第二批 family 可先支持 anomaly discovery，但不强制支持高频 observation shock。

---

## 6. 单市场实时预警指标

### 6.1 Observation Shock

用于衡量 observation 值在短时间窗口内是否发生显著突变。

核心子指标：

- `threshold_cross_event`
- `threshold_cross_direction`
- `shock_delta_value`
- `shock_delta_abs`
- `shock_slope_per_minute`

治理要求：

- 必须保留 `previous_observation_value` 与 `previous_observed_at`
- 阈值由 threshold policy registry 按 family / variable 管理
- `source_match_grade != exact_station` 时，shock 只能降级为 review signal

### 6.2 Forecast Divergence

衡量 observation 与 forecast / model snapshot 的偏离程度。

核心子指标：

- `value_divergence`
- `value_divergence_abs`
- `band_divergence`
- `band_distance`
- `forecast_divergence_score`

治理要求：

- `market_id`、`variable_name`、`target_date` 必须一致
- `station_id` 一致或满足 family 级可比较条件
- `band_scheme` 一致
- 否则输出 `invalid_comparison=true` 与 `comparison_block_reason`

### 6.3 Market Reaction Gap

衡量 weather evidence 已变化，而市场价格尚未同步或反应异常。

核心子指标：

- `fair_value_gap`
- `reaction_lag_score`
- `market_band_mismatch`

治理要求：

- 必须基于标准化 `MarketSnapshot` 与 `ProbabilityState`
- `probability_mode` 非可执行模式时，仅允许 advisory / alert

### 6.4 Resolver / Source Risk

衡量 evidence 与市场结算口径的匹配程度。

核心字段：

- `required_sources`
- `settlement_source_type`
- `official_vs_proxy_source`
- `source_match_grade`
- `official_source_url`
- `resolver_status`
- `resolver_confidence`

核心子指标：

- `source_match_risk`
- `officialness_risk`
- `freshness_risk`

治理要求：

- 必须进入 top parameter ribbon、compact gate stack、`gate_stack_api.v1`、Telegram `/status` 与 `/market`

### 6.5 Alert Severity

将上述信号聚合为单市场预警等级：

- `info`
- `watch`
- `amber`
- `red`

输出字段：

- `severity`
- `recommended_operator_action`
- `alert_score`
- `primary_reason`

---

## 7. Family 级异常发现指标

### 7.1 Price Velocity

衡量短时间内价格变化速度。

输出：

- `price_velocity`
- `price_velocity_bucket`

### 7.2 Edge Dislocation

衡量 fair value 与 market implied probability 的偏离程度。

输出：

- `edge_dislocation`
- `confidence_adjusted_edge_dislocation`

### 7.3 Evidence Mismatch

衡量市场变化方向与 evidence 变化方向不一致。

输出：

- `evidence_mismatch`
- `evidence_mismatch_score`

### 7.4 Microstructure Stress

衡量盘口结构的异常压力。

输出：

- `spread_jump`
- `liquidity_drop`
- `one_sided_pressure`
- `favored_side_flip_frequency`
- `microstructure_stress_score`

### 7.5 Peer Relative Anomaly

衡量某市场相对于同 family / 同地区 / 同日期 peer 市场的异常程度。

输出：

- `peer_rank`
- `peer_zscore`
- `peer_outlier_flag`

### 7.6 Intervention-like Score

综合识别强异常市场微结构与证据不一致特征。

输出：

- `intervention_like_score`
- `intervention_like_flag`

---

## 8. 数据治理框架

### 8.1 治理对象

所有指标必须可追溯到：

- `MarketSnapshot`
- `ResolvedMarketRule`
- `ForecastSnapshot`
- `ObservationSnapshot`
- `ProbabilityState`
- `ComparisonPoint`
- `gate_stack_api.v1`

### 8.2 Indicator Registry

建议新增：

- `indicator_registry/observation_alert_registry/`
- `indicator_registry/family_anomaly_registry/`
- `threshold_policy_registry/`

每个指标注册内容至少包括：

- `indicator_name`
- `definition`
- `formula`
- `input_contracts`
- `output_fields`
- `applicable_families`
- `threshold_policy_ref`
- `version`

### 8.3 Threshold Policy Registry

用于管理：

- observation shock 阈值
- divergence 阈值
- anomaly score 阈值
- severity 分级阈值

### 8.4 指标输出契约

建议至少形成两个正式输出对象：

- `market_alert_event.v1`
- `market_anomaly_event.v1`

### 8.5 数据质量控制

1. Freshness 校验
2. Source precision 校验
3. Missing-data 语义统一
4. 历史可重算
5. Versioned computation

---

## 9. 实施蓝图

### 9.1 推荐目录树

```text
weather-comparison-engine/
  src/weather_comparison_engine/
    indicator_registry/
    threshold_policy_registry/
    observation_alert_layer/
    family_scanner/
    scripts/
  data/
    registries/
    outputs/
```

### 9.2 最小实施顺序

1. 创建 registry 与 threshold policy
2. 实现 `observation_shock_detector.py`、`forecast_divergence_detector.py`、`market_alert_event_writer.py`
3. 实现 family scanner 最小版
4. 补齐 `microstructure_stress_detector.py`、`peer_relative_anomaly.py`、`intervention_like_scorer.py`

---

## 10. 与现有系统的关系

当前系统已经具备以下承载位：

- `gate_stack_ops_alert.v1` 运行时告警事件
- Telegram ops bridge 队列与回执链路
- dashboard 的 Ops Alert / Queue 面板
- `TopParameterView` 首屏合同

本规范定义的是上游监测采集层和 family 级异常发现层，后续将作为：

- observation alert 的输入源
- family anomaly scanner 的输出源
- dashboard / telegram / automation 的统一消费依据

## 11. Completion Note

Phase 27 的监测采集闭环已经完成并进入正式基线；Phase 28 / Phase 29 / Phase 30 / Phase 31 也已沿着同一套 canonical-only 监测契约完成收口。当前的监测层、family anomaly 层、validation assimilation 层、自动扫描 / 实时告警层与 dashboard / Telegram / workstation 只读消费面已经对齐，后续扩展只应继续沿既有指标治理与 gate 分层推进。
