---
title: DGM_P2_Gap_Compression_Note_v0
doc_type: p2_gap_compression_note
project: Pilot_001_CDA
domain: nuclear_design_construction
case_id: CASE-NPP-DGM-01
version: v0
status: reviewable
stability: p2_gap_compression_baseline
aars_step: objectized_case_execution
scope_type: bounded_case
tags:
  - AARS
  - CDA
  - DGM
  - p2-gap
  - compression
  - nuclear
  - baseline
---

## Links
- Home: [[Pilot_001_CDA_Home]]
- MOC: [[DGM_CASE_NPP_01_MOC]]
- P1 Gap Compression: [[DGM_Rule_Gap_Compression_Note_v0]]
- Rule Gap List: [[DGM_Rule_Gap_List_v0]]
- Evidence Granularity: [[DGM_Evidence_Granularity_Note_v0]]
- Disposition Transition: [[DGM_Disposition_Transition_Rulebook_v0]]
- Propagation Note: [[DGM_Propagation_Pattern_Note_v0]]
- Impact Matrix: [[DGM_Impact_Object_Matrix_v0]]
- Third-Round Completion: [[../03_Reviews/DGM_Third_Round_Completion_Note_v0]]

# DGM_P2_Gap_Compression_Note_v0

## Position
本文件用于对 `CASE-NPP-DGM-01` 当前规则体系中的 P2 gaps 做有界压缩。  
它的目标不是处理最危险的误升级风险，而是继续提升当前单场景规则基线的：

- 一致性
- 可解释性
- 时序纪律
- bundle-level 判断稳定性

## Current Objective
本文件只处理以下三个 P2 gaps：

1. Transition Timing Discipline Gap  
2. Installation Sequence Confirmation Gap  
3. Evidence Bundle Conflict Resolution Gap  

---

## Scope

### In Scope
- timing discipline tightening
- installation sequence consequence confirmation tightening
- evidence bundle conflict handling tightening

### Out of Scope
- P3 gaps
- second case
- multi-case comparison
- implementation workflow
- domain-wide generalization

---

## 1. Compression Use Rules

### Rule 1
本轮只压缩 P2 gaps，不重写既有 P1 rules。

### Rule 2
本轮压缩目标是提升解释力与一致性，而不是增加更多可升级路径。

### Rule 3
任何 timing / sequence / bundle rule 都必须继续服从已有：
- evidence granularity discipline
- disposition transition discipline
- bounded scope discipline

### Rule 4
当 P2 压缩与 P1 压缩冲突时，P1 优先。

---

## 2. P2-Gap-01 Compression  
## Transition Timing Discipline Gap

### Current Gap
当前已定义升级/降级条件，但仍不足以说明：
- 为什么某状态应立即升级
- 为什么某状态应暂缓升级
- 为什么某状态虽然可升级，但当前应先保持

### Compression Goal
让 disposition transition 不仅有条件，还有时序纪律。

### Compressed Rule P2-C1
当某对象满足“升级条件的主体部分”，但仍存在以下任一情况时，应进入 **timing hold**，而不是立即升级：

1. evidence 刚达到最低门槛，尚未形成稳定组合  
2. route-specific bridge 刚成立，但 consequence domain 尚未稳定  
3. relevance 已确认，但 acceptance evidence 刚补齐且尚未完成 review pass  
4. 当前 upgrade 会显著改变主控制顺序，而 supporting context 尚未同步

### Timing Hold Meaning
`timing hold` 不是新 disposition state，  
而是对当前状态的一条附加纪律：

- 保持原 disposition
- 明确记录“可升级但暂缓”
- 不把暂缓误写成“不成立”

### Immediate Upgrade Rule
只有同时满足以下条件，才应立即升级：
- evidence 门槛达标
- route / consequence 条件稳定
- no unresolved blocker remains
- 当前 upgrade 不会依赖刚形成、尚未稳定的单点证据

### Compression Effect
这条规则压缩了“刚刚够门槛就立即升级”的冲动，增强了 transition consistency。

---

## 3. P2-Gap-02 Compression  
## Installation Sequence Confirmation Gap

### Current Gap
当前 installation sequence object 已被纳入 construction consequence 域，但其确认门槛仍偏粗，容易被 generic construction impact 带着升级。

### Compression Goal
把 installation sequence relevance 与一般 construction effect 区分开。

### Compressed Rule P2-C2
只有同时满足以下三项，installation sequence relevance 才可进入 confirmed consequence status：

1. **specific sequence dependency named**  
   必须指向具体 sequence dependency、step relation 或等价的顺序对象。
2. **sequence change mechanism stated**  
   必须说明为什么该设计变更会改变 sequence，而不仅是“可能影响施工安排”。
3. **sequence-sensitive downstream condition stated**  
   必须说明 sequence 变化会影响哪类后续动作，如 package execution、inspection ordering 或 handoff timing。

### Invalid Forms
以下表述不得支持 confirmed installation sequence consequence：
- “可能影响施工节奏”
- “可能影响建造顺序”
- “施工安排可能调整”
- 未说明具体 sequence dependency 的泛化 construction effect

### Default Fallback
若只满足其中 1–2 项：
- 保持在 `Bounded Review`
- 最多作为 G5-adjacent consequence tendency
- 不得升级为 confirmed installation consequence

### Compression Effect
installation sequence 不再作为 generic construction consequence 的自然延伸，而成为一个需要单独确认的 consequence subtype。

---

## 4. P2-Gap-03 Compression  
## Evidence Bundle Conflict Resolution Gap

### Current Gap
当前已有 evidence precedence，但当多个 bundle 分别支持不同方向判断时，bundle-level conflict handling 还不够细。

### Compression Goal
把“单条 evidence 优先级”推进到“bundle-level 冲突处理纪律”。

### Compressed Rule P2-C3
当 evidence bundle 出现冲突时，应按以下三步处理：

#### Step 1 — Identify Dominant Bundle Type
先判断各 bundle 属于哪类：
- relevance bundle
- propagation bundle
- consequence bundle
- acceptance bundle

#### Step 2 — Apply Highest-Required Bundle Gate
若更高层 required bundle 不成立，则低层 supporting bundle 不得推动强升级。

即：
- acceptance bundle 缺失，阻断 confirmed action
- consequence bundle 不成立，阻断 confirmed consequence
- propagation bundle 不成立，阻断 confirmed propagation
- relevance bundle 不成立，阻断 confirmed relevance

#### Step 3 — Apply Non-Convergence Hold
若两个 bundle 在同一层级互相拉扯，且都未形成 clearly dominant direction，则：
- 不允许强升级
- 默认保持当前 disposition
- 进入 timing hold 或 bounded review

### Bundle Conflict Rule
**same-level unresolved bundle conflict defaults to non-upgrade**

### Compression Effect
这条规则避免了“多个半强 bundle 被拼成一个强结论”的情况，也避免冲突状态下被 narrative 整体拉强。

---

## 5. Compression Summary Table

| P2 Gap | Compression Rule | Main Effect |
|---|---|---|
| Transition Timing Discipline Gap | P2-C1 timing hold rule | reduces premature upgrade |
| Installation Sequence Confirmation Gap | P2-C2 sequence-specific consequence rule | separates sequence consequence from generic construction impact |
| Evidence Bundle Conflict Resolution Gap | P2-C3 bundle conflict handling rule | blocks forced convergence under conflict |

---

## 6. Integration with Existing Rule System

### With P1 Compression
- P1 负责收紧最危险误升级点
- P2 负责减少“虽不致命但不够稳”的解释性漂移

### With Evidence Granularity
- P2-C1 约束达到门槛后的时序处理
- P2-C3 约束多个 evidence bundle 同时存在时的组合纪律

### With Disposition Transition
- P2-C1 为 transition 提供 timing discipline
- P2-C2 限制 installation sequence 的 consequence 升级
- P2-C3 限制 bundle-conflict 场景下的越级升级

### With Propagation Note
- P2-C2 防止 construction handoff propagation 被直接泛化为 confirmed sequence consequence

---

## 7. Current Research Judgment

### What this compression achieves
本文件使当前规则体系在三个方面更稳：
- 不是一达门槛就立即升级
- installation sequence 不再混入 generic construction effect
- conflicting bundles 不再容易被强行收敛成单一强结论

### What this compression does not yet solve
本文件不处理：
- P3 gaps
- historical similar-case evidence policy
- outer-scope re-entry strictness tightening
- narrative override as long-term maintenance issue

---

## 8. Latest Stable View
当前最稳定的 P2 压缩结论是：

当前 DGM 规则体系不仅在 P1 层更能防误升级，也在 P2 层更能解释“为什么现在还不该升”“为什么 installation sequence 不能泛化确认”“为什么 conflicting bundles 不能强行收敛”；因此当前单场景规则基线已从“更可防御”进一步推进为“更一致、更可解释”。

## 9. Recommended Next Step
第四轮当前已完成核心压缩文件。  
下一步最合适的是：
`DGM_Fourth_Round_Validation_Check_v0.md`