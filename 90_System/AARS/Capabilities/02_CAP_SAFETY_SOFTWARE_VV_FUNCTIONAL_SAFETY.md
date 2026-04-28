---
id: CAP_SAFETY_SOFTWARE_VV_FUNCTIONAL_SAFETY
title: Safety Software V&V and Functional Safety Capability
type: capability
status: draft
version: v0
owner: AARS Research OS
domain: safety_engineering
capability_family:
  - verification_validation
  - functional_safety
  - safety_evidence
  - engineering_governance
---

# CAP_SAFETY_SOFTWARE_VV_FUNCTIONAL_SAFETY

## 1. Capability Name

Safety Software V&V and Functional Safety Analysis

## 2. Capability Purpose

This capability supports governed analysis, planning, review, and evidence generation for safety-related software, E/E/PE safety-related systems, SIS/SIF functions, high-integrity HMI, industrial control systems, and nuclear digital systems.

It converts safety engineering standards into bounded, traceable, reviewable outputs.

## 3. Capability Scope

### In Scope

```text
IEEE 1012-based V&V planning
IEC 61508 functional safety reasoning
IEC 61511 SIS/SIF lifecycle support
software safety requirements
SIF SRS generation
SIL evidence review
safety validation planning
change impact analysis
safety evidence matrix construction
HMI safety review
V&V gap analysis
```

### Out of Scope

- formal certification
- regulatory licensing approval
- final SIL certification
- third-party functional safety assessment replacement
- nuclear safety licensing decision

## 4. Input Objects

| Input Object | Required? | Description |
| --- | --- | --- |
| `system_description` | Yes | Description of target system, software, control logic, SIS, SIF, or HMI |
| `industry_context` | Yes | Nuclear, process industry, industrial control, medical, aerospace, etc. |
| `hazard_context` | Conditional | Hazard, unsafe scenario, or initiating event |
| `safety_function_description` | Conditional | Safety function or SIF description |
| `requirements_artifacts` | Conditional | Requirements, SRS, logic spec, C&E matrix |
| `design_artifacts` | Conditional | Architecture, diagrams, logic, interface description |
| `evidence_artifacts` | Conditional | Test reports, validation reports, SIL calculations |
| `change_description` | Conditional | For change impact analysis |
| `desired_output_type` | Yes | Report, guide, template, review, matrix, plan |

## 5. Output Objects

| Output Object | Description |
| --- | --- |
| `vv_plan` | V&V plan based on lifecycle and criticality |
| `safety_requirements` | Safety requirements or SRS |
| `sif_srs` | SIF-specific safety requirements specification |
| `sil_verification_record` | Structured SIL verification record |
| `safety_validation_report` | Validation report or validation plan |
| `change_impact_analysis` | Safety-related change assessment |
| `safety_evidence_matrix` | Hazard-to-evidence traceability matrix |
| `review_note` | Structured review with pass/hold/fail judgement |
| `evidence_gap_report` | Missing evidence and required actions |
| `prompt_pack` | Reusable prompt instructions for GPT/Codex |

## 6. Invocation Preconditions

Before invoking this capability, check:

- [ ] Is the target item potentially safety-related?
- [ ] Is there a system or software boundary?
- [ ] Is the user asking for V&V, functional safety, SIS/SIF, SIL, SRS, or safety evidence?
- [ ] Is the requested conclusion within engineering support scope rather than formal certification?

If evidence is limited, proceed with bounded analysis and mark gaps.

## 7. Invocation Modes

### Mode 1 - Research Report

Use when the task asks for investigation or standard comparison.

Expected output:

- standard positioning
- industry application
- lifecycle interpretation
- evidence framework
- engineering recommendations

### Mode 2 - Engineering Framework

Use when the task asks for method, guide, or implementation path.

Expected output:

- purpose
- scope
- input conditions
- workflow
- roles
- activities
- deliverables
- review points
- acceptance criteria
- risks

### Mode 3 - Template Generation

Use when the task asks for documents.

Expected output:

- V&V Plan
- Safety Requirements Specification
- SIF SRS
- SIL Verification Record
- Safety Validation Report
- Change Impact Analysis
- Safety Evidence Matrix
- Final V&V Summary Report

### Mode 4 - Review / Gap Analysis

Use when the task provides an existing plan, design, logic, or evidence set.

Expected output:

- review conclusion
- satisfied items
- missing evidence
- risks
- required corrective actions
- phase-gate recommendation

Allowed conclusions:

- Pass
- Conditional Pass
- Hold
- Fail
- Insufficient Evidence

## 8. Governance Gates

### Gate 1 - System Boundary Gate

Required check:

Is the system boundary clear enough to assess safety relevance?

If no:

Output: Boundary insufficient. Define system, interfaces, operating context.

### Gate 2 - Safety Relevance Gate

Required check:

Could the item affect safety, risk reduction, operator action, or safety decision-making?

If yes:

Apply V&V and functional safety evidence workflow.

### Gate 3 - Evidence Sufficiency Gate

Required check:

Is there enough evidence for the requested conclusion?

If no:

Output preliminary judgement only. List missing evidence. Do not claim compliance.

### Gate 4 - SIL Claim Gate

Required check:

Is the SIL claim based on a complete safety function/SIF rather than a single device?

If no:

Reject final SIL claim. Request complete loop evidence.

### Gate 5 - Validation Gate

Required check:

Does validation address intended safety use and representative scenarios?

If no:

Mark validation incomplete. Recommend safety validation scenarios.

### Gate 6 - Change Impact Gate

Required check:

Does the change affect safety function, logic, HMI, bypass, response time, proof testing, device type, software version, or operating procedure?

If yes:

Require Change Impact Analysis and regression V&V.

## 9. Risks

| Risk ID | Risk | Mitigation |
| --- | --- | --- |
| `R-001` | False SIL claim | Require complete SIF evidence |
| `R-002` | Testing confused with V&V | Enforce lifecycle V&V scope |
| `R-003` | Validation incomplete | Require intended-use scenarios |
| `R-004` | Missing traceability | Build evidence matrix |
| `R-005` | Change not assessed | Trigger change impact workflow |
| `R-006` | Nuclear-specific standards bypassed | Treat IEC 61508/61511 as references, not replacements |
| `R-007` | AI output treated as certified | Mark AI output as advisory and human-reviewed |

## 10. Health Indicators

| Health Indicator | Good State | Bad State |
| --- | --- | --- |
| Boundary clarity | System and interfaces defined | Vague or implicit boundary |
| Safety relevance | Explicit classification | Unknown safety role |
| Requirement quality | Testable and traceable | Ambiguous or unverifiable |
| V&V coverage | Lifecycle coverage | Only testing |
| Validation quality | Intended-use scenarios | Only functional checks |
| Traceability | Hazard-to-validation chain | Disconnected evidence |
| Change control | Impact analysis present | Ad hoc changes |
| SIL evidence | Complete SIF evidence | Device-only claim |

## 11. Default Execution Chain

```text
Input
-> Boundary Check
-> Safety Relevance Classification
-> Hazard / Unsafe Scenario Identification
-> Safety Function / SIF Definition
-> Integrity / SIL Consideration
-> Safety Requirement Formation
-> V&V Activity Mapping
-> Evidence Chain Construction
-> Validation Scenario Definition
-> Operation / Proof Test / Bypass / MOC Control
-> Review Conclusion or Deliverable Output
```

## 12. Default Output Header

Use this header for capability outputs:

```markdown
# Safety Software V&V / Functional Safety Output
## 1. Invocation Context
## 2. System Boundary
## 3. Safety Relevance
## 4. Applicable Standard Logic
## 5. Analysis / Deliverable
## 6. Evidence and Gaps
## 7. Risks
## 8. Recommended Next Step
## 9. Capability Closure Status
```

## 13. Closure Status

Allowed closure statuses:

- Complete
- Conditional Complete
- Hold - Evidence Missing
- Hold - Boundary Missing
- Hold - Safety Claim Unsupported
- Rejected - Out of Scope

## 14. Obsidian Placement

```text
90_System/
  AARS/
    Capabilities/
      CAP_SAFETY_SOFTWARE_VV_FUNCTIONAL_SAFETY.md
```

Alternative:

```text
02_Knowledge/
  Skills/
    Safety_Engineering/
      CAP_SAFETY_SOFTWARE_VV_FUNCTIONAL_SAFETY.md
```
