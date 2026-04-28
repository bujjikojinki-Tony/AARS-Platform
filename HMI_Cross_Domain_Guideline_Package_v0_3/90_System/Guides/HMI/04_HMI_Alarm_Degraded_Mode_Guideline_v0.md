# 04 HMI Alarm and Degraded Mode Guideline v0

## 1. Alarm Lifecycle

每条告警必须经过生命周期管理：

```text
Triggered
→ Displayed
→ Acknowledged
→ Assigned
→ Acted
→ Verified
→ Closed
→ Reviewed
```

## 2. Alarm Object Schema

```yaml
alert_id:
alert_title:
severity:
object:
source:
trigger_condition:
detected_at:
current_status:
impact_scope:
recommended_action:
deadline:
evidence:
acknowledged_by:
disposition:
closure_condition:
review_note:
```

## 3. Severity Levels

| Level | Name | Meaning | UI Behavior |
|---|---|---|---|
| A0 | Info | 仅记录 | 低优先级日志 |
| A1 | Watch | 需要观察 | 观察队列 |
| A2 | Warning | 需要处理 | 告警中心提示 |
| A3 | Severe | 需要立即处置 | 置顶、高亮 |
| A4 | Critical | 阻断性风险 | 阻塞操作并启动恢复路径 |

## 4. Alarm Flooding Control

系统应支持：

- 重复告警折叠；
- 同源告警聚合；
- 父子告警关联；
- 低优先级告警抑制；
- 已确认告警降噪；
- 恢复告警自动归档。

## 5. Degraded Mode Types

| Type | Example | Required UI |
|---|---|---|
| Data Degraded | 延迟、缺失、不一致 | 数据可信度标签 |
| Model Degraded | 模型不可用、置信度低 | 模型状态条 |
| Automation Degraded | 自动扫描停止 | 自动化模式提示 |
| Communication Degraded | API 失败、断链 | 连接状态图标 |
| Operation Degraded | 权限不足、动作受限 | 操作门控提示 |
| View Degraded | 图表不可用、只读 | 页面顶部降级横幅 |

## 6. Recovery Path Schema

```yaml
recovery_id:
trigger:
current_degraded_state:
impact:
allowed_actions:
blocked_actions:
recovery_steps:
verification_condition:
fallback:
escalation_condition:
```

## 7. Recovery Page Must Answer

- 发生了什么？
- 影响什么？
- 还能做什么？
- 不能做什么？
- 如何恢复？
- 恢复后如何确认？
- 何时升级人工处理？

## 8. Review Rules

告警与降级模式设计进入实现前必须确认：

- 是否有明确触发条件；
- 是否有严重度分级；
- 是否有影响范围；
- 是否有推荐动作；
- 是否有证据；
- 是否有关闭条件；
- 是否有恢复路径；
- 是否避免告警洪泛。
