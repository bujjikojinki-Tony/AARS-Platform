---
title: AARS_Project_Review_Queue
type: moc
status: draft
project: AARS
tags:
  - aars
  - moc
  - review-queue
  - system
created: 2026-03-28
source: ChatGPT
---

# AARS_Project_Review_Queue

## 1. Purpose

This page is the review-queue coordination hub for AARS.

It is intended to:
- show which projects currently require review
- clarify what each pending review is about
- distinguish review targets from general project activity
- support bounded governance decisions across multiple projects
- make the review workload visible at system level

This page is a coordination page, not a review model.

---

## 2. Use Rule

Use this page when:
- checking which project needs review next
- identifying what kind of review is pending
- preparing freeze / continue / recover decisions
- coordinating system-level attention across active projects

Do not use this page as a substitute for local review notes themselves.

---

## 3. Current Review Queue

## Queue Item 1 — Pilot_001_CDA Second-Pass Review
**Project:** [[CDA_Project_Home]]  
**Domain:** CDA  
**Review Type:** second-pass bounded pilot review  
**Current State:** ready for review  
**Why It Is In Queue:** the first bounded loop is complete and the project is in reviewable / conditionally stable state, so a second-pass review is needed before freeze or second-case branching.

### Review Focus
- glossary baseline sufficiency  
- taxonomy baseline sufficiency  
- risk v2 strengthening adequacy  
- control-priority v2 strengthening adequacy  
- latest stable view formalization  
- freeze-or-extend decision readiness  

### Expected Review Output
One or more of:
- `Pilot_001_CDA_Final_Review.md`
- `Pilot_001_CDA_Latest_Stable_View.md`
- `Pilot_001_CDA_Second_Pass_Acceptance_Note.md`

---

## 4. Review Queue Summary Table

| Queue Order | Project | Review Type | Current State | Expected Decision |
|---|---|---|---|---|
| 1 | [[CDA_Project_Home]] | second-pass pilot review | ready for review | continue / freeze / second-case decision |

---

## 5. Review Queue Logic

A project should appear in the review queue when:
- it has completed a meaningful bounded loop
- continuation depends on explicit judgment
- freeze is being considered
- recovery is being considered
- baseline upgrade or promotion is being considered

This keeps review visible instead of implicit.

---

## 6. Difference Between Status Board and Review Queue

### Status Board
Shows the current condition of projects.

### Review Queue
Shows which projects currently need governance attention.

### Priority Board
Shows which projects should receive effort first.

These three pages should remain separate.

---

## 7. Typical Review Queue States

Review queue items may be marked as:

- queued
- ready for review
- under review
- waiting for strengthening
- decision ready
- closed

These are queue states, not project maturity states.

---

## 8. Recommended Future Expansion

When more projects exist, add:
- owner or review responsibility
- last review date
- required inputs
- current blocker
- target decision deadline
- linked review note

This will make the queue more operational without needing a full platform dashboard yet.

---

## 9. Relationship to Other Pages

### Navigation
- [[AARS_System_Home]]

### Active Projects
- [[AARS_Active_Projects_Home]]

### Priority
- [[AARS_Project_Priority_Board]]

### Status
- [[AARS_Project_Status_Board]]

### Frozen
- [[AARS_Frozen_Projects_Home]]

### Archived
- [[AARS_Archived_Projects_Home]]

---

## 10. Update Rule

Update this page whenever:
- a project becomes ready for review
- a review starts
- a review requires strengthening before closure
- a review produces freeze / continue / recover outcomes
- a queue item is closed

---

## 11. Closing Note

This page should remain the lightweight review coordination board for AARS until review traffic becomes large enough to justify a fuller governance dashboard.