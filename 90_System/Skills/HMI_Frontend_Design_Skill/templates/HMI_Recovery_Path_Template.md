# HMI Recovery Path Template

```yaml
recovery_id:
trigger:
current_degraded_state:
impact:
allowed_actions: []
blocked_actions: []
recovery_steps: []
verification_condition:
fallback:
escalation_condition:
```

## Recovery questions

- What failed or degraded?
- What still works?
- What must stop?
- What is the safest fallback?
- How does the operator verify recovery?
