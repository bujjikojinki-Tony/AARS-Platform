# HMI Component Spec Template

## 1. Component identity

```yaml
component_name:
component_type:
page_used:
criticality:
owner:
```

## 2. Purpose

```yaml
supported_task:
user_decision:
operator_action:
```

## 3. Input data

```yaml
required_data: []
optional_data: []
data_source:
data_freshness_required:
confidence_required:
```

## 4. Display rules

```yaml
normal_state:
warning_state:
critical_state:
degraded_state:
unknown_state:
```

## 5. Interaction rules

```yaml
click_action:
hover_action:
expand_action:
disabled_condition:
confirmation_required:
```

## 6. Risk and alarm handling

```yaml
related_alarm:
severity_mapping:
recommended_action:
closure_condition:
```

## 7. Automation and AI handling

```yaml
automation_mode:
ai_recommendation:
confidence_display:
evidence_required:
human_override:
```

## 8. Accessibility and human factors

```yaml
color_only_encoding_allowed: false
text_label_required: true
keyboard_access_required:
contrast_required:
```

## 9. Review gate

```yaml
task_fit:
risk_visible:
action_clear:
data_trust_visible:
automation_transparent:
recovery_available:
review_status:
```
