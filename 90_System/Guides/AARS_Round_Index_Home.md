
---
title: AARS_Round_Index_Home
type: document
status: draft
project: AARS
tags:
  - aars
  - round
  - index
  - moc
created: 2026-03-28
source: ChatGPT
---

# AARS_Round_Index_Home

## 1. Purpose

This page is the round-index navigation surface for AARS.

It is intended to:
- show major bounded system rounds
- distinguish active, closed, frozen, and archived rounds
- connect rounds to closure notes, baselines, and change logs
- provide a readable round lineage over time

This page functions as the round-history MOC of AARS.

---

## 2. Current Round Register

| Round ID | Round Name | Scope | Current State | Closure Note | Baseline / Release Note | Notes |
|---|---|---|---|---|---|---|
| Round_01 | System Definition + Production Readiness Phase 1 | system layer | closure allowed / freeze recommended | [[AARS_Round_01_Closure_Note]] | [[AARS_System_Baseline_Release_Note]] | first major AARS system-building round |
| Round_01_Final_Consolidation | Round_01 closure pass | system closure layer | complete-in-practice | [[AARS_Round_01_Closure_Note]] | [[AARS_Round_01_Freeze_Decision_Note]] | treated as the final consolidation pass of Round_01 |

---

## 3. Current Active Round

### Current Active / Most Recent Completed Round
- **Round_01**
- Scope: system-definition + production-readiness Phase 1
- State: closure allowed / freeze recommended
- Stable anchor: [[AARS_Round_01_End_of_Round_Review_Note]]

### Main Related Artifacts
- [[AARS_Round_01_End_of_Round_Review_Note]]
- [[AARS_Round_01_Closure_Note]]
- [[AARS_Round_01_Change_Log]]
- [[AARS_Round_01_Freeze_Decision_Note]]

---

## 4. Closed / Frozen Rounds

| Round ID | Closure State | Frozen? | Closure Note | Freeze Decision | Notes |
|---|---|---|---|---|---|
| Round_01 | closure allowed | freeze recommended | [[AARS_Round_01_Closure_Note]] | [[AARS_Round_01_Freeze_Decision_Note]] | first major coherent system baseline round |

---

## 5. Archived Rounds

| Round ID | Archive State | Archive Decision Note | Superseded By | Historical Value |
|---|---|---|---|---|
| _TBD_ |  |  |  |  |

---

## 6. Related Round Artifacts

### Closure
- [[AARS_Round_Closure_Note_Template]]
- [[AARS_Round_01_Closure_Note]]

### Change Logs
- [[AARS_Release_Change_Log_Template]]
- [[AARS_Round_01_Change_Log]]

### Freeze / Archive Decisions
- [[AARS_System_Freeze_Decision_Note_Template]]
- [[AARS_System_Archive_Decision_Note_Template]]
- [[AARS_Round_01_Freeze_Decision_Note]]

### Packaging
- [[AARS_End_of_Round_Packaging_Guide]]

---

## 7. Relationship to Other Homes

### System Home
- [[AARS_System_Home]]

### Active Projects Home
- [[AARS_Active_Projects_Home]]

### Baseline History Home
- [[90_System/MOCs/AARS_Baseline_History_Home]]

This page is about round lineage, not full portfolio status.

---

## 8. Maintenance Rule

Update this page whenever:
- a new major round starts
- a round closes
- a round freezes
- a round is archived
- a new baseline release note becomes the active system reference

---

## 9. Suggested Placement

```text
90_System/MOCs/AARS_Round_Index_Home.md