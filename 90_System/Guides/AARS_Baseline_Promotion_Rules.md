---
title: AARS_Baseline_Promotion_Rules
type: guide
status: draft
project: AARS
tags:
  - aars
  - baseline
  - promotion
  - rules
created: 2026-03-28
source: ChatGPT
---

# AARS_Baseline_Promotion_Rules

## 1. Purpose

This guide defines how artifacts in AARS may be promoted into stronger baseline status.

It is intended to:
- clarify when project-local material may become reusable system-level baseline material
- reduce premature promotion
- protect the difference between reviewable, stable, frozen, and archived assets
- support explicit governance when promoting knowledge, objects, or project outputs

This is a governance guide, not a baseline model.

---

## 2. Core Principle

The core principle is:

**promotion should follow evidence of reuse, stability, and governance readiness, not convenience**

This means:
- not every good project note should become system knowledge
- not every reviewable object should become a stable baseline
- not every stable note should become frozen
- not every project output should be promoted out of project space

Promotion must be earned.

---

## 3. What Promotion Means

Promotion in AARS means moving an artifact to a stronger reference role.

Typical promotion examples include:

- project-local concept note → reusable knowledge asset
- reviewable object → conditionally stable object
- stable view → frozen baseline
- project-local method note → system operating guide
- local pattern → reusable template

Promotion changes governance meaning, not just file placement.

---

## 4. Promotion Directions

AARS commonly promotes in the following directions:

### A. Status Promotion
Example:
- draft → reviewable
- reviewable → conditionally stable
- conditionally stable → stable

### B. Baseline Promotion
Example:
- stable state → frozen baseline

### C. Knowledge-Scope Promotion
Example:
- project-local note → reusable system knowledge

### D. Operational Promotion
Example:
- repeated local structure → official checklist / guide / template

These promotion directions should be distinguished.

---

## 5. Promotion Questions

Before promoting anything, AARS should ask:

1. Is this artifact bounded enough?
2. Is it stable enough?
3. Is it reusable enough?
4. Has it been reviewed enough?
5. Would promotion reduce duplication or create confusion?
6. Is the promotion about status, scope, baseline, or all three?

If these cannot be answered clearly, promotion is likely premature.

---

## 6. Minimum Promotion Conditions

An artifact should only be promoted when all or most of the following are true:

- it is interpretable
- it is reviewable or better
- its terminology is stable enough
- its role is clear
- its scope is explicit
- it has more than one-use value
- promotion would improve system clarity

These are minimum governance conditions.

---

## 7. Non-Promotion Conditions

An artifact should not be promoted when:

- it is still materially contradictory
- it is only useful inside one narrow local moment
- its status is still weak
- it has not been properly reviewed
- promotion is being proposed mainly for tidiness or convenience
- it would crowd the system layer with project-local material

This protects against promotion inflation.

---

## 8. Promotion of Project Notes into Reusable Knowledge

A project note may be promoted into `02_Knowledge/` only if:

- it has value beyond the original project
- it is no longer mainly project-local commentary
- its terminology and role are stable enough
- future projects would genuinely reuse it
- promotion reduces duplication

### Good Example
A project-origin file becomes a reusable cross-project model.

### Bad Example
A local project reflection note is moved into system knowledge just because it was written well.

---

## 9. Promotion of Stable Views into Frozen Baselines

A latest stable view may be promoted to frozen baseline only if:

- the bounded loop is complete
- review has already occurred
- the state is reusable enough to preserve
- future continuation should inherit from it
- further revision would likely create churn

Stable view and frozen baseline should not be collapsed automatically.

---

## 10. Promotion of Reviewable Objects

Reviewable objects may be promoted to conditionally stable or stable only when:

- the object is structurally complete enough
- the object has bounded usefulness
- review confirms its role
- known limitations are explicit
- the object can safely participate in future work

A reviewable object should not be promoted just because it exists in a frozen project.

---

## 11. Promotion of Repeated Local Structures into Templates

A repeated local pattern may become a template when:

- it recurs across more than one project or loop
- its fields are stable enough
- it reduces repeated manual design
- it remains simple enough to use operationally

### Good Candidates
- project template
- pilot template
- review note template
- stable view template

### Bad Candidates
- one-off highly specialized local files

---

## 12. Promotion of Repeated Local Instructions into Guides

A local instruction may become a system guide when:

- it is repeatedly used
- it is applicable beyond one project
- it clarifies system operation
- it reduces ambiguity across users or tools

This is how local practice becomes operational guidance.

---

## 13. Promotion of Historical Material

Historical material should usually not be promoted upward.  
It should usually move toward:
- frozen baseline if still actively reference-worthy
- archive if no longer active

Promotion and retention should not be confused.

---

## 14. Promotion and File Placement

Promotion often changes placement, but not always.

### Example 1
Project note → system knowledge  
This changes:
- status
- reuse scope
- often file placement

### Example 2
Stable view → frozen baseline  
This changes:
- governance meaning
- often file naming
- often storage location

### Example 3
Reviewable object → stable object  
This may change:
- metadata
- project role
but not always directory placement

Thus promotion is broader than movement.

---

## 15. Promotion Failure Modes

This guide protects against:

### Failure 1 — Promotion Inflation
Too many local notes become “system knowledge.”

### Failure 2 — Promotion by Tidiness
Artifacts are promoted just to clean folders.

### Failure 3 — Frozen Means Everything Is Good
A frozen project causes weak internal artifacts to be over-promoted.

### Failure 4 — Duplicate Promotion
Many overlapping artifacts are promoted without consolidation.

### Failure 5 — Historical Mis-Promotion
Old material is promoted when it should be archived.

---

## 16. Promotion Review Checklist

Before promotion, ask:

- [ ] Has this artifact been reviewed?
- [ ] Is the status strong enough?
- [ ] Is the scope beyond one local use?
- [ ] Is the naming stable enough?
- [ ] Will promotion help future projects?
- [ ] Will promotion reduce or increase confusion?
- [ ] Should this be promoted, frozen, or archived instead?

---

## 17. Human / GPT / Codex Roles in Promotion

### Human
- approves major promotions
- decides whether cross-project reuse is truly justified
- prevents promotion inflation

### GPT
- recommends whether promotion is warranted
- compares local artifact role vs system role
- detects premature promotion
- helps explain promotion rationale

### Codex
- performs file moves when approved
- updates links, MOCs, and indexes
- applies metadata changes
- should not promote major artifacts silently

---

## 18. Practical Promotion Sequence

A practical promotion sequence is:

```text id="0ld4p6"
Artifact Created
→ Reviewed
→ Status Clarified
→ Promotion Candidate Identified
→ Promotion Decision Made
→ File Placement / Metadata Updated
→ MOC / Index Updated