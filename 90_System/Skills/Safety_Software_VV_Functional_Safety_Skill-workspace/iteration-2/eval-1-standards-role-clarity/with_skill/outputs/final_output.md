# Safety Software V&V / Functional Safety Output

## 1. Invocation Context

Primary mode: Research Report

Topic: role clarity among IEEE 1012, IEC 61508, and IEC 61511 for a chemical process SIS retrofit program.

Requested outcome: a structured explanation that supports engineering execution without claiming formal compliance.

## 2. System Boundary

This report addresses the boundary of safety-related software, SIS lifecycle evidence, and SIF engineering decisions relevant to a process-industry retrofit.

Inside the boundary:

- SIS / SIF lifecycle activities
- software V&V planning and evidence
- safety requirements, validation, and change control logic

Outside the boundary:

- regulator approval
- certification decisions
- plant-wide non-safety optimization functions unless they affect the SIS or SIF behavior

## 3. Safety Relevance

This topic is safety-related because poor separation of standard roles can create:

- incomplete V&V coverage
- false SIL confidence
- weak validation planning
- incomplete lifecycle evidence
- unsafe change control after retrofit

## 4. Applicable Standard Logic

### IEEE 1012

Use IEEE 1012 as the V&V process discipline for:

- V&V planning
- lifecycle review structure
- independence expectations
- traceability
- anomaly management
- configuration management
- V&V summary reporting

### IEC 61508

Use IEC 61508 as the generic functional safety lifecycle logic for:

- hazard and risk reasoning
- safety function definition
- SIL reasoning
- systematic capability
- safety validation
- lifecycle expectations for modification and maintenance

### IEC 61511

Use IEC 61511 as the process-industry execution framework for:

- SIS / SIF lifecycle activities
- HAZOP / LOPA connections
- SRS development
- SIL verification
- proof testing
- bypass management
- management of change

## 5. Analysis / Deliverable

## Executive Summary

The clean separation is:

- IEEE 1012 explains how V&V work is planned, reviewed, traced, and concluded
- IEC 61508 explains the generic functional safety lifecycle and safety-function logic
- IEC 61511 applies that functional safety logic to process-industry SIS and SIF execution

The most common engineering error is to treat a certified component as sufficient evidence for an overall SIF SIL claim. SIL applies to a safety function or SIF, not simply to a single device.

## Standard Positioning

### What problem IEEE 1012 solves

IEEE 1012 solves the discipline problem: how to organize V&V so that requirements, design, implementation, testing, validation, anomalies, traceability, and reporting are handled in a governed way.

### What problem IEC 61508 solves

IEC 61508 solves the generic lifecycle and integrity problem: how to reason about safety functions, lifecycle activities, integrity expectations, validation, and modification for E/E/PE safety-related systems.

### What problem IEC 61511 solves

IEC 61511 solves the process-industry application problem: how hazard studies, SIF definition, SRS development, proof testing, bypass management, and lifecycle evidence are executed in real SIS work.

## Industry Application

For a chemical process SIS retrofit, the standards usually map like this:

1. Use hazard and risk basis to define what protection is needed.
2. Use IEC 61511 to identify SIFs and structure SIS lifecycle deliverables.
3. Use IEC 61508 to support the functional safety logic behind lifecycle integrity and SIL reasoning.
4. Use IEEE 1012 to govern V&V planning, review depth, traceability, and final V&V closure.

## Core Concepts

### Verification and validation

- Verification asks whether the design and implementation were built correctly.
- Validation asks whether the implemented system actually fulfills the intended safety purpose under representative conditions.

### SIL

SIL should be claimed at the safety-function or SIF level. A device certificate can contribute evidence, but it does not close the full claim by itself.

### Evidence chain

A credible safety position normally connects:

```text
Hazard
-> Risk Scenario
-> Safety Function / SIF
-> Safety Requirement
-> Design and Logic
-> Verification Evidence
-> Validation Evidence
-> Operation / Proof Test Evidence
-> Change Record
```

## Lifecycle Method

Recommended integrated method:

1. Define system and SIS boundary.
2. confirm hazard and risk basis.
3. identify safety functions / SIFs.
4. assign target SIL where required.
5. issue SRS / SIF SRS.
6. design sensors, logic solver, and final elements.
7. implement software or logic under configuration control.
8. execute verification and review activities under IEEE 1012 discipline.
9. perform SIL verification where applicable.
10. perform safety validation against intended-use scenarios.
11. define proof test, bypass, reset, and MOC controls.
12. maintain lifecycle evidence through operation and modification.

## Engineering Application

Practical assignment of work products:

- IEEE 1012: V&V Plan, traceability, review records, anomaly logs, configuration control, final V&V summary
- IEC 61508: safety lifecycle reasoning, safety-function integrity logic, systematic capability expectations
- IEC 61511: SIF identification, SRS, SIS lifecycle execution, proof test, bypass control, MOC expectations

## Standard Relationships

The three standards are complementary:

- IEEE 1012 does not replace functional safety lifecycle requirements
- IEC 61508 / IEC 61511 do not replace disciplined V&V planning and reporting
- IEC 61511 is the most operational standard for process-industry SIS execution

## Typical Workflow

1. hazard basis available
2. SIF defined
3. target SIL allocated
4. SRS issued
5. design completed
6. V&V plan issued
7. implementation and integration verified
8. SIL verification completed
9. safety validation completed
10. proof test and MOC controls established

## Recommendations

1. Create one internal standard-role note that assigns each standard to its engineering purpose.
2. Ban device-only SIL conclusions in review templates.
3. Make validation scenario coverage a formal release gate.
4. Tie proof test, bypass, and MOC records into the same evidence chain as V&V artifacts.
5. Use IEEE 1012 traceability and anomaly control to strengthen SIS retrofit governance.

## 6. Evidence and Gaps

This report is methodological rather than project-certification oriented. No plant-specific evidence set was reviewed.

## 7. Risks

- treating testing as full V&V
- reducing IEC 61511 to hardware selection only
- making device-only SIL claims
- omitting intended-use validation
- weakening change control after retrofit

## 8. Recommended Next Step

Generate a project-specific V&V Plan or an integrated SIS evidence matrix using the packaged templates.

## 9. Closure Status

Conditional Complete
