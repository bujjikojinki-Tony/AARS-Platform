---
title: AARS_File_Placement_Guide
type: guide
status: draft
project: AARS
tags:
  - aars
  - file-placement
  - guide
created: 2026-03-28
source: ChatGPT
---

# AARS_File_Placement_Guide

## 1. Purpose

This guide defines where different kinds of AARS and CDA files should be placed in the vault/repo structure.

It is intended to:
- reduce placement confusion
- separate project-local files from system-wide files
- improve long-term reuse
- support Codex-based normalization and automation
- preserve a stable relationship between project work, system knowledge, outputs, and archives

This document is a placement guide, not a runtime or governance model.

---

## 2. Core Placement Principle

The core placement principle is:

**place files according to function, not according to when they were written**

This means:
- system-wide reusable knowledge should not be buried inside one pilot project
- project-bound work should not be promoted to core knowledge too early
- frozen or historical materials should not remain mixed with active working files
- guides and MOCs should remain distinct from knowledge kernels and active execution files

---

## 3. Primary Directory Families

The current vault structure is interpreted through the following main families:

### A. `02_Knowledge/`
For reusable system knowledge and stable cross-project knowledge assets.

### B. `03_Projects/`
For bounded project-specific working materials.

### C. `05_Glossary/`
For glossary baselines and terminology assets.

### D. `06_Archive/`
For frozen, historical, or no-longer-active reference materials.

### E. `90_System/Guides/`
For usage guides, operational manuals, and governance prompt handbooks.

### F. `90_System/MOCs/`
For system-level navigation pages and MOCs.

---

## 4. What Belongs in `02_Knowledge/`

Place a file in `02_Knowledge/` when it is:

- reusable beyond one single project
- part of the AARS system definition
- part of the core operating logic
- intended to support future pilots and future domains
- not dependent on one specific CDA-only project context

### Typical File Types
- positioning documents
- execution models
- governance models
- continuity models
- stable view model
- recovery model
- object chain model
- capability lifecycle model
- project model
- bounded case model
- knowledge capture model

### Example Files
- `AARS_System_Positioning.md`
- `AARS_Execution_Model.md`
- `AARS_Object_Chain_Overview.md`
- `AARS_Governance_Model.md`
- `AARS_Runtime_Model.md`
- `AARS_Stable_View_Model.md`
- `AARS_Recovery_Model.md`
- `AARS_Continuity_Model.md`
- `AARS_Capability_Lifecycle_Model.md`
- `AARS_Knowledge_Capture_Model.md`
- `AARS_Project_Model.md`
- `AARS_Bounded_Case_Model.md`

---

## 5. What Belongs in `03_Projects/`

Place a file in `03_Projects/` when it is:

- specific to one active project
- tied to one bounded pilot or domain execution path
- meaningful mainly inside that project boundary
- part of active working progression

### Typical File Types
- project charter
- project home
- working questions
- project concept map
- project layer validation note
- project architecture note
- project roadmap
- project review note
- paper outlines tied to one project

### Example Location
`03_Projects/CDA/Pilot_001_CDA/`

### Example Files
- `Pilot_001_CDA_Project_Charter.md`
- `CDA_Project_Home.md`
- `CDA_Working_Questions.md`
- `CDA_Concept_Map.md`
- `CDA_Layer_Validation_Note.md`
- `CDA_Layered_Architecture.md`
- `CDA_3_Paper_Roadmap.md`
- `Pilot_001_CDA_Review_Note.md`
- `CDA_Paper_1_Outline.md`

---

## 6. What Belongs in `05_Glossary/`

Place a file in `05_Glossary/` when it is primarily a terminology baseline.

### Typical File Types
- glossary baselines
- terminology harmonization documents
- domain term references

### Example Files
- `CDA_Glossary_Baseline.md`

### Rule
Even if a glossary originates inside a project, it may be placed in glossary space if its main function is terminology control rather than local execution.

---

## 7. What Belongs in `06_Archive/`

Place a file in `06_Archive/` when it is:

- frozen
- historical
- inactive but still valuable
- preserved for reference rather than active editing

### Typical File Types
- frozen baseline
- superseded pilot state
- historical review package
- retired reference materials

### Example Files
- `Pilot_001_CDA_Frozen_Baseline.md`

### Rule
Archive does not mean “bad” or “obsolete only.”  
It means “not the active working baseline.”

---

## 8. What Belongs in `90_System/Guides/`

Place a file in `90_System/Guides/` when it is:

- an operational guide
- a user-facing how-to
- a governance checklist
- a prompt handbook
- a file usage guide
- a workflow instruction document

### Typical File Types
- usage guide
- automation operating guide
- self-check prompt handbook
- GPT inventory guide
- file placement guide

### Example Files
- `AARS_Usage_Model.md`
- `AARS_Automation_Operating_Model.md`
- `AARS_Content_Governance_Self_Check_Prompts.md`
- `AARS_Custom_GPT_Inventory.md`
- `AARS_File_Placement_Guide.md`

### Rule
Guides explain how to operate the system, but do not define the system core itself.

---

## 9. What Belongs in `90_System/MOCs/`

Place a file in `90_System/MOCs/` when it is:

- a navigation page
- a system entry page
- a content map
- a system landing page
- a project-of-projects overview

### Typical File Types
- system home
- MOC pages
- major navigation pages

### Example Files
- `AARS_System_Home.md`

### Rule
MOCs should link and orient.  
They should not carry the full system logic themselves.

---

## 10. System Files vs Project Files

This distinction is essential.

### System Files
Ask questions like:
- what is AARS?
- how does AARS execute?
- what is the object chain?
- how does governance work?
- how does continuity work?

These belong in:
- `02_Knowledge/`
- `90_System/Guides/`
- `90_System/MOCs/`

### Project Files
Ask questions like:
- what is Pilot_001_CDA trying to do?
- what is in scope for CDA?
- what are the current project artifacts?
- what is the current CDA roadmap/review/state?

These belong in:
- `03_Projects/...`

---

## 11. Immediate Placement Rules

Use the following immediate rule set.

### Rule 1
If the file is reusable across future projects, place it in `02_Knowledge/`.

### Rule 2
If the file is mainly about one pilot’s active work, place it in `03_Projects/`.

### Rule 3
If the file is mainly terminology control, place it in `05_Glossary/`.

### Rule 4
If the file is a frozen or historical reference state, place it in `06_Archive/`.

### Rule 5
If the file teaches how to use or manage the system, place it in `90_System/Guides/`.

### Rule 6
If the file is primarily for navigation, place it in `90_System/MOCs/`.

---

## 12. Controlled Exceptions

There are a few controlled exceptions.

### Exception A — Project-Origin Glossary
A glossary may originate inside a project, but still be placed in `05_Glossary/` if its primary function is vocabulary control.

### Exception B — Project-Origin Review Becoming Archive
A project review note may begin in `03_Projects/`, but a frozen or superseded version may later move to `06_Archive/`.

### Exception C — Project-Origin Concept Becoming System Knowledge
A project-origin concept note should only move into `02_Knowledge/` if it becomes genuinely reusable beyond the original project.

---

## 13. Current Recommended Placement Map

### `02_Knowledge/`
- `AARS_System_Positioning.md`
- `AARS_Execution_Model.md`
- `AARS_Object_Chain_Overview.md`
- `AARS_Governance_Model.md`
- `AARS_Runtime_Model.md`
- `AARS_Stable_View_Model.md`
- `AARS_Recovery_Model.md`
- `AARS_Continuity_Model.md`
- `AARS_Capability_Lifecycle_Model.md`
- `AARS_Knowledge_Capture_Model.md`
- `AARS_Project_Model.md`
- `AARS_Bounded_Case_Model.md`

### `03_Projects/CDA/Pilot_001_CDA/`
- `Pilot_001_CDA_Project_Charter.md`
- `CDA_Project_Home.md`
- `CDA_Working_Questions.md`
- `CDA_Concept_Map.md`
- `CDA_Layer_Validation_Note.md`
- `CDA_Layered_Architecture.md`
- `CDA_3_Paper_Roadmap.md`
- `Pilot_001_CDA_Review_Note.md`
- `CDA_Paper_1_Outline.md`

### `05_Glossary/`
- `CDA_Glossary_Baseline.md`

### `06_Archive/`
- `Pilot_001_CDA_Frozen_Baseline.md`

### `90_System/Guides/`
- `AARS_Usage_Model.md`
- `AARS_Automation_Operating_Model.md`
- `AARS_Content_Governance_Self_Check_Prompts.md`
- `AARS_Custom_GPT_Inventory.md`
- `AARS_File_Placement_Guide.md`

### `90_System/MOCs/`
- `AARS_System_Home.md`

---

## 14. Future Directory Refinement

When the system grows, the following directories may later be added:

### Under `02_Knowledge/`
- `Concepts/`
- `Schemas/`
- `Templates/`
- `Kernels/`

### Under `05_Outputs/`
- `Roadmaps/`
- `Reviews/`
- `Submission_Packs/`

At the current stage, this refinement is optional, not mandatory.

---

## 15. Placement Failure Modes

This guide protects against several placement failures.

### Failure 1 — Project/Knowledge Collapse
Project-local material is incorrectly treated as reusable system knowledge.

### Failure 2 — System Buried in Projects
AARS-wide logic becomes trapped inside one pilot directory.

### Failure 3 — Frozen/Active Confusion
Frozen baselines remain mixed with active working files.

### Failure 4 — Guide/Kernel Confusion
Operational guides are mistaken for system core definitions.

### Failure 5 — Navigation/Logic Confusion
MOCs begin carrying too much system logic instead of linking to it.

---

## 16. Final Statement

AARS file placement should always reflect functional role, reuse scope, and governance status rather than writing chronology.

That is how the vault remains scalable, navigable, and system-consistent.