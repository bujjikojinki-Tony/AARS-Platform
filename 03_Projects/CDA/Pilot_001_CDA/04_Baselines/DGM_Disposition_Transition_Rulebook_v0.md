---
title: DGM_Disposition_Transition_Rulebook_v0
doc_type: disposition_transition_rulebook
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
  - disposition
  - transition
  - nuclear
  - baseline
---

## Links
- Home: [[Pilot_001_CDA_Home]]
- MOC: [[DGM_CASE_NPP_01_MOC]]
- Disposition Framework: [[04_Baselines/DGM_Governance_Disposition_Framework_v0]]
- Evidence Granularity: [[04_Baselines/DGM_Evidence_Granularity_Note_v0]]
- Evidence Note: [[04_Baselines/DGM_Evidence_Requirement_Note_v0]]
- Propagation Note: [[04_Baselines/DGM_Propagation_Pattern_Note_v0]]
- Impact Matrix: [[04_Baselines/DGM_Impact_Object_Matrix_v0]]
- Final Review: [[03_Reviews/Pilot_001_DGM_Final_Review_Note_v0]]
- Deepening Review: [[03_Reviews/DGM_Research_Deepening_Review_Note_v0]]

# DGM_Disposition_Transition_Rulebook_v0

## Position
本文件用于把 `CASE-NPP-DGM-01` 中的 disposition framework 从“处置类别”推进到“处置转换规则”。

它关注的不是 disposition 有哪些类，而是：

- 什么条件下从一个 disposition 升级到另一个 disposition
- 什么条件下必须降级
- 什么条件下应保持原状态
- 什么条件下允许从 out-of-scope 重新进入主链

---

## Current Objective
回答以下问题：

1. `bounded review` 在什么条件下可升级为 `confirmed action`
2. `confirmed action` 在什么条件下必须回退
3. `monitored continuation` 在什么条件下可进入主控制链
4. `no-action / bounded out-of-scope` 在什么条件下允许重入
5. evidence granularity、propagation status 与 disposition transition 如何联动

---

## Scope

### In Scope
- escalation rules
- downgrade rules
- hold rules
- re-entry rules
- transition blockers
- transition discipline for CASE-NPP-DGM-01

### Out of Scope
- workflow engine design
- approval system implementation
- enterprise governance workflow orchestration
- full lifecycle transition model

---

## 1. Transition Use Rules

### Rule 1
Disposition transition 必须由对象相关性、传播确认度与证据粒度共同触发，不能由单一因素决定。

### Rule 2
任何升级都必须比当前状态拥有更强的 evidence basis 或更清晰的 propagation status。

### Rule 3
任何关键 evidence 缺口出现时，应优先降级，而不是保持强状态。

### Rule 4
`monitored continuation` 与 `no-action / bounded out-of-scope` 不是空白状态，而是正式状态。

### Rule 5
任何 re-entry 都必须重新满足 bounded scope discipline。

---

## 2. Core Disposition States

### State A — Confirmed Action
当前对象或判断已满足进入正式治理动作的条件。

### State B — Bounded Review
当前对象或判断已有较强相关性，但仍需 review、补证或边界确认。

### State C — Monitored Continuation
当前对象或判断值得持续监视，但不进入当前主控制链。

### State D — No-Action / Bounded Out-of-Scope
当前对象或判断被正式标记为不进入当前主治理链。

---

## 3. Transition Inputs

Disposition transition 的判断输入包括三类：

### Input 1 — Relevance Status
- confirmed relevance
- likely relevance
- review-required relevance
- bounded out-of-scope relevance

### Input 2 — Propagation Status
- contained propagation
- confirmed propagation
- likely propagation
- review-required propagation
- no bounded propagation

### Input 3 — Evidence Granularity Status
- G1 presence-level
- G2 reference-level
- G3 trace-level
- G4 route-specific
- G5 consequence-specific
- G6 acceptance-level

---

## 4. Escalation Rules

### Escalation E1
`Monitored Continuation` → `Bounded Review`

#### Conditions
- relevance 至少达到 likely relevance
- propagation 至少达到 likely or review-required propagation
- evidence 至少达到 G3 trace-level 或有效 bounded support bundle

#### Meaning
对象已从外围可见性，进入当前 case 的正式 review 主链。

---

### Escalation E2
`Bounded Review` → `Confirmed Action`

#### Conditions
- relevance 达到 confirmed relevance
- propagation 达到 confirmed propagation（如相关）
- consequence claim 具备 G5 consequence-specific evidence（如相关）
- action input 具备 G6 acceptance-level evidence

#### Meaning
对象或判断已满足进入正式治理动作的条件。

---

### Escalation E3
`No-Action / Bounded Out-of-Scope` → `Monitored Continuation`

#### Conditions
- 新 evidence 表明对象已开始进入 bounded scope 邻接带
- relevance 不再纯 out-of-scope
- 但仍不足以进入 review 主链

#### Meaning
对象从正式排除状态，重新进入受控观察状态。

---

### Escalation E4
`No-Action / Bounded Out-of-Scope` → `Bounded Review`

#### Conditions
- 有新的 bounded scope linkage
- 至少具备 G3 trace-level evidence
- propagation bridge 已识别
- 不再仅是外围协调对象

#### Meaning
对象正式重入当前 bounded case 主链。

---

## 5. Downgrade Rules

### Downgrade D1
`Confirmed Action` → `Bounded Review`

#### Triggers
- G6 acceptance-level evidence 失效或不足
- route-specific evidence 被削弱
- applicability boundary 被重新收紧
- scope consistency 出现疑问

#### Meaning
当前动作资格被撤回，但对象仍保留 review 价值。

---

### Downgrade D2
`Bounded Review` → `Monitored Continuation`

#### Triggers
- relevance 降弱为外围相关
- propagation 不能维持
- evidence 退化到 G1 / G2
- 当前 control leverage 明显不足

#### Meaning
对象不再值得占用 review 主序列，但仍需观察。

---

### Downgrade D3
`Monitored Continuation` → `No-Action / Bounded Out-of-Scope`

#### Triggers
- 对象被确认超出当前 bounded scope
- 没有有效 route linkage
- 没有继续监控价值

#### Meaning
对象从观察状态正式退出当前治理链。

---

### Downgrade D4
`Confirmed Action` → `No-Action / Bounded Out-of-Scope`

#### Triggers
- 当前对象被重新界定为 scope error
- earlier mapping 被证伪
- evidence 指向错误对象或错误边界

#### Meaning
这是强制性退回，说明 earlier action qualification 失效。

---

## 6. Hold Rules

### Hold H1
保持 `Confirmed Action`
当以下条件持续成立：
- confirmed relevance 维持
- confirmed propagation 维持
- G6 acceptance-level evidence 维持
- bounded scope consistency 维持

---

### Hold H2
保持 `Bounded Review`
当以下条件成立：
- review value 明确存在
- 关键 evidence 缺口尚未补足
- 但对象仍在 bounded main chain 内

---

### Hold H3
保持 `Monitored Continuation`
当以下条件成立：
- 对象有外围相关性
- 但不足以进入 review 主链
- 且持续观测仍有意义

---

### Hold H4
保持 `No-Action / Bounded Out-of-Scope`
当以下条件成立：
- 对象持续超出 bounded scope
- 无新 evidence 支持 re-entry
- 无当前 control leverage

---

## 7. Transition Blockers

### Blocker B1
没有 G3 trace-level evidence  
→ 不允许进入 `Bounded Review` 以上状态

### Blocker B2
没有 G4 route-specific evidence  
→ 不允许确认 propagation-based upgrade

### Blocker B3
没有 G5 consequence-specific evidence  
→ 不允许把 construction-relevant impact 升级为强状态

### Blocker B4
没有 G6 acceptance-level evidence  
→ 不允许进入 `Confirmed Action`

### Blocker B5
对象被判定为 outer-scope target  
→ 不允许在无新 bounded linkage 前重入主链

---

## 8. Transition Map

| Current State | Trigger Condition | Next State |
|---|---|---|
| Monitored Continuation | stronger relevance + G3 trace | Bounded Review |
| Bounded Review | confirmed relevance + G4/G5/G6 as needed | Confirmed Action |
| No-Action / Out-of-Scope | bounded linkage appears | Monitored Continuation or Bounded Review |
| Confirmed Action | acceptance loss / scope doubt | Bounded Review |
| Bounded Review | weakened relevance / weak leverage | Monitored Continuation |
| Monitored Continuation | confirmed outer-scope | No-Action / Out-of-Scope |

---

## 9. Transition by Typical Object Family

### 9.1 Interface Object
- Default entry: `Bounded Review`
- Upgrade to `Confirmed Action`: requires G4 route-specific + G6 acceptance
- Downgrade: if route ambiguity reappears

### 9.2 Construction Package Object
- Default entry: `Bounded Review`
- Upgrade to `Confirmed Action`: requires G5 consequence-specific + G6 acceptance
- Downgrade: if package linkage weakens

### 9.3 QA / Inspection Record Object
- Default entry: `Monitored Continuation` or `Bounded Review`
- Upgrade to `Confirmed Action`: requires explicit QA relevance evidence
- Downgrade: if QA linkage remains generic

### 9.4 Decision-Support Output Object
- Default entry: `Bounded Review`
- Upgrade to `Confirmed Action`: requires output-to-evidence binding + explicit applicability boundary
- Downgrade: if acceptance evidence weakens

---

## 10. Transition Discipline for Strong Conclusions

### Rule T1
No direct jump from `Monitored Continuation` to `Confirmed Action`
除非同时满足：
- G3 trace
- G4 route
- G5 consequence（如相关）
- G6 acceptance

### Rule T2
No direct jump from `Out-of-Scope` to `Confirmed Action`
必须至少经过一次 bounded re-entry confirmation。

### Rule T3
Any loss of G6 triggers immediate review of `Confirmed Action`
G6 是强状态的最后门槛。

### Rule T4
Propagation weakening outranks narrative confidence
只要 route-specific evidence 弱化，强叙事不得维持强状态。

---

## 11. Current Research Judgment

### What this rulebook adds
本文件增加了：
- disposition state transition logic
- escalation / downgrade / hold / re-entry discipline
- blocker logic
- object-family-specific transition expectations

### What remains open
仍待后续 review 的点：
- QA-related transitions 的粒度还能更细
- re-entry from out-of-scope 的最小 bounded linkage 条件还可更紧
- multiple evidence bundles 的优先级冲突规则尚未定义
- transition timing discipline 尚未单独定义

---

## 12. Latest Stable View
当前最稳定的 disposition transition 结论是：

在 DGM 场景中，治理状态不应被视为静态标签，而应被视为受 relevance、propagation 和 evidence granularity 共同控制的 bounded transition system；因此 confirmed action、bounded review、monitored continuation 与 no-action / bounded out-of-scope 应通过明确升级、降级、保持与重入规则来管理。

## 13. Recommended Next Step
在本文件之后，第二轮的两份主文件已完成。  
下一步最合适的是生成一个小型验证文件：

`DGM_Rule_Validation_Note_v0.md`