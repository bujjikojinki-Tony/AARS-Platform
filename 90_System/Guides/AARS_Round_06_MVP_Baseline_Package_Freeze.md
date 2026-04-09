---
title: AARS_Round_06_MVP_Baseline_Package_Freeze
type: package-freeze-note
status: draft
project: AARS
tags:
  - aars
  - round-06
  - mvp
  - baseline
  - package
  - freeze
created: 2026-04-08
source: Codex
---

# AARS_Round_06_MVP_Baseline_Package_Freeze

## 1. Purpose

This note freezes the accepted Round_06 first-set working package.

It defines what belongs to the current bounded working package for continuation, review, and hardening.

---

## 2. Accepted Surfaces

The accepted surfaces in the Round_06 first-set working package are:

- `src/pages/ProjectOverviewPage.tsx`
- `src/pages/CurrentStepPage.tsx`
- `src/pages/ReviewDecisionPage.tsx`
- `src/pages/ActiveProjectsSurface.tsx`

The package app entry remains:

- `src/App.tsx`

---

## 3. Authoritative Payload Contracts And Mocks

The authoritative payload contract file in the package is:

- `src/types/aars.ts`

The accepted mock payload files in the package are:

- `src/data/mock/projectOverviewMock.ts`
- `src/data/mock/currentStepMock.ts`
- `src/data/mock/reviewDecisionMock.ts`
- `src/data/mock/activeProjectsSurfaceMock.ts`

---

## 4. Cross-Surface Support

The accepted shared support files currently used across the package are:

- `src/components/aars/StatusBadge.tsx`
- `src/components/aars/LatestStableViewCard.tsx`

---

## 5. Build-Gate Files

The minimal root verification files in the package are:

- `package.json`
- `package-lock.json`
- `tsconfig.json`
- `src/types/react-shim.d.ts`

The current verification boundary is:

- `npm run typecheck`

---

## 6. Required Note Bundle

The minimum Round_06 note bundle required to understand and continue the accepted package is:

- `90_System/Guides/AARS_Round_06_MVP_Implementation_Latest_Stable_View.md`
- `90_System/Guides/AARS_Round_06_MVP_Implementation_Review_Note.md`
- `90_System/Guides/AARS_Round_06_MVP_Status_Note.md`
- `90_System/Guides/AARS_Round_06_MVP_Execution_Note.md`
- `90_System/Guides/AARS_Round_06_MVP_Cross_Surface_Semantics_Glossary.md`
- `90_System/Guides/AARS_Round_06_MVP_First_Set_Acceptance_Note.md`
- `90_System/Guides/AARS_Round_06_MVP_Accepted_Path_Inventory_Freeze.md`
- `90_System/Guides/AARS_Round_06_Active_Projects_Surface_Implementation_Review_Note.md`
- `90_System/Guides/AARS_Round_06_Page_01_Implementation_Review_Note.md`
- `90_System/Guides/AARS_Round_06_Page_02_Implementation_Review_Note.md`
- `90_System/Guides/AARS_Round_06_Page_03_Implementation_Review_Note.md`

---

## 7. Package Rule

For Round_06 continuation:

- this note defines the current working Round_06 first-set package
- files outside this package may still exist in the repo, but they are not package-authoritative
- compatibility wrappers, sandbox/reference paths, and legacy root noise remain outside the package unless explicitly promoted later
- package widening must be explicitly recorded before it is treated as accepted

---

## 8. Closing Note

The Round_06 first-set working package is now explicit enough to support bounded hardening, type-check verification, and continued review without widening the accepted baseline.
