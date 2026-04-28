# NPP Cybersecurity AI Skills Pack Usage Guide

## 1. When to Call Each Skill

| Skill | Use when | Typical output |
|---|---|---|
| Regulatory Review | You need standards, regulatory basis, compliance themes, or design input requirements. | Regulatory baseline, standards mapping, gap questions |
| Architecture Design | You need OT zones, conduits, CDA scope, DMZ, remote access, logging, or V&V controls. | Architecture design note, communication matrix, prohibited paths |
| AI Anomaly Detection Design | You need detection layers, data sources, engines, alert object, or deployment boundary. | AI detection architecture and V&V plan |
| XAI Alert Explanation | You need to explain a concrete alert or create an audit-ready explanation record. | Alert explanation, evidence chain, role-based views |
| AI Application Governance | You need to classify an AI use case and decide approval controls. | AI level, allowed/prohibited uses, approval gates |
| UI Page Design | You need to turn the above into pages, components, fields, buttons, and state transitions. | Page specification, workflow, acceptance checklist |

## 2. User Input Templates

Regulatory review:

```text
Jurisdiction:
Plant lifecycle phase:
System type:
Safety/security/emergency/operational relevance:
OT/I&C/IT/AI/data/remote access involvement:
Required output:
```

Architecture design:

```text
Plant / unit scope:
Systems involved:
Asset list:
CDA candidates:
Remote access needs:
Data transfer needs:
AI or analytics requirements:
Known constraints:
```

AI anomaly detection:

```text
Monitored systems:
Data sources:
OT zones:
Communication matrix:
Protocols:
Maintenance/work-order context:
Preferred detection mode:
Deployment boundary:
```

XAI alert explanation:

```text
Alert object:
Asset context:
Network context:
Rule or matrix context:
Baseline context:
Model score:
Evidence items:
Work order / maintenance context:
```

AI governance:

```text
AI use case:
Affected system/process:
Data involved:
Model type:
Deployment mode:
Output action type:
Human review:
Approval target:
```

UI page design:

```text
Target page/workflow:
User roles:
Data objects:
Alert lifecycle states:
Model governance needs:
Visual mockup or page spec:
```

## 3. Output Templates

Use the output template embedded in each skill file. For end-to-end work, produce outputs in this order:

1. Regulatory baseline
2. Architecture design
3. AI anomaly detection design
4. AI governance review
5. XAI alert template
6. UI page specification

## 4. Obsidian Project Document Mapping

| Project document | Suggested source skill |
|---|---|
| Regulatory baseline note | Regulatory Review |
| Design input requirement list | Regulatory Review + Architecture Design |
| CDA inventory and communication matrix | Architecture Design |
| AI detection object model | AI Anomaly Detection Design |
| Alert explanation record template | XAI Alert Explanation |
| AI model card / approval gate note | AI Application Governance |
| Alert Board / Detail page spec | UI Page Design |
| Audit report template | XAI Alert Explanation + UI Page Design |

## 5. Codex / Front-End Development Mapping

Use the UI skill to produce page specifications before asking Codex to implement code.

Recommended sequence:

1. Generate `Alert Object Schema` from the anomaly detection skill.
2. Generate `Page Specification` from the UI skill.
3. Convert standard components into frontend components.
4. Implement state transitions with reason capture and audit fields.
5. Verify no prohibited buttons are exposed by default.
6. Add test data for severity, CDA status, evidence completeness, and review state.

## 6. From Research Report to System Design

Start with a regulatory review, then extract:

- applicable standards
- design input requirements
- gap questions
- prohibited assumptions
- V&V expectations

Feed these into the architecture design skill to produce:

- zone model
- CDA scope
- conduit / communication matrix
- boundary controls
- remote access controls
- monitoring and logging design

## 7. From System Design to UI Page

Use the architecture and detection outputs to define:

- assets and zones
- alert categories
- evidence objects
- human review states
- role-based views
- model governance fields

Then call the UI page design skill to produce:

- Alert Board
- Alert Detail
- Explanation View
- Human Review Workspace
- Model Governance Dashboard
- V&V Checklist Workspace

## 8. From UI Page to Code Implementation

Before implementation, confirm:

- all required fields are present
- high-impact auto-action buttons are absent by default
- controlled actions require approval states
- every state transition captures a reason
- medium and above alerts require human review
- evidence and uncertainty are visible
- model version, rule version, and review history are auditable

## 9. Suggested End-to-End Prompt

```text
Use the NPP Cybersecurity AI Skills Pack to design a nuclear OT AI anomaly detection governance workflow.

Scope:
- monitor DCS engineering workstation, historian, industrial DMZ, and selected network conduits
- use passive network data, logs, configuration baselines, and work-order context
- include regulatory basis, architecture, anomaly detection design, AI governance, XAI alert template, and Alert Board page specification
- enforce nuclear safety first, read-only OT access, human review for medium and above alerts, and no automatic isolation/shutdown
```

