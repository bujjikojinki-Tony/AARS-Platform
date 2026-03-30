---
title: AARS_Freeze_Checklist
type: guide
status: draft
project: AARS
tags:
  - aars
  - freeze
  - checklist
created: 2026-03-28
source: ChatGPT
---

# AARS_Freeze_Checklist

## 1. Purpose

This checklist provides a practical freeze decision routine for AARS projects, baselines, and bounded loops.

It is intended to:
- turn the AARS freeze model into an operational checklist
- reduce premature or vague freeze decisions
- distinguish freeze from pause, archive, and stable-but-active states
- support explicit baseline preservation decisions

This is a practical freeze checklist, not a theory note.

---

## 2. Core Freeze Rule

Freeze should only happen when:

**the current state is good enough to preserve, and further immediate revision is more likely to create churn than structural gain**

If this condition is not met, freeze is premature.

---

## 3. Freeze Output States

A freeze review should normally end in one of the following:

- **Freeze Recommended**
- **Stay Conditionally Stable**
- **Extend Before Freeze**
- **Recover Before Freeze**
- **Archive Instead of Freeze**

Freeze must end in a clear governance judgment.

---

## 4. Universal Freeze Checklist

Use this checklist before freezing any important baseline.

### A. Scope Check
- [ ] Is the bounded loop actually complete?
- [ ] Has the work stayed within intended scope?
- [ ] Is the current state still aligned with project goal?

### B. Review Check
- [ ] Has a structured review already occurred?
- [ ] Did review produce a clear judgment?
- [ ] Are the major contradictions resolved or explicitly bounded?

### C. Stability Check
- [ ] Is the Latest Stable View clear?
- [ ] Is the current state more stable than earlier alternatives?
- [ ] Would continuing revision now likely reduce clarity rather than improve it?

### D. Reuse Check
- [ ] Is this state reusable enough to inherit from?
- [ ] Would future work benefit from preserving this version explicitly?
- [ ] Is the baseline coherent enough to act as a reference anchor?

### E. Decision Check
- [ ] Freeze is truly preferable to continued active revision
- [ ] Freeze is not being used just to force closure
- [ ] Freeze is not being confused with archive or pause

---

## 5. Project Freeze Checklist

Use this when deciding whether to freeze an entire project baseline or pilot loop.

### Project Completeness
- [ ] Has the project completed its current bounded loop?
- [ ] Are the core intended outputs present?
- [ ] Is the project state interpretable to someone returning later?

### Project Review
- [ ] Has the project been reviewed as a whole?
- [ ] Is the current project health acceptable?
- [ ] Is the current project stable enough to preserve?

### Project Continuity
- [ ] Does the project have a clear continuity anchor?
- [ ] Does the project have a latest stable view?
- [ ] Would freezing improve future continuation clarity?

### Project Freeze Decision
- [ ] Freeze project baseline
- [ ] Keep active but stable
- [ ] Extend before freeze
- [ ] Recover before freeze

---

## 6. Knowledge Baseline Freeze Checklist

Use this when freezing:
- glossary baselines
- taxonomy baselines
- architecture baselines
- system models

### Knowledge Quality
- [ ] Is the content coherent enough?
- [ ] Is terminology sufficiently stable?
- [ ] Are known limitations explicit rather than hidden?

### Reuse Value
- [ ] Is this asset reusable beyond immediate current editing?
- [ ] Would preserving this version reduce future confusion?
- [ ] Is the value of preservation higher than the value of continued reworking right now?

### Baseline Decision
- [ ] Freeze as knowledge baseline
- [ ] Keep as reviewable
- [ ] Revise before freeze
- [ ] Archive older version first if needed

---

## 7. Bounded Case Freeze Checklist

Use this when deciding whether a bounded case should contribute to a frozen baseline.

### Case Completeness
- [ ] Has the case reached its intended bounded objective?
- [ ] Is the case still bounded?
- [ ] Has the minimum object chain been produced?

### Object Chain Check
- [ ] Invocation exists
- [ ] Dependency object exists
- [ ] Risk object exists
- [ ] Health snapshot exists
- [ ] Stable view update exists
- [ ] Recovery / no-recovery note exists if required

### Case Decision
- [ ] Freeze case as reference loop
- [ ] Keep case reviewable
- [ ] Strengthen case before freeze
- [ ] Use case only as working material, not baseline yet

---

## 8. Stable View Freeze Checklist

Use this when deciding whether the latest stable view should become a frozen baseline.

### Stable View Strength
- [ ] Is this truly the best current continuation anchor?
- [ ] Is it bounded and interpretable?
- [ ] Is it strong enough to preserve beyond ordinary continuation?

### Freeze Justification
- [ ] Would preserving this state reduce future drift?
- [ ] Is this state likely to be inherited by future work?
- [ ] Is it sufficiently stronger than earlier stable states?

### Decision
- [ ] Freeze current stable view
- [ ] Keep as active stable view only
- [ ] Strengthen before freeze
- [ ] Review again before freeze

---

## 9. Freeze vs Archive Decision Checklist

Use this when uncertain whether something should be frozen or archived.

### Freeze if:
- [ ] it is still a meaningful active reference
- [ ] future work should inherit from it
- [ ] it is stable enough to preserve as a baseline

### Archive if:
- [ ] it is no longer the active reference
- [ ] a newer stronger baseline exists
- [ ] it should remain historically available but not active

### Warning
- [ ] Do not archive what should still be the active baseline
- [ ] Do not freeze what is only historical residue

---

## 10. Freeze Red Flags

If any of these are true, freeze is likely premature:

- [ ] review has not happened yet
- [ ] latest stable view is unclear
- [ ] scope drift is unresolved
- [ ] object chain is materially incomplete
- [ ] terminology remains highly unstable
- [ ] major contradictions are still being discovered
- [ ] the freeze desire is mostly emotional fatigue rather than governance logic

---

## 11. Minimal Freeze Summary Template

Use this short form if needed.

### Freeze Target
[project / baseline / case / stable view / system note]

### Current State
[reviewable / conditionally stable / stable]

### Why Freeze Is Being Considered
- 

### What Is Strong Enough
1.  
2.  
3.  

### What Remains Unresolved
1.  
2.  

### Decision
[Freeze Recommended / Extend Before Freeze / Recover Before Freeze / Keep Active]

### Recommended Next Step After Decision
- 

---

## 12. Final Rule

AARS freeze is complete only when:
- review has occurred
- stable view is explicit
- bounded reuse value is clear
- unresolved items are documented
- a clear freeze judgment is made

That is the minimum operational standard for freeze in AARS.