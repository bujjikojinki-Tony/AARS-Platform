# AARS Polymarket Weather Trading Console
# Functional Safety V&V Report

Generated: 2026-04-27

## 1. Scope

This V&V report reviews the dashboard runtime as safety-relevant operator support software.

It is **not** a certification claim for IEC 61508, ISO 26262, DO-178C, IEC 62304, or any other formal safety standard. It is an engineering V&V package that applies functional-safety-style controls to this console:

- Hazard identification
- Safety requirements
- Control verification
- Degraded-mode verification
- Traceability to implemented tests
- Residual-risk tracking

## 2. System Boundary

The dashboard is an advisory, monitoring, and operator-command surface.

In-scope:

- Operations Monitor
- Monitoring Signals
- Opportunity Board
- Workstation
- Command
- Settings governance pages
- `page_context.v1`
- `ui_action_event.v1`

Out-of-scope:

- Live financial execution
- Broker-side order submission
- Certification-grade independent safety assessment
- Formal probability-of-failure quantification

## 3. Safety Position

The console must preserve these invariants:

1. Alert does not imply execution permission.
2. Anomaly does not imply execution permission.
3. Validation strength does not imply execution permission.
4. Opportunity score is only a research priority.
5. Gate remains the only execution-permission boundary.
6. Settings changes must not directly change gate allow state.
7. High-risk operator/configuration actions must be deliberate and auditable.
8. A degraded visualization dependency must not disable table review or safe actions.

## 4. Hazard Analysis

| Hazard ID | Hazard | Cause | Potential Effect | Safety Control | Status |
|---|---|---|---|---|---|
| HZ-01 | Operator mistakes alert/anomaly for allow | Mixed visual semantics or action placement | Unsafe operator decision | Alert/anomaly/gate separated; Command shows gate status and disabled actions | Partially verified |
| HZ-02 | Static visual element looks clickable | HTML mock controls without state mutation | False belief action occurred | Fake tabs/actions removed from key pages; static scan added | Verified for current target files |
| HZ-03 | Critical settings changed accidentally | One-click disable/restart | Loss of monitoring/alerting/source evidence | Confirmation gates for critical rule, P1 source, system maintenance | Verified |
| HZ-04 | Context lost across pages | Navigation changes page without `page_context` | Audit/review chain incomplete | `page_context.v1` written for core flows and Settings -> History | Partially verified |
| HZ-05 | Missing chart library breaks signal handling | Optional visualization dependency unavailable | Signals page import/load failure | Plotly import is optional; table/actions remain available | Verified |
| HZ-06 | Keyboard user loses focus | Weak focus indication on dark UI | Action error or inability to recover | Global focus-visible style | Verified by static check |
| HZ-07 | Motion/update fatigue | Auto-refresh animation/motion | Reduced readability | Reduced-motion CSS | Verified by static check |
| HZ-08 | Audit event lacks confirmation evidence | Sparse event schema | Cannot reconstruct operator intent | Audit includes operator/result/confirmation fields | Verified |

## 5. Safety Requirements

| Req ID | Requirement | Verification Method | Evidence |
|---|---|---|---|
| FS-REQ-01 | High-risk Settings actions require explicit confirmation. | Automated static and unit checks | `test_functional_safety_vv_contracts.py`, `test_settings_hmi_vv.py` |
| FS-REQ-02 | Settings action events include operator, result, and confirmation state. | Unit test | `test_settings_hmi_vv.py` |
| FS-REQ-03 | Settings -> History navigation preserves context. | Unit test | `test_settings_hmi_vv.py` |
| FS-REQ-04 | Signal sections filter by governed type and do not depend on fake HTML tabs. | Unit test | `test_monitoring_signals_panel.py` |
| FS-REQ-05 | Plotly absence does not break Monitoring Signals import. | Unit test | `test_monitoring_signals_panel.py` |
| FS-REQ-06 | No known fake interaction markers remain in target HMI files. | Static test | `test_functional_safety_vv_contracts.py` |
| FS-REQ-07 | Global keyboard focus and reduced-motion controls exist. | Static test | `test_functional_safety_vv_contracts.py` |
| FS-REQ-08 | UI review evidence is documented. | Documentation review | This report and HMI V&V report |

## 6. Verification Results

Current result: **Conditional Pass**

Passed:

- HMI static fake-action scan for target files.
- Settings high-risk confirmation gates.
- Settings audit schema extension.
- Settings page-context persistence.
- Monitoring Signals governed sections.
- Monitoring Signals optional Plotly degraded mode.
- Global focus-visible and reduced-motion controls.

Blocked / Not complete:

- Full browser E2E V&V is not yet implemented in CI.
- Settings changes are still session/local-audit level, not registry-first persisted writes.
- All page actions are not yet enforced by a central action visibility policy.
- Telegram summary consistency is not yet fully contract-tested.

## 7. Traceability Matrix

| Safety Requirement | Implemented In | Test Evidence | Residual Risk |
|---|---|---|---|
| FS-REQ-01 | `settings_pages.py` | Static/unit tests | Confirmation is local UI; needs registry workflow |
| FS-REQ-02 | `_write_settings_audit` | Unit test | Other pages should converge on same schema |
| FS-REQ-03 | `_write_settings_page_context` | Unit test | Broaden to every cross-page action |
| FS-REQ-04 | `_apply_signal_section` | Unit test | Need browser test for live Streamlit interaction |
| FS-REQ-05 | Optional `plotly` import | Unit test | Visual chart missing in lean env but safe table remains |
| FS-REQ-06 | Removed fake HTML actions | Static test | Continue scanning as pages evolve |
| FS-REQ-07 | App CSS | Static test | Needs visual/keyboard browser pass |

## 8. Functional Safety Gate

Gate status: **Yellow / Conditional Pass**

Allowed:

- Continue local and dry-run operator testing.
- Continue dashboard runtime refinement.
- Use Settings pages for local governance prototyping.

Not allowed:

- Treat Settings UI as production configuration authority.
- Treat audit events as certification-grade audit trail.
- Treat alert, anomaly, validation, or opportunity score as execution permission.

## 9. Required Next V&V Work

P0:

- Implement central action visibility policy enforcement.
- Implement registry-first Settings write events with rollback/versioning.
- Add browser E2E tests for:
  - Operations Monitor -> Workstation -> Command -> History
  - Monitoring Signals -> Command
  - Settings -> History
- Add Dashboard/Telegram surface consistency tests.

P1:

- Add explicit “Latest Stable View” timestamps to fast-changing pages.
- Add disabled-reason tests for every disabled action.
- Add contrast snapshots for ALERT / ANOM / BLOCKED / LIVE / STALE / B.

## 10. Final Assessment

The current UI is moving in the right direction for a safety-relevant HMI: actions are increasingly deliberate, page context is becoming traceable, and degraded visualization does not block review workflows.

The system is not yet production-governed. The next meaningful safety milestone is not more visual polish; it is centralized action-policy enforcement plus registry-backed Settings writes.
