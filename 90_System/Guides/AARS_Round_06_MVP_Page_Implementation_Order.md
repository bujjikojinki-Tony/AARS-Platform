---
title: AARS_Round_06_MVP_Page_Implementation_Order
type: document
status: draft
project: AARS
tags:
  - aars
  - round-06
  - mvp
  - implementation-order
created: 2026-03-28
source: ChatGPT
---

# AARS_Round_06_MVP_Page_Implementation_Order

## 1. Purpose

This note defines the implementation order for the AARS Runtime MVP pages and shared components.

It is intended to:
- establish the build sequence for the MVP
- prevent random page implementation order
- make dependencies between pages, payloads, and components explicit
- reduce overbuild and implementation drift

This is an MVP implementation-order note.

---

## 2. Core Principle

The core principle is:

**build the highest-governance-value surfaces first, and only then expand laterally**

This means:
- start with pages that expose project state, stable anchor, and next-step logic
- avoid building low-value or decorative surfaces first
- make shared components reusable before multiplying page count

---

## 3. Implementation Order Overview

The recommended order is:

1. Shared Types / Payload Layer  
2. Shared Components  
3. Project Overview Page  
4. Current Step Page  
5. Review / Decision Page  
6. Active Projects Summary Surface  
7. Closure / Freeze Preview Surface *(optional within Round_06)*  

This is the bounded MVP order.

---

## 4. Step 1 — Shared Types / Payload Layer

## Why First
Without a stable payload layer:
- pages will drift into inconsistent props
- shared components will be harder to reuse
- the MVP will fragment early

## Must Be Ready
- `ProjectSummary`
- `StepState`
- `ReviewSummary`
- `StableViewSummary`
- `ClosureSummary`
- `ActiveProjectsRegister`

## Output
- one stable `types.ts` or equivalent
- one mock data source layer

---

## 5. Step 2 — Shared Components

## Why Second
The MVP should establish the component spine before page proliferation.

## Components to Build First
- `ProcessMapBar`
- `ProjectIdentityCard`
- `CurrentObjectivePanel`
- `MainResultPanel`
- `HealthSnapshotCard`
- `LatestStableViewCard`
- `NextStepRecommendationCard`
- `ActionCommandBar`

## Output
- reusable UI building blocks
- page composition foundation

---

## 6. Step 3 — Project Overview Page

## Why Third
This is the highest-value orientation surface.

## Required Payloads
- `ProjectSummary`
- `StableViewSummary`
- `ReviewSummary`

## Required Components
- `ProjectIdentityCard`
- `CurrentObjectivePanel`
- `MainResultPanel`
- `HealthSnapshotCard`
- `LatestStableViewCard`
- `NextStepRecommendationCard`
- `ActionCommandBar`

## Success Condition
A user can tell:
- what project is active
- what it is trying to do
- what its stable anchor is
- what should happen next

---

## 7. Step 4 — Current Step Page

## Why Fourth
Once orientation exists, the next most useful surface is immediate control.

## Required Payloads
- `ProjectSummary`
- `StepState`
- `ReviewSummary`

## Required Components
- `ProcessMapBar`
- `CurrentObjectivePanel`
- `MainResultPanel`
- `HealthSnapshotCard`
- `NextStepRecommendationCard`
- `ActionCommandBar`

## Success Condition
A user can tell:
- what step is current
- what is completed
- what is open
- what is blocked
- what should happen next

---

## 8. Step 5 — Review / Decision Page

## Why Fifth
This page completes the core governance MVP.

## Required Payloads
- `ReviewSummary`
- `StableViewSummary`
- `ProjectSummary`

## Required Components
- `ProjectIdentityCard`
- `MainResultPanel`
- `HealthSnapshotCard`
- `LatestStableViewCard`
- `NextStepRecommendationCard`
- `ActionCommandBar`

## Success Condition
A user can tell:
- what the current decision is
- why it was made
- whether to continue, freeze, recover, or close

---

## 9. Step 6 — Active Projects Summary Surface

## Why Sixth
After the three core pages are stable, portfolio visibility can be added.

## Required Payloads
- `ActiveProjectsRegister`
- lightweight `ProjectSummary` subset

## Required Components
- project summary cards or compact list
- priority / status indicators

## Success Condition
A user can tell:
- what projects are active
- which one is highest priority
- what should not be touched

---

## 10. Step 7 — Closure / Freeze Preview Surface (Optional in Round_06)

## Why Last
Closure/freeze surfaces are valuable, but lower priority than orientation, control, and review.

## Required Payloads
- `ClosureSummary`
- `StableViewSummary`
- `ReviewSummary`

## Success Condition
A user can tell:
- whether closure is near
- whether freeze is recommended
- what remains incomplete but tolerable

This step is optional within Round_06 if time or scope must remain tight.

---

## 11. Dependency Rules

### Rule 1
No page should bypass the shared payload model.

### Rule 2
No page should introduce a page-specific data logic that duplicates existing payload meaning.

### Rule 3
Shared components should be used across at least two surfaces before new component families are added.

### Rule 4
Page implementation should remain tied to real AARS artifacts and mock data, not generic dashboard placeholders.

---

## 12. Recommended First Build Order in Code

A clean implementation order is:

```text
1. /src/types/
2. /src/data/mock/
3. /src/components/shared/
4. /src/pages/ProjectOverviewPage
5. /src/pages/CurrentStepPage
6. /src/pages/ReviewDecisionPage
7. /src/pages/ActiveProjectsPage or panel
8. /src/pages/ClosurePreviewPage (optional)