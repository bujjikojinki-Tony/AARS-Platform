---
title: AARS_System_Freeze_Decision_Note_Template
type: template
status: draft
project: AARS
tags:
  - aars
  - freeze
  - decision-note
  - template
created: 2026-03-28
source: ChatGPT
---

# AARS_System_Freeze_Decision_Note_Template

## 1. Purpose

This template provides the standard structure for recording a system-level freeze decision in AARS.

It is intended to:
- explicitly record why a system round or baseline is being frozen
- preserve the decision logic behind the freeze
- distinguish a frozen system baseline from active working state
- support future inheritance and later archive decisions

This is a system freeze decision template.

---

## 2. Recommended File Name

Examples:
- `AARS_System_Freeze_Decision_v0_1.md`
- `AARS_Round_01_Freeze_Decision_Note.md`
- `AARS_Production_Readiness_Phase_1_Freeze_Decision.md`

---

## 3. Template

```md id="gc6f1n"
---
title: 
type: freeze-decision-note
status: draft
project: AARS
tags: []
created: 
source: 
freeze_decision_id: 
freeze_scope: 
---

# <System Freeze Decision Note Title>

## 1. Freeze Decision Identity

**Freeze Decision ID:**  
**Freeze Scope:**  
**Round / Baseline:**  
**Current Status:**  

---

## 2. Freeze Target

[What system round, baseline, or release state is being frozen]

---

## 3. Why Freeze Is Being Considered

[What bounded reason justifies preservation]

---

## 4. What Is Strong Enough

1.  
2.  
3.  
4.  
5.  

---

## 5. What Remains Incomplete but Acceptable

1.  
2.  
3.  

---

## 6. Current Stable Anchor

[What stable anchor supports the freeze decision]

---

## 7. Freeze Judgment

[Freeze Recommended / Freeze Approved / Extend Before Freeze / Recover Before Freeze]

---

## 8. Why This Judgment Was Made

- 
- 
- 

---

## 9. Inheritance Guidance

[What future work should inherit from this frozen system state]

---

## 10. Related Artifacts

- baseline release note
- production readiness review note
- round closure note
- change log
- latest stable view

---

## 11. Recommended Next Step

[ ]

---

## 12. Closing Note

[Short bounded summary of what freezing this system round means]