# **AARS Polymarket Weather Trading Source Cadence / Freshness / Priority Policy v0.1**

## **1. 文档目的**

本文档定义 AARS Polymarket Weather Trading Console 中各类数据源的：

- 采集周期（Cadence）
- 写入节奏（Write Interval）
- 新鲜度阈值（Freshness Threshold）
- 优先级（Priority）
- 回退策略（Fallback Policy）

本文档的目标不是定义交易策略，而是把不同 source 的采集与 freshness 规则收口成统一治理策略，供以下层共同消费：

- `market_layer`
- `resolver_layer`
- `weather_data_adapters`
- `probability_layer`
- `comparison_layer`
- `monitoring_layer`
- `observation_alert_layer`
- `family_scanner`
- `unified_status.json`
- `gate_stack_api.v1`
- dashboard / telegram / automation

---

## **2. 适用范围**

本策略适用于以下 source 类型：

1. 市场源（Market Sources）
2. 元数据与规则源（Metadata / Resolver Sources）
3. Forecast 源（Forecast Sources）
4. Observation 源（Observation Sources）
5. Official / Settlement 源（Truth Sources）
6. 派生状态源（Derived State Sources）
7. 监测采集源（Alert / Anomaly Derived Sources）

本文档不直接替代 execution policy，但 freshness / priority 策略会进入：

- `monitoring_status.json`
- `unified_status.json`
- `gate_stack_api.v1`
- `market_alert_event.v1`
- `market_anomaly_event.v1`

---

## **3. 设计原则**

### **3.1 周期按业务语义定义，不按技术便利定义**

不同 source 的采集节奏必须服从其业务角色：

- 盘口源高频
- 规则解析源中低频
- forecast 源按发布节奏驱动
- observation 源按近实时特性驱动
- official truth 源低频但高权威
- family scanner 批量低频扫描

### **3.2 采集周期、写入周期、freshness 阈值必须分开治理**

以下概念必须区分：

- `poll_interval`
- `write_interval`
- `fresh_threshold`
- `stale_threshold`

轮询周期不等于 freshness 阈值，写入周期也不等于 stale 判定周期。

### **3.3 Selected Market、Watchlist、Family Scan 采用不同优先级**

同一个 source 在不同业务情境中必须允许采用不同 cadence：

- `selected_market_priority`
- `watchlist_priority`
- `family_scan_priority`

### **3.4 Freshness 是系统级 gate 输入，不只是 UI 提示**

当 source 超过 freshness 阈值时，必须同时影响：

- `source_confidence`
- comparison validity
- alert severity
- anomaly scoring confidence
- gate blocking / degraded state

### **3.5 Source policy 必须 registry-first**

所有 source cadence / freshness / fallback 规则必须进入统一 policy registry，不允许在 worker、dashboard、telegram、scanner 中硬编码一套独立规则。

---

## **4. 术语定义**

### **4.1 Poll Interval**

worker 或 adapter 主动检查 source 是否有新数据的周期。

### **4.2 Write Interval**

满足写入条件后，把数据持久化为标准 snapshot / event 的周期。

### **4.3 Fresh Threshold**

source 在该时间窗内被视为 `fresh`。

### **4.4 Stale Threshold**

超过该阈值后，source 被视为 `stale`；继续超出可进入 `unavailable` 或 `blocked`。

### **4.5 Publish-aware Poll**

根据 source 自身发布时间或 run 周期决定是否写入新 snapshot，而不是每次轮询都覆盖。

### **4.6 Event-driven Recompute**

上游 source 更新后，触发 comparison / probability / alert 增量重算。

### **4.7 Priority Level**

描述 source 在某场景下的业务优先级，例如：

- `critical`
- `high`
- `medium`
- `low`

---

## **5. Source Policy 总表**

|**source_name**|**source_type**|**primary_use**|**trigger_mode**|**selected_market_poll**|**watchlist_poll**|**family_scan_poll**|**write_interval**|**fresh_threshold**|**stale_threshold**|**priority_level**|**fallback_policy**|
|---|---|---|---|---|---|---|---|---|---|---|---|
|`polymarket_clob`|market_realtime|盘口、price velocity、spread、market truth|websocket + debounce|1–5s|5–15s 聚合|1–5m 汇总|1–5s|30s|90s|critical|fallback to last price snapshot + stale badge|
|`polymarket_gamma`|market_metadata|市场发现、问题文本、元数据|poll + on-demand|5m|10–15m|30–60m|5–15m|30m|2h|medium|fallback to local cache|
|`resolver_registry`|rule_contract|market rule / source contract|event + scheduled refresh|on select|30–60m|60–120m|on change|6h|24h|high|fallback to last valid resolved rule|
|`hrrr`|forecast_short_range|美国短临高分辨率 forecast|publish-aware poll|5–15m|15–30m|30–60m|on new run|2h|6h|high|fallback to last valid run|
|`ecmwf`|forecast_synoptic|全局/日级 forecast 基线|publish-aware poll|15–30m check|30–60m|60–120m|on new run|12h|24h|high|fallback to previous run|
|`wunderground_station`|station_forecast/history|站点 forecast/history、本地支持|poll + cache-first|5–15m|15–30m|30–60m|5–15m|3h|12h|medium|fallback to cached station snapshot|
|`metar`|observation_realtime|observation shock、阈值穿越、forecast divergence|poll + bounded watchlist|1–5m|5–10m|10–30m|1–5m|30–90m|3h|high|fallback to last observation + downgrade confidence|
|`official_obs`|observation_official|结算 truth、label、official confirmation|poll + batch backfill|15–60m|60m|6–24h|on update|6h|24h|critical|fallback to proxy source with explicit downgrade|
|`climate_index_source`|climate_index|全球温度/气候指数|publish-aware poll|30–60m|2–6h|6–24h|on update|24h|72h|high|fallback to previous official release|
|`sea_ice_dataset`|climate_dataset|海冰范围等低频官方数据|publish-aware poll|30–60m|2–6h|6–24h|on update|24h|72h|high|fallback to previous published snapshot|
|`comparison_engine`|derived_state|edge / divergence / dashboard rows|upstream-triggered|event-driven|1–5m|5–15m|on recompute|15m|60m|high|fallback to last successful comparison with stale badge|
|`observation_alert_layer`|derived_alert|单市场实时预警|observation-first trigger|event-driven|1–5m|n/a|on alert|15m|60m|high|fallback to recompute from latest valid upstream facts|
|`family_scanner`|derived_scan|family anomaly discovery|batch + targeted rescan|n/a|n/a|5–15m|5–15m|30m|2h|medium|fallback to previous scan report with degraded confidence|

---

## **6. Source 类型分层解释**

## **6.1 市场源（Market Sources）**

### 

### **6.1.1**

**`polymarket_clob`**

#### **角色**

- 市场盘口事实源
- 价格、spread、favored side、market implied probability 的唯一高频上游
- family anomaly 中 `price_velocity`、`microstructure_stress` 的主源

#### **周期策略**

- 通过 WebSocket 持续接收
- 采用 debounce / coalescing 写快照
- selected market 可保持 1–5 秒级聚合刷新
- watchlist / family 使用低频聚合视图即可

#### **Freshness 策略**

- `fresh_threshold = 30s`
- `stale_threshold = 90s`

#### **治理要求**

- 所有 market-level 高频异常判断必须以 `MarketSnapshot` 为基础
- 不允许以 Gamma metadata 替代 CLOB price truth

### 

### **6.1.2**

**`polymarket_gamma`**

#### **角色**

- 市场发现
- 问题文本、slug、event metadata 支持
- resolver 的结构辅助输入

#### **周期策略**

- 不需要高频
- selected market 可 5 分钟检查一次
- watchlist / discovery 10–15 分钟即可
- family scan 30–60 分钟即可

#### **Freshness 策略**

- `fresh_threshold = 30m`
- `stale_threshold = 2h`

#### **治理要求**

- Gamma metadata 仅为结构辅助源，不得直接作为高频 market fact

---

## **6.2 Resolver / Rule 源**

### 

### **6.2.1**

**`resolver_registry`**

#### **角色**

- 统一 market rule
- 输出 source contract
- 解释 station / variable / target_date / band_scheme

#### **周期策略**

- selected market 切换时立即运行
- watchlist 周期回扫 30–60 分钟
- family scan 低频使用缓存 resolver result
- registry / override 更新时事件触发重算

#### **Freshness 策略**

- `fresh_threshold = 6h`
- `stale_threshold = 24h`

#### **治理要求**

- resolver contract 变化后，依赖它的 forecast / observation / probability / alert 必须按 `market_id` 失效或重算

---

## **6.3 Forecast 源（Forecast Sources）**

### 

### **6.3.1**

**`hrrr`**

#### **角色**

- 美国本土短临高分辨率 forecast
- 适合 wind / precipitation / temperature 的短时段判断

#### **周期策略**

- 5–15 分钟检查一次是否出现新有效 run
- 仅在新 run 出现时写新 snapshot
- watchlist 与 family scan 可低频化

#### **Freshness 策略**

- `fresh_threshold = 2h`
- `stale_threshold = 6h`

#### **治理要求**

- HRRR 只在支持区域启用，不适用于全球泛化 family

### 

### **6.3.2**

**`ecmwf`**

#### **角色**

- 全局 / 日级 synoptic forecast 基线
- 中低频 temperature / climate 类判断的重要 forecast 源

#### **周期策略**

- 15–30 分钟检查是否有新 run
- 只有在新 run 出现时写入新 `ForecastSnapshot`
- 不允许用频繁轮询伪造高频更新

#### **Freshness 策略**

- `fresh_threshold = 12h`
- `stale_threshold = 24h`

#### **治理要求**

- 必须保留 forecast run 时间，不允许覆盖式隐藏旧 run

### 

### **6.3.3**

**`wunderground_station`**

#### **角色**

- 站点级补充 forecast / history
- 本地 station support

#### **周期策略**

- selected market：5–15 分钟
- watchlist：15–30 分钟
- family scan：30–60 分钟

#### **Freshness 策略**

- `fresh_threshold = 3h`
- `stale_threshold = 12h`

#### **治理要求**

- 仅作为 station support / supplement，不替代 official settlement truth

---

## **6.4 Observation 源（Observation Sources）**

### 

### **6.4.1**

**`metar`**

#### **角色**

- 单市场 Observation Alert 的核心近实时触发源
- 支持：
    - `Observation Shock`
    - `Forecast Divergence`
    - `Market Reaction Gap`

#### **周期策略**

- selected market：1–5 分钟
- watchlist matched station markets：5–10 分钟
- family scan：10–30 分钟
- 仅对 matched / high-priority station markets 高优先采集

#### **Freshness 策略**

- `fresh_threshold = 30–90m`
- `stale_threshold = 3h`

#### **治理要求**

- `source_match_grade != exact_station` 时默认降权
- freshness 不足时可继续参与 alert，但必须降低 `source_confidence`
- 不能把 METAR 默认等价为 settlement truth

### 

### **6.4.2**

**`official_obs`**

#### **角色**

- 权威 truth / settlement / label / confirmation source
- 训练验证、promotion、label store 的关键输入

#### **周期策略**

- selected market：15–60 分钟
- watchlist：60 分钟
- family scan：6–24 小时
- 历史 backfill 可按小时或按天批量运行

#### **Freshness 策略**

- `fresh_threshold = 6h`
- `stale_threshold = 24h`

#### **治理要求**

- official obs 是 truth anchor，不必与 METAR 同频
- 当 official obs 缺失时，若 fallback 到 proxy source，必须显式降级 source contract

---

## **6.5 低频官方数据集（Climate / Dataset Sources）**

### 

### **6.5.1**

**`climate_index_source`**

#### **角色**

- 全球温度 / 气候指数类 family 的主 truth / forecast support 源

#### **周期策略**

- selected market：30–60 分钟检查新发布
- watchlist：2–6 小时
- family scan：6–24 小时
- snapshot 仅在新 release 可用时更新

#### **Freshness 策略**

- `fresh_threshold = 24h`
- `stale_threshold = 72h`

### 

### **6.5.2**

**`sea_ice_dataset`**

#### **角色**

- 海冰范围、低频官方 climate dataset

#### **周期策略**

- selected market：30–60 分钟检查
- watchlist：2–6 小时
- family scan：6–24 小时

#### **Freshness 策略**

- `fresh_threshold = 24h`
- `stale_threshold = 72h`

#### **治理要求**

- 不适合高频 observation shock
- 更适合 anomaly discovery / trend comparison / truth alignment

---

## **6.6 派生状态源（Derived State Sources）**

### 

### **6.6.1**

**`comparison_engine`**

#### **角色**

- 生成 `ProbabilityState`
- 生成 `ComparisonPoint`
- 输出 dashboard rows / history relationship / top parameter derived fields

#### **周期策略**

- 完全由上游 facts 触发
- selected market：event-driven 增量重算
- watchlist：1–5 分钟批重算
- family scan：5–15 分钟聚合重算

#### **Freshness 策略**

- `fresh_threshold = 15m`
- `stale_threshold = 60m`

#### **治理要求**

- comparison / probability 只能派生，不改写上游 facts

### 

### **6.6.2**

**`observation_alert_layer`**

#### **角色**

- 单市场实时预警
- 输出 `market_alert_event.v1`

#### **周期策略**

- observation 更新优先触发
- market 更新次级触发
- watchlist 下可按 1–5 分钟 bounded recompute

#### **Freshness 策略**

- `fresh_threshold = 15m`
- `stale_threshold = 60m`

#### **治理要求**

- alert 层不重新定义 market truth，仅消费上游 snapshot

### 

### **6.6.3**

**`family_scanner`**

#### **角色**

- family anomaly discovery
- 输出 `market_anomaly_event.v1` 与 family scan reports

#### **周期策略**

- 批量 5–15 分钟扫描
- 高优先事件触发 targeted rescan
- 不做秒级全 family 扫描

#### **Freshness 策略**

- `fresh_threshold = 30m`
- `stale_threshold = 2h`

#### **治理要求**

- scanner 只做批量分析，不定义 execution permission

---

## **7. Priority Policy**

## **7.1 Priority Levels**

### **`critical`**

用于：

- `polymarket_clob`
- `official_obs`

要求：

- failure / stale 直接影响 gate 或 truth validity

### **`high`**

用于：

- `resolver_registry`
- `hrrr`
- `ecmwf`
- `metar`
- `comparison_engine`
- `observation_alert_layer`

要求：

- stale 时必须进入 degraded state 或 risk penalty

### **`medium`**

用于：

- `polymarket_gamma`
- `wunderground_station`
- `family_scanner`

要求：

- stale 时允许继续展示，但必须降权或降级

### **`low`**

适用于纯展示性或非核心辅助源

---

## **8. Freshness State Machine**

建议所有 source 统一使用：

- `fresh`
- `stale`
- `unavailable`

### **8.1 状态规则**

#### **fresh**

- `age <= fresh_threshold`

#### **stale**

- `fresh_threshold < age <= stale_threshold`

#### **unavailable**

- `age > stale_threshold`
- 或数据缺失 / 请求失败 / schema invalid

### **8.2 治理要求**

- freshness 状态必须进入：
    - `monitoring_status.json`
    - `unified_status.json`
    - `gate_stack_api.v1`
    - `market_alert_event.v1`
    - `market_anomaly_event.v1`
- stale 不得默默显示为正常

---

## **9. Fallback Policy**

## **9.1 基本规则**

所有 source 必须定义 fallback，但 fallback 不得伪装成 primary truth。

### **9.1.1 Market Source Fallback**

- CLOB 失效：回退到最近 market snapshot
- UI 必须显示 stale/degraded

### **9.1.2 Resolver Fallback**

- resolver registry 不可用：回退到最近已验证的 `MarketRule`
- 必须记录 fallback source 与 timestamp

### **9.1.3 Forecast Fallback**

- 未出现新 run：保持前一有效 run，不覆盖为空
- stale 超阈值后进入 degraded

### **9.1.4 Observation Fallback**

- official obs 不可用时，可临时回退到 proxy observation（如 METAR / Wunderground）
- 必须同步降级：
    - `official_vs_proxy_source`
    - `source_match_grade`
    - `source_confidence`

### **9.1.5 Derived Source Fallback**

- comparison / alert / scanner 失败时，可回退到最近成功产物
- 但必须标记 stale / degraded，不得当作 fresh output

---

## **10. 与监测预警和异常发现的关系**

## **10.1 Observation Alert**

`Observation Shock`、`Forecast Divergence`、`Market Reaction Gap` 必须同时读取：

- source freshness
- source priority
- source match precision

只有在 freshness 和 source contract 满足要求时，alert 才能进入高 severity。

## **10.2 Family Anomaly Discovery**

`Price Velocity`、`Edge Dislocation`、`Evidence Mismatch`、`Microstructure Stress`、`Peer Relative Anomaly` 必须建立在：

- 同周期语义兼容的 market / forecast / observation snapshot 之上
- 不允许把低频 climate dataset 与高频 price source 直接视作同 cadence truth

---

## **11. Source Policy Registry Schema**

建议新增：

```text
source_policy_registry/
  source_cadence_policy.json
```

### **11.1 字段定义**

|**字段**|**类型**|**必填**|**含义**|
|---|---|---|---|
|`source_name`|string|是|数据源名称|
|`source_type`|string|是|market / resolver / forecast / observation / official / derived|
|`primary_use`|string|是|主用途|
|`trigger_mode`|string|是|websocket / poll / publish-aware / event-driven / batch|
|`selected_market_poll_interval`|string|否|选中市场周期|
|`watchlist_poll_interval`|string|否|watchlist 周期|
|`family_scan_interval`|string|否|family scan 周期|
|`write_interval`|string|是|写入周期|
|`fresh_threshold`|string|是|fresh 阈值|
|`stale_threshold`|string|是|stale 阈值|
|`priority_level`|string|是|critical / high / medium / low|
|`fallback_policy`|string|是|降级描述|
|`status`|string|是|active / deprecated / draft|
|`version`|string|是|策略版本|
|`notes`|string|否|备注|

### **11.2 JSON 示例**

```json
{
  "source_name": "metar",
  "source_type": "observation",
  "primary_use": "observation shock and forecast divergence",
  "trigger_mode": "poll",
  "selected_market_poll_interval": "1-5m",
  "watchlist_poll_interval": "5-10m",
  "family_scan_interval": "10-30m",
  "write_interval": "1-5m",
  "fresh_threshold": "90m",
  "stale_threshold": "3h",
  "priority_level": "high",
  "fallback_policy": "fallback to last observation and downgrade source confidence",
  "status": "active",
  "version": "v1",
  "notes": "Use exact_station markets first; degrade when source_match_grade != exact_station."
}
```

---

## **12. 实施建议**

### **Step 1**

先把本策略固化为正式 source policy registry。

### **Step 2**

让以下模块统一消费：

- `monitoring_layer`
- `weather_data_adapters`
- `observation_alert_layer`
- `family_scanner`

### **Step 3**

将 freshness / priority / fallback 统一接入：

- `unified_status.json`
- `gate_stack_api.v1`
- `TopParameterView`
- Telegram `/status` / `/market`

### **Step 4**

对 selected market、watchlist、family scanner 分层压测 cadence 成本与收益。

---

## **13. Measurement Normalization / Precision / Rounding / Band Mapping Governance**

本章补充定义跨 source 的数值标准化治理，用于解决：

- 不同 source 单位不一致
- 转换后精度不一致
- rounding 规则不一致
- band / threshold 判定口径不一致

本章适用于：

- `ForecastSnapshot`
- `ObservationSnapshot`
- `ProbabilityState`
- `ComparisonPoint`
- `TopParameterView`
- `market_alert_event.v1`
- `market_anomaly_event.v1`

### **13.1 设计目标**

Measurement Normalization 的目标是：

1. 所有跨源比较必须先统一到 canonical unit。
2. 所有数值计算必须明确使用哪一种 precision。
3. 所有 rounding / truncation 行为必须进入 policy，而不是散落在代码中。
4. 所有 band / threshold 判定必须基于同一 canonical unit 与 rounding policy。
5. UI 只能展示标准化后的字段，必要时可展开查看 raw 字段，但不得自行转换并改写事实。

### **13.2 Canonical Unit Policy**

每类变量都必须定义：

- `raw_units[]`
- `canonical_unit`
- `display_unit`
- `conversion_rules[]`

建议最小分类如下：

|**variable_group**|**raw_units**|**canonical_unit**|**display_unit**|
|---|---|---|---|
|`temperature`|`celsius`, `fahrenheit`|`celsius`|`celsius`|
|`wind_speed`|`kt`, `mph`, `m/s`, `km/h`|`kt`|`kt`|
|`precipitation`|`mm`, `inch`|`mm`|`mm`|
|`snowfall`|`mm`, `cm`, `inch`|`mm`|`mm`|
|`climate_index`|source-defined|source-defined canonical|source-defined canonical|

治理要求：

- comparison / alert / anomaly / gate 使用 canonical unit
- display 可使用 display_unit，但不得脱离 canonical value 独立计算
- raw unit 只能作为审查信息，不得直接进入跨源比较

### **13.3 Precision Policy**

必须显式区分四种 precision：

#### **A. Storage Precision**

用于 snapshot / feature store 持久化。

#### **B. Comparison Precision**

用于 divergence、delta、slope、fair value 输入计算。

#### **C. Display Precision**

用于 dashboard / Telegram 展示。

#### **D. Settlement / Band Precision**

用于 threshold 判定、band 映射、official band 对齐。

示例：

|**family**|**canonical_unit**|**storage_precision**|**comparison_precision**|**display_precision**|**band_precision**|
|---|---|---|---|---|---|
|`temperature_daily_max`|`celsius`|3|2|1|integer|
|`temperature_daily_min`|`celsius`|3|2|1|integer|
|`weather_metric.wind_speed`|`kt`|3|2|1|1|
|`weather_metric.precipitation`|`mm`|3|2|1|1|

治理要求：

- detector 不得默认沿用 display precision 做比较
- band mapping 只能使用 settlement / band precision
- feature store 不得使用 UI 显示精度覆盖存储精度

### **13.4 Rounding Policy**

所有 rounding 行为必须进入统一 policy registry。允许的 rounding 语义建议限定为：

- `round_half_up`
- `floor`
- `ceil`
- `truncate`
- `exact_no_rounding`

不同 family / indicator 可绑定不同 rounding rule，但必须显式声明：

- `rounding_rule`
- `rounding_stage`
- `applies_to`

示例：

|**family**|**applies_to**|**rounding_rule**|**说明**|
|---|---|---|---|
|`temperature_daily_max`|band_mapping|`round_half_up`|用于 market band / official band 映射|
|`temperature_daily_max`|display|`round_half_up`|UI 显示|
|`weather_metric.precipitation`|threshold_compare|`exact_no_rounding`|threshold 判断不先取整|
|`wind_speed`|display|`round_half_up`|仅展示使用|

治理要求：

- rounding rule 不得在 dashboard / Telegram / scanner 中单独硬编码
- rounding rule 必须进入 registry，并允许回放时追溯

### **13.5 Band Mapping Policy**

所有 `band_scheme` 必须绑定：

- `canonical_unit`
- `band_precision`
- `rounding_rule`
- `mapping_rule`

例如：

#### **`temperature_celsius_integer`**

- canonical unit: `celsius`
- band precision: integer
- rounding rule: policy-defined
- mapping rule: `band = int(rounded_canonical_value)`

#### **`wind_speed_threshold_knots`**

- canonical unit: `kt`
- band precision: 1 decimal or threshold rule
- rounding rule: family policy-defined
- mapping rule: threshold compare against canonical kt

治理要求：

- `market_band`
- `model_band`
- `observation_band`
- `official_band`  
    必须使用同一 band mapping policy 生成
- 不允许在 comparison layer 与 UI layer 各自计算 band

### **13.6 Measurement Normalization Contract**

所有进入 `ForecastSnapshot` / `ObservationSnapshot` 的关键数值，应在标准化后显式携带以下字段：

```json
{
  "raw_value": 84.2,
  "raw_unit": "fahrenheit",
  "canonical_value": 29.0,
  "canonical_unit": "celsius",
  "conversion_rule": "f_to_c",
  "conversion_applied": true,
  "precision_policy_ref": "precision_policy.temperature_daily_max.v1",
  "rounding_rule": "round_half_up",
  "normalization_version": "measurement_normalization.v1"
}
```

治理要求：

- raw 字段必须保留，以便审计与回放
- canonical 字段是 comparison / alert / anomaly 的唯一输入
- `TopParameterView` 默认展示 canonical 字段，必要时可展开 raw 字段做 operator 审查

### **13.7 Measurement Registry 建议**

建议新增以下 registry：

```text
measurement_registry/
  unit_registry.json
  precision_policy_registry.json
  rounding_policy_registry.json
  band_mapping_policy_registry.json
```

#### **`unit_registry.json`**

定义：

- variable group
- raw units
- canonical unit
- display unit
- conversion rules

#### **`precision_policy_registry.json`**

定义：

- family
- variable_name
- storage precision
- comparison precision
- display precision
- settlement / band precision

#### **`rounding_policy_registry.json`**

定义：

- family
- applies_to
- rounding rule
- notes

#### **`band_mapping_policy_registry.json`**

定义：

- band scheme
- canonical unit
- band precision
- rounding rule
- mapping formula

### **13.8 与监测采集层的关系**

Measurement Normalization 是 Observation Alert 与 Family Anomaly Discovery 的硬前置条件：

- `Observation Shock` 必须基于 canonical observation value
- `Forecast Divergence` 必须基于 canonical forecast / observation values
- `Market Reaction Gap` 的 band mismatch 必须基于统一 band mapping policy
- `Family Anomaly Discovery` 的 peer comparison 必须基于统一 canonical units 和 precision policies

因此：

- 不允许 detector 自行做单位转换
- 不允许 UI 先格式化后反向参与指标计算
- 不允许 alert / anomaly contract 混用 raw value 与 canonical value 做正式判断

### **13.9 实施建议**

#### **Step 1**

先建立：

- `unit_registry.json`
- `precision_policy_registry.json`
- `rounding_policy_registry.json`
- `band_mapping_policy_registry.json`

#### **Step 2**

在 `weather_data_adapters` 中统一引入 normalization step，输出 raw + canonical fields。

#### **Step 3**

在 `ForecastSnapshot` / `ObservationSnapshot` / `TopParameterView` 中补充 normalization fields。

#### **Step 4**

让以下模块仅消费 canonical fields：

- `comparison_layer`
- `observation_alert_layer`
- `family_scanner`
- `gate_stack_api` 上游 scorer

#### **Step 5**

增加回归测试：

- Fahrenheit -> Celsius
- inch -> mm
- mph / m/s -> kt
- rounding / band mapping consistency

## **14. Registry JSON 样例文件**

本节给出可直接落盘的 registry 样例，供后续实现 `weather_data_adapters`、`comparison_layer`、`observation_alert_layer`、`family_scanner` 与 `gate_stack` 上游 scorer 统一消费。

### 

### **14.1**

**`source_policy_registry.json`**

```json
{
  "schema_version": "source_policy_registry.v1",
  "generated_at": "2026-04-21T00:00:00Z",
  "sources": [
    {
      "source_name": "polymarket_clob",
      "source_type": "market_realtime",
      "primary_use": "market truth, price velocity, spread, favored_side",
      "trigger_mode": "websocket_debounce",
      "selected_market_poll_interval": "1-5s",
      "watchlist_poll_interval": "5-15s",
      "family_scan_interval": "1-5m",
      "write_interval": "1-5s",
      "fresh_threshold": "30s",
      "stale_threshold": "90s",
      "priority_level": "critical",
      "fallback_policy": "fallback_to_last_market_snapshot_with_stale_badge",
      "status": "active",
      "version": "v1",
      "notes": "Primary market truth source."
    },
    {
      "source_name": "polymarket_gamma",
      "source_type": "market_metadata",
      "primary_use": "market discovery, question text, slug, metadata",
      "trigger_mode": "poll_on_demand",
      "selected_market_poll_interval": "5m",
      "watchlist_poll_interval": "10-15m",
      "family_scan_interval": "30-60m",
      "write_interval": "5-15m",
      "fresh_threshold": "30m",
      "stale_threshold": "2h",
      "priority_level": "medium",
      "fallback_policy": "fallback_to_local_market_metadata_cache",
      "status": "active",
      "version": "v1",
      "notes": "Never used as high-frequency market truth."
    },
    {
      "source_name": "resolver_registry",
      "source_type": "rule_contract",
      "primary_use": "market rule, station mapping, source contract",
      "trigger_mode": "event_and_scheduled_refresh",
      "selected_market_poll_interval": "on_select",
      "watchlist_poll_interval": "30-60m",
      "family_scan_interval": "60-120m",
      "write_interval": "on_change",
      "fresh_threshold": "6h",
      "stale_threshold": "24h",
      "priority_level": "high",
      "fallback_policy": "fallback_to_last_valid_market_rule",
      "status": "active",
      "version": "v1",
      "notes": "Contract provider, not a realtime fact source."
    },
    {
      "source_name": "hrrr",
      "source_type": "forecast_short_range",
      "primary_use": "US short-range forecast support",
      "trigger_mode": "publish_aware_poll",
      "selected_market_poll_interval": "5-15m",
      "watchlist_poll_interval": "15-30m",
      "family_scan_interval": "30-60m",
      "write_interval": "on_new_run",
      "fresh_threshold": "2h",
      "stale_threshold": "6h",
      "priority_level": "high",
      "fallback_policy": "fallback_to_previous_valid_run",
      "status": "active",
      "version": "v1",
      "notes": "Use only in supported region."
    },
    {
      "source_name": "ecmwf",
      "source_type": "forecast_synoptic",
      "primary_use": "global or day-scale forecast baseline",
      "trigger_mode": "publish_aware_poll",
      "selected_market_poll_interval": "15-30m",
      "watchlist_poll_interval": "30-60m",
      "family_scan_interval": "60-120m",
      "write_interval": "on_new_run",
      "fresh_threshold": "12h",
      "stale_threshold": "24h",
      "priority_level": "high",
      "fallback_policy": "fallback_to_previous_run",
      "status": "active",
      "version": "v1",
      "notes": "Do not overwrite snapshot unless a new run exists."
    },
    {
      "source_name": "wunderground_station",
      "source_type": "station_forecast_history",
      "primary_use": "station support, history, local forecast supplement",
      "trigger_mode": "poll_cache_first",
      "selected_market_poll_interval": "5-15m",
      "watchlist_poll_interval": "15-30m",
      "family_scan_interval": "30-60m",
      "write_interval": "5-15m",
      "fresh_threshold": "3h",
      "stale_threshold": "12h",
      "priority_level": "medium",
      "fallback_policy": "fallback_to_cached_station_snapshot",
      "status": "active",
      "version": "v1",
      "notes": "Supplement source; not equal to settlement truth by default."
    },
    {
      "source_name": "metar",
      "source_type": "observation_realtime",
      "primary_use": "observation shock, threshold crossing, forecast divergence",
      "trigger_mode": "poll_bounded_watchlist",
      "selected_market_poll_interval": "1-5m",
      "watchlist_poll_interval": "5-10m",
      "family_scan_interval": "10-30m",
      "write_interval": "1-5m",
      "fresh_threshold": "90m",
      "stale_threshold": "3h",
      "priority_level": "high",
      "fallback_policy": "fallback_to_last_observation_and_downgrade_confidence",
      "status": "active",
      "version": "v1",
      "notes": "Use matched exact-station markets first."
    },
    {
      "source_name": "official_obs",
      "source_type": "observation_official",
      "primary_use": "settlement truth, label, official confirmation",
      "trigger_mode": "poll_batch_backfill",
      "selected_market_poll_interval": "15-60m",
      "watchlist_poll_interval": "60m",
      "family_scan_interval": "6-24h",
      "write_interval": "on_update",
      "fresh_threshold": "6h",
      "stale_threshold": "24h",
      "priority_level": "critical",
      "fallback_policy": "fallback_to_proxy_source_with_explicit_contract_downgrade",
      "status": "active",
      "version": "v1",
      "notes": "Truth anchor for settlement and labels."
    },
    {
      "source_name": "comparison_engine",
      "source_type": "derived_state",
      "primary_use": "probability, edge, divergence, dashboard rows",
      "trigger_mode": "upstream_event_driven",
      "selected_market_poll_interval": "event_driven",
      "watchlist_poll_interval": "1-5m",
      "family_scan_interval": "5-15m",
      "write_interval": "on_recompute",
      "fresh_threshold": "15m",
      "stale_threshold": "60m",
      "priority_level": "high",
      "fallback_policy": "fallback_to_last_successful_comparison_with_stale_badge",
      "status": "active",
      "version": "v1",
      "notes": "Derived only; must not rewrite upstream facts."
    },
    {
      "source_name": "observation_alert_layer",
      "source_type": "derived_alert",
      "primary_use": "single-market realtime alerting",
      "trigger_mode": "observation_first_event_driven",
      "selected_market_poll_interval": "event_driven",
      "watchlist_poll_interval": "1-5m",
      "family_scan_interval": null,
      "write_interval": "on_alert",
      "fresh_threshold": "15m",
      "stale_threshold": "60m",
      "priority_level": "high",
      "fallback_policy": "recompute_from_latest_valid_upstream_facts",
      "status": "active",
      "version": "v1",
      "notes": "Consumes upstream facts only."
    },
    {
      "source_name": "family_scanner",
      "source_type": "derived_scan",
      "primary_use": "family anomaly discovery",
      "trigger_mode": "batch_and_targeted_rescan",
      "selected_market_poll_interval": null,
      "watchlist_poll_interval": null,
      "family_scan_interval": "5-15m",
      "write_interval": "5-15m",
      "fresh_threshold": "30m",
      "stale_threshold": "2h",
      "priority_level": "medium",
      "fallback_policy": "fallback_to_previous_scan_with_degraded_confidence",
      "status": "active",
      "version": "v1",
      "notes": "Not a permission source; analysis only."
    }
  ]
}
```

### 

### **14.2**

**`unit_registry.json`**

```json
{
  "schema_version": "unit_registry.v1",
  "generated_at": "2026-04-21T00:00:00Z",
  "variable_groups": [
    {
      "variable_group": "temperature",
      "raw_units": ["celsius", "fahrenheit"],
      "canonical_unit": "celsius",
      "display_unit": "celsius",
      "conversion_rules": ["c_to_c", "f_to_c"]
    },
    {
      "variable_group": "wind_speed",
      "raw_units": ["kt", "mph", "m/s", "km/h"],
      "canonical_unit": "kt",
      "display_unit": "kt",
      "conversion_rules": ["kt_to_kt", "mph_to_kt", "ms_to_kt", "kmh_to_kt"]
    },
    {
      "variable_group": "precipitation",
      "raw_units": ["mm", "inch"],
      "canonical_unit": "mm",
      "display_unit": "mm",
      "conversion_rules": ["mm_to_mm", "inch_to_mm"]
    },
    {
      "variable_group": "snowfall",
      "raw_units": ["mm", "cm", "inch"],
      "canonical_unit": "mm",
      "display_unit": "mm",
      "conversion_rules": ["mm_to_mm", "cm_to_mm", "inch_to_mm"]
    },
    {
      "variable_group": "climate_index",
      "raw_units": ["source_defined"],
      "canonical_unit": "source_defined",
      "display_unit": "source_defined",
      "conversion_rules": ["identity"]
    }
  ]
}
```

### 

### **14.3**

**`precision_policy_registry.json`**

```json
{
  "schema_version": "precision_policy_registry.v1",
  "generated_at": "2026-04-21T00:00:00Z",
  "policies": [
    {
      "policy_id": "precision_policy.temperature_daily_max.v1",
      "family": "temperature_daily_max",
      "variable_name": "daily_max_temperature",
      "canonical_unit": "celsius",
      "storage_precision": 3,
      "comparison_precision": 2,
      "display_precision": 1,
      "band_precision": "integer",
      "status": "active",
      "version": "v1"
    },
    {
      "policy_id": "precision_policy.temperature_daily_min.v1",
      "family": "temperature_daily_min",
      "variable_name": "daily_min_temperature",
      "canonical_unit": "celsius",
      "storage_precision": 3,
      "comparison_precision": 2,
      "display_precision": 1,
      "band_precision": "integer",
      "status": "active",
      "version": "v1"
    },
    {
      "policy_id": "precision_policy.weather_metric.wind_speed.v1",
      "family": "weather_metric.wind_speed",
      "variable_name": "wind_speed",
      "canonical_unit": "kt",
      "storage_precision": 3,
      "comparison_precision": 2,
      "display_precision": 1,
      "band_precision": 1,
      "status": "active",
      "version": "v1"
    },
    {
      "policy_id": "precision_policy.weather_metric.precipitation.v1",
      "family": "weather_metric.precipitation",
      "variable_name": "precipitation_amount",
      "canonical_unit": "mm",
      "storage_precision": 3,
      "comparison_precision": 2,
      "display_precision": 1,
      "band_precision": 1,
      "status": "active",
      "version": "v1"
    },
    {
      "policy_id": "precision_policy.weather_metric.snowfall.v1",
      "family": "weather_metric.snowfall",
      "variable_name": "snowfall_amount",
      "canonical_unit": "mm",
      "storage_precision": 3,
      "comparison_precision": 2,
      "display_precision": 1,
      "band_precision": 1,
      "status": "active",
      "version": "v1"
    }
  ]
}
```

### 

### **14.4**

**`rounding_policy_registry.json`**

```json
{
  "schema_version": "rounding_policy_registry.v1",
  "generated_at": "2026-04-21T00:00:00Z",
  "policies": [
    {
      "policy_id": "rounding_policy.temperature_daily_max.v1",
      "family": "temperature_daily_max",
      "rules": [
        {
          "applies_to": "display",
          "rounding_rule": "round_half_up"
        },
        {
          "applies_to": "band_mapping",
          "rounding_rule": "round_half_up"
        }
      ],
      "status": "active",
      "version": "v1"
    },
    {
      "policy_id": "rounding_policy.weather_metric.precipitation.v1",
      "family": "weather_metric.precipitation",
      "rules": [
        {
          "applies_to": "display",
          "rounding_rule": "round_half_up"
        },
        {
          "applies_to": "threshold_compare",
          "rounding_rule": "exact_no_rounding"
        }
      ],
      "status": "active",
      "version": "v1"
    },
    {
      "policy_id": "rounding_policy.weather_metric.wind_speed.v1",
      "family": "weather_metric.wind_speed",
      "rules": [
        {
          "applies_to": "display",
          "rounding_rule": "round_half_up"
        },
        {
          "applies_to": "band_mapping",
          "rounding_rule": "round_half_up"
        }
      ],
      "status": "active",
      "version": "v1"
    }
  ]
}
```

### 

### **14.5**

**`band_mapping_policy_registry.json`**

```json
{
  "schema_version": "band_mapping_policy_registry.v1",
  "generated_at": "2026-04-21T00:00:00Z",
  "policies": [
    {
      "policy_id": "band_mapping.temperature_celsius_integer.v1",
      "band_scheme": "temperature_celsius_integer",
      "canonical_unit": "celsius",
      "band_precision": "integer",
      "rounding_rule": "round_half_up",
      "mapping_formula": "band = int(round_half_up(canonical_value))",
      "status": "active",
      "version": "v1"
    },
    {
      "policy_id": "band_mapping.wind_speed_threshold_knots.v1",
      "band_scheme": "wind_speed_threshold_knots",
      "canonical_unit": "kt",
      "band_precision": 1,
      "rounding_rule": "round_half_up",
      "mapping_formula": "compare threshold against canonical kt using policy precision",
      "status": "active",
      "version": "v1"
    },
    {
      "policy_id": "band_mapping.precipitation_mm_threshold.v1",
      "band_scheme": "precipitation_mm_threshold",
      "canonical_unit": "mm",
      "band_precision": 1,
      "rounding_rule": "exact_no_rounding",
      "mapping_formula": "threshold compare uses canonical mm without pre-rounding",
      "status": "active",
      "version": "v1"
    }
  ]
}
```

## **15. Schema 草案：带 Normalization 字段的核心对象**

本节基于前述 source / measurement registry，补充 `ForecastSnapshot`、`ObservationSnapshot` 与 `TopParameterView` 的 normalization-aware schema 草案，作为后续 loader / normalizer / band mapper 的稳定输入输出基础。

### **15.1 设计目标**

这三个对象需要满足：

1. 同时保留 raw fields 与 canonical fields。
2. 任何 comparison / alert / anomaly 只允许基于 canonical fields 计算。
3. UI 默认展示 canonical fields，必要时可展开 raw fields 审查。
4. 每个对象都必须能回指到所使用的 normalization / precision / rounding / band mapping policy。

---

### 

### 

### **15.2**

**`ForecastSnapshot`**

**Schema 草案**

#### **15.2.1 用途**

表示某个 market 在当前 forecast source 下的标准化预测结果。

#### **15.2.2 字段建议**

```json
{
  "schema_version": "forecast_snapshot.v2",
  "forecast_snapshot_id": "fcst_20260421_379803_001",
  "market_id": "379803",
  "market_family": "temperature_daily_max",
  "variable_name": "daily_max_temperature",
  "target_date": "2026-04-16",
  "station_id": "ZSPD",
  "source_name": "ecmwf",
  "source_mode": "publish_aware_cache",
  "source_confidence": 0.82,
  "freshness_status": "fresh",
  "source_generated_at": "2026-04-21T00:00:00Z",
  "fetched_at": "2026-04-21T00:10:00Z",

  "raw_value": 84.2,
  "raw_unit": "fahrenheit",
  "canonical_value": 29.0,
  "canonical_unit": "celsius",
  "display_value": 29.0,
  "display_unit": "celsius",

  "model_band": "29",
  "band_scheme": "temperature_celsius_integer",

  "conversion_rule": "f_to_c",
  "conversion_applied": true,
  "precision_policy_ref": "precision_policy.temperature_daily_max.v1",
  "rounding_policy_ref": "rounding_policy.temperature_daily_max.v1",
  "band_mapping_policy_ref": "band_mapping.temperature_celsius_integer.v1",
  "normalization_version": "measurement_normalization.v1",

  "target_window": {
    "start": "2026-04-16T00:00:00+08:00",
    "end": "2026-04-16T23:59:59+08:00"
  },
  "upstream_refs": {
    "market_rule_ref": "rule_379803_zspd_v1",
    "source_policy_ref": "source_policy_registry.v1:ecmwf"
  }
}
```

#### **15.2.3 关键治理要求**

- `raw_value` 与 `raw_unit` 必须保留，禁止只写 canonical value。
- `canonical_value` 是 comparison / probability / alert 的唯一数值输入。
- `model_band` 必须由 `band_mapping_policy_ref` 生成，不允许由 UI 或 comparison 层临时映射。
- `display_value` 仅用于展示；若未单独存储，也必须能由 canonical value + display precision 重建。

---

### 

### 

### **15.3**

**`ObservationSnapshot`**

**Schema 草案**

#### **15.3.1 用途**

表示某个 market 对应 station / official source 的标准化观测结果。

#### **15.3.2 字段建议**

```json
{
  "schema_version": "observation_snapshot.v2",
  "observation_snapshot_id": "obs_20260421_379803_001",
  "market_id": "379803",
  "market_family": "temperature_daily_max",
  "variable_name": "daily_max_temperature",
  "target_date": "2026-04-16",
  "station_id": "ZSPD",
  "station_name": "Shanghai Pudong Intl Airport",
  "source_name": "metar",
  "settlement_source_type": "station_observation",
  "official_vs_proxy_source": "proxy",
  "source_match_grade": "exact_station",
  "source_confidence": 0.74,
  "freshness_status": "fresh",
  "observed_at": "2026-04-21T00:09:00Z",
  "fetched_at": "2026-04-21T00:10:00Z",

  "raw_value": 84.2,
  "raw_unit": "fahrenheit",
  "canonical_value": 29.0,
  "canonical_unit": "celsius",
  "display_value": 29.0,
  "display_unit": "celsius",

  "observation_band": "29",
  "settlement_ready": false,

  "conversion_rule": "f_to_c",
  "conversion_applied": true,
  "precision_policy_ref": "precision_policy.temperature_daily_max.v1",
  "rounding_policy_ref": "rounding_policy.temperature_daily_max.v1",
  "band_mapping_policy_ref": "band_mapping.temperature_celsius_integer.v1",
  "normalization_version": "measurement_normalization.v1",

  "raw_text": "ZSPD 210009Z ...",
  "upstream_refs": {
    "market_rule_ref": "rule_379803_zspd_v1",
    "source_policy_ref": "source_policy_registry.v1:metar"
  }
}
```

#### **15.3.3 关键治理要求**

- observation alert 指标必须使用 `canonical_value` 和 `observation_band`，不能直接使用 raw value。
- `source_match_grade` 与 `official_vs_proxy_source` 必须跟着 observation 一起流转，不能只存在 resolver report 里。
- `settlement_ready` 只表示接近结算或可用于 truth alignment，不等价于已成为最终官方结算值。

---

### 

### 

### **15.4**

**`TopParameterView`**

**Schema 草案（Normalization-aware）**

#### **15.4.1 用途**

作为 dashboard / Telegram / gateway / comparison-engine 首屏参数聚合对象，展示 market、weather、forecast、source contract 与 decision 参数。

#### **15.4.2 字段建议**

```json
{
  "schema_version": "top_parameter_view.v2",
  "market_id": "379803",
  "market_question": "Highest temperature in Shanghai on April 16?",
  "market_family": "temperature_daily_max",
  "location_name": "Shanghai",
  "target_date": "2026-04-16",
  "variable_name": "daily_max_temperature",

  "polymarket": {
    "yes_price": 0.63,
    "no_price": 0.37,
    "market_implied_probability": 0.63,
    "favored_side": "yes",
    "market_band": "29",
    "spread": 0.02,
    "updated_at": "2026-04-21T00:10:00Z"
  },

  "weather": {
    "raw_value": 84.2,
    "raw_unit": "fahrenheit",
    "canonical_value": 29.0,
    "canonical_unit": "celsius",
    "display_value": 29.0,
    "display_unit": "celsius",
    "observation_band": "29",
    "observed_at": "2026-04-21T00:09:00Z",
    "station_id": "ZSPD",
    "settlement_ready": false
  },

  "forecast": {
    "raw_value": 84.2,
    "raw_unit": "fahrenheit",
    "canonical_value": 29.0,
    "canonical_unit": "celsius",
    "display_value": 29.0,
    "display_unit": "celsius",
    "model_band": "29",
    "forecast_timestamp": "2026-04-21T00:00:00Z",
    "source_mode": "publish_aware_cache",
    "source_confidence": 0.82
  },

  "source_contract": {
    "settlement_source_type": "station_observation",
    "official_vs_proxy_source": "proxy",
    "source_match_grade": "exact_station",
    "required_sources": [
      "metar",
      "ecmwf"
    ],
    "official_source_url": "https://www.wunderground.com/history/weekly/cn/shanghai/ZSPD",
    "freshness_status": "fresh"
  },

  "decision": {
    "fair_value": 0.71,
    "model_probability": 0.71,
    "edge": 0.08,
    "confidence_adjusted_edge": 0.06,
    "probability_mode": "shadow_calibrated_candidate",
    "execution_constraint": "dry_run_only",
    "can_execute": false,
    "primary_block_reason": "shadow_only"
  },

  "normalization": {
    "precision_policy_ref": "precision_policy.temperature_daily_max.v1",
    "rounding_policy_ref": "rounding_policy.temperature_daily_max.v1",
    "band_mapping_policy_ref": "band_mapping.temperature_celsius_integer.v1",
    "normalization_version": "measurement_normalization.v1"
  },

  "upstream_refs": {
    "market_snapshot_ref": "mkt_379803_001",
    "market_rule_ref": "rule_379803_zspd_v1",
    "forecast_snapshot_ref": "fcst_20260421_379803_001",
    "observation_snapshot_ref": "obs_20260421_379803_001",
    "comparison_point_ref": "cmp_20260421_379803_001"
  }
}
```

#### **15.4.3 关键治理要求**

- `TopParameterView` 仍然只是聚合对象，不是新的事实源。
- 顶层默认展示 `display_value` / `display_unit`，但必须可回看 `raw_value` 与 `canonical_value`。
- `weather` 与 `forecast` 段都必须显式携带 normalization fields，防止前端各自做单位转换。
- `normalization` 段用于统一说明当前首屏所使用的 measurement policy refs。

---

### **15.5 Comparison / Alert / Anomaly 的强制输入规则**

为避免后续模块再次混用 raw/canonical 字段，建议明确以下强制规则：

#### **Comparison Layer**

- 只能使用：`canonical_value`、`canonical_unit`、`model_band`、`observation_band`
- 禁止直接使用：`raw_value`

#### **Observation Alert Layer**

- 只能使用：`canonical_value`、`observed_at`、`observation_band`
- shock / divergence / threshold compare 必须绑定 `precision_policy_ref` 与 `band_mapping_policy_ref`

#### **Family Scanner**

- peer comparison、edge dislocation、evidence mismatch 必须统一基于 canonical values 与标准 band

#### **Top Parameter UI**

- 默认展示：`display_value`
- 审查展开时展示：`raw_value`、`raw_unit`、`canonical_value`、`canonical_unit`

---

### **15.6 最小实施建议**

#### **Step 1**

先将 `ForecastSnapshot` / `ObservationSnapshot` / `TopParameterView` 升级为 `v2` schema，并补 normalization fields。

#### **Step 2**

在 `weather_data_adapters` 中统一引入 normalization step：

- raw -> canonical
- precision policy binding
- band mapping binding

#### **Step 3**

让以下层只吃 canonical fields：

- `comparison_layer`
- `observation_alert_layer`
- `family_scanner`

#### **Step 4**

增加测试矩阵：

- Fahrenheit -> Celsius
- inch -> mm
- mph -> kt
- canonical / display / band mapping consistency

## **16. 术语与缩略语（新增）**

本章补充 Phase 28 / Phase 29 相关术语、缩略语与字段解释，用于统一 Opportunity Board、Single Market Workstation、Monitoring Collection、Alert / Anomaly / Gate / Ops 各层语义。

### **16.1 术语表**

|**术语**|**定义**|
|---|---|
|`Opportunity Board`|上层机会发现板，用于城市 / family / 市场优先级排序，不直接给出执行许可。|
|`Single Market Workstation`|单市场统一工作台，用于在统一上下文中查看参数、证据、告警、异常、验证与 gate。|
|`Opportunity Score`|用于表示某城市 / family / 市场当前“值得优先审查”的程度，不等于交易结论。|
|`Difficulty Score`|用于表示某城市 / family / 市场“做起来有多难”的程度，不等于 gate block。|
|`Best Model`|当前城市 / family 下优先推荐的主参考 forecast 模型。|
|`Best Source Stack`|当前城市 / family 下推荐的 source 组合，通常包含 forecast / realtime observation / official truth 三类来源。|
|`Source Precision`|source 与市场结算口径的匹配程度，主要由 `source_match_grade`、`official_vs_proxy_source`、resolver confidence 等因素决定。|
|`Freshness`|source 当前数据的新鲜度状态，用于指示数据是否可作为高可信输入。|
|`Alert`|单市场实时预警事件，描述 observation / forecast / market 的局部异常。|
|`Anomaly`|family 级异常事件，描述市场在群体中的偏离、异常波动或结构性异常。|
|`Gate`|执行许可边界，决定当前是否可执行。|
|`Ops`|运行时系统级状态、队列与阻断信息，不等同于市场层 alert/anomaly。|
|`Canonical Value`|经过单位转换、精度与 rounding 治理后用于正式计算的标准值。|
|`Raw Value`|source 原始值，仅用于审查、回放与审计，不直接进入正式比较。|
|`Display Value`|展示值，用于 UI/Telegram 呈现，不参与正式计算。|
|`Band Mapping`|将 canonical value 映射为 market / model / observation / official band 的过程。|
|`Recommended Action`|基于机会、难度、source 与 freshness 给出的 operator 建议动作，如 `prioritize_review`、`watch`、`avoid`。|

### **16.2 缩略语表**

|**缩略语**|**全称**|**说明**|
|---|---|---|
|`Opp`|Opportunity|机会分数或机会优先级|
|`Diff`|Difficulty|难度分数或难度标签|
|`FV`|Fair Value|模型 fair value|
|`Obs`|Observation|观测值 / 观测源|
|`Fcst`|Forecast|预测值 / 预测源|
|`Src`|Source|数据源|
|`SP`|Source Precision|source 精度|
|`Fresh`|Freshness|新鲜度|
|`RR`|Resolver Result / Resolver Rule|resolver 输出或 rule contract|
|`TPV`|Top Parameter View|顶层参数聚合合同|
|`MWV`|Market Workstation View|单市场工作台聚合对象|
|`OBV`|Opportunity Board View|机会板聚合对象|
|`LLM`|Large Language Model|大语言模型|
|`MVP`|Minimum Viable Product|最小可用版本|

### **16.3 术语治理要求**

- `Opportunity Score`、`Difficulty Score`、`Best Model`、`Recommended Action` 均属于 operator prioritization 语义，不属于 execution permission 语义。
- `Alert` 与 `Anomaly` 必须与 `Gate`、`Ops` 分层显示，不得混用。
- `Canonical Value` 是 comparison / alert / anomaly / validation 的唯一正式数值输入；`Display Value` 仅用于展示；`Raw Value` 仅用于审查与回放。
- `Best Model` 是推荐而不是唯一 truth source；`Best Source Stack` 是建议而不是硬约束。

## **17. 字段数值选取治理设计**

本章针对 Opportunity Board 与 Single Market Workstation 中新增或强化字段的数值选取方式，给出正式治理设计。目标是避免字段看似精确、实则口径漂移，确保所有分数、标签与推荐都可解释、可回放、可被 registry-first 管理。

### **17.1 总体原则**

#### **原则 1：字段必须分层**

字段按语义分为四类：

- 事实字段（facts）
- 派生字段（derived metrics）
- 排序字段（ranking / prioritization）
- 建议字段（recommendation）

#### **原则 2：禁止把建议字段伪装成事实字段**

例如：

- `best_model`
- `recommended_action`
- `difficulty_label`  
    不得被视为 market truth。

#### **原则 3：所有数值字段必须可追溯**

凡是 score / label / recommendation，必须能回指到：

- 输入字段
- policy refs
- 计算版本
- 计算时间

#### 

#### **原则 4：score 默认归一到**

**`[0,1]`**

除非明确另有规定，Opportunity / Difficulty / Precision / Freshness / Confidence 类 score 应使用 `[0,1]` 区间，便于统一排序、过滤和 explainability。

#### **原则 5：label 不直接手填**

像 `easy / medium / hard`、`prioritize_review / watch / avoid` 等标签，必须由 score + policy 规则映射得出。

---

### **17.2 字段分类治理表**

|**字段类别**|**典型字段**|**数值来源**|**是否可人工写入**|**是否进入 gate**|
|---|---|---|---|---|
|事实字段|`yes_price`, `canonical_value`, `model_band`, `source_match_grade`|上游事实对象|否|可作为 gate 输入|
|派生字段|`edge`, `market_lag_score`, `source_precision_score`|上游事实 + policy|否|可间接作为 gate 输入|
|排序字段|`opportunity_score`, `difficulty_score`, `opportunity_rank`|派生字段 + ranking policy|否|否|
|建议字段|`best_model`, `best_source_stack`, `recommended_action`, `difficulty_label`|score + registry mapping|可作为 seed，但正式值应系统生成|否|

---

### 

### 

### **17.3**

**`opportunity_score`**

**治理设计**

#### **定义**

`opportunity_score` 表示某个城市 / family / 市场当前值得优先审查的程度。

#### **允许输入**

- `confidence_adjusted_edge`
- `market_lag_score`
- `source_precision_score`
- `freshness_score`
- `liquidity_score`
- `anomaly_penalty_score`

#### **禁止输入**

- `can_execute`
- `gate_stack allow/deny`
- 人工主观文本说明

#### **计算规则**

首版采用线性可解释加权：

```text
opportunity_score
= w1 * edge_component
+ w2 * market_lag_component
+ w3 * source_precision_component
+ w4 * freshness_component
+ w5 * liquidity_component
- w6 * anomaly_penalty_component
```

#### **治理要求**

- 所有 component 必须先标准化到 `[0,1]`
- 权重来自 `opportunity_scoring_policy`
- 输出必须带 `opportunity_components` 和 `scoring_policy_ref`
- 该字段仅用于排序和优先级，不进入 execution gate

---

### 

### 

### **17.4**

**`difficulty_score`**

**治理设计**

#### **定义**

`difficulty_score` 表示某个市场“做起来有多难”的程度。

#### **允许输入**

- `source_match_grade`
- `official_vs_proxy_source`
- `resolver_confidence`
- settlement clarity
- freshness reliability
- market complexity

#### **输出**

- `difficulty_score` in `[0,1]`
- `difficulty_label = easy | medium | hard`

#### **标签映射**

建议统一映射：

- `0.00 - 0.33 -> easy`
- `0.34 - 0.66 -> medium`
- `0.67 - 1.00 -> hard`

#### **治理要求**

- label 必须由 `difficulty_score` + `difficulty_label_policy` 生成
- `difficulty_score` 不等价于 risk gate block
- 输出必须带 `difficulty_components`

---

### 

### 

### 

### 

### **17.5**

**`best_model`**

**/**

**`best_source_stack`**

**治理设计**

#### **定义**

- `best_model`：主推荐 forecast 模型
- `best_source_stack`：推荐 source 组合

#### **输入**

- family candidate set
- source availability
- source freshness reliability
- source precision fit
- validation support

#### **输出**

- `best_model`
- `best_source_stack`
- `best_model_reason`
- `source_stack_reason`

#### **治理要求**

- `best_model` 必须来自 `model_recommendation_policy`
- 不得由 dashboard 或 telegram 本地猜测
- `best_model` 不等于唯一允许 source
- 若 source unavailable，应可输出 fallback model / stack

---

### 

### 

### **17.6**

**`recommended_action`**

**治理设计**

#### **定义**

给 operator 的动作建议，不是 execution permission。

#### **建议枚举**

- `prioritize_review`
- `open_workstation`
- `watch`
- `avoid`

#### **生成规则**

建议由以下条件映射：

- `opportunity_score`
- `difficulty_score`
- `freshness_status`
- `source_precision_score`
- latest alert / anomaly state

#### **治理要求**

- `recommended_action` 必须来自 `action_mapping_policy`
- 不得直接输出下单指令
- 不得在 gateway 中被解释为 execution allow

---

### 

### 

### **17.7**

**`source_precision_score`**

**治理设计**

#### **定义**

反映 source 与市场结算口径的匹配程度。

#### **推荐映射基线**

- `exact_station + official -> 1.00`
- `exact_station + proxy -> 0.80`
- `family_exact + official -> 0.70`
- `family_exact + proxy -> 0.55`
- `family_only -> 0.30`
- `unmatched -> 0.00`

#### **治理要求**

- 映射必须来自 `source_precision_policy`
- 不得在 detector / board / UI 中单独重写映射

---

### 

### 

### 

### 

### **17.8**

**`freshness_status`**

**/**

**`freshness_score`**

**治理设计**

#### **定义**

- `freshness_status`：离散状态（`fresh / stale / unavailable`）
- `freshness_score`：排序/优先级分数（`[0,1]`）

#### **推荐映射**

- `fresh -> 1.00`
- `stale -> 0.45`
- `unavailable -> 0.00`

#### **治理要求**

- `freshness_status` 必须由 source policy registry 生成
- `freshness_score` 必须由 `freshness_mapping_policy` 生成
- `freshness_score` 可进入 `opportunity_score` / `difficulty_score`，但不应替代原始 freshness 状态展示

---

### 

### 

### 

### 

### **17.9**

**`alert_count`**

**/**

**`anomaly_count`**

**治理设计**

#### **定义**

在指定 lookback window 内，该 city / family / market 聚合到的 alert / anomaly 事件数量。

#### **治理要求**

- 必须显式声明聚合窗口，如 `last_24h`、`last_7d`
- 必须区分：
    - count
    - distinct market count
    - latest severity / latest anomaly score
- 不得只给 count 不说明窗口

---

### **17.10 解释字段（Explainability Fields）治理设计**

所有 score / label / recommendation 必须配套 explainability 字段。

#### **必备 explainability 字段**

- `components`
- `policy_ref`
- `generated_at`
- `version`
- `upstream_refs`

#### **适用对象**

- `opportunity_score`
- `difficulty_score`
- `best_model`
- `best_source_stack`
- `recommended_action`

---

### **17.11 推荐新增 policy registry**

建议新增：

```text
opportunity_policy_registry/
  opportunity_scoring_policy.json
  difficulty_scoring_policy.json
  model_recommendation_policy.json
  action_mapping_policy.json
  freshness_mapping_policy.json
  source_precision_policy.json
```

各 policy 至少应包含：

- `policy_id`
- `applicable_scope`
- `formula_or_mapping`
- `version`
- `status`
- `notes`

---

### **17.12 输出 contract 增补要求**

在 `opportunity_board_view.v1` 和 `opportunity_explanation.v1` 中，建议为每行增加：

- `opportunity_policy_ref`
- `difficulty_policy_ref`
- `model_recommendation_policy_ref`
- `action_mapping_policy_ref`
- `freshness_mapping_policy_ref`
- `source_precision_policy_ref`

这样后续任何排序、推荐、标签都能审计和回放。

## **18. 当前结论**

在 Phase 28 / 29 相关字段中：

- 事实字段必须继续遵守唯一事实链
- 派生字段必须基于 canonical fields
- 排序字段必须使用可解释、可审计的 scoring policy
- 建议字段必须通过 policy 生成，不得由前端或 operator 本地猜测

只有这样，Opportunity Board 与 Single Market Workstation 中的这些新增字段，才能在不破坏既有数据治理与 gate 边界的前提下稳定落地。