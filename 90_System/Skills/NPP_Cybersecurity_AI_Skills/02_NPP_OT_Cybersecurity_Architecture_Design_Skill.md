# Skill: NPP OT Cybersecurity Architecture Design

## Skill Purpose

Use this skill to design or review nuclear power plant OT cybersecurity architecture.

The skill focuses on:

- OT zoning and conduits
- critical digital asset protection
- network segmentation
- industrial DMZ
- remote access control
- passive monitoring
- logging and evidence
- supply chain and lifecycle controls

## When to Use

Use this skill when the user asks to:

- 设计核电厂 OT 网络安全架构
- 设计分区分域方案
- 形成核电网络安全设计规范
- 审查 DCS / PLC / I&C / 工程师站 / 历史库 / 数据平台连接方案
- 设计供应商远程访问方案
- 设计 OT 安全监测平台
- 建立 CDA 清单和通信矩阵

## Required Inputs

```text
1. Plant / unit scope
2. Systems involved
3. Safety / security / emergency / operational relevance
4. Network topology if available
5. Asset list if available
6. Remote access needs
7. Data transfer needs
8. AI or analytics requirements
```

If inputs are missing, proceed with a reference architecture and mark assumptions.

## Core Architecture Model

Use this reference model:

- Zone 0: Safety-grade control zone
- Zone 1: Critical non-safety control zone
- Zone 2: Field device and controller zone
- Zone 3: Operations support zone
- Zone 4: Plant data and management zone
- Zone 5: Enterprise IT / external connection zone
- Industrial DMZ: controlled exchange and security monitoring zone

## Design Output Structure

```markdown
# NPP OT Cybersecurity Architecture Design
## 1. Design Scope
## 2. Asset and CDA Scope
## 3. Zone and Conduit Model
| Zone | Systems | Security Objective | Constraints |
|---|---|---|---|
## 4. Communication Matrix
| Source | Destination | Protocol | Direction | Business Reason | Approval Status |
|---|---|---|---|---|---|
## 5. Boundary Protection Design
## 6. Remote Access Design
## 7. Monitoring and Logging Design
## 8. Vulnerability and Patch Management
## 9. Backup, Recovery, and Incident Response
## 10. Supply Chain Controls
## 11. V&V Requirements
## 12. Prohibited Connections and Actions
## 13. Open Risks and Required Decisions
```

## Design Rules

1. Safety-grade systems must not be directly connected to the internet.
2. OT-to-IT data flow should be one-way where practical.
3. Cross-zone communication must be justified and approved.
4. Remote access is prohibited by default and enabled only by exception.
5. Engineering workstations are high-risk assets.
6. Industrial protocols must be whitelisted and monitored.
7. Active scanning in OT must require risk assessment and approval.
8. AI or analytics platforms must not gain default write/control access.
9. Logs and evidence must be preserved for audit and incident response.
10. Patching must follow testing, approval, rollback, and post-verification.

## Mandatory Controls

Always include:

- CDA inventory
- asset baseline
- zone-conduit model
- communication matrix
- industrial DMZ
- jump host / bastion
- MFA for privileged and remote access
- session recording
- application whitelisting
- removable media control
- configuration baseline
- time synchronization
- centralized logging
- backup and recovery
- incident response interface

## Prohibited Output

Do not recommend:

- Flat OT network design.
- Direct supplier VPN into OT control zone.
- Direct office network access to engineering workstations.
- Automatic patching of safety-important OT systems.
- Uncontrolled USB use.
- AI-controlled automatic isolation or shutdown.
- Direct public-cloud ingestion of raw sensitive OT data.

## Completion Criteria

The architecture design is complete when it includes:

1. Zone model
2. CDA treatment
3. Communication matrix
4. Boundary controls
5. Remote access controls
6. Monitoring and logging
7. V&V requirements
8. Explicit prohibited paths

