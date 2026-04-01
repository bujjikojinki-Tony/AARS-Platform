---
title: AARS_Runtime_Prototype_Checklist
type: guide
status: draft
project: AARS
tags:
  - aars
  - runtime
  - prototype
  - checklist
created: 2026-03-28
source: ChatGPT
---

# AARS_Runtime_Prototype_Checklist

## 1. Purpose

This checklist defines how to review whether the first AARS runtime prototype is good enough for bounded internal use.

It is intended to:
- turn the runtime prototype guide into an operational validation checklist
- prevent prototypes that look complete but are weak in governance visibility
- support bounded iteration before broader platform work

This is a prototype validation checklist.

---

## 2. Core Prototype Rule

A runtime prototype is acceptable only if it makes the following visible enough:

- active project
- current step
- current objective
- latest stable view
- current decision state
- next bounded step

If these are weak or hidden, the prototype is not yet successful.

---

## 3. Minimum Prototype Checklist

### A. Project Visibility
- [ ] Is the active project visible?
- [ ] Is project identity clear?
- [ ] Is current project status visible?

### B. Step Visibility
- [ ] Is the current step visible?
- [ ] Are prior / blocked / upcoming steps distinguishable?
- [ ] Can the user tell where they are in progression?

### C. Objective Visibility
- [ ] Is the current objective visible?
- [ ] Is the current work focus clear?
- [ ] Is scope context visible enough?

### D. Continuity Visibility
- [ ] Is the Latest Stable View visible?
- [ ] Is it clear what the current continuation anchor is?
- [ ] Can the user tell whether newer work is already accepted or not?

### E. Decision Visibility
- [ ] Is the current decision state visible?
- [ ] Is the next-step recommendation visible?
- [ ] Is the rationale understandable enough?

### F. Action Visibility
- [ ] Are Continue / Review / Freeze / Recover actions visible?
- [ ] Do actions reflect state rather than appearing blindly?
- [ ] Is the command bar bounded rather than noisy?

---

## 4. Prototype Failure Red Flags

Treat the prototype as weak if:

- [ ] it looks like a generic dashboard only
- [ ] latest stable view is buried
- [ ] review/decision state is hard to find
- [ ] current step is unclear
- [ ] too much content is shown with too little state context
- [ ] it behaves like a chat window with labels, rather than a governed operating surface

---

## 5. Prototype Success Condition

The prototype is minimally successful when a user can answer, from the UI alone:

1. What project is active?
2. What step is current?
3. What is the current objective?
4. What is the current stable anchor?
5. What is the current recommended decision?
6. What is the next bounded step?

If these six questions can be answered clearly, the first prototype is meaningful.

---

## 6. Final Statement

The first AARS runtime prototype is acceptable when it improves state visibility and governed continuation clarity, not merely when it looks polished.