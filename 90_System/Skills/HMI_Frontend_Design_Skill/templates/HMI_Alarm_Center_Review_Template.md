# HMI Alarm Center Review Template

Use this template when reviewing a React alarm center or alarm management page in a safety-critical HMI.

## 1. Review header

```yaml
review_id:
review_date:
reviewer:
page_name:
version:
criticality:
```

## 2. Review context

```yaml
task_supported:
user_role:
operating_context:
alarm_sources: []
automation_involved: []
failure_modes: []
degraded_modes: []
```

## 3. Alarm-center specific questions

```yaml
highest_priority_visible:
status_only_messages_separated:
new_acknowledged_cleared_visible:
first_out_visible:
suppressed_alarms_retrievable:
filtered_alarms_justified:
alarm_priority_reasonable:
alarm_flood_controls_present:
maintenance_alarm_operational_significance_visible:
acknowledge_silence_reset_gated:
closure_condition_visible:
```

## 4. HMI Review Gate

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

## 5. Review findings format

```text
# Findings
1. [P1] ...
2. [P2] ...
3. [P3] ...

## Summary
...
```

## 6. Evidence to retain

- page sketch or screenshot
- task model
- alarm hierarchy and severity mapping
- suppressed and filtered alarm strategy
- first-out and root-cause handling
- acknowledge, silence, and reset behavior
- degraded mode and recovery path
- audit trail or action log

## 7. Suggested disposition logic

- `Accept` if the highest-priority alarm is visible, actionable, and the recovery path is clear
- `Accept with Minor Issues` if only minor wording, spacing, or grouping issues remain
- `Defer` if the review lacks enough evidence to judge alarm behavior
- `Block` if hidden alarms, unexplained blocking, or unsafe alarm handling remain
- `Rework` if the page must be redesigned around the alarm model

## 8. Review checklist

- highest-risk alarms are visible in the main view
- alarm status and severity are distinct
- first-out and initiating-event clues are available where relevant
- suppressed alarms are accessible
- filtered alarms are justified by operational insignificance
- maintenance alarms show their operational impact
- acknowledge, silence, and reset are safe and explicit
- alarm flood controls do not hide important alarms
- closure conditions are visible
- latest stable view and degraded mode handling are present
