# HMI Page Review Template

## Review header

```yaml
review_id:
review_date:
reviewer:
page_name:
version:
```

## Review context

```yaml
task_supported:
user_role:
operating_context:
critical_decisions: []
alarms_involved: []
automation_involved: []
failure_modes: []
degraded_modes: []
```

## HMI Review Gate

```yaml
G1_task_fit:
G2_situation_visibility:
G3_risk_visibility:
G4_action_clarity:
G5_action_gate:
G6_alarm_actionability:
G7_data_trust:
G8_automation_transparency:
G9_recovery:
G10_evidence:
final_disposition:
major_findings: []
minor_findings: []
blocking_issues: []
next_action:
```

## Evidence to retain

- page sketch or screenshot
- task model
- information architecture
- alarm and degraded mode notes
- automation or AI notes
- review gate result
- unresolved issues
