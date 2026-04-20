---
title: DGM_Rule_Gap_Compression_Note_v0
doc_type: rule_gap_compression_note
project: Pilot_001_CDA
domain: nuclear_design_construction
case_id: CASE-NPP-DGM-01
version: v0
status: reviewable
stability: p1_gap_compression_baseline
aars_step: objectized_case_execution
scope_type: bounded_case
tags:
  - AARS
  - CDA
  - DGM
  - rule-gap
  - compression
  - nuclear
  - baseline
---

## Links
- Home: [[Pilot_001_CDA_Home]]
- MOC: [[DGM_CASE_NPP_01_MOC]]
- Rule Gap List: [[DGM_Rule_Gap_List_v0]]
- Rule Validation: [[../03_Reviews/DGM_Rule_Validation_Note_v0]]
- Evidence Granularity: [[DGM_Evidence_Granularity_Note_v0]]
- Disposition Transition: [[DGM_Disposition_Transition_Rulebook_v0]]
- Evidence Requirement: [[DGM_Evidence_Requirement_Note_v0]]
- Disposition Framework: [[DGM_Governance_Disposition_Framework_v0]]
- Propagation Note: [[DGM_Propagation_Pattern_Note_v0]]
- Impact Matrix: [[DGM_Impact_Object_Matrix_v0]]

# DGM_Rule_Gap_Compression_Note_v0

## Position
本文件用于对 `CASE-NPP-DGM-01` 当前规则体系中已识别的 **P1 rule gaps** 做有界压缩。  
其目标不是重写整个规则系统，而是让最关键的强结论门槛和强状态门槛更紧。

## Current Objective
本文件只处理以下四个 P1 gaps：

1. G5 Consequence-Specific Evidence Minimum Threshold Gap  
2. QA / Inspection Relevance Confirmation Gap  
3. Conflicting Evidence Precedence Gap  
4. Acceptance Evidence Loss Response Gap  

---

## Scope

### In Scope
- G5 minimum threshold tightening
- QA / inspection confirmation tightening
- conflicting evidence precedence tightening
- G6 loss response tightening

### Out of Scope
- P2 gaps
- P3 gaps
- second case comparison
- implementation workflow
- new object family expansion

---

## 1. Compression Use Rules

### Rule 1
本轮压缩只允许 tightening，不允许新增大结构。

### Rule 2
任何 compression rule 都必须直接服务于：
- stronger confirmation discipline
- stronger downgrade discipline
- stronger conflict handling discipline

### Rule 3
若某 gap 不直接影响强结论或强状态，不在本轮压缩。

### Rule 4
压缩规则应优先减少“误升级”，而不是追求“更多可升级”。

---

## 2. P1-Gap-01 Compression  
## G5 Consequence-Specific Evidence Minimum Threshold

### Current Gap
当前 G5 已存在，但“达到什么最小粒度才算 consequence-specific evidence”仍偏粗。

### Compression Goal
禁止将一般 construction relevance 表述误写成 confirmed construction-relevant impact。

### Compressed Rule C1
只有同时满足以下三项，才可判定为 **G5-valid consequence-specific evidence**：

1. **specific target named**  
   必须明确到具体 consequence target，而不是泛指“建造影响”。
2. **specific consequence domain named**  
   必须明确是 package / installation sequence / QA / inspection 哪一类后果域。
3. **specific linkage stated**  
   必须说明 source object 如何进入该后果域，而不是只说“可能影响”。

### Invalid Forms
以下情况不得视为 G5-valid：
- “可能影响施工”
- “可能涉及质量调整”
- “可能影响工程包安排”
- 未说明具体 target / domain / linkage 的 consequence assertion

### Compression Effect
没有满足 C1 三条件时：
- 最多停留在 G4 route-specific consequence tendency
- 不得升级为 confirmed construction-relevant impact

---

## 3. P1-Gap-02 Compression  
## QA / Inspection Relevance Confirmation

### Current Gap
QA / inspection relevance 最容易被写得过强，但确认门槛仍不够细。

### Compression Goal
让 QA / inspection relevance 只有在明确进入“记录/检验点/质保动作”时才能升级。

### Compressed Rule C2
只有同时满足以下三项，QA / inspection relevance 才可进入 confirmed consequence status：

1. **specific QA / inspection object named**  
   必须指向 record class、inspection point、QA action type 或等价对象。
2. **explicit relevance reason stated**  
   必须说明为什么该 QA / inspection object 被影响。
3. **update or review condition stated**  
   必须说明它是需要 update、re-check 还是 review，不得只说“有 QA 影响”。

### Default Fallback
若只满足其中 1–2 项：
- 默认保持在 `Bounded Review`
- 不得直接进入 `Confirmed Action`

### Compression Effect
QA / inspection 将不再因为 generic consequence wording 被过快升级。

---

## 4. P1-Gap-03 Compression  
## Conflicting Evidence Precedence

### Current Gap
当不同 evidence 指向不同结论时，尚无足够明确的 precedence rule。

### Compression Goal
避免 narrative confidence override evidence discipline。

### Compressed Rule C3
当 evidence 冲突时，优先级按以下顺序处理：

### Precedence Order
1. **Acceptance failure overrides consequence confidence**
2. **Consequence failure overrides route confidence**
3. **Route failure overrides reference confidence**
4. **Trace failure overrides mere presence/reference**

换句话说：

- G6 缺失优先触发对强 action 的 review
- G5 不成立，优先阻断 confirmed consequence
- G4 不成立，优先阻断 confirmed propagation
- G3 不成立，优先阻断 confirmed relevance

### Operational Meaning
若高层级 required evidence 缺失，低层级 supporting evidence 不得补位越级。

### Compression Effect
这条规则直接压缩了“弱强混合证据被叙事性解释成强结论”的空间。

---

## 5. P1-Gap-04 Compression  
## Acceptance Evidence Loss Response

### Current Gap
虽已知道 G6 缺失会触发 review，但“何时立即回退”还不够紧。

### Compression Goal
让 confirmed action 对 acceptance evidence loss 更敏感、更一致。

### Compressed Rule C4
以下任一情况成立时，`Confirmed Action` 必须立即降级为 `Bounded Review`：

1. applicability boundary no longer explicit  
2. output-to-evidence binding no longer explicit  
3. review condition missing or withdrawn  
4. output limitation statement missing when previously required

### No-Hold Rule
在 C4 条件触发时，不允许：
- 保持 `Confirmed Action`
- 用 narrative confidence 暂时维持强状态

### Compression Effect
G6 不再只是“最好有”，而成为 confirmed action 的真实保留门槛。

---

## 6. Compression Summary Table

| Gap | Compression Rule | Main Effect |
|---|---|---|
| P1-Gap-01 | C1: G5 must name target + domain + linkage | blocks generic consequence inflation |
| P1-Gap-02 | C2: QA confirmation requires object + reason + action condition | blocks premature QA-related upgrades |
| P1-Gap-03 | C3: higher-level required evidence overrides lower-level support | blocks narrative override under conflict |
| P1-Gap-04 | C4: loss of G6 triggers immediate downgrade | protects confirmed action discipline |

---

## 7. Integration with Existing Rule System

### With Evidence Granularity
- C1 tightens G5
- C4 tightens G6 retention discipline

### With Disposition Transition
- C2 limits premature escalation to `Confirmed Action`
- C4 strengthens downgrade logic from `Confirmed Action` to `Bounded Review`

### With Propagation Note
- C1 ensures route-specific relevance does not automatically become consequence-specific confirmation

### With Rule Validation
- C3 responds directly to conflict-handling weakness
- C4 responds directly to confirmed-action stability weakness

---

## 8. Current Research Judgment

### What this compression achieves
本文件使当前规则体系在四个最危险位置更紧：
- consequence confirmation
- QA relevance confirmation
- conflicting evidence precedence
- acceptance loss response

### What this compression does not yet solve
本文件没有处理：
- transition timing discipline
- installation sequence detail
- bundle conflict nuance
- outer-scope re-entry strictness

这些仍留给 P2 / P3 或后续轮次。

---

## 9. Latest Stable View
当前最稳定的压缩结论是：

当前 DGM 规则体系最关键的 P1 gaps 已获得有界压缩；因此 single-case rule-strengthened baseline 现在比第二轮结束时更具防误升级、防弱证据越级和防 acceptance-loss 漂移的能力。

## 10. Recommended Next Step
第三轮当前已完成：
- gap identification
- P1 gap compression

下一步最合适的是：
- 生成一个很小的 `DGM_Third_Round_Validation_Check_v0.md`
- 或直接形成 `DGM_Third_Round_Completion_Note_v0.md`