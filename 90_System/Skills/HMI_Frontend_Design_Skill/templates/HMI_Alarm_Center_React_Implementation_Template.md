# HMI Alarm Center React Implementation Template

Use this template when you want Codex to implement a React alarm center for a safety-critical or mission-critical HMI.

## 1. Page intent

```yaml
page_name:
page_goal:
primary_user:
operating_context:
criticality:
```

## 2. Alarm model

```yaml
alarm_sources: []
alarm_severity_scale: []
alarm_lifecycle: [new, acknowledged, assigned, acted, verified, closed]
alarm_status_labels: [new, acknowledged, cleared, suppressed, filtered, first_out]
```

## 3. Page layout

```text
Top Bar:
  system status / data freshness / active mode / highest severity alarm

Left Panel:
  filters / source groups / mode groups / severity groups

Center Panel:
  alarm queue with sorting, grouping, and status badges

Right Panel:
  alarm detail drawer / recommended action / evidence / closure condition

Bottom Bar:
  latest stable view / recovery path / acknowledgement log / quick actions
```

## 4. Required React components

```yaml
components:
  - AlarmCenterPage
  - AlarmSummaryBar
  - AlarmFilterPanel
  - AlarmQueueTable
  - AlarmQueueCard
  - AlarmStatusBadge
  - SeverityBadge
  - FirstOutBadge
  - AlarmDetailDrawer
  - AlarmEvidencePanel
  - AlarmActionPanel
  - AcknowledgeButton
  - SilenceButton
  - ResetButton
  - SuppressedAlarmPanel
  - RecoveryPathPanel
  - DegradedModeBanner
  - DataFreshnessBadge
```

## 5. State model

```yaml
state:
  selected_alarm_id:
  selected_filters: []
  sort_key: severity
  sort_direction: desc
  group_mode: by_source
  show_suppressed: false
  show_filtered: false
  show_first_out: true
  drawer_open: false
  page_mode: normal
```

## 6. Data contract

```yaml
alarm_record:
  id:
  title:
  severity:
  object:
  source:
  trigger_condition:
  detected_at:
  updated_at:
  status:
  impact_scope:
  recommended_action:
  closure_condition:
  evidence: []
  is_first_out:
  is_suppressed:
  is_filtered:
  is_shared_alarm:
  mode_dependency:
  blocked_reason:
  recovery_steps: []
```

## 7. Interaction rules

```yaml
row_click: open detail drawer
acknowledge_action: requires confirmation for critical alarms
silence_action: explain why it is safe or allowed
reset_action: only after closure condition is met
suppressed_alarm_access: available on request
blocked_action_feedback: always visible
audit_log: required for all operator actions
```

## 8. Display rules

```yaml
priority_order:
  - critical
  - severe
  - warning
  - watch
  - info

default_sort: severity_then_recency
show_actual_state: true
show_new_acknowledged_cleared: true
show_trigger_time: true
show_freshness: true
show_data_source: true
show_confidence_or_validity: true
```

## 9. Accessibility and human factors

```yaml
color_only_encoding_allowed: false
text_labels_required: true
keyboard_navigation_required: true
focus_management_required: true
high_contrast_required: true
screen_reader_labels_required: true
```

## 10. Error and degraded mode handling

```yaml
degraded_states:
  - data_degraded
  - model_degraded
  - automation_degraded
  - communication_degraded
  - view_degraded

fallbacks:
  - latest_stable_view
  - suppressed_alarm_access
  - backup_procedure_link
  - recovery_path_panel
```

## 11. Implementation prompt skeleton

```text
Build a React alarm center page for a safety-critical HMI.

Requirements:
- show a summary bar with system status, data freshness, active mode, and highest severity alarm
- show a filterable, sortable alarm queue in the center panel
- keep high-priority alarms visible by default
- distinguish new, acknowledged, cleared, suppressed, filtered, and first-out alarms
- expose alarm details in a drawer with trigger condition, impact, evidence, recommended action, and closure condition
- support acknowledge, silence, and reset actions with confirmation and audit logging
- allow access to suppressed alarms without hiding them permanently
- show degraded mode states and a recovery path when data or automation is unavailable
- keep the latest stable view visible and separate from raw live updates
- make all disabled actions explain why they are blocked

Deliver:
1. React component tree
2. TypeScript props and data types
3. state management strategy
4. rendering logic for severity/status/filtering
5. accessibility notes
6. sample mock data
```

## 12. Suggested file split

```text
AlarmCenterPage.tsx
AlarmSummaryBar.tsx
AlarmFilterPanel.tsx
AlarmQueueTable.tsx
AlarmDetailDrawer.tsx
AlarmActionPanel.tsx
RecoveryPathPanel.tsx
degradedMode.ts
alarmTypes.ts
mockAlarms.ts
```

## 13. Review checklist

- highest severity is visible without opening tabs
- suppressed alarms are retrievable
- first-out clues are visible when relevant
- acknowledge, silence, and reset are gated appropriately
- details include evidence and closure condition
- degraded state and recovery are explicit
- latest stable view is separated from live raw data
