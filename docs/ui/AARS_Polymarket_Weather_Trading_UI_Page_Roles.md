# AARS Polymarket Weather Trading Console
# UI Page Roles

版本：v1.0  
日期：2026-04-25

| Page | Role | Primary Question | Must Not Do |
|---|---|---|---|
| Operations Monitor | Runtime operations monitor | What is happening now across the monitored market universe? | Must not become a research ranking board or evidence deep-dive page |
| Monitoring Signals | Signal and alert feed | Which alert, anomaly, recovery, or ops signals are active? | Must not perform execution or long-form evidence analysis |
| Opportunity Board | Opportunity ranking and research candidate entry | Which markets should be researched next? | Must not become the realtime operations monitor or execution page |
| Workstation | Single-market evidence workstation | Does the evidence support the current market interpretation? | Must not perform authorization closure as its primary role |
| Command | Operator decision and authorization closure | What action is allowed next, and how is it recorded? | Must not repeat evidence deep-dive or multi-market monitoring |
| Pipeline | Data pipeline and processing diagnostics | Is the data pipeline healthy and synchronized? | Must not rank market opportunities or make operator decisions |
| Markets | Market inventory and watchlist administration | Which markets are known, watched, focused, hidden, or removed? | Must not duplicate Opportunity Board scoring logic |
| Charts | Visual analysis and trend exploration | What do historical trends and distributions show? | Must not serve as the realtime alert entry point |
| History | Event replay and audit trail | What happened, when, and through which chain of events? | Must not perform realtime action decisions |
| Evidence / Raw | Raw evidence, canonical conversion, and lineage review | Where did the data come from and how was it transformed? | Must not serve as the primary operator decision page |
| Alerts & Rules | Alert rule, routing, throttle, and notification governance | Which alert rules exist, how do they trigger, and how are they routed? | Must not become the realtime signal feed or operator action closure page |
| Data & Sources | Source contract, measurement, freshness, and data-quality governance | Which sources are active, degraded, down, or mapped to which contracts? | Must not become the raw evidence drill-down or market research ranking page |
| System | Runtime health, services, permissions, maintenance, and admin configuration | Is the platform healthy, maintainable, and correctly configured? | Must not become a market monitoring, evidence analysis, or execution decision page |

## Boundary Rule

If a page needs information outside its role, it should link to the appropriate page or consume a summary field from the view contract. It should not duplicate another page's full logic.

## Settings Role Notes

- `Alerts & Rules` writes to rule registries and alert policy objects. It may show recent triggers, but live signal handling remains in `Monitoring Signals`.
- `Data & Sources` writes to source registries, measurement mappings, refresh schedules, and data-quality policies. Detailed raw payload inspection remains in `Evidence / Raw`.
- `System` writes to system configuration, maintenance, and permission registries. System-level ops events may surface in `Monitoring Signals`, but market-level state must remain separate.
