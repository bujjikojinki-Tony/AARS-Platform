# HMI Alarm Center Data Model Template

Use this template to define the TypeScript data model for a React alarm center.

## 1. Alarm record

```ts
export type AlarmSeverity = "critical" | "severe" | "warning" | "watch" | "info";
export type AlarmStatus = "new" | "acknowledged" | "cleared" | "suppressed" | "filtered" | "first_out";
export type AlarmLifecycle = "new" | "acknowledged" | "assigned" | "acted" | "verified" | "closed";

export interface AlarmEvidenceItem {
  id: string;
  label: string;
  value: string;
  source?: string;
  timestamp?: string;
  confidence?: number;
}

export interface AlarmRecord {
  id: string;
  title: string;
  severity: AlarmSeverity;
  status: AlarmStatus;
  lifecycle: AlarmLifecycle;
  object: string;
  source: string;
  triggerCondition: string;
  detectedAt: string;
  updatedAt: string;
  impactScope: string;
  recommendedAction: string;
  closureCondition: string;
  evidence: AlarmEvidenceItem[];
  isFirstOut: boolean;
  isSuppressed: boolean;
  isFiltered: boolean;
  isSharedAlarm: boolean;
  modeDependency?: string;
  blockedReason?: string;
  recoverySteps: string[];
}
```

## 2. Filter and sort model

```ts
export interface AlarmFilterState {
  severities: AlarmSeverity[];
  statuses: AlarmStatus[];
  sources: string[];
  modeDependencies: string[];
  showFirstOutOnly: boolean;
  showSuppressed: boolean;
  showFiltered: boolean;
  searchText: string;
}

export type AlarmSortKey = "severity" | "detectedAt" | "updatedAt" | "source" | "status";
export type AlarmSortDirection = "asc" | "desc";
```

## 3. Page state model

```ts
export interface AlarmCenterState {
  selectedAlarmId: string | null;
  filterState: AlarmFilterState;
  sortKey: AlarmSortKey;
  sortDirection: AlarmSortDirection;
  groupMode: "by_source" | "by_severity" | "by_mode" | "flat";
  drawerOpen: boolean;
  pageMode: "normal" | "degraded" | "maintenance" | "read_only";
  latestStableViewId?: string;
}
```

## 4. Summary model

```ts
export interface AlarmSummary {
  total: number;
  critical: number;
  severe: number;
  warning: number;
  watch: number;
  info: number;
  newCount: number;
  acknowledgedCount: number;
  suppressedCount: number;
  filteredCount: number;
  firstOutCount: number;
}
```

## 5. Recovery and degraded mode model

```ts
export interface RecoveryStep {
  id: string;
  label: string;
  description: string;
  required: boolean;
  blockedBy?: string[];
}

export interface DegradedModeState {
  type: "data_degraded" | "model_degraded" | "automation_degraded" | "communication_degraded" | "view_degraded";
  message: string;
  allowedActions: string[];
  blockedActions: string[];
  recoverySteps: RecoveryStep[];
  fallbackViewLabel: string;
}
```

## 6. Action model

```ts
export type AlarmActionType = "acknowledge" | "silence" | "reset" | "assign" | "open_detail" | "open_recovery";

export interface AlarmActionRequest {
  type: AlarmActionType;
  alarmId: string;
  reason?: string;
  confirmationToken?: string;
}
```

## 7. Data mapping notes

- keep actual values separate from demand or commanded values
- keep status labels separate from severity labels
- make first-out explicit rather than inferred
- keep suppressed and filtered alarms available as separate categories
- keep recovery steps distinct from alarm evidence
- support raw live data and Latest Stable View as separate records

## 8. Mock data starter

```ts
export const alarmSummary: AlarmSummary = {
  total: 12,
  critical: 1,
  severe: 2,
  warning: 4,
  watch: 3,
  info: 2,
  newCount: 5,
  acknowledgedCount: 4,
  suppressedCount: 1,
  filteredCount: 0,
  firstOutCount: 1,
};
```

## 9. Review checklist

- types are explicit and reusable
- status and severity are separate enums
- filters can represent suppressed, filtered, and first-out states
- action requests are explicit and auditable
- recovery and degraded mode have their own types
- the model can support both dense tables and card views
