# MIL-3.22 Governed Isolated Runtime Console HMI Design v10

## 1. Page Purpose

Provide one read-only surface for deciding whether a PAPER_ONLY shadow strategy deserves further research and whether its evidence remains stable across daily validation cycles. It must not be interpreted as a trading terminal.

## 2. User Role and Scenario

The user is a research operator comparing Buy & Hold, Spot Grid, Leveraged Futures Long Grid and AARS Dynamic on the same replay window. The primary scenario is risk-adjusted comparison, followed by investigation of leverage, drawdown, data freshness and evidence.

## 3. Task Model

1. Confirm execution authority and data trust.
2. Identify the highest current replay risk.
3. Compare the four strategy summaries.
4. Inspect equity/drawdown or liquidation/leverage traces.
5. Switch BTC/ETH/SOL and replay windows without changing execution authority.
6. Review current or archived Latest Stable View evidence.
7. Review combined BTC/ETH/SOL exposure and the asset driving highest risk.
8. Compare two Stable View archives for semantic change.
9. Resolve open risk objects before accepting a shadow strategy.
10. Distinguish the cadence used by the replay from Binance's latest observed funding cadence.
11. Confirm the latest immutable daily shadow snapshot and synchronized evidence time.
12. Review parameter churn, recurring warnings, return/risk drift and Review Gate transitions.
13. Drill into per-asset train-selected candidates without exposing raw JSON as the primary view.
14. Distinguish insufficient evidence from material rejection and a fully passing promotion candidate.
15. Inspect every governance threshold, impact and recovery condition without changing strategy state.
16. Inspect immutable before/after paper parameters, observed risk evidence, stop conditions and the terminal human review record.
17. Confirm that acknowledgement did not apply a parameter and that no approve/apply control exists in the console.
18. Compare the baseline and proposed configuration on identical hashed trial inputs.
19. Distinguish stored runtime status from current effective runtime authority.
20. Confirm kill-switch state, heartbeat age, lease deadline, fencing version and stop cause.
21. Review immutable runtime and kill-switch events plus the exact local recovery path.
19. Identify hard-stop triggers before considering extended paper observation.
20. Trace the result to its proposal, source snapshot, exact settings and per-asset evidence.
21. Confirm funding completeness and effective Binance cadence for each trial asset.
22. Verify the candidate lifecycle, permitted local human action and immutable review lineage.
23. Verify the evidence-bundle component count and combined SHA-256 before external retention.
24. Distinguish offline verification, retention and approval as separate governed tasks.
25. Confirm every activation prerequisite, sandbox scope, expiry and revocation state without applying configuration.
26. Distinguish the stored sandbox pointer from the currently effective configuration.
27. Verify state version, atomic event lineage, rollback target validity and fail-safe invalidation reason.

## 4. Information Architecture

- Top: PAPER_ONLY authority, freshness, highest risk, payload time and read-only view selectors.
- Left: four-strategy comparison set.
- Center: selected strategy metrics, traces and common-ledger table.
- Right: liquidation-risk priority and actionable risk queue.
- Lower deck: Latest Stable View, P&L attribution, cross-asset portfolio risk and Stable View differences.
- Continuous-shadow deck: Latest Stable Snapshot, history trust, safe next step, stability trace, warning memory, daily change log and selected immutable evidence.
- Governance card: advisory disposition, permanent authority locks, evidence window, blocking/rejection counts, ordered checks and conservative policy thresholds.
- Paper proposal card: immutable proposal status, deterministic selection provenance, before/after changes, risk boundary, stop condition and human review record.
- Paper trial card: advisory result, authority locks, common comparison, cost/P&L deltas, hard-stop result, per-asset evidence and input hashes.

## 5. Layout Design

The desktop layout follows a flight-recorder/control-desk pattern with a persistent status header and three operational columns. Below 1250 px the risk rail moves below the center analysis; below 900 px the page becomes a single-column inspection sequence. No horizontal page overflow is permitted.

## 6. Component List

- `SystemStatusBar`
- `DegradedModeBanner`
- `StrategyComparisonRail`
- `SituationSummaryPanel`
- `ReplayTracePanel`
- `CommonLedgerTable`
- `LiquidationRiskDial`
- `AlertActionCard`
- `LatestStableViewCard`
- `EvidenceTracePanel`
- `PaperLedgerAttribution`
- `ParameterProvenanceDrawer`
- `MarketAndWindowSelector`
- `StableViewArchiveSelector`
- `FundingHistoryStatus`
- `FundingCoverageAlert`
- `CrossAssetPortfolioRiskPanel`
- `StableViewDiffPanel`
- `FundingCadenceProvenance`
- `LatestStableSnapshotBanner`
- `ShadowHistoryTrustIndicator`
- `ShadowStabilityTrace`
- `RecurringWarningMemory`
- `DailySnapshotTimeline`
- `PerAssetCandidateEvidence`
- `PromotionGovernanceDecision`
- `PromotionAuthorityLockPanel`
- `PromotionCheckEvidence`
- `PromotionRecoveryCondition`
- `PaperConfigurationProposalCard`
- `ParameterDifferencePanel`
- `PaperTrialStopCondition`
- `ImmutableHumanReviewRecord`
- `PaperTrialResultCard`
- `CommonInputAuthorityBar`
- `BaselineProposedComparison`
- `TrialStopConditionPanel`
- `TrialInputHashTrace`
- `ForwardObservationCard`
- `StrictOutOfSampleBoundary`
- `ForwardCheckpointLineage`
- `ForwardConfirmationProgress`
- `ForwardStabilityTrace`
- `ForwardEvidenceAlarm`
- `ForwardCandidateLifecycle`
- `ImmutableForwardReviewHistory`
- `ForwardEvidenceManifest`
- `OfflineEvidencePrerequisitePanel`
- `EvidenceRetentionPolicyCard`
- `IsolatedActivationLifecycle`
- `ImmutableActivationReviewHistory`
- `StoredEffectiveConfigurationPanel`
- `ImmutableRegistryEntryCard`
- `RollbackGatePanel`
- `AtomicSandboxEventTrail`

## 7. Data Model

The page consumes the existing MIL-3 schemas plus `mil3.isolated-paper-configuration-index.v1`, `mil3.isolated-paper-sandbox-view.v1` and `mil3.isolated-paper-sandbox-event-index.v1`. The client rejects any execution mode other than `PAPER_ONLY`; configuration and sandbox evidence must prove that no strategy process starts and shared, automatic and live authority remain disabled. An effective configuration is accepted only when the sandbox state is exactly `ACTIVE`; all fail-safe states require a null effective configuration.

## 8. Alarm and Risk Design

Risk items expose severity, object, trigger, impact, recommended next step, status and closure condition. Highest liquidation risk remains in the main view. Funding gaps explicitly warn that futures costs may be understated and state the effective cadence/provenance. Current Binance cadence and replay cadence remain visibly distinct. Portfolio degradation names affected assets and never implies cross-margin netting.

Recurring validation warnings are treated as evidence objects. Each shows its recurrence count and a specific review or recovery instruction. Parameter churn, insufficient daily history, DEFER transitions and liquidation-risk drift remain visible in the main continuous-shadow deck.

Governance orders material `REJECT` checks before `BLOCK` and `PASS` checks. Non-pass checks state their observed value, requirement, impact and recovery condition. Color is reinforced by explicit text labels.

The trial hard-stop panel remains in the main evidence card. `STOP_TRIAL` uses red plus explicit text; no-stop and continuation states use explicit labels rather than color alone. Drawdown, liquidation risk and breach count are always visible.

Funding-dependent trials fail before replay when cadence-aware coverage is missing or gapped. Each asset card shows coverage status, effective cadence and cadence source.

## 9. Automation / AI Design

AARS output is presented as a recommendation with state, confidence, Bull/Base/Bear probabilities, supporting evidence, counter evidence and the transparent decision reason. Daily snapshot detail separately identifies the train-selected validation candidate and the fixed monitored portfolio policy so research selection is never presented as automatic promotion. `PROMOTION_CANDIDATE` authorizes only a separate human paper-only review. It has no execution authority or action control.

MIL-3.15 proposal selection exposes its cross-asset mode and tie-break. Expected risk impact is labeled `NOT_FORECAST`. An acknowledgement is shown as an immutable human record and explicitly states that it did not apply parameters.

MIL-3.16 exposes the common-input rule, aggregation method, exact input hash and advisory scoring boundary. `ELIGIBLE_FOR_EXTENDED_PAPER_OBSERVATION` is not parameter authority.

## 10. Degraded Mode and Recovery

Missing, stale or unconfirmed data produces a prominent degraded banner. The screen states what remains permitted (inspect stable replay), what is blocked (treating the view as current) and how to recover (refresh candles and regenerate the payload). The embedded strategy demonstration payload is always degraded. Continuous-shadow sample history is never fabricated: direct-file or unavailable-API mode instead shows the explicit local recovery path.

If no proposal exists, the console keeps `NO CHANGE PERMITTED` visible and explains that an explicit local proposal may be created only after promotion candidacy. If the proposal API is unavailable, no review or parameter state is inferred.

If no trial exists, the console shows `NO CONFIGURATION APPLIED` and states that an acknowledged proposal is required. If the API or trial evidence is unavailable, no stop result or disposition is inferred.

If no forward checkpoint exists, the console states that an eligible trial and new market data are required. If its boundary or authority evidence is invalid, no forward disposition is rendered and historical results are never treated as out-of-sample evidence.

If forward stability is unavailable, the checkpoint itself may remain visible but the console states `NO PERSISTENCE CLAIM`. Stability alarms remain continuously visible in the main card and expose trigger, impact, recommended response and closure condition without dismissal or execution controls.

If lifecycle, latest-review or manifest evidence is unavailable or violates its
authority schema, the console states `NO HUMAN ACTION PERMITTED`. It does not
infer a state, review or export identity. Termination is visibly irreversible.

If evidence policy or isolated approval evidence is unavailable, the console
shows `APPROVAL UNAVAILABLE`, blocks every prerequisite and infers no sandbox
authority. Expired, rejected and revoked states state their terminal recovery
path in text as well as color.

If registry, sandbox or pointer-event evidence is unavailable, the console
shows `REGISTRY UNAVAILABLE`, infers no effective configuration and blocks
rollback. A stored pointer remains visible for audit when expiry or revocation
makes it ineffective.

If runtime evidence is unavailable, the console shows `RUNTIME UNAVAILABLE`,
infers the kill switch as armed and permits no runtime action. If a stored
RUNNING session loses its lease or authority, the fail-safe effective state and
stop cause remain visible until explicit reconciliation persists the stop.

## 11. User Actions and Gates

Available actions only change the inspected market, replay window, archive, strategy, trace, diff baseline, validation-strategy filter or immutable snapshot detail. Refresh reads evidence and recomputes advisory governance but does not archive or promote anything. There are no order, credential, live-mode, approval, parameter-change or execution controls. A failed switch preserves the last displayed stable evidence and raises the degraded banner.

Proposal creation and terminal human review are separate explicit local commands. The browser exposes neither command as a button and performs only GET requests.

Trial execution is also an explicit local command. The browser can inspect archived trial evidence only; it cannot run, rerun, accept or apply a trial.

Forward acknowledgement, pause, restart, termination and complete evidence
export are also explicit local commands. The browser can inspect lifecycle,
review and manifest evidence only; it cannot create a review or export file.

Offline verify/retain and isolated approve/reject/revoke are explicit local
commands. The browser performs GET requests only and has no approve, activate,
revoke or configuration control.

Registry REGISTER, ACTIVATE, ROLLBACK and RECONCILE are explicit local commands.
The browser cannot mutate the sandbox pointer or start a strategy process.

Runtime RUN, STOP, ARM_KILL, CLEAR_KILL and RECONCILE are explicit local
commands. The browser cannot acquire a lease, renew a heartbeat or change the
kill switch. Clearing the kill switch never restarts a stopped session.

## 12. HMI Review Gate

- G1 Task Fit: Accept
- G2 Situation Visibility: Accept
- G3 Risk Visibility: Accept
- G4 Action Clarity: Accept
- G5 Action Gate: Accept; no execution actions exist
- G6 Alarm Actionability: Accept
- G7 Data Trust: Accept
- G8 Automation Transparency: Accept
- G9 Recovery: Accept
- G10 Evidence: Accept with Minor Issues; immutable snapshot IDs and per-asset fold evidence are visible, while formal usability validation remains future work

Overall disposition: **Accept with Minor Issues for PAPER_ONLY research use**.

## 13. Run and Regenerate

From `03_Projects/Polymarket/mil3`:

```bash
python run_ingest.py --db mil3_market.sqlite --days 365
python run_funding_ingest.py --db mil3_market.sqlite --days 365
python run_scheduler.py --db mil3_market.sqlite --poll-seconds 3600 --max-cycles 1
python run_archive.py --db mil3_market.sqlite --symbol SOLUSDT --window 90d
python run_shadow_daily.py --db mil3_market.sqlite --validation-strategy AARS_DYNAMIC
python run_paper_proposal.py --db mil3_market.sqlite --strategy AARS_DYNAMIC
python run_paper_review.py --db mil3_market.sqlite --proposal-id <proposal_id> --disposition ACKNOWLEDGED_FOR_PAPER_TRIAL --reviewer local-owner --note "Paper trial only."
python run_paper_trial.py --db mil3_market.sqlite --proposal-id <proposal_id>
python run_forward_monitor.py --db mil3_market.sqlite --max-cycles 1
python run_forward_review.py --db mil3_market.sqlite --trial-id <trial_id> --action PAUSE_PAPER_OBSERVATION --reviewer local-owner --note "Pause for review."
python run_forward_evidence_export.py --db mil3_market.sqlite --trial-id <trial_id> --output evidence/<trial_id>.json
python run_forward_evidence_verify.py --bundle evidence/<trial_id>.json --report evidence/<trial_id>.verification.json
python run_forward_evidence_retain.py --bundle evidence/<trial_id>.json --archive-dir /Volumes/AARS-Evidence/forward
python run_isolated_activation_review.py --db mil3_market.sqlite --trial-id <trial_id> --action REJECT_ISOLATED_PAPER_ACTIVATION --bundle evidence/<trial_id>.json --reviewer local-owner --note "Evidence is not ready."
python run_isolated_paper_config.py --db mil3_market.sqlite --action REGISTER --trial-id <trial_id>
python run_isolated_paper_config.py --db mil3_market.sqlite --action ACTIVATE --configuration-id <configuration_id> --sandbox-id aars-paper-sandbox --operator local-owner --note "Select isolated pointer."
python run_isolated_paper_config.py --db mil3_market.sqlite --action RECONCILE
python run_isolated_paper_runtime.py --db mil3_market.sqlite --action CLEAR_KILL --sandbox-id aars-paper-sandbox --operator local-owner --note "Initialize runtime control."
python run_isolated_paper_runtime.py --db mil3_market.sqlite --action RUN --sandbox-id aars-paper-sandbox --max-cycles 1
python run_isolated_paper_runtime.py --db mil3_market.sqlite --action RECONCILE
python run_api.py --db mil3_market.sqlite --port 8765
```

Open `http://127.0.0.1:8765/`. The server binds to localhost by default and exposes a GET/HEAD/OPTIONS-only API.

For a no-server preview, open `ui/index.html` directly. Direct-file mode uses the degraded demonstration payload; market/window/archive controls require the read-only local API.

For personal long-running Mac mini installation, health, backup, upgrade and restore procedures, see `../MAC_MINI_OPERATIONS.md`.
