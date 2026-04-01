---
title: AARS_Active_Projects_Home
type: moc
status: draft
project: AARS
tags:
  - aars
  - moc
  - active-projects
  - system
created: 2026-03-28
source: ChatGPT
---

---

# AARS_Active_Projects_Home

## 1. Purpose

This page is the active-projects control surface for AARS.

It is intended to:
- show which projects are currently active
- distinguish active, frozen, paused, archived, and recovering projects
- support multi-project governance
- provide a single project portfolio entry point
- reduce confusion between current execution and historical baselines

This page should function as the project portfolio MOC of AARS.

---

## 2. Project Portfolio States

AARS projects should be understood through the following portfolio states:

### Active
Project is currently being advanced.

### Reviewable
Project has meaningful outputs and needs structured judgment.

### Conditionally Stable
Project can continue, but with caution.

### Frozen
Project baseline is preserved as a reusable reference state.

### Paused
Project is temporarily inactive but not archived.

### Recovering
Project requires corrective action before normal continuation.

### Archived
Project is no longer active, but retained historically.

---

## 3. Current Portfolio Summary

### Active Projects
- [[CDA_Project_Home]]

### Reviewable / Conditionally Stable Projects
- [[Pilot_001_CDA_Review_Note]]

### Frozen Projects
- [[Pilot_001_CDA_Frozen_Baseline]]

### Archived Projects
- _None formally indexed yet_

### Paused Projects
- _None formally indexed yet_

### Recovering Projects
- _None formally indexed yet_

---

## 4. Active Project Register

Use the following section to track currently active projects.

| Project ID | Project Name | Domain | Current Stage | Current State | Latest Stable View | Next Step |
|---|---|---|---|---|---|---|
| Pilot_001_CDA | CDA Pilot | Critical Digital Assets | Review / Freeze Transition | Conditionally Stable | First bounded pilot baseline | Prepare for next bounded extension or system reuse |

---

## 5. Frozen Project Register

Use the following section to track frozen baselines.

| Project ID | Frozen Asset | Domain | Freeze Scope | Status | Notes |
|---|---|---|---|---|---|
| Pilot_001_CDA | [[Pilot_001_CDA_Frozen_Baseline]] | CDA | pilot baseline | Frozen | First bounded reference pilot |

---

## 6. Paused / Recovering Register

Use this section when projects are not active but are not archived either.

| Project ID | State | Reason | Stable Anchor | Re-entry Condition |
|---|---|---|---|---|
| _TBD_ |  |  |  |  |

---

## 7. Archived Project Register

Use this section for projects no longer active.

| Project ID | Archive Asset | Domain | Reason Archived | Historical Value |
|---|---|---|---|---|
| _TBD_ |  |  |  |  |

---

## 8. Active Project Entry Links

### CDA Domain
- [[Pilot_001_CDA_Project_Charter]]
- [[CDA_Project_Home]]
- [[CDA_Glossary_Baseline]]
- [[CDA_Taxonomy_Baseline]]
- [[CDA_Concept_Map]]
- [[CDA_Layer_Validation_Note]]
- [[CDA_Layered_Architecture]]
- [[CDA_3_Paper_Roadmap]]
- [[Pilot_001_CDA_Review_Note]]
- [[Pilot_001_CDA_Frozen_Baseline]]

---

## 9. Cross-Project Governance Questions

This page should help answer:

1. Which projects are currently active?
2. Which projects are frozen and should not be casually reopened?
3. Which projects are still only reviewable?
4. Which projects have a valid stable anchor?
5. Which project should receive next implementation effort?
6. Which project-origin assets may deserve promotion into reusable AARS knowledge?

---

## 10. Priority Guidance

When more than one project becomes active, priority should consider:

- strategic importance
- stage readiness
- continuity risk
- freeze readiness
- system refinement value
- domain validation value

Priority should be explicit, not assumed.

---

## 11. Relationship to Other Pages

### System-Level Entry
- [[AARS_System_Home]]

### System Governance
- [[AARS_Multi_Project_Governance_Model]]
- [[AARS_Project_Model]]
- [[AARS_Stage_Model]]
- [[AARS_Next_Step_Decision_Model]]

### Templates
- [[AARS_Project_Template]]
- [[AARS_Pilot_Template]]

This page is the active portfolio view, not the full governance logic itself.

---

## 12. Maintenance Rule

Update this page whenever:
- a new project becomes active
- a project freezes
- a project moves to archive
- a project enters recovery
- project priority materially changes

If this page is stale, multi-project governance quality weakens.

---

## 13. Recommended Next Step

The next useful file after this one is:

`02_Knowledge/AARS_Schema_Layer_Overview.md`

because the system now has:
- models
- guides
- templates
- active-project visibility

and the next missing production-readiness layer is the schema overview.

---

## 14. Closing Note

This page should remain the main active-project portfolio surface for AARS until a more advanced runtime dashboard or UI implementation exists.