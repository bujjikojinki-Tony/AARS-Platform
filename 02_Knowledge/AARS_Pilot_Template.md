---
title: AARS_Pilot_Template
type: template
status: draft
project: AARS
tags:
  - aars
  - pilot
  - template
created: 2026-03-28
source: ChatGPT
---

# AARS_Pilot_Template

## 1. Purpose

This template provides the standard starting structure for an AARS pilot.

It is intended to:
- standardize how pilots are opened
- make pilot scope explicitly bounded
- ensure pilots are designed as validation loops rather than open-ended studies
- support cross-pilot comparison and reuse
- accelerate setup of new domain pilots

This is a pilot template, not a filled pilot file.

---

## 2. Use Rule

Use this template when the work is intended to:
- validate AARS in a real bounded case
- test a new domain inside AARS
- migrate a legacy domain/system into AARS
- produce an operational proof loop
- generate a freeze-worthy baseline

If the work is not primarily a bounded validation loop, use `AARS_Project_Template.md` instead.

---

## 3. Recommended File Name

Typical names include:
- `Pilot_001_<Domain>_Project_Charter.md`
- `Pilot_002_<Domain>_Project_Charter.md`

If possible, always include:
- pilot number
- domain identifier
- charter role

---

## 4. Pilot Template

### Copy from here

```md id="pi4j0z"
---
title: 
type: project-note
status: draft
project: 
tags: []
created: 
source: 
---

# <Pilot Title>

## 1. Pilot Identity

**Pilot ID:**  
**Pilot Name:**  
**Pilot Type:** bounded validation pilot  
**System Context:** AARS  
**Primary Domain:**  
**Current Status:**  

---

## 2. Pilot Intent

### Core Intent
[What this pilot is intended to validate]

### Why This Pilot Exists
[Why AARS needs this bounded validation case]

### Pilot Framing
[This is a migration pilot / domain pilot / system pilot / operational proof pilot / comparative pilot]

---

## 3. Problem Statement

[What gap or uncertainty this pilot is intended to resolve]

---

## 4. Goal Definition

### Primary Goal
[Main validation goal]

### Secondary Goals
1. 
2. 
3. 

### Non-Goals
- 
- 
- 

---

## 5. Goal Type

**Primary Goal Type:**  
**Secondary Goal Types:**  

---

## 6. Track Selection

**Primary Track:**  
**Secondary Tracks:**  
**Deferred Tracks:**  

---

## 7. Pilot Scope

### In Scope
- 
- 
- 

### Out of Scope
- 
- 
- 

### Scope Boundary Rule
[How this pilot will remain bounded]

---

## 8. Validation Focus

This pilot is intended to validate whether:
1. 
2. 
3. 

---

## 9. Minimum Success Criteria

The pilot is successful when:
1. 
2. 
3. 
4. 

---

## 10. Minimum Deliverables

1. 
2. 
3. 
4. 
5. 

---

## 11. Capability Expectations

### Candidate Capability Family
1. 
2. 
3. 

### Minimum Capability Requirement
[How many capabilities must be formalized or exercised]

---

## 12. Bounded Case Requirement

### Minimum Case Requirement
The pilot must include at least one bounded case that produces:
- one invocation record
- one dependency object
- one risk object
- one health snapshot
- one stable-view update
- one recovery / no-recovery conclusion

### Why
[Explain why the pilot must include operational proof]

---

## 13. Risks

### Risk 1
[ ]

### Risk 2
[ ]

### Risk 3
[ ]

---

## 14. Risk Mitigation Principles

- 
- 
- 

---

## 15. Review Questions

1. Has the pilot remained bounded?
2. Has the pilot actually produced operational proof?
3. Are the outputs reusable?
4. Is the current state stable enough to freeze or extend?
5. What should happen next?

---

## 16. Expected Progression Sequence

1. Project Framing  
2. Discovery / Mapping / Structuring  
3. Capability Preparation  
4. Bounded Case Execution  
5. Review and Stabilization  
6. Freeze / Extend / Recover Decision  
7. Knowledge Capture  

---

## 17. Immediate Next Step

[The first concrete next action]

---

## 18. Closing Statement

[Short bounded summary of what this pilot is supposed to prove]