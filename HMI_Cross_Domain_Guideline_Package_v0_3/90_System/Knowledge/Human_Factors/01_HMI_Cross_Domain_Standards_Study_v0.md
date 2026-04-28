# 01 HMI Cross-Domain Standards Study v0

## 1. Purpose

本文件调研核电、船舶、航空航天及通用 HCI/告警管理标准，提炼适用于高可靠计算机界面的 HMI/HSI 设计原则。

本研究的核心判断是：高可靠行业中的人机接口不是普通信息展示界面，而是支撑操作者在复杂、高风险、动态环境下形成态势感知、做出判断、执行受控动作并完成异常恢复的任务控制界面。

## 2. Scope

适用于以下界面设计场景：

- 核电主控室、计算机化规程、数字化运行支持系统；
- 船舶导航、桥楼告警、多设备综合显示；
- 航空航天任务控制、多功能显示、自动化监控；
- AI agent 控制台；
- 多市场运行监控台；
- 工程研究操作系统界面；
- 安全关键或任务关键的工业软件界面。

## 3. Reference Standards

| Domain | Standard / Guide | Relevance |
|---|---|---|
| Nuclear | NUREG-0700 Rev.4 | HSI design review; information display; interaction; alarm; soft control; computer-based procedure; automation; degraded HSI/I&C conditions |
| Nuclear | NUREG-0711 | Human factors engineering program review model; useful for design lifecycle and V&V framing |
| Nuclear | IEC 60964 | Main control room design for nuclear power plants |
| Marine | IMO MSC.1/Circ.1609 | Standardized user interface for navigation equipment |
| Marine | IEC 62288 | Presentation of navigation-related information on shipborne displays |
| Marine | IEC 62923 | Bridge alert management / alert interfaces |
| Aviation | FAA HF-STD-001B | Human factors design standard covering automation, display, controls, alerts, input devices, workplace and HCI |
| Aerospace | NASA Human Systems Integration Handbook | Human-system integration principles across system lifecycle |
| General HCI | ISO 9241-110 | Dialogue principles for interactive systems |
| General HCI | ISO 9241-112 | Principles for information presentation |
| Alarm Management | IEC 62682 | Alarm management lifecycle based on control systems and HMI |

## 4. Cross-Domain Findings

### Finding 1 — HMI is a task-control interface

高可靠 HMI 的目标不是“把信息显示出来”，而是帮助操作者完成任务判断、风险识别、处置动作和结果验证。

### Finding 2 — Situation awareness is the primary design goal

界面必须支持三层态势感知：

1. 感知：当前发生了什么；
2. 理解：为什么重要，影响范围是什么；
3. 预测：接下来可能发生什么，是否需要动作。

### Finding 3 — Alarms must be actionable

告警不应只是消息提示，而应包含触发条件、严重度、影响范围、推荐动作、证据、确认状态和关闭条件。

### Finding 4 — Critical operations require gating

高影响动作必须经过前置条件检查、权限检查、风险检查、人工确认、执行反馈和审计记录。

### Finding 5 — Automation must be visible and overridable

自动化/AI 功能必须显示当前模式、输入、依据、置信度、边界、不可用条件和人工接管方式。

### Finding 6 — Degraded mode is a normal design case

数据缺失、模型不可用、接口失败、通信延迟、权限不足、视图降级等情况必须在界面中显性显示，并提供恢复路径。

### Finding 7 — Consistency is more important than local innovation

术语、缩写、图标、颜色、告警等级、快捷入口和关键按钮位置必须统一。

### Finding 8 — Design must be reviewable

高可靠 HMI 设计必须留下可审查证据，包括任务模型、信息架构、告警设计、操作门控、降级恢复和验证方法。

## 5. Stable Conclusion

高可靠计算机界面应按照以下模式设计：

```text
Task Situation
+ Risk / Alarm Management
+ Controlled Action
+ Automation Transparency
+ Degraded Mode Recovery
+ Reviewable Evidence
```

中文表达为：

```text
任务态势 + 风险告警 + 操作门控 + 自动化透明 + 降级恢复 + 审查证据
```

## 6. Recommended Use

本文件作为系统级知识文件，用于支撑后续 HMI 设计导则、项目页面设计、界面审查和 AI/自动化界面治理。
