---
title: CDA Taxonomy Baseline
type: taxonomy
status: draft
project: CDA
tags:
  - aars
  - cda
  - taxonomy
  - pilot
created: 2026-03-27
source: canonical CDA taxonomy baseline
---

# CDA Taxonomy Baseline

## 1. Purpose

This document establishes a bounded taxonomy baseline for the **Pilot_001_CDA** project.

Its purpose is to:
- classify CDA-related concepts into stable groups
- support concept-layer validation
- reduce category mixing across pilot outputs
- provide a reusable structural baseline for concept mapping, architecture notes, and roadmap generation

This taxonomy is a **pilot baseline**, not a final ontology or authoritative domain standard.

---

## 2. Taxonomy Design Rules

This taxonomy follows these rules:

1. Categories must support bounded CDA pilot work.
2. Categories should separate **concept type** from **instance example**.
3. Categories should reduce confusion between:
   - asset
   - property
   - consequence
   - relation
   - method
   - context
   - governance artifact
4. The taxonomy should remain usable for vault/repo capture.
5. When a concept could fit more than one category, the ambiguity must be noted explicitly.

---

## 3. Taxonomy Scope

This baseline taxonomy covers only the minimum concept structure needed for the pilot to proceed through:
- glossary stabilization
- concept mapping
- layer validation
- architecture expression
- roadmap generation

It does **not** yet attempt:
- full operational subclassing
- full domain ontology
- full regulatory decomposition
- formal machine-readable representation

---

## 4. Top-Level Taxonomy

The pilot taxonomy is organized into eight top-level categories:

1. **Core Domain Concepts**
2. **Asset and Artifact Concepts**
3. **Property and Evaluation Concepts**
4. **Consequence and Assurance Concepts**
5. **Structural and Relation Concepts**
6. **Context and System Concepts**
7. **Method and Representation Concepts**
8. **Governance and Process Concepts**

---

## 5. Category Definitions and Members

## 5.1 Core Domain Concepts

### Definition
Concepts that define the central subject matter of the pilot.

### Included Concepts
- [[CDA]]
- [[Digital Asset]]

### Rationale
These concepts provide the principal domain anchor for the pilot.

### Boundary Notes
- `Digital Asset` is broader than `CDA`.
- `CDA` should not be collapsed into cybersecurity language alone.

---

## 5.2 Asset and Artifact Concepts

### Definition
Concepts that refer to digital things, managed digital objects, or structured artifacts that may be treated as assets, evidence-bearing objects, or operationally relevant digital entities.

### Included Concepts
- [[Digital Asset]]
- [[Data]]
- [[Configuration]]
- [[Model]]
- [[Digital Twin]]

### Provisional Members
- Assurance Artifact

### Rationale
These concepts identify what kinds of digital things may be evaluated for criticality or relied upon in operation, analysis, assurance, or governance.

### Boundary Notes
- `Model` is not identical to `Digital Twin`.
- `Configuration` should not be treated merely as metadata if its state can influence system behavior.
- `Assurance Artifact` remains provisional until later refinement.

---

## 5.3 Property and Evaluation Concepts

### Definition
Concepts that express qualities, evaluative dimensions, or criteria used to assess the status, importance, trustworthiness, or relevance of an asset or relation.

### Included Concepts
- [[Criticality]]
- [[Integrity]]
- [[Availability]]
- [[Confidentiality]]
- [[Trust]]

### Provisional Members
- Asset Criticality Criteria

### Rationale
These concepts are necessary to judge whether an asset may qualify as critical and how its role should be interpreted.

### Boundary Notes
- `Criticality` is an evaluative status, not an asset.
- `Integrity`, `Availability`, and `Confidentiality` are quality/protection dimensions, not standalone asset classes.
- `Trust` is a judgment concept, not a direct control mechanism.

---

## 5.4 Consequence and Assurance Concepts

### Definition
Concepts that describe adverse outcomes, protected values, or assurance-oriented states that justify why an asset may matter.

### Included Concepts
- [[Mission Impact]]
- [[Risk]]
- [[Safety]]
- [[Security]]
- [[Cybersecurity]]

### Provisional Members
- Regulatory Relevance

### Rationale
These concepts explain why criticality matters and how consequences are interpreted in operational or regulated settings.

### Boundary Notes
- `Risk` is not equivalent to `Criticality`.
- `Security` is broader than `Cybersecurity`.
- `Regulatory Relevance` remains provisional until later domain-specific refinement.

---

## 5.5 Structural and Relation Concepts

### Definition
Concepts that describe how assets, functions, and consequences are linked across the system structure.

### Included Concepts
- [[Dependency]]
- [[System Function]]

### Provisional Members
- Operational Dependency Chain

### Rationale
Criticality often emerges through structural dependence rather than from intrinsic asset type alone.

### Boundary Notes
- `Dependency` is a relation concept, not a quality.
- `System Function` is not itself an asset, though assets may support it.
- `Operational Dependency Chain` remains provisional until the relation structure is further formalized.

---

## 5.6 Context and System Concepts

### Definition
Concepts that describe the broader system setting, domain environment, or operational context in which CDA reasoning occurs.

### Included Concepts
- [[CPS]]

### Related Context Concepts
- [[Mission Impact]]
- [[Safety]]
- [[Cybersecurity]]

### Rationale
CDA does not exist in abstraction; it is judged within system and mission context.

### Boundary Notes
- `CPS` is a contextual system class, not the same thing as CDA.
- Context concepts should not replace core CDA concepts.

---

## 5.7 Method and Representation Concepts

### Definition
Concepts that describe engineering approaches, representational methods, or formalized means used to structure and reason about systems and assets.

### Included Concepts
- [[MBSE]]
- [[Model]]
- [[Digital Twin]]
- [[Validation]]
- [[Review]]

### Rationale
These concepts support structured analysis, representation, and evaluation in the pilot.

### Boundary Notes
- `MBSE` is a method/support discipline, not a CDA subclass.
- `Validation` and `Review` are process/assessment concepts but are included here because they are methodologically central to structured reasoning.
- `Digital Twin` may appear here and in asset/artifact-related reasoning; this dual role should be tracked explicitly.

---

## 5.8 Governance and Process Concepts

### Definition
Concepts that support bounded progression, continuity, stability, review, recovery, and structured knowledge capture within AARS-guided work.

### Included Concepts
- [[Stable View]]
- [[Latest Stable View]]
- [[Health Snapshot]]
- [[Recovery Path]]
- [[Pilot]]
- [[Bounded Case]]
- [[Knowledge Capture]]

### Rationale
These concepts are necessary because the pilot is not only studying CDA content; it is also validating governed research progression.

### Boundary Notes
- These are not CDA domain concepts in the narrow sense.
- They are pilot-operating concepts required for AARS execution and continuity.

---

## 6. Cross-Category Placement Notes

Some concepts may appear relevant to more than one category. For the pilot, use the following primary placements:

| Concept | Primary Placement | Secondary Relevance |
|---|---|---|
| Digital Asset | Core Domain Concepts | Asset and Artifact Concepts |
| Digital Twin | Asset and Artifact Concepts | Method and Representation Concepts |
| Model | Asset and Artifact Concepts | Method and Representation Concepts |
| Review | Method and Representation Concepts | Governance and Process Concepts |
| Validation | Method and Representation Concepts | Governance and Process Concepts |
| Mission Impact | Consequence and Assurance Concepts | Context and System Concepts |
| System Function | Structural and Relation Concepts | Context and System Concepts |

### Rule
When ambiguity exists, keep one **primary taxonomy placement** and note secondary relevance rather than duplicating the concept as multiple independent types.

---

## 7. Category-to-Pilot Mapping

This taxonomy supports the pilot outputs as follows:

### Glossary Support
The taxonomy gives stable concept grouping for glossary refinement.

### Concept Map Support
The taxonomy provides category anchors for relation mapping.

### Layer Validation Support
The taxonomy helps identify whether concept types have been mixed across layers.

### Architecture Note Support
The taxonomy helps distinguish:
- assets
- relations
- consequence logic
- context
- method support

### Roadmap Support
The taxonomy helps separate possible paper contributions by conceptual focus.

---

## 8. Preliminary Substructure for Later Use

The following internal subdivision may be useful later but is not yet final.

### Under Core Domain Concepts
- asset scope concepts
- criticality framing concepts

### Under Asset and Artifact Concepts
- data-like artifacts
- model-like artifacts
- configuration-like artifacts

### Under Property and Evaluation Concepts
- protection properties
- trust/evaluation properties
- criticality criteria

### Under Consequence and Assurance Concepts
- consequence concepts
- protected-value concepts
- assurance relevance concepts

### Under Structural and Relation Concepts
- direct dependency concepts
- propagated dependency concepts
- function-support concepts

### Under Governance and Process Concepts
- state monitoring concepts
- continuity concepts
- bounded progression concepts

---

## 9. Taxonomic Distinctions to Preserve

The following distinctions must be preserved throughout the pilot:

1. **CDA** is a domain-central concept, not a synonym for cybersecurity issue.
2. **Digital Asset** is broader than **CDA**.
3. **Criticality** is an evaluative property, not an object class.
4. **Risk** is a consequence/governance concept, not the same as criticality.
5. **Dependency** is a relation concept, not a quality.
6. **CPS** is a system context, not a CDA subtype.
7. **MBSE** is a method discipline, not a core CDA class.
8. **Pilot governance concepts** should not be mistaken for CDA content categories.

---

## 10. Known Taxonomy Tensions

The following issues remain open and should be revisited during concept-layer validation:

### Tension 1 — Digital Twin Placement
`Digital Twin` can be treated as:
- an artifact
- a representation
- an operationally significant digital asset

This requires later refinement.

### Tension 2 — Model vs Asset
Some models are merely design artifacts; others may become operationally critical.  
The taxonomy must later distinguish representational role from operational dependency.

### Tension 3 — Security vs Cybersecurity
The pilot currently places both under consequence and assurance logic, but domain refinement may require stricter nesting.

### Tension 4 — Governance Concepts vs Domain Concepts
AARS governance concepts are necessary for pilot execution, but should remain separable from CDA domain taxonomy.

---

## 11. Immediate Next Use

This taxonomy should be used next to support:
1. `CDA_Concept_Map.md`
2. `CDA_Layer_Validation_Note.md`
3. `CDA_Layered_Architecture.md`

It should be revised if:
- concept mapping exposes category conflicts
- layer validation finds systematic mixing
- roadmap generation requires clearer conceptual boundaries

---

## 12. Current Baseline Judgment

At this stage, the taxonomy baseline is considered:

- **usable for pilot continuation**
- **sufficient for initial concept mapping**
- **not yet final**
- **subject to refinement after layer validation**

This document therefore serves as a **working taxonomy baseline** for the next pilot phase.
