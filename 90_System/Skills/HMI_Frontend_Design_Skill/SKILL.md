---
name: safety-critical-hmi-frontend-design
description: Design, review, or refactor safety-critical or mission-critical frontend UIs. Use this skill whenever the user asks for a dashboard, console, alert center, control room page, current-step screen, page review, component spec, or React implementation prompt where state, risk, gated actions, alarm actionability, latest stable view, degraded mode, AI evidence, and review gates must be visible. Also use it for hidden alerts, unexplained disabled buttons, or any UI that should be treated as a task-centered control surface rather than a charts-only dashboard.
---

# Safety-Critical HMI Frontend Design Skill

## 1. Skill purpose

Use this skill to turn high-reliability HMI guidance into frontend design decisions that are practical for implementation and review.

It is for interfaces that must support:

- operational monitoring
- alarm and risk handling
- automation or AI recommendations
- procedural or step-based workflows
- degraded mode and recovery
- reviewable design evidence

It is not a generic visual-design skill. Optimize for task execution, risk visibility, controlled action, and human oversight.

When the request is ambiguous, infer the intent in this order:

1. page or screen design
2. UI review or HMI gate review
3. component specification
4. implementation guidance for frontend code

If the user asks for a dashboard, do not default to charts-first layouts. Reframe it as a task-centered control surface unless the user explicitly wants a reporting-only view.

## 2. Design thesis

A safety-critical HMI is a task-centered control surface, not a dashboard.

The user should be able to answer, quickly and in one place:

1. What is happening now?
2. Why does it matter?
3. What is the current risk?
4. What can I do now?
5. What is blocked and why?
6. What does automation or AI recommend?
7. What evidence supports that recommendation?
8. What is degraded?
9. How do I recover?
10. How will this design be reviewed?

## 3. When to use this skill

Use this skill when the user asks to:

- design a frontend page, console, or dashboard
- redesign an operational or monitoring UI
- create an alert or risk center
- design an AI recommendation surface
- design a workflow or control page
- review a screenshot, wireframe, or component layout
- generate implementation constraints for React, Vue, or similar frontend code
- create page-level HMI design documentation

## 4. Core rules

### P1. Task first

Start from the user task, not from backend modules or database tables.

Every page should define:

- supported task
- user role
- operating context
- current state
- available actions
- blocked actions
- verification criteria

### P2. Situation awareness

Support three layers of understanding:

- perception: what is happening
- comprehension: why it matters
- projection: what may happen next

### P3. Risk visibility

Keep the highest risk in the main view.

Do not bury critical risks in tabs, drawers, logs, or secondary panels.

### P4. Action gating

Critical actions should show:

- preconditions
- permission checks
- risk checks
- confirmation
- execution feedback
- audit record
- verification condition

Disabled actions must explain why they are disabled.

### P5. Alarm as action object

Treat alarms as objects that can be acted on, not as passive messages.

Each alarm should expose:

- severity
- object
- trigger condition
- impact
- evidence
- recommended action
- owner or status
- closure condition

### P6. Automation transparency

If automation or AI is present, show:

- mode
- input data
- evidence or reasoning
- confidence
- limitations or boundaries
- human override path
- audit trail

### P7. Degraded mode visibility

If data, model, communication, automation, operation, or view is degraded, make that explicit.

State:

- what is degraded
- what is still allowed
- what is blocked
- how to recover
- when to escalate

### P8. Latest stable view

For fast-changing or uncertain systems, provide a Latest Stable View as a trusted baseline.

Do not confuse the latest raw data with the latest stable view.

### P9. Consistency before novelty

Reuse the same meanings for terms, colors, icons, severity labels, and action placement.

Prefer consistency over local cleverness.

### P10. Reviewable by design

Every page should produce review evidence:

- task model
- information architecture
- alarm and risk handling
- automation handling
- degraded mode handling
- HMI review gate result

### P11. Nuclear-grade additions from NUREG-0700 Rev.3

If the page is used for nuclear, control-room, safety-critical, or similarly governed operations, add these checks:

- distinguish actual state from commanded or demand state
- annotate fast-changing values with time and provide an obvious freeze state
- keep high-priority alarms continuously visible and distinguish them from status-only messages
- reduce alarm floods with processing, but keep suppressed alarms retrievable
- surface first-out or initiating-event clues when diagnosis depends on root cause
- make mode-dependent alarms and lockouts explain why they are active
- let users see which condition caused a control block and what must happen to release it
- require deliberate actions, confirmation, and cancel or undo paths for safety-significant controls
- show procedure identification, step status, warnings, cautions, notes, and recovery or backup procedures
- show automation purpose, mode, current authority, limits, and fallback path
- make degraded display or I&C conditions explicit, including source validity and backup to paper or alternate procedures

When the page specifically involves alarms, soft controls, or procedures, consult the matching reference first:

- `references/08_NUREG_0700_Alarm_Substandard.md`
- `references/09_NUREG_0700_Soft_Control_Substandard.md`
- `references/10_NUREG_0700_CBP_Substandard.md`

## 5. Required output structure

When asked to design a page, respond in this structure:

# <Page Name> HMI Design v0
## 1. Page Purpose
## 2. User Role and Scenario
## 3. Task Model
## 4. Information Architecture
## 5. Layout Design
## 6. Component List
## 7. Data Model
## 8. Alarm and Risk Design
## 9. Automation / AI Design
## 10. Degraded Mode and Recovery
## 11. User Actions and Gates
## 12. HMI Review Gate
## 13. Codex Implementation Prompt

If the user asks for a shorter answer, keep the same order and compress the sections rather than changing the structure.

## 6. Default page pattern

Prefer this layout for operational surfaces:

```text
Top Bar:
  system status / data freshness / automation mode / highest alert

Left Panel:
  object list / task list / market list / system list

Center Panel:
  selected object or current task situation view

Right Panel:
  alarm queue / risk queue / recommendation queue

Bottom Bar:
  latest stable view / current step / recovery path / quick actions
```

Use this pattern as a starting point, then adapt it to the task.

## 7. Component guidance

Favor component names that make the HMI intent obvious:

- `SystemStatusBar`
- `DataFreshnessBadge`
- `LatestStableViewCard`
- `CurrentTaskCard`
- `SituationSummaryPanel`
- `AlertQueuePanel`
- `RiskSeverityBadge`
- `AlarmDetailDrawer`
- `AlertActionCard`
- `RiskImpactPanel`
- `ActionCommandBar`
- `GatedActionButton`
- `DisabledActionReasonTooltip`
- `ConfirmationDialog`
- `ExecutionFeedbackPanel`
- `AutomationModeIndicator`
- `AIRecommendationCard`
- `ConfidenceBadge`
- `EvidenceTracePanel`
- `HumanOverridePanel`
- `DegradedModeBanner`
- `RecoveryPathPanel`
- `FallbackActionCard`
- `EscalationNotice`
- `ReviewGateChecklist`
- `AuditTrailPanel`
- `EvidenceDrilldownPanel`
- `RawDataDrawer`

Avoid vague component names that hide intent.

## 8. Frontend implementation rules

When generating frontend code or implementation constraints:

- do not hide critical alerts in tabs
- do not put raw JSON on the main overview page
- do not use color as the only status encoding
- do not create disabled buttons without explaining why
- do not create AI recommendations without evidence and confidence
- do not create critical actions without confirmation and feedback
- do not mix latest raw data with Latest Stable View
- do not create deep navigation for urgent actions
- do not use vague labels such as "smart optimize" or "auto action" without boundaries
- do not make the page visually dense without task hierarchy

## 9. HMI review gate

Before implementation, check the page against these gates:

- G1 Task Fit: does the page clearly support a specific task?
- G2 Situation Visibility: can the user understand current state within 5 seconds?
- G3 Risk Visibility: is the highest risk visible in the main view?
- G4 Action Clarity: does the user know what can be done next?
- G5 Action Gate: are critical actions gated by conditions, risk, and permission?
- G6 Alarm Actionability: are alarms actionable with cause, impact, and recommended response?
- G7 Data Trust: are data source, freshness, and confidence visible?
- G8 Automation Transparency: are automation mode, evidence, limits, and override visible?
- G9 Recovery: is there a clear degraded-mode and recovery path?
- G10 Evidence: is the design reviewable and traceable?

Allowed dispositions:

- Accept
- Accept with Minor Issues
- Defer
- Block
- Rework

## 10. How to answer different request types

- If the user wants a page design, produce the full page spec and end with a direct implementation prompt if helpful.
- If the user wants a UI review, lead with findings against the HMI review gate, ordered by severity, then give a short summary.
- If the user wants component design, define purpose, data, states, interactions, disabled behavior, and gate behavior.
- If the user wants implementation help, translate the HMI constraints into concrete frontend guidance and call out the minimum safe component set.
- For alarm-center implementation requests, prefer `templates/HMI_Alarm_Center_React_Implementation_Template.md` as the starting structure.
- For alarm-center reviews, prefer `templates/HMI_Alarm_Center_Review_Template.md` as the starting structure.
- For alarm-center component decomposition, prefer `templates/HMI_Alarm_Center_Component_Split_Template.md`.
- For alarm-center data typing, prefer `templates/HMI_Alarm_Center_Data_Model_Template.md`.

## 11. Response priorities

When generating a design, prioritize in this order:

1. task clarity
2. risk visibility
3. action gating
4. data trust
5. automation transparency
6. degraded mode and recovery
7. review evidence
8. visual polish

Visual polish matters, but only after the control surface is safe and legible.

## 12. Reference files

Read the relevant reference file when you need to justify the design or recover a rule:

- `references/01_HMI_Cross_Domain_Standards_Study_v0.md`
- `references/02_HMI_Design_Principles_v0.md`
- `references/03_HMI_Information_Architecture_Guideline_v0.md`
- `references/04_HMI_Alarm_Degraded_Mode_Guideline_v0.md`
- `references/05_HMI_Automation_AI_Interface_Guideline_v0.md`
- `references/06_HMI_Design_Review_Checklist_v0.md`
- `references/07_NUREG_0700_Rev3_Extracted_Rules.md`
- `references/08_NUREG_0700_Alarm_Substandard.md`
- `references/09_NUREG_0700_Soft_Control_Substandard.md`
- `references/10_NUREG_0700_CBP_Substandard.md`

## 13. Skill boundaries

This skill gives frontend design and review guidance. It does not replace:

- domain safety analysis
- regulatory review
- formal human factors engineering validation
- verification and validation

For production safety-critical systems, formal review is still required.
