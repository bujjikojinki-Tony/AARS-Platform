# 02 HMI Design Principles v0

## 1. Design Thesis

高可靠计算机界面不是 dashboard，而是人机协同控制台。

其目标是帮助操作者：

1. 感知当前状态；
2. 理解当前风险；
3. 判断下一步动作；
4. 执行受控操作；
5. 验证操作结果；
6. 在异常时恢复到稳定状态。

## 2. Core Principles

### P1 — Task-First

界面应围绕任务组织，而不是围绕数据库、模块或菜单组织。

每个页面必须回答：

- 当前任务是什么？
- 当前状态是什么？
- 为什么重要？
- 用户现在能做什么？
- 做完后如何验证？

### P2 — Situation-Aware

首页必须显示：

- 系统总体状态；
- 当前关键任务；
- 最高优先级风险；
- 最新稳定视图；
- 数据更新时间；
- 降级状态；
- 可执行动作。

### P3 — Alarm-as-Action

告警不是消息，而是处置对象。

每条告警必须包含：

- 触发条件；
- 影响范围；
- 严重度；
- 推荐动作；
- 证据；
- 当前处置状态；
- 关闭条件。

### P4 — Controlled Action

关键操作必须经过：

- 条件检查；
- 风险检查；
- 权限检查；
- 二次确认；
- 执行反馈；
- 操作记录；
- 结果验证。

### P5 — Automation Transparency

自动化与 AI 必须显示：

- 当前模式；
- 输入数据；
- 判断依据；
- 置信度；
- 适用边界；
- 人工接管方式；
- 审计记录。

### P6 — Degraded Mode Visibility

当数据、模型、接口、自动化、权限或视图降级时，界面必须显性显示。

### P7 — Consistency Before Novelty

术语、缩写、颜色、图标、按钮、状态、告警等级和快捷入口必须统一。

### P8 — Reviewable by Design

每个关键界面必须可审查、可验证、可追溯。

## 3. General HMI Pattern

```text
Goal
→ Situation
→ Risk
→ Action
→ Evidence
→ Verification
→ Recovery
```

## 4. Anti-Patterns

禁止以下设计模式：

- 首页堆叠大量图表但没有主态势；
- 告警隐藏在多层 Tab；
- 按钮置灰但不说明原因；
- AI 给出建议但没有证据；
- 自动化状态不可见；
- 异常状态只显示错误但不给恢复路径；
- 关键操作没有前置条件检查；
- 只按模块组织界面，不按任务组织界面。
