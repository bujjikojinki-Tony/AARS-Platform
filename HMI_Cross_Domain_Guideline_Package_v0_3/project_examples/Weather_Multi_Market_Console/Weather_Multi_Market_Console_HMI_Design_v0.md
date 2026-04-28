# Weather Multi-Market Console HMI Design v0

## 1. Design Goal

建立一个多市场运行监控台，将天气市场的状态、异常、机会、风险、告警、模型判断和人工处置动作集中呈现，避免关键信息藏在 Tab 中。

## 2. Main Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ System Status | Data Freshness | Scanner Mode | Alert Count   │
├───────────────┬──────────────────────────────┬───────────────┤
│ Market List   │ Selected Market Situation    │ Alert/Risk    │
│ - sorted by   │                              │ Queue         │
│   anomaly     │  Market Probability          │               │
│ - watchlist   │  Model Probability           │  A3 Alerts    │
│ - region      │  Weather Forecast            │  A2 Warnings  │
│ - event type  │  Divergence                  │  Opportunities│
│               │  Threshold Distance          │               │
├───────────────┴──────────────────────────────┴───────────────┤
│ Latest Stable View | Current Recommended Action | Recovery     │
└──────────────────────────────────────────────────────────────┘
```

## 3. Required Fields

```yaml
system_status:
data_freshness:
scanner_status:
highest_alert:
market_count:
watchlist_count:
selected_market:
market_probability:
model_probability:
divergence:
forecast_value:
threshold_distance:
liquidity:
risk_level:
recommended_action:
confidence:
latest_stable_view:
```

## 4. Single Market Situation Card

```yaml
market_id:
market_name:
event_condition:
event_deadline:
region:
weather_source:
forecast_value:
forecast_range:
threshold:
threshold_distance:
market_price:
market_probability:
model_probability:
divergence:
liquidity:
volume:
data_freshness:
confidence:
risk_level:
opportunity_level:
recommended_action:
evidence:
```

## 5. Alert / Opportunity Card

```yaml
card_type: alert | opportunity | data_quality | model_risk
severity:
object:
trigger:
why_it_matters:
evidence:
recommended_action:
human_confirmation_required:
closure_condition:
```

## 6. Design Rule

多市场监控台首页必须让用户在 5 秒内回答：

1. 当前系统是否正常？
2. 哪些市场最值得关注？
3. 最高风险或最大机会是什么？
4. 模型与市场偏差在哪里？
5. 是否存在数据或自动化降级？
6. 下一步应该执行什么动作？
