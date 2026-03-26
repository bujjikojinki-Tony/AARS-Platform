---
title: AARS Risk Object Schema
type: schema
status: stable
project: AARS
tags:
  - aars
  - schema
  - risk
  - object
created: 2026-03-26
source: AARS vNext knowledge asset
domain: AARS
layer: knowledge
aliases:
  - AARS_Risk_Object_Schema
  - Risk Schema
related:
  - "[[AARS_vNext_Terminology_Glossary]]"
  - "[[AARS_Capability_Object_Schema]]"
  - "[[AARS_Dependency_Object_Schema]]"
  - "[[AARS_Health_Snapshot_Template]]"
  - "[[AARS_Recovery_Path_Template]]"
---
# AARS Risk Object Schema

## 1. Purpose
Define the formal [[AARS_vNext_Terminology_Glossary#Risk Object|Risk Object]] schema used to represent detected research-quality and governance [[AARS_vNext_Terminology_Glossary#Risk|risks]] in [[AARS_vNext_Terminology_Glossary#AARS vNext|AARS vNext]].

## 2. Risk Object Sections
1. Identity Section
2. Detection Section
3. Scope and Impact Section
4. Severity and Confidence Section
5. Control Section
6. Resolution Section
7. Continuity Section
8. Governance Section

## 3. Identity Section

### Required Fields
- Risk ID
- Risk Class
- Risk Title
- Status

## 4. Detection Section

### Required Fields
- Detection Stage
- Detection Context
- Trigger Condition
- Detection Basis
- Detected By

## 5. Scope and Impact Section

### Required Fields
- Affected Object Type
- Affected Object Name or ID
- Impact Domain
- Impact Summary

## 6. Severity and Confidence Section

### Required Fields
- Severity Level
- Confidence Level
- Severity Rationale
- Confidence Rationale

## 7. Control Section

### Required Fields
- Control Decision
- Control Effect
- Control Priority
- Certainty Adjustment

## 8. Resolution Section

### Required Fields
- Resolution State
- Recommended Resolution Path
- Resolution Owner Context
- Residual Risk State

## 9. Continuity Section

### Required Fields
- Continuity Relevance
- Health Impact Level
- Resume or Recovery Relevance

## 10. Governance Section

### Required Fields
- Reporting Requirement
- Acceptance Gate Impact
- Logging Requirement
- Review Requirement

## 11. Vocabulary

### Status
- Open
- Monitoring
- In Progress
- Resolved
- Accepted with Record
- Blocked Unresolved

### Severity
- S1 Minimal
- S2 Moderate
- S3 Significant
- S4 Critical

### Confidence
- C1 Tentative
- C2 Working
- C3 Strong
- C4 Controlling

### Control Decision
- Monitor
- Warn
- Reroute to Validation
- Reroute to Supervision
- Require Evidence Refresh
- Lower Confidence
- Block Packaging
- Block Acceptance
- Continue with Residual Risk Disclosure
