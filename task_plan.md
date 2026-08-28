# Task Plan: PWB-03 Probability Governance & Calibration v0

## Goal
Design and implement a probability-governance layer that compares multiple weather probability engines, records calibration outcomes, and governs active engine selection without enabling live trading.

## Current Phase
PWB-11 Complete

## Phases

### Phase 1: Backlog and Boundary Definition
- [x] Translate the PWB-03 charter into an executable backlog
- [x] Confirm frozen PWB-02 boundaries remain unchanged
- [x] Identify repository surfaces for registry, comparison, calibration, and governance APIs
- **Status:** complete

### Phase 2: Backend Data Model and Storage
- [x] Add probability engine config/run/comparison/outcome/calibration/promotion models
- [x] Extend SQLite schema for governance tables
- [x] Add repository methods for reads, writes, and aggregation
- **Status:** complete

### Phase 3: Engine Registry and Shadow Engines
- [x] Register gaussian_v0, deb_shadow_v0, and emos_shadow_v0
- [x] Implement shadow engine placeholders with deterministic adjustments
- [x] Implement active engine policy and promotion gate inputs
- **Status:** complete

### Phase 4: Comparison and Calibration
- [x] Build probability comparison views from WeatherView
- [x] Record market outcomes and calibration results
- [x] Compute Brier score, absolute error, and bucket metrics
- **Status:** complete

### Phase 5: Governance APIs and UI
- [x] Add probability governance API routes
- [x] Expose registry and comparison views in Workstation / Settings / History
- [x] Add calibration history panel and comparison panel
- **Status:** complete

### Phase 6: Verification and Freeze
- [x] Add acceptance tests for registry, comparison, calibration, and promotion gate
- [x] Verify shadow engines do not drive trading
- [x] Freeze PWB-03 baseline
- **Status:** complete

### Phase 7: Test Isolation and App Factory Hardening
- [x] Add `create_app(db_path, allow_network=False)` for isolated API tests
- [x] Update PWB-02 and PWB-03 API tests to use temporary databases
- [x] Add an isolation regression test for separate app instances
- **Status:** complete

## Key Questions
1. Should PWB-03 persist comparison and calibration records in the same SQLite database as PWB-01/PWB-02? Yes, unless a later scaling need appears.
2. Should gaussian_v0 remain the active primary by default? Yes, until a promotion gate explicitly changes it.
3. Should shadow engines be allowed to influence UI only, never strategy output? Yes.

## Decisions Made
| Decision | Rationale |
|----------|-----------|
| Keep PWB-03 offline and non-trading | Charter explicitly excludes live trading and auto trading |
| Treat gaussian_v0 as the active primary | Preserves PWB-02 stability while governance is added |
| Use shadow outputs for comparison only | Allows calibration and promotion workflows without execution risk |

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| None yet | 1 | N/A |

## Notes
- Preserve the PWB-02 freeze line.
- Keep shadow engines deterministic and transparent.
- Prefer additive changes over refactors unless a schema boundary requires it.

## PWB-04C Test Isolation and App Factory Hardening
- [x] Add `backend/services.py` with `AppServices` and `create_services()`
- [x] Add `backend/app_factory.py` with isolated `create_app(...)`
- [x] Refactor `backend/main.py` to a thin default app entrypoint
- [x] Update API tests to use temporary databases
- [x] Add an isolation regression test for separate app instances
- **Status:** complete

## PWB-04C Router Integration and Freeze
- [x] Ensure `create_app()` mounts opportunities, command, history, settings, weather, evidence, workstation, and probability governance routers
- [x] Pass `allow_network`, `default_year`, and `default_sigma` into the weather router from `create_app()`
- [x] Freeze PWB-04C with isolated app/database behavior only
- **Status:** complete

## PWB-04D Read-Only Polymarket Connector
- [x] Add read-only Polymarket models and connector config defaults
- [x] Add read-only Gamma / CLOB client stubs
- [x] Add market normalization, weather filtering, connector health, and mock fallback source
- [x] Add connector status panel to Settings
- [x] Add read-only connector tests and freeze docs
- **Status:** complete

## PWB-04D Settings UI and Acceptance
- [x] Upgrade the Settings connector panel from static copy to live read-only API actions
- [x] Surface source mode, network gate, health, cached markets, preview snapshots, warnings, and raw state in the dashboard
- [x] Consolidate the PWB-04D acceptance checks into a single read-only connector regression file
- [x] Verify dashboard panel tests and PWB-04D backend acceptance tests pass together
- **Status:** complete

## PWB-04E Market Snapshot Archive
- [x] Add snapshot archive models, SQLite table, indexes, and repository methods
- [x] Add archive service and snapshot archive APIs
- [x] Add optional sync and scan capture hooks that remain non-executing
- [x] Expose snapshot archive summary/recent/series/current-source actions in the dashboard History shell
- [x] Add PWB-04E tests and freeze docs
- **Status:** complete

## PWB-04F Weather Forecast Archive
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define weather archive models, SQLite tables, and repository methods
- [x] Add weather archive service and passive archive APIs
- [x] Add optional archive hooks from accepted weather-side flows
- [x] Expose weather archive visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

## PWB-04G Outcome Resolver Read-Only
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define outcome resolver models, SQLite tables, and repository methods
- [x] Add read-only resolver service and APIs
- [x] Expose read-only resolver visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

## PWB-05 Real Calibration Data & Backtest Memory
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define calibration-memory and backtest-memory models, SQLite tables, and repository methods
- [x] Add read-only assembly service and APIs
- [x] Expose read-only memory visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

## PWB-05A Real DEB Shadow Implementation
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define DEB shadow models, SQLite tables, and repository methods
- [x] Add read-only DEB shadow service and APIs
- [x] Expose DEB shadow visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

## PWB-05B EMOS Shadow Evaluation
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define EMOS shadow models, SQLite tables, and repository methods
- [x] Add read-only EMOS shadow service and APIs
- [x] Expose EMOS shadow visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

## PWB-05C Shadow Engine Evaluation Matrix
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define evaluation models, SQLite tables, and repository methods
- [x] Add read-only evaluation service and APIs
- [x] Expose evaluation visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

## PWB-06 Governed Command Review
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define governed command review models, SQLite tables, and repository methods
- [x] Add read-only command review service and APIs
- [x] Expose command review visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

### PWB-06 Phase A/B - Command Review Models + Storage
- [x] Define command review models and enums
- [x] Extend SQLite schema with review tables and indexes
- [x] Add repository save/list/bundle/summary helpers
- [x] Add latest lookup for command review context
- **Status:** complete

### PWB-06 Phase C/D - Command Review Service + APIs
- [x] Add read-only command review service
- [x] Add read-only command review endpoints
- [x] Ensure responses carry safety flags
- [x] Preserve no-execution boundary
- **Status:** complete

## PWB-07 Governed Execution Decision Review
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define governed execution-decision review models, SQLite tables, and repository methods
- [x] Add read-only execution-decision review service and APIs
- [x] Expose execution-decision review visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

## PWB-08 Governed Execution Queue Review
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define governed execution-queue review models, SQLite tables, and repository methods
- [x] Add read-only execution-queue review service and APIs
- [x] Expose execution-queue review visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

## PWB-09 Governed Approval Window Review
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define governed approval-window review models, SQLite tables, and repository methods
- [x] Add read-only approval-window review service and APIs
- [x] Expose approval-window review visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

### PWB-09 Phase A/B - Approval Window Review Models + Storage
- [x] Define approval-window review models and enums
- [x] Extend SQLite schema with approval review tables and indexes
- [x] Add repository save/list/bundle/summary helpers
- [x] Add latest lookup for approval review context
- **Status:** complete

### PWB-09 Phase C/D - Approval Window Review Service + APIs
- [x] Add read-only approval-window review service
- [x] Add read-only approval-window review endpoints
- [x] Ensure responses carry safety flags
- [x] Preserve no-execution boundary
- **Status:** complete

### PWB-09 Phase E/F - Approval Window Review UI + Freeze
- [x] Add the approval-window review panel to the History shell
- [x] Add dashboard panel smoke tests
- [x] Add PWB-09 status / inventory / freeze docs
- **Status:** complete

## PWB-10 Governed Activation Readiness Review
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define governed activation-readiness review models, SQLite tables, and repository methods
- [x] Add read-only activation-readiness review service and APIs
- [x] Expose activation-readiness review visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

### PWB-10 Phase A/B - Activation Readiness Review Models + Storage
- [x] Define activation-readiness review models and enums
- [x] Extend SQLite schema with readiness review tables and indexes
- [x] Add repository save/list/bundle/summary helpers
- [x] Add latest lookup for activation-readiness review context
- **Status:** complete

### PWB-10 Phase C/D - Activation Readiness Review Service + APIs
- [x] Add read-only activation-readiness review service
- [x] Add read-only activation-readiness review endpoints
- [x] Ensure responses carry safety flags
- [x] Preserve no-execution boundary
- **Status:** complete

### PWB-10 Phase E/F - Activation Readiness Review UI + Freeze
- [x] Add the activation-readiness review panel to the History shell
- [x] Add dashboard panel smoke tests
- [x] Add PWB-10 status / inventory / freeze docs
- **Status:** complete

## PWB-11 Governed Activation Authorization Review
- [x] Translate the charter into repo docs and an executable backlog
- [x] Define governed activation-authorization review models, SQLite tables, and repository methods
- [x] Add read-only activation-authorization review service and APIs
- [x] Expose activation-authorization review visibility in the dashboard shell
- [x] Add acceptance tests and freeze docs
- **Status:** complete

### PWB-11 Phase A/B - Activation Authorization Review Models + Storage
- [x] Define activation-authorization review models and enums
- [x] Extend SQLite schema with authorization review tables and indexes
- [x] Add repository save/list/bundle/summary helpers
- [x] Add latest lookup for activation-authorization review context
- **Status:** complete

### PWB-11 Phase C/D - Activation Authorization Review Service + APIs
- [x] Add read-only activation-authorization review service
- [x] Add read-only activation-authorization review endpoints
- [x] Ensure responses carry safety flags
- [x] Preserve no-execution boundary
- **Status:** complete

### PWB-11 Phase E/F - Activation Authorization Review UI + Freeze
- [x] Add the activation-authorization review panel to the History shell
- [x] Add dashboard panel smoke tests
- [x] Add PWB-11 status / inventory / freeze docs
- **Status:** complete

### PWB-08 Phase A/B - Execution Queue Review Models + Storage
- [x] Define execution-queue review models and enums
- [x] Extend SQLite schema with queue review tables and indexes
- [x] Add repository save/list/bundle/summary helpers
- [x] Add latest lookup for queue review context
- **Status:** complete

### PWB-08 Phase C/D - Execution Queue Review Service + APIs
- [x] Add read-only execution queue review service
- [x] Add read-only execution queue review endpoints
- [x] Ensure responses carry safety flags
- [x] Preserve no-execution boundary
- **Status:** complete

### PWB-08 Phase E/F - Execution Queue Review UI + Freeze
- [x] Add the execution queue review panel to the History shell
- [x] Add dashboard panel smoke tests
- [x] Add PWB-08 status / inventory / freeze docs
- **Status:** complete

### PWB-07 Phase E/F - Dashboard Shell + Freeze
- [x] Add the execution-decision review panel to the History shell
- [x] Add dashboard panel smoke tests
- [x] Add PWB-07 status / inventory / freeze docs
- **Status:** complete

### PWB-07 Phase A/B - Execution Decision Review Models + Storage
- [x] Define execution-decision review models and enums
- [x] Extend SQLite schema with decision review tables and indexes
- [x] Add repository save/list/bundle/summary helpers
- [x] Add latest lookup for execution-decision review context
- **Status:** complete

### PWB-07 Phase C/D - Execution Decision Review Service + APIs
- [x] Add read-only execution-decision review service
- [x] Add read-only execution-decision review endpoints
- [x] Ensure responses carry safety flags
- [x] Preserve no-execution boundary
- **Status:** complete

## MIL-3.17 Forward-Only Extended Paper Observation
- [x] Define the immutable forward-observation contract and strict out-of-sample boundary
- [x] Add forward-only replay construction, funding coverage gates, and advisory dispositions
- [x] Persist append-only observation checkpoints with lineage and content hashes
- [x] Add read-only service, API, CLI, and dashboard visibility
- [x] Add deterministic leakage, immutability, risk, API, CLI, and UI tests
- [x] Update MIL-3 documentation and run the full suite
- [x] Commit the milestone
- **Status:** complete

## MIL-3.18 Continuous Forward Observation Governance
- [x] Define checkpoint scheduling, stability analysis, decay warnings, and confirmation policy
- [x] Add deterministic forward-observation stability/governance model
- [x] Add safe scheduled checkpoint orchestration without duplicate writes or execution paths
- [x] Expose read-only stability/governance API and task-centered UI evidence
- [x] Add deterministic scheduler, stability, degradation, API, CLI, and UI tests
- [x] Update documentation and run the full suite
- [x] Review and commit the milestone
- **Status:** complete

## MIL-3.19 Human Forward Review and Evidence Export
- [x] Define immutable human review actions and candidate lifecycle transitions
- [x] Persist lineage-chained review records with stability/source verification
- [x] Make the monitor respect pause, termination, and governed restart state
- [x] Add deterministic complete evidence-bundle export with component hashes
- [x] Expose read-only review/evidence status through API and task-centered UI
- [x] Add deterministic state-machine, tamper, monitor, export, API, CLI, and UI tests
- [x] Update documentation, run the full suite, review, and commit
- **Status:** complete

## MIL-3.20 Offline Evidence Verification, Retention, and Isolated Activation Approval
- [x] Define offline verification report, retention policy, and isolated approval authority contract
- [x] Add database-independent evidence-bundle verification CLI and deterministic report
- [x] Add scoped evidence retention/backup inventory with integrity verification and safe pruning
- [x] Add immutable isolated PAPER_ONLY activation-approval state and storage verification
- [x] Expose approval/retention status through read-only API and task-centered console
- [x] Add deterministic tamper, retention, approval, API, CLI, and UI tests
- [x] Update operations/milestone documentation and run the full suite
- [x] Review and commit the milestone
- **Status:** complete

## MIL-3.21 Isolated PAPER_ONLY Configuration Registry and Atomic Lifecycle
- [x] Define immutable registry, one-time approval consumption, sandbox pointer and fail-safe expiry contract
- [x] Add registry/storage models with exact configuration and authority verification
- [x] Add atomic activate, rollback and persisted expiry/revocation reconciliation events
- [x] Add immediate read-only effective-configuration resolution that fails safe without GET mutations
- [x] Add explicit local registry/activation/reconciliation CLI and read-only API
- [x] Add task-centered UI for stored pointer vs effective state, rollback target and blocking reason
- [x] Add deterministic registry, race, expiry, revocation, rollback, API, CLI and UI tests
- [x] Update documentation, run full verification, review and commit
- **Status:** complete

## MIL-3.22 Governed Isolated PAPER Runtime
- [x] Define runtime lease, heartbeat, stop, kill-switch and fail-safe authority contract
- [x] Add append-only runtime sessions/events with atomic lease acquisition and fencing
- [x] Add a bounded PAPER_ONLY runtime worker that consumes only effective configuration
- [x] Enforce automatic stop on expiry, revocation, pointer change, lease loss or kill switch
- [x] Add explicit local lifecycle CLI plus read-only service/API surfaces
- [x] Add task-centered runtime HMI with actual state, lease freshness, blockers and recovery
- [x] Add deterministic concurrency, timeout, kill-switch, API, CLI and UI tests
- [x] Update documentation, run full verification, review and commit
- **Status:** complete

## MIL-3.23 Deterministic Snapshot-to-Paper Ledger Runtime
- [x] Define immutable market snapshot, cycle identity, checkpoint and paper-ledger authority contract
- [x] Add atomic checkpoint/result storage with session fencing and unique idempotency keys
- [x] Implement deterministic effective-configuration calculation from read-only stored candles/funding
- [x] Add crash recovery and duplicate-cycle reuse without double-applying ledger state
- [x] Integrate calculations into bounded runtime cycles while preserving lease/kill fail-safe behavior
- [x] Add explicit local CLI plus read-only checkpoint/result service/API surfaces
- [x] Add task-centered HMI for snapshot boundary, commit state, idempotency and recovery
- [x] Add deterministic snapshot, crash, duplicate, fencing, API, CLI and UI tests
- [x] Update documentation, run full verification, review and commit
- **Status:** complete

## MIL-3.24 PAPER_ONLY Shadow Strategy Bot Orchestrator
- [x] Inspect approved configuration, replay engine, runtime checkpoint, API and HMI contracts
- [x] Define immutable bot/account/order/fill/cycle contracts with independent ledgers
- [x] Implement deterministic four-bot orchestration over one synchronized stored-market snapshot
- [x] Persist idempotent bot-cycle results and expose read-only service/API/HMI evidence
- [x] Add runtime risk-stop behavior that can only freeze PAPER_ONLY bots
- [x] Add deterministic bot isolation, accounting, duplicate, recovery, risk, API and UI tests
- [x] Update MIL-3 documentation and Mac mini operations guidance
- [x] Run targeted and full verification, safety review, and commit the milestone
- **Status:** complete

## MIL-3.25 Forward Bot Operations
- [x] Inspect candle finality, ingestion scheduler, runtime lease, ledger lineage and Mac service contracts
- [x] Define closed-bar trigger, missed/duplicate wake and single-instance scheduling invariants
- [x] Implement deterministic cycle-to-cycle bot account deltas and forward operations status
- [x] Implement actionable local runtime/data/risk alerts with immutable evidence
- [x] Add bounded background runner and deferred Mac LaunchAgent generation without installing it
- [x] Add 7/14-day burn-in progress, continuity and readiness evaluation
- [x] Expose forward operations through read-only API and task-centered UI
- [x] Add deterministic trigger, delta, alert, scheduler, burn-in, API and UI tests
- [x] Update MIL-3 and Mac operations documentation
- [x] Run targeted/full verification, safety review and commit the milestone
- **Status:** complete
