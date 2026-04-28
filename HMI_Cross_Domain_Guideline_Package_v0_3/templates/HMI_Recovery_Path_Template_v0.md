# HMI Recovery Path Template v0

```yaml
recovery_id:
trigger:
current_degraded_state:
impact:
allowed_actions:
blocked_actions:
recovery_steps:
  - step_id:
    action:
    expected_result:
    verification_condition:
fallback:
escalation_condition:
owner:
status:
```

## Recovery Page Must Answer

1. 发生了什么？
2. 影响什么？
3. 还能做什么？
4. 不能做什么？
5. 如何恢复？
6. 恢复后如何确认？
7. 何时升级人工处理？
