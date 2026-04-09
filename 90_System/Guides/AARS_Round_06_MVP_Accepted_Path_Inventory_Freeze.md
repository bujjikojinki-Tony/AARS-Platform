---
title: AARS_Round_06_MVP_Accepted_Path_Inventory_Freeze
type: inventory-freeze-note
status: draft
project: AARS
tags:
  - aars
  - round-06
  - mvp
  - inventory
  - freeze
created: 2026-04-08
source: Codex
---

# AARS_Round_06_MVP_Accepted_Path_Inventory_Freeze

## 1. Purpose

This note freezes the accepted-path inventory for the Round_06 first-set MVP baseline.

It exists to keep the authoritative baseline boundary explicit without deleting broad file groups or reopening ownership refactors.

---

## 2. Accepted Baseline Path

The accepted Round_06 first-set baseline path is:

### App Entry

- `src/App.tsx`

### Accepted Surfaces

- `src/pages/ProjectOverviewPage.tsx`
- `src/pages/CurrentStepPage.tsx`
- `src/pages/ReviewDecisionPage.tsx`
- `src/pages/ActiveProjectsSurface.tsx`

### Authoritative Payload Contracts

- `src/types/aars.ts`

### Accepted Baseline Mocks

- `src/data/mock/projectOverviewMock.ts`
- `src/data/mock/currentStepMock.ts`
- `src/data/mock/reviewDecisionMock.ts`
- `src/data/mock/activeProjectsSurfaceMock.ts`

### Accepted Shared Components

- `src/components/aars/StatusBadge.tsx`
- `src/components/aars/LatestStableViewCard.tsx`

### Minimal Build Gate

- `package.json`
- `package-lock.json`
- `tsconfig.json`
- `src/types/react-shim.d.ts`

### Accepted Note Bundle

- `90_System/Guides/AARS_Round_06_MVP_Implementation_Latest_Stable_View.md`
- `90_System/Guides/AARS_Round_06_MVP_Implementation_Review_Note.md`
- `90_System/Guides/AARS_Round_06_MVP_Status_Note.md`
- `90_System/Guides/AARS_Round_06_MVP_Execution_Note.md`
- `90_System/Guides/AARS_Round_06_MVP_Cross_Surface_Semantics_Glossary.md`
- `90_System/Guides/AARS_Round_06_MVP_First_Set_Acceptance_Note.md`
- `90_System/Guides/AARS_Round_06_Active_Projects_Surface_Implementation_Review_Note.md`
- `90_System/Guides/AARS_Round_06_Page_01_Implementation_Review_Note.md`
- `90_System/Guides/AARS_Round_06_Page_02_Implementation_Review_Note.md`
- `90_System/Guides/AARS_Round_06_Page_03_Implementation_Review_Note.md`

---

## 3. Compatibility Wrappers

The following files remain in the repo but are not baseline-authoritative:

- `src/pages/ActiveProjectsPage.tsx`

These should be treated as compatibility-facing only.

---

## 4. Sandbox / Reference Residue

The following paths remain present as sandbox/reference material and are explicitly outside the accepted baseline path:

- `runtime-mvp/page-01/`
- `runtime-mvp/page-02/`
- `runtime-mvp/page-03/`
- `runtime-mvp/active-projects/`

These paths may remain useful as historical or sandbox context, but they are not the Round_06 authoritative implementation lane.

---

## 5. Legacy Root Noise

The following root files remain present but should not be treated as baseline-authoritative in the current pass:

### Older Root Mock Noise

- `src/data/mock/activeProjectsMock.ts`

### Older Root Component / Export Noise

- `src/components/aars/ActionCommandBar.tsx`
- `src/components/aars/ActiveProjectCard.tsx`
- `src/components/aars/ActiveProjectRow.tsx`
- `src/components/aars/BlockerPanel.tsx`
- `src/components/aars/DecisionBanner.tsx`
- `src/components/aars/HealthSnapshotCard.tsx`
- `src/components/aars/MainResultPanel.tsx`
- `src/components/aars/NextStepRecommendationCard.tsx`
- `src/components/aars/NonActiveProjectsPanel.tsx`
- `src/components/aars/PortfolioSummaryBar.tsx`
- `src/components/aars/PortfolioSummaryHeader.tsx`
- `src/components/aars/PriorityBadge.tsx`
- `src/components/aars/ProcessMapBar.tsx`
- `src/components/aars/ProjectIdentityCard.tsx`
- `src/components/aars/ProjectStateBadge.tsx`
- `src/components/aars/RationalePanel.tsx`
- `src/components/aars/ReviewIdentityCard.tsx`
- `src/components/aars/StepIdentityCard.tsx`
- `src/components/aars/WeaknessListPanel.tsx`

These files may still be useful later, but they are not part of the accepted first-set baseline package unless they are explicitly promoted into it in a later bounded review.

---

## 6. Boundary Rule

For Round_06 first-set baseline continuation:

- accepted baseline work should continue only in the accepted baseline path
- compatibility wrappers remain non-authoritative
- sandbox/reference paths remain non-authoritative
- legacy root noise should be disciplined, not broadly deleted in this pass
- any future widening of the accepted baseline path should be explicitly recorded before it is treated as authoritative

---

## 7. Closing Note

The accepted baseline boundary is now explicit enough to support bounded hardening, review, and minimal verification work without broad cleanup or repo redesign.
