# IEC 61508 Logic Summary

## Purpose

Use this reference when the task is about generic functional safety lifecycle reasoning for E/E/PE safety-related systems.

IEC 61508 is most useful when the user needs to reason about:

- safety functions
- hazard and risk basis
- SIL logic
- lifecycle expectations
- systematic capability
- validation and modification logic

## Core idea

IEC 61508 is about the lifecycle integrity of safety functions, not just product selection.

The most important guardrail:

SIL applies to a safety function, not simply to a single device.

## When to use it as the primary logic

Use IEC 61508 as primary when the request is about:

- generic functional safety analysis
- safety-function definition
- SIL reasoning
- lifecycle integrity expectations
- systematic capability
- validation of safety-related systems
- modification impact on functional safety claims

If the task is process-industry SIS/SIF specific, IEC 61511 is usually the more operational reference while IEC 61508 remains the generic foundation.

## What to look for

### Hazard and risk basis

- hazards identified
- risk scenarios identified
- risk reduction need stated

### Safety function logic

- safety function defined
- safe state defined
- response requirement defined
- assumptions stated

### SIL logic

- target SIL basis
- architecture logic
- subsystem contribution
- diagnostics and assumptions
- proof test assumptions where relevant

### Lifecycle evidence

- requirements
- design
- implementation
- verification
- validation
- operation and maintenance constraints
- modification control

## Common mistakes

### Mistake 1: device-only SIL claims

Do not accept a SIL claim based only on:

- a sensor certificate
- a logic solver certificate
- a final element certificate

A credible claim usually needs evidence across the function boundary.

### Mistake 2: ignoring systematic capability

Strong hardware data does not close software or lifecycle discipline issues.

### Mistake 3: skipping lifecycle closure

If the user jumps from design or hardware selection directly to compliance language, slow down and ask what evidence exists for validation, operation, maintenance, and modification.

### Mistake 4: vague safe-state reasoning

If the safe state is undefined or the response time basis is unclear, the safety-function reasoning is not mature.

## Preferred output cues

For IEC 61508-centered outputs, prefer:

- safety-function-centered language
- lifecycle logic from hazard to validation
- explicit assumptions
- caution around SIL claims

## Minimal checklist

- [ ] hazards and risk basis are identified
- [ ] safety function is defined
- [ ] safe state is defined
- [ ] SIL logic is stated at function level
- [ ] systematic capability is addressed
- [ ] validation is addressed
- [ ] operation and maintenance constraints are addressed
- [ ] modification impact is addressed
