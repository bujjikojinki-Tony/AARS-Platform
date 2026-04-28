# Safety Software V&V / Functional Safety Output

## 1. Invocation Context

Task type: Research Report

Context: Chemical process plant SIS retrofit. The team is confusing the roles of IEEE 1012, IEC 61508, and IEC 61511 and needs an engineering-ready explanation rather than a certification opinion.

## 2. System Boundary

The target boundary for this report is the safety-related software and lifecycle evidence associated with a process-industry Safety Instrumented System and its Safety Instrumented Functions.

Included:

- SIS lifecycle activities
- SIF definition and evidence
- safety-related software V&V activities
- validation, proof test, and change control expectations

Not included:

- final regulator judgement
- formal certification decision
- plant-wide non-safety business control functions unless they affect SIS behavior

## 3. Safety Relevance

This topic is safety-related because misunderstanding the division of responsibility between V&V and functional safety standards can lead to:

- incomplete lifecycle evidence
- false SIL confidence
- testing being mistaken for full V&V
- missing validation of the intended safety function
- unsafe modification control

## 4. Applicable Standard Logic

### IEEE 1012

IEEE 1012 is primarily the V&V process backbone. It structures how to plan, perform, review, and report verification and validation activities across the lifecycle. It is especially useful for:

- V&V planning
- independence expectations
- requirements, design, and implementation review
- traceability
- anomaly management
- configuration management
- final V&V reporting

It answers the question: how do we obtain disciplined evidence that the lifecycle outputs have been checked appropriately?

### IEC 61508

IEC 61508 is the generic functional safety lifecycle standard for E/E/PE safety-related systems. It is used to reason about:

- hazard and risk analysis
- safety functions
- SIL allocation logic
- systematic capability
- hardware and software lifecycle expectations
- safety validation
- operation, maintenance, and modification

It answers the question: what must exist across the lifecycle for a safety function to be justified?

### IEC 61511

IEC 61511 is the process-industry application layer for SIS and SIF work. It operationalizes functional safety for process plants and is the most directly relevant standard when the project is about SIS retrofit, SIF definition, SRS, SIL verification, proof testing, bypass control, and MOC.

It answers the question: how is functional safety actually executed for process-industry SIS/SIF engineering and operation?

### Relationship among the three

- IEEE 1012 governs the quality and completeness of V&V activities
- IEC 61508 governs the generic functional safety lifecycle logic
- IEC 61511 adapts that lifecycle into concrete SIS/SIF process-industry practice

They are complementary, not interchangeable.

## 5. Analysis / Deliverable

## Executive Summary

The cleanest way to separate the standards is:

- Use IEEE 1012 to govern how V&V is planned, executed, traced, and concluded
- Use IEC 61508 to define the generic functional safety lifecycle expectations
- Use IEC 61511 to execute that lifecycle for process-industry SIS/SIF applications

The most common misunderstanding is treating a SIL-certified device as sufficient evidence for an overall SIF SIL claim. That is incorrect. SIL applies to the safety function or SIF, not simply to one certified component.

## Standard Positioning

### Where IEEE 1012 fits

IEEE 1012 is strongest when the team asks:

- what reviews are required
- how independent the V&V work should be
- how traceability should be maintained
- how anomalies and configuration changes should be handled
- what belongs in a V&V summary report

### Where IEC 61508 fits

IEC 61508 is strongest when the team asks:

- what constitutes a safety function
- how SIL should be reasoned about
- what lifecycle evidence is required
- how software and hardware safety expectations connect
- what validation means for the safety function

### Where IEC 61511 fits

IEC 61511 is strongest when the team asks:

- how to identify a SIF
- how HAZOP / LOPA results feed target SIL
- what the SRS should contain
- how proof test and bypass management should be controlled
- how MOC affects SIS lifecycle evidence

## Industry Application

For SIS retrofit projects, the practical mapping is:

1. Use process hazard and risk work to define or confirm the SIF basis.
2. Use IEC 61511 to structure the SIS/SIF lifecycle artifacts.
3. Use IEC 61508 as the generic functional safety logic behind lifecycle expectations and SIL reasoning.
4. Use IEEE 1012 to make the V&V work disciplined, reviewable, and traceable.

## Core Concepts

### Verification vs validation

- Verification: did we build it right?
- Validation: did we build the right thing for the intended safety purpose?

### SIL

SIL belongs to the safety function or SIF. It is not a property that can be claimed solely from:

- a logic solver certificate
- a sensor certificate
- a final element data sheet

### Lifecycle evidence

A credible safety claim needs evidence across:

- hazard basis
- safety function definition
- requirements
- design
- implementation
- verification
- validation
- operation and maintenance controls
- proof testing
- change control

## Lifecycle Method

Recommended integrated lifecycle:

1. Define EUC and SIS boundary.
2. Confirm hazard and risk basis.
3. Identify safety functions / SIFs.
4. Assign target SIL where required.
5. Create SRS / SIF SRS.
6. Design sensors, logic solver, and final elements.
7. Implement logic and configuration under control.
8. Execute V&V activities using IEEE 1012 discipline.
9. Perform SIL verification where applicable.
10. Perform safety validation against intended-use scenarios.
11. Define proof test, bypass, alarm, reset, and MOC controls.
12. Maintain evidence through operation and modification.

## Engineering Application

For day-to-day project execution, use the standards this way:

- IEEE 1012 for the V&V Plan, traceability matrix, review records, anomaly control, and final V&V summary
- IEC 61511 for SIF identification, SRS development, FAT / SAT, proof test planning, bypass control, and MOC expectations
- IEC 61508 for the generic logic behind lifecycle integrity, SIL reasoning, systematic capability, and validation expectations

## Standard Relationships

The standards should not be treated as substitutes:

- IEEE 1012 cannot replace functional safety lifecycle requirements
- IEC 61508 / 61511 cannot replace disciplined lifecycle V&V planning and reporting
- IEC 61511 should be the most operational standard for process SIS/SIF execution

## Typical Workflow

1. Hazard basis available
2. SIF defined
3. Target SIL assigned
4. SRS issued
5. Design completed
6. V&V plan issued
7. Logic and integration verified
8. SIL verification completed
9. Safety validation completed
10. Proof test and bypass control defined
11. MOC and operational evidence maintained

## Evidence Chain

```text
Hazard
-> Risk Scenario
-> Safety Function / SIF
-> Safety Requirement
-> Design Element
-> Logic / Configuration
-> Verification Evidence
-> Validation Evidence
-> Operation / Proof Test Evidence
-> Change Record
```

## Recommendations

1. Write one integrated project note that explicitly assigns each standard to its role.
2. Prohibit device-only SIL claims in internal reviews.
3. Make validation scenario coverage a formal gate before release.
4. Add IEEE 1012-style traceability, anomaly management, and configuration control to SIS retrofit work.
5. Treat proof testing, bypass management, and MOC as part of the safety evidence chain, not post-project housekeeping.

## 6. Evidence and Gaps

This is a standards-positioning report, not a plant-specific compliance review. No plant-specific evidence set was assessed.

## 7. Risks

- treating testing as equivalent to full V&V
- treating IEC 61511 as only a hardware selection exercise
- claiming SIL from certified devices without full SIF evidence
- omitting validation of intended safety purpose
- weakening change control after retrofit

## 8. Recommended Next Step

Generate an integrated SIS retrofit execution guide or a project-specific V&V Plan and SIF evidence matrix.

## 9. Closure Status

Conditional Complete
