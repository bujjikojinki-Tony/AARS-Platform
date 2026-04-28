# 06 HMI Design Review Checklist v0

## 1. Review Gate

每个界面进入实现前，必须通过 10 个 Gate。

| Gate | Question | Pass Criteria |
|---|---|---|
| G1 | 任务是否明确？ | 页面明确支持哪个任务 |
| G2 | 当前状态是否可见？ | 用户一眼看到系统/对象状态 |
| G3 | 最高风险是否可见？ | 最高风险不藏在 Tab 中 |
| G4 | 当前可执行动作是否明确？ | 用户知道现在能做什么 |
| G5 | 关键动作是否有门控？ | 高影响动作有条件检查 |
| G6 | 告警是否可处置？ | 告警包含原因、影响、动作 |
| G7 | 数据可信度是否显示？ | 显示更新时间、来源、可信度 |
| G8 | 自动化是否透明？ | 显示模式、依据、边界、接管 |
| G9 | 降级是否有恢复路径？ | 异常状态可恢复、可升级 |
| G10 | 是否形成审查证据？ | 有设计理由和验证方法 |

## 2. Page Review Template

```yaml
page_name:
page_owner:
task_supported:
user_role:
operating_context:
critical_decisions:
information_required:
operator_actions:
alarms_involved:
automation_involved:
failure_modes:
degraded_modes:
design_rationale:
review_gate_result:
open_issues:
verification_method:
test_cases:
final_disposition:
```

## 3. Review Disposition

| Disposition | Meaning |
|---|---|
| Accept | 可进入实现 |
| Accept with Minor Issues | 可实现，但需记录小问题 |
| Defer | 信息不足，暂缓 |
| Block | 存在安全/任务关键问题，不可实现 |
| Rework | 需要重构设计 |

## 4. Required Evidence

每次审查至少保留：

- 页面草图或截图；
- 页面任务模型；
- 信息架构说明；
- 告警/降级设计说明；
- 自动化/AI 说明；
- Gate 检查结果；
- 未关闭问题；
- 最终处置结论。

## 5. Minimum Review Record

```yaml
review_id:
review_date:
reviewer:
page:
version:
gate_result:
major_findings:
minor_findings:
blocking_issues:
final_disposition:
next_action:
```
