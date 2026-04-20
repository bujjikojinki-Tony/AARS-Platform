---
title: DGM_Governance_Disposition_Framework_v0
doc_type: governance_disposition_framework
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
  - governance
  - disposition
  - nuclear
  - baseline
---

## Links
- Home: [[Pilot_001_CDA_Home]]
- MOC: [[DGM_CASE_NPP_01_MOC]]
- Case: [[01_Cases/CASE-NPP-DGM-01_Case_File_v0]]
- Control: [[02_Objects/CTRL-NPP-DGM-01_v0]]
- Risk: [[02_Objects/RISK-NPP-DGM-01_v0]]
- Strengthening: [[03_Reviews/DGM_Second_Pass_Strengthening_Note_v0]]
- Impact Matrix: [[04_Baselines/DGM_Impact_Object_Matrix_v0]]
- Propagation Note: [[04_Baselines/DGM_Propagation_Pattern_Note_v0]]
- Evidence Note: [[04_Baselines/DGM_Evidence_Requirement_Note_v0]]
- Baseline: [[04_Baselines/DGM_Glossary_Taxonomy_Mini_Baseline_v0]]

# DGM_Governance_Disposition_Framework_v0

## Position
本文件用于定义 `CASE-NPP-DGM-01` 中设计变更影响分析模型场景的治理处置框架。  
其核心目标不是做全流程审批制度，而是明确：当 impact、propagation 与 evidence 被分析后，当前 bounded case 中应如何做出治理性处置。

## Current Objective
回答以下问题：
1. 影响判断最终如何转化为治理动作  
2. 哪些结论可以进入 confirmed action  
3. 哪些必须进入 bounded review  
4. 哪些只应进入 monitored continuation  
5. 哪些应明确列为 no-action 或 bounded out-of-scope  

## Scope

### In Scope
- confirmed action conditions
- bounded review conditions
- monitored continuation conditions
- no-action conditions
- escalation and downgrade rules
- disposition discipline for CASE-NPP-DGM-01

### Out of Scope
- enterprise workflow engine design
- formal approval process software implementation
- plant-wide governance workflow architecture
- legal / contractual disposition logic

---

## 1. Governance Disposition Use Rules

### Rule 1
Disposition 是治理动作，不是影响判断本身。

### Rule 2
只有当 object relevance、propagation relevance 和 evidence strength 三者组合足够稳时，结论才可进入 confirmed action。

### Rule 3
证据不足时，应优先进入 bounded review 或 monitored continuation，而不是强行升级。

### Rule 4
Disposition 的设计目标是保持 bounded control，不是追求最大覆盖。

### Rule 5
No-action 不是“忽略”，而是一种正式治理状态。

---

## 2. Core Disposition Classes

### Class A — Confirmed Action
#### Definition
结论已具备足够对象绑定、传播确认与证据强度，可进入正式治理动作。

#### Typical Meaning
- 应启动明确的变更控制动作
- 应更新受影响 baseline / package / QA relevance
- 可作为正式评审输入

#### Minimum Requirements
- confirmed relevance
- confirmed propagation (where applicable)
- confirmed or acceptance-level evidence
- bounded scope consistency

---

### Class B — Bounded Review
#### Definition
结论已有较强相关性，但仍需人工评审、边界确认或进一步绑定证据后，才可进入正式动作。

#### Typical Meaning
- 暂不直接执行治理动作
- 进入 review queue
- 要求补充 binding / route / consequence / acceptance evidence

#### Minimum Requirements
- likely relevance or review-required relevance
- route partially established
- bounded supporting evidence or review-required evidence

---

### Class C — Monitored Continuation
#### Definition
对象或传播路径值得继续观察，但当前不足以进入主控制链或 review priority 主序列。

#### Typical Meaning
- 保留监视状态
- 不立即触发高优先级动作
- 在后续 update log 中持续跟踪

#### Minimum Requirements
- weak or peripheral relevance
- partial route indication
- low or incomplete evidence strength
- no immediate control leverage

---

### Class D — No-Action / Bounded Out-of-Scope
#### Definition
当前对象、传播或后果虽可能存在相关性，但不属于本 bounded case 的主控制范围，不进入当前治理动作链。

#### Typical Meaning
- 明确记录但不升级
- 保持 out-of-scope discipline
- 防止 scope drift

#### Minimum Requirements
- out-of-scope target
- insufficient bounded relevance
- no current control leverage inside this case

---

## 3. Disposition Decision Logic

### Step 1 — Relevance Check
先判断对象是否属于：
- confirmed relevance
- likely relevance
- review-required relevance
- bounded out-of-scope

### Step 2 — Propagation Check
再判断是否存在：
- contained propagation
- cross-discipline propagation
- construction-relevant propagation
- only suspected propagation

### Step 3 — Evidence Check
再判断 evidence 属于：
- confirmed evidence
- bounded supporting evidence
- review-required evidence
- insufficient / out-of-scope evidence

### Step 4 — Disposition Assignment
根据前三步的组合，赋予 disposition class。

---

## 4. Disposition Matrix

| Relevance | Propagation | Evidence | Default Disposition |
|---|---|---|---|
| confirmed relevance | confirmed propagation | confirmed / acceptance evidence | Confirmed Action |
| confirmed relevance | likely propagation | bounded supporting evidence | Bounded Review |
| likely relevance | likely propagation | bounded supporting evidence | Bounded Review |
| review-required relevance | partial propagation | review-required evidence | Bounded Review |
| peripheral relevance | weak propagation | weak evidence | Monitored Continuation |
| bounded out-of-scope | any | insufficient / out-of-scope evidence | No-Action / Bounded Out-of-Scope |

---

## 5. Disposition by Typical Object Family

### 5.1 Change Request Object
默认 disposition：
- **Confirmed Action**  
前提：change request 已批准且作用边界明确。

### 5.2 Configuration Baseline Object
默认 disposition：
- **Confirmed Action**  
前提：baseline binding 已确认。

### 5.3 Interface Object
默认 disposition：
- **Bounded Review** 或 **Confirmed Action**  
取决于 interface propagation 是否已确认。

### 5.4 Affected Discipline Object
默认 disposition：
- **Bounded Review**  
若 discipline impact trace 已明确，可上升为 Confirmed Action input。

### 5.5 Construction Package Object
默认 disposition：
- **Bounded Review**  
若 package mapping 与 consequence evidence 已确认，可上升为 Confirmed Action。

### 5.6 Inspection / QA Record Object
默认 disposition：
- **Monitored Continuation** 或 **Bounded Review**  
只有在 QA relevance evidence 明确时才可升级。

### 5.7 Validation Evidence Object
默认 disposition：
- **Confirmed Action prerequisite**  
它本身不是动作对象，但决定是否允许其他对象进入 confirmed action。

### 5.8 Outer-Scope Coordination Object
默认 disposition：
- **No-Action / Bounded Out-of-Scope**

---

## 6. Escalation Rules

### Escalation Rule A
从 Bounded Review → Confirmed Action  
需要补足：
- route confirmation
- consequence evidence or acceptance evidence
- scope consistency

### Escalation Rule B
从 Monitored Continuation → Bounded Review  
需要补足：
- stronger object relevance
- clearer propagation bridge
- bounded supporting evidence

### Escalation Rule C
从 No-Action / Out-of-Scope → Monitored Continuation  
仅当其开始进入 bounded case main chain 时，才允许提升。

---

## 7. Downgrade Rules

### Downgrade Rule A
若 acceptance evidence 缺失  
→ Confirmed Action 降级为 Bounded Review

### Downgrade Rule B
若 route-specific propagation evidence 缺失  
→ Confirmed propagation 相关 disposition 降级为 likely / review-required

### Downgrade Rule C
若 target object 被判定超出 bounded scope  
→ 直接降级为 No-Action / Bounded Out-of-Scope

### Downgrade Rule D
若 consequence evidence 不成立  
→ construction-related disposition 不得保留 Confirmed Action

---

## 8. Governance Meaning of Each Disposition

### Confirmed Action Means
- 可进入正式治理动作
- 可进入控制顺序
- 可支持评审/变更动作

### Bounded Review Means
- 可进入当前 case 的人工审查主链
- 不得假装已经确认
- 应在 update log 中跟踪补证

### Monitored Continuation Means
- 保持可见
- 不抢占当前 review / control 主链
- 防止外围对象过早升级

### No-Action / Out-of-Scope Means
- 正式不纳入当前治理主链
- 不是忽略，而是边界纪律

---

## 9. Current Research Judgment

### What this framework clarifies
本文件澄清了：
- 研究结论如何落到治理动作
- confirmed action 的门槛是什么
- bounded review 与 monitored continuation 的区别是什么
- no-action 是一种正式治理状态，而不是空白状态

### What remains open
仍待深化：
- disposition 与 control priority groups 的更细映射
- review queue 的最小结构
- QA-related disposition 的粒度规则
- outer-scope coordination 的升级条件

---

## 10. Latest Stable View
当前最稳定的治理处置研究结论是：

在设计变更影响分析模型场景中，治理动作不应由“看起来重要”直接触发，而应由对象相关性、传播确认度和证据强度的组合决定；因此 confirmed action、bounded review、monitored continuation 与 no-action / bounded out-of-scope 应被视为当前 bounded case 的四类正式处置状态。

## 11. Recommended Next Step
当前 “对象—传播—证据—处置” 四层深化链已完整。  
下一步最合适的是回到 `DGM_CASE_NPP_01_MOC.md` 与 `Pilot_001_CDA_Home.md`，把这四份新文件挂接进去，形成更新后的 authoritative research package。