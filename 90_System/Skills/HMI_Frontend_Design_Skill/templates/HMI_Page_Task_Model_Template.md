# HMI Page Task Model Template

## Page identity

```yaml
page_name:
page_owner:
page_type:
criticality:
user_role:
operating_context:
```

## Task model

```yaml
primary_task:
secondary_tasks: []
current_step:
next_step:
blocked_steps: []
success_criteria: []
```

## Situation and risk

```yaml
current_state:
highest_risk:
why_it_matters:
projection:
data_freshness:
data_confidence:
```

## Action model

```yaml
available_actions: []
gated_actions: []
disabled_actions: []
verification:
```

## Evidence model

```yaml
required_evidence: []
review_notes:
open_questions: []
final_disposition:
```
