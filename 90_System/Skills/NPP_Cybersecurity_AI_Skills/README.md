# NPP Cybersecurity AI Skills Pack

This package captures a v1 Obsidian-ready skills pack for nuclear power plant OT cybersecurity and AI-assisted anomaly detection governance.

## What it is for

- nuclear OT cybersecurity regulatory review
- OT / I&C cybersecurity architecture design
- CDA, zone, conduit, and communication matrix development
- AI-assisted OT anomaly detection design
- explainable alert records and evidence chains
- AI application governance and V&V gates
- cybersecurity governance platform UI page specifications

## Package layout

- `00_NPP_Cybersecurity_AI_Skills_Index.md`: pack index and skill selection map
- `SKILL.md`: executable routing entry for Codex/Claude-style skill use
- `01_NPP_Cybersecurity_Regulatory_Review_Skill.md`: regulatory and standards review
- `02_NPP_OT_Cybersecurity_Architecture_Design_Skill.md`: OT architecture and controls
- `03_NPP_OT_AI_Anomaly_Detection_Design_Skill.md`: anomaly detection design
- `04_NPP_OT_XAI_Alert_Explanation_Skill.md`: explainable alert record
- `05_NPP_AI_Application_Governance_Skill.md`: AI use-case governance
- `06_NPP_OT_AI_UI_Page_Design_Skill.md`: UI page and workflow specification
- `07_NPP_Cybersecurity_AI_Custom_GPT_Instructions.md`: Custom GPT instruction block
- `08_NPP_Cybersecurity_AI_Skills_Usage_Guide.md`: usage guide and workflow mapping
- `evals/evals.json`: initial test prompts for later skill evaluation

## How to use

Start from the index, pick the skill matching the task, then use the skill's required inputs and output structure.

Example:

> Use the NPP OT AI Anomaly Detection Design Skill to design a read-only, passive-monitoring anomaly detection system for DCS engineering workstation, historian, industrial DMZ, and selected conduits. Include alert object schema, evidence requirements, human review, model governance, and V&V gates.

## Governance note

This package is advisory and engineering-support oriented. It helps produce structured, reviewable outputs, but does not replace licensed engineering, cybersecurity, nuclear safety, QA, or regulatory review.
