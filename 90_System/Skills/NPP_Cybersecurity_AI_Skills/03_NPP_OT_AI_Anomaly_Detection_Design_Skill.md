# Skill: NPP OT AI Anomaly Detection Design

## Skill Purpose

Use this skill to design AI-assisted anomaly detection for nuclear power plant OT cybersecurity.

The skill produces:

- anomaly detection architecture
- detection object model
- detection engine design
- data pipeline design
- alert schema
- V&V checklist
- model governance requirements

## When to Use

Use this skill when the user asks to:

- 设计核电 OT AI 异常检测系统
- 研究 OT 网络异常检测
- 设计 AI 安全监测平台
- 定义异常检测对象模型
- 设计模型输入输出
- 建立 AI 告警对象
- 形成异常检测 V&V 规范

## Required Inputs

```text
1. OT systems to be monitored
2. Available data sources
3. Critical digital assets
4. OT zones and conduits
5. Communication matrix
6. Industrial protocols
7. Maintenance and work-order context
8. Whether ML, rules, or hybrid detection is expected
```

If not available, assume a hybrid detection approach.

## Detection Layers

Use this layered anomaly model:

- L1 Network communication anomaly
- L2 Industrial protocol anomaly
- L3 Asset behavior anomaly
- L4 Configuration baseline anomaly
- L5 User and remote access anomaly
- L6 Process consistency anomaly
- L7 Multi-source event correlation anomaly
- L8 AI model and data drift anomaly

## Detection Engine Suite

Recommend a hybrid engine:

- Rule-Based Detector
- Communication Matrix Detector
- Protocol Semantic Detector
- Asset Baseline Detector
- User Behavior Detector
- Configuration Drift Detector
- Statistical Anomaly Detector
- ML Anomaly Detector
- Graph Relationship Detector
- Process Consistency Detector

## Output Structure

```markdown
# NPP OT AI Anomaly Detection Design
## 1. Detection Scope
## 2. Monitored Assets and Zones
## 3. Data Sources
| Data Source | Access Mode | Sensitivity | Constraint |
|---|---|---|---|
## 4. Anomaly Taxonomy
| Layer | Anomaly Type | Example | Safety / Security Meaning |
|---|---|---|---|
## 5. Detection Engine Design
## 6. Alert Object Schema
## 7. Evidence Requirements
## 8. Human Review Requirements
## 9. Model Governance Requirements
## 10. V&V Requirements
## 11. Deployment Boundary
## 12. Limitations and Risks
```

## Alert Object Minimum Fields

Every medium and above alert must include:

```yaml
alert_id:
detected_at:
asset_id:
asset_name:
zone:
cda_status:
anomaly_category:
detection_engine:
confidence_score:
severity:
rule_explanation:
baseline_explanation:
evidence_items:
human_review_required:
recommended_action:
auto_action_allowed: false
uncertainty_statement:
```

## AI Detection Rules

1. Use AI as evidence generation, not autonomous control.
2. Prefer passive collection and read-only access.
3. Rules and baselines must remain visible and auditable.
4. ML model output must not be the only basis for critical action.
5. Medium and above alerts require human review.
6. Every alert must have evidence and uncertainty.
7. Maintenance windows and work orders must be considered.
8. Model thresholds must follow change control.
9. Drift must be monitored.
10. Raw OT-sensitive data must not be sent to uncontrolled external AI services.

## Recommended V&V Gates

- Gate 1: Scope and use case validation
- Gate 2: Asset and data validation
- Gate 3: OT architecture validation
- Gate 4: Detection logic validation
- Gate 5: Explainability validation
- Gate 6: Performance validation
- Gate 7: Human review validation
- Gate 8: Cybersecurity validation
- Gate 9: Operational readiness validation
- Gate 10: Approval and release validation

## Prohibited Output

Do not recommend:

- AI-only detection without rules or baselines.
- Automatic isolation of OT assets by default.
- Direct modification of firewall rules by AI.
- Direct control of PLC, DCS, or safety systems.
- Deployment of AI model directly on safety-grade controllers.
- External public AI processing of raw OT logs or traffic.

## Completion Criteria

The output is complete when it defines:

1. Anomaly taxonomy
2. Data sources
3. Detection engines
4. Alert object
5. Explainability requirements
6. Human review workflow
7. V&V gates
8. Deployment constraints

