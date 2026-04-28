# Safety Software V&V / Functional Safety Output

## 1. Invocation Context

Primary mode: Template Generation

Requested deliverable: SIF Safety Requirements Specification

Primary governing logic: IEC 61511

## 2. System Boundary

The SIF boundary includes:

- pressure sensing subsystem with 2oo3 transmitters
- safety PLC as logic solver
- feed isolation valve
- vent valve
- associated reset, bypass, proof test, and validation expectations

## 3. Safety Relevance

This SIF is safety-related because it is intended to reduce risk from reactor high-high pressure by driving the process toward a defined safe state.

## 4. Applicable Standard Logic

- IEC 61511 as the primary SIF lifecycle logic
- IEC 61508 as supporting generic functional-safety logic where useful
- IEEE 1012 only as supporting V&V discipline if software-review structure is needed

## 5. Analysis / Deliverable

## 1. SIF Summary

SIF name:

- Reactor High-High Pressure Protection

SIF purpose:

- on reactor pressure exceeding the trip setpoint, isolate feed and establish relief through the vent path

## 2. Hazard and Risk Basis

Known basis:

- high-high reactor pressure requiring rapid protective action

Still required:

- initiating event detail: gap
- consequence severity basis: gap
- hazard review / LOPA reference: gap

## 3. SIF Statement

When reactor pressure exceeds the defined high-high trip setpoint, the SIF shall command feed isolation and open the vent path so that the process moves to the defined safe state.

## 4. Target SIL Basis

- target SIL: SIL 2 (stated as provisional)
- SIL allocation rationale and approved basis: gap

This document does not claim the SIF achieves SIL 2. It records the provisional target and the requirements basis to be verified later.

## 5. Sensor Elements

- three pressure transmitters in a 2oo3 arrangement
- detailed tag list and calibration basis: gap
- fault handling for bad transmitter or maintenance state: gap

## 6. Logic Solver

- safety PLC
- application software version and logic baseline: gap
- diagnostic behavior and fault response detail: gap

## 7. Final Elements

- feed isolation valve
- vent valve
- valve fail position detail: gap
- final element stroke-time basis: gap

## 8. Trip Logic

Trip action:

- detect reactor pressure above high-high setpoint
- apply the configured voting logic from the 2oo3 transmitter set
- on confirmed trip, command feed isolation and vent opening

Detailed trip setpoint, filtering, debounce, and reset interlock logic: gap

## 9. Cause and Effect Matrix

Required cause and effect relationship:

- cause: reactor pressure > high-high trip setpoint
- effect 1: feed isolation valve commanded to close
- effect 2: vent valve commanded to open

Full approved C&E matrix reference: gap

## 10. Safe State

Defined safe state:

- feed cut off
- vent path established

Additional downstream unit-state expectations: gap

## 11. Response Time

The SIF shall complete detection and final action within the response-time basis required by the hazard and risk analysis.

Numerical response-time requirement: gap

## 12. Reset Requirement

Manual reset shall only be permitted after:

- reactor pressure has returned to an acceptable range
- the hazardous condition is removed or controlled
- permissive reset conditions are satisfied

Detailed reset permissives: gap

## 13. Bypass / Override Requirement

- bypass or override of this SIF shall be controlled
- bypass state shall be visible to operators
- bypass use shall be subject to authorization, duration control, and restoration tracking

Detailed bypass procedure reference: gap

## 14. Alarm and HMI Requirement

- trip status shall be visible
- bypass status shall be visible
- fault status for sensing or logic elements should be visible where relevant

Detailed alarm priority and operator response guidance: gap

## 15. Proof Test Requirement

Proof testing shall verify the continued ability of:

- the 2oo3 sensing arrangement
- the logic solver trip path
- the feed isolation valve final action
- the vent valve final action

Proof test interval and proof test coverage basis: gap

## 16. Diagnostics and Fault Handling

- bad sensor detection and degraded voting response: gap
- logic solver fault response: gap
- final element fault handling: gap

## 17. Environmental and Installation Constraints

- installation and environmental assumptions: gap
- common cause and separation assumptions: gap

## 18. Validation Criteria

Validation should demonstrate that the SIF:

- trips on the required condition
- achieves the safe state
- meets the required response-time basis
- handles reset and bypass behavior as intended

Validation scenario set and acceptance records: gap

## 19. Traceability

Traceability should connect:

- hazard basis
- SIL allocation basis
- SIF statement
- SIF requirements
- logic implementation
- verification evidence
- validation evidence

Traceability repository or matrix reference: gap

## 20. Evidence Gaps

- approved hazard / LOPA basis
- SIL allocation rationale
- numeric response-time requirement
- detailed trip setpoint and reset permissives
- valve fail-state and stroke-time basis
- proof test interval and coverage basis
- validation scenario set
- formal verification evidence

## 6. Evidence and Gaps

This SIF SRS is a drafting baseline. It does not claim the SIF achieves the target SIL without complete SIL verification and lifecycle evidence.

## 7. Risks

- provisional SIL basis being mistaken for achieved SIL
- incomplete response-time basis
- incomplete bypass and proof-test controls

## 8. Recommended Next Step

Complete the hazard basis, SIL allocation rationale, response-time basis, and proof-test assumptions, then issue a controlled SIF SRS revision.

## 9. Closure Status

Conditional Complete
