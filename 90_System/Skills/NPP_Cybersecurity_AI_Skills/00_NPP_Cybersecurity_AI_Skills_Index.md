# NPP Cybersecurity AI Skills Pack v1

## Purpose

This Skills Pack supports structured research, design, review, and specification development for nuclear power plant OT cybersecurity and AI-assisted anomaly detection.

It is intended for:

- nuclear power plant OT cybersecurity design
- nuclear I&C cybersecurity review
- AI-assisted anomaly detection design
- explainable AI alert governance
- AI application approval and V&V
- front-end page design for cybersecurity governance platforms

## Skill List

1. [[01_NPP_Cybersecurity_Regulatory_Review_Skill|NPP Cybersecurity Regulatory Review Skill]]
2. [[02_NPP_OT_Cybersecurity_Architecture_Design_Skill|NPP OT Cybersecurity Architecture Design Skill]]
3. [[03_NPP_OT_AI_Anomaly_Detection_Design_Skill|NPP OT AI Anomaly Detection Design Skill]]
4. [[04_NPP_OT_XAI_Alert_Explanation_Skill|NPP OT XAI Alert Explanation Skill]]
5. [[05_NPP_AI_Application_Governance_Skill|NPP AI Application Governance Skill]]
6. [[06_NPP_OT_AI_UI_Page_Design_Skill|NPP OT AI UI Page Design Skill]]

Related operational files:

- [[07_NPP_Cybersecurity_AI_Custom_GPT_Instructions|Custom GPT Instructions]]
- [[08_NPP_Cybersecurity_AI_Skills_Usage_Guide|Usage Guide]]

## Core Governance Position

AI in nuclear OT cybersecurity shall be treated as:

> an explainable, auditable, human-reviewed evidence-generation capability

It shall not be treated as:

> an autonomous control, isolation, blocking, shutdown, or plant operation decision system

## Stable Constraints

- Nuclear safety first.
- OT read-only access by default.
- Passive data collection preferred.
- Medium and above alerts require human review.
- AI outputs must include evidence and uncertainty.
- No high-impact automatic actions without governed approval.
- External public AI services must not receive raw OT-sensitive data.
- Model changes, threshold changes, and rule changes must follow change control.

## Recommended Skill Selection

| User intent | Start with |
|---|---|
| Build a regulatory baseline or standards mapping | [[01_NPP_Cybersecurity_Regulatory_Review_Skill]] |
| Design OT zoning, conduits, DMZ, remote access, CDA protection | [[02_NPP_OT_Cybersecurity_Architecture_Design_Skill]] |
| Design anomaly detection architecture, data pipeline, alert object | [[03_NPP_OT_AI_Anomaly_Detection_Design_Skill]] |
| Explain or review one AI alert | [[04_NPP_OT_XAI_Alert_Explanation_Skill]] |
| Decide whether an AI use case is allowed and governed | [[05_NPP_AI_Application_Governance_Skill]] |
| Convert requirements into pages, workflows, and UI specs | [[06_NPP_OT_AI_UI_Page_Design_Skill]] |

