# AARS Polymarket Weather Trading Console UI 图例与状态规范

版本：v0.1  
日期：2026-04-24  
适用范围：`weather-dashboard`、`weather-telegram-console`、`weather-comparison-engine` 的只读可视化、监控台、工作台、机会板、监测面板

相关文档：

- [AARS_Polymarket_Weather_Trading_UI_Design_Status_Roadmap.md](./AARS_Polymarket_Weather_Trading_UI_Design_Status_Roadmap.md)
- [AARS_Polymarket_Weather_Trading_Implementation_Plan_Status.md](./AARS_Polymarket_Weather_Trading_Implementation_Plan_Status.md)
- [AARS_Polymarket_Weather_Trading_Detailed_Design.md](./AARS_Polymarket_Weather_Trading_Detailed_Design.md)

---

## 1. 文档目标

本文档定义 AARS Polymarket Weather Trading Console 的统一界面图例与状态规范，用于保证：

1. 页面视觉风格一致。
2. 状态颜色含义一致。
3. 数据质量标识一致。
4. 实时刷新、阻断、异常、告警的语义不混淆。
5. Dashboard、Telegram、Console 三个表面的用词和颜色体系一致。

本文档重点回答四类问题：

- 这个值是否实时更新。
- 这个值是否已经过时。
- 这个值是否被阻断。
- 这个值的数据质量是否较差。

---

## 2. 设计原则

### 2.1 前景必须清晰压住背景

页面文字必须和背景明显区分，禁止出现“灰字压灰底”。

要求：

- 正文值必须接近 off-white 或白。
- 标签文字必须比背景亮至少一个明显等级。
- 低对比灰字只能用于次级注释，不得用于关键数值。

### 2.2 线条必须细、淡、统一

页面分割线、卡片边线、标题线条必须统一使用低饱和细灰线。

要求：

- 不使用厚重装饰边。
- 不使用高饱和霓虹边。
- 不用大面积发光描边。
- 不用强烈渐变作为主分割方式。

### 2.3 一屏优先

操作台默认态必须尽量在一个屏幕内完成监控。

要求：

- 关键状态放首屏。
- 长列表进入折叠区。
- 详情默认收起。
- 标题短、卡片短、字段短。

### 2.4 状态语义优先于装饰语义

颜色和标签必须首先表达状态，不做无意义装饰。

优先级：

1. LIVE / STALE / BLOCKED
2. ALERT / ANOM / GATE / OPS
3. 数据质量标识 `B`
4. 纯视觉装饰

---

## 3. 基础视觉基调

### 3.1 推荐背景与表面

| Token | 含义 | 推荐值 |
|---|---|---|
| `--ops-bg` | 页面底色 | `#050608` |
| `--ops-bg-2` | 页面次底色 | `#0a0c10` |
| `--ops-surface` | 卡片主表面 | `#10141a` |
| `--ops-surface-2` | 卡片副表面 | `#141922` |
| `--ops-surface-3` | 更高层表面 | `#191f29` |

### 3.2 推荐文本与边线

| Token | 含义 | 推荐值 |
|---|---|---|
| `--ops-text` | 主文本 | `#f1f4f7` |
| `--ops-text-muted` | 次级文本 | `#9aa3ad` |
| `--ops-text-dim` | 弱提示文本 | `#72808e` |
| `--ops-border` | 细边线 | `rgba(255, 255, 255, 0.08)` |
| `--ops-border-strong` | 强边线 | `rgba(91, 148, 225, 0.28)` |

### 3.3 推荐强调色

| Token | 含义 | 推荐值 |
|---|---|---|
| `--ops-accent` | 主强调蓝 | `#4f8fe6` |
| `--ops-accent-2` | 次强调蓝 | `#3f6fa8` |
| `--ops-good` | 正常 / LIVE | `#69d39a` |
| `--ops-warn` | 异常 / ANOM | `#d7ab57` |
| `--ops-bad` | 告警 / BLOCKED | `#d96d67` |
| `--ops-quality-bad` | 数据质量差 / B | `#ff73e1` |

---

## 4. 状态图例

### 4.1 LIVE

含义：

- 数据正在刷新。
- 当前值在有效窗口内。
- 不代表结论正确，只代表“当前可用且在更新”。

视觉：

- 绿色圆点。
- 绿色或浅绿色文字。
- 可配轻微呼吸动画。

适用场景：

- 页面心跳。
- 最近刷新时间。
- 扫描状态正常。
- freshness 正常。

### 4.2 STALE

含义：

- 数据仍可见，但已变旧。
- 需要 operator 关注是否过期。
- 不应当与 LIVE 混为一类。

视觉：

- 琥珀色。
- 用于过期、延迟、弱化、等待刷新。

适用场景：

- freshness 变旧。
- 证据时间轴过时。
- 低优先级但未失效。

### 4.2.1 ANOM

含义：

- 该值或该市场处于异常状态，需要安全复核。
- 与 `BLOCKED` 不同，ANOM 表示“偏离/异常”而非“被阻断”。

视觉：

- 安全黄色。
- 用于 anomaly、轻中度偏离、异常但未被 gate 阻断的场景。

适用场景：

- family anomaly。
- evidence mismatch。
- forecast divergence。
- 市场偏离但仍可审查。

### 4.3 BLOCKED

含义：

- 数据、规则、验证、gate 或执行边界阻断。
- 阻断不等于错误，有时是正确的保护状态。

视觉：

- 红色或偏红橙色。
- 用于 gate、authorization、validation blockage。

适用场景：

- can_execute = false。
- resolver / source mismatch。
- validation blocked。
- execution blocked。

### 4.3.1 ALERT

含义：

- 该值或该市场已进入告警状态，需要立即注意。
- 与 `ANOM` 不同，ALERT 表示更高优先级的风险提醒。

视觉：

- 红色。
- 用于市场告警、严重 source 风险、运维告警、系统性异常。

适用场景：

- market_alert_event。
- scanner_ops_alert。
- 严重 source unavailable。
- 运维阻断、队列风暴、执行边界红灯。

### 4.4 DATA QUALITY `B`

含义：

- 该值数据质量较差。
- 这不是状态本身，而是对值可信度的附加标记。
- `B` 表示 “Bad quality”。

视觉：

- 品红色 `B`。
- 仅放在字段旁边，不占整行主状态。

适用场景：

- source precision 较差。
- resolver confidence 过低。
- 证据缺失或不完整。
- label coverage / normalization coverage 偏低。
- 观测或 forecast 仅为 fallback / proxy。

触发条件建议：

- `data_quality = bad`
- `quality = poor`
- `quality_level = low`

### 4.5 补充状态图例

| 图例 | 含义 | 颜色 |
|---|---|---|
| `ALERT` | 市场层告警 | 红 / 橙红 |
| `ANOM` | family 异常 | 安全黄色 |
| `GATE` | 执行边界 | 蓝灰 / 红灰 |
| `OPS` | 系统运维状态 | 灰蓝 / 琥珀 |

---

## 5. 数据质量规范

### 5.1 定义

数据质量标识用于描述“这个值靠不靠谱”，不用于替代业务结论。

### 5.2 推荐分级

| 质量 | 含义 | 是否显示 `B` |
|---|---|---|
| `good` / `high` / `excellent` | 可信度正常 | 否 |
| `fair` / `warning` | 可用但需注意 | 可选 |
| `bad` / `poor` / `low` | 明显偏弱 | 是，显示 `B` |

### 5.3 建议触发点

建议在以下字段上支持质量标记：

- `Source Match`
- `Resolver Confidence`
- `Freshness`
- `Forecast`
- `Observation`
- `Label Coverage`
- `Source Precision`
- `Validation Status`
- `Scanner Status`
- `Source Health`

### 5.4 品红 `B` 的使用规则

要求：

1. 只对字段级质量差的值打 `B`。
2. 不对整个页面乱贴 `B`。
3. 不和 `BLOCKED` 混用。
4. `B` 代表“值质量差”，不是“业务失败”。

---

## 6. 页面级图例规范

### 6.1 页头

页头仅放最少的全局状态：

- LIVE 心跳。
- 自动刷新间隔。
- 当前页最后刷新时间。
- 关键系统总览。

页头不应堆满字段。

### 6.2 分区标题

分区标题应满足：

- 短。
- 大小写统一。
- 不要长条灰块。
- 需要用细线和小点辅助分隔。

### 6.3 卡片标题

卡片标题应满足：

- 小于正文块长度。
- 保持一行优先。
- 避免整块灰色标题栏。

### 6.4 字段行

字段行应同时支持：

- 状态徽标：LIVE / STALE / BLOCKED
- 质量徽标：B

推荐顺序：

1. 字段名
2. 状态徽标
3. 质量徽标
4. 字段值

---

## 7. 组件适用范围

### 7.1 Operations Monitor

适用：

- 页面页头 LIVE 心跳。
- Scanner / Queue / Gate。
- Focus Markets。
- Market Radar。
- Quick Detail。

### 7.2 Opportunity Board

适用：

- Opportunity score。
- Difficulty score。
- Best model / source stack。
- Validation / Promotion。
- Family anomaly 概览。

### 7.3 Single Market Workstation

适用：

- Top Parameter Ribbon。
- Rule / Source / Model。
- Evidence Timeline。
- Validation / Compare。
- Gate / Advisory / Dry-run。

### 7.4 Monitoring Signals

适用：

- Scanner Status。
- Source Policy。
- Universe Snapshot。
- Evidence Scan。
- Alert Queue。

---

## 8. 交互规范

### 8.1 自动刷新

默认页面应尽可能支持自动刷新。

建议节奏：

- Operations Monitor：15 秒。
- Monitoring Signals：15 秒。
- Single Market Workstation：20 秒。
- Opportunity Board：30 秒。

### 8.2 视觉反馈

当页面刷新时：

- LIVE 心跳点轻微呼吸。
- 刷新时间更新。
- 关键值保持稳定结构，不要跳版。

### 8.3 状态更新原则

状态变化时：

- 优先更新标签，不先改布局。
- 优先改数值，不改变信息结构。
- 不要让状态颜色压过数据本身。

---

## 9. 实施约束

### 9.1 不做的事

不建议：

- 用紫色做主背景。
- 用大面积渐变装饰。
- 用灰色标题条遮住视觉。
- 用多种高饱和状态色同时竞争。
- 把质量标记做成过多字母体系。

### 9.2 一致性要求

所有新页面都必须遵守：

- 同一组颜色 token。
- 同一组状态图例。
- 同一组质量标记。
- 同一组 LIVE / STALE / BLOCKED 语义。

---

## 10. 推荐最小图例卡

每个主页面建议在首屏角落保留一个最小图例卡：

| 图例 | 说明 |
|---|---|
| LIVE | 自动更新中 |
| STALE | 值已变旧 |
| BLOCKED | 被规则或边界阻断 |
| B | 数据质量差 |

如果页面空间紧张，可只保留图标，不保留说明文本。

---

## 11. 结论

这套图例规范的核心不是“做更多颜色”，而是把颜色收敛成少数几个可解释状态：

- 绿色表示可用和实时。
- 琥珀表示变旧和需要注意。
- 红色表示阻断。
- 品红 `B` 表示数据质量差。

这样 UI 才能同时满足：

- 一屏监控。
- 高对比可读。
- 数据质量提示。
- 实时运行态识别。
- 控制台式统一语言。

---

## 12. Runtime State Governance v1

本节对齐 [AARS_Polymarket_Weather_Trading_UI_Runtime_Architecture.md](./AARS_Polymarket_Weather_Trading_UI_Runtime_Architecture.md)，将状态图例从视觉规范升级为运行时治理规则。

### 12.1 状态总表

| 状态 | 类型 | 主状态可用 | 次状态可用 | 影响 gate | 可触发 operator action | 颜色 |
|---|---|---|---|---|---|---|
| LIVE | freshness | 否 | 是 | 间接 | 否 | green |
| STALE | freshness | 是 | 是 | 间接 | 是 | blue / amber |
| ALERT | market signal | 是 | 是 | 否 | 是 | red |
| ANOM | anomaly signal | 是 | 是 | 否 | 是 | amber |
| BLOCKED | gate state | 是 | 是 | 是 | 是 | red |
| NORMAL | display state | 是 | 否 | 否 | 否 | green / neutral |
| ALLOW | gate state | 否 | 是 | 是 | 否 | green |
| B | data quality | 否 | 是 | 间接 | 是 | magenta |
| OPS | system state | 不用于 market card 主状态 | 是 | 否 | 是 | red / amber |
| FOCUS | view state | 否 | 是 | 否 | 否 | blue |
| WATCH | view group | 否 | 是 | 否 | 否 | amber / neutral |

### 12.2 主状态 contract

所有市场卡片、Focus 卡、Quick Detail 必须使用统一字段：

```json
{
  "primary_state": "BLOCKED",
  "primary_state_reason": "Gate blocked by validation coverage below threshold",
  "secondary_states": ["LIVE", "DATA_QUALITY_B"],
  "display_priority": 92
}
```

主状态优先级：

```text
BLOCKED > ALERT > ANOM > STALE > NORMAL
```

生成规则：

```text
if can_execute == false and primary_block_reason exists:
    primary_state = BLOCKED
elif latest_alert_severity in ["red", "amber"]:
    primary_state = ALERT
elif latest_anomaly_score >= anomaly_threshold:
    primary_state = ANOM
elif freshness_status in ["stale", "unavailable"]:
    primary_state = STALE
else:
    primary_state = NORMAL
```

### 12.3 Policy Registry

图例与颜色语义应由以下 registry 驱动：

- `weather-comparison-engine/data/registries/ui_policy_registry/primary_state_policy.json`
- `weather-comparison-engine/data/registries/ui_policy_registry/ui_color_semantics_policy.json`
- `weather-comparison-engine/data/registries/ui_policy_registry/ui_legend_policy.json`
