# DGM_Glossary_Taxonomy_Mini_Baseline_v0

**Document Type**: Glossary + Taxonomy Mini-Baseline  
**Project Context**: Model-Governed Data Governance Foundation Architecture Study  
**Primary Case**: CASE-NPP-DGM-01  
**System Context**: AARS Research OS vNext  
**Version**: v0  
**Status**: Reviewable  
**Purpose**: 为“核电研发设计与工程建造阶段的设计变更影响分析模型场景”提供最小术语与标签基线，减少 object / relation / risk / output 表达中的漂移与重叠。

## 1. Baseline Role
本 mini-baseline 的作用是：
- 固定当前场景中的核心命名
- 区分 object、relation、risk、output 四类标签
- 避免把对象、关系、风险和输出类型混写
- 为后续 second-pass / third-pass strengthening 提供统一表达基线

## 2. Use Rules
### Rule 1
对象标签只描述“分析对象是什么”，不描述其关系或风险。

### Rule 2
关系标签只描述“对象之间如何连接”，不充当对象名称。

### Rule 3
风险标签只描述“何种失真、遗漏、传播或不充分状态”，不替代对象标签或关系标签。

### Rule 4
输出标签只描述“当前产物是什么类型”，不描述领域对象本身。

### Rule 5
任何输出中都应尽量保持：
- 一个对象一个主对象标签
- 一个关系一个主关系标签
- 一个风险一个主风险标签
- 一个文件一个主输出标签

## 3. Glossary Baseline

### 3.1 Core Scope Terms

#### DGM Scenario
Design Change Governance Model Scenario。  
指当前核电研发设计与工程建造阶段中，以设计变更影响分析模型为主轴的 bounded validation 场景。

#### Bounded Case
有界案例。  
指边界、对象、输入、输出与判断范围被明确控制的最小验证案例。

#### Model-Governed Data Governance Foundation
模型治理驱动型数据治理底座。  
指围绕模型生命周期、模型证据、模型边界和模型控制需求来组织数据治理对象链与证据链的基础治理结构。

### 3.2 Object Terms

#### Change Request
设计变更请求对象。  
是当前场景的主触发对象。

#### Baseline Object
设计基线对象。  
指受控的设计依据、配置基线或正式版本化设计对象。

#### Interface Object
接口对象。  
指用于连接不同专业、系统、模型或工程对象的接口定义对象。

#### Affected Discipline Object
受影响专业对象。  
指因设计变更而被判断为需要复核、更新或重新协调的专业对象。

#### Construction Package Object
工程包对象。  
指设计变更可能进一步影响到的施工、安装、建造执行包对象。

#### QA / Inspection Record Object
质保/检验记录对象。  
指用于承接建造质量、检验、验证或记录更新要求的对象。

#### Evidence Object
证据对象。  
指支撑模型结论、影响判断、传播判断或控制优先级的证据性对象。

#### Decision-Support Output Object
决策支持输出对象。  
指模型或分析过程输出的影响范围、优先级、传播判断或审查建议。

### 3.3 Relation Terms

#### Baseline Dependency
基线依赖。  
指 Change Request、专业对象或模型输入对正式设计基线的依赖关系。

#### Interface Propagation Dependency
接口传播依赖。  
指设计变更沿接口定义跨专业传播的关系。

#### Construction Handoff Dependency
建造交接依赖。  
指设计对象、接口对象或专业对象向工程包和建造活动传递影响的关系。

#### Evidence-Binding Dependency
证据绑定依赖。  
指模型结论、影响判断或风险判断必须绑定到相应证据对象的关系。

### 3.4 Risk Terms

#### Misjudgment Risk
误判风险。  
指由于对象映射、关系识别或证据绑定不足，导致影响范围或优先级判断失真的风险。

#### Cross-Discipline Propagation Risk
跨专业传播风险。  
指设计变更通过接口关系传播到其他专业对象而未被充分识别的风险。

#### Construction-Impact Omission Risk
建造影响遗漏风险。  
指设计变更已影响工程包或建造活动，但影响未被及时纳入判断链的风险。

#### Evidence-Insufficiency Risk
证据不足风险。  
指模型输出或评审判断缺少足够绑定证据而不应被视为高可信结论的风险。

### 3.5 Output Terms

#### Case File
案例文件。  
定义 bounded case 的目标、边界、对象与状态。

#### Dependency Object
依赖对象。  
定义关键依赖链及高杠杆依赖点。

#### Risk Object
风险对象。  
定义主风险、触发条件、传播条件和严重度判断。

#### Health Snapshot
健康快照。  
定义当前 bounded case 的状态、稳定性与继续条件。

#### Control Priority Note
控制优先级说明。  
定义当前案例中的 control groups 与 verification order。

#### Final Review Note
最终审查说明。  
定义本轮工作的收口判断、完成项、缺口与下一步建议。

#### Strengthening Note
强化说明。  
定义 second-pass 或后续强化动作的目标与强化点。

## 4. Taxonomy Baseline

### 4.1 Layer Structure
本 mini-taxonomy 采用四层结构：
1. Object Layer
2. Relation Layer
3. Risk Layer
4. Output Layer

---

## 5. Object Layer

### 5.1 Preferred Object Labels
- change request
- baseline object
- interface object
- affected discipline object
- construction package object
- QA / inspection record object
- evidence object
- decision-support output object

### 5.2 Object Layer Rule
对象标签只回答：
**“当前分析对象是什么？”**

### 5.3 Anti-Overlap Examples
- “construction handoff dependency” 不是 object label
- “misjudgment risk” 不是 object label
- “risk object” 不是 object label

---

## 6. Relation Layer

### 6.1 Preferred Relation Labels
- baseline dependency
- interface propagation dependency
- construction handoff dependency
- evidence-binding dependency

### 6.2 Relation Layer Rule
关系标签只回答：
**“对象之间以什么方式连接或传播？”**

### 6.3 Anti-Overlap Examples
- “baseline object” 不是 relation label
- “construction-impact omission risk” 不是 relation label
- “dependency object” 不是 relation label

---

## 7. Risk Layer

### 7.1 Preferred Risk Labels
- misjudgment risk
- cross-discipline propagation risk
- construction-impact omission risk
- evidence-insufficiency risk

### 7.2 Risk Layer Rule
风险标签只回答：
**“当前最值得警惕的失真、遗漏或不充分状态是什么？”**

### 7.3 Anti-Overlap Examples
- “interface object” 不是 risk label
- “construction handoff dependency” 不是 risk label
- “health snapshot” 不是 risk label

---

## 8. Output Layer

### 8.1 Preferred Output Labels
- case file
- dependency object
- risk object
- health snapshot
- control priority note
- final review note
- strengthening note

### 8.2 Output Layer Rule
输出标签只回答：
**“当前文档或对象的产物类型是什么？”**

### 8.3 Anti-Overlap Examples
- “change request” 不是 output label
- “misjudgment risk” 不是 output label
- “baseline dependency” 不是 output label

---

## 9. Controlled Expression Patterns

### 9.1 Object Expression Pattern
建议写法：
- Change Request Object
- Baseline Object
- Interface Object
- Construction Package Object

不建议写法：
- baseline propagation object
- risk interface object
- dependency package node

### 9.2 Relation Expression Pattern
建议写法：
- A has baseline dependency on B
- A propagates to B through interface dependency
- A affects B through construction handoff dependency

不建议写法：
- A is a dependency object to B
- A is a risk relation object

### 9.3 Risk Expression Pattern
建议写法：
- misjudgment risk under incomplete baseline evidence
- construction-impact omission risk under weak handoff mapping
- evidence-insufficiency risk for decision-support output

不建议写法：
- generic high risk
- broad system risk
- all-stage propagation risk

---

## 10. Current Controlled Label Set for CASE-NPP-DGM-01

### Object Labels
- change request
- baseline object
- interface object
- affected discipline object
- construction package object
- QA / inspection record object
- evidence object
- decision-support output object

### Relation Labels
- baseline dependency
- interface propagation dependency
- construction handoff dependency
- evidence-binding dependency

### Risk Labels
- misjudgment risk
- cross-discipline propagation risk
- construction-impact omission risk
- evidence-insufficiency risk

### Output Labels
- case file
- dependency object
- risk object
- health snapshot
- control priority note
- final review note
- strengthening note

---

## 11. Current Stability Judgment
- terminology clarity: improved
- label overlap reduction: improved
- bounded usability: high
- cross-case reuse readiness: medium
- domain-wide finality: not allowed yet

## 12. Conclusion
本 mini-baseline 已足以作为 CASE-NPP-DGM-01 当前 working baseline。  
后续所有 second-pass / third-pass 修订，建议优先以本标签集回写既有对象，而不是继续发明新术语。