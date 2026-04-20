---
title: DGM_Impact_Object_Matrix_v0
doc_type: impact_object_matrix
project: Pilot_001_CDA
domain: nuclear_design_construction
case_id: CASE-NPP-DGM-01
version: v0
status: reviewable
stability: bounded_research_baseline
aars_step: bounded_case_design
scope_type: bounded_case
tags:
  - AARS
  - CDA
  - DGM
  - impact-matrix
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
- Baseline: [[04_Baselines/DGM_Glossary_Taxonomy_Mini_Baseline_v0]]

# DGM_Impact_Object_Matrix_v0

## Position
本文件用于把 `CASE-NPP-DGM-01` 中“设计变更影响分析模型场景”的影响对象系统化。  
其作用不是替代 case file 或 dependency object，而是作为 impact-side 研究基线，为传播模式、证据要求与治理处置提供对象化支撑。

## Current Objective
明确回答四个问题：
1. 设计变更会影响哪些对象族  
2. 每类对象承受的主要影响类型是什么  
3. 这些影响如何传播  
4. 不同对象的证据要求与控制动作分别是什么  

## Scope
### In Scope
- change-triggered impact objects
- baseline-linked objects
- interface-linked objects
- construction-handoff objects
- QA / inspection relevance objects
- evidence and decision-support objects

### Out of Scope
- full lifecycle asset universe
- plant operation objects
- enterprise governance objects
- implementation software objects

---

## 1. Matrix Use Rules

### Rule 1
本矩阵关注的是 **impact-bearing objects**，不是所有项目对象。

### Rule 2
每一行对象族都应回答：
- 它为什么会被影响
- 它通过什么关系被影响
- 需要什么证据来确认
- 是否进入主控制链

### Rule 3
矩阵中的 `Current Judgment` 只允许使用：
- confirmed relevance
- likely relevance
- review-required relevance
- bounded out-of-scope

### Rule 4
如果对象没有足够证据进入 confirmed relevance，应保留为 review-required，而不是强行升级。

---

## 2. Impact Object Matrix

| Impact Object Family | Primary Impact Type | Propagation Route | Evidence Requirement | Control Relevance | Current Judgment |
|---|---|---|---|---|---|
| Change Request Object | trigger impact | direct trigger | approved change request, classification, scope statement | immediate attention | confirmed relevance |
| Design Basis Object | baseline impact | baseline propagation | approved design basis reference, baseline version binding | immediate attention | confirmed relevance |
| Configuration Baseline Object | configuration impact | baseline propagation | formal baseline version, controlled configuration reference | immediate attention | confirmed relevance |
| Approved Design Document Object | document-level baseline impact | baseline propagation | document version, approval state, trace to baseline | near-term control | likely relevance |
| Parameter / Rule / Logic Object | logic/configuration impact | baseline propagation | parameter set, rule mapping, logic ownership | immediate attention | likely relevance |
| Interface Object | cross-boundary impact | interface propagation | interface definition version, affected endpoint mapping | immediate attention | confirmed relevance |
| Affected Discipline Object | discipline coordination impact | interface propagation | discipline mapping evidence, impact trace | immediate attention | confirmed relevance |
| Discipline Data Object | data consistency impact | interface propagation | data version, dependency mapping, affected data class | near-term control | likely relevance |
| Construction Package Object | construction handoff impact | construction handoff propagation | package mapping, issued package status, affected work scope | near-term control | confirmed relevance |
| Installation Sequence Object | execution order impact | construction handoff propagation | sequence dependency, work-step mapping, package linkage | near-term control | review-required relevance |
| Inspection / QA Record Object | QA / verification impact | construction handoff propagation | inspection point linkage, QA relevance evidence, record class | near-term control | likely relevance |
| As-Built Evidence Object | downstream evidence impact | construction handoff propagation | as-built update condition, trace to construction scope | monitored continuation | review-required relevance |
| Validation Evidence Object | model-governance impact | evidence-binding dependency | evidence source, model applicability boundary, verification basis | immediate attention | confirmed relevance |
| Decision-Support Output Object | review / decision impact | evidence-binding dependency | output-to-evidence binding, scope limit, review condition | near-term control | confirmed relevance |
| Outer-Scope Coordination Object | outer coordination impact | indirect propagation | cross-boundary coordination trace | monitored continuation | bounded out-of-scope |

---

## 3. Object Family Notes

### 3.1 Trigger Layer
`Change Request Object` 是唯一明确的主触发对象。  
若其分类、范围或批准状态不清，后续所有 impact reasoning 都会降级。

### 3.2 Baseline Layer
`Design Basis Object` 与 `Configuration Baseline Object` 构成第一主控制层。  
若这层不能确认，不能把后续传播判断写成 confirmed conclusion。

### 3.3 Interface Layer
`Interface Object` 与 `Affected Discipline Object` 决定是否发生跨专业传播。  
这是最关键的 propagation bridge layer。

### 3.4 Construction Handoff Layer
`Construction Package Object`、`Installation Sequence Object`、`Inspection / QA Record Object` 决定场景是否进入设计—建造连续性影响域。  
其中 `Construction Package Object` 是核心承接对象。

### 3.5 Evidence / Decision Layer
`Validation Evidence Object` 和 `Decision-Support Output Object` 决定模型结论是否可被治理性接纳。  
这层不是附属层，而是 acceptance layer。

---

## 4. Primary Impact Types

本场景中的 impact type 建议固定为五类：

### 4.1 Trigger Impact
由变更请求直接触发的影响起点。

### 4.2 Baseline Impact
对设计依据、配置控制、文档正式状态造成的影响。

### 4.3 Interface Impact
沿专业接口、数据接口或功能接口扩散的影响。

### 4.4 Construction Handoff Impact
跨越设计边界，进入工程包、安装顺序与建造验证体系的影响。

### 4.5 Evidence / Decision Impact
影响模型结论是否能进入正式评审、验证与治理动作的影响。

---

## 5. Propagation Route Model

本矩阵默认采用三类主传播路径：

### Route A — Baseline Propagation
change request → design basis / configuration baseline → controlled design objects

### Route B — Interface Propagation
baseline-linked change → interface object → affected discipline object / discipline data object

### Route C — Construction Handoff Propagation
affected design-side object → construction package / installation / QA relevance object

说明：
- Route A 成立不代表 Route C 自动成立
- Route B 成立不代表 construction impact 已确认
- Route C 成立前，必须至少有 package-level mapping evidence

---

## 6. Evidence Requirement Classes

建议将 evidence requirement 固定为四级：

### Level 1 — Source Evidence
证明变更真实存在并被正式纳入控制。

### Level 2 — Binding Evidence
证明对象间存在正式绑定关系。

### Level 3 — Propagation Evidence
证明影响确实沿某路径传播。

### Level 4 — Acceptance Evidence
证明模型输出可以进入评审或治理动作。

---

## 7. Control Relevance Classes

建议将 control relevance 固定为三类：

### Immediate Attention
不确认就无法维持主判断有效性的对象。

### Near-Term Control
影响后果域与治理收口，但不一定决定主判断是否成立的对象。

### Monitored Continuation
值得追踪，但当前不应抢占主控制顺序的对象。

---

## 8. Current Research Judgment

### What this matrix clarifies
本矩阵澄清了：
- “影响范围”不是一个扁平列表
- 不同对象的影响层次不同
- propagation route 与 evidence requirement 必须跟对象绑定
- control relevance 不应只由直觉决定

### What remains open
仍待深化：
- 安装顺序对象的证据要求
- QA 记录相关性的确认粒度
- outer-scope coordination object 的边界
- parameter / rule / logic object 的子分类

---

## 9. Latest Stable View
当前最稳定的理解是：

设计变更影响分析模型场景中的“影响”应被理解为一个由 trigger layer、baseline layer、interface layer、construction handoff layer 与 evidence / decision layer 共同构成的多层对象体系，而不是单一影响清单。

## 10. Recommended Next Step
在本矩阵之后，建议继续形成：

1. `DGM_Propagation_Pattern_Note_v0.md`
2. `DGM_Evidence_Requirement_Note_v0.md`
3. `DGM_Governance_Disposition_Framework_v0.md`

其中优先级最高的是：
`DGM_Propagation_Pattern_Note_v0.md`