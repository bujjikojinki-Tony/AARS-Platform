# 09 NUREG-0700 Soft Control Substandard

Source: `/Users/maolei/Documents/数字化/Nureg 0700 Rev3.pdf`

## Soft control rules to carry forward

- Support recognition-based selection of plant parameters and components.
- Use simple input actions for selection whenever possible.
- Distinguish interface-management actions from process-control actions.
- Require deliberate action for significant consequences.
- Provide feedback for selected actions before execution, with cancel or modify paths.
- Use interlocks, lockouts, and lockins to restrict unsafe actions, but make the blocking reason visible.
- Do not automatically start a blocked action just because the blocking condition clears.
- Ensure soft controls are not active when the associated display is inoperable.
- Avoid excessive mode complexity; if modes are necessary, make the active mode obvious at a glance.
- Keep destructive or safety-significant commands unique and hard to confuse with benign commands.
- Support sequential actions with clear ordering, status, and recovery from interruption.
- Show reference values and current values for numeric inputs.

## HMI implications

When a page contains soft controls or digital actuation:

- show what is selected
- show what mode is active
- show what is blocked and why
- show the value that will be acted on
- allow review before commit
- expose undo, cancel, or revert behavior

