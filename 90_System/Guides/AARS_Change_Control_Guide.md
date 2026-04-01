---
title: AARS_Change_Control_Guide
type: guide
status: draft
project: AARS
tags:
  - aars
  - change-control
  - guide
created: 2026-03-28
source: ChatGPT
---

# AARS_Change_Control_Guide

## 1. Purpose

This guide defines change control for AARS.

It is intended to:
- make system changes explicit
- reduce hidden drift
- protect active projects and baselines
- define how meaningful changes should be proposed, reviewed, and accepted
- ensure that the system evolves through governed adjustment rather than informal mutation

This is a change-control guide, not a system model.

---

## 2. Core Principle

The core principle is:

**all meaningful change should be reviewable before it becomes normal**

This means:
- important changes should be visible
- affected scope should be known
- baseline impact should be understood
- active-project impact should be checked
- change should not become “the new normal” silently

---

## 3. What Counts as a Controlled Change

Controlled changes include:

- adding a new system model
- changing major terminology
- modifying project operating rules
- changing review / freeze / archive logic
- introducing new directory tiers
- changing template structure
- changing object schemas
- changing runtime page logic
- changing portfolio-state semantics

Minor typo fixes do not require the same level of control.

---

## 4. Change Classes

AARS should distinguish at least three change classes.

### Class A — Minor Clarification
Low-risk wording, naming, formatting, or linkage improvements.

### Class B — Structural Change
A change that affects how the system is organized or used.

### Class C — Baseline-Sensitive Change
A change that may alter the meaning of the current active system baseline.

The higher the class, the stronger the required review.

---

## 5. Change Proposal Structure

Every meaningful change proposal should answer:

1. What is changing?
2. Why is it changing?
3. What problem does it solve?
4. What files or layers are affected?
5. Is the change minor, structural, or baseline-sensitive?
6. What should remain unchanged?
7. What is the rollback path if needed?

Without this, the change proposal is weak.

---

## 6. Change Review Criteria

A meaningful change should be reviewed against:

- scope clarity
- necessity
- impact on active projects
- impact on stable view / freeze / archive logic
- impact on templates and schemas
- continuity safety
- rollback clarity

Change control is not only about correctness, but about system stability.

---

## 7. Change Approval Logic

### Minor Clarification
May be approved with light review.

### Structural Change
Should usually require explicit review and index/MOC update.

### Baseline-Sensitive Change
Should usually require:
- explicit review
- possible baseline note update
- impact check on active projects
- possible freeze-before-change decision

This keeps major changes governed.

---

## 8. Change Failure Modes

This guide protects against:

### Failure 1 — Silent Drift
The system changes meaning without explicit acknowledgment.

### Failure 2 — Scope-Blind Change
A change is made without knowing what it affects.

### Failure 3 — Baseline Damage
Active baseline meaning is altered accidentally.

### Failure 4 — Project Breakage
Project templates, guides, or current active work become misaligned after the change.

### Failure 5 — No Rollback Thinking
A structural change is introduced without clear recovery path.

---

## 9. Human / GPT / Codex Roles in Change Control

### Human
- approves major changes
- judges whether the change is worth the continuity cost
- decides whether freeze or baseline update is needed

### GPT
- clarifies the change rationale
- classifies change type
- reviews coherence and risk
- recommends whether the change should be accepted now or deferred

### Codex
- applies approved changes
- updates affected files, links, and indexes
- prepares reviewable diffs
- should not silently implement baseline-sensitive changes

---

## 10. Suggested Placement

This file is best placed at:

```text id="zwwwdi"
90_System/Guides/AARS_Change_Control_Guide.md