# HMI Alarm Center React Example

## Scenario

Design a React alarm center for a mission-critical operations console. The current system has too many alarms, hides important alarms behind tabs, and does not explain why some actions are blocked.

## Page intent

```yaml
page_name: Operations Alarm Center
page_goal: Help operators identify the highest-priority alarms, understand why they matter, and take controlled actions with clear recovery paths.
primary_user: Control room operator
operating_context: Safety-critical monitoring and response
criticality: high
```

## Alarm model

```yaml
alarm_sources:
  - reactor_protection
  - process_monitoring
  - maintenance_diagnostics
  - automation_health

alarm_severity_scale:
  - critical
  - severe
  - warning
  - watch
  - info

alarm_lifecycle: [new, acknowledged, assigned, acted, verified, closed]
alarm_status_labels: [new, acknowledged, cleared, suppressed, filtered, first_out]
```

## Suggested page layout

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

## Required React components

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
  - LatestStableViewCard
```

## Data contract example

```yaml
alarm_record:
  id: ALM-1042
  title: Reactor coolant pressure trend approaching limit
  severity: critical
  object: RCS pressure
  source: process_monitoring
  trigger_condition: pressure trend exceeded pre-alarm threshold for 90 seconds
  detected_at: 2026-04-26T09:15:00+08:00
  updated_at: 2026-04-26T09:15:12+08:00
  status: new
  impact_scope: potential trip risk and procedure escalation
  recommended_action: open recovery path, verify sensor validity, prepare controlled response
  closure_condition: pressure trend stabilizes below threshold and operator verifies recovery
  evidence:
    - sensor feed valid
    - trend graph over 15 minutes
    - first-out correlation unavailable
  is_first_out: false
  is_suppressed: false
  is_filtered: false
  is_shared_alarm: false
  mode_dependency: full_power
  blocked_reason: acknowledge requires secondary confirmation for critical alarms
  recovery_steps:
    - verify latest stable view
    - open detail drawer
    - review evidence
    - acknowledge and assign
    - execute recovery path
```

## State model

```yaml
state:
  selected_alarm_id: ALM-1042
  selected_filters:
    - critical
    - new
  sort_key: severity
  sort_direction: desc
  group_mode: by_source
  show_suppressed: false
  show_filtered: false
  show_first_out: true
  drawer_open: true
  page_mode: degraded
```

## Example implementation prompt for Codex

```text
Use the Safety-Critical HMI Frontend Design Skill.

Task:
Build a React alarm center page for a mission-critical operations console.

Context:
- Operators need to see the highest-priority alarms first.
- Status-only messages must not be mixed into the active alarm queue.
- Suppressed alarms should still be retrievable.
- Acknowledge, silence, and reset actions need gating, confirmation, and audit logging.
- The page must show a latest stable view, a recovery path, and degraded mode status.

Requirements:
1. Create a React component tree with a summary bar, filter panel, alarm queue, detail drawer, and recovery path panel.
2. Model alarm records with severity, source, trigger condition, detected time, status, evidence, recommended action, and closure condition.
3. Sort by severity first and recency second.
4. Keep the highest-priority alarm visible without opening tabs.
5. Make the detail drawer show evidence, closure condition, and blocked reasons.
6. Add keyboard navigation and accessible labels.
7. Include sample mock data for critical, severe, warning, watch, and info alarms.
8. Add a degraded-mode banner and a latest stable view card.

Deliver:
- component tree
- TypeScript types
- state model
- rendering logic
- sample data
- accessibility notes
```

## Review checklist

- highest-priority alarm is visible immediately
- alarm status and priority are clearly separated
- suppressed alarms are accessible
- action buttons are gated and explain why
- evidence and closure conditions are visible
- latest stable view is separate from live data
- degraded mode and recovery are explicit
