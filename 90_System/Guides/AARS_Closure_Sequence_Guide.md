---
title: AARS_Closure_Sequence_Guide
type: guide
status: draft
project: AARS
tags:
  - aars
  - closure
  - sequence
  - guide
created: 2026-03-28
source: ChatGPT
---

# AARS_Closure_Sequence_Guide

## 1. Purpose

This guide defines the standard closure sequence for a bounded AARS round, project loop, or pilot loop.

It is intended to:
- give operators an explicit end-of-round order
- prevent closure steps from happening out of sequence
- align review, stable view, freeze, archive, and packaging logic
- reduce ambiguity when moving from active work into preserved baseline state

This is a closure-sequence guide, not a model.

---

## 2. Core Principle

The core principle is:

**close in sequence, not by scattered decisions**

This means closure should not happen through isolated actions like:
- freezing first without review
- archiving before closure is understood
- updating the baseline without stable-view logic
- packaging before the closure judgment is explicit

Closure should follow an ordered progression.

---

## 3. Standard Closure Sequence

The standard closure sequence in AARS is:

1. Review the current loop  
2. Confirm or update the latest stable view  
3. Decide whether closure is allowed  
4. Decide whether freeze, extension, recovery, or archive is appropriate  
5. Create closure note  
6. Package the round  
7. Update history / portfolio / navigation  
8. Set the next bounded step or next phase  

This is the recommended default order.

---

## 4. Step 1 — Review the Current Loop

### Purpose
Determine current condition and admissibility.

### Main Questions
- Is the loop actually complete?
- Is the state bounded and interpretable?
- What is strong enough?
- What remains unresolved?
- Is continuation, closure, or recovery more appropriate?

### Main Artifact
- review note

No serious closure should begin without this step.

---

## 5. Step 2 — Confirm or Update the Latest Stable View

### Purpose
Identify the safest accepted continuation anchor.

### Main Questions
- What is the current stable anchor?
- Is the newest state actually safer than the prior one?
- Should the stable anchor change?

### Main Artifact
- latest stable view note

Closure without an explicit stable anchor is weak.

---

## 6. Step 3 — Decide Whether Closure Is Allowed

### Purpose
Judge whether the current bounded loop is truly closure-ready.

### Main Questions
- Is the current loop boundedly complete?
- Is the object chain sufficient?
- Is the stable anchor strong enough?
- Would keeping the loop open improve quality, or only create churn?

### Main Artifact
- closure judgment
- baseline closure checklist result

This is the gateway step.

---

## 7. Step 4 — Decide Freeze / Extend / Recover / Archive

### Purpose
Determine what type of closure or continuation path applies.

### Possible Decisions
- Freeze current baseline
- Extend into a new bounded loop
- Recover before closure
- Archive older state
- Keep active but stable

### Main Artifacts
- freeze decision note
- archive decision note
- no-recovery-needed note
- extension note if needed

This is the major branch point in closure logic.

---

## 8. Step 5 — Create Closure Note

### Purpose
Record what round is ending and what that means.

### Main Questions
- What round is being closed?
- What was completed?
- What is now strong enough?
- What remains incomplete but tolerable?
- What next?

### Main Artifact
- round closure note

This makes the closure interpretable later.

---

## 9. Step 6 — Package the Round

### Purpose
Preserve the round as a coherent reference bundle.

### Should Usually Include
- closure note
- review note
- latest stable view
- active or frozen baseline
- next-step note
- change log if relevant

### Main Artifact
- end-of-round package

This keeps closure reusable rather than scattered.

---

## 10. Step 7 — Update History / Portfolio / Navigation

### Purpose
Ensure system surfaces reflect the new state.

### Typical Updates
- active projects home
- project status register
- baseline history home
- round index home
- system home if needed
- archive/freeze links

Closure is incomplete if the navigation layer still shows the old state.

---

## 11. Step 8 — Set the Next Bounded Step or Next Phase

### Purpose
Define what follows closure.

### Typical Next Steps
- begin new bounded loop
- freeze and pause
- archive and close
- enter production readiness review
- begin runtime prototype phase
- begin next pilot

Closure should always leave a bounded next condition.

---

## 12. Closure Sequence by Scope

## A. Project Closure Sequence
Review → Stable View → Closure Judgment → Freeze/Extend/Recover → Closure Note → Project Package → Status Register Update

## B. Pilot Closure Sequence
Review → Stable View → Pilot Closure Judgment → Freeze/Extend/Recover → Closure Note → Pilot Package → Active/Frozen Project Update

## C. System Round Closure Sequence
Final Review → Stable System Anchor → Closure Judgment → Freeze/Archive Decision → Closure Note → Round Package → Baseline History / Round Index Update

---

## 13. Closure Sequence Failure Modes

This guide protects against:

### Failure 1 — Freeze First
A baseline is frozen before review and stable-view logic are complete.

### Failure 2 — Archive Too Early
Material is archived before closure meaning is preserved.

### Failure 3 — Package Without Judgment
Files are bundled, but no explicit closure decision exists.

### Failure 4 — Navigation Lag
Portfolio and history pages still reflect pre-closure state.

### Failure 5 — No Next Phase Logic
The round closes, but the system does not know what follows.

---

## 14. Human / GPT / Codex Roles in Closure Sequence

### Human
- approves closure
- approves freeze/archive decisions
- decides what the next phase is

### GPT
- supports review and closure reasoning
- recommends stable anchor and decision logic
- helps package the round coherently

### Codex
- generates files
- updates links and MOCs
- prepares change logs and package artifacts
- should not silently reorder or skip closure stages

---

## 15. Minimal Closure Sequence Summary

Use this short form if needed.

### Review Completed?
[yes / no]

### Stable View Explicit?
[yes / no]

### Closure Allowed?
[yes / no]

### Freeze / Archive / Extend / Recover Decision
[ ]

### Closure Note Created?
[yes / no]

### Package Completed?
[yes / no]

### Navigation Updated?
[yes / no]

### Next Phase Defined?
[yes / no]

---

## 16. Suggested Placement

This guide is best placed at:

```text id="wy4r69"
90_System/Guides/AARS_Closure_Sequence_Guide.md