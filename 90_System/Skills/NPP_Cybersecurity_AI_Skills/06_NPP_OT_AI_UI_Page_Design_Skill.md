# Skill: NPP OT AI UI Page Design

## Skill Purpose

Use this skill to design front-end pages for a nuclear OT AI anomaly detection and explainability platform.

The skill produces:

- page specifications
- object-to-page mappings
- field lists
- button rules
- navigation logic
- state transition models
- role-based views
- UI acceptance checklist

## When to Use

Use this skill when the user asks to:

- 设计核电 OT AI 异常检测系统界面
- 画 Alert Board
- 设计告警详情页
- 设计可解释性页面
- 设计模型治理页面
- 设计 V&V 页面
- 设计审计报告页面
- 将异常检测规范转为前端设计

## Required Inputs

```text
1. Target page or workflow
2. User roles
3. Data objects
4. Alert lifecycle states
5. Model governance requirements
6. Whether visual mockup or page specification is needed
```

If the page is not specified, start with Alert Board.

## Standard Page Set

Use this page set:

1. Alert Board
2. Alert Detail
3. Explanation View
4. Evidence Timeline
5. Human Review Workspace
6. Model Governance Dashboard
7. Drift Review Workspace
8. V&V Checklist Workspace
9. Rule and Matrix Management
10. Audit Report View

## Output Structure

```markdown
# NPP OT AI UI Page Specification
## 1. Page Purpose
## 2. User Roles
## 3. Page Layout
## 4. Data Objects Used
## 5. Core Fields
## 6. Filters and Controls
## 7. Buttons and Actions
## 8. State Transitions
## 9. Role-Based Views
## 10. Prohibited Buttons
## 11. Validation Rules
## 12. Acceptance Checklist
```

## UI Design Rules

1. Show risk and asset impact before model score.
2. Show CDA status prominently.
3. Show human review requirement for medium and above alerts.
4. Show evidence completeness.
5. Show explanation readiness.
6. Show model version and rule version.
7. Do not provide high-impact auto-action buttons by default.
8. Role views must distinguish cybersecurity, I&C, operations, management, and audit.
9. Every state change must require reason and be auditable.
10. Every alert must link to explanation and evidence.

## Standard Components

- SeverityBadge
- StatusBadge
- CDAFlag
- ZoneTag
- ConfidenceBar
- AnomalyScoreCard
- ExplanationStack
- EvidenceTimeline
- FeatureContributionTable
- RoleViewSwitcher
- HumanReviewChecklist
- DispositionSelector
- ModelStatusBadge
- DriftIndicator
- VVGateProgress
- AuditExportPanel

## Button Rules

Allowed:

- Open
- Review
- Assign Reviewer
- Request I&C Review
- Request Operations Review
- Open Evidence
- Open Explanation
- Link Work Order
- Mark False Positive
- Mark Known Activity
- Escalate
- Close with Reason
- Feedback to Model
- Start Drift Review
- Open V&V Checklist
- Export Report

Controlled:

- Suspend Model
- Rollback Model
- Approve Release
- Retire Rule
- Approve Matrix Change
- Export Evidence Package

Prohibited by default:

- Auto Isolate
- Auto Block
- Auto Shutdown
- Auto Disable Account
- Auto Modify Rule
- Auto Modify Controller
- Auto Push Config
- Bypass Approval

## Alert Board Required Fields

- alertId
- detectedAt
- severity
- status
- assetName
- zone
- cdaStatus
- anomalyCategory
- detectionEngine
- confidenceScore
- humanReviewRequired
- explanationReady
- evidenceCompleteness
- disposition

## Completion Criteria

The UI spec is complete when it defines:

1. Page purpose
2. Layout
3. Data fields
4. Filters
5. Buttons
6. State flow
7. Role views
8. Prohibited actions
9. Acceptance checklist

