# IEEE 1012 Logic Summary

## Purpose

Use this reference when the task is mainly about software verification and validation discipline rather than generic functional-safety lifecycle allocation.

IEEE 1012 is most useful when the user needs:

- a V&V plan
- lifecycle V&V task mapping
- review scope definition
- V&V independence reasoning
- traceability expectations
- anomaly management logic
- configuration control logic
- final V&V summary framing

## Core idea

Keep the distinction clear:

- verification asks whether we built it right
- validation asks whether we built the right thing for the intended use

Do not let the output blur those two questions.

## When to use it as the primary logic

Use IEEE 1012 as the primary review or generation logic when the request is about:

- software lifecycle review
- V&V completeness
- requirements, design, code, test, and validation coverage
- readiness for a lifecycle gate
- V&V reporting
- independence and review organization

In mixed safety tasks, IEEE 1012 often governs the V&V discipline while IEC 61508 or IEC 61511 govern the functional-safety lifecycle logic.

## What to look for

### Planning

- V&V purpose
- scope and boundary
- applicable standards
- organization and independence
- lifecycle activities
- acceptance criteria

### Verification coverage

- requirements review
- design review
- implementation review
- integration verification
- traceability

### Validation coverage

- intended-use scenarios
- abnormal scenarios
- safe-state confirmation where relevant
- operational context coverage

### Control evidence

- anomaly tracking
- configuration baseline control
- change impact logic
- V&V closure summary

## Common mistakes

### Mistake 1: treating test execution as full V&V

Testing is only one part of V&V. If the evidence set contains test reports but weak requirements review, design review, traceability, anomaly closure, or validation evidence, do not describe it as complete V&V.

### Mistake 2: treating validation as a synonym for FAT or SAT

Validation should show the implemented system meets the intended safety purpose in representative use conditions. FAT and SAT may contribute, but they do not automatically close validation.

### Mistake 3: weak baseline control

If the reviewed version is unclear, V&V completeness claims should be bounded.

### Mistake 4: no explicit gap statement

If evidence is partial, say so plainly and list what is missing.

## Preferred output cues

For IEEE 1012-centered outputs, prefer:

- explicit lifecycle structure
- verification and validation separated clearly
- evidence and gaps called out directly
- bounded conclusions if evidence is incomplete

## Minimal checklist

- [ ] system boundary is defined
- [ ] V&V scope is defined
- [ ] verification coverage is described
- [ ] validation coverage is described
- [ ] traceability is addressed
- [ ] anomaly management is addressed
- [ ] configuration control is addressed
- [ ] final judgement is bounded by evidence quality
