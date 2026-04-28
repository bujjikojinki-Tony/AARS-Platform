# 05 HMI Automation and AI Interface Guideline v0

## 1. Automation Visibility

任何自动化或 AI 功能必须显示：

- 当前是否开启；
- 当前模式；
- 输入数据；
- 判断依据；
- 输出结果；
- 置信度；
- 适用边界；
- 不可用条件；
- 人工接管方式；
- 审计记录。

## 2. AI Recommendation Card

```yaml
recommendation_id:
recommendation:
reason:
input_data:
evidence:
confidence:
risk:
assumption:
boundary:
human_action_required:
audit_record:
```

## 3. AI Authority Levels

| Level | Capability | Human Requirement |
|---|---|---|
| AI-L0 | 信息显示 | 无需确认 |
| AI-L1 | 分析解释 | 人工判断 |
| AI-L2 | 行动建议 | 人工确认 |
| AI-L3 | 半自动执行 | 人工授权 + 过程监控 |
| AI-L4 | 自动执行 | 仅限低风险、可回滚任务 |
| AI-L5 | 自主闭环 | 高可靠领域默认不采用 |

## 4. Forbidden Patterns

禁止：

- 黑箱“一键优化”；
- 无证据的智能推荐；
- 无置信度的模型判断；
- 无人工接管的自动动作；
- 无审计记录的自动化操作；
- 高风险动作默认自动执行。

## 5. Recommended AI Action Format

```text
Action:
  Run market-weather divergence scan

Input:
  latest weather forecast + market probability + historical forecast error

Output:
  candidate abnormal markets

Boundary:
  analysis only, no automatic trading

Human Required:
  confirm watchlist promotion
```

## 6. Design Review Questions

- AI 是否只是在显示信息，还是在提出动作？
- AI 建议是否有证据？
- 是否显示置信度？
- 是否说明适用边界？
- 是否存在误用风险？
- 是否允许人工接管？
- 是否记录 AI 输出和人工处置？
