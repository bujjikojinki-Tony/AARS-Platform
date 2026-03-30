---
title: AARS_Capability_Lifecycle_Model
type: spec
status: draft
project: AARS
tags:
  - aars
  - capability
  - lifecycle
  - model
created: 2026-03-28
source: ChatGPT
---

# AARS_Capability_Lifecycle_Model

## 1. Purpose

This document defines the lifecycle model of capabilities in AARS.

It explains:
- how capabilities are discovered
- how they are formalized
- how they are validated through bounded cases
- how they move from candidate to reusable system asset
- how they are reviewed, frozen, revised, or retired

This document is the capability-side operating model of AARS.

---

## 2. Core Definition

A capability in AARS is:

**a reusable bounded operational unit that can be invoked within a project or case to produce structured outputs under governed conditions.**

A capability is not:
- a vague task label
- a one-time prompt
- a generic topic
- a polished description without operational use

A capability must be reusable, bounded, and operationally meaningful.

---

## 3. Lifecycle Principle

The core principle is:

**a capability should not be treated as mature until it has been exercised in bounded execution and reviewed through objectized outputs.**

This means capabilities do not become stable merely because they sound useful.

They must move through a lifecycle.

---

## 4. Capability Lifecycle Stages

The recommended lifecycle is:

1. Candidate  
2. Framed  
3. Formalized  
4. Invoked  
5. Reviewable  
6. Conditionally Stable  
7. Stable  
8. Frozen  
9. Revised  
10. Retired  

---

## 5. Stage 1 — Candidate

### Meaning
A possible reusable operation has been identified.

### Typical Source
- legacy routines
- domain method notes
- repeated analyst behavior
- recurring review steps
- migration mapping
- case needs

### Questions
- Is this operation recurring?
- Is it worth formalizing?
- Is it bounded enough?
- Does it belong to this domain/project?

### Output
- capability candidate note
- capability catalog entry

At this stage, a capability is only a candidate.

---

## 6. Stage 2 — Framed

### Meaning
The capability has a bounded role and scope.

### It should now define:
- purpose
- inputs
- outputs
- scope
- limits
- where it fits in the workflow

### Questions
- What exactly does this capability do?
- What does it not do?
- What object chain might it feed?
- What case should validate it first?

At this stage, the capability becomes operationally discussable.

---

## 7. Stage 3 — Formalized

### Meaning
The capability has been expressed in a formal capability object form.

### It should now include:
- stable name
- bounded purpose
- expected inputs
- expected outputs
- invocation conditions
- relationship to other capabilities
- current review status

### Questions
- Is the object complete enough to invoke?
- Is the naming stable?
- Is the scope narrow enough?
- Does it avoid capability inflation?

At this stage, the capability is ready for bounded execution.

---

## 8. Stage 4 — Invoked

### Meaning
The capability has been used in a real bounded case.

### Requirements
- invocation record exists
- case linkage exists
- outputs are inspectable
- downstream object relevance is visible

### Questions
- Did the capability work in context?
- Did it produce meaningful output?
- Did it create useful structured downstream objects?
- Was its scope realistic?

Invocation is the first operational proof step.

---

## 9. Stage 5 — Reviewable

### Meaning
The capability has enough evidence to be reviewed, but not yet enough to be considered stable.

### Typical Signs
- first invocation completed
- outputs are meaningful
- limitations remain visible
- edge cases remain open
- naming or scope may still need refinement

### Questions
- Is the capability worth keeping?
- Is the formalization good enough?
- Are outputs structurally aligned?
- Is revision required before reuse?

Reviewable is a legitimate maturity state, not a failure.

---

## 10. Stage 6 — Conditionally Stable

### Meaning
The capability is usable, but with visible limits or caution conditions.

### Typical Signs
- more than one reasonable use path exists
- outputs are sufficiently coherent
- known limitations are explicit
- reuse is possible under stated conditions

### Questions
- Under what conditions is this capability safe to reuse?
- What unresolved items remain?
- Is further strengthening needed before wider use?

This stage is often appropriate for first-wave domain capabilities.

---

## 11. Stage 7 — Stable

### Meaning
The capability has enough bounded evidence and consistency to be reused with confidence in normal cases.

### Typical Signs
- naming is stable
- scope is stable
- repeated use is coherent
- downstream object behavior is predictable enough
- limitations are known and manageable

### Questions
- Can this capability now be treated as part of the reusable system capability family?
- Can later projects inherit it without redefining it?

Stable does not mean permanent; it means sufficiently reusable.

---

## 12. Stage 8 — Frozen

### Meaning
The capability is preserved as part of a known baseline.

### Why Freeze
- to anchor reuse
- to protect validated structure
- to avoid unnecessary churn
- to support future domain scaling

Frozen is stronger than stable because it is intentionally baseline-preserved.

---

## 13. Stage 9 — Revised

### Meaning
A previously formalized or stable capability needs bounded correction.

### Reasons for Revision
- scope too broad
- scope too narrow
- poor outputs
- weak alignment with taxonomy/glossary
- missing downstream object usefulness
- poor evidence handling

### Rule
Revision should preserve continuity rather than reset blindly.

---

## 14. Stage 10 — Retired

### Meaning
The capability is no longer justified as an active reusable asset.

### Reasons for Retirement
- redundant with another capability
- too vague to be useful
- repeatedly failed bounded execution
- better absorbed into a broader capability
- no longer fits system or domain structure

Retirement is legitimate and should remain part of lifecycle governance.

---

## 15. Capability Lifecycle Triggers

Capabilities move between stages through triggers such as:

### Candidate → Framed
A recurring operation is judged worth bounding.

### Framed → Formalized
A reusable operational definition becomes clear enough for objectization.

### Formalized → Invoked
A bounded case is selected.

### Invoked → Reviewable
At least one meaningful invocation has completed.

### Reviewable → Conditionally Stable
Review shows bounded reuse is justified with caution.

### Conditionally Stable → Stable
Repeated or strong enough evidence supports confident reuse.

### Stable → Frozen
The capability is accepted into a baseline.

### Any Stage → Revised
A material weakness is found.

### Any Active Stage → Retired
The capability no longer justifies maintenance.

---

## 16. Lifecycle and Object Chain

Capabilities are upstream objects in the AARS object chain.

A typical lifecycle-enabled execution path is:

```text
Capability Candidate
→ Capability Object
→ Invocation Record
→ Dependency / Risk / Health Outputs
→ Review
→ Stable Capability Status