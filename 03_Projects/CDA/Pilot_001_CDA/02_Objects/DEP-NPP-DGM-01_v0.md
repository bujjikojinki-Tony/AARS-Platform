# DEP-NPP-DGM-01_v0

**Document Type**: Dependency Object  
**Project Context**: Model-Governed Data Governance Foundation for Nuclear Design and Construction  
**Case ID**: CASE-NPP-DGM-01  
**Object ID**: DEP-NPP-DGM-01  
**Version**: v0  
**Status**: Reviewable  
**Purpose**: 描述设计变更影响分析模型场景中的关键依赖结构、依赖主轴与高杠杆依赖点。

## 1. Dependency Name
Design-Baseline / Interface / Construction-Package Dependency Cluster

## 2. Dependency Role
该依赖对象用于说明：
- 模型输入是否建立在受控设计基线之上
- 变更影响是否能通过接口定义传播识别
- 设计影响是否能映射到工程包与质保证据链
- 模型输出是否具备足够的治理可信度

## 3. Primary Dependencies

### Dependency 1
设计变更请求必须绑定到正式受控的 Configuration Baseline Object。

### Dependency 2
Configuration Baseline Object 必须可映射到 Design Basis Object 与 Interface Definition Object。

### Dependency 3
Interface Definition Object 必须可映射到受影响专业对象与相关专业数据对象。

### Dependency 4
受影响专业对象必须可进一步映射到 Construction Package Object。

### Dependency 5
Construction Package Object 必须可关联到 Inspection / QA Record Object 与 As-Built Evidence Object。

### Dependency 6
Model Object 的输入特征必须来源于已受控的变更对象、基线对象、接口对象与工程对象。

### Dependency 7
Validation Evidence Object 必须能绑定到模型输出结论，而不是脱离场景独立存在。

## 4. Dependency Structure Type
- baseline dependency
- interface dependency
- cross-discipline dependency
- construction handoff dependency
- evidence-binding dependency

## 5. Highest-Leverage Dependency
**Configuration Baseline ↔ Interface Definition**

原因：
- 它决定设计变更是否真正进入受控传播链
- 它决定模型是否能识别跨专业传播
- 它决定后续工程包影响是否只是表面映射，还是结构性影响判断

## 6. Dependency Failure Conditions
若出现以下情况，则该 dependency cluster 被视为失稳：
- 设计变更请求未绑定正式基线
- 接口定义版本不一致
- 专业对象映射关系不完整
- 工程包与设计对象缺少映射
- 质保证据链无法回连到变更与模型结论

## 7. Dependency Risk Implication
若 dependency cluster 失稳，模型可能：
- 低估传播范围
- 漏掉受影响工程包
- 错判验证优先顺序
- 输出不可审计的决策建议

## 8. Dependency Judgment
- leverage: high
- propagation sensitivity: high
- cross-stage relevance: high
- current confidence: medium
- bounded usability: high

## 9. Current Conclusion
该 dependency object 已足以支撑首轮 bounded case，但后续仍需对基线—接口—工程包映射做 second-pass strengthening。