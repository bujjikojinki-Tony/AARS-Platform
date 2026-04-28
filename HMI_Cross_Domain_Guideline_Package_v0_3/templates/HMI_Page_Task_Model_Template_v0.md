# HMI Page Task Model Template v0

## 1. Page Identity

```yaml
page_name:
page_type:
system:
version:
owner:
```

## 2. Supported Task

```yaml
task_name:
task_goal:
user_role:
operating_context:
normal_condition:
abnormal_condition:
degraded_condition:
```

## 3. Required Information

```yaml
input_data:
system_status:
risk_status:
alarm_status:
automation_status:
data_quality:
historical_context:
```

## 4. User Decisions

```yaml
decision_1:
  question:
  required_information:
  consequence:
  failure_mode:
```

## 5. User Actions

```yaml
action_1:
  action_name:
  precondition:
  confirmation_required:
  system_feedback:
  verification_condition:
  fallback:
```

## 6. Failure and Recovery

```yaml
possible_failure:
impact:
recovery_path:
escalation_condition:
```

## 7. Review Result

```yaml
review_status:
open_issues:
final_disposition:
```
