# 07 NUREG-0700 Rev.3 Extracted Rules

Source: `/Users/maolei/Documents/数字化/Nureg 0700 Rev3.pdf`

## What this reference adds

This file captures the most transferable rules from NUREG-0700 Rev.3 for high-reliability frontend design:

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

## Design implications

If a page contains alarms, soft controls, procedures, or automation, the design should explicitly show:

- what is happening now
- whether the view reflects actual state or commanded state
- what is safe to do now
- what is blocked and why
- what the next step is
- how to verify execution
- how to recover if the display or control path degrades
