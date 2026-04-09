# CASE-NPP-DGM-01_Case_File_v0

**Document Type**: Case File  
**Case ID**: CASE-NPP-DGM-01  
**Domain**: Nuclear Power Plant R&D Design and Engineering Construction  
**System Context**: AARS Research OS vNext  
**Version**: v0  
**Status**: Reviewable  
**Purpose**: 作为当前 bounded case 的正式工作文件，定义核电研发设计与工程建造阶段“设计变更影响分析模型场景”的目标、边界、对象范围与当前执行状态。

## 1. 案例名称
核电研发设计与工程建造阶段的设计变更影响分析模型场景。

## 2. 案例目标
验证模型治理驱动的数据治理底座，是否能够支撑设计变更影响分析模型对以下内容形成受控判断：
- 受影响设计基线对象
- 接口传播路径
- 受影响工程包
- 质保/检验证据更新需求
- 验证优先级与评审顺序

## 3. 案例边界

### In Scope
- 设计变更请求对象
- 设计依据与设计基线对象
- 多专业接口定义对象
- 受影响专业数据对象
- 工程包对象
- 检验/质保记录对象
- 设计变更影响分析模型对象
- 模型验证证据对象
- 模型使用边界对象

### Out of Scope
- 全厂级运行运维影响分析
- 企业级经营管理与计划协同
- 全量供应链与采购联动
- 全生命周期平台建设
- 具体软件系统实施与集成

## 4. 研究问题
当设计变更发生时，设计变更影响分析模型能否在受控数据治理底座上，识别影响范围、传播链和验证优先顺序，并使模型结论保持可追溯、可审计、可约束？

## 5. 首轮对象链
- Invocation context
- Dependency object
- Risk object
- Health snapshot
- No-recovery-needed conclusion

## 6. 当前关键对象

### 6.1 Design-Side Objects
- Requirement Object
- Design Basis Object
- Configuration Baseline Object
- Interface Definition Object
- Change Request Object

### 6.2 Construction-Side Objects
- Construction Package Object
- Inspection / QA Record Object
- As-Built Evidence Object

### 6.3 Model-Governance Objects
- Feature Object
- Model Object
- Validation Evidence Object
- Model Use Boundary Object
- Decision Support Output Object

## 7. 最小关系链
Change Request Object
→ Design Basis / Configuration Baseline / Interface Definition
→ Feature Object
→ Design Change Impact Analysis Model
→ Impact Scope / Affected Packages / Review Priority
→ Validation Evidence
→ Design Review / Construction Coordination Decision

## 8. 当前案例判断
该案例已具备 bounded case 的最小结构，适合进入 dependency / risk / health objectization。

## 9. 当前状态
- scope clarity: high
- object clarity: high
- dependency visibility: medium-high
- evidence depth: bounded
- stability: conditionally stable

## 10. 当前结论
本案例已足以作为核电研发设计与工程建造阶段的数据治理底座架构研究的首个 bounded validation case。