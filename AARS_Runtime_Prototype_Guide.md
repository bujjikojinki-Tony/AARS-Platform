---
title: AARS_Runtime_Prototype_Guide
type: guide
status: draft
project: AARS
tags:
  - aars
  - runtime
  - prototype
  - guide
created: 2026-03-28
source: ChatGPT
---

# AARS_Runtime_Prototype_Guide

## 1. Purpose

This guide explains how to build a first runtime prototype for AARS.

It is intended to:
- translate the current AARS system models into a minimal usable prototype
- keep the prototype bounded
- avoid overbuilding too early
- define the minimum screens, states, and interactions needed for a first operational prototype

This is a prototype guide, not a final UI specification.

---

## 2. Core Prototype Principle

The core principle is:

**prototype the control surface, not the whole platform**

This means the first runtime prototype should focus on making visible:

- active project
- current step
- current objective
- object-chain state
- health state
- latest stable view
- next-step decision

The prototype does not need to implement every possible feature.

---

## 3. Why a Runtime Prototype Matters

A runtime prototype matters because it tests whether:

- the page model is understandable
- the UI components are sufficient
- stable view is actually visible enough
- review and decision surfaces are operational
- the system feels like an operating system rather than a document pile

Without a prototype, the runtime layer remains too theoretical.

---

## 4. Minimum Prototype Scope

The first runtime prototype should include only:

1. Project Overview surface  
2. Current Step surface  
3. Review / Decision surface  
4. Latest Stable View surface  
5. Basic Action Command Bar  

That is enough for a first bounded prototype.

---

## 5. Prototype Inputs

The prototype should be driven by existing system artifacts such as:

- `AARS_System_Home.md`
- `AARS_Active_Projects_Home.md`
- `AARS_Project_Status_Register.md`
- one active project home
- one latest stable view note
- one review note
- one bounded case / object chain example

This keeps the prototype grounded in real system material.

---

## 6. Prototype Surface 1 — Project Overview

### Should Show
- active project
- project goal
- current track
- current stage
- project status
- latest stable view summary
- next-step summary

### Why
This is the main “orientation” surface.

---

## 7. Prototype Surface 2 — Current Step

### Should Show
- current step name
- current objective
- required outputs for the step
- current blockers
- current local state

### Why
This prevents runtime ambiguity.

---

## 8. Prototype Surface 3 — Review / Decision

### Should Show
- review target
- review findings
- current health
- stable anchor
- current decision state
- recommended next step

### Why
This is the main governance surface of the runtime.

---

## 9. Prototype Surface 4 — Latest Stable View

### Should Show
- stable view summary
- what is already accepted
- unresolved but tolerable issues
- maturity state
- continuity guidance

### Why
This is the continuity anchor surface.

---

## 10. Prototype Surface 5 — Action Command Bar

### Should Show
- Continue
- Review
- Freeze
- Recover
- Jump
- Capture

### Rule
These actions should reflect current state, not just always be available.

---

## 11. Prototype States to Support

The first prototype should support at least:

### Project States
- active
- reviewable
- conditionally stable
- frozen

### Step States
- current
- completed
- blocked
- upcoming

### Decision States
- Continue With Caution
- Review Required
- Closure Allowed
- Freeze Recommended
- Recover Before Continue

These are enough for meaningful prototype behavior.

---

## 12. What the Prototype Does Not Need Yet

The first prototype does **not** need:

- full user permissions
- multi-user collaboration
- complete automation layer
- complete archive browser
- every object schema form
- complex analytics
- polished visual theme system

That would be overbuilding too early.

---

## 13. Recommended Build Order

### Step 1
Build project overview

### Step 2
Build current step page

### Step 3
Build latest stable view card/panel

### Step 4
Build review / decision surface

### Step 5
Add basic action bar

### Step 6
Test with one real project, such as CDA pilot

This is the bounded prototype path.

---

## 14. Prototype Evaluation Questions

After building the prototype, ask:

1. Can a user immediately tell what project is active?
2. Can a user tell what step is current?
3. Is the latest stable view easy to locate?
4. Can the user tell what decision is currently justified?
5. Does the prototype help continuation more than a folder tree alone?

If not, the prototype is still too weak.

---

## 15. GPT / Codex Roles in Prototyping

### GPT
- clarifies surface logic
- checks whether page content reflects system models
- tests whether decision surfaces are understandable

### Codex
- scaffolds the prototype
- builds page components
- maps artifacts into mock runtime data
- iterates on layout and logic

### Human
- judges usability
- checks whether the prototype reflects real working needs
- prevents overbuilding

---

## 16. Recommended Placement

This file should be placed in:

```text
90_System/Guides/AARS_Runtime_Prototype_Guide.md