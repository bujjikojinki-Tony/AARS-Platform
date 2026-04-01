---
title: AARS_Validation_Context_Selection_Guide
type: guide
status: draft
project: AARS
tags:
  - aars
  - validation
  - context
  - guide
created: 2026-03-28
source: ChatGPT
---

# AARS_Validation_Context_Selection_Guide

## 1. Purpose

This guide explains how to choose the next bounded validation context for AARS.

It is intended to:
- help Round_02 select a useful additional validation context
- prevent weak or redundant validation choices
- ensure the chosen context actually strengthens production-readiness evidence
- preserve boundedness during validation expansion

This is a validation-context selection guide.

---

## 2. Core Principle

The core principle is:

**choose the next validation context for contrast value, boundedness, and operational proof value**

This means the next validation context should:
- differ enough from Round_01 to test repeatability
- remain small enough to finish
- be operational enough to expose real system behavior

Do not choose a new context only because it is interesting.

---

## 3. What a Good Validation Context Should Do

A good validation context should help answer at least one of these:

- Can AARS work beyond the original Round_01 reference context?
- Can the templates be reused without major confusion?
- Can the stable-view and review logic repeat cleanly?
- Can portfolio and status tracking handle more than one active context?
- Can runtime/prototype logic be grounded in real use?

If the new context does not strengthen one of these, it is weak validation.

---

## 4. Selection Criteria

Use the following criteria when selecting the next validation context.

### A. Boundedness
- Is it small enough to complete?
- Can it fit into one bounded validation loop?

### B. Contrast Value
- Is it meaningfully different from the primary Round_01 context?

### C. Operational Value
- Will it exercise real project / review / stable-view behavior?

### D. Reuse Pressure
- Will it test whether current templates and guides are reusable?

### E. Portfolio Value
- Will it help validate multi-project visibility or status tracking?

A strong validation context should score well on most of these.

---

## 5. Recommended Validation Context Types

### Type A — Additional Small Project
A small new bounded project using the current templates.

### Type B — Additional Small Pilot
A second pilot with a different local structure or objective.

### Type C — AARS Self-Refinement Project
A bounded project where AARS itself is the subject, but the work is run strictly through the current governance stack.

### Type D — Runtime Prototype Validation Context
A bounded real-use context used to test the runtime/page/component logic.

These are the best first validation types.

---

## 6. Weak Validation Context Types

Avoid choosing a context that is:

- too large
- too abstract
- too similar to the original reference context
- too dependent on unfinished future UI
- mostly packaging-oriented
- unlikely to produce a bounded review and stable-view update

Such contexts create weak evidence.

---

## 7. Selection Questions

Before choosing the next context, ask:

1. What new thing will this context validate?
2. How is it different from Round_01?
3. Can it be completed in bounded form?
4. Will it produce at least one review and one stable-view update?
5. Will it reveal whether the templates are truly reusable?

These questions should drive the decision.

---

## 8. Selection Output

The selection result should normally state:

- chosen validation context
- why it was chosen
- what it is expected to validate
- what is explicitly out of scope
- what would count as success

The selection should be explicit and reviewable.

---

## 9. Human / GPT / Codex Roles

### Human
- chooses among candidate contexts
- judges strategic contrast value
- prevents overexpansion

### GPT
- compares candidate validation contexts
- identifies likely validation value
- recommends a bounded best-fit option

### Codex
- scaffolds the chosen context once selected
- prepares files and links
- should not choose the context silently

---

## 10. Suggested Placement

This guide is best placed at:

```text id="til7gy"
90_System/Guides/AARS_Validation_Context_Selection_Guide.md