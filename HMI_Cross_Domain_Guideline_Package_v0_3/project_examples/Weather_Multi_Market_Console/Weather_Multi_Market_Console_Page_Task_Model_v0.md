# Weather Multi-Market Console Page Task Model v0

## 1. Page Identity

```yaml
page_name: Weather Multi-Market Console
page_type: Overview / Situation Console
system: Weather Trading System
version: v0
owner: TBD
```

## 2. Supported Task

```yaml
task_name: Multi-market weather anomaly monitoring
task_goal: Identify markets with abnormal divergence between weather forecast and market probability
user_role: operator / analyst
operating_context: real-time or near-real-time market monitoring
normal_condition: scanner running, data fresh, no severe alerts
abnormal_condition: high divergence, threshold proximity, liquidity anomaly, data mismatch
degraded_condition: weather API delayed, market data missing, model unavailable, scanner stopped
```

## 3. Required Information

```yaml
input_data:
  - market price
  - market probability
  - weather forecast
  - forecast uncertainty
  - historical model error
  - liquidity / volume
system_status:
  - scanner status
  - data freshness
  - API status
risk_status:
  - highest risk market
  - open severe alerts
alarm_status:
  - A2 / A3 / A4 alert count
automation_status:
  - scanner mode
  - model mode
  - manual override status
data_quality:
  - source freshness
  - missing values
  - confidence level
historical_context:
  - previous stable view
  - divergence trend
```

## 4. User Decisions

```yaml
decision_1:
  question: Should this market be promoted to priority monitoring?
  required_information: divergence, threshold distance, data confidence, liquidity, weather forecast uncertainty
  consequence: market receives focused monitoring and possibly manual review
  failure_mode: false opportunity or missed opportunity

decision_2:
  question: Should the alert be acknowledged or escalated?
  required_information: severity, impact, evidence, closure condition
  consequence: alert enters handling queue or escalation path
  failure_mode: alarm fatigue or delayed response
```

## 5. User Actions

```yaml
action_1:
  action_name: Add market to watchlist
  precondition: selected market has sufficient data confidence
  confirmation_required: false for low risk, true for high-risk action
  system_feedback: watchlist status updated
  verification_condition: market appears in priority list
  fallback: defer and request data refresh

action_2:
  action_name: Acknowledge alert
  precondition: alert has severity, trigger and recommended action
  confirmation_required: true for A3/A4
  system_feedback: alert status becomes acknowledged
  verification_condition: alert appears in acknowledged queue
  fallback: escalate to manual review
```

## 6. Failure and Recovery

```yaml
possible_failure: scanner stopped or data stale
impact: abnormal markets may not be detected
recovery_path: restart scanner, refresh data, switch to manual monitoring
escalation_condition: data stale exceeds allowed threshold or A3/A4 alert remains unresolved
```

## 7. Review Result

```yaml
review_status: draft
open_issues:
  - define severity thresholds
  - define data freshness SLA
  - define model confidence bands
final_disposition: defer until thresholds are confirmed
```
