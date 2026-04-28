# HMI Alarm Center Component Split Template

Use this template to break a React alarm center into concrete components before implementation.

## 1. Component tree

```text
AlarmCenterPage
├── AlarmSummaryBar
├── AlarmFilterPanel
├── AlarmQueuePanel
│   ├── AlarmQueueTable
│   ├── AlarmQueueCard
│   └── AlarmStatusBadge
├── AlarmDetailDrawer
│   ├── AlarmEvidencePanel
│   ├── AlarmActionPanel
│   └── ClosureConditionPanel
├── SuppressedAlarmPanel
├── RecoveryPathPanel
└── DegradedModeBanner
```

## 2. Component responsibilities

```yaml
AlarmCenterPage: owns layout, global state, and page mode
AlarmSummaryBar: shows system status, data freshness, active mode, and highest severity
AlarmFilterPanel: controls severity, source, mode, status, and first-out filters
AlarmQueuePanel: renders the prioritized alarm list and grouping behavior
AlarmQueueTable: supports dense list scanning and sorting
AlarmQueueCard: supports card view for narrow screens or summary previews
AlarmStatusBadge: shows new, acknowledged, cleared, suppressed, filtered, or first-out state
AlarmDetailDrawer: shows selected alarm evidence, impact, recommendation, and closure condition
AlarmEvidencePanel: surfaces the data used to justify the alarm
AlarmActionPanel: hosts acknowledge, silence, reset, and assignment actions
SuppressedAlarmPanel: provides access to suppressed alarms on demand
RecoveryPathPanel: shows what to do next and how to recover safely
DegradedModeBanner: makes degraded data, model, automation, or view states explicit
```

## 3. State ownership

```yaml
global_state_owner: AlarmCenterPage
list_state_owner: AlarmQueuePanel
drawer_state_owner: AlarmDetailDrawer
filter_state_owner: AlarmFilterPanel
recovery_state_owner: RecoveryPathPanel
degraded_state_owner: DegradedModeBanner
```

## 4. Props contract outline

```yaml
AlarmSummaryBar:
  severity_counts: {}
  highest_alarm:
  data_freshness:
  active_mode:

AlarmFilterPanel:
  filters:
  onFilterChange:
  onResetFilters:

AlarmQueuePanel:
  alarms: []
  selectedAlarmId:
  sortKey:
  sortDirection:
  groupMode:
  onSelectAlarm:

AlarmDetailDrawer:
  alarm:
  open:
  onClose:
  onAcknowledge:
  onSilence:
  onReset:

RecoveryPathPanel:
  recoverySteps: []
  blockedActions: []
  allowedActions: []
```

## 5. Layout notes

- keep filters and queue visible at the same time
- keep the selected alarm's detail one click away
- keep recovery and suppressed alarms reachable without hiding them behind deep navigation
- do not split critical actions across unrelated menus

## 6. Responsive strategy

```yaml
desktop:
  left: filters
  center: queue
  right: drawer or detail panel

tablet:
  filters: collapsible
  queue: primary
  drawer: overlay

mobile:
  summary: sticky
  queue: stacked
  drawer: full-screen
```

## 7. Implementation prompt starter

```text
Break the alarm center into the components listed above.

For each component:
- define responsibility
- define props
- define state ownership
- define events emitted
- define empty, loading, degraded, and error states
- define how the component supports alarm priority, first-out, suppressed alarms, and recovery

Then provide a React file map and a minimal TypeScript interface for each component.
```

## 8. Review checklist

- each component has a single primary responsibility
- page state ownership is unambiguous
- detail drawer is separate from queue rendering
- suppressed alarms are isolated but retrievable
- degraded mode and recovery have dedicated ownership
- mobile and desktop behaviors are both addressed
