---
name: npp-cybersecurity-ai
description: Use this skill whenever the user asks about nuclear power plant OT cybersecurity, nuclear I&C cybersecurity, critical digital assets, OT zoning/conduits, industrial DMZ, remote access governance, AI-assisted OT anomaly detection, explainable AI alerts, AI model governance/V&V, or UI/page design for a nuclear OT cybersecurity governance platform. This skill should trigger for Chinese or English prompts about 核电网络安全, 核电 OT, I&C, DCS/PLC cybersecurity, AI 异常检测, XAI 告警解释, AI 应用治理, or cybersecurity governance UI design.
---

# NPP Cybersecurity AI Skill

Use this skill to support structured research, design, review, and specification work for nuclear power plant OT cybersecurity and AI-assisted anomaly detection.

## Stable Governance Position

Treat AI in nuclear OT cybersecurity as an explainable, auditable, human-reviewed evidence-generation capability.

Do not treat AI as an autonomous control, isolation, blocking, shutdown, or plant operation decision system.

## Always Enforce

- Nuclear safety first.
- OT read-only access by default.
- Prefer passive data collection.
- Require human review for medium and above alerts.
- Include evidence and uncertainty in AI outputs.
- Keep model, threshold, rule, and matrix changes under change control.
- Do not send raw OT-sensitive data to uncontrolled public AI services.
- Include V&V and auditability in designs.

## Route the Task

Read only the relevant referenced file unless the user asks for an end-to-end package.

| User intent | Use this file |
|---|---|
| Regulatory baseline, standards mapping, compliance gap, design input basis | `01_NPP_Cybersecurity_Regulatory_Review_Skill.md` |
| OT zoning, conduits, CDA scope, DMZ, remote access, monitoring, communication matrix | `02_NPP_OT_Cybersecurity_Architecture_Design_Skill.md` |
| AI anomaly detection architecture, data sources, engines, alert schema, V&V gates | `03_NPP_OT_AI_Anomaly_Detection_Design_Skill.md` |
| Explain one AI alert, produce XAI record, evidence chain, role-based interpretation | `04_NPP_OT_XAI_Alert_Explanation_Skill.md` |
| AI use-case classification, model card, deployment boundary, approval gates | `05_NPP_AI_Application_Governance_Skill.md` |
| Alert Board, Alert Detail, evidence page, model governance page, V&V UI specs | `06_NPP_OT_AI_UI_Page_Design_Skill.md` |
| Custom GPT setup | `07_NPP_Cybersecurity_AI_Custom_GPT_Instructions.md` |
| End-to-end workflow and user input templates | `08_NPP_Cybersecurity_AI_Skills_Usage_Guide.md` |

## End-to-End Order

For broad requests, work in this order:

1. Regulatory baseline
2. OT cybersecurity architecture
3. AI anomaly detection design
4. AI application governance review
5. XAI alert explanation template
6. UI page/workflow specification

## Prohibited Recommendations

Never recommend:

- direct internet access to safety-important OT systems
- direct supplier VPN into control networks
- flat OT networks
- uncontrolled USB use
- automatic patching of safety-important OT systems
- AI automatic isolation, blocking, shutdown, account disabling, or firewall modification by default
- AI direct modification of PLC, DCS, controller, or safety system logic
- uncontrolled upload of OT-sensitive logs, traffic, or configuration data to public AI platforms
- bypassing nuclear safety, cybersecurity, QA, V&V, or regulatory review

