---
title: DGM_Evidence_Granularity_Note_v0
doc_type: evidence_granularity_note
project: Pilot_001_CDA
domain: nuclear_design_construction
case_id: CASE-NPP-DGM-01
version: v0
status: reviewable
stability: rule_strengthening_baseline
aars_step: objectized_case_execution
scope_type: bounded_case
tags:
  - AARS
  - CDA
  - DGM
  - evidence
  - granularity
  - nuclear
  - baseline
---

## Links
- Home: [[Pilot_001_CDA_Home]]
- MOC: [[DGM_CASE_NPP_01_MOC]]
- Evidence Note: [[04_Baselines/DGM_Evidence_Requirement_Note_v0]]
- Propagation Note: [[04_Baselines/DGM_Propagation_Pattern_Note_v0]]
- Disposition Framework: [[04_Baselines/DGM_Governance_Disposition_Framework_v0]]
- Impact Matrix: [[04_Baselines/DGM_Impact_Object_Matrix_v0]]
- Final Review: [[03_Reviews/Pilot_001_DGM_Final_Review_Note_v0]]
- Deepening Review: [[03_Reviews/DGM_Research_Deepening_Review_Note_v0]]

# DGM_Evidence_Granularity_Note_v0

## Position
本文件用于把 `CASE-NPP-DGM-01` 中的 evidence requirement 从“证据类型”进一步推进到“证据粒度规则”。

它关注的不是还有哪些 evidence class，而是：

- 什么粒度足以支撑 confirmed judgment
- 什么粒度只够支撑 bounded supporting judgment
- 什么缺口必须触发降级
- 哪些 evidence bundle 仍然不能越级支持强结论

---

## Current Objective
回答以下问题：

1. 证据最小要细到什么程度，才算 usable evidence  
2. 证据粒度不足时，结论应如何降级  
3. 多个较弱证据能否构成 bounded support bundle  
4. 哪些关键缺口必须阻断 confirmed relevance、confirmed propagation 或 confirmed action

---

## Scope

### In Scope
- source evidence granularity
- binding evidence granularity
- propagation evidence granularity
- consequence evidence granularity
- acceptance evidence granularity
- evidence bundle logic
- downgrade-triggering evidence gaps

### Out of Scope
- evidence repository design
- audit database structure
- enterprise document management architecture
- software implementation of evidence engine

---

## 1. Granularity Use Rules

### Rule 1
证据类型存在，不等于证据粒度足够。

### Rule 2
粒度判断必须围绕具体判断目标，而不是抽象地说“有证据”。

### Rule 3
confirmed judgment 需要的不只是 evidence presence，而是 evidence specificity。

### Rule 4
多个弱证据可以形成 bounded support，但不能自动等价于 confirmed evidence。

### Rule 5
关键 bridge evidence 缺失时，其他外围证据不得替代。

---

## 2. Granularity Levels

### Level G1 — Presence-Level Evidence
只证明某对象或事件存在。

#### Example
- 有 change request 编号
- 有 baseline 文件名
- 有 interface 文档存在

#### Can Support
- trigger acknowledged
- object exists

#### Cannot Support
- confirmed relevance
- confirmed propagation
- confirmed action

---

### Level G2 — Reference-Level Evidence
证明对象之间存在某种引用或关联。

#### Example
- change request 引用了某 baseline
- baseline 文档引用了某 interface
- package 列表提到某 affected item

#### Can Support
- preliminary binding
- likely relevance

#### Cannot Support
- confirmed route
- confirmed consequence
- confirmed governance action

---

### Level G3 — Trace-Level Evidence
证明对象之间存在明确 trace link，可追到具体对象、版本或关系。

#### Example
- change request → baseline version trace
- interface version → affected endpoint mapping
- package → affected design object mapping

#### Can Support
- confirmed relevance
- likely propagation
- bounded supporting judgment

#### Cannot Support
- confirmed action by itself
- confirmed consequence without additional evidence

---

### Level G4 — Route-Specific Evidence
证明影响沿特定 propagation route 发生，而不是仅仅存在关联。

#### Example
- interface route mapping 明确显示跨专业传播
- construction handoff mapping 明确连接到 package / sequence / QA relevance
- propagation bridge object 已确认

#### Can Support
- confirmed propagation
- route-specific review escalation

#### Cannot Support
- confirmed action without acceptance evidence
- confirmed consequence without downstream consequence evidence

---

### Level G5 — Consequence-Specific Evidence
证明传播已进入后果域，而不仅是路径成立。

#### Example
- issued construction package impacted
- installation sequence dependency changed
- QA / inspection point update relevance confirmed

#### Can Support
- confirmed construction-relevant impact
- bounded action preparation

#### Cannot Support
- final governance action without acceptance evidence

---

### Level G6 — Acceptance-Level Evidence
证明模型输出可被治理体系接纳，而不是只作为分析结果存在。

#### Example
- validation basis clearly stated
- applicability boundary stated
- review condition stated
- output-to-evidence binding explicit

#### Can Support
- confirmed governance action input
- confirmed action under bounded scope

---

## 3. Granularity by Evidence Class

### 3.1 Source Evidence Granularity
#### Minimum Usable Granularity
- approved or formally recognized change trigger
- change scope statement
- change classification

#### Weak Form
- informal mention of change
- unapproved draft trigger

#### Judgment
没有达到 minimum usable granularity，不进入正式 impact reasoning。

---

### 3.2 Binding Evidence Granularity
#### Minimum Usable Granularity
- trace from change request to specific baseline object
- version-specific linkage
- named affected object family

#### Weak Form
- generic reference to “relevant baseline”
- broad mention of “related interface”

#### Judgment
binding evidence 若只有 generic reference，不足以支撑 confirmed relevance。

---

### 3.3 Propagation Evidence Granularity
#### Minimum Usable Granularity
- route-specific bridge object identified
- source object and target object both named
- propagation path bounded within current case

#### Weak Form
- “可能影响其他专业”
- “可能影响施工”

#### Judgment
propagation evidence 若没有 route-specific bridge，最多支持 review-required propagation。

---

### 3.4 Consequence Evidence Granularity
#### Minimum Usable Granularity
- specific construction package named
- specific sequence / QA relevance identified
- consequence domain explicitly stated

#### Weak Form
- “可能带来建造影响”
- “可能需要质量更新”

#### Judgment
没有 consequence-specific evidence，不得确认 construction-relevant impact。

---

### 3.5 Acceptance Evidence Granularity
#### Minimum Usable Granularity
- model output linked to specific evidence set
- applicability boundary explicit
- review condition explicit
- output limitation explicit

#### Weak Form
- “模型显示有影响”
- “系统建议优先处理”

#### Judgment
没有 acceptance-level granularity，模型输出不得直接进入 confirmed action。

---

## 4. Evidence Bundle Logic

### 4.1 Valid Bounded Support Bundle
以下组合可支撑 bounded review:
- G2 reference-level evidence
- G3 trace-level evidence
- partial G4 route-specific evidence

#### Result
可进入 likely relevance / bounded review

---

### 4.2 Invalid Bundle
以下组合仍不足以支撑 confirmed action:
- 多个 G1 presence-level evidence
- G2 reference without G3 trace
- G3 trace without G4/G5 for consequence claim
- G4 route without G6 acceptance for governance action

#### Result
不得越级升级

---

### 4.3 Confirmable Bundle
以下组合可支撑 confirmed action input:
- G3 trace-level evidence
- G4 route-specific evidence
- G5 consequence-specific evidence（如适用）
- G6 acceptance-level evidence

#### Result
可支撑 confirmed action under bounded scope

---

## 5. Granularity-to-Judgment Map

| Evidence Granularity | Strongest Supported Judgment |
|---|---|
| G1 Presence-Level | acknowledged existence only |
| G2 Reference-Level | likely relevance |
| G3 Trace-Level | confirmed relevance / likely propagation |
| G4 Route-Specific | confirmed propagation |
| G5 Consequence-Specific | confirmed construction-relevant impact |
| G6 Acceptance-Level | confirmed governance action input |

---

## 6. Mandatory Downgrade Triggers

### Trigger A
只有 G1 / G2，没有 G3  
→ 不得写 confirmed relevance

### Trigger B
只有 G3，没有 G4  
→ 不得写 confirmed propagation

### Trigger C
只有 G4，没有 G5  
→ 不得写 confirmed construction impact

### Trigger D
有 G3 / G4 / G5，但没有 G6  
→ 不得写 confirmed action

### Trigger E
evidence 指向 outer-scope target  
→ 降为 bounded out-of-scope or monitored continuation

---

## 7. Granularity by Typical Object Family

| Object Family | Minimum Evidence Granularity Needed | For Confirmed Judgment |
|---|---|---|
| Change Request Object | G1 + G2 | G3 |
| Baseline Object | G2 + G3 | G3 |
| Interface Object | G3 | G4 |
| Affected Discipline Object | G3 | G4 |
| Construction Package Object | G3 + G4 | G5 |
| Installation Sequence Object | G4 | G5 |
| QA / Inspection Record Object | G4 | G5 |
| Decision-Support Output Object | G3 + G4 | G6 |

---

## 8. Current Research Judgment

### What this note adds
本文件增加了：
- evidence 从类型到粒度的转换
- weak evidence bundle 与 strong evidence bundle 的区分
- mandatory downgrade triggers
- object-family-specific granularity expectation

### What remains open
仍待后续 review 的点：
- G5 consequence-specific evidence 的最小标准还可更细
- QA relevance granularity 仍可进一步压缩
- historical similar-case evidence 是否可以进入 bounded support bundle
- conflicting evidence 的优先级规则尚未定义

---

## 9. Latest Stable View
当前最稳定的证据粒度结论是：

在 DGM 场景中，evidence 的关键不只是“有没有”，而是“是否达到足以支持特定判断的粒度”；因此 G1–G6 应被视为当前 bounded research framework 中控制 judgment strength 与 downgrade discipline 的最小粒度序列。

## 10. Recommended Next Step
在本文件之后，直接进入：
`DGM_Disposition_Transition_Rulebook_v0.md`