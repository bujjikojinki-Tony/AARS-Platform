# 04 HMI Alarm Degraded Mode Guideline v0

Source: `90_System/Guides/HMI/04_HMI_Alarm_Degraded_Mode_Guideline_v0.md`

## Stable rules

- alarms should follow a lifecycle from triggered to reviewed
- every alarm should carry object, trigger condition, impact, evidence, recommended action, status, and closure condition
- severity should drive UI behavior
- flooding should be controlled by aggregation and suppression
- degraded modes should be explicit and categorized
- recovery paths should show allowed actions, blocked actions, steps, and escalation conditions

## How this file is used

Read this reference when designing alert queues, degraded-mode banners, recovery flows, or operator triage screens.
