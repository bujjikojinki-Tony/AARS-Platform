---
title: AARS Dependency Object Schema
type: schema
domain: AARS
status: stable
layer: knowledge
tags:
  - aars
  - schema
  - dependency
  - object
aliases:
  - AARS_Dependency_Object_Schema
  - Dependency Schema
source: AARS vNext knowledge asset
related:
  - "[[AARS_Terminology_Glossary]]"
  - "[[AARS_Capability_Object_Schema]]"
  - "[[AARS_Risk_Object_Schema]]"
  - "[[AARS_Invocation_Record_Template]]"
  - "[[AARS_Health_Snapshot_Template]]"
---
# AARS_Dependency_Object_Schema

## 1. Purpose
Define the formal object schema used to represent dependencies in AARS vNext across kernels, capabilities, artifacts, stages, threads, and recovery pathways.

## 2. Dependency Object Sections
1. Identity Section
2. Relation Section
3. Requirement Section
4. Current State Section
5. Control Section
6. Resolution Section
7. Continuity Section
8. Governance Section

## 3. Identity Section

### Required Fields
- Dependency ID
- Dependency Title
- Dependency Domain
- Dependency Type
- Status

## 4. Relation Section

### Required Fields
- Dependent Object Type
- Dependent Object Name or ID
- Prerequisite Object Type
- Prerequisite Object Name or ID
- Relation Summary

## 5. Requirement Section

### Required Fields
- Required State
- Requirement Basis
- Criticality Level
- Intended Use Scope

## 6. Current State Section

### Required Fields
- Current State
- State Basis
- State Confidence
- State Impact Summary

## 7. Control Section

### Required Fields
- Control Effect
- Control Priority
- Progression Impact
- Invocation Impact

## 8. Resolution Section

### Required Fields
- Resolution State
- Recommended Resolution Path
- Resolution Owner Context
- Residual Limitation State

## 9. Continuity Section

### Required Fields
- Continuity Relevance
- Latest Stable View Relevance
- Recovery Relevance
- Migration Relevance

## 10. Governance Section

### Required Fields
- Logging Requirement
- Review Requirement
- Acceptance Gate Impact
- Disclosure Requirement

## 11. Vocabulary

### Dependency Domain
- Kernel
- Capability
- Artifact
- Stage
- Thread
- Recovery

### Dependency Type
- Hard Dependency
- Soft Dependency
- Contextual Dependency
- Version Dependency
- Supervision Dependency
- Freshness Dependency
- Governance Dependency
- Merge Dependency
- Packaging Dependency
- Rollback Dependency

### Dependency State
- satisfied
- partially satisfied
- unsatisfied
- unstable
- stale
- blocked by conflict
- waived with record
- not applicable

### Control Effect
- continue
- continue with warning
- continue conditionally
- reroute to validation
- reroute to supervision
- defer stage progression
- block invocation
- block packaging
- block acceptance
- waive with record