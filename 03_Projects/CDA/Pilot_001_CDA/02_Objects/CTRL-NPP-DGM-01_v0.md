# CTRL-NPP-DGM-01_v0

**Document Type**: Control Priority Note  
**Project Context**: Model-Governed Data Governance Foundation for Nuclear Design and Construction  
**Case ID**: CASE-NPP-DGM-01  
**Object ID**: CTRL-NPP-DGM-01  
**Version**: v0  
**Status**: Reviewable  
**Purpose**: 将设计变更影响分析模型场景中的 dependency 与 risk 结果转化为 bounded control priority、verification order 与 review sequencing。

## 1. Control Priority Role
本对象用于回答三个问题：
1. 当前案例中最应优先确认的控制面是什么。  
2. 哪些验证动作应先做。  
3. 如何在 bounded case 内避免 false precision 和过度扩张。

## 2. Priority Principle
优先级不基于细碎数值打分。  
优先级基于以下四个 bounded factors：
1. baseline relevance
2. interface propagation leverage
3. construction handoff sensitivity
4. evidence controllability within current case boundary

## 3. Priority Groups

### Group A — Immediate Attention
1. Configuration Baseline binding confirmation  
2. Interface Definition version and propagation confirmation  
3. Change Request to affected discipline mapping confirmation  

**Reason**:  
这三项决定模型是否真正建立在受控变更链上。若这三项不稳，后续工程包与质保证据判断都会失真。

---

### Group B — Near-Term Control
4. Construction Package impact mapping confirmation  
5. Inspection / QA Record update relevance confirmation  
6. Model Validation Evidence applicability confirmation  

**Reason**:  
这三项决定模型输出是否能够进入设计评审和建造协调，而不仅仅停留在分析建议层。

---

### Group C — Monitored Continuation
7. Peripheral downstream document updates  
8. Outer-scope coordination assumptions  
9. Low-confidence inferred propagation paths  

**Reason**:  
这些对象仍值得监视，但在当前 bounded case 中不应抢占主控制顺序。

## 4. Verification Order
建议验证顺序如下：

### Step 1
确认 Change Request 是否绑定正式 Configuration Baseline Object。

### Step 2
确认 Configuration Baseline 与 Interface Definition 是否版本一致、是否已更新。

### Step 3
确认 Interface Definition 到 affected discipline objects 的传播关系。

### Step 4
确认 affected discipline objects 是否已映射到 Construction Package Object。

### Step 5
确认 Construction Package 是否已触发 Inspection / QA Record 相关更新需求。

### Step 6
确认 Model Validation Evidence 是否覆盖当前使用边界。

## 5. Control Targets by Layer

### Object Targets
- Configuration Baseline Object
- Interface Definition Object
- Change Request Object
- Construction Package Object
- Inspection / QA Record Object
- Validation Evidence Object

### Relation Targets
- baseline dependency
- interface dependency
- cross-discipline propagation dependency
- construction handoff dependency
- evidence-binding dependency

### Risk Targets
- propagation misjudgment
- construction impact omission
- evidence-insufficient decision support

## 6. False-Precision Reduction Rules
本控制优先级对象明确避免：
- 无证据支撑的精细化 1-to-N 排序
- 把 outer-scope 对象强行纳入 immediate control
- 把模型输出误当作自动决策结果
- 把场景控制优先级写成全项目控制清单

## 7. Actionability Judgment
该控制优先级输出适合用于：
- bounded review sequencing
- verification sequencing
- architecture validation closure
- second-pass strengthening planning

不适用于：
- full project execution plan
- software implementation roadmap
- enterprise governance rollout plan

## 8. Unresolved Control Questions
仍需 review 的问题：
- Group B 中是否有项应提升到 Group A
- QA record relevance 的确认粒度是否需要更细
- validation evidence applicability 是否需要更严格边界
- inferred propagation paths 是否需要建立单独的 caution subgroup

## 9. Current Conclusion
该控制优先级对象已足以支撑 CASE-NPP-DGM-01 的第一轮 bounded closure。后续应在 second-pass 中强化 Group A/B 边界、验证顺序说明和 evidence linkage。