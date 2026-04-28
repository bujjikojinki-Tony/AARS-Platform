# Skill: NPP OT XAI Alert Explanation

## Skill Purpose

Use this skill to generate explainable AI records for nuclear OT cybersecurity anomaly alerts.

The skill helps answer:

- Why did the AI raise this alert?
- Which rule or baseline was violated?
- Which asset or function may be affected?
- What evidence supports the alert?
- What is uncertain?
- What should humans verify next?

## When to Use

Use this skill when the user asks to:

- 解释 AI 异常检测告警
- 生成可解释性记录
- 设计 XAI 告警模板
- 对 AI 告警进行人工复核
- 将异常检测结果转成审计证据
- 面向网络安全、I&C、运行、管理分别解释告警

## Required Inputs

```text
1. Alert object
2. Asset context
3. Network context
4. Rule or communication matrix context
5. Baseline context
6. Model score or detection result
7. Evidence items
8. Work order or maintenance context if available
```

If evidence is missing, explicitly state what is missing.

## Explanation Structure

Always produce five explanation layers:

- E1 Rule explanation
- E2 Baseline explanation
- E3 Feature contribution explanation
- E4 Asset / function impact explanation
- E5 Uncertainty and human verification explanation

## Output Structure

```markdown
# OT AI Alert Explanation Record
## 1. Alert Summary
## 2. Rule Explanation
- Violated rule:
- Rule source:
- Observed behavior:
- Why it violates the rule:
## 3. Baseline Explanation
- Normal baseline:
- Current observation:
- Deviation:
- Baseline confidence:
## 4. Feature Contribution Explanation
| Feature | Expected | Observed | Contribution | Meaning |
|---|---|---|---|---|
## 5. Asset and Function Impact
| Impact Area | Status | Explanation |
|---|---|---|
## 6. Evidence Chain
| Evidence | Source | Time | Integrity | Relevance |
|---|---|---|---|---|
## 7. Role-Based Explanation
### Cybersecurity View
### I&C View
### Operations View
### Management / Audit View
## 8. Uncertainty Statement
## 9. Recommended Human Verification
## 10. Reviewer Decision Fields
```

## Role-Based Explanation Rules

For cybersecurity engineers:

- Emphasize source, destination, protocol, attack hypothesis, logs, and lateral movement.

For I&C engineers:

- Emphasize engineering workstation, controller, logic, configuration, and protocol operation.

For operations staff:

- Emphasize plant operation impact and whether immediate operational action is required.

For management:

- Emphasize severity, scope, response status, and escalation need.

For audit:

- Emphasize evidence, model version, rule version, reviewer decision, and closure traceability.

## Required Phrases for Uncertainty

Always include:

```text
Known:
Unknown:
Requires human verification:
Model cannot determine:
```

## Prohibited Output

Do not say:

> The AI has confirmed an incident

unless human review has already confirmed it.

Do not recommend high-impact actions such as:

- disconnect controller
- shutdown system
- modify PLC logic
- block network path
- disable account

unless framed as a governed action requiring authorized human approval.

## Completion Criteria

The explanation is complete when it includes:

1. Rule explanation
2. Baseline explanation
3. Feature contribution
4. Asset/function impact
5. Evidence chain
6. Role-based explanation
7. Uncertainty
8. Recommended human verification

