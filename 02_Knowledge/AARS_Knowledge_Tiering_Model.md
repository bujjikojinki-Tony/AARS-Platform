---
title: AARS_Knowledge_Tiering_Model
type: spec
status: draft
project: AARS
tags:
  - aars
  - knowledge
  - tiering
  - model
created: 2026-03-28
source: ChatGPT
---

# AARS_Knowledge_Tiering_Model

## 1. Purpose

This document defines the knowledge tiering model of AARS.

It explains:
- how different knowledge assets should be tiered
- why not all knowledge should be treated equally
- how system knowledge differs from project knowledge
- how active, stable, frozen, and archived knowledge relate
- how knowledge tiering supports reuse, navigation, and governance

This is the knowledge-layer organization model of AARS.

---

## 2. Core Definition

Knowledge tiering in AARS means:

**the explicit classification of knowledge assets into different levels of reuse, stability, scope, and governance relevance.**

Knowledge tiering is needed because:
- some assets are system-wide
- some assets are project-local
- some assets are active but unstable
- some assets are stable baselines
- some assets are historical only

Without tiering, the knowledge layer becomes noisy and misleading.

---

## 3. Core Principle

The core principle is:

**place knowledge according to reuse scope and governance status, not just according to when it was produced**

This means:
- not every project note belongs in core knowledge
- not every stable file should be treated as system-level
- not every archived item should disappear from interpretation
- not every guide is a kernel
- not every glossary is equally system-wide

---

## 4. Why Tiering Matters

Tiering matters because it helps answer:

- what is system-wide?
- what is project-local?
- what is stable enough to inherit?
- what is active but still evolving?
- what is historical only?

Without tiering:
- navigation becomes weak
- file placement becomes arbitrary
- system knowledge becomes polluted by project-local material
- frozen baselines and active notes become confused

---

## 5. Main Knowledge Tiers

AARS should recognize at least the following knowledge tiers:

1. System Core Knowledge  
2. System Operational Knowledge  
3. Project-Bound Knowledge  
4. Output / Milestone Knowledge  
5. Continuity Knowledge  
6. Historical / Archive Knowledge  

These are not merely folders; they are functional tiers.

---

## 6. Tier 1 — System Core Knowledge

## Definition
Knowledge that defines the operating logic of AARS itself.

## Characteristics
- cross-project reuse
- high governance relevance
- system-defining role
- slow-changing compared with project notes

## Typical Content
- system positioning
- execution model
- governance model
- object chain model
- stage model
- project model
- baseline model
- continuity model

## Typical Placement
- `02_Knowledge/`

This is the highest reusable tier.

---

## 7. Tier 2 — System Operational Knowledge

## Definition
Knowledge that explains how to operate, apply, or maintain the system.

## Characteristics
- reusable
- human-facing
- process-supportive
- often guide or checklist form

## Typical Content
- usage model
- operating guides
- review checklist
- freeze checklist
- naming rules
- file placement guide
- latest stable view operating guide

## Typical Placement
- `90_System/Guides/`

This tier supports operation, not core system definition.

---

## 8. Tier 3 — Project-Bound Knowledge

## Definition
Knowledge that belongs mainly to one bounded project.

## Characteristics
- local scope
- tied to one pilot, project, or domain loop
- often meaningful mainly inside one project container
- may later contribute to reusable core knowledge, but is not automatically core knowledge

## Typical Content
- project charter
- project home
- working questions
- concept map
- layer validation note
- local architecture note
- project review note

## Typical Placement
- `03_Projects/...`

This is the main active project tier.

---

## 9. Tier 4 — Output / Milestone Knowledge

## Definition
Knowledge preserved primarily because it is a stage output, milestone deliverable, or packaging result.

## Characteristics
- often structured around deliverables
- may be reusable, but primarily milestone-oriented
- often more endpoint-oriented than system-defining

## Typical Content
- roadmap
- paper outline
- submission checklist
- milestone report
- review package

## Typical Placement
- `05_Outputs/...` if used
- or project folder until outputs are separated more formally

This tier is outcome-oriented rather than system-defining.

---

## 10. Tier 5 — Continuity Knowledge

## Definition
Knowledge preserved because it supports safe continuation, review traceability, or recovery.

## Characteristics
- state-aware
- continuity-anchoring
- often tied to governance status
- not always “knowledge article” shaped

## Typical Content
- continuity log
- latest stable view
- health snapshot
- freeze note
- recovery path
- no-recovery-needed conclusion

## Typical Placement
- project directory
- continuity area
- archive if inactive

This tier protects resumability.

---

## 11. Tier 6 — Historical / Archive Knowledge

## Definition
Knowledge preserved for reference, traceability, or historical interpretation after it is no longer the active working baseline.

## Characteristics
- inactive
- historically meaningful
- not the current reference state
- should remain interpretable

## Typical Content
- frozen past baselines
- retired notes
- superseded roadmaps
- deprecated structures
- archived project states

## Typical Placement
- `06_Archive/`

This is the historical memory tier.

---

## 12. Tier Relationships

These tiers should relate as follows:

```text id="x4zyqj"
System Core Knowledge
↕
System Operational Knowledge
↕
Project-Bound Knowledge
↕
Output / Milestone Knowledge
↕
Continuity Knowledge
↕
Historical / Archive Knowledge