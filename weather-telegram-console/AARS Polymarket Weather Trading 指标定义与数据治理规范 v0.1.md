#

## **1. 文档目的**

本文档定义 AARS Polymarket Weather Trading Console 中两类新能力的指标体系、数据契约与治理要求：

1. 单市场实时预警（Observation Alert）
2. Family 级异常发现（Family Anomaly Discovery）

本文档目标不是直接定义交易执行策略，而是为后续 alert、scanner、dashboard、telegram、gate、automation 提供统一的指标口径、阈值治理和数据契约。

---

## **2. 文档适用范围**

本规范适用于以下系统层：

- `02_resolver_layer`
- `weather_data_adapters`
- `03_probability_layer`
- `04_comparison_layer`
- `05_decision_layer`
- `06_xai_layer`
- `07_authorization_layer`
- `gate_stack_api.v1`
- dashboard / telegram / automation consumers

本规范不直接授权真实执行，不替代 authorization gate、execution gate 或 live trading policy。

---

## **3. 设计原则**

### **3.1 指标先于策略**

指标定义必须先稳定，策略只能消费指标，不得反向决定指标口径。

### **3.2 指标先校验 contract，再参与比较**

若 `market_id`、`station_id`、`variable_name`、`target_date`、`source_match_grade` 或 `band_scheme` 不一致，则禁止进入强比较或强告警逻辑。

### **3.3 指标与 gate 分离**

指标负责描述异常、偏离、冲击与风险；gate 负责决定是否允许执行。

### **3.4 指标按 family 治理**

所有阈值、单位、窗口、band 规则必须 family-specific，不允许全局硬编码一套统一阈值。

### **3.5 指标必须可回放、可追溯**

所有指标都必须可从历史 snapshot 重算，并能追溯到：

- 输入对象
- 阈值策略
- contract version
- 计算时间

---

## **4. 术语定义**

### **4.1 Observation**

来自 METAR、official observation、station settlement source 的近实时或结算观测值。

### **4.2 Forecast**

来自 ECMWF、HRRR、Wunderground、官方指数或其他 adapter 的预测值或模型投影值。

### **4.3 Resolver Source Contract**

由 resolver 输出的稳定 source 语义，包括：

- `required_sources`
- `settlement_source_type`
- `official_vs_proxy_source`
- `source_match_grade`
- `official_source_url`
- `source_note`

### **4.4 Observation Alert**

围绕单个市场，对观测、forecast、market 之间的实时变化进行事件检测和分级预警。

### **4.5 Family Anomaly Discovery**

围绕同一 market family 的所有市场进行批量扫描，识别异常波动、偏离和 intervention-like 特征。

### **4.6 Intervention-like Market**

指在研究语义下具有强异常市场微结构与证据不一致特征的市场，不等同于法律意义上的操纵认定。

---

## **5. 适用 market family**

### **5.1 第一批优先支持**

- `temperature_daily_max`
- `temperature_daily_min`
- `weather_metric.precipitation`
- `weather_metric.wind_speed`
- `weather_metric.snowfall`

### **5.2 第二批条件支持**

- `global_temperature_index`
- `sea_ice_extent`

第二批 family 可先支持 anomaly discovery，但不强制支持高频 observation shock。

---

## **6. 单市场实时预警指标（Observation Alert）**

## **6.1 Observation Shock**

### **6.1.1 指标定义**

Observation Shock 用于衡量 observation 值在短时间窗口内是否发生显著突变。

### **6.1.2 核心子指标**

#### **A. Threshold Cross Event**

定义：

- `prev_observation < threshold <= current_observation`
- 或 `prev_observation > threshold >= current_observation`

输出字段：

- `threshold_cross_event: bool`
- `threshold_cross_direction: up | down | null`

#### **B. Shock Delta**

定义：

- `shock_delta = current_observation_value - previous_observation_value`

输出字段：

- `shock_delta_value`
- `shock_delta_abs`

#### **C. Shock Slope**

定义：

- `shock_slope = shock_delta / delta_time_minutes`

输出字段：

- `shock_slope_per_minute`

### **6.1.3 治理要求**

- 必须保留 `previous_observation_value` 与 `previous_observed_at`
- 阈值不允许全局统一，必须由 threshold policy registry 按 family / variable 管理
- `source_match_grade != exact_station` 时，shock 只能降级为 review signal

---

## **6.2 Forecast Divergence**

### **6.2.1 指标定义**

Forecast Divergence 衡量 observation 与当前 forecast / model snapshot 的偏离程度。

### **6.2.2 核心子指标**

#### **A. Value Divergence**

- `value_divergence = observation_value - forecast_value`
- `value_divergence_abs = abs(value_divergence)`

#### **B. Band Divergence**

- `band_divergence = observation_band != model_band`
- `band_distance`

#### **C. Confidence-weighted Divergence**

- `forecast_divergence_score = abs(observation_value - forecast_value) * source_confidence`

### **6.2.3 治理要求**

只有满足以下条件时，forecast divergence 才可标记为有效比较：

- `market_id` 一致
- `variable_name` 一致
- `target_date` 一致
- `station_id` 一致或满足 family 级可比较条件
- `band_scheme` 一致

否则输出：

- `invalid_comparison=true`
- `comparison_block_reason`

---

## **6.3 Market Reaction Gap**

### **6.3.1 指标定义**

Market Reaction Gap 用于衡量 weather evidence 已变化，而市场价格尚未及时同步或反应异常。

### **6.3.2 核心子指标**

#### **A. Fair Value Gap**

- `fair_value_gap = fair_value - market_implied_probability`

#### **B. Reaction Lag Score**

建议定义：

- `reaction_lag_score = evidence_change_score - market_move_score`

#### **C. Market Band Mismatch**

- `market_band != model_band`
- `band_distance`

### **6.3.3 治理要求**

- 必须基于标准化 `MarketSnapshot` 与 `ProbabilityState`
- 当前 `probability_mode` 若非可执行模式，reaction gap 只能进入 advisory / alert，不能直接用于 live action

---

## **6.4 Resolver / Source Risk**

### **6.4.1 指标定义**

Resolver / Source Risk 用于衡量当前 evidence 与市场结算口径的匹配程度。

### **6.4.2 核心字段**

直接使用 resolver/source contract：

- `required_sources`
- `settlement_source_type`
- `official_vs_proxy_source`
- `source_match_grade`
- `official_source_url`
- `resolver_status`
- `resolver_confidence`

### **6.4.3 核心子指标**

#### **A. Source Match Risk**

- 由 `source_match_grade` 推导：`low | medium | high`

#### **B. Officialness Risk**

- 由 `official_vs_proxy_source` 推导：`low | medium | high`

#### **C. Freshness Risk**

- 由 `freshness_status` 推导：`low | medium | high`

### **6.4.4 治理要求**

这些字段必须进入：

- top parameter ribbon
- compact gate stack
- gate_stack_api.v1
- telegram `/status` 与 `/market`

---

## **6.5 Alert Severity**

### **6.5.1 指标定义**

将 Observation Shock、Forecast Divergence、Market Reaction Gap、Resolver / Source Risk 聚合为单市场预警等级。

### **6.5.2 输出等级**

- `info`
- `watch`
- `amber`
- `red`

### **6.5.3 聚合规则**

建议使用“规则优先、分数辅助”的混合机制。

#### **Red**

满足任一：

- `threshold_cross_event=true` 且 `reaction_lag_score` 显著，且 `source_match_grade=exact_station` 且 `freshness_status=fresh`
- 强 forecast divergence + 高 fair value gap + 无高风险 source blocker

#### **Amber**

满足任一：

- 显著 observation shock
- 显著 forecast divergence
- 明显 market lag
- 存在 source 风险但仍需要人工复核

#### **Watch**

- 轻度波动
- 证据不足以升级

#### **Info**

- 仅状态变化记录

### **6.5.4 输出字段**

- `severity`
- `recommended_operator_action`
- `alert_score`
- `primary_reason`

### **6.5.5 语义对齐要求**

severity 与 `recommended_operator_action` 必须对齐 `gate_stack_api.v1` 既有语义。

---

## **7. Family 级异常发现指标（Family Anomaly Discovery）**

## **7.1 Price Velocity**

### **定义**

- `price_velocity = abs(current_market_probability - previous_market_probability) / delta_time`

### **输出字段**

- `price_velocity`
- `price_velocity_bucket`

### **用途**

识别短时间内价格快速变动市场。

---

## **7.2 Edge Dislocation**

### **定义**

- `edge_dislocation = abs(fair_value - market_implied_probability)`

### **输出字段**

- `edge_dislocation`
- `confidence_adjusted_edge_dislocation`

### **用途**

识别市场与模型显著偏离市场。

---

## **7.3 Evidence Mismatch**

### **定义**

市场变化方向与 evidence 变化方向不一致。

建议定义：

- `sign(market_move) != sign(evidence_move)`

其中 evidence_move 可来自：

- observation shock
- forecast revision
- model band shift

### **输出字段**

- `evidence_mismatch: bool`
- `evidence_mismatch_score`

---

## **7.4 Microstructure Stress**

### **定义**

衡量盘口结构的异常压力。

### **核心子指标**

- `spread_jump`
- `liquidity_drop`
- `one_sided_pressure`
- `favored_side_flip_frequency`

### **输出字段**

- `microstructure_stress_score`

### **治理要求**

必须基于标准化 `MarketSnapshot`，不得使用 UI 派生值作为正式输入。

---

## **7.5 Peer Relative Anomaly**

### **定义**

衡量某市场相对于同 family / 同地区 / 同日期 peer 市场的异常程度。

### **输出字段**

- `peer_rank`
- `peer_zscore`
- `peer_outlier_flag`

### **推荐分组维度**

- `market_family`
- `location_name`
- `target_date`
- `variable_name`

---

## **7.6 Intervention-like Score**

### **定义**

用于识别具备强异常市场微结构与证据不一致特征的市场。

### **组成建议**

由以下因素加权：

- 高 `price_velocity`
- 高 `microstructure_stress_score`
- 高 `evidence_mismatch_score`
- 高 `peer_relative_anomaly`
- 低 weather evidence support

### **输出字段**

- `intervention_like_score`
- `intervention_like_flag`

### **术语治理要求**

必须统一使用 `intervention_like`，不得使用法律定性术语替代。

---

## **8. 指标数据治理框架**

## **8.1 治理对象**

所有指标必须可追溯到以下标准对象：

- `MarketSnapshot`
- `ResolvedMarketRule`
- `ForecastSnapshot`
- `ObservationSnapshot`
- `ProbabilityState`
- `ComparisonPoint`
- `gate_stack_api.v1`

---

## **8.2 指标注册表（Indicator Registry）**

建议新增：

```text
indicator_registry/
  observation_alert_registry/
  family_anomaly_registry/
  threshold_policy_registry/
```

每个指标注册内容至少包括：

- `indicator_name`
- `definition`
- `formula`
- `input_contracts`
- `output_fields`
- `applicable_families`
- `threshold_policy_ref`
- `version`

---

## **8.3 阈值策略注册表（Threshold Policy Registry）**

用于管理：

- observation shock 阈值
- divergence 阈值
- anomaly score 阈值
- severity 分级阈值

字段建议：

- `family`
- `variable_name`
- `indicator_name`
- `threshold_value`
- `time_window`
- `unit`
- `policy_version`

---

## **8.4 指标产物契约（Indicator Output Contracts）**

建议至少形成两个正式输出对象：

### 

### **8.4.1**

**`market_alert_event.v1`**

用于单市场实时预警。

建议字段：

- `market_id`
- `event_type`
- `severity`
- `primary_reason`
- `observation_value`
- `forecast_value`
- `market_probability`
- `fair_value`
- `source_match_grade`
- `freshness_status`
- `recommended_operator_action`
- `generated_at`
- `contract_version`

### 

### **8.4.2**

**`market_anomaly_event.v1`**

用于 family 异常发现。

建议字段：

- `market_id`
- `market_family`
- `anomaly_score`
- `intervention_like_score`
- `signals[]`
- `primary_reason`
- `recommended_operator_action`
- `generated_at`
- `contract_version`

---

## **8.5 数据质量控制要求**

### **8.5.1 Freshness 校验**

所有 observation / market / forecast 输入必须带 freshness。若 freshness 缺失或 stale，指标可计算但必须降级。

### **8.5.2 Source Precision 校验**

若 `source_match_grade != exact_station`，则 observation-driven 指标默认降权或进入 review-only。

### **8.5.3 Missing-data 语义统一**

缺数据不等于 0，不等于正常。必须显式输出：

- `missing_input`
- `incomplete_signal`
- `degraded_confidence`

### **8.5.4 历史可重算**

所有指标必须支持基于历史 snapshot 重算，以支持：

- backtest
- anomaly review
- operator replay

### **8.5.5 Versioned Computation**

所有指标计算必须记录：

- `indicator_version`
- `threshold_policy_version`
- `contract_version`

---

## **9. 推荐输出文档结构**

建议后续形成三份正式文档：

1. 《Observation Alert 指标定义规范》
2. 《Family Anomaly Discovery 指标定义规范》
3. 《指标数据治理与阈值策略规范》

当前阶段可先合并为一份：  
《AARS Polymarket Weather Trading 指标定义与数据治理规范 v0.1》

---

## **10. 实施建议**

### **Step 1**

先固化本文档为正式规范。

### **Step 2**

建立：

- indicator registry
- threshold policy registry
- indicator output contracts

### **Step 3**

先实现单市场：

- `Observation Shock`
- `Forecast Divergence`
- `Market Reaction Gap`

### **Step 4**

再实现 family scanner：

- `Price Velocity`
- `Edge Dislocation`
- `Evidence Mismatch`
- `Intervention-like Score`

---

## **11. Registry 字段表与 JSON Schema 草案**

本节给出后续实现所需的最小 registry 与 output contract 字段定义，便于直接进入 Phase 1 实施。

### **11.1 Indicator Registry 字段表**

|**字段**|**类型**|**必填**|**含义**|
|---|---|---|---|
|`indicator_name`|string|是|指标唯一名称|
|`indicator_family`|string|是|`observation_alert` 或 `family_anomaly`|
|`version`|string|是|指标版本，如 `v1`|
|`definition`|string|是|指标自然语言定义|
|`formula`|string|是|指标公式或规则描述|
|`input_contracts`|string[]|是|允许输入的 contract 列表|
|`output_fields`|string[]|是|指标输出字段列表|
|`applicable_families`|string[]|是|适用 market family|
|`threshold_policy_ref`|string|否|关联阈值策略 ID|
|`requires_exact_station`|boolean|否|是否要求 exact station|
|`requires_fresh_inputs`|boolean|否|是否要求 fresh 输入|
|`severity_mapping`|object|否|分级规则引用|
|`status`|string|是|`active / deprecated / draft`|
|`owner`|string|否|维护人或模块|
|`notes`|string|否|备注|

#### **Indicator Registry JSON 示例**

```json
{
  "indicator_name": "observation_shock",
  "indicator_family": "observation_alert",
  "version": "v1",
  "definition": "Detect whether observation changes sharply within a short time window.",
  "formula": "shock_delta = current_observation_value - previous_observation_value; shock_slope = shock_delta / delta_time_minutes",
  "input_contracts": [
    "ObservationSnapshot",
    "ResolvedMarketRule"
  ],
  "output_fields": [
    "threshold_cross_event",
    "shock_delta_value",
    "shock_delta_abs",
    "shock_slope_per_minute"
  ],
  "applicable_families": [
    "temperature_daily_max",
    "temperature_daily_min",
    "weather_metric.precipitation",
    "weather_metric.wind_speed",
    "weather_metric.snowfall"
  ],
  "threshold_policy_ref": "threshold_policy.observation_shock.temperature_daily_max.v1",
  "requires_exact_station": true,
  "requires_fresh_inputs": true,
  "severity_mapping": {
    "watch": "low shock",
    "amber": "threshold cross or large shock",
    "red": "threshold cross + market lag"
  },
  "status": "active",
  "owner": "observation_alert_layer",
  "notes": "Degrade to review-only when source_match_grade != exact_station."
}
```

### **11.2 Threshold Policy Registry 字段表**

|**字段**|**类型**|**必填**|**含义**|
|---|---|---|---|
|`policy_id`|string|是|阈值策略唯一 ID|
|`indicator_name`|string|是|对应指标名称|
|`family`|string|是|适用 market family|
|`variable_name`|string|是|变量名|
|`threshold_type`|string|是|`absolute / relative / bucket / rule_based`|
|`threshold_value`|number/string/object|是|阈值内容|
|`time_window`|string|否|如 `15m`、`1h`|
|`unit`|string|否|指标单位|
|`severity_rules`|object|否|watch/amber/red 分级|
|`freshness_required`|string|否|`fresh / fresh_or_stale`|
|`source_match_required`|string|否|`exact_station / family_exact / any`|
|`status`|string|是|`active / deprecated / draft`|
|`version`|string|是|策略版本|
|`notes`|string|否|备注|

#### **Threshold Policy JSON 示例**

```json
{
  "policy_id": "threshold_policy.observation_shock.temperature_daily_max.v1",
  "indicator_name": "observation_shock",
  "family": "temperature_daily_max",
  "variable_name": "daily_max_temperature",
  "threshold_type": "rule_based",
  "threshold_value": {
    "shock_delta_abs": 0.3,
    "shock_slope_per_minute": 0.02,
    "threshold_cross_event": true
  },
  "time_window": "15m",
  "unit": "celsius",
  "severity_rules": {
    "watch": {
      "shock_delta_abs_gte": 0.2
    },
    "amber": {
      "shock_delta_abs_gte": 0.3
    },
    "red": {
      "threshold_cross_event": true,
      "requires_market_lag": true
    }
  },
  "freshness_required": "fresh",
  "source_match_required": "exact_station",
  "status": "active",
  "version": "v1",
  "notes": "Use review-only downgrade when official_vs_proxy_source != official."
}
```

### 

### 

### **11.3**

**`market_alert_event.v1`**

**JSON Schema 草案**

```json
{
  "schema_version": "market_alert_event.v1",
  "event_id": "alert_20260418_379803_001",
  "market_id": "379803",
  "market_family": "temperature_daily_max",
  "indicator_name": "observation_shock",
  "event_type": "threshold_cross",
  "severity": "amber",
  "primary_reason": "threshold_cross_with_fresh_exact_station_observation",
  "observation_value": 29.1,
  "forecast_value": 28.4,
  "market_probability": 0.22,
  "fair_value": 0.71,
  "source_match_grade": "exact_station",
  "official_vs_proxy_source": "official",
  "freshness_status": "fresh",
  "recommended_operator_action": "review_market_now",
  "contract_refs": {
    "market_snapshot_ref": "market_snapshot_id",
    "market_rule_ref": "market_rule_id",
    "forecast_snapshot_ref": "forecast_snapshot_id",
    "observation_snapshot_ref": "observation_snapshot_id",
    "probability_state_ref": "probability_state_id"
  },
  "generated_at": "2026-04-18T10:00:00Z",
  "indicator_version": "v1",
  "threshold_policy_version": "v1"
}
```

### 

### 

### **11.4**

**`market_anomaly_event.v1`**

**JSON Schema 草案**

```json
{
  "schema_version": "market_anomaly_event.v1",
  "event_id": "anomaly_20260418_379803_001",
  "market_id": "379803",
  "market_family": "temperature_daily_max",
  "anomaly_score": 0.91,
  "intervention_like_score": 0.84,
  "signals": [
    "price_velocity_high",
    "evidence_mismatch",
    "peer_outlier",
    "spread_stress"
  ],
  "primary_reason": "price_velocity_high_and_edge_dislocation",
  "peer_group": {
    "location_name": "Shanghai",
    "target_date": "2026-04-16",
    "variable_name": "daily_max_temperature"
  },
  "recommended_operator_action": "review_market_now",
  "generated_at": "2026-04-18T10:00:00Z",
  "indicator_version": "v1",
  "threshold_policy_version": "v1"
}
```

## **12. 实现蓝图（目录树 + 文件骨架 + JSON 布局）**

本节将本规范直接翻译为最小可实施的工程骨架，目标是为后续 Phase 1 实现提供稳定落点。

### **12.1 推荐目录树**

```text
weather-comparison-engine/
  src/weather_comparison_engine/
    indicator_registry/
      __init__.py
      registry_loader.py
      observation_alert_registry.py
      family_anomaly_registry.py
    threshold_policy_registry/
      __init__.py
      registry_loader.py
      observation_alert_policies.py
      family_anomaly_policies.py
    observation_alert_layer/
      __init__.py
      models.py
      observation_shock_detector.py
      forecast_divergence_detector.py
      market_reaction_gap_detector.py
      source_risk_evaluator.py
      alert_severity_builder.py
      market_alert_event_writer.py
    family_scanner/
      __init__.py
      models.py
      family_market_loader.py
      anomaly_feature_builder.py
      evidence_mismatch_detector.py
      microstructure_stress_detector.py
      peer_relative_anomaly.py
      intervention_like_scorer.py
      family_scan_report_writer.py
      market_anomaly_event_writer.py
    scripts/
      run_observation_alert_once.py
      run_family_anomaly_scan_once.py
  data/
    registries/
      indicators/
        observation_alert_registry.json
        family_anomaly_registry.json
      threshold_policies/
        observation_alert_policies.json
        family_anomaly_policies.json
    outputs/
      market_alert_events/
      market_anomaly_events/
      family_scan_reports/
```

### **12.2 Indicator Registry 文件骨架**

#### **`observation_alert_registry.py`**

职责：注册单市场实时预警类指标。

建议导出：

- `OBSERVATION_ALERT_REGISTRY`
- `get_indicator_definition(indicator_name)`

最小指标集：

- `observation_shock`
- `forecast_divergence`
- `market_reaction_gap`
- `resolver_source_risk`
- `alert_severity`

#### **`family_anomaly_registry.py`**

职责：注册 family 批量扫描类指标。

最小指标集：

- `price_velocity`
- `edge_dislocation`
- `evidence_mismatch`
- `microstructure_stress`
- `peer_relative_anomaly`
- `intervention_like_score`

### **12.3 Threshold Policy Registry 文件骨架**

#### **`observation_alert_policies.py`**

职责：定义 observation alert 的阈值策略。

建议至少包含：

- `temperature_daily_max`
- `temperature_daily_min`
- `weather_metric.precipitation`
- `weather_metric.wind_speed`
- `weather_metric.snowfall`

#### **`family_anomaly_policies.py`**

职责：定义 anomaly discovery 的阈值策略。

建议至少包含：

- price velocity thresholds
- edge dislocation thresholds
- evidence mismatch thresholds
- intervention-like score buckets

### **12.4 Observation Alert Layer 文件骨架**

#### **`models.py`**

建议定义：

- `ObservationAlertInput`
- `ObservationShockResult`
- `ForecastDivergenceResult`
- `MarketReactionGapResult`
- `SourceRiskResult`
- `MarketAlertEvent`

#### **`observation_shock_detector.py`**

输入：

- `ObservationSnapshot`
- `ResolvedMarketRule`
- threshold policy

输出：

- `threshold_cross_event`
- `shock_delta_value`
- `shock_delta_abs`
- `shock_slope_per_minute`

#### **`forecast_divergence_detector.py`**

输入：

- `ForecastSnapshot`
- `ObservationSnapshot`
- `ResolvedMarketRule`

输出：

- `value_divergence`
- `value_divergence_abs`
- `band_divergence`
- `forecast_divergence_score`

#### **`market_reaction_gap_detector.py`**

输入：

- `MarketSnapshot`
- `ProbabilityState`
- 上述 evidence 指标

输出：

- `fair_value_gap`
- `reaction_lag_score`
- `market_band_mismatch`

#### **`source_risk_evaluator.py`**

输入：

- `ResolvedMarketRule`
- freshness / source contract

输出：

- `source_match_risk`
- `officialness_risk`
- `freshness_risk`

#### **`alert_severity_builder.py`**

职责：将上述指标聚合为：

- `severity`
- `recommended_operator_action`
- `alert_score`
- `primary_reason`

#### **`market_alert_event_writer.py`**

职责：输出 `market_alert_event.v1` 到：

- `data/outputs/market_alert_events/`

### **12.5 Family Scanner 文件骨架**

#### **`models.py`**

建议定义：

- `FamilyScanInput`
- `PriceVelocityResult`
- `EdgeDislocationResult`
- `EvidenceMismatchResult`
- `MicrostructureStressResult`
- `PeerRelativeAnomalyResult`
- `MarketAnomalyEvent`
- `FamilyScanReport`

#### **`family_market_loader.py`**

职责：按 family 加载：

- market snapshots
- resolver rules
- forecast snapshots
- observation snapshots
- probability states
- comparison points

#### **`anomaly_feature_builder.py`**

职责：聚合基础 anomaly 特征：

- `price_velocity`
- `edge_dislocation`
- `market_move`
- `evidence_move`
- `peer_group_key`

#### **`evidence_mismatch_detector.py`**

职责：输出：

- `evidence_mismatch`
- `evidence_mismatch_score`

#### **`microstructure_stress_detector.py`**

职责：输出：

- `spread_jump`
- `liquidity_drop`
- `one_sided_pressure`
- `favored_side_flip_frequency`
- `microstructure_stress_score`

#### **`peer_relative_anomaly.py`**

职责：输出：

- `peer_rank`
- `peer_zscore`
- `peer_outlier_flag`

#### **`intervention_like_scorer.py`**

职责：综合：

- `price_velocity`
- `microstructure_stress_score`
- `evidence_mismatch_score`
- `peer_relative_anomaly`
- low evidence support

输出：

- `intervention_like_score`
- `intervention_like_flag`

#### **`family_scan_report_writer.py`**

职责：输出 `family_scan_report.v1` 到：

- `data/outputs/family_scan_reports/`

#### **`market_anomaly_event_writer.py`**

职责：输出 `market_anomaly_event.v1` 到：

- `data/outputs/market_anomaly_events/`

### **12.6 JSON 文件布局建议**

#### **`data/registries/indicators/observation_alert_registry.json`**

建议包含：

- `observation_shock`
- `forecast_divergence`
- `market_reaction_gap`
- `resolver_source_risk`
- `alert_severity`

#### **`data/registries/indicators/family_anomaly_registry.json`**

建议包含：

- `price_velocity`
- `edge_dislocation`
- `evidence_mismatch`
- `microstructure_stress`
- `peer_relative_anomaly`
- `intervention_like_score`

#### **`data/registries/threshold_policies/observation_alert_policies.json`**

建议按：

- family
- variable_name
- indicator_name  
    组织。

#### **`data/registries/threshold_policies/family_anomaly_policies.json`**

建议按：

- family
- anomaly indicator
- score bucket  
    组织。

#### **`data/outputs/market_alert_events/`**

建议文件命名：

- `market_alert_<market_id>_<timestamp>.json`

#### **`data/outputs/market_anomaly_events/`**

建议文件命名：

- `market_anomaly_<market_id>_<timestamp>.json`

#### **`data/outputs/family_scan_reports/`**

建议文件命名：

- `family_scan_<family>_<timestamp>.json`

### **12.7 最小实施顺序**

#### **Phase A**

先创建 registry 与 threshold policy 文件，不写 detector 逻辑。

#### **Phase B**

先实现 `observation_shock_detector.py`、`forecast_divergence_detector.py`、`market_alert_event_writer.py`。

#### **Phase C**

再实现 family scanner 的最小版：

- `family_market_loader.py`
- `anomaly_feature_builder.py`
- `market_anomaly_event_writer.py`

#### **Phase D**

最后补齐：

- `microstructure_stress_detector.py`
- `peer_relative_anomaly.py`
- `intervention_like_scorer.py`
- `family_scan_report_writer.py`

## **13. 当前结论**

当前 alert / anomaly 机制不应直接从脚本开始，而应先完成：

- 指标定义清晰
- 数据治理清晰
- 阈值策略可管理
- 输出契约稳定
- 目录结构与 registry 落点稳定

只有这样，后续的 dashboard、telegram、gate、automation 才能在同一语义上消费这些能力。