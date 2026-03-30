---
title: AARS_Knowledge_Capture_Model
type: spec
status: draft
project: AARS
tags:
  - aars
  - knowledge
  - capture
  - model
created: 2026-03-28
source: ChatGPT
---

# AARS_Knowledge_Capture_Model

## 1. Purpose

This document defines the knowledge capture model of AARS.

It explains:
- what kinds of outputs should be captured
- when work is ready to be captured
- where different kinds of artifacts should go
- how capture relates to stable view, review, freeze, and archive
- how AARS preserves reusable knowledge without collapsing process and content

This is a knowledge-governance model, not just a filing guide.

---

## 2. Core Definition

Knowledge capture in AARS means:

**the structured preservation of validated or sufficiently reusable work into stable knowledge assets, project assets, continuity assets, or archive assets.**

Knowledge capture is not:
- saving everything
- storing all drafts equally
- moving files without judgment
- converting all process artifacts into permanent knowledge

Knowledge capture requires governed selection.

---

## 3. Core Principle

The core principle is:

**capture what is reusable, anchored, and structurally meaningful**

This means AARS should capture:
- validated concepts
- stable terminology
- bounded methods
- reusable object patterns
- accepted baselines
- meaningful continuity anchors

It should not capture every unstable intermediate state as if it were equal to stable knowledge.

---

## 4. Why Knowledge Capture Matters

Knowledge capture is necessary because otherwise:
- bounded work disappears into conversation history
- structured reasoning must be recreated repeatedly
- stable outputs get mixed with temporary drafts
- future projects lose continuity with past validated work
- the system cannot accumulate durable knowledge

Knowledge capture is how AARS becomes cumulative.

---

## 5. Main Capture Classes

AARS should distinguish at least five capture classes:

1. Core Knowledge Assets  
2. Project Assets  
3. Output Assets  
4. Continuity Assets  
5. Archive Assets  

Each class should be captured differently.

---

## 6. Core Knowledge Assets

## Definition
Stable or broadly reusable content that should support future work beyond one single project loop.

## Typical Examples
- glossary baseline
- taxonomy baseline
- core concepts
- kernels
- schemas
- templates
- system models
- methodology principles

## Capture Rule
Only capture into core knowledge when the content has:
- stable meaning
- cross-case or cross-project reuse value
- bounded enough structure to survive outside its original conversation

## Typical Destination
- `02_Knowledge/`
- glossary directories
- schema directories
- guide directories

---

## 7. Project Assets

## Definition
Artifacts that belong primarily to a specific project.

## Typical Examples
- project charter
- project home
- working questions
- project review note
- pilot-specific concept map
- bounded architecture note

## Capture Rule
Capture as project assets when the content is useful mainly inside the project boundary.

## Typical Destination
- `03_Projects/...`

Project assets may later produce core knowledge, but are not automatically core knowledge themselves.

---

## 8. Output Assets

## Definition
Artifacts produced as stage deliverables or milestone outputs.

## Typical Examples
- roadmap
- paper outline
- review package
- submission checklist
- structured reports
- migration report

## Capture Rule
Capture as output assets when the artifact records a stage result rather than timeless knowledge.

## Typical Destination
- `05_Outputs/...`

---

## 9. Continuity Assets

## Definition
Artifacts that preserve safe continuation logic.

## Typical Examples
- continuity log
- health snapshot
- latest stable view
- freeze note
- recovery path
- no-recovery-needed conclusion

## Capture Rule
Capture continuity assets whenever the system needs to preserve:
- a safe anchor
- a reviewable state
- a recovery route
- a future resume point

## Typical Destination
- project directory
- system continuity area
- freeze note directory

Continuity assets are essential even if they are not “knowledge articles” in the traditional sense.

---

## 10. Archive Assets

## Definition
Artifacts preserved for historical traceability rather than immediate operational reuse.

## Typical Examples
- superseded baselines
- old drafts
- retired models
- historical reviews
- obsolete structures
- frozen past states no longer active

## Capture Rule
Archive when:
- the artifact is no longer active
- it still has reference value
- it should not be confused with the current stable baseline

## Typical Destination
- `06_Archive/`

---

## 11. Capture Entry Conditions

An artifact should only be captured when at least one of the following is true:

1. it is sufficiently stable
2. it is reusable
3. it is required for continuity
4. it records a key project decision
5. it represents a meaningful output milestone
6. it preserves a review or freeze state
7. it is historically valuable enough to archive

If none of these are true, it may remain working material rather than captured knowledge.

---

## 12. Capture Non-Entry Conditions

An artifact should not yet be captured as stable knowledge when:

- it is still materially contradictory
- its terminology is unstable
- it is purely conversational residue
- it duplicates stronger existing assets
- it is useful only for immediate scratch work
- it has not yet passed minimal review for its intended class

This prevents capture inflation.

---

## 13. Capture and Stable View

Stable view is one of the main triggers for capture.

### Rule
If a state becomes the latest stable view, AARS should assess whether:
- it should remain only as continuity anchor
- it should also be captured as project knowledge
- it should be frozen as a reusable baseline

Stable view therefore often precedes knowledge capture.

---

## 14. Capture and Freeze

Freeze strengthens capture.

### When Freeze Happens
- bounded loop is complete
- stable baseline exists
- later work should inherit the baseline
- churn should be reduced

### Capture Role
A frozen baseline is a special captured asset:
- stable
- preserved
- explicitly reusable
- protected from casual rewriting

---

## 15. Capture and Review

Review should shape capture decisions.

### Review Questions
- Is this artifact stable enough?
- Is it only project-bound?
- Is it reusable across work?
- Is it better placed in project, knowledge, or archive?
- Should it remain reviewable instead of stable?

AARS should not capture blindly based on file existence alone.

---

## 16. Capture and Object Chain

Not every object-chain artifact becomes core knowledge.

### Typical Rule
- capability objects may become reusable knowledge assets
- invocation records usually remain project/case assets
- dependency/risk/health objects usually remain project or output assets unless generalized
- latest stable view and freeze notes become continuity assets
- particularly reusable patterns may later be abstracted into templates

This protects AARS from treating every runtime object as permanent system knowledge.

---

## 17. Capture and Directory Logic

AARS should use directory placement as a reflection of knowledge status.

### Typical Mapping

#### Core Knowledge
- `02_Knowledge/`

#### Project Work
- `03_Projects/...`

#### Output Milestones
- `05_Outputs/...`

#### Archive
- `06_Archive/`

#### System Navigation / Guides
- `90_System/...`

Directory placement is part of the knowledge capture model, not only repository hygiene.

---

## 18. Capture Failure Modes

The knowledge capture model protects against:

### Failure 1 — Capture Inflation
Too many weak artifacts are preserved as if they were stable knowledge.

### Failure 2 — Project/Knowledge Collapse
Project-specific files are treated as global reusable knowledge without justification.

### Failure 3 — Continuity Loss
Stable anchors are not captured, making resumption harder.

### Failure 4 — Archive Neglect
Old but important reference states are lost or overwritten.

### Failure 5 — Duplicate Capture
The same logic is repeatedly preserved in multiple conflicting files.

### Failure 6 — Premature Stabilization
Unstable drafts are captured into core knowledge too early.

---

## 19. Capture Decision Questions

When deciding capture destination, AARS should ask:

1. Is this reusable beyond the current project?
2. Is this mainly a project-working artifact?
3. Is this a milestone output?
4. Is this a continuity anchor?
5. Is this historical rather than active?
6. Is this stable enough for its intended destination?

These questions are more important than file naming alone.

---

## 20. Capture in Current Practical Stack

In the current AARS practical stack:

### ChatGPT
supports capture judgment and artifact classification

### Codex
supports file creation, normalization, and destination routing

### Obsidian
holds the persistent Markdown knowledge structure

### GitHub
preserves captured history, rollback, and branching continuity

This means knowledge capture is already partially operational.

---

## 21. Final Statement

The AARS Knowledge Capture Model ensures that validated work becomes durable, reusable, and properly classified knowledge rather than being lost in transient execution or mixed indiscriminately across project, output, continuity, and archive layers.