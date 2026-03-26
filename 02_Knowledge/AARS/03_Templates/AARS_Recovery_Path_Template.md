---
title: AARS Recovery Path Template
type: template
domain: AARS
status: reusable
layer: operational
tags:
  - aars
  - template
  - recovery
  - fallback
aliases:
  - AARS_Recovery_Path_Template
  - Recovery Path Template
source: AARS reusable template
related:
  - "[[AARS_Health_Snapshot_Template]]"
  - "[[AARS_Risk_Object_Schema]]"
  - "[[AARS_Dependency_Object_Schema]]"
  - "[[AARS_Invocation_Record_Template]]"
---
# AARS_Recovery_Path_Template

## 1. Purpose
Define the standard format used to represent recovery paths in AARS vNext, including trigger state, affected scope, recovery objective, required actions, dependency conditions, risk constraints, stable anchor usage, success criteria, and post-recovery review.

## 2. Recovery Path Sections
1. Path Identity
2. Trigger State
3. Recovery Objective
4. Affected Scope
5. Stable Anchor and Continuation Basis
6. Recovery Action Sequence
7. Dependency and Risk Constraints
8. Success and Exit Criteria
9. Post-Recovery Review

## 3. Path Identity Section

### Required Fields
- Recovery Path ID
- Recovery Path Title
- Status
- Priority

## 4. Trigger State Section

### Required Fields
- Trigger Type
- Trigger Description
- Trigger Source
- Trigger Severity
- Trigger Confirmation Basis

## 5. Recovery Objective Section

### Required Fields
- Recovery Objective
- Intended Continuation Scope
- Recovery Strategy Type
- Target Restored State

## 6. Affected Scope Section

### Required Fields
- Affected Object Type
- Affected Object Name or ID
- Affected Thread or Stage
- Scope Impact Summary

## 7. Stable Anchor and Continuation Basis Section

### Required Fields
- Latest Stable View Reference
- Stable Anchor Description
- Why This Anchor Is Safe
- Continuation Limitation Note

## 8. Recovery Action Sequence Section

### Required Fields
- Action Sequence
- Action Order Rationale
- Action Owner Context
- Revalidation Requirement

## 9. Dependency and Risk Constraints Section

### Required Fields
- Dependency Constraints
- Risk Constraints
- Waiver Conditions
- Blocking Conditions

## 10. Success and Exit Criteria Section

### Required Fields
- Success Criteria
- Exit State
- Residual Risk State After Recovery
- Post-Recovery Health Expectation

## 11. Post-Recovery Review Section

### Required Fields
- Required Review Action
- Required Log Updates
- Required Health Snapshot Update
- Follow-up Recommendation

## 12. Vocabulary

### Status
- Proposed
- Active
- In Progress
- Completed
- Blocked
- Abandoned with Record

### Priority
- Low
- Medium
- High
- Critical

### Recovery Strategy Type
- Refresh
- Reroute
- Rollback
- Replace
- Split Thread
- Downgrade Certainty
- Conditional Continuation

### Exit State
- Restored Stable
- Conditionally Stable
- Reviewable
- Unresolved

## 13. Template Use Rules
1. recovery must be triggered by a visible problem state
2. recovery must name a stable anchor where possible
3. recovery must be sequenced
4. revalidation is part of recovery
5. recovery scope must stay bounded