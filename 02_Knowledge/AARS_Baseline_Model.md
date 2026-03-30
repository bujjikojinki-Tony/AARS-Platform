---
title: AARS_Baseline_Model
type: spec
status: draft
project: AARS
tags:
  - aars
  - baseline
  - model
created: 2026-03-28
source: ChatGPT
---

# AARS_Baseline_Model

## 1. Purpose

This document defines the baseline model of AARS.

It explains:
- what a baseline is in AARS
- how baseline differs from stable view, freeze, and archive
- how baseline states are assigned
- how baselines support continuity, review, and reuse
- how AARS manages multiple baseline conditions across projects and system assets

This is the baseline-governance model of AARS.

---

## 2. Core Definition

A baseline in AARS is:

**a recognized reference state of work that is sufficiently defined, bounded, and interpretable to support review, continuation, reuse, comparison, or preservation.**

A baseline is not necessarily final.  
A baseline is a reference state.

This means a baseline may be:
- reviewable
- conditionally stable
- stable
- frozen
- archived

as long as it is explicit and interpretable.

---

## 3. Core Principle

The core principle is:

**AARS should not treat all saved states as equivalent; it should classify reference states by governance quality and reuse meaning.**

This prevents confusion between:
- active but weak states
- stable working states
- preserved baseline states
- historical states

---

## 4. Why Baseline Matters

Baseline matters because it allows the system to answer:

- what state is currently being worked from
- what state is strong enough to compare against
- what state is strong enough to inherit from
- what state should no longer be treated as active
- what state should remain available historically

Without a baseline model:
- stability labels become inconsistent
- freeze becomes vague
- archive becomes overloaded
- continuity anchors become unclear

---

## 5. Baseline vs Related Concepts

## 5.1 Baseline vs Stable View

### Stable View
The current best safe continuation anchor.

### Baseline
Any recognized reference state that has governance meaning.

### Difference
Stable view is one important kind of baseline, but baseline is broader.

---

## 5.2 Baseline vs Freeze

### Freeze
An explicit preservation decision.

### Baseline
A reference state, whether frozen or not.

### Difference
Frozen baselines are a subset of baselines.  
Not all baselines are frozen.

---

## 5.3 Baseline vs Archive

### Archive
Historical or inactive retention.

### Baseline
A recognized reference state with governance meaning.

### Difference
Archived states may still be baselines, but only as historical baselines, not active ones.

---

## 5.4 Baseline vs Draft

### Draft
A working state not yet reliable enough to be used as reference.

### Baseline
A state accepted enough to be referenced, even if still reviewable.

### Difference
Draft is pre-baseline.  
Baseline begins when reference value is explicit.

---

## 6. Baseline Classes

AARS should recognize at least five baseline classes:

1. Reviewable Baseline  
2. Conditionally Stable Baseline  
3. Stable Baseline  
4. Frozen Baseline  
5. Archived Baseline  

These classes should not be treated as synonyms.

---

## 7. Reviewable Baseline

## Definition
A reference state that is coherent enough to be reviewed and compared, but not yet strong enough to serve as an unrestricted continuation anchor.

## Use
Useful when:
- the structure is visible
- the work is meaningful
- more validation is still needed

## Typical Meaning
“This is now a real state worth reviewing, but not yet a strong reusable baseline.”

---

## 8. Conditionally Stable Baseline

## Definition
A reference state that is usable for continuation, but only under explicit caution conditions.

## Use
Useful when:
- the work is coherent enough
- unresolved issues remain visible
- continuation is allowed, but not unconstrained

## Typical Meaning
“This can be used, but only with clear awareness of its limits.”

---

## 9. Stable Baseline

## Definition
A reference state that is sufficiently coherent, bounded, and reusable for normal continuation and inheritance.

## Use
Useful when:
- major contradictions are resolved or bounded
- the state is fit to support future work
- the current structure no longer requires immediate correction

## Typical Meaning
“This is the current accepted working reference state.”

---

## 10. Frozen Baseline

## Definition
A stable baseline that has been deliberately preserved as a reference checkpoint.

## Use
Useful when:
- a loop is complete
- churn should stop
- later work should inherit this state rather than keep rewriting it

## Typical Meaning
“This is intentionally preserved as a reference anchor.”

---

## 11. Archived Baseline

## Definition
A previously meaningful baseline that is no longer active but should remain historically interpretable.

## Use
Useful when:
- a newer baseline replaces it
- the related project loop is closed
- the baseline still matters for traceability or comparison

## Typical Meaning
“This is no longer active, but still important as historical reference.”

---

## 12. Baseline State Progression

A normal baseline progression may look like:

```text
Draft
→ Reviewable Baseline
→ Conditionally Stable Baseline
→ Stable Baseline
→ Frozen Baseline
→ Archived Baseline