---
title: DGM_Propagation_Pattern_Note_v0
doc_type: propagation_pattern_note
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
  - propagation
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
- Baseline: [[04_Baselines/DGM_Glossary_Taxonomy_Mini_Baseline_v0]]

# DGM_Propagation_Pattern_Note_v0

## Position
本文件用于深化 `CASE-NPP-DGM-01` 中“设计变更影响分析模型场景”的 propagation logic。  
其目标不是重新定义场景，而是把传播模式从 general wording 压实为可分析、可分层、可审查的结构。

## Current Objective
明确回答以下问题：
1. 设计变更影响沿哪些主路径传播  
2. 不同传播路径的成立条件是什么  
3. 哪些传播已足以进入 confirmed relevance  
4. 哪些传播必须停留在 review-required relevance  

## Scope

### In Scope
- baseline propagation
- interface propagation
- construction handoff propagation
- propagation bridge objects
- propagation stopping conditions
- propagation confirmation discipline

### Out of Scope
- full lifecycle propagation universe
- plant operation propagation
- enterprise coordination propagation
- software implementation flow propagation

---

## 1. Propagation Use Rules

### Rule 1
传播不是单一概念，而是多层次关系展开。

### Rule 2
任何传播判断都必须指向明确的 propagation route，而不是泛泛写成“可能有影响”。

### Rule 3
若某传播路径缺少 binding evidence，不得自动升级为 confirmed propagation。

### Rule 4
Propagation relevance 与 impact relevance 相关，但两者不是同一件事。

### Rule 5
Route A 成立，不代表 Route B 或 Route C 自动成立。

---

## 2. Core Propagation Types

### Type A — Baseline Propagation
#### Definition
设计变更首先沿 design basis、configuration baseline、approved design document 等正式控制对象传播。

#### Route
Change Request  
→ Design Basis Object  
→ Configuration Baseline Object  
→ Approved Design Document / Parameter / Rule / Logic Object

#### Meaning
这是所有后续传播的起始层。  
若这一层无法成立，后续 interface 或 construction propagation 都只能降级。

#### Typical Question
- 变更是否真正进入正式 baseline
- 变更影响的是哪类 baseline-controlled object
- 变更是配置级、逻辑级、规则级还是参数级影响

#### Judgment
**foundational propagation**

---

### Type B — Interface Propagation
#### Definition
设计变更沿接口定义、专业接口或数据交互边界向其他 discipline objects 传播。

#### Route
Baseline-linked change  
→ Interface Object  
→ Affected Discipline Object  
→ Discipline Data Object

#### Meaning
这是从“局部设计对象影响”转向“跨专业传播”的关键层。

#### Typical Question
- 接口是否受该变更影响
- 传播是否跨专业边界
- 接口传播是单向、双向还是条件性传播
- affected discipline mapping 是否完整

#### Judgment
**bridge propagation**

---

### Type C — Construction Handoff Propagation
#### Definition
设计变更通过工程包、安装顺序、质保/检验要求等对象传播到建造后果域。

#### Route
Affected design-side object  
→ Construction Package Object  
→ Installation Sequence Object  
→ Inspection / QA Record Object  
→ As-Built Evidence Object

#### Meaning
这是从 design-side relevance 转向 design-construction continuity relevance 的关键层。

#### Typical Question
- 变更是否已进入工程包
- 是否改变施工准备或安装顺序
- 是否触发 QA / inspection record 更新需求
- 是否要求 downstream evidence 更新

#### Judgment
**consequence-domain propagation**

---

## 3. Propagation Bridge Objects

### 3.1 Baseline Bridge Objects
这些对象承接触发并建立正式控制链：
- Design Basis Object
- Configuration Baseline Object
- Approved Design Document Object

### 3.2 Interface Bridge Objects
这些对象承接跨专业传播：
- Interface Object
- Affected Discipline Object
- Discipline Data Object

### 3.3 Construction Bridge Objects
这些对象承接设计到建造的后果转换：
- Construction Package Object
- Installation Sequence Object
- Inspection / QA Record Object

### 3.4 Acceptance Bridge Objects
这些对象承接传播判断进入治理接纳：
- Validation Evidence Object
- Decision-Support Output Object

---

## 4. Propagation Strength Classes

### Level 1 — Contained Propagation
传播仅停留在 baseline-controlled design layer 内部，尚未跨接口、跨专业或跨建造边界。

### Level 2 — Cross-Discipline Propagation
传播已穿过 interface layer，进入其他 discipline objects。

### Level 3 — Construction-Relevant Propagation
传播已穿过 handoff layer，进入 construction package / QA relevance 域。

### Level 4 — Review-Escalated Propagation
传播迹象存在，但证据不足以确认，应进入人工评审升级。

---

## 5. Propagation Confirmation Discipline

### 5.1 Confirmed Propagation
只有满足以下条件，传播才可被写为 confirmed:
- 有正式 source trigger
- 有 binding evidence
- 有 route-specific propagation evidence
- 有 scope-consistent impact target

### 5.2 Likely Propagation
以下情况可写为 likely:
- route logic strong
- target object plausible
- evidence incomplete but bounded

### 5.3 Review-Required Propagation
以下情况必须保留 review-required:
- bridge object unclear
- route incomplete
- evidence not bound
- outer-scope target introduced

### 5.4 Bounded Out-of-Scope Propagation
虽存在远端传播可能，但超出当前 bounded case，不进入当前主判断链。

---

## 6. Propagation Stopping Conditions

### Stop Condition A
Baseline propagation 未成立  
→ 不继续推导 interface propagation

### Stop Condition B
Interface mapping 不完整  
→ 不继续推导 cross-discipline impact 为 confirmed

### Stop Condition C
Construction package mapping 缺失  
→ 不继续推导 construction-relevant propagation

### Stop Condition D
QA relevance evidence 缺失  
→ 不把 QA / inspection update 写为 confirmed requirement

### Stop Condition E
Outer-scope coordination target 出现  
→ 标记 bounded out-of-scope，不纳入当前主控制链

---

## 7. Propagation Pattern Summary Table

| Propagation Type | Entry Condition | Bridge Objects | Typical Target | Evidence Need | Default Judgment |
|---|---|---|---|---|---|
| Baseline Propagation | approved change request + baseline binding | design basis, configuration baseline | baseline-controlled design objects | source + binding evidence | foundational |
| Interface Propagation | baseline propagation established + interface relevance | interface object, affected discipline object | cross-discipline objects | route-specific evidence | bridge |
| Construction Handoff Propagation | affected design object + package mapping | construction package, installation sequence, QA record | construction / QA consequence objects | mapping + consequence evidence | consequence-domain |
| Review-Escalated Propagation | partial route only | incomplete bridge objects | uncertain targets | bounded supporting evidence only | review-required |

---

## 8. Current Research Judgment

### What this note clarifies
本文件澄清了：
- propagation 是分层的，不是统一概念
- 传播桥对象决定传播是否成立
- confirmed propagation 必须有 route-specific evidence
- construction relevance 不能从 design relevance 自动推出

### What remains open
仍待深化：
- propagation strength 的更细分级
- interface propagation 的 bidirectionality 处理
- installation sequence object 的传播判定规则
- outer-scope coordination propagation 的更严格边界

---

## 9. Latest Stable View
当前最稳定的传播研究结论是：

设计变更影响分析模型场景中的传播，应被理解为从 baseline propagation 出发，经 interface propagation 扩展，并在满足 handoff mapping 与 consequence evidence 条件下进入 construction handoff propagation；未满足这些条件的传播不得自动升级为 confirmed conclusion。

## 10. Recommended Next Step
在本文件之后，建议继续形成：
`DGM_Evidence_Requirement_Note_v0.md`