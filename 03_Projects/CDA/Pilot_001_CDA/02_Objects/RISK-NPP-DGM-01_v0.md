---
title: RISK-NPP-DGM-01_v0
doc_type: risk_object
project: Pilot_001_CDA
domain: nuclear_design_construction
case_id: CASE-NPP-DGM-01
object_id: RISK-NPP-DGM-01
version: v0
status: reviewable
stability: conditionally_stable
aars_step: objectized_case_execution
primary_risk: design_change_propagation_misjudgment
scope_type: bounded_case
tags:
  - AARS
  - CDA
  - DGM
  - risk
  - nuclear
  - design-change
  - object
---
## Links
- Case: [[CASE-NPP-DGM-01_Case_File_v0]]
- Dependency: [[DEP-NPP-DGM-01_v0]]
- Health: [[HEALTH-NPP-DGM-01_v0]]
- Control: [[CTRL-NPP-DGM-01_v0]]
- Review: [[Pilot_001_DGM_Final_Review_Note_v1]]
- Strengthening: [[DGM_Second_Pass_Strengthening_Note_v0]]
- Baseline: [[DGM_Glossary_Taxonomy_Mini_Baseline_v0]]
# RISK-NPP-DGM-01_v0

**Document Type**: Risk Object  
**Project Context**: Model-Governed Data Governance Foundation for Nuclear Design and Construction  
**Case ID**: CASE-NPP-DGM-01  
**Object ID**: RISK-NPP-DGM-01  
**Version**: v0  
**Status**: Reviewable  
**Purpose**: 描述设计变更影响分析模型场景中的主要 bounded risk，包括触发条件、传播条件与风险判断。

## 1. Risk Name
Design Change Propagation Misjudgment Risk

## 2. Risk Role
该风险对象用于表达：
- 设计变更影响分析模型在治理底座不完整时的主要失真风险
- 影响传播范围误判的主要来源
- 为什么该场景需要先强调 dependency 和 evidence，而不是只强调模型算法

## 3. Core Risk Statement
当设计变更影响分析模型所依赖的数据治理底座不完整时，模型可能错误判断设计变更的实际影响范围，进而低估跨专业传播、遗漏受影响工程包、忽视质保证据更新需求，或把证据不足的模型输出当成可直接采用的工程决策依据。

## 4. In-Scope Risk Focus
- 设计基线绑定不足风险
- 接口传播关系识别不足风险
- 工程包落地影响遗漏风险
- 质保/检验证据链断裂风险
- 模型验证证据不足风险

## 5. Out-of-Scope Risk Focus
- 企业级信息安全总体风险
- 全厂运行运维总体风险
- 通用 AI 伦理治理全域风险
- 项目经营与合同风险
- 非本场景相关供应链风险

## 6. Risk Triggers
1. Change Request Object 未绑定正式 Configuration Baseline
2. Interface Definition Object 存在版本冲突或未更新
3. 受影响专业对象映射关系不完整
4. Construction Package Object 未与设计对象建立稳定映射
5. Inspection / QA Record Object 无法回连变更来源
6. Model Object 的 Validation Evidence 不足或适用边界不清晰

## 7. Propagation Conditions
该风险在以下条件下放大：
- 变更跨越多个专业接口
- 变更已进入工程包下发阶段
- 施工准备或质量活动已部分展开
- 变更涉及高杠杆配置基线对象
- 模型结论被用于加速评审或缩短人工核查路径

## 8. Severity Judgment
**High-attention, bounded, propagation-capable risk**

## 9. Evidence Discipline
当前风险对象应遵循以下证据规则：
- 已确认依赖高于假设依赖
- 已确认传播链高于潜在传播链
- 已绑定正式基线高于草稿状态基线
- 证据不足应保留为 unresolved item，不应伪装为强结论

## 10. Unresolved Items
- 接口定义更新滞后的实际概率
- 工程包与设计对象映射的完整程度
- 质保记录回链粒度是否足够
- 模型适用边界是否需要更严格收缩

## 11. Current Conclusion
该风险对象已足以用于首轮场景控制与评审，但仍应在 second-pass 中强化 evidence binding 与 propagation discrimination。