---
title: AARS_Stage_Model
type: spec
status: draft
project: AARS
tags:
  - aars
  - stage
  - model
created: 2026-03-28
source: ChatGPT
---

# AARS_Stage_Model

## 1. Purpose

This document defines the stage model of AARS.

It explains:
- what a stage is in AARS
- why staged progression matters
- how stages differ from steps, tasks, and outputs
- how stage transition should be governed
- what minimum completion means at stage level

This is the stage-governance model of AARS.

---

## 2. Core Definition

A stage in AARS is:

**a bounded progression segment with its own purpose, entry conditions, exit conditions, expected outputs, and review logic.**

A stage is not:
- a single task
- a file
- a generic milestone label
- a chat turn
- a vague project mood

A stage is a governed progression unit.

---

## 3. Core Principle

The core principle is:

**projects should move through explicit stages rather than drift through implicit activity**

This means:
- every project should know its current stage
- each stage should have a clear purpose
- progression should not happen only because work exists
- transition between stages should be justified

---

## 4. Why Stages Matter

Stages matter because without them:
- projects blur framing, structuring, execution, and review
- freeze may happen too early
- objectization may happen too late
- capability extraction may begin before concept stability
- bounded cases may run without readiness

Stage clarity protects bounded progression.

---

## 5. Stage vs Related Concepts

## 5.1 Stage vs Step

### Stage
A major bounded progression segment.

### Step
A smaller unit inside a stage.

### Difference
Stages are higher-order progression containers.  
Steps are operational actions or local movements within them.

---

## 5.2 Stage vs Task

### Stage
Defines bounded progression meaning.

### Task
Defines work to perform.

### Difference
Tasks may change frequently.  
Stages define the stable logic of what phase the project is in.

---

## 5.3 Stage vs Output

### Stage
Defines progression state.

### Output
Defines artifact result.

### Difference
A stage may produce many outputs.  
An output does not by itself define the stage.

---

## 6. Standard AARS Stage Sequence

A default AARS stage sequence is:

1. Intent Framing  
2. Goal Definition  
3. Track Selection  
4. Discovery  
5. Structuring  
6. Capability Preparation  
7. Bounded Case Execution  
8. Review and Stabilization  
9. Freeze / Extend / Recover Decision  
10. Knowledge Capture  

This sequence may be adapted by project type, but the logic should remain visible.

---

## 7. Stage 1 — Intent Framing

## Purpose
Clarify why the project exists.

## Core Questions
- Why are we doing this?
- What kind of problem is this?
- What kind of project is this?
- Why is it bounded in this way?

## Minimum Outputs
- initial project intent statement
- initial project identity

## Exit Condition
Intent is explicit enough to support goal definition.

---

## 8. Stage 2 — Goal Definition

## Purpose
Define what the project is trying to achieve.

## Core Questions
- What is the primary goal?
- What are secondary goals?
- What are non-goals?
- What would count as success?

## Minimum Outputs
- goal statement
- success criteria
- non-goal statement

## Exit Condition
Project purpose is specific enough to support track selection.

---

## 9. Stage 3 — Track Selection

## Purpose
Select the right path of work for this project.

## Core Questions
- Is this primarily migration, structuring, capability, case, governance, or packaging work?
- Which track should dominate first?
- Which tracks are deferred?

## Minimum Outputs
- primary track statement
- deferred track statement

## Exit Condition
A bounded working path has been selected.

---

## 10. Stage 4 — Discovery

## Purpose
Identify the materials, assets, concepts, routines, or legacy structures relevant to the project.

## Core Questions
- What already exists?
- What legacy material is relevant?
- What domain assets or routines are present?
- What continuity anchors already exist?

## Minimum Outputs
- discovery notes
- asset or legacy inventory
- initial continuity anchor note

## Exit Condition
The project has enough discovered material to begin structuring or mapping.

---

## 11. Stage 5 — Structuring

## Purpose
Stabilize the project’s conceptual and organizational structure.

## Core Questions
- What are the core concepts?
- What glossary is needed?
- What taxonomy is needed?
- What concept distinctions must be preserved?
- What layers are being mixed?

## Minimum Outputs
Depending on project type:
- glossary
- taxonomy
- concept map
- layer validation
- mapping file

## Exit Condition
The project is structured enough to support capability or case work.

---

## 12. Stage 6 — Capability Preparation

## Purpose
Identify and formalize the first reusable operations.

## Core Questions
- What capabilities are needed?
- Which belong in the first-wave bounded family?
- Which are premature?

## Minimum Outputs
- capability catalog
- one or more capability objects
- capability-use plan

## Exit Condition
At least one capability is ready to enter bounded execution.

---

## 13. Stage 7 — Bounded Case Execution

## Purpose
Run the first serious operational proof loop.

## Core Questions
- What is the bounded case?
- Which capabilities are being tested?
- What object chain is expected?
- What dependencies and risks emerge?

## Minimum Outputs
- invocation
- dependency object
- risk object
- health snapshot
- stable view candidate
- recovery/no-recovery logic

## Exit Condition
The case is complete enough for review.

---

## 14. Stage 8 — Review and Stabilization

## Purpose
Determine whether the results are coherent enough to continue, freeze, or recover.

## Core Questions
- Did the object chain complete?
- Is the case bounded and meaningful?
- What is the current health state?
- What is the latest stable view?
- What next step is admissible?

## Minimum Outputs
- review note
- stable view update
- continuation judgment

## Exit Condition
A governance decision becomes possible.

---

## 15. Stage 9 — Freeze / Extend / Recover Decision

## Purpose
Determine whether the project should preserve, continue, or correct the current state.

## Core Questions
- Should the current baseline be frozen?
- Is more bounded work justified?
- Is recovery required?

## Minimum Outputs
- freeze note or frozen baseline
- extension note
- recovery path
- no-recovery-needed conclusion

## Exit Condition
The project has a clear continuation or preservation path.

---

## 16. Stage 10 — Knowledge Capture

## Purpose
Move validated outputs into the correct long-term locations.

## Core Questions
- What remains project-local?
- What becomes system knowledge?
- What becomes output asset?
- What becomes continuity anchor?
- What becomes archive?

## Minimum Outputs
- updated file placement
- updated MOCs/indexes
- captured baseline assets

## Exit Condition
The project’s current loop is preserved and reusable.

---

## 17. Stage Entry Conditions

A project should not enter a stage without the minimum conditions for that stage.

Examples:
- do not enter capability preparation without sufficient structuring
- do not enter bounded case execution without at least one usable capability
- do not enter freeze decision without review
- do not enter knowledge capture without baseline clarity

This prevents sequence collapse.

---

## 18. Stage Exit Conditions

A stage should not be treated as complete until:
- its minimum outputs exist
- its main questions are answered enough
- review or progression logic supports exit

A stage may be:
- completed
- blocked
- deferred
- revisited
- exited with caution

This allows bounded flexibility without hidden drift.

---

## 19. Stage Failure Modes

The stage model protects against:

### Failure 1 — Stage Collapse
Framing, structuring, execution, and review all blur together.

### Failure 2 — Premature Transition
The project moves into a later stage without enough readiness.

### Failure 3 — Endless Early Stages
The project keeps structuring forever and never executes.

### Failure 4 — Review Skipping
The project moves from execution to continuation without explicit review.

### Failure 5 — Capture Without Stage Closure
Outputs are filed away before the loop is actually complete.

---

## 20. Stage State Indicators

A stage may carry states such as:

- not started
- current
- reviewable
- completed
- blocked
- skipped
- deferred

These indicators help runtime and interface surfaces remain clear.

---

## 21. Human / GPT / Codex Roles in Stage Progression

### Human
- decides major transition approval
- judges stage sufficiency
- controls re-scope decisions

### GPT
- reasons about stage readiness
- recommends transitions
- checks whether stage outputs are sufficient
- identifies premature progression

### Codex
- prepares stage artifacts
- normalizes stage outputs
- updates MOCs and project homes
- automates repetitive stage checks where safe

---

## 22. Final Statement

The AARS Stage Model ensures that project progression occurs through explicit, governed, bounded phases rather than through uncontrolled accumulation of tasks, files, or outputs.