---
title: AARS Health Snapshot Template
type: template
domain: AARS
status: reusable
layer: operational
tags:
  - aars
  - template
  - health
  - snapshot
aliases:
  - AARS_Health_Snapshot_Template
  - Health Snapshot Template
source: AARS reusable template
related:
  - "[[AARS_Risk_Object_Schema]]"
  - "[[AARS_Dependency_Object_Schema]]"
  - "[[AARS_Recovery_Path_Template]]"
  - "[[AARS_Invocation_Record_Template]]"
---
# AARS_Health_Snapshot_Template

## 1. Purpose
Define the standard format used to produce health snapshots in AARS vNext, covering project health, thread state, artifact stability, capability readiness, gate performance, blocker visibility, risk load, and recovery guidance.

## 2. Snapshot Sections
1. Snapshot Identity
2. Project Health Summary
3. Thread Health Summary
4. Artifact and Capability Stability
5. Gate and Risk Summary
6. Blocker Summary
7. Latest Stable View
8. Recovery Guidance

## 3. Snapshot Identity Section

### Required Fields
- Snapshot ID
- Snapshot Time or Sequence Marker
- Project or Task Name
- Active Goal Type
- Active Track
- Current Stage Focus
- Overall Health State

## 4. Project Health Summary

### Required Fields
- Overall Health State
- Health Rationale
- Active Progress State
- Health Trend

## 5. Thread Health Summary

### Required Fields
- Active Thread Count
- Stable Thread Count
- Watch-State Thread Count
- Blocked Thread Count
- Stale Thread Count
- Thread Summary Notes

## 6. Artifact and Capability Stability

### Required Fields
- Stable Artifact Count
- Reviewable Artifact Count
- Stale-Sensitive Artifact Count
- Deprecated or Superseded Artifact Count
- Stable Capability Count
- Unstable or Blocked Capability Count
- Stability Summary Notes

## 7. Gate and Risk Summary

### Required Fields
- Gate Pass Ratio
- Conditional Pass Count
- Fail Count
- Rollback Count
- Active Risk Count
- Critical Risk Count
- Gate and Risk Notes

## 8. Blocker Summary

### Required Fields
- Active Blocker Count
- Major Blocker Count
- Critical Blocker Count
- Blocker Summary Notes

## 9. Latest Stable View

### Required Fields
- Latest Stable Artifact
- Stable Artifact Version or Marker
- Stable Continuation Note

## 10. Recovery Guidance

### Required Fields
- Recovery State
- Recommended Next Action
- Action Priority
- Recovery Rationale

## 11. Vocabulary

### Overall Health State
- Healthy
- Watch
- Constrained
- Blocked
- Degraded
- Recovering

### Health Trend
- Improving
- Stable
- Worsening
- Mixed

### Recovery State
- No Recovery Needed
- Recovery Path Identified
- Recovery In Progress
- Recovery Blocked
- Recovery Unavailable