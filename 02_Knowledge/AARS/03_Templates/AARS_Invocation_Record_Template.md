---
title: AARS Invocation Record Template
type: template
domain: AARS
status: reusable
layer: operational
tags:
  - aars
  - template
  - invocation
  - record
aliases:
  - AARS_Invocation_Record_Template
  - Invocation Record Template
source: AARS reusable template
related:
  - "[[AARS_Capability_Object_Schema]]"
  - "[[AARS_Risk_Object_Schema]]"
  - "[[AARS_Dependency_Object_Schema]]"
  - "[[AARS_Health_Snapshot_Template]]"
---
# AARS_Invocation_Record_Template

## 1. Purpose
Define the standard record format used to log capability invocation events in AARS vNext, including invocation context, compatibility basis, dependencies, outputs, limitations, supervision notes, and outcome status.

## 2. Invocation Record Sections
1. Record Identity
2. Invocation Context
3. Compatibility Basis
4. Dependency State
5. Execution Outcome
6. Governance and Risk Notes
7. Version and Continuity
8. Follow-up Actions

## 3. Record Identity Section

### Required Fields
- Invocation Record ID
- Capability ID
- Capability Name
- Capability Version
- Invocation Time or Sequence Marker
- Invocation Status

## 4. Invocation Context Section

### Required Fields
- Active Goal Type
- Active Track
- Active Stage
- Trigger Reason
- Input Context Summary
- Target Artifact or Entity

## 5. Compatibility Basis Section

### Required Fields
- Compatibility Match Level
- Goal Compatibility Basis
- Stage Compatibility Basis
- Input Compatibility Basis
- Invocation Conditions Check

## 6. Dependency State Section

### Required Fields
- Hard Dependency Status
- Soft Dependency Status
- Dependency Notes

## 7. Execution Outcome Section

### Required Fields
- Output Summary
- Output Type
- Completion Condition Result
- Outcome Status
- Outcome Quality Note

## 8. Governance and Risk Notes Section

### Required Fields
- Risk Note
- Validation Note
- Supervision Note
- Certainty Constraint Applied

## 9. Version and Continuity Section

### Required Fields
- Source Capability Version
- Artifact Version Impact
- Continuity Relevance

## 10. Follow-up Actions Section

### Required Fields
- Recommended Next Action
- Follow-up Priority
- Follow-up Owner Context

## 11. Standard Status Vocabularies

### Invocation Status
- Completed
- Partially Completed
- Blocked
- Failed Validation
- Skipped
- Replaced

### Compatibility Match
- Strong
- Compatible
- Conditional
- Weak
- Blocked

### Dependency Status
- Satisfied
- Partially Satisfied
- Unsatisfied
- Unstable
- Not Applicable

### Follow-up Priority
- Low
- Medium
- High
- Critical