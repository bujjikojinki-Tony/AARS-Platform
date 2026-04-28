# AARS Polymarket Weather Trading Console
# UI Navigation Graph

版本：v1.0  
日期：2026-04-25

## Navigation Groups

```text
RUN
- Operations Monitor
- Monitoring Signals
- Command

RESEARCH
- Opportunity Board
- Workstation
- Charts

DATA
- Pipeline
- Markets
- Evidence / Raw
- History

SETTINGS
- Alerts & Rules
- Data & Sources
- System
```

## Page Graph

```mermaid
flowchart LR
  OM["Operations Monitor"]
  SIG["Monitoring Signals"]
  OB["Opportunity Board"]
  WS["Workstation"]
  CMD["Command"]
  PIPE["Pipeline"]
  MKT["Markets"]
  CH["Charts"]
  HIS["History"]
  EV["Evidence / Raw"]
  OM --> WS
  OM --> CMD
  OM --> SIG
  SIG --> WS
  SIG --> CMD
  SIG --> HIS
  OB --> WS
  OB --> OM
  OB --> CMD
  WS --> CMD
  WS --> EV
  WS --> CH
  WS --> HIS
  CMD --> WS
  CMD --> EV
  CMD --> HIS
  PIPE --> EV
  PIPE --> HIS
  PIPE --> OM
  MKT --> OB
  MKT --> WS
  MKT --> OM
  CH --> WS
  CH --> HIS
  EV --> WS
  EV --> HIS
```

## Standard Flows

| Flow | Path |
|---|---|
| Runtime monitoring closure | Operations Monitor -> Quick Detail -> Workstation -> Command -> History |
| Signal handling closure | Monitoring Signals -> Signal Detail -> Workstation -> Command -> History |
| Opportunity research closure | Opportunity Board -> Opportunity Explanation -> Add to Focus -> Workstation -> Command |
| Data diagnostic closure | Pipeline -> Evidence / Raw -> Charts -> History -> Workstation |

