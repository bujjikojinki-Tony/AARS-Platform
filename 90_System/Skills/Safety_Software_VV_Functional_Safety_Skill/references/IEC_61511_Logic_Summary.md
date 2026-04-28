# IEC 61511 Logic Summary

## Purpose

Use this reference when the task is about process-industry SIS / SIF lifecycle work.

IEC 61511 is most useful when the user needs:

- SIF identification
- target SIL assignment logic
- SRS / SIF SRS structure
- SIS lifecycle reasoning
- proof test logic
- bypass control logic
- management of change logic
- lifecycle evidence expectations for process-industry applications

## Core idea

IEC 61511 is the operational lifecycle reference for process-industry SIS / SIF work.

The main guardrail:

A SIS / SIF claim requires lifecycle evidence, not only certified hardware.

## When to use it as the primary logic

Use IEC 61511 as primary when the request is about:

- SIS design or retrofit
- SIF definition
- SIF SRS generation
- SIL verification review for a process protection function
- proof testing
- bypass or override management
- MOC for SIS-relevant changes

## What to look for

### Basis

- HAZOP or equivalent hazard basis
- LOPA or equivalent risk basis
- initiating event logic

### SIF definition

- SIF statement
- sensors
- logic solver
- final elements
- safe state
- response time

### SRS quality

- clear trip logic
- reset logic
- bypass / override rules
- alarm and HMI expectations
- diagnostics and fault handling

### Lifecycle evidence

- FAT / SAT
- validation
- proof test requirements
- operating constraints
- maintenance expectations
- MOC discipline

## Common mistakes

### Mistake 1: calling certified hardware a complete SIF justification

Hardware certification can support the case, but it does not replace:

- function definition
- loop-level evidence
- proof test assumptions
- validation
- operating and maintenance controls

### Mistake 2: weak bypass visibility

Bypass logic that is poorly controlled or poorly visible on the HMI is a significant lifecycle weakness.

### Mistake 3: incomplete response-time basis

If the SIF response time is vague or unjustified, the safety argument is weak.

### Mistake 4: no MOC trigger for safety-relevant changes

Changes to timing, logic, device type, parameters, HMI behavior, or procedures should trigger safety impact review.

## Preferred output cues

For IEC 61511-centered outputs, prefer:

- SIF-centered wording
- loop-level evidence language
- proof test and bypass control visibility
- explicit MOC triggers

## Minimal checklist

- [ ] hazard and risk basis exists
- [ ] SIF is clearly defined
- [ ] target SIL basis is identified
- [ ] SRS quality is adequate
- [ ] sensors / logic solver / final elements are defined
- [ ] proof test logic is addressed
- [ ] bypass control is addressed
- [ ] validation is addressed
- [ ] MOC is addressed
