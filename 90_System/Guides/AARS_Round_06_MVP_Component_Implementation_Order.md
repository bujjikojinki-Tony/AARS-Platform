---
title: AARS_Round_06_MVP_Component_Implementation_Order
type: document
status: draft
project: AARS
tags:
  - aars
  - round-06
  - mvp
  - component
  - implementation-order
created: 2026-03-28
source: ChatGPT
---

# AARS_Round_06_MVP_Component_Implementation_Order

## 1. Purpose

This note defines the implementation order for the shared components of the AARS Runtime MVP.

It is intended to:
- establish the build sequence for reusable MVP components
- prevent component sprawl
- make shared dependencies explicit
- ensure the MVP component layer is aligned with governance value rather than visual decoration

This is a component implementation-order note.

---

## 2. Core Principle

The core principle is:

**implement the components that carry governance meaning first**

This means the first components should make visible:
- project identity
- current objective
- stable anchor
- health
- next-step logic

Do not prioritize purely decorative or low-value utility components first.

---

## 3. Component Build Order Overview

The recommended component implementation order is:

1. `ProjectIdentityCard`
2. `CurrentObjectivePanel`
3. `LatestStableViewCard`
4. `NextStepRecommendationCard`
5. `HealthSnapshotCard`
6. `ActionCommandBar`
7. `ProcessMapBar`
8. `MainResultPanel`

This is the best bounded order for Round_06.

---

## 4. Component 1 — ProjectIdentityCard

## Why First
This is the simplest high-value component and gives immediate runtime identity.

## Expected Inputs
- `ProjectSummary.projectId`
- `ProjectSummary.projectName`
- `ProjectSummary.projectType`
- `ProjectSummary.status`

## Success Condition
A user can immediately tell:
- what project is active
- what type of project it is
- what state it is in

---

## 5. Component 2 — CurrentObjectivePanel

## Why Second
After project identity, the next highest-value information is current intent.

## Expected Inputs
- `ProjectSummary.currentObjective`
- optionally `StepState.objective`

## Success Condition
A user can immediately tell:
- what the current work is trying to achieve
- what the immediate bounded focus is

---

## 6. Component 3 — LatestStableViewCard

## Why Third
Latest Stable View is one of the most distinctive AARS control components.

## Expected Inputs
- `StableViewSummary.summary`
- `StableViewSummary.maturity`
- `StableViewSummary.recommendedNextStep`

## Success Condition
A user can immediately tell:
- what the current safe anchor is
- how mature it is
- what continuation path it supports

---

## 7. Component 4 — NextStepRecommendationCard

## Why Fourth
Once stable anchor is visible, the next most important thing is bounded continuation logic.

## Expected Inputs
- `ProjectSummary.nextStep`
- `StableViewSummary.recommendedNextStep`
- `ReviewSummary.decision`

## Success Condition
A user can tell:
- what should happen next
- whether the recommendation is grounded in review / stable-view logic

---

## 8. Component 5 — HealthSnapshotCard

## Why Fifth
Health state is important, but should follow identity, objective, anchor, and next step.

## Expected Inputs
- `ReviewSummary.currentState`
- or later dedicated health-summary payload

## Success Condition
A user can tell:
- whether the current condition is healthy, cautionary, degraded, or blocked

---

## 9. Component 6 — ActionCommandBar

## Why Sixth
Once state, stable anchor, and next step are visible, the bounded action surface can be added.

## Expected Inputs
- derived from:
  - `ReviewSummary.decision`
  - `ClosureSummary.closureDecision`
  - current page context

## Success Condition
A user can see only bounded admissible actions rather than a generic toolbar.

---

## 10. Component 7 — ProcessMapBar

## Why Seventh
This is a very important component, but it depends on clearer step-state structures and should follow the simpler cards first.

## Expected Inputs
- `StepState[]`

## Success Condition
A user can tell:
- what step is current
- what is completed
- what is blocked
- what is upcoming

---

## 11. Component 8 — MainResultPanel

## Why Last in Core Set
This is useful, but it is often more page-specific and flexible than the other core governance cards.

## Expected Inputs
- `ReviewSummary.findings`
- current artifact summary
- page-level content summary

## Success Condition
It supports the page without becoming a generic dumping area.

---

## 12. Shared Styling Rule

All core MVP components should:
- be readable
- expose state clearly
- avoid excessive decoration
- keep labels and hierarchy simple
- remain reusable across multiple pages

Do not optimize visual polish before operational clarity.

---

## 13. Component Dependency Rule

### Rule 1
Each component must consume the shared MVP payloads rather than inventing local structures.

### Rule 2
A component should be used in at least two surfaces before being treated as stable shared UI.

### Rule 3
No component should hide or dilute review / stable-view / next-step meaning.

---

## 14. What Not to Build Early

Do not prioritize these before the core set exists:

- filters
- tabs complexity
- settings components
- portfolio analytics widgets
- archive browsers
- advanced badge systems
- decorative activity streams

These are later-round concerns.

---

## 15. Recommended First Code Sequence

A practical implementation order in code is:

```text
1. ProjectIdentityCard
2. CurrentObjectivePanel
3. LatestStableViewCard
4. NextStepRecommendationCard
5. HealthSnapshotCard
6. ActionCommandBar
7. ProcessMapBar
8. MainResultPanel