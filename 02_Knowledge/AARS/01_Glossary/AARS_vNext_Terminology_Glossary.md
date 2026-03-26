---
title: AARS vNext Terminology Glossary
type: glossary
status: stable
project: AARS
tags:
  - aars
  - glossary
  - terminology
  - vnext
created: 2026-03-26
source: migrated AARS vNext terminology asset
domain: AARS
layer: knowledge
aliases:
  - 04_AARS_vNext_Terminology_Glossary
  - AARS_Terminology_Glossary
  - AARS_vNext_Terminology_Glossary
  - AARS Terminology Glossary
related:
  - "[[AARS_Knowledge_Index]]"
  - "[[AARS_Capability_Object_Schema]]"
  - "[[AARS_Risk_Object_Schema]]"
  - "[[AARS_Dependency_Object_Schema]]"
---

# AARS vNext Terminology Glossary

## 1. Purpose
Provide a unified terminology baseline for AARS vNext so that architecture, kernel, object, validation, migration, and implementation artifacts use a shared conceptual vocabulary.

## 2. Core System Terms

### AARS
The research operating system framework being developed and refined across the current document set.

### AARS vNext
The upgraded form of AARS defined by gateway-driven input governance, capability-based operation, explicit risk control, ops visibility, stable-view selection, and recovery logic.

### Research Operating System
A governed system for framing, executing, validating, supervising, stabilizing, and packaging research work through structured control layers rather than ad hoc drafting alone.

### Artifact
Any governed document, schema, template, note, record, or structured output within the AARS system.

### Object
A formally represented governed unit inside AARS vNext, such as a capability object, dependency object, risk object, health snapshot, stable view, or recovery path.

### Asset
A reusable resource that may or may not yet be formalized as a vNext object.

## 3. Kernel Terms

### Kernel
A major control component in AARS that governs a distinct domain of research-system behavior.

### Input Gateway
The governed entry layer that classifies, qualifies, and routes incoming inputs into the research system.

### Capability Registry
The control layer that discovers, matches, governs, versions, and supervises callable capabilities.

### Risk Control
The governance layer that monitors non-structural research risks such as evidence weakness, trust mismatch, freshness mismatch, evaluation drift, tooling drift, packaging drift, governance drift, and unsupported certainty.

### Ops Health
The operational visibility layer that summarizes the condition of the project, threads, artifacts, blockers, and recovery readiness.

## 4. Capability Terms

### Capability
A callable, governed, reusable research unit inside AARS vNext.

### Capability Object
The formal schema-based representation of a capability, including identity, function, compatibility, invocation rules, dependencies, governance notes, version state, and migration lineage. See [[AARS_Capability_Object_Schema]].

### Invocation
The actual governed use of a capability in a live task context.

### Invocation Record
The structured trace of a capability-use event, including compatibility basis, dependency state, outcome status, and follow-up actions. See [[AARS_Invocation_Record_Template]].

## 5. Dependency Terms

### Dependency
A prerequisite relation in which one object, stage, thread, or output relies on another being present, valid, fresh, compatible, or governed.

### Dependency Object
The formal representation of a dependency relation, including dependent object, prerequisite object, required state, actual state, control effect, and resolution logic. See [[AARS_Dependency_Object_Schema]].

### Hard Dependency
A dependency whose absence normally blocks valid progression or invocation.

### Soft Dependency
A dependency whose absence weakens quality or confidence but does not always block work.

## 6. Risk Terms

### Risk
A governed representation of a quality, evidence, control, or governance threat to valid research progression or output.

### Risk Object
The formal representation of a risk instance, including class, severity, confidence, control effect, resolution state, and health impact. See [[AARS_Risk_Object_Schema]].

### Freshness Mismatch
A condition where evidence does not meet the temporal requirement of the task.

### Unsupported Certainty
A condition where conclusion strength exceeds what the evidence or controls justify.

## 7. Health and Stability Terms

### Health Snapshot
A point-in-time summary of project condition across threads, artifacts, capabilities, risks, blockers, and recovery readiness. See [[AARS_Health_Snapshot_Template]].

### Latest Stable View
The most recent state that is safe enough for the intended continuation use.

### Stable Anchor
The actual artifact, thread state, capability version, or project state used as the continuation base.

### Reviewable
A state that is coherent enough for structured review but not yet strong enough to serve as unrestricted stable baseline.

## 8. Recovery Terms

### Recovery
The governed correction process used when work becomes blocked, degraded, stale, or risk-constrained.

### Recovery Path
The formal representation of a corrective sequence that restores a usable continuation state. See [[AARS_Recovery_Path_Template]].

### Rollback
A controlled return to a prior stable anchor when the current state is less safe than a known earlier state.

## 9. Normalization Rules
1. Use capability instead of mixing “tool,” “routine,” and “operation” unless subtype matters.
2. Use risk object only for a formalized risk instance.
3. Use dependency object only when the dependency is explicitly represented.
4. Use stable view only for selected continuation anchors.
5. Use reviewable for coherent-but-not-yet-stable states.
6. Use recovery path for formal corrective sequences.
