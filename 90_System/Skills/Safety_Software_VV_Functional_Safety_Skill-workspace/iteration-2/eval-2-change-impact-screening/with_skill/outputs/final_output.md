# Safety Software V&V / Functional Safety Output

## 1. Invocation Context

Primary mode: Template Generation / Change Impact Analysis

System: burner management system

Requested outcome: safety-related change impact analysis for a timing change and new HMI bypass indication.

## 2. System Boundary

The relevant boundary is the safety-related combustion protection function, associated trip logic, operator visibility of maintenance bypass status, and the evidence set needed to justify the modified release.

## 3. Safety Relevance

This change is safety-related because it can affect:

- protective response timing
- transition to safe state
- operator visibility of protection availability
- validation and release evidence

## 4. Applicable Standard Logic

- IEEE 1012: change-focused V&V discipline, traceability, and evidence control
- IEC 61508: safety function, response-time, and validation reasoning
- IEC 61511 by analogy: lifecycle evidence, bypass control, proof testing, and MOC logic relevant to protection functions

## 5. Analysis / Deliverable

## 1. Change Summary

Proposed changes:

- low airflow trip delay changed from 2 seconds to 5 seconds
- maintenance bypass state added to the HMI

This is a functional safety-relevant modification, not a cosmetic update.

## 2. Affected Items

- trip response timing
- application logic
- cause and effect behavior
- HMI bypass visibility
- operator understanding of protection availability
- release evidence baseline

## 3. Safety Impact Screening

### Safety function

Affected. The delay change can alter when the protection function initiates the safe response.

### SIL / integrity claim

Potentially affected. A timing change may invalidate prior assumptions supporting the protection claim.

### Safe state

Potentially affected. Delayed trip initiation can reduce margin to safe-state achievement.

### Response time

Directly affected. The change from 2 seconds to 5 seconds requires explicit justification against the hazard basis and allowable process safety time.

### Logic

Affected. The application logic and associated sequence behavior have changed.

### Alarm / HMI

Affected. The HMI now exposes maintenance bypass state, which changes operator awareness and potentially operating assumptions.

### Bypass / override

Affected. The new display is tied directly to bypass state visibility and control discipline.

## 4. Hazard and Risk Impact

Main risk question: does the extended delay increase exposure to unsafe combustion conditions beyond the accepted hazard basis?

Potential consequences:

- delayed protective action
- reduced safety margin
- changed assumptions from the original hazard review
- increased reliance on operator awareness if bypass is active

## 5. Requirements Impact

Likely affected requirements:

- trip response time requirement
- safety function initiation criteria
- HMI bypass indication requirement
- operator action requirement when bypass is active
- verification and test acceptance criteria tied to delay behavior

## 6. Design and Implementation Impact

Impacted elements:

- PLC timing implementation
- interlock sequence behavior
- HMI status object and display logic
- possibly associated reset or nuisance-trip handling logic

## 7. Verification and Regression Impact

Required verification work:

- logic review of the modified path
- update review of cause and effect matrix
- traceability update from requirement to logic
- regression verification on affected trip paths
- HMI verification for clear and unambiguous bypass visibility

## 8. Required Validation

Required validation work:

- representative low-flow scenarios
- abnormal condition scenarios
- safe-state confirmation under revised delay
- operator interpretation of maintenance bypass visibility

FAT fragments alone are not sufficient if they do not show intended-use validation.

## 9. Evidence Gaps

Current missing or weak evidence:

- approved rationale for the timing change
- hazard basis showing 5 seconds is acceptable
- process safety time basis or equivalent timing justification
- updated requirements or approved design basis
- complete change-focused verification record
- complete regression results
- intended-use validation evidence
- updated operating or maintenance procedure references if bypass visibility changes practice
- formal release baseline for the modified logic

## 10. Disposition

Hold

The currently described evidence set does not support direct deployment.

## 11. Required Actions

1. Confirm the affected protection function and its hazard basis.
2. Re-check response-time assumptions.
3. Update requirements and cause and effect records.
4. Complete change-focused verification and regression testing.
5. Execute validation against representative scenarios.
6. Verify HMI bypass visibility and its procedure alignment.
7. issue a controlled release baseline with approval records.

## 12. Closure Conditions

Close this change only when:

- timing justification is documented
- requirements and design basis are updated
- verification and regression evidence is complete
- validation evidence is complete
- HMI bypass behavior is verified
- controlled baseline and release approval exist

## 6. Evidence and Gaps

Current evidence is insufficient for a formal safety compliance conclusion. Only preliminary engineering judgement can be provided. The missing evidence is listed above.

## 7. Risks

- underestimating the timing effect
- using partial FAT records as if they were full release evidence
- treating bypass visibility as non-safety-relevant
- releasing without controlled baseline closure

## 8. Recommended Next Step

Generate a formal project change package using the packaged Change Impact Analysis template and then attach scenario-based validation records.

## 9. Closure Status

Hold - Evidence Missing
