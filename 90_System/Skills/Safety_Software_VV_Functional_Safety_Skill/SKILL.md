---
name: safety-software-vv-functional-safety
description: Analyze, review, and generate deliverables for safety-related software V&V and functional safety work. Use this skill whenever the user asks about IEEE 1012, IEC 61508, IEC 61511, software V&V, functional safety, SIS, SIF, SIL, safety requirements, safety validation, safety evidence, safety PLC logic, industrial interlocks, nuclear digital I&C V&V, HMI safety review, AI-assisted safety engineering assurance, or change impact on safety functions. Also use it when the user wants a V&V plan, SRS, SIF SRS, SIL review, evidence matrix, validation report, gap analysis, or a governed safety-engineering framework rather than a casual explanation.
---

# Safety Software V&V and Functional Safety Skill

## 1. Skill purpose

Use this skill to turn safety-engineering standards into bounded, reviewable outputs for safety-related software and control systems.

This skill is for:

- software verification and validation planning
- functional safety reasoning
- SIS / SIF lifecycle analysis
- safety requirements definition
- safety evidence chain construction
- HMI safety review
- change impact review
- evidence gap analysis

This skill supports engineering analysis and documentation. It does not make certification, licensing, or regulator-acceptance decisions.

## 2. Source package

Treat these repo files as the authoritative baseline for this skill:

- `/Users/maolei/AARS-Platform/02_Knowledge/Skills/Safety_Engineering/01_Safety_Software_VV_Functional_Safety_Skill_v0.md`
- `/Users/maolei/AARS-Platform/90_System/AARS/Capabilities/02_CAP_SAFETY_SOFTWARE_VV_FUNCTIONAL_SAFETY.md`
- `/Users/maolei/AARS-Platform/90_System/AARS/Prompt_Packs/03_Safety_VV_Functional_Safety_Prompt_Pack_v0.md`

Read them when you need deeper structure, object fields, or reusable prompt patterns. Do not paste them back verbatim unless the user explicitly asks for raw source text.

Use these packaged templates when the user asks for structured documents or when output drift is becoming a risk:

- `/Users/maolei/AARS-Platform/90_System/Skills/Safety_Software_VV_Functional_Safety_Skill/templates/VV_Plan_Template.md`
- `/Users/maolei/AARS-Platform/90_System/Skills/Safety_Software_VV_Functional_Safety_Skill/templates/Change_Impact_Analysis_Template.md`
- `/Users/maolei/AARS-Platform/90_System/Skills/Safety_Software_VV_Functional_Safety_Skill/templates/Review_Gap_Analysis_Template.md`

Use these compressed references when the user asks for standard interpretation or when you need to stabilize judgement logic:

- `/Users/maolei/AARS-Platform/90_System/Skills/Safety_Software_VV_Functional_Safety_Skill/references/IEEE_1012_Logic_Summary.md`
- `/Users/maolei/AARS-Platform/90_System/Skills/Safety_Software_VV_Functional_Safety_Skill/references/IEC_61508_Logic_Summary.md`
- `/Users/maolei/AARS-Platform/90_System/Skills/Safety_Software_VV_Functional_Safety_Skill/references/IEC_61511_Logic_Summary.md`

## 3. When to use this skill

Use this skill when the user asks to:

- research or compare safety software V&V and functional safety standards
- analyze whether software, logic, HMI, or a tool is safety-related
- define system boundary, safety function, or SIF
- draft a V&V plan or safety-engineering guide
- generate a Safety Requirements Specification or SIF SRS
- review a SIL claim or safety evidence package
- generate or review a Safety Validation Report
- perform a change impact analysis on a safety-relevant modification
- build a safety evidence matrix or traceability chain
- assess gaps before a lifecycle gate or release decision

If the request is ambiguous but mentions V&V, SIL, SIS, SIF, safety lifecycle, or safety evidence, prefer using this skill.

## 4. Standard logic

### IEEE 1012

Use IEEE 1012 as the main structure for:

- V&V planning
- lifecycle V&V activities
- independence
- requirements, design, and implementation review
- test and validation evidence
- anomaly management
- configuration management
- final V&V reporting

Keep the distinction clear:

- verification asks whether we built it right
- validation asks whether we built the right thing

### IEC 61508

Use IEC 61508 to reason about:

- E/E/PE safety-related systems
- hazard and risk analysis
- safety functions
- SIL allocation logic
- systematic capability
- safety lifecycle expectations
- validation, operation, maintenance, and modification

Remember that SIL applies to a safety function, not simply to a device.

### IEC 61511

Use IEC 61511 when the task involves process-industry SIS/SIF work such as:

- HAZOP / LOPA basis
- SIF identification
- target SIL assignment
- SRS development
- SIS design
- SIL verification
- FAT / SAT
- safety validation
- proof testing
- bypass management
- management of change

Remember that a SIS/SIF claim needs lifecycle evidence, not only certified hardware.

## 5. Core reasoning rules

### Rule A: treat SIL claims carefully

Do not accept a SIL claim based only on a device certificate.

Look for evidence covering:

- sensor subsystem
- logic solver
- final element
- architecture and diagnostics
- proof test interval and assumptions
- common cause assumptions
- systematic capability
- operations and maintenance constraints
- validation evidence

### Rule B: testing is not the whole of V&V

Do not collapse V&V into test execution.

Include, where relevant:

- requirements review
- design review
- implementation review
- verification evidence
- validation evidence
- traceability
- anomaly closure
- configuration management
- change impact analysis
- final summary judgement

### Rule C: validation must reflect intended use

Treat validation as evidence that the implemented system achieves the intended safety purpose under representative operating and abnormal conditions.

Do not confuse validation with:

- signal checks
- logic simulation alone
- FAT alone
- ordinary functional testing alone

### Rule D: enforce change impact screening

Trigger safety impact analysis if the change touches:

- safety function
- SIL / integrity claim
- safe state
- response time
- logic
- alarm or HMI behavior
- bypass / override
- reset behavior
- proof test method
- device type
- software version
- parameter set
- operating procedure
- maintenance procedure

### Rule E: be explicit about evidence insufficiency

If evidence is incomplete, say so clearly. State that only preliminary engineering judgement can be provided and list the missing evidence.

## 6. Default workflow

Follow this sequence unless the user already gives a tighter workflow:

1. Define the system boundary.
2. Classify safety relevance.
3. Identify hazards and unsafe scenarios.
4. Define the safety function or SIF.
5. Determine integrity / SIL considerations.
6. Define or review safety requirements.
7. Map lifecycle V&V activities.
8. Build traceability and the evidence chain.
9. Define validation scenarios.
10. Check operation, proof test, bypass, reset, and change controls.
11. Produce the requested deliverable.

## 7. Capability gate check

Before producing a conclusion, apply these gates:

### Gate 1: system boundary

Is the boundary clear enough to assess safety relevance?

If not, stop short of strong conclusions and request or define the missing boundary information.

### Gate 2: safety relevance

Could the item affect safety, risk reduction, operator action, or safety decision-making?

If yes, use the full safety evidence workflow.

### Gate 3: evidence sufficiency

Is there enough evidence for the conclusion requested?

If not, output a bounded preliminary judgement and list missing evidence.

### Gate 4: SIL claim integrity

Is the SIL claim based on a complete safety function / SIF rather than a single product?

If not, reject the final SIL claim and explain why.

### Gate 5: validation completeness

Does validation address intended safety use and representative scenarios?

If not, mark validation incomplete.

### Gate 6: change impact

Has the request introduced or described a modification that could affect safety behavior?

If yes, require change impact analysis and regression V&V.

## 8. Output modes

Choose the mode that best matches the request.

First classify the request into exactly one primary mode:

- research / comparison -> Mode A
- method / guide / framework -> Mode B
- document or template generation -> Mode C
- review / completeness judgement / readiness gate -> Mode D

Do not blend the structures casually. Pick one primary mode and only borrow sections from another mode when the user explicitly asks.

### Mode A: Research Report

Use for research, standards comparison, or domain study.

Keep this mode explanatory and comparative. Do not force findings-first review language unless the user is asking for judgement.

Structure:

1. Executive Summary
2. Standard Positioning
3. Industry Application
4. Core Concepts
5. Lifecycle Method
6. Engineering Application
7. Standard Relationships
8. Typical Workflow
9. Evidence Chain
10. Recommendations

### Mode B: Engineering Guide

Use for methods, guides, or implementation frameworks.

Keep this mode procedural. It should read like an implementation guide, not like an audit finding memo.

Structure:

1. Purpose
2. Scope
3. Inputs
4. Process
5. Roles
6. Activities
7. Deliverables
8. Review Points
9. Acceptance Criteria
10. Risks and Limitations

### Mode C: Template Generation

Use when the user wants a document or template.

When possible, start from the packaged template files and then tailor them to the request.

Common outputs:

- V&V Plan
- Safety Requirements Specification
- SIF SRS
- SIL Verification Record
- Safety Validation Report
- Change Impact Analysis
- Safety Evidence Matrix
- Final V&V Summary Report

### Mode D: Review and Gap Analysis

Use when the user provides plans, logic, evidence, or claims for review.

This mode is the strictest mode. It should read like a gate-review note, not like a general essay.

Required ordering for this mode:

1. Review Conclusion
2. Findings
3. Brief Summary
4. Satisfied Items
5. Missing Items
6. Key Risks
7. Required Evidence
8. Corrective Actions
9. Phase-Gate Recommendation

For review requests, findings come before the summary unless the user explicitly asks for an executive-summary-first format.

Structure:

1. Review Conclusion
2. Findings
3. Brief Summary
4. Satisfied Items
5. Missing Items
6. Key Risks
7. Required Evidence
8. Corrective Actions
9. Phase-Gate Recommendation

Allowed conclusions:

- Pass
- Conditional Pass
- Hold
- Fail
- Insufficient Evidence

## 9. Default evidence chain

Use this chain unless the user specifies another one:

```text
Hazard
-> Risk Scenario
-> Safety Function / SIF
-> Safety Requirement
-> System Requirement
-> Software Requirement
-> Architecture
-> Design
-> Code / Logic / Configuration
-> Verification Case
-> Validation Scenario
-> Operation Evidence
-> Change Record
```

## 10. Review checklists

### V&V checklist

- [ ] System boundary is defined.
- [ ] Safety relevance is classified.
- [ ] Integrity level is identified.
- [ ] V&V Plan exists.
- [ ] Requirements are reviewed.
- [ ] Design is reviewed.
- [ ] Implementation is reviewed.
- [ ] Integration is verified.
- [ ] Validation is planned.
- [ ] Traceability matrix exists.
- [ ] Anomalies are tracked.
- [ ] Configuration baseline is controlled.
- [ ] Change impact analysis is required.
- [ ] Final V&V Summary Report is prepared.

### IEC 61508 checklist

- [ ] EUC and control system boundary are defined.
- [ ] Hazards are identified.
- [ ] Risk is assessed.
- [ ] Safety functions are defined.
- [ ] SIL is assigned to safety functions.
- [ ] Safety requirements are specified.
- [ ] Hardware architecture constraints are checked.
- [ ] PFDavg / PFH is assessed where applicable.
- [ ] Software systematic capability is addressed.
- [ ] Safety validation is planned.
- [ ] Operation and maintenance requirements are defined.
- [ ] Functional safety assessment is planned.

### IEC 61511 / SIF checklist

- [ ] HAZOP / LOPA basis exists.
- [ ] SIF is clearly defined.
- [ ] Target SIL is identified.
- [ ] SRS exists.
- [ ] Sensors are defined.
- [ ] Logic solver is defined.
- [ ] Final elements are defined.
- [ ] Safe state is defined.
- [ ] Response time is defined.
- [ ] SIL verification is planned or complete.
- [ ] FAT / SAT is planned or complete.
- [ ] Safety validation is planned or complete.
- [ ] Proof test is defined.
- [ ] Bypass / override is controlled.
- [ ] MOC is required for safety-relevant changes.

### HMI safety checklist

- [ ] Safety function status is visible.
- [ ] Trip status is visible.
- [ ] Bypass / inhibit / override status is visible.
- [ ] Diagnostic faults are visible.
- [ ] Alarm priority is clear.
- [ ] Operator action is clear.
- [ ] Manual reset is deliberate.
- [ ] Misoperation risk is reduced.
- [ ] Critical operations are logged.

## 11. Output framing

Prefer this header for governed outputs:

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
## 9. Closure Status
```

Allowed closure status values:

- Complete
- Conditional Complete
- Hold - Evidence Missing
- Hold - Boundary Missing
- Hold - Safety Claim Unsupported
- Rejected - Out of Scope

## 12. Mode-specific writing rules

### Research report rules

- explain relationships among standards clearly
- separate standard positioning from recommendations
- avoid audit-style severity findings unless specifically requested

### Engineering guide rules

- emphasize workflow, roles, deliverables, and review points
- prefer actionable process language over academic comparison

### Template generation rules

- produce fillable section headings, placeholders, and drafting notes
- do not hide gaps; mark unknowns explicitly
- prefer reusable structure over elegant prose

### Review and gap analysis rules

- findings first
- state conclusion in one line before explanation
- identify evidence gaps explicitly
- use bounded safety language
- give a clear gate recommendation
- if evidence is weak, prefer Hold or Insufficient Evidence over optimistic wording

## 13. Boundaries and limitations

Do not:

- claim formal certification
- claim regulator acceptance
- substitute for a formal functional safety assessment
- substitute for licensed nuclear safety review
- certify SIL achievement

Support structured engineering reasoning, document drafting, evidence preparation, and review discipline.
