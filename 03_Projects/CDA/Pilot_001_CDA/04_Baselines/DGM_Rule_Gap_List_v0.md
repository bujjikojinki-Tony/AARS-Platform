---
title: DGM_Rule_Gap_List_v0
doc_type: rule_gap_list
project: Pilot_001_CDA
domain: nuclear_design_construction
case_id: CASE-NPP-DGM-01
version: v0
status: reviewable
stability: gap_identification_baseline
aars_step: objectized_case_execution
scope_type: bounded_case
tags:
  - AARS
  - CDA
  - DGM
  - rule-gap
  - nuclear
  - baseline
---

## Links
- Home: [[Pilot_001_CDA_Home]]
- MOC: [[DGM_CASE_NPP_01_MOC]]
- Rule Validation: [[../03_Reviews/DGM_Rule_Validation_Note_v0]]
- Second Round Completion: [[../03_Reviews/DGM_Second_Round_Completion_Note_v0]]
- Evidence Granularity: [[DGM_Evidence_Granularity_Note_v0]]
- Disposition Transition: [[DGM_Disposition_Transition_Rulebook_v0]]
- Evidence Requirement: [[DGM_Evidence_Requirement_Note_v0]]
- Disposition Framework: [[DGM_Governance_Disposition_Framework_v0]]
- Propagation Note: [[DGM_Propagation_Pattern_Note_v0]]
- Impact Matrix: [[DGM_Impact_Object_Matrix_v0]]

# DGM_Rule_Gap_List_v0

## Position
本文件用于识别 `CASE-NPP-DGM-01` 在第二轮有界深化完成后仍然存在的关键规则缺口。  
它不新增规则，而是明确：
- 哪些 gaps 已经被看见
- 哪些 gaps 会影响当前规则的防误判能力
- 哪些 gaps 必须优先压缩
- 哪些 gaps 仍可保持 reviewable

---

## Current Objective
回答以下问题：

1. 当前 rule-strengthened baseline 里，最重要的缺口是什么  
2. 哪些缺口会直接影响 evidence threshold 或 disposition transition 的稳定性  
3. 哪些缺口是当前最值得优先压缩的 P1 gaps  
4. 哪些缺口可以保留到后续轮次再处理  

---

## Scope

### In Scope
- evidence granularity gaps
- consequence confirmation gaps
- QA / inspection relevance gaps
- conflicting evidence precedence gaps
- transition timing gaps
- re-entry discipline gaps

### Out of Scope
- second case comparison gaps
- platform implementation gaps
- full lifecycle methodology gaps
- generic enterprise governance gaps

---

## 1. Gap Identification Rules

### Rule 1
只有会影响当前单场景规则稳定性的缺口，才进入本 list。

### Rule 2
gap 必须能被明确表述为“当前规则哪里还不够紧”，而不是泛泛说“未来还可完善”。

### Rule 3
P1 gap 指会直接影响强结论升级/降级纪律的缺口。

### Rule 4
P2 gap 指会影响解释力或维护性，但暂不破坏主判断链的缺口。

### Rule 5
P3 gap 指当前已知但仍可保持 reviewable 的边缘缺口。

---

## 2. P1 Rule Gaps

### P1-Gap-01
#### Name
G5 Consequence-Specific Evidence Minimum Threshold Gap

#### Description
当前已定义 G5 consequence-specific evidence，但“最小到什么程度才算足够确认 construction-relevant impact”仍偏粗。

#### Why It Matters
如果 G5 门槛过松，construction-relevant impact 会被过快确认。

#### Current Risk
- consequence claim upgrade too early
- package relevance 被误写成 confirmed consequence
- QA relevance 被带着一起误升级

#### Current Judgment
**P1 / must compress**

---

### P1-Gap-02
#### Name
QA / Inspection Relevance Confirmation Gap

#### Description
当前 QA / inspection record 相关 disposition 仍偏 reviewable，缺少更细的确认条件。

#### Why It Matters
QA / inspection 是当前场景最容易被“泛化写强”的后果域之一。

#### Current Risk
- generic QA relevance 被误写成 confirmed action input
- review-required QA signal 被误升级

#### Current Judgment
**P1 / must compress**

---

### P1-Gap-03
#### Name
Conflicting Evidence Precedence Gap

#### Description
当不同 evidence 指向不同判断时，当前尚无明确 precedence 规则。

#### Why It Matters
如果没有 precedence，规则会在冲突情况下退回主观判断。

#### Current Risk
- stronger source + weaker consequence 组合被误解释
- narrative confidence override evidence discipline
- downgrade timing inconsistent

#### Current Judgment
**P1 / must compress**

---

### P1-Gap-04
#### Name
Acceptance Evidence Loss Response Gap

#### Description
当前已规定 G6 缺失会触发 review，但“丢失到什么程度、何时立即回退”仍可更细。

#### Why It Matters
G6 是 confirmed action 的最后门槛，若响应不清，会削弱整个 disposition transition 体系。

#### Current Risk
- confirmed action 维持过久
- action status 回退不及时
- review trigger 粒度不一致

#### Current Judgment
**P1 / must compress**

---

## 3. P2 Rule Gaps

### P2-Gap-01
#### Name
Transition Timing Discipline Gap

#### Description
当前已定义升级/降级条件，但“何时立即转移、何时暂缓转移”仍未单独定义。

#### Why It Matters
它影响状态切换的一致性，但不一定立即破坏主链。

#### Current Judgment
**P2 / should compress later**

---

### P2-Gap-02
#### Name
Installation Sequence Confirmation Gap

#### Description
installation sequence object 的 consequence relevance 已被纳入，但确认门槛仍偏粗。

#### Why It Matters
它影响 construction handoff 的细度，但当前仍可暂时保持 reviewable。

#### Current Judgment
**P2 / should compress later**

---

### P2-Gap-03
#### Name
Evidence Bundle Conflict Resolution Gap

#### Description
当前已定义 valid/invalid bundles，但多个 bundle 相互矛盾时的处理规则还不够细。

#### Why It Matters
它与 precedence gap 相关，但更偏 bundle handling 细化。

#### Current Judgment
**P2 / linked to P1-Gap-03**

---

## 4. P3 Rule Gaps

### P3-Gap-01
#### Name
Outer-Scope Re-entry Strictness Gap

#### Description
当前已定义 out-of-scope re-entry，但其最小 bounded linkage 还可更严格。

#### Why It Matters
会影响边界纪律，但当前仍未成为主链不稳定来源。

#### Current Judgment
**P3 / reviewable**

---

### P3-Gap-02
#### Name
Historical Similar-Case Evidence Use Gap

#### Description
历史相似变更证据是否可作为 bounded support bundle 成员，目前还未明确。

#### Why It Matters
有研究价值，但当前不是单场景规则稳定性的核心问题。

#### Current Judgment
**P3 / reviewable**

---

### P3-Gap-03
#### Name
Narrative Override Risk Gap

#### Description
虽然已有 blocker logic，但仍需持续防止“叙事确信”压倒 evidence discipline。

#### Why It Matters
这更像长期维护风险，而不是当前必须新增规则的缺口。

#### Current Judgment
**P3 / maintenance caution**

---

## 5. Priority Summary Table

| Gap ID | Gap Name | Priority | Why Priority Matters |
|---|---|---|---|
| P1-Gap-01 | G5 Consequence-Specific Evidence Minimum Threshold Gap | P1 | affects consequence confirmation |
| P1-Gap-02 | QA / Inspection Relevance Confirmation Gap | P1 | affects QA-related upgrade discipline |
| P1-Gap-03 | Conflicting Evidence Precedence Gap | P1 | affects conflict resolution and downgrade consistency |
| P1-Gap-04 | Acceptance Evidence Loss Response Gap | P1 | affects confirmed action stability |
| P2-Gap-01 | Transition Timing Discipline Gap | P2 | affects transition consistency |
| P2-Gap-02 | Installation Sequence Confirmation Gap | P2 | affects construction handoff detail |
| P2-Gap-03 | Evidence Bundle Conflict Resolution Gap | P2 | affects bundle handling logic |
| P3-Gap-01 | Outer-Scope Re-entry Strictness Gap | P3 | affects scope discipline maintenance |
| P3-Gap-02 | Historical Similar-Case Evidence Use Gap | P3 | affects support-evidence policy |
| P3-Gap-03 | Narrative Override Risk Gap | P3 | affects maintenance discipline |

---

## 6. Compression Readiness Judgment

### Ready for Immediate Compression
- P1-Gap-01
- P1-Gap-02
- P1-Gap-03
- P1-Gap-04

### Better Deferred
- all P2 gaps
- all P3 gaps

### Why
因为当前最需要的是先压缩会直接影响：
- strong conclusion qualification
- consequence claim discipline
- confirmed action stability
的缺口。

---

## 7. Current Research Judgment

### What this gap list clarifies
本文件澄清了：
- 当前规则并不“缺框架”
- 当前缺的是少数关键规则点的进一步压实
- 第三轮应优先压 P1，不必贪多

### What this gap list avoids
本文件避免了：
- 无边界新增新规则主题
- 提前跳到第二个 case
- 把所有 reviewable point 都当作当前必须解决的问题

---

## 8. Latest Stable View
当前最稳定的缺口判断是：

当前 DGM 规则体系已经具备基本可判定性，但仍存在四个会直接影响 consequence confirmation、QA relevance、conflicting evidence handling 与 confirmed action stability 的 P1 缺口；第三轮最合理的任务是只压缩这些高杠杆缺口，而不是扩展新结构。

## 9. Recommended Next Step
在本文件之后，直接进入：
`DGM_Rule_Gap_Compression_Note_v0.md`