# AARS Polymarket Weather Trading Console
# UI Runtime Architecture Refactor Landing Plan v1

版本：v1.0  
日期：2026-04-25  
定位：UI Runtime Architecture Refactor 的可落地文件清单、文档更新顺序与验收清单

---

## 1. Core Judgment

The console now has a complete page family:

```text
RUN:
- Operations Monitor
- Monitoring Signals
- Command

RESEARCH:
- Opportunity Board
- Workstation
- Charts

DATA:
- Pipeline
- Markets
- Evidence / Raw
- History

SETTINGS:
- Alerts & Rules
- Data & Sources
- System
```

The most important task is no longer adding pages. The system must stabilize:

- page roles,
- navigation logic,
- action model,
- state legend,
- dynamic parameter governance,
- view contracts,
- policy registry.

Without this layer, pages will diverge on `ALERT / ANOM / BLOCKED`, Opportunity Board will overlap Operations Monitor, Workstation and Command will blur, frontend code will infer `primary_state`, and Telegram / Dashboard may disagree.

---

## 2. Target Documentation Package

Final `docs/ui/` structure:

```text
docs/ui/
  01_UI_Design_Status_Roadmap.md
  02_UI_Runtime_Architecture.md
  03_UI_Page_Roles.md
  04_UI_Navigation_Graph.md
  05_UI_View_Contracts.md
  06_UI_Legend_Spec.md
  07_UI_Action_Policy.md
  08_UI_Dynamic_Parameter_Governance.md
  09_UI_Surface_Consistency.md
```

Current implementation also keeps descriptive long names for readability:

```text
docs/ui/AARS_Polymarket_Weather_Trading_UI_Runtime_Architecture.md
docs/ui/AARS_Polymarket_Weather_Trading_UI_Page_Roles.md
docs/ui/AARS_Polymarket_Weather_Trading_UI_Navigation_Graph.md
docs/ui/AARS_Polymarket_Weather_Trading_UI_Action_Policy.md
docs/ui/AARS_Polymarket_Weather_Trading_UI_Legend_Spec.md
docs/ui/AARS_Polymarket_Weather_Trading_UI_View_Contracts.md
docs/ui/AARS_Polymarket_Weather_Trading_UI_Dynamic_Parameter_Governance.md
```

---

## 3. Minimum Landing Set

The minimum landing set is:

1. `UI_Design_Status_Roadmap.md`
2. `UI_Runtime_Architecture.md`
3. `UI_Legend_And_Dynamic_Parameter_Governance.md`
4. `UI_View_Contracts_And_Action_Policy.md`

Current status:

| Minimal Document | Implemented File |
|---|---|
| UI Design Status Roadmap | `docs/ui/UI_Design_Status_Roadmap.md` + root roadmap mirror |
| UI Runtime Architecture | `docs/ui/UI_Runtime_Architecture.md` + `docs/ui/AARS_Polymarket_Weather_Trading_UI_Runtime_Architecture.md` |
| UI Legend + Dynamic Governance | `docs/ui/UI_Legend_And_Dynamic_Parameter_Governance.md` + canonical split docs |
| UI View Contracts + Action Policy | `docs/ui/UI_View_Contracts_And_Action_Policy.md` + canonical split docs |

---

## 4. Update Order

### Step 1: UI Roadmap

Write:

- current page family,
- new navigation grouping,
- Operations Monitor v3.1,
- Opportunity Board new role,
- Command new role,
- Phase 32-35.

### Step 2: UI Runtime Architecture

Write:

- page roles,
- navigation graph,
- action model,
- state governance,
- view contract architecture,
- view builder architecture.

### Step 3: UI Legend + Dynamic Governance

Write:

- state table,
- primary state / secondary states,
- color semantics,
- dynamic field ownership,
- frontend prohibitions,
- policy registry references.

### Step 4: UI View Contracts + Action Policy

Write:

- page-level contract table,
- summary contract table,
- action visibility policy,
- navigation context schema,
- button output objects.

### Step 5: Implementation Plan

Write:

- Phase 32,
- Phase 33,
- Phase 34,
- Phase 35.

---

## 5. Policy Registry Landing Files

Canonical location:

```text
weather-comparison-engine/data/registries/ui_policy_registry/
```

Files:

- `primary_state_policy.json`
- `display_priority_policy.json`
- `next_operator_action_policy.json`
- `action_visibility_policy.json`
- `navigation_policy.json`
- `ui_color_semantics_policy.json`
- `ui_legend_policy.json`
- `ui_static_registry.json`

The three highest priority policies are:

1. `primary_state_policy.json`
2. `navigation_policy.json`
3. `action_visibility_policy.json`

---

## 6. View Contract Landing Files

Canonical location:

```text
weather-comparison-engine/data/contracts/ui/
```

Initial schema draft files:

- `operations_monitor_view.schema.json`
- `monitoring_signals_view.schema.json`
- `opportunity_board_view.schema.json`
- `market_workstation_view.schema.json`
- `command_context_view.schema.json`
- `pipeline_status_view.schema.json`
- `markets_inventory_view.schema.json`
- `charts_analysis_view.schema.json`
- `history_event_view.schema.json`
- `evidence_raw_view.schema.json`
- `page_context_schema.json`

The first implementation priority is:

1. `operations_monitor_view.v1`
2. `opportunity_board_view.v1`
3. `market_workstation_view.v1`
4. `command_context_view.v1`

Current landing status:

- Policy registry draft files are present under `weather-comparison-engine/data/registries/ui_policy_registry/`.
- Page-level JSON Schema drafts are present under `weather-comparison-engine/data/contracts/ui/`.
- `page_context_schema.json` is the first shared cross-page navigation schema and should be used by `Open Workstation`, `Send to Command`, and `Review Evidence` flows before additional action-specific schemas are introduced.
- The first four core contracts now have stricter structural draft schemas:
  - `operations_monitor_view.schema.json`
  - `opportunity_board_view.schema.json`
  - `market_workstation_view.schema.json`
  - `command_context_view.schema.json`
- `operations_monitor_view`, `opportunity_board_view`, and `market_workstation_view` are aligned to currently observed builder output shapes.
- `command_context_view` is currently a target governed contract for the future command view builder and should be treated as a forward contract rather than a fully implemented runtime export.

---

## 7. Acceptance Criteria

This refactor is accepted when:

1. Left navigation follows `RUN / RESEARCH / DATA / SETTINGS`.
2. Every page has one explicit role and does not duplicate another page's core responsibility.
3. Governed dynamic fields have explicit owners.
4. Colors and legend semantics are unified.
5. Button actions are governed by action policy.
6. Cross-page navigation carries entry context.
7. Dashboard and Telegram can consume the same summary contract family.
8. Frontend code no longer derives `primary_state`, `gate_summary`, `opportunity_score`, `freshness_status`, or similar governed fields.
