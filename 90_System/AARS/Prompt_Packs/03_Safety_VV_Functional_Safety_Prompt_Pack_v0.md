---
title: Safety V&V Functional Safety Prompt Pack v0
type: prompt_pack
status: draft
version: v0
domain: safety_engineering
related_capability: CAP_SAFETY_SOFTWARE_VV_FUNCTIONAL_SAFETY
---

# Safety V&V Functional Safety Prompt Pack v0

## 1. Purpose

This prompt pack provides reusable prompts for applying IEEE 1012, IEC 61508, and IEC 61511 to safety-related software, industrial control systems, SIS/SIF, HMI, and safety evidence workflows.

## Prompt 1 - General Research Report

```text
Please produce a structured research report on [TOPIC] from the perspective of safety software V&V and functional safety.
Use:
- IEEE 1012 for V&V planning, independence, traceability, verification, validation, anomaly management, configuration control, and final V&V summary;
- IEC 61508 for E/E/PE functional safety lifecycle, safety functions, SIL, systematic capability, safety validation, operation, maintenance, and modification;
- IEC 61511 where SIS/SIF, process industry, HAZOP/LOPA, SRS, proof testing, bypass, and MOC are relevant.
Report structure:
1. Executive Summary
2. Problem Context
3. Applicable Standards
4. Key Concepts
5. Lifecycle Workflow
6. Evidence Chain
7. Industry Application
8. Risks and Misunderstandings
9. Recommended Engineering Framework
10. Next Deliverables
Do not claim formal compliance or certification unless evidence is complete and certification basis is provided.
```

## Prompt 2 - V&V Plan Generation

```text
Generate a V&V Plan for the following system:
System:
[INSERT SYSTEM DESCRIPTION]
Industry context:
[NUCLEAR / PROCESS INDUSTRY / INDUSTRIAL CONTROL / MEDICAL / AEROSPACE / OTHER]
Safety relevance:
[INSERT SAFETY ROLE OR UNKNOWN]
Available evidence:
[INSERT AVAILABLE DOCUMENTS OR SAY UNKNOWN]
Use IEEE 1012 as the main V&V process structure.
Use IEC 61508 / IEC 61511 only where functionally relevant.
The V&V Plan shall include:
1. Purpose
2. Scope
3. Applicable Standards
4. System Description
5. Criticality / Integrity Level
6. V&V Objectives
7. Organization and Independence
8. Lifecycle V&V Activities
9. Traceability Strategy
10. Verification Methods
11. Validation Strategy
12. Tool Confidence
13. Configuration Management
14. Anomaly Management
15. Acceptance Criteria
16. Required Evidence
17. Open Issues
18. Approval
If information is missing, mark it as a gap instead of inventing assumptions.
```

## Prompt 3 - Safety Requirements Specification

```text
Generate a Safety Requirements Specification for the following system or function:
System / function:
[INSERT DESCRIPTION]
Hazard context:
[INSERT HAZARDS OR UNSAFE SCENARIOS]
Operational context:
[INSERT OPERATING MODES / USERS / ENVIRONMENT]
Applicable standard logic:
[IEEE 1012 / IEC 61508 / IEC 61511 / INDUSTRY-SPECIFIC]
The SRS shall include:
1. Purpose
2. System Boundary
3. Operational Context
4. Hazard and Risk Basis
5. Safety Function List
6. Safety Requirement Statements
7. Non-Functional Safety Requirements
8. HMI / Operator Safety Requirements
9. Failure Handling Requirements
10. Traceability Matrix
11. Assumptions and Constraints
12. Open Issues
13. Approval
Each requirement shall be testable, traceable, and linked to a hazard or safety function where possible.
```

## Prompt 4 - SIF SRS Generation

```text
Generate a SIF Safety Requirements Specification for the following Safety Instrumented Function:
SIF description:
[INSERT SIF DESCRIPTION]
Hazard / initiating event:
[INSERT HAZARD]
Target SIL:
[INSERT TARGET SIL OR UNKNOWN]
Known components:
Sensors:
[INSERT SENSOR TAGS OR UNKNOWN]
Logic solver:
[INSERT LOGIC SOLVER OR UNKNOWN]
Final elements:
[INSERT FINAL ELEMENTS OR UNKNOWN]
Use IEC 61511 as the primary lifecycle logic.
The SIF SRS shall include:
1. SIF Summary
2. Hazard and Risk Basis
3. SIF Statement
4. Target SIL Basis
5. Sensor Elements
6. Logic Solver
7. Final Elements
8. Trip Logic
9. Cause and Effect Matrix
10. Safe State
11. Response Time
12. Reset Requirement
13. Bypass / Override Requirement
14. Alarm and HMI Requirement
15. Proof Test Requirement
16. Diagnostics and Fault Handling
17. Environmental and Installation Constraints
18. Validation Criteria
19. Traceability
20. Evidence Gaps
Do not claim the SIF achieves the target SIL unless complete SIL verification evidence is provided.
```

## Prompt 5 - SIL Verification Review

```text
Review the following SIL claim:
Claim:
[INSERT SIL CLAIM]
SIF:
[INSERT SIF DESCRIPTION]
Evidence:
[INSERT AVAILABLE EVIDENCE]
Use IEC 61508 / IEC 61511 reasoning.
Assess whether the claim is supported by:
1. Complete SIF definition
2. Sensor subsystem evidence
3. Logic solver evidence
4. Final element evidence
5. Architecture / voting evidence
6. Failure rate data
7. PFDavg / PFH calculation
8. Proof test interval and coverage
9. Diagnostic coverage
10. Common cause assumptions
11. Systematic capability
12. Application logic V&V
13. Safety validation
14. Operation and maintenance constraints
Output:
1. Review Conclusion: Pass / Conditional Pass / Hold / Fail / Insufficient Evidence
2. Supported Items
3. Missing Evidence
4. Key Risks
5. Required Actions
6. Whether the SIL claim can be used as-is
```

## Prompt 6 - Safety Validation Report

```text
Generate a Safety Validation Report for the following system / safety function:
System / function:
[INSERT DESCRIPTION]
Safety requirements:
[INSERT REQUIREMENTS OR SUMMARY]
Validation scenarios:
[INSERT SCENARIOS OR ASK TO GENERATE]
Configuration baseline:
[INSERT VERSION INFORMATION OR UNKNOWN]
The report shall include:
1. Purpose
2. Validation Scope
3. Validation Basis
4. Configuration Baseline
5. Validation Scenarios
6. Validation Execution Record
7. Safety Function Validation
8. Response Time Validation
9. HMI / Alarm Validation
10. Bypass / Override / Reset Validation
11. Abnormal and Failure Condition Validation
12. Deviations and Anomalies
13. Validation Conclusion
14. Conditions / Restrictions
15. Approval
Clearly distinguish validation from verification and ordinary testing.
```

## Prompt 7 - Change Impact Analysis

```text
Perform a Change Impact Analysis for the following change:
Change:
[INSERT CHANGE DESCRIPTION]
Affected system:
[INSERT SYSTEM DESCRIPTION]
Known safety functions:
[INSERT SAFETY FUNCTIONS OR UNKNOWN]
Current evidence:
[INSERT AVAILABLE EVIDENCE]
Use safety software V&V and functional safety reasoning.
Check whether the change affects:
- safety function
- SIL / integrity claim
- safe state
- response time
- logic
- alarm / HMI
- bypass / override
- reset
- proof test
- device type
- software version
- parameter setting
- operating procedure
- maintenance procedure
- cybersecurity assumptions
Output:
1. Change Summary
2. Affected Items
3. Safety Impact Screening
4. Hazard and Risk Impact
5. Requirements Impact
6. Design and Implementation Impact
7. Verification and Regression Impact
8. Required Validation
9. Disposition
10. Required Actions
11. Closure Conditions
```

## Prompt 8 - Safety Evidence Matrix

```text
Build a Safety Evidence Matrix for the following project:
Project:
[INSERT PROJECT DESCRIPTION]
Hazards:
[INSERT HAZARDS]
Safety functions:
[INSERT SAFETY FUNCTIONS]
Requirements:
[INSERT REQUIREMENTS OR UNKNOWN]
Evidence:
[INSERT AVAILABLE EVIDENCE]
Use the following evidence chain:
Hazard
-> Risk Scenario
-> Safety Function / SIF
-> Safety Requirement
-> Design Element
-> Implementation Element
-> Verification Evidence
-> Validation Evidence
-> Operation Evidence
-> Change Evidence
Output:
1. Master Evidence Matrix
2. Requirements-to-Test Matrix
3. Validation Scenario Matrix
4. Operation Evidence Matrix
5. Change Evidence Matrix
6. Evidence Gap List
7. Evidence Completeness Summary
8. Final Evidence Status
```

## Prompt 9 - HMI Safety Review

```text
Review the following HMI / control interface for safety-related use:
HMI description:
[INSERT DESCRIPTION OR SCREEN SUMMARY]
Safety context:
[INSERT SAFETY FUNCTIONS / OPERATOR TASKS / ALARMS]
Use IEEE 1012 for V&V review logic.
Use IEC 61508 / IEC 61511 where safety functions, alarms, bypasses, resets, or SIS states are involved.
Review against:
1. Safety function status visibility
2. Trip status visibility
3. Bypass / inhibit / override visibility
4. Diagnostic fault visibility
5. Alarm priority clarity
6. Operator action clarity
7. Manual reset behavior
8. Prevention of misoperation
9. Critical operation logging
10. Validation scenario coverage
Output:
1. Review Conclusion
2. Strengths
3. Safety Gaps
4. HMI Risks
5. Required Improvements
6. Validation Scenarios
7. Evidence Needed
```

## Prompt 10 - Nuclear Digital I&C V&V Review

```text
Review the following nuclear digital I&C software or control system from a V&V perspective:
System:
[INSERT SYSTEM DESCRIPTION]
Safety classification:
[INSERT CLASSIFICATION OR UNKNOWN]
Available documents:
[INSERT DOCUMENTS OR UNKNOWN]
Use IEEE 1012 as the primary V&V process logic.
Treat IEC 61508 / IEC 61511 as functional safety references only, not as replacements for nuclear-specific regulatory requirements.
Review:
1. System boundary
2. Safety classification
3. Software V&V scope
4. Independence
5. Requirements traceability
6. Configuration management
7. Verification coverage
8. Validation coverage
9. Review and audit evidence
10. Change impact analysis
11. Evidence gaps
12. Readiness for next lifecycle phase
Do not make formal licensing or regulatory acceptance claims.
```

## Prompt 11 - AI-Assisted Safety Engineering Tool Review

```text
Review the following AI-assisted engineering tool for safety-related support use:
Tool:
[INSERT TOOL DESCRIPTION]
Intended use:
[INSERT USE CASE]
Safety relevance:
[INSERT WHETHER IT SUPPORTS SAFETY DECISIONS]
Use safety software V&V reasoning.
Assess:
1. Whether the AI tool is advisory or control-authoritative
2. Input data quality
3. Output verification method
4. Human review requirement
5. Traceability of AI-generated output
6. Configuration and model version control
7. Failure modes
8. Hallucination / false recommendation risk
9. Validation scenarios
10. Change and update control
11. Whether it can be used in safety-related workflows
Output:
1. Review Conclusion
2. Permitted Use Boundary
3. Prohibited Use Boundary
4. Required Controls
5. Evidence Required
6. V&V Plan Outline
```

## Prompt 12 - Final V&V Summary Report

```text
Generate a Final V&V Summary Report for the following project:
Project:
[INSERT PROJECT DESCRIPTION]
V&V activities completed:
[INSERT COMPLETED ACTIVITIES]
Requirements status:
[INSERT STATUS]
Validation status:
[INSERT STATUS]
Anomalies:
[INSERT ANOMALIES]
Configuration baseline:
[INSERT BASELINE]
The report shall include:
1. Purpose
2. Scope
3. V&V Basis
4. V&V Activities Completed
5. Requirements Verification Summary
6. Validation Summary
7. Traceability Summary
8. Anomaly Summary
9. Change Summary
10. Configuration Baseline
11. V&V Conclusion
12. Release / Use Recommendation
13. Restrictions / Conditions
14. Lessons Learned
15. Approval
Conclusion must be one of:
Pass / Conditional Pass / Hold / Fail / Insufficient Evidence.
```

## Prompt 13 - Evidence Gap Review

```text
Perform an evidence gap review for the following safety-related system:
System:
[INSERT SYSTEM DESCRIPTION]
Claim:
[INSERT SAFETY / V&V / SIL / VALIDATION CLAIM]
Available evidence:
[INSERT EVIDENCE]
Review the evidence against:
1. Boundary definition
2. Hazard identification
3. Safety function definition
4. Safety requirements
5. Integrity / SIL basis
6. Design evidence
7. Implementation evidence
8. Verification evidence
9. Validation evidence
10. Operation and maintenance evidence
11. Change control evidence
12. Independent review evidence
Output:
1. Claim Under Review
2. Evidence Present
3. Evidence Missing
4. Critical Gaps
5. Non-critical Gaps
6. Risk of Proceeding
7. Required Evidence Before Closure
8. Recommended Disposition
```

## Prompt 14 - AARS Capability Invocation Prompt

```text
Invoke CAP_SAFETY_SOFTWARE_VV_FUNCTIONAL_SAFETY for the following task.
Task:
[INSERT TASK]
Input objects:
- system_description:
- industry_context:
- hazard_context:
- safety_function_description:
- requirements_artifacts:
- design_artifacts:
- evidence_artifacts:
- change_description:
- desired_output_type:
Use the capability gates:
1. System Boundary Gate
2. Safety Relevance Gate
3. Evidence Sufficiency Gate
4. SIL Claim Gate
5. Validation Gate
6. Change Impact Gate
Output:
1. Invocation Context
2. System Boundary
3. Safety Relevance
4. Applicable Standard Logic
5. Analysis / Deliverable
6. Evidence and Gaps
7. Risks
8. Recommended Next Step
9. Capability Closure Status
```

## Prompt 15 - Minimal Quick Review

```text
Quickly review the following safety-related item:
[INSERT ITEM]
Classify it as:
- Not safety-related
- Safety-supporting
- Safety-related
- Safety-critical
- Insufficient information
Then provide:
1. Why
2. Applicable standard logic
3. Minimum required V&V
4. Evidence gaps
5. Next action
```

## 2. Prompt Pack Usage Rules

When using this prompt pack:

- Do not invent missing evidence.
- Do not claim formal compliance without evidence.
- Do not equate testing with V&V.
- Do not equate device SIL certificate with complete SIF SIL achievement.
- Always identify whether the output is preliminary engineering judgement or final review.
- Always list missing evidence when evidence is incomplete.
- Always separate verification from validation.
- Always include change impact if the task involves modification.

## 3. Recommended Placement

```text
90_System/
  AARS/
    Prompt_Packs/
      Safety_VV_Functional_Safety_Prompt_Pack_v0.md
```

Alternative:

```text
02_Knowledge/
  Skills/
    Safety_Engineering/
      Safety_VV_Functional_Safety_Prompt_Pack_v0.md
```
