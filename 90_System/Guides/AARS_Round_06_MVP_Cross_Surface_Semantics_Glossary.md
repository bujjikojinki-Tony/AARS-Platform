---
title: AARS_Round_06_MVP_Cross_Surface_Semantics_Glossary
type: glossary-note
status: draft
project: AARS
tags:
  - aars
  - round-06
  - mvp
  - semantics
  - glossary
created: 2026-04-07
source: Codex
---

# AARS_Round_06_MVP_Cross_Surface_Semantics_Glossary

## Purpose

This note records only the small set of cross-surface governance terms that recur across the accepted first-set MVP surfaces.

It is semantic guidance only.
It is **not** a global schema and **not** a payload-unification rule.

---

## Shared Terms

### Status

`status` expresses the current operating condition of the surface or subject being shown.

- It is page-local and does not need one universal enum
- It should answer: what condition is this item currently in?

### Health

`health` expresses bounded operational risk/readiness.

- It should answer: is this safe enough to continue from right now?
- It is distinct from status and distinct from decision

### Stability

`stability` expresses whether the current condition is steady enough to support continuation.

- It should answer: how safe is this current state as a continuation basis?
- It is closely related to, but not identical with, the latest stable view

### Decision

`decision` expresses current governance judgment.

- It should answer: what continuation judgment is currently in force?
- Typical language should remain bounded governance language such as review required, continue with caution, or closure allowed

### Latest Stable View

`latest stable view` is the current trusted continuation anchor.

- It should answer: what is the last safe bounded state we can continue from?
- It should always be paired with why it is trusted and what can safely continue

### Recommended Next Step / Next Action

`recommended next step` or `recommended next action` expresses the immediate bounded move supported by the current surface.

- The naming may stay page-local
- It should answer: what should happen next if we stay within the current accepted scope?

### Admissible Actions

`admissible actions` are the actions the surface is willing to expose right now.

- They should remain bounded and governance-consistent
- They should not imply routing, orchestration, or backend capability that does not exist

---

## Usage Rule

Across the accepted first-set MVP surfaces:

- keep these terms semantically consistent
- allow the payload fields themselves to remain page-local
- avoid widening the current page contracts into one global schema unless a later explicit contract-upgrade decision is recorded
