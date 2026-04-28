# AARS UI Runtime Documentation

This directory contains the UI runtime architecture documents for the AARS Polymarket Weather Trading Console.

The current UI is governed as an HMI-style operations console rather than a conventional dashboard. The core principle is:

```text
Data / Signals / Governance
-> View Builders
-> View Contracts
-> Dashboard / Telegram / CLI / Reports
```

## Documents

- [UI Runtime Architecture](./AARS_Polymarket_Weather_Trading_UI_Runtime_Architecture.md)
- [UI Legend Spec](./AARS_Polymarket_Weather_Trading_UI_Legend_Spec.md)
- [UI Page Roles](./AARS_Polymarket_Weather_Trading_UI_Page_Roles.md)
- [UI Navigation Graph](./AARS_Polymarket_Weather_Trading_UI_Navigation_Graph.md)
- [UI Action Policy](./AARS_Polymarket_Weather_Trading_UI_Action_Policy.md)
- [UI View Contracts](./AARS_Polymarket_Weather_Trading_UI_View_Contracts.md)
- [Dynamic Parameter Governance](./AARS_Polymarket_Weather_Trading_UI_Dynamic_Parameter_Governance.md)
- [Surface Consistency](./AARS_Polymarket_Weather_Trading_UI_Surface_Consistency.md)
- [Runtime Architecture Refactor Landing Plan](./AARS_Polymarket_Weather_Trading_UI_Runtime_Architecture_Refactor_Landing_Plan.md)

## Short-Form Landing Files

- [UI Design Status Roadmap](./UI_Design_Status_Roadmap.md)
- [UI Runtime Architecture](./UI_Runtime_Architecture.md)
- [UI Legend And Dynamic Parameter Governance](./UI_Legend_And_Dynamic_Parameter_Governance.md)
- [UI View Contracts And Action Policy](./UI_View_Contracts_And_Action_Policy.md)

## Compatibility Mirrors

Root-level UI documents are kept for compatibility with earlier planning material:

- `AARS_Polymarket_Weather_Trading_UI_Runtime_Architecture.md`
- `AARS_Polymarket_Weather_Trading_UI_Design_Status_Roadmap.md`
- `AARS_Polymarket_Weather_Trading_UI_Legend_Spec.md`

## Runtime Assets

Governed runtime assets referenced by these documents live in:

- `weather-comparison-engine/data/registries/ui_policy_registry/`
- `weather-comparison-engine/data/contracts/ui/`
