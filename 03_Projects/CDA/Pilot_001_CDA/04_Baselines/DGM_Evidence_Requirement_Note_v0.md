---
title: DGM_Evidence_Requirement_Note_v0
doc_type: evidence_requirement_note
project: Pilot_001_CDA
domain: nuclear_design_construction
case_id: CASE-NPP-DGM-01
version: v0
status: reviewable
stability: bounded_research_baseline
aars_step: objectized_case_execution
scope_type: bounded_case
tags:
  - AARS
  - CDA
  - DGM
  - evidence
  - nuclear
  - design-change
  - baseline
---

## Links
- Home: [[Pilot_001_CDA_Home]]
- MOC: [[DGM_CASE_NPP_01_MOC]]
- Case: [[01_Cases/CASE-NPP-DGM-01_Case_File_v0]]
- Dependency: [[02_Objects/DEP-NPP-DGM-01_v0]]
- Risk: [[02_Objects/RISK-NPP-DGM-01_v0]]
- Control: [[02_Objects/CTRL-NPP-DGM-01_v0]]
- Strengthening: [[03_Reviews/DGM_Second_Pass_Strengthening_Note_v0]]
- Impact Matrix: [[04_Baselines/DGM_Impact_Object_Matrix_v0]]
- Propagation Note: [[04_Baselines/DGM_Propagation_Pattern_Note_v0]]
- Baseline: [[04_Baselines/DGM_Glossary_Taxonomy_Mini_Baseline_v0]]

# DGM_Evidence_Requirement_Note_v0

## Position
本文件用于定义 `CASE-NPP-DGM-01` 中证据要求的最小研究基线。  
其目标不是建立全域证据体系，而是明确在设计变更影响分析模型场景中，什么样的 evidence 足以支撑不同层级的判断与治理动作。

## Current Objective
回答以下问题：
1. 哪些证据是当前场景必须有的  
2. 哪些证据只够支撑 bounded supporting judgment  
3. 哪些结论必须因为证据不足而降级  
4. 模型输出要进入评审与治理动作，最低需要什么证据纪律  

## Scope

### In Scope
- source evidence
- baseline binding evidence
- propagation evidence
- construction handoff evidence
- QA relevance evidence
- acceptance evidence

### Out of Scope
- plant-wide audit evidence architecture
- enterprise legal/compliance evidence framework
- implementation platform evidence storage design
- operation-phase evidence universe

---

## 1. Evidence Use Rules

### Rule 1
任何重要判断都必须绑定到 evidence class，而不能只以 prose assertion 存在。

### Rule 2
证据要求应与判断强度匹配。  
强结论必须有强绑定证据；弱证据只能支撑 bounded supporting judgment 或 review-required judgment。

### Rule 3
证据不足不是失败，而是一种正式状态。  
证据不足时，应将结论降级，而不是用强语言掩盖。

### Rule 4
不同 propagation route 需要不同 evidence；不能用 baseline evidence 替代 construction handoff evidence。

### Rule 5
模型输出若要进入治理动作，必须具备 acceptance evidence，而不仅是内部分析依据。

---

## 2. Evidence Requirement Layers

### Layer 1 — Source Evidence
#### Purpose
证明变更真实存在，并进入正式控制链。

#### Typical Evidence
- approved change request
- change classification
- scope statement
- formal initiation record

#### Use
没有 source evidence，不应启动正式 impact reasoning。

---

### Layer 2 — Binding Evidence
#### Purpose
证明 change request 与 baseline / interface / object families 之间存在正式绑定关系。

#### Typical Evidence
- baseline version binding
- design basis reference
- object trace link
- interface definition version linkage

#### Use
没有 binding evidence，不能把对象 relevance 升为 confirmed relevance。

---

### Layer 3 — Propagation Evidence
#### Purpose
证明影响确实沿某条 propagation route 展开。

#### Typical Evidence
- interface route mapping
- affected discipline linkage
- package mapping
- sequence dependency mapping

#### Use
没有 propagation evidence，不能把 likely propagation 写成 confirmed propagation。

---

### Layer 4 — Consequence Evidence
#### Purpose
证明传播已进入后果域，如 construction package、QA / inspection relevance、downstream execution relevance。

#### Typical Evidence
- issued package mapping
- installation sequence linkage
- inspection point linkage
- QA update relevance trace

#### Use
没有 consequence evidence，不得确认 construction-relevant impact。

---

### Layer 5 — Acceptance Evidence
#### Purpose
证明模型输出可以进入评审、验证或治理动作，而不仅是内部推演结果。

#### Typical Evidence
- validation evidence
- applicability boundary statement
- decision-support limitation statement
- review condition statement

#### Use
没有 acceptance evidence，模型输出最多只能作为 review-required input，而不能直接进入 confirmed governance action。

---

## 3. Evidence Classes for CASE-NPP-DGM-01

### Evidence Class A — Confirmed Evidence
满足：
- 来源正式
- 绑定明确
- 路径清晰
- 适用边界明确

可支撑：
- confirmed relevance
- confirmed propagation
- confirmed control action input

---

### Evidence Class B — Bounded Supporting Evidence
满足：
- 路径逻辑较强
- 对象映射基本成立
- 但部分绑定或适用边界尚不完整

可支撑：
- likely relevance
- likely propagation
- bounded supporting judgment

---

### Evidence Class C — Review-Required Evidence
满足：
- 存在线索
- 但 route、binding 或 boundary 尚不够稳

可支撑：
- review-required relevance
- review escalation
- monitored continuation

---

### Evidence Class D — Insufficient / Out-of-Scope Evidence
满足：
- 证据碎片化
- 对象映射不完整
- route 过远或超出 bounded case

可支撑：
- bounded out-of-scope
- no confirmed conclusion

---

## 4. Evidence-to-Judgment Mapping

| Evidence Class | Supports Which Judgment | Not Allowed to Support |
|---|---|---|
| Confirmed Evidence | confirmed relevance / confirmed propagation / confirmed control input | none |
| Bounded Supporting Evidence | likely relevance / likely propagation | confirmed conclusion |
| Review-Required Evidence | review-required relevance / review escalation | confirmed or strong likely conclusion |
| Insufficient / Out-of-Scope Evidence | bounded out-of-scope / no-action | any confirmed in-scope conclusion |

---

## 5. Evidence Requirements by Object Family

| Object Family | Minimum Evidence Requirement | Stronger Requirement for Confirmation |
|---|---|---|
| Change Request Object | source evidence | approved and scoped change trigger |
| Design Basis / Baseline Object | binding evidence | formal baseline version + trace link |
| Interface Object | binding + route evidence | interface version + affected endpoint mapping |
| Affected Discipline Object | route evidence | explicit discipline impact trace |
| Construction Package Object | route + consequence evidence | package mapping + issued scope trace |
| Installation Sequence Object | consequence evidence | sequence dependency confirmation |
| QA / Inspection Record Object | consequence evidence | inspection point / QA linkage confirmation |
| Validation Evidence Object | acceptance evidence | applicability boundary + validation basis |
| Decision-Support Output Object | acceptance evidence | output-to-evidence binding + review condition |

---

## 6. Evidence Discipline for Strong Conclusions

### 6.1 Confirmed Relevance Requires
- source evidence
- binding evidence
- object-specific trace

### 6.2 Confirmed Propagation Requires
- source evidence
- binding evidence
- route-specific propagation evidence

### 6.3 Confirmed Construction Impact Requires
- propagation evidence
- package mapping
- consequence evidence

### 6.4 Confirmed Governance Action Input Requires
- acceptance evidence
- limitation statement
- review condition clarity

---

## 7. Evidence Failure Modes

### Failure Mode A — Source Without Binding
有正式变更来源，但无法绑定 baseline 或 interface。  
结果：只能停留在 trigger acknowledged，不应进入 confirmed impact。

### Failure Mode B — Binding Without Route
有对象绑定，但无法证明影响如何传播。  
结果：只能停留在 likely relevance，不应进入 confirmed propagation。

### Failure Mode C — Route Without Consequence
传播逻辑存在，但没有 construction / QA relevance evidence。  
结果：不应确认 construction impact。

### Failure Mode D — Analysis Without Acceptance
模型输出存在，但没有 validation basis 或 review condition。  
结果：输出不得直接进入 confirmed governance action。

---

## 8. Current Research Judgment

### What this note clarifies
本文件澄清了：
- evidence 不是单一概念，而是层级体系
- 不同判断需要不同证据等级
- acceptance evidence 是模型治理真正成立的关键层
- 证据不足时应降级，而不是含糊处理

### What remains open
仍待深化：
- evidence freshness discipline
- conflicting evidence handling
- historical similar-change evidence 是否纳入 bounded support
- QA relevance evidence 的最小粒度标准

---

## 9. Latest Stable View
当前最稳定的证据研究结论是：

在设计变更影响分析模型场景中，只有当 source、binding、propagation、consequence 与 acceptance evidence 按判断强度适当组合时，模型输出才可进入 confirmed relevance、confirmed propagation 或 confirmed governance action；否则必须显式降级为 likely、review-required 或 bounded out-of-scope。

## 10. Recommended Next Step
在本文件之后，建议继续形成：
`DGM_Governance_Disposition_Framework_v0.md`