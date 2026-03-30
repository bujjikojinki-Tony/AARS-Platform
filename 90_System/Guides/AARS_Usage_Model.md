---
title: AARS_Usage_Model
type: guide
status: draft
project: AARS
tags:
  - aars
  - usage
  - operating-model
created: 2026-03-28
source: ChatGPT
---

# AARS_Usage_Model

## 1. Purpose

This document explains how AARS should be used in practice.

It defines:
- the standard operating sequence
- human-system division of labor
- runtime usage logic
- decision checkpoints
- practical toolchain use

---

## 2. Standard Operating Sequence

AARS should normally be used in the following sequence:

1. Project Framing  
2. Legacy Discovery  
3. Legacy-to-vNext Mapping  
4. Terminology / Concept Stabilization  
5. Capability Extraction  
6. Bounded Case Design  
7. Objectized Case Execution  
8. Final Review  
9. Knowledge Capture  

This sequence may be adapted, but bounded progression should remain visible.

---

## 3. How to Start a Project

Every project should begin with:

- project intent
- goal
- scope
- non-goals
- success criteria
- stage flow

This is typically captured in a **project charter**.

The user should not start with unconstrained generation.  
The user should start with bounded framing.

---

## 4. How to Handle Legacy Material

If a project includes prior materials, systems, or research assets, AARS should next perform:

- legacy discovery
- mapping
- continuity preservation

Each legacy element should be judged as:
- preserve
- preserve with extension
- transform
- split
- absorb
- retire

This prevents both blind carryover and discontinuous redesign.

---

## 5. How to Stabilize Knowledge

Before expanding structure, AARS should stabilize:

- glossary
- taxonomy
- concept distinctions
- layer placement

This prevents downstream drift in:
- capability naming
- case logic
- risk wording
- object labels

---

## 6. How to Extract Capabilities

Once the project boundary and concept layer are stable, AARS should identify reusable operations and formalize them into candidate capabilities.

The rule is:

- first-wave bounded capability family first
- do not inflate too many capabilities too early
- prioritize capabilities that can enter case execution

---

## 7. How to Run a Bounded Case

A bounded case is the minimum operational proof loop.

A bounded case should normally produce:

- invocation record
- dependency object
- risk object
- health snapshot
- recovery path or no-recovery-needed conclusion
- latest stable view

Without this loop, the project remains descriptive rather than operational.

---

## 8. How to Review Progress

At checkpoints, AARS should ask:

- Is the project still in scope?
- Is the output objectized enough?
- Is the state stable, reviewable, or degraded?
- Is recovery needed?
- Is closure allowed?
- What is the next bounded step?

The allowed judgments are typically:
- Review Required
- Continue With Caution
- Closure Allowed

---

## 9. How to Capture Knowledge

Once outputs are validated, they should be captured into the knowledge layer as:

- glossary baselines
- taxonomy baselines
- methodology notes
- stable project outputs
- frozen baselines
- continuity logs

The purpose is not only storage, but safe continuation.

---

## 10. Human-System Division of Labor

### Human
Responsible for:
- intent
- scope decisions
- tradeoff judgment
- freeze / extend / revise decisions

### GPT
Responsible for:
- reasoning
- review support
- framing
- concept stabilization
- next-step recommendation
- objectization judgment

### Codex
Responsible for:
- file generation
- normalization
- repository operations
- automation
- template application
- worktree-safe execution

### Obsidian / GitHub
Responsible for:
- storage
- navigation
- versioning
- rollback
- continuity anchoring

---

## 11. Practical Toolchain Usage

### ChatGPT app
Use for:
- project framing
- review
- planning
- concept clarification
- decision support

### Codex app
Use for:
- generating structured files
- applying frontmatter
- updating MOCs / index
- automating repetitive repository tasks
- object/template alignment

### Obsidian
Use for:
- stable note storage
- project navigation
- glossary and taxonomy browsing
- baseline preservation
- continuity review

### GitHub
Use for:
- commit history
- branching
- rollback
- repository integrity

---

## 12. Runtime Check Questions

At any time, the user should be able to answer:

1. What project is active?
2. What step is current?
3. What capability is being used?
4. What object should this output become?
5. What is the current health state?
6. What is the latest stable view?
7. What is the next bounded step?

If these questions cannot be answered, work is likely drifting.

---

## 13. Recommended Daily Pattern

A practical daily pattern is:

### Step A
Use ChatGPT to define today’s bounded objective.

### Step B
Use Codex to update the vault/repo structure and generate or normalize artifacts.

### Step C
Use Obsidian to review, link, and preserve the updated knowledge state.

### Step D
Use GitHub to keep the state versioned and recoverable.

---

## 14. Recommended Project Pattern

For each project:

- build charter first
- stabilize glossary/taxonomy early
- extract a small capability family
- run one bounded case
- objectize outputs
- review and freeze
- only then expand

This prevents premature over-expansion.

---

## 15. Closing Statement

AARS should be used as a governed progression system.

The goal is to move work from:
- scattered prompts
- unstable documents
- disconnected outputs

into:
- bounded projects
- reusable capabilities
- governed objects
- stable continuation
- reusable knowledge assets