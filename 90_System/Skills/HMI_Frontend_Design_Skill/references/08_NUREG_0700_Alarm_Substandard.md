# 08 NUREG-0700 Alarm Substandard

Source: `/Users/maolei/Documents/数字化/Nureg 0700 Rev3.pdf`

## Alarm design rules to carry forward

- Select alarms for critical safety functions, personnel hazards, equipment protection, technical-spec compliance, procedure decision points, and all relevant operating modes.
- Set alarm thresholds so the crew has time to notice, understand, and act before a serious consequence.
- Avoid nuisance alarms by balancing early warning against false or trivial excursions.
- Keep only truly urgent, safety-significant messages in the active alarm state.
- Under heavy alarm load, preserve rapid detection of the alarms that require immediate action.
- Reduce flood conditions with validation, filtering, time delay, deadbanding, first-out processing, and suppression of logical consequence alarms.
- Keep status-only messages out of the alarm stream unless they are clearly distinguishable.
- Suppressed alarms should remain retrievable; filtered alarms should only be removed when they have no operational significance.
- Route alarms to the right audience, and expose maintenance alarms to operators when the condition affects operation.
- Show alarm priority, state, contents, and the difference between new, acknowledged, cleared, and first-out alarms.
- Make coding consistent across tiles, lists, and embedded displays.

## HMI implications

When a page includes alarms, the design should surface:

- severity and urgency
- object and trigger condition
- impact and operator action
- acknowledgement and closure state
- access to suppressed or detailed alarm information
- links to the detailed diagnostic or process view

