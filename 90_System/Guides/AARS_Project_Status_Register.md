---
title: AARS_Project_Status_Register
type: guide
status: draft
project: AARS
tags:
  - aars
  - project
  - status
  - register
created: 2026-03-28
source: ChatGPT
---

# AARS_Project_Status_Register

## 1. Purpose

This register provides a standard way to track the current state of AARS projects across the system.

It is intended to:
- make project state visible at portfolio level
- distinguish active, reviewable, frozen, paused, recovering, and archived projects
- support multi-project governance
- reduce ambiguity around what is current, stable, or inactive
- provide a repeatable status surface for humans, GPT, and Codex

This is a status register guide, not a system model.

---

## 2. Core Principle

The core principle is:

**every meaningful AARS project should have an explicit current status**

This means the system should not rely on memory or folder age to infer:
- whether a project is active
- whether it is stable
- whether it is frozen
- whether it should be resumed
- whether it should remain archived

Status must be visible.

---

## 3. Why the Register Matters

Without a status register:
- active and frozen projects get mixed
- paused projects are forgotten
- recovering projects continue as if healthy
- priority becomes implicit
- multi-project governance weakens

The register gives AARS a portfolio-level control surface.

---

## 4. Primary Project Status Classes

AARS should recognize at least the following project statuses:

1. Active  
2. Reviewable  
3. Conditionally Stable  
4. Frozen  
5. Paused  
6. Recovering  
7. Archived  

These statuses describe the current governance condition of the project as a whole.

---

## 5. Status Definitions

### Active
The project is currently being advanced.

### Reviewable
The project has produced meaningful outputs and requires structured review.

### Conditionally Stable
The project may continue, but caution conditions remain visible.

### Frozen
The current project baseline has been preserved as a bounded reference state.

### Paused
The project is temporarily inactive but not archived.

### Recovering
The project requires bounded corrective action before normal continuation.

### Archived
The project is no longer active and is preserved mainly for historical reference.

---

## 6. Recommended Register Fields

A project status register should include at least:

- Project ID
- Project Name
- Domain
- Primary Goal Type
- Primary Track
- Current Stage
- Current Status
- Latest Stable View
- Immediate Next Step
- Priority
- Notes

These fields are the minimum portfolio-control fields.

---

## 7. Register Template

### Copy from here

```md
# AARS_Project_Status_Register

| Project ID | Project Name | Domain | Goal Type | Track | Current Stage | Status | Latest Stable View | Next Step | Priority | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |  |