---
title: AARS Capability Object Schema
type: schema
status: stable
project: AARS
tags:
  - aars
  - schema
  - capability
  - object
created: 2026-03-26
source: AARS vNext knowledge asset
domain: AARS
layer: knowledge
aliases:
  - AARS_Capability_Object_Schema
  - Capability Schema
related:
  - "[[AARS_vNext_Terminology_Glossary]]"
  - "[[AARS_Risk_Object_Schema]]"
  - "[[AARS_Dependency_Object_Schema]]"
  - "[[AARS_vNext_Executive_Summary]]"
---
# AARS Capability Object Schema

## 1. Purpose
Define the formal [[AARS_vNext_Terminology_Glossary#Capability Object|Capability Object]] schema used to register, version, match, invoke, supervise, and migrate [[AARS_vNext_Terminology_Glossary#Capability|capability]] units within [[AARS_vNext_Terminology_Glossary#AARS vNext|AARS vNext]].

## 2. Schema Sections
1. Identity Section
2. Function Section
3. Compatibility Section
4. Invocation Section
5. Dependency Section
6. Governance Section
7. Version Section
8. Operational Section
9. Migration Section

## 3. Identity Section

### Required Fields
- Capability ID
- Capability Name
- Capability Class
- Functional Group
- Status

## 4. Function Section

### Required Fields
- Purpose
- Core Operation
- Typical Use Case
- Output Intention

## 5. Compatibility Section

### Required Fields
- Compatible Goal Types
- Compatible Tracks
- Compatible Stages
- Accepted Input Types
- Produced Output Types

## 6. Invocation Section

### Required Fields
- Invocation Conditions
- Invocation Triggers
- Invocation Priority
- Invocation Mode
- Completion Conditions

## 7. Dependency Section

### Required Fields
- Hard Dependencies
- Soft Dependencies
- Dependency Type Notes

## 8. Governance Section

### Required Fields
- Risk Notes
- Validation Rules
- Supervision Priority
- Certainty Constraint
- Governance Constraints

## 9. Version Section

### Required Fields
- Version
- Lifecycle State
- Last Updated
- Change Summary
- Preferred Status

## 10. Operational Section

### Required Fields
- Match Keywords
- Output Artifact Type
- Invocation Record Requirement
- Health Impact Level
- Registry Visibility

## 11. Migration Section

### Required Fields
- Migration Source
- Legacy Asset Relation
- Migration Readiness
- Formalization Status

## 12. Minimal Canonical Capability Object
- Capability ID
- Capability Name
- Capability Class
- Functional Group
- Status
- Purpose
- Core Operation
- Compatible Goal Types
- Compatible Tracks
- Compatible Stages
- Accepted Input Types
- Produced Output Types
- Invocation Conditions
- Invocation Triggers
- Invocation Priority
- Invocation Mode
- Completion Conditions
- Hard Dependencies
- Soft Dependencies
- Risk Notes
- Validation Rules
- Supervision Priority
- Certainty Constraint
- Governance Constraints
- Version
- Lifecycle State
- Last Updated
- Change Summary
- Preferred Status
- Match Keywords
- Output Artifact Type
- Invocation Record Requirement
- Health Impact Level
- Registry Visibility
- Migration Source
- Legacy Asset Relation
- Migration Readiness
- Formalization Status

## 13. Constraint Rules
1. Capability ID and Capability Name must uniquely resolve to the same object
2. Compatible stages and input types must be explicit
3. A capability is not registry-ready if invocation conditions are undefined
4. A capability cannot be marked stable if hard dependencies are unknown
5. A capability cannot be preferred if risk notes and validation rules are missing
6. Version traceability must be preserved
7. Migration lineage should be visible
