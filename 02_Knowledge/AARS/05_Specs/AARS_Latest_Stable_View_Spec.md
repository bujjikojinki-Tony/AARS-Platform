---
title: AARS Latest Stable View Spec
type: spec
status: reviewable
project: AARS
tags:
  - aars
  - spec
  - stable-view
  - recovery
  - core-knowledge
created: 2026-03-26
source: migrated from 00_Inbox/ChatGPT_Imports/AARS_Latest_Stable_View_Spec.md
domain: AARS
layer: specification
aliases:
  - AARS_Latest_Stable_View_Spec
related:
  - "[[AARS_Knowledge_Index]]"
  - "[[AARS_vNext_Terminology_Glossary]]"
  - "[[AARS_vNext_Master_Spec]]"
  - "[[AARS_Health_Snapshot_Template]]"
  - "[[AARS_Dependency_Object_Schema]]"
  - "[[AARS_Risk_Object_Schema]]"
  - "[[AARS_Recovery_Path_Template]]"
---

# AARS Latest Stable View Spec

## 1. Purpose
Define how [[AARS_vNext_Terminology_Glossary#AARS vNext|AARS vNext]] identifies, represents, selects, and uses the [[AARS_vNext_Terminology_Glossary#Latest Stable View|latest stable continuation base]] across artifacts, threads, capabilities, and project states for [[AARS_vNext_Terminology_Glossary#Recovery|recovery]], resumption, rollback, and controlled progression.

## 2. View Scopes

### Core Scopes
- Artifact Stable View
- Thread Stable View
- Capability Stable View
- Project Stable View
- Release Stable View

## 3. Stability Model

### Stability States
- active draft
- reviewable
- stable
- conditionally stable
- stale-sensitive stable
- superseded
- unstable
- blocked

### Stability Priority Rule
When selecting a [[AARS_vNext_Terminology_Glossary#Latest Stable View|Latest Stable View]], stable and conditionally stable states should be preferred over mere recency.

## 4. Stable View Object Schema

### Required Fields
- Stable View ID
- Stable View Scope
- Target Object Name or ID
- Selected Stable Version or Marker
- Stability State
- Stability Basis
- Safe Continuation Use
- Excluded Newer Alternatives Note

## 5. Selection Rules
1. Stability Before Recency
2. Scope Compatibility
3. Risk Compatibility
4. Dependency Compatibility
5. Acceptance Compatibility
6. Explicit Exclusion

## 6. Selection Procedure
1. Define Scope
2. Define Intended Use
3. Identify Candidate States
4. Filter by Blocking Instability
5. Compare Stability Basis
6. Select Preferred Stable Anchor
7. Record Excluded Newer Alternatives

## 7. Integration Rules

### Health Integration
- every [[AARS_vNext_Terminology_Glossary#Health Snapshot|health snapshot]] should identify at least one [[AARS_vNext_Terminology_Glossary#Latest Stable View|latest stable view]] where relevant
- absence of any [[AARS_vNext_Terminology_Glossary#Stable Anchor|stable anchor]] should be treated as a serious ops signal

### Risk Integration
- critical unresolved [[AARS_vNext_Terminology_Glossary#Risk|risk]] usually disqualifies a candidate from stable selection
- residual risk must be reflected in limitations

### Dependency Integration
- unsatisfied hard [[AARS_vNext_Terminology_Glossary#Dependency|dependencies]] disqualify stable selection for dependent use cases

## 8. Minimal Acceptance Criteria
1. support artifact, thread, capability, project, and release stable views
2. prioritize stability over naive recency
3. integrate with health, risk, dependency, and rollback logic
4. explain why newer alternatives were excluded
5. support resume and recovery workflows with explicit anchors
