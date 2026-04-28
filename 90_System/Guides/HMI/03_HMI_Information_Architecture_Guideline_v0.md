# 03 HMI Information Architecture Guideline v0

## 1. Page Hierarchy

高可靠界面应采用四层信息结构：

| Layer | Name | Purpose |
|---|---|---|
| L1 | Overview | 总体态势、关键风险、当前任务 |
| L2 | Current Task | 当前步骤、输入、动作、验证 |
| L3 | Diagnosis | 原因、依赖、证据、日志 |
| L4 | Raw Data | 表格、JSON、历史记录、接口返回 |

## 2. Overview Page Rules

Overview 页面必须显示：

- 系统总体状态；
- 最高优先级告警；
- 当前任务；
- 关键对象状态；
- 最新稳定视图；
- 数据更新时间；
- 数据可信度；
- 降级状态；
- 进入当前任务、告警中心、恢复路径的快捷入口。

## 3. Recommended Layout

```text
Top Bar:
  system status / time / data freshness / automation mode

Left Panel:
  object list / task list / market list / system list

Center Panel:
  selected object main situation view

Right Panel:
  alarm queue / risk queue / opportunity queue

Bottom Bar:
  latest stable view / current step / quick action / recovery path
```

## 4. Information Display Rule

任何关键指标必须同时显示：

- 当前值；
- 阈值；
- 正常范围；
- 趋势；
- 更新时间；
- 数据源；
- 可信度；
- 风险解释；
- 推荐动作。

## 5. Status Encoding

| State | Meaning | Required UI |
|---|---|---|
| Normal | 正常 | 文本 + 稳定状态标识 |
| Watch | 观察 | 观察标签 + 原因 |
| Caution | 注意 | 黄色/提示图标 + 文本说明 |
| Warning | 警告 | 橙色/风险图标 + 推荐动作 |
| Critical | 危急 | 红色/阻塞标识 + 立即动作 |
| Degraded | 降级 | 降级标签 + 影响范围 |
| Unknown | 未知 | 未知标签 + 待确认条件 |

颜色不能作为唯一表达方式，必须配合文本、图标、位置或形状。

## 6. Table Design Rules

高可靠界面的表格应支持：

- 默认按风险排序；
- 关键列固定；
- 异常行突出；
- 可解释排序；
- 可筛选状态；
- 可展开证据；
- 可跳转处置页。

## 7. Anti-Patterns

禁止：

- 首页堆叠全部图表；
- 关键告警藏在 Tab 中；
- 原始 JSON 放在首页；
- 关键动作超过两次点击；
- 只显示数值，不显示阈值和趋势；
- 只显示颜色，不显示文本状态；
- 禁用按钮不说明原因。
