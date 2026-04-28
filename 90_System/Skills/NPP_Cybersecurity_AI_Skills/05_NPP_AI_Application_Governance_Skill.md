# Skill: NPP AI Application Governance

## Skill Purpose

Use this skill to govern AI applications in nuclear power plant OT, I&C, cybersecurity, maintenance, data governance, or operations-support contexts.

The skill supports:

- AI use-case classification
- AI risk assessment
- AI model card generation
- AI data governance review
- AI V&V planning
- AI application approval gates
- AI deployment boundary definition

## When to Use

Use this skill when the user asks to:

- 判断 AI 是否可以用于核电 OT 场景
- 形成 AI 应用规范
- 设计 AI 上线门禁
- 建立 AI 模型卡
- 审查大模型在核电中的应用风险
- 设计 AI 运维、维修、网络安全、规程问答应用
- 判断 AI 能否接入 OT 数据

## Required Inputs

```text
1. AI use case
2. System or process affected
3. Data involved
4. Whether OT, I&C, safety, security, emergency, or operation is involved
5. AI model type
6. Deployment mode
7. Output action type
8. Whether human review exists
```

## AI Application Levels

Classify the use case:

- AI-L1: Offline support
- AI-L2: Online read-only analysis
- AI-L3: Decision support with human approval
- AI-L4: Automatic execution

## Decision Rules

- If AI is offline and uses approved documents, classify as AI-L1.
- If AI reads OT data but cannot write or execute, classify as AI-L2.
- If AI recommends operational or cybersecurity decisions, classify as AI-L3 and require human approval.
- If AI executes isolation, blocking, control, configuration, or shutdown, classify as AI-L4 and prohibit by default unless separately licensed and justified.

## Output Structure

```markdown
# NPP AI Application Governance Review
## 1. Use Case Summary
## 2. AI Level Classification
## 3. Data Scope and Sensitivity
## 4. System Impact Screening
| Area | Impact | Explanation |
|---|---|---|
| Nuclear safety |  |  |
| Nuclear security |  |  |
| Emergency preparedness |  |  |
| Plant operation |  |  |
| OT cybersecurity |  |  |
| Data confidentiality |  |  |
## 5. Allowed Uses
## 6. Prohibited Uses
## 7. Required Controls
## 8. Model Card Requirements
## 9. V&V Requirements
## 10. Human Review Requirements
## 11. Deployment Boundary
## 12. Approval Gates
## 13. Final Recommendation
```

## Required Controls

For any nuclear OT AI use case, require:

- AI risk assessment
- data classification
- data minimization
- model card
- approved use cases
- prohibited use cases
- human review
- logging and audit
- explainability
- uncertainty statement
- performance validation
- drift monitoring
- rollback plan
- change control
- supplier review if third-party model is used

## LLM-Specific Rules

If LLM is used:

1. Use approved knowledge sources.
2. Prefer local or controlled deployment for sensitive data.
3. Require citations or evidence references.
4. Require uncertainty statement.
5. Do not allow tool execution into OT systems.
6. Do not allow direct generation or modification of PLC/DCS logic without engineering review.
7. Log prompts and outputs where appropriate.
8. Defend against prompt injection.

## Prohibited Output

Do not approve:

- Public LLM upload of raw OT-sensitive logs.
- LLM direct control of OT assets.
- AI replacing licensed or authorized personnel.
- AI automatic safety or security decisions.
- AI-generated control logic without V&V and engineering approval.

## Completion Criteria

The governance review is complete when it includes:

1. AI level
2. Impact screening
3. Allowed/prohibited uses
4. Controls
5. V&V gates
6. Deployment boundary
7. Final recommendation

