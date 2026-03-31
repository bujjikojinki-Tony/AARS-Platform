---
title: AARS_Directory_Architecture_Guide
type: guide
status: draft
project: AARS
tags:
  - aars
  - directory
  - architecture
  - guide
created: 2026-03-28
source: ChatGPT
---

# AARS_Directory_Architecture_Guide

## 1. Purpose

This guide defines the directory architecture of the AARS vault/repo.

It is intended to:
- explain why the directory structure exists in its current layered form
- define how files should be grouped across knowledge, projects, outputs, glossary, archive, and system guidance
- support future growth without structural drift
- make Codex-based normalization easier
- preserve human readability in Obsidian

This is a directory-architecture guide, not a runtime model.

---

## 2. Core Principle

The core principle is:

**directories should reflect functional role, governance status, and reuse scope**

This means:
- system core files should not be buried in project folders
- project-local files should not be promoted too early into reusable knowledge
- guides should not be mixed with models
- archive should not be confused with active baselines
- navigation pages should remain distinct from system logic files

---

## 3. Main Directory Families

The AARS directory architecture should be understood through the following main families:

### 3.1 Knowledge Layer
`02_Knowledge/`

### 3.2 Project Layer
`03_Projects/`

### 3.3 Glossary Layer
`05_Glossary/`

### 3.4 Output Layer
`05_Outputs/` (if used)

### 3.5 Archive Layer
`06_Archive/`

### 3.6 System Operations Layer
`90_System/Guides/`

### 3.7 System Navigation Layer
`90_System/MOCs/`

These families are not arbitrary.  
They represent different governance roles.

---

## 4. `02_Knowledge/` — Knowledge Layer

## Role
Stores reusable system knowledge and cross-project knowledge assets.

## Suitable Content
- system models
- execution logic
- governance logic
- object chain logic
- stage / goal / track models
- stable view / recovery / continuity models
- knowledge-tiering and capture models
- reusable templates if not yet split into a separate template folder

## Unsuitable Content
- active project-only notes
- one-off project review logs
- current case-local working notes
- navigation-only pages

## Meaning
This is the main reusable system knowledge layer.

---

## 5. `03_Projects/` — Project Layer

## Role
Stores bounded project-local execution materials.

## Suitable Content
- project charter
- project home
- working questions
- local concept map
- local taxonomy if still project-bound
- project architecture note
- project roadmap
- project review note
- project paper outline
- project stable view and continuity notes if they are local

## Unsuitable Content
- general AARS system models
- system-wide guides
- long-term archive states unless still active

## Meaning
This is the local work container layer.

---

## 6. `05_Glossary/` — Glossary Layer

## Role
Stores terminology baselines.

## Suitable Content
- glossary baselines
- domain term stabilization files
- system glossary if you later create one

## Unsuitable Content
- project review notes
- concept maps
- methodology notes unless purely terminology-oriented

## Meaning
This is the vocabulary control layer.

---

## 7. `05_Outputs/` — Output Layer

## Role
Stores milestone-oriented outputs and packaging-oriented artifacts.

## Suitable Content
- roadmaps
- report packages
- paper packages
- submission drafts
- final output bundles

## Unsuitable Content
- system models
- live local project notes
- archive materials

## Meaning
This is the deliverable layer.

### Note
If `05_Outputs/` is not yet active, output files may temporarily remain inside project folders until the output layer is worth separating.

---

## 8. `06_Archive/` — Archive Layer

## Role
Stores historical, frozen, superseded, or inactive but still meaningful materials.

## Suitable Content
- frozen pilot baselines no longer active
- superseded versions
- historical reviews
- retired models
- archived project states

## Unsuitable Content
- active latest stable view
- still-current baseline
- active working project files

## Meaning
This is the historical memory layer.

---

## 9. `90_System/Guides/` — System Operations Layer

## Role
Stores operational guides, checklists, and file-use rules.

## Suitable Content
- usage guide
- automation guide
- file placement guide
- directory architecture guide
- latest stable view operating guide
- review checklist
- freeze checklist
- naming rules
- project operating guide

## Unsuitable Content
- system core models
- project-local execution files
- MOC entry pages

## Meaning
This is the human-operating layer of the system.

---

## 10. `90_System/MOCs/` — System Navigation Layer

## Role
Stores system-level MOCs and entry pages.

## Suitable Content
- system home
- domain family entry pages
- top-level navigation hubs

## Unsuitable Content
- full system model definitions
- long-form guides
- active project-local notes

## Meaning
This is the navigation layer.

---

## 11. Recommended Current AARS Structure

A practical current AARS structure may look like this:

```text id="ndjblk"
02_Knowledge/
  AARS_System_Positioning.md
  AARS_Execution_Model.md
  AARS_Object_Chain_Overview.md
  AARS_Governance_Model.md
  AARS_Runtime_Model.md
  AARS_Stable_View_Model.md
  AARS_Recovery_Model.md
  AARS_Continuity_Model.md
  AARS_Capability_Lifecycle_Model.md
  AARS_Knowledge_Capture_Model.md
  AARS_Project_Model.md
  AARS_Bounded_Case_Model.md
  AARS_Review_Model.md
  AARS_Freeze_Model.md
  AARS_Archive_Model.md
  AARS_Baseline_Model.md
  AARS_Stage_Model.md
  AARS_Goal_Model.md
  AARS_Track_Model.md
  AARS_Object_Status_Model.md
  AARS_Next_Step_Decision_Model.md
  AARS_Project_Template.md
  AARS_Pilot_Template.md
  AARS_Knowledge_Tiering_Model.md

03_Projects/
  CDA/
    Pilot_001_CDA/
      ...

05_Glossary/
  CDA_Glossary_Baseline.md

06_Archive/
  Pilot_001_CDA_Frozen_Baseline.md

90_System/
  Guides/
    ...
  MOCs/
    AARS_System_Home.md