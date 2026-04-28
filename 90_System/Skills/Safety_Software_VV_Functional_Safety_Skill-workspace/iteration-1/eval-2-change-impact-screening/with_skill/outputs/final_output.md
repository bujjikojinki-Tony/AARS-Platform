# Safety Software V&V / Functional Safety Output

## 1. Invocation Context

Task type: Change Impact Analysis

System: Burner Management System

Proposed change:

- low airflow trip delay changed from 2 seconds to 5 seconds
- maintenance bypass status indication added to the HMI

Available evidence:

- legacy cause and effect matrix
- partial FAT records
- PLC logic printout

## 2. System Boundary

The change affects a safety-related combustion protection function within the burner management system boundary.

Included in the assessment:

- trip logic timing behavior
- HMI indication related to bypass state
- associated verification and validation needs
- baseline evidence sufficiency for implementation approval

## 3. Safety Relevance

This change is safety-related because it can affect:

- hazard detection to trip response timing
- maintenance bypass visibility to the operator
- operator understanding of protection availability
- evidence needed to justify the modified behavior

## 4. Applicable Standard Logic

- Use IEEE 1012 logic for lifecycle V&V, traceability, and change assessment discipline.
- Use IEC 61508 logic for safety function integrity and validation expectations.
- Use IEC 61511 logic by analogy for lifecycle evidence, bypass control, proof testing, and MOC expectations relevant to an instrumented protection function.

## 5. Analysis / Deliverable

## 1. Change Summary

The proposed logic change extends the trip delay from 2 seconds to 5 seconds for a low-flow initiating condition and introduces a new HMI indication for maintenance bypass state.

This is not a cosmetic-only change. It affects both protection behavior and operator visibility of protection availability.

## 2. Affected Items

- safety function response timing
- trip logic implementation
- cause and effect behavior
- HMI bypass visibility
- possible operator response assumptions
- verification and regression scope
- validation scenarios
- baseline documentation and release evidence

## 3. Safety Impact Screening

### Impact on safety function

Yes. The trip delay directly affects the timing by which the burner management system drives the system toward a safe state under low-flow conditions.

### Impact on response time

Yes. Changing the delay from 2 seconds to 5 seconds is a direct response-time modification and must be justified against the hazard basis and allowable process safety time.

### Impact on logic

Yes. The application logic and trip behavior have changed.

### Impact on HMI / bypass behavior

Yes. Adding maintenance bypass indication changes operator visibility and potentially operator decision-making around protection availability.

### Impact on proof test / operations

Potentially yes. If bypass state visibility is part of operator checks or maintenance practices, procedures and test expectations may need updating.

## 4. Hazard and Risk Impact

Key question: does increasing the delay from 2 seconds to 5 seconds reduce the margin between hazard onset and required protective action?

Potential risk consequences:

- delayed transition to safe state
- increased exposure time to unsafe combustion conditions
- changed assumptions used in the original hazard analysis
- increased dependence on operator awareness if bypass is active

Without the hazard basis, process safety time, and rationale for the timing change, the change cannot be treated as automatically acceptable.

## 5. Requirements Impact

Potentially affected requirements:

- trip response time requirement
- safety function initiation criteria
- HMI requirement for bypass visibility
- operator action requirement if bypass is active
- test acceptance criteria tied to the trip delay

The existing cause and effect matrix is necessary but not sufficient as sole approval evidence.

## 6. Design and Implementation Impact

Impacted design elements:

- PLC timing implementation
- trip logic sequence
- alarm / status indication behavior
- HMI object for maintenance bypass state
- possibly related interlock or reset logic if timing interacts with nuisance trips or manual recovery

## 7. Verification and Regression Impact

Required verification scope:

- logic review of the modified delay path
- update review of cause and effect matrix
- requirements-to-logic trace check
- targeted regression test of affected low-flow trip path
- HMI verification for bypass status visibility, clarity, and consistency

Regression concerns:

- unintended interaction with other permissives or trip paths
- timing side effects in startup, transient, or degraded flow conditions
- mismatch between PLC logic and HMI status behavior

## 8. Required Validation

Required validation topics:

- representative low-flow scenarios demonstrating the modified 5-second delay is still safe for intended use
- abnormal condition scenarios
- operator understanding of active maintenance bypass state
- validation of safe-state achievement under the revised logic timing

FAT records alone are not enough if they do not demonstrate intended-use validation.

## 9. Evidence Gaps

Missing or insufficient evidence currently includes:

- approved rationale for changing the response time
- hazard analysis or risk basis confirming 5 seconds is acceptable
- process safety time basis or equivalent timing justification
- updated safety requirements or approved design basis
- complete V&V impact assessment
- complete regression test results for the modified logic
- validation evidence for intended-use scenarios
- updated operator / maintenance procedure references if bypass visibility is operationally relevant
- formal configuration baseline for the changed release

## 10. Disposition

Recommended disposition: Hold

This change should not be approved for direct deployment on the currently described evidence set.

## 11. Required Actions

1. Confirm whether the low-flow trip is part of a defined safety function.
2. Re-check the hazard basis and allowable response time.
3. Update requirements and cause and effect documentation.
4. Perform change-focused logic verification and regression testing.
5. Validate the modified timing behavior under representative safety scenarios.
6. Verify that maintenance bypass indication is visible, unambiguous, and aligned with operating procedures.
7. issue a controlled release baseline with change records and approval evidence.

## 12. Closure Conditions

The change may proceed only when:

- timing justification is documented
- safety requirements and design basis are updated
- regression verification is complete
- validation evidence is available
- HMI bypass indication is verified
- configuration baseline and approval records are in place

## 6. Evidence and Gaps

Current evidence is insufficient for a formal safety compliance conclusion. Only preliminary engineering judgement can be provided. The missing evidence is listed above.

## 7. Risks

- underestimating response-time impact
- approving a logic change from partial FAT evidence only
- assuming HMI visibility is non-safety-relevant
- missing procedure updates for bypass awareness

## 8. Recommended Next Step

Generate a formal project Change Impact Analysis template package and a validation scenario set for the modified low-flow trip behavior.

## 9. Closure Status

Hold - Evidence Missing
