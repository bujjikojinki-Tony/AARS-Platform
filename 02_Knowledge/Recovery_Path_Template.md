---
title: Recovery_Path_Template
type: template
status: draft
project: AARS
tags:
  - aars
  - template
  - recovery
created: 2026-03-31
source: aligned from root template stub and AARS recovery model
---
# Recovery_Path_Template

## 1. Purpose

This template provides the standard structure for recovery paths in AARS.

It is intended to:
- make corrective re-entry explicit
- support safe continuation after degraded states
- reduce vague "fix later" behavior
- preserve revalidation logic

This is a recovery path template.

---

## 2. Recommended File Name

Examples:
- `RECOVERY-CDA-CASE01-01.md`
- `RECOVERY-Pilot_001_CDA-01.md`
- `RECOVERY-AARS-System-01.md`

---

## 3. Template

```md
---
title: 
type: recovery-path
status: draft
project: 
tags: []
created: 
source: 
recovery_id: 
recovery_target: 
linked_stable_view: 
---

# <Recovery Path Title>

## 1. Recovery Identity

**Recovery ID:**  
**Recovery Target:**  
**Project / System:**  
**Current Status:**  

---

## 2. Trigger State

[What degraded, drifted, or became unsafe enough that normal continuation should stop]

---

## 3. Current Degraded Condition

- 
- 
- 

---

## 4. Safe Anchor

[What prior stable anchor still exists and why it can still be trusted]

---

## 5. Recovery Objective

[What valid continuation state the recovery path is trying to restore]

---

## 6. Recovery Sequence

1. 
2. 
3. 
4. 

---

## 7. Revalidation Conditions

- 
- 
- 

---

## 8. Exit Decision

[continue / continue with caution / freeze / archive / stop]

---

## 9. Recommended Next Step

[ ]
```
