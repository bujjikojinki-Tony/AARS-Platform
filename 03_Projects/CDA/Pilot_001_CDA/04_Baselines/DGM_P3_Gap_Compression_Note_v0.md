---
title: DGM_P3_Gap_Compression_Note_v0
doc_type: p3_gap_compression_note
project: Pilot_001_CDA
domain: nuclear_design_construction
case_id: CASE-NPP-DGM-01
version: v0
status: reviewable
stability: p3_gap_compression_baseline
aars_step: objectized_case_execution
scope_type: bounded_case
tags:
  - AARS
  - CDA
  - DGM
  - p3-gap
  - compression
  - nuclear
  - baseline
---

## Links
- Home: [[Pilot_001_CDA_Home]]
- MOC: [[DGM_CASE_NPP_01_MOC]]
- P2 Gap Compression: [[DGM_P2_Gap_Compression_Note_v0]]
- P1 Gap Compression: [[DGM_Rule_Gap_Compression_Note_v0]]
- Rule Gap List: [[DGM_Rule_Gap_List_v0]]
- Evidence Granularity: [[DGM_Evidence_Granularity_Note_v0]]
- Disposition Transition: [[DGM_Disposition_Transition_Rulebook_v0]]
- Rule Validation: [[../03_Reviews/DGM_Rule_Validation_Note_v0]]
- Fourth-Round Completion: [[../03_Reviews/DGM_Fourth_Round_Completion_Note_v0]]

# DGM_P3_Gap_Compression_Note_v0

## Position
本文件用于对 `CASE-NPP-DGM-01` 当前规则体系中的 P3 gaps 做有界压缩。  
它的目标不是继续增强强结论门槛，也不是继续增加状态复杂度，而是进一步提升当前单场景规则基线的：

- 边界纪律
- supporting evidence 使用纪律
- 长期维护中的反漂移能力

## Current Objective
本文件只处理以下三个 P3 gaps：

1. Outer-Scope Re-entry Strictness Gap  
2. Historical Similar-Case Evidence Use Gap  
3. Narrative Override Risk Gap  

---

## Scope

### In Scope
- out-of-scope re-entry tightening
- historical similar-case evidence policy tightening
- narrative override protection tightening

### Out of Scope
- second case
- multi-case comparison
- methodology extraction
- implementation workflow
- new disposition states

---

## 1. Compression Use Rules

### Rule 1
本轮只压缩 P3 gaps，不改变 P1/P2 已建立的主规则结构。

### Rule 2
P3 压缩的目标是减少长期漂移，而不是提高更多升级概率。

### Rule 3
P3 规则必须服务于 bounded discipline；不能因为“更完善”而偷渡新范围。

### Rule 4
若 P3 压缩与 P1/P2 规则冲突，以 P1/P2 为准。

---

## 2. P3-Gap-01 Compression  
## Outer-Scope Re-entry Strictness Gap

### Current Gap
当前虽已定义 out-of-scope 对象可在一定条件下 re-entry，但最小 bounded linkage 仍不够严格，可能导致外围对象过早重新进入主链。

### Compression Goal
让 re-entry 成为一个真正受控动作，而不是“只要看起来相关就回来”。

### Compressed Rule P3-C1
`No-Action / Bounded Out-of-Scope` 状态下的对象，只有同时满足以下三项，才允许进入 re-entry evaluation：

1. **bounded linkage explicit**  
   必须明确指出其与当前 bounded case 主链的具体连接点。
2. **non-peripheral relevance shown**  
   不能只是外围协调相关，而必须显示其已接近主判断链。
3. **new evidence introduced**  
   不能仅基于原有材料重复解释，必须有新 evidence 或新 trace。

### Re-entry Default
若三项中任一缺失：
- 保持 `No-Action / Bounded Out-of-Scope`
- 不进入 `Monitored Continuation`
- 不进入 `Bounded Review`

### Compression Effect
re-entry 现在从“弱相关就可重回观察”收紧为“必须具备明确 bounded linkage + 新证据”。

---

## 3. P3-Gap-02 Compression  
## Historical Similar-Case Evidence Use Gap

### Current Gap
历史相似变更案例具有启发价值，但若不加约束，容易被过度当作当前 case 的强支持证据。

### Compression Goal
让 historical similar-case evidence 只能作为 bounded support，而不能替代当前 case 的核心 evidence。

### Compressed Rule P3-C2
historical similar-case evidence 只允许作为 **bounded supporting evidence supplement**，并必须满足：

1. **analogy boundary explicit**  
   必须明确说明相似性在哪些方面成立，哪些方面不成立。
2. **non-substitution rule**  
   历史相似案例不得替代当前 case 的 G3/G4/G5/G6 required evidence。
3. **support-only positioning**  
   其作用仅限于：
   - 支持 review prioritization
   - 支持 bounded plausibility
   - 支持 monitored continuation relevance  
   不得直接支持 confirmed relevance / confirmed propagation / confirmed action。

### Invalid Uses
以下用法无效：
- 用历史相似案例替代当前 trace evidence
- 用历史相似案例替代当前 route-specific evidence
- 用历史相似案例替代 acceptance-level evidence

### Compression Effect
historical similar-case evidence 现在被正式限定为“辅助支持”，而不是“强证明替代品”。

---

## 4. P3-Gap-03 Compression  
## Narrative Override Risk Gap

### Current Gap
即使已建立 evidence thresholds 与 transition rules，后续维护中仍存在叙事性把握压倒规则纪律的风险。

### Compression Goal
让 narrative confidence 不能绕开规则门槛，尤其不能在 review 或维护轮中把弱证据说成强结论。

### Compressed Rule P3-C3
当 narrative statement 强于当前 evidence/disposition status 时，必须优先回看 rule status，而不是提升 narrative status。

### Operational Rule
出现以下情况时，默认触发 **narrative override caution**：

1. 叙事语言已经接近 confirmed，但 supporting evidence 仍停留在 G1/G2/G3  
2. 叙事语言把 review-required propagation 写成已确认传播  
3. 叙事语言把 bounded review 写成 action-ready  
4. 叙事语言把 monitored continuation 写成“基本确定”

### Required Response
一旦触发 narrative override caution：
- 不允许升级 disposition
- 应回看对应 evidence granularity
- 应回看对应 propagation status
- 必要时在 update log 中记录为 wording correction item

### Compression Effect
这条规则不是新增一个状态，而是给长期维护增加一个“反叙事漂移护栏”。

---

## 5. Compression Summary Table

| P3 Gap | Compression Rule | Main Effect |
|---|---|---|
| Outer-Scope Re-entry Strictness Gap | P3-C1 | blocks weak re-entry into main chain |
| Historical Similar-Case Evidence Use Gap | P3-C2 | limits analogy evidence to support-only role |
| Narrative Override Risk Gap | P3-C3 | blocks wording-driven overstatement |

---

## 6. Integration with Existing Rule System

### With P1 Compression
- P1 收紧强结论门槛
- P3 防止这些门槛在长期维护中被重新稀释

### With P2 Compression
- P2 增强一致性与解释力
- P3 增强长期 bounded discipline 与 wording discipline

### With Evidence Granularity
- P3-C2 明确历史相似案例不能替代 G3/G4/G5/G6
- P3-C3 要求 narrative 服从 evidence granularity

### With Disposition Transition
- P3-C1 限制 out-of-scope 对象重入主链
- P3-C3 阻断 narrative 对 disposition 的越级牵引

---

## 7. Current Research Judgment

### What this compression achieves
本文件使当前规则体系在三个长期风险点上更稳：
- 不轻易让外围对象重入
- 不过度依赖历史相似案例
- 不让 wording 强度超过 rule status

### What this compression does not yet solve
本文件不处理：
- multi-case comparative transferability
- broader methodology extraction
- implementation-level control logic

---

## 8. Latest Stable View
当前最稳定的 P3 压缩结论是：

当前 DGM 规则体系不仅更可防御、更一致、更可解释，也开始具备更强的边界纪律与长期维护纪律；因此当前单场景研究基线已从“更一致、更可解释”进一步推进到“更有边界自律性”。

## 9. Recommended Next Step
第五轮当前已完成核心压缩文件。  
下一步最合适的是：
`DGM_Fifth_Round_Validation_Check_v0.md`