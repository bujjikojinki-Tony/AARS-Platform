# HMI Alarm Object Template v0

```yaml
alert_id:
alert_title:
severity: A0 | A1 | A2 | A3 | A4
object:
source:
trigger_condition:
detected_at:
current_status: new | acknowledged | assigned | in_progress | verified | closed
impact_scope:
recommended_action:
deadline:
evidence:
acknowledged_by:
disposition: accept | monitor | defer | escalate | close
closure_condition:
review_note:
```

## Review Questions

- 告警是否有明确触发条件？
- 告警是否有影响范围？
- 告警是否可处置？
- 告警是否有关闭条件？
- 告警是否需要进入恢复路径？
