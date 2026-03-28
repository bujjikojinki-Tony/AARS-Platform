---
title: CDA_Glossary_Baseline
type: glossary
status: draft
project: CDA
tags:
  - aars
  - cda
  - glossary
  - pilot
created: 2026-03-27
source: ChatGPT
---

# CDA_Glossary_Baseline

## 1. Purpose

This glossary establishes a bounded baseline vocabulary for the **Pilot_001_CDA** project.

Its purpose is to:
- stabilize core terminology
- reduce semantic drift across pilot outputs
- support taxonomy construction
- support concept-layer validation
- provide reusable vocabulary for later roadmap and architecture work

This glossary is intentionally minimal and pilot-oriented.  
It is **not** intended to be a final domain ontology.

---

## 2. Scope Rules

This glossary follows these rules:

1. Terms included here must be relevant to the bounded CDA pilot.
2. Definitions should be stable enough to support taxonomy and concept mapping.
3. Terms should be written in a way that supports reuse in future AARS work.
4. Terms should not prematurely assume a final framework.
5. Where ambiguity exists, the ambiguity should be noted explicitly.

---

## 3. Core Terms

## CDA
**Full term:** Critical Digital Assets  
**Type:** core domain concept  
**Definition:**  
Digital assets whose compromise, degradation, corruption, unavailability, or misuse could produce significant adverse consequences for the mission, safety, security, reliability, or regulated operation of a system or organization.

**Notes:**  
Within this pilot, CDA is treated as the central organizing concept.  
The exact operational boundary of CDA may vary by domain and requires structured scoping rather than informal assumption.

**Related terms:**  
[[Digital Asset]], [[Criticality]], [[Cybersecurity]], [[Mission Impact]]

---

## Digital Asset
**Type:** foundational asset concept  
**Definition:**  
Any software, data, digital model, digital configuration, digital service, or digitally mediated artifact that contributes to system operation, decision-making, control, monitoring, analysis, or evidence handling.

**Notes:**  
Not every digital asset is a CDA.  
“Digital Asset” is broader than “Critical Digital Asset.”

**Related terms:**  
[[CDA]], [[Configuration]], [[Data]], [[Digital Twin]]

---

## Criticality
**Type:** evaluation concept  
**Definition:**  
The degree to which an asset, function, or dependency is important to maintaining acceptable mission, safety, security, reliability, compliance, or operational continuity.

**Notes:**  
Criticality is not binary in all cases.  
It may be domain-defined, consequence-based, dependency-based, or risk-informed.

**Related terms:**  
[[CDA]], [[Risk]], [[Mission Impact]], [[Dependency]]

---

## Mission Impact
**Type:** consequence concept  
**Definition:**  
The effect that degradation, loss, corruption, or misuse of an asset or function has on system goals, operational objectives, safety functions, security posture, or organizational responsibilities.

**Notes:**  
Mission impact is one basis for determining criticality.

**Related terms:**  
[[Criticality]], [[Risk]], [[Safety]], [[Security]]

---

## Dependency
**Type:** structural relation concept  
**Definition:**  
A required relationship in which one asset, function, model, service, or process relies on another for availability, integrity, correctness, or continued effectiveness.

**Notes:**  
Dependency is central to CDA reasoning because criticality often emerges through dependence chains, not only from the asset itself.

**Related terms:**  
[[Criticality]], [[Risk]], [[Invocation]], [[System Function]]

---

## Risk
**Type:** governance and assessment concept  
**Definition:**  
The possibility that uncertainty, threat, failure, misuse, corruption, or degradation leads to undesirable consequences affecting safety, security, mission, compliance, or continuity.

**Notes:**  
In the AARS context, risk is not only descriptive but also operationally relevant to acceptance, deferral, and control decisions.

**Related terms:**  
[[CDA]], [[Cybersecurity]], [[Safety]], [[Health Snapshot]]

---

## Safety
**Type:** assurance concept  
**Definition:**  
The condition in which unacceptable harm to people, environment, equipment, or regulated functions is prevented or adequately controlled.

**Notes:**  
In regulated domains, safety relevance may strongly influence whether a digital asset is considered critical.

**Related terms:**  
[[Risk]], [[Criticality]], [[Mission Impact]]

---

## Security
**Type:** assurance concept  
**Definition:**  
The condition in which systems and assets are protected against unauthorized access, misuse, manipulation, disruption, disclosure, or destruction.

**Notes:**  
Security is broader than cybersecurity.  
For this pilot, cybersecurity is treated as a major but not exclusive lens for CDA analysis.

**Related terms:**  
[[Cybersecurity]], [[Risk]], [[Integrity]], [[Availability]]

---

## Cybersecurity
**Type:** protection concept  
**Definition:**  
The discipline and practice of protecting digital systems, software, data, communications, and connected infrastructure against cyber threats and cyber-enabled harm.

**Notes:**  
Cybersecurity is an important support domain for CDA work, but CDA is not reducible to cybersecurity alone.

**Related terms:**  
[[CDA]], [[Security]], [[Integrity]], [[Availability]]

---

## Integrity
**Type:** quality and protection concept  
**Definition:**  
The property that information, software, models, and digital functions remain correct, unaltered in unauthorized ways, and trustworthy for intended use.

**Notes:**  
Integrity loss may be a critical mechanism through which a digital asset becomes mission- or safety-significant.

**Related terms:**  
[[Availability]], [[Confidentiality]], [[Trust]], [[Cybersecurity]]

---

## Availability
**Type:** quality and continuity concept  
**Definition:**  
The property that an asset, function, service, or system is accessible and usable when required.

**Notes:**  
Availability is a key dimension in evaluating whether a digital asset may be critical.

**Related terms:**  
[[Integrity]], [[Continuity]], [[Dependency]]

---

## Confidentiality
**Type:** protection concept  
**Definition:**  
The property that sensitive information is not disclosed to unauthorized entities, processes, or users.

**Notes:**  
Confidentiality may contribute to CDA status in domains where sensitive data handling is mission-relevant or compliance-relevant.

**Related terms:**  
[[Integrity]], [[Cybersecurity]], [[Security]]

---

## System Function
**Type:** functional concept  
**Definition:**  
A defined operational or supporting function performed within a system to achieve mission, control, monitoring, analysis, protection, or compliance objectives.

**Notes:**  
Assets may be critical because they support critical system functions.

**Related terms:**  
[[Dependency]], [[Mission Impact]], [[Digital Asset]]

---

## Configuration
**Type:** managed asset concept  
**Definition:**  
The set of controlled settings, parameters, versions, structures, or digital definitions that determine how a digital component or system behaves.

**Notes:**  
Configurations themselves may become CDAs if incorrect, corrupted, or uncontrolled configurations can cause unacceptable consequences.

**Related terms:**  
[[Digital Asset]], [[Integrity]], [[System Function]]

---

## Data
**Type:** informational asset concept  
**Definition:**  
Encoded information used for operation, monitoring, control, analysis, decision support, evidence, or communication.

**Notes:**  
Data can be a digital asset and, under certain consequences or dependencies, a CDA.

**Related terms:**  
[[Digital Asset]], [[Integrity]], [[Availability]], [[Digital Twin]]

---

## Digital Twin
**Type:** model-based digital concept  
**Definition:**  
A digital representation of a physical asset, process, or system that is linked to its behavior, condition, lifecycle state, or operational context.

**Notes:**  
A digital twin may itself contain or depend on digital assets whose criticality requires analysis.

**Related terms:**  
[[Model]], [[Data]], [[Digital Asset]], [[MBSE]]

---

## Model
**Type:** representation concept  
**Definition:**  
A structured abstraction used to represent, analyze, design, simulate, specify, or reason about a system, function, process, or asset.

**Notes:**  
Models may become critical when they are operationally relied upon for decisions, control, assurance, or regulatory evidence.

**Related terms:**  
[[Digital Twin]], [[MBSE]], [[Digital Asset]]

---

## MBSE
**Full term:** Model-Based Systems Engineering  
**Type:** engineering method concept  
**Definition:**  
An engineering approach that uses formalized or structured models as central artifacts for system specification, design, analysis, verification, and lifecycle management.

**Notes:**  
MBSE is a support discipline in this pilot, not the central organizing concept.

**Related terms:**  
[[Model]], [[Digital Twin]], [[System Function]]

---

## CPS
**Full term:** Cyber-Physical System  
**Type:** system context concept  
**Definition:**  
A system in which computational elements, communication structures, and physical processes are tightly coupled through monitoring, control, feedback, and operational interaction.

**Notes:**  
CDA analysis may occur within CPS contexts, but CDA is not identical to CPS.

**Related terms:**  
[[Digital Asset]], [[System Function]], [[Cybersecurity]]

---

## Trust
**Type:** assurance judgment concept  
**Definition:**  
The justified confidence that an asset, system, model, data source, or process behaves as expected for a defined purpose under defined conditions.

**Notes:**  
Trust may be affected by integrity, provenance, validation status, and dependency quality.

**Related terms:**  
[[Integrity]], [[Validation]], [[Health Snapshot]]

---

## Validation
**Type:** assessment concept  
**Definition:**  
The process of determining whether a concept, model, artifact, method, or output is suitable for its intended purpose in context.

**Notes:**  
In this pilot, validation is especially important for concept layering and output stability.

**Related terms:**  
[[Trust]], [[Review]], [[Layer Validation]]

---

## Review
**Type:** governance process concept  
**Definition:**  
A structured examination of outputs, assumptions, decisions, or artifacts to determine whether they are acceptable, stable, bounded, and suitable for continuation or capture.

**Notes:**  
Review is part of supervision and bounded progression.

**Related terms:**  
[[Validation]], [[Stable View]], [[Pilot]]

---

## Stable View
**Type:** continuity and governance concept  
**Definition:**  
A coherent, sufficiently validated representation of the latest acceptable state of work that can be relied upon for continuation, review, or recovery.

**Notes:**  
Stable view is important in AARS because progression should preserve continuity and bounded reuse.

**Related terms:**  
[[Latest Stable View]], [[Recovery Path]], [[Health Snapshot]]

---

## Latest Stable View
**Type:** continuity state concept  
**Definition:**  
The most recent stable representation of project state that is judged suitable for reuse and forward progression.

**Notes:**  
This term is relevant to pilot governance and knowledge capture, even though the pilot itself is research-oriented.

**Related terms:**  
[[Stable View]], [[Recovery Path]], [[Review]]

---

## Health Snapshot
**Type:** operational state concept  
**Definition:**  
A bounded summary of current project or system condition used to assess whether progress is stable, degraded, blocked, or at risk.

**Notes:**  
Included here because AARS pilot governance depends on monitored continuity, not only content production.

**Related terms:**  
[[Risk]], [[Stable View]], [[Recovery Path]]

---

## Recovery Path
**Type:** corrective governance concept  
**Definition:**  
A defined route by which work can move from unstable, blocked, or degraded state back to a validated progression path.

**Notes:**  
Included because pilot work must remain recoverable and auditable.

**Related terms:**  
[[Health Snapshot]], [[Latest Stable View]], [[Review]]

---

## Pilot
**Type:** bounded project concept  
**Definition:**  
A deliberately limited, governed trial project used to validate methods, workflows, structures, or outputs before broader expansion.

**Notes:**  
Pilot_001_CDA is treated as a bounded validation case, not a final comprehensive program.

**Related terms:**  
[[Bounded Case]], [[Review]], [[Knowledge Capture]]

---

## Bounded Case
**Type:** scope-control concept  
**Definition:**  
A constrained case used to test structure, workflow, or method within clear scope limits and explicit non-goals.

**Notes:**  
The CDA pilot is intended to remain a bounded case.

**Related terms:**  
[[Pilot]], [[Scope]], [[Review]]

---

## Knowledge Capture
**Type:** persistence concept  
**Definition:**  
The structured preservation of outputs, decisions, vocabulary, and reusable artifacts into stable repositories or knowledge systems.

**Notes:**  
For this pilot, knowledge capture includes vault/repo placement and reuse readiness.

**Related terms:**  
[[Stable View]], [[Review]], [[Glossary]]

---

## 4. Working Terms Requiring Later Refinement

The following terms are relevant but should remain provisional until taxonomy and concept-layer validation are further developed:

### Asset Criticality Criteria
**Type:** provisional evaluation concept  
**Definition:**  
The set of explicit rules or conditions used to judge whether a digital asset should be treated as critical.

**Status:** provisional

---

### Operational Dependency Chain
**Type:** provisional structural concept  
**Definition:**  
A linked sequence of dependencies through which consequences propagate across functions, assets, services, or decisions.

**Status:** provisional

---

### Regulatory Relevance
**Type:** provisional domain concept  
**Definition:**  
The degree to which a digital asset, function, or output affects compliance, licensing, evidence, or regulated obligations.

**Status:** provisional

---

### Assurance Artifact
**Type:** provisional artifact concept  
**Definition:**  
A document, model, dataset, analysis, or output used to demonstrate confidence, compliance, verification, or validation.

**Status:** provisional

---

## 5. Terms to Keep Distinct During This Pilot

The following distinctions must be preserved:

1. **Digital Asset** ≠ **Critical Digital Asset**
2. **CDA** ≠ **Cybersecurity**
3. **Concept** ≠ **Asset instance**
4. **Model** ≠ **Digital Twin**
5. **Criticality** ≠ **Risk**
6. **Taxonomy** ≠ **Concept Map**
7. **Pilot baseline** ≠ **final framework**

---

## 6. Open Vocabulary Questions

These questions should be resolved in later pilot phases:

1. What is the minimum sufficient operational definition of CDA for this pilot?
2. What consequence dimensions should be used to determine criticality?
3. How should CDA relate to assurance artifacts and regulated evidence?
4. Should data, models, and configurations be treated as separate CDA subclasses?
5. How far should CDA scope extend into digital services and external dependencies?

---

## 7. Next Use of This Glossary

This glossary should be used as the immediate vocabulary basis for:

1. `CDA_Taxonomy_Baseline.md`
2. `CDA_Concept_Map.md`
3. `CDA_Layer_Validation_Note.md`
4. `CDA_3_Paper_Roadmap.md`

It should be revised only when:
- taxonomy construction reveals missing or unstable terms
- concept-layer validation reveals structural ambiguity
- pilot review identifies definition drift