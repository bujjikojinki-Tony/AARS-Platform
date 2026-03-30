---
title: AARS_Next_Step_Decision_Model
type: spec
status: draft
project: AARS
tags:
  - aars
  - next-step
  - decision
  - model
created: 2026-03-28
source: ChatGPT
---

# AARS_Next_Step_Decision_Model

## 1. Purpose

This document defines the next-step decision model of AARS.

It explains:
- how AARS determines what should happen next
- how next-step decisions differ from generic suggestions
- what inputs are required before a next-step decision is valid
- how next-step recommendations should remain bounded and governed
- how next-step logic connects review, stable view, recovery, and project progression

This is the bounded continuation-decision model of AARS.

---

## 2. Core Definition

A next-step decision in AARS is:

**an explicit bounded judgment about the most admissible immediate continuation action given the current project state, object state, review state, and stable continuation anchor.**

A next-step decision is not:
- a random idea
- a brainstorming list
- a broad future roadmap
- a generic “we could also do X”
- an unconstrained expansion impulse

A next-step decision must be:
- bounded
- justified
- state-aware
- governance-aware

---

## 3. Core Principle

The core principle is:

**the next step should be the most admissible step, not the most ambitious step**

This means AARS should prefer:
- controllable continuation
- continuity-preserving movement
- review-consistent progression
- bounded operational value

over:
- largest expansion
- most exciting branch
- most polished-looking output
- premature totalization

---

## 4. Why the Next-Step Model Matters

This model matters because without it:
- projects drift after review
- stable view does not guide action
- users move by momentum instead of governance
- “what next?” becomes arbitrary
- automation becomes noisy
- projects over-expand too early

AARS needs explicit next-step logic because continuation is one of its core control points.

---

## 5. Next Step vs Related Concepts

## 5.1 Next Step vs Roadmap

### Roadmap
Defines medium- or longer-horizon pathways.

### Next Step
Defines the most appropriate immediate bounded continuation action.

### Difference
Roadmap is strategic sequence.  
Next step is operational continuation.

---

## 5.2 Next Step vs Task

### Task
A local action item.

### Next Step
A governance judgment about what immediate bounded action should happen next.

### Difference
A next-step decision may generate one or more tasks, but it is not merely a task label.

---

## 5.3 Next Step vs Goal

### Goal
Defines intended project outcome.

### Next Step
Defines the most appropriate immediate move toward or around that goal.

### Difference
Goal gives direction.  
Next step gives immediate admissible movement.

---

## 6. Inputs Required for a Valid Next-Step Decision

A valid next-step decision should consider, at minimum:

1. current project goal  
2. current stage  
3. current track  
4. current object status  
5. current health state  
6. latest stable view  
7. latest review judgment  
8. unresolved blockers or drift conditions  

Without these, next-step logic is weak.

---

## 7. Primary Next-Step Decision Types

AARS should recognize several classes of next-step decisions:

1. Continue Current Track  
2. Enter Review  
3. Stabilize Before Continue  
4. Freeze Current Baseline  
5. Recover Before Continue  
6. Extend to Next Loop  
7. Capture Before Further Expansion  

These are not equal in meaning.

---

## 8. Continue Current Track

## Meaning
The current line of work remains admissible and should continue in bounded form.

## Use When
- scope remains valid
- current track still fits the goal
- no major recovery is needed
- health is acceptable
- stable view supports continuation

## Typical Example
Continue capability formalization or continue bounded case execution.

---

## 9. Enter Review

## Meaning
Further continuation should pause until structured review is performed.

## Use When
- uncertainty is high
- outputs are meaningful but not yet sufficiently judged
- object status is reviewable but not stable
- next move cannot be justified without evaluation

## Typical Example
A first bounded case completed, but its adequacy is still uncertain.

---

## 10. Stabilize Before Continue

## Meaning
The project should remain on the same general path, but first strengthen current structure.

## Use When
- terminology is drifting
- taxonomy is weak
- evidence is too thin
- object quality is uneven
- continuation is possible only if stronger local coherence is built first

## Typical Example
Do second-pass strengthening of risk/control notes before opening a new case.

---

## 11. Freeze Current Baseline

## Meaning
The current state is good enough to preserve before additional movement.

## Use When
- a bounded loop is complete
- current stable view is strong
- more revision would create churn
- future work should inherit this baseline

## Typical Example
Freeze the first successful pilot baseline.

---

## 12. Recover Before Continue

## Meaning
Continuation is currently not safe enough, so bounded corrective action is required first.

## Use When
- health is degraded or blocked
- stable view is weak or lost
- scope drift is material
- contradictions are unresolved
- object-chain integrity is broken

## Typical Example
Recover the project boundary after over-expansion.

---

## 13. Extend to Next Loop

## Meaning
The current bounded loop is complete, and the project should open a new bounded execution loop.

## Use When
- one loop has closed well
- the current baseline is strong enough
- a new bounded case or branch is justified
- continuity is clear

## Typical Example
After freezing a pilot baseline, begin Paper 1 or start a second bounded case.

---

## 14. Capture Before Further Expansion

## Meaning
The system should capture and place current assets correctly before continuing outward.

## Use When
- important outputs exist but are not yet well placed
- MOCs / indexes are stale
- glossary/taxonomy baselines are not yet anchored
- continuity value may be lost if work expands first

## Typical Example
Update vault placement and indexes before starting the next domain branch.

---

## 15. Decision Selection Logic

AARS should select next-step type by asking:

1. Is continuation admissible right now?
2. Is review required first?
3. Is current structure strong enough?
4. Is freeze more valuable than immediate expansion?
5. Is recovery needed?
6. Is current knowledge captured enough to support the next move?

The answer to these questions determines the next-step class.

---

## 16. Next-Step Readiness Conditions

A next-step decision should only be issued when:
- the current state is interpretable
- the stable view is known or explicitly absent
- unresolved issues are visible
- current stage is identified
- there is enough evidence to justify a bounded move

Otherwise the correct next-step decision may simply be:
**review first**.

---

## 17. Next-Step Output Structure

A good next-step output should usually include:

- decision type
- bounded action statement
- rationale
- what not to do next
- prerequisite conditions
- expected artifact or outcome

This prevents vague next-step language.

---

## 18. Example Next-Step Form

A next-step recommendation should ideally look like:

### Decision
Stabilize Before Continue

### Why
Risk object and control note are meaningful but still only reviewable / conditionally stable.

### Bound
Do not open a new case yet.

### Required Action
Strengthen risk evidence and control grouping.

### Expected Output
Second-pass risk note, second-pass control note, updated review judgment.

This is stronger than saying:
“Maybe refine the analysis.”

---

## 19. What Not to Do in Next-Step Logic

AARS should avoid:

- giving too many equal-priority next steps
- suggesting expansion before baseline clarity
- recommending packaging while execution is still weak
- giving next-step suggestions unrelated to current stage
- proposing new work that breaks project scope

A next-step decision should narrow action, not multiply it.

---

## 20. Next Step and Stable View

Stable view is one of the strongest inputs to next-step logic.

### Rule
The next step should usually be chosen from the current latest stable view, not from the newest unstable output.

This is what makes next-step logic continuity-aware.

---

## 21. Next Step and Review

Review frequently determines next-step state.

Typical review outcomes map like this:

- Review Required → enter review
- Continue With Caution → continue current track or stabilize first
- Closure Allowed → freeze, capture, or extend
- Recover Before Continue → recovery path required

Thus next-step logic should often be review-derived.

---

## 22. Next Step Failure Modes

The model protects against:

### Failure 1 — Ambition Bias
Choosing the largest or most exciting next move rather than the safest one.

### Failure 2 — Expansion Drift
Opening new branches before the current loop is governed enough.

### Failure 3 — Packaging Drift
Jumping to paper drafting or reporting before operational proof is sufficient.

### Failure 4 — Multi-Step Confusion
Giving too many equally emphasized next steps so that no real bounded next step exists.

### Failure 5 — Continuity Ignorance
Choosing next steps without reference to stable view, review, or health.

---

## 23. Human / GPT / Codex Roles in Next-Step Decisions

### Human
- approves major branching, freeze, and recovery choices
- judges strategic tradeoffs
- decides when re-framing is needed

### GPT
- reasons about admissibility
- recommends bounded next-step type
- explains why some next steps are premature
- synthesizes review into actionable continuation logic

### Codex
- prepares the artifacts needed for the chosen next step
- updates project home, indexes, and file structures
- automates bounded normalization after decision

---

## 24. Final Statement

The AARS Next-Step Decision Model ensures that continuation happens through bounded, state-aware, governance-consistent decisions rather than through momentum, output volume, or arbitrary expansion.