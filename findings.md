# Findings

## Inbox Scan
- `00_Inbox/ChatGPT_Imports/01_AARS_vNext_Master_Spec.md` is an AARS master specification and fits stable knowledge better than project workspace material.
- `00_Inbox/ChatGPT_Imports/AARS_Latest_Stable_View_Spec.md` is a stable-view specification that complements existing glossary, health, dependency, and recovery notes.
- `00_Inbox/README.md` is not an AARS knowledge asset for migration.

## Existing Formal Structure
- Current AARS knowledge notes live under `02_Knowledge/AARS/` with glossary, schemas, templates, and summary sections already present.
- There is no current specs directory, so adding `02_Knowledge/AARS/05_Specs/` is the cleanest canonical target.

## Polymarket Bot Research
- Existing workspace already contains a small Telegram bot scaffold under `telegram-aars-bot/`, which may be reusable for operator command UX and notification patterns.
- This research track needs two distinct outputs: GitHub ecosystem capability mapping and a target-system recommendation that is safer than a copy-paste trading bot.
- Official Polymarket repositories provide a solid execution foundation: authenticated CLOB SDKs in Python/TypeScript plus an official market-maker keeper with midpoint-driven re-quoting loops.
- Official WebSocket coverage is asymmetric for this use case: market channels are public and useful for signal detection, while user channels only cover the bot owner's own account, so whale tracking needs chain analytics or third-party wallet event feeds.
- `structbuild/polymarket-telegram-alerts-bot` is the strongest reference for Telegram-side monitor UX, filter state, webhook verification, and subscriber routing.
- `voicegn/polymarket-bot` contains real code for copy-trade and smart execution patterns, but some data dependencies appear to rely on weakly documented public endpoints and should not be treated as stable infrastructure.
- The most defensible product path is phased: alerting first, decision support second, controlled execution third, maker-follow last and isolated.

## Operations Monitor Reuse
- The dashboard already has first-class sources for scanner status, alert queue, market alerts, family anomaly summaries, opportunity board rows, market workstation summaries, and unified status, so Operations Monitor can be assembled as a read-only aggregation layer instead of inventing new facts.
- `weather-dashboard/src/weather_dashboard/app.py` already loads `render_monitoring_signals_panel`, `render_opportunity_board_panel`, and `render_market_workstation_page`, which gives a direct path to a new homepage-level Operations Monitor layout.
- Telegram already exposes `/monitoring`, `/scanstatus`, `/alerts`, `/anomalies`, `/market`, and `/opportunities`, so the new monitor view can be surfaced as lightweight read-only summaries rather than a new command family.

## PWB-03 Baseline Inputs
- PWB-02 is frozen and accepted, so PWB-03 must stay additive and preserve the Gaussian v0 weather chain.
- The new round is governance-focused: compare engines, store calibration, and govern active probability selection without changing strategy or enabling trading.
- Shadow engines are intentionally placeholders, so their job is comparison and calibration scaffolding rather than model improvement.
- The active primary engine remains `gaussian_v0` until a promotion gate explicitly changes it.

## PWB-03 Storage Baseline
- The governance layer now has dedicated model and SQLite storage support for engine configs, engine runs, comparisons, outcomes, calibration results, and promotion decisions.
- Default engine configs are seeded at database initialization: `gaussian_v0` primary, `deb_shadow_v0` shadow, and `emos_shadow_v0` shadow.
- Repository round-trips for the governance objects are covered by storage smoke tests and stay offline/non-trading.

## PWB-03 Engine Registry Baseline
- The probability engine registry now exposes enabled configs, the primary engine config, and shadow engine configs.
- Shadow engines are deterministic placeholders that compare against Gaussian v0 but do not drive active trading decisions.
- The comparison builder always selects the primary engine run as the active probability and records disagreement without changing engine policy.

## PWB-03 Calibration Baseline
- Calibration is manual-outcome driven and only proceeds when the latest market outcome is `RESOLVED` with a non-null direction hit.
- Brier score, absolute error, and probability bucket are implemented as pure local metrics.
- Promotion decisions are persisted and default to `KEEP_PRIMARY` for `gaussian_v0` and `NEEDS_MORE_DATA` for shadow engines until evidence grows.

## PWB-03 UI Baseline
- Workstation now shows the probability comparison panel alongside the existing weather probability and evidence view.
- History now exposes calibration history controls and rows.
- Settings now exposes the probability engine registry and promotion evaluation entry point for governance review.

## PWB-04C Isolation Baseline
- `backend.main.create_app(db_path, allow_network=False)` now provides isolated FastAPI instances backed by caller-selected SQLite files.
- PWB-02 and PWB-03 API tests now use temporary app instances instead of the module-level default app.
- The new isolation regression test confirms that changing one app's execution mode does not leak into another app with a different database path.

## PWB-04C Router Integration Baseline
- `create_app()` now mounts the opportunities, command, history, settings, weather, evidence, workstation, and probability governance routers.
- The weather router receives `allow_network`, `default_year`, and `default_sigma` from the factory, keeping runtime defaults centralized.
- PWB-04C is frozen as engineering hardening only, with no trading or model-behavior changes.

## PWB-04D Read-Only Connector Baseline
- PWB-04D now has a read-only Polymarket connector boundary with defaults set to `MOCK_ONLY` and `allow_polymarket_network = false`.
- Gamma/CLOB client stubs expose GET-only methods and refuse network access when disabled; no order, cancel, or sign methods are present.
- Weather filtering excludes closed and non-binary markets, and HYBRID mode falls back to mock data when the network is disabled.
- The Settings page now surfaces connector status and warnings without introducing trading controls.

## PWB-04D Phase H/I Baseline
- The actual UI shell for this workspace is `weather-dashboard`, not a React `frontend/` app, so the accepted Phase H implementation was applied to the Streamlit Settings page.
- The Settings connector panel now performs live read-only actions against `/api/polymarket/health`, `/markets`, `/weather-markets`, `/sync-weather-markets`, and `/source-mode` while preserving the no-wallet / no-order / no-live-trading boundary.
- PWB-04D acceptance coverage is now consolidated into a single backend regression file that checks defaults, forbidden methods/fields, normalization, filtering, mock fallback, API behavior, execution-mode isolation, and `LIVE_EXECUTE` rejection.

## PWB-04E Backlog Baseline
- PWB-04E is positioned as a read-only archive round that preserves time-indexed `MarketSnapshot` state rather than adding modeling or trading behavior.
- The accepted capture points are post-scan capture, sync capture, manual archive, and current-source archive.
- The most important safety boundary is that archive writes must never trigger strategy, simulation, execution, or promotion behavior.

## PWB-04E Implementation Baseline
- Snapshot archive persistence now exists as a first-class layer with dedicated models, SQLite storage, repository methods, and an archive service.
- `archive-current-source` and optional sync/scan capture hooks remain non-executing: they archive snapshots only and do not create candidates, run simulations, or trigger execution.
- The current UI shell for PWB-04E is the `weather-dashboard` History page, where the archive panel exposes summary, recent rows, market-series lookup, and current-source archive actions without any trading controls.

## PWB-04F Backlog Baseline
- PWB-04F is positioned as the weather-side companion to PWB-04E: it archives forecast inputs, evidence packs, and weather views rather than market snapshots.
- The critical value of the round is future alignment: market snapshot archive plus weather archive plus probability runs can later become calibration and backtest samples.
- The most important freeze line for implementation is that weather archive behavior must stay passive and must not trigger strategy, simulation, execution, or promotion behavior.

## PWB-04F Implementation Baseline
- Weather archive persistence now exists as a first-class weather-side layer with dedicated models, SQLite storage, repository methods, and an archive service.
- `archive_weather_on_probability_build` is a passive sidecar only: it archives weather-side records after a normal probability build and must not change `model_probability` or weather-view semantics.
- `POST /api/weather-archive/latest/{market_id}` archives existing latest weather-side records from repository state only and does not fetch external weather, run strategy, simulate, or execute.

## PWB-04F Governance Baseline
- PWB-04F now has a dedicated governance document that freezes weather archive as a passive evidence layer rather than a computation or execution layer.
- The strongest red line is that weather archive APIs must not trigger weather fetch, `WeatherProbabilityProvider`, `StrategyRunner`, simulation, execution, calibration, or promotion behavior.

## PWB-04G Backlog Baseline
- PWB-04G is positioned as the read-only outcome-side companion to PWB-04E market archive and PWB-04F weather archive.
- The value of the round is to preserve outcome-resolution facts without introducing settlement execution or automatic strategy behavior.
- The key safety line is that resolver behavior must stay passive: it may store outcome facts, but it must not settle trades, change execution mode, or trigger strategy/simulation/execution flows.

## PWB-04G Implementation Baseline
- PWB-04G now has a separate outcome-side persistence layer for manual market outcomes, weather actual observations, and derived read-only resolution records.
- `resolve-from-weather` uses existing weather actual rows plus current threshold/direction context only; it does not fetch weather, run strategy, simulate, execute, calibrate, or promote.
- The current UI shell for PWB-04G is the `weather-dashboard` History page, where the outcome panel exposes summary, recent rows, market bundle lookup, and manual forms without any trading controls.

## PWB-05 Backlog Baseline
- PWB-05 is positioned as the first round that assembles accepted market archive, weather archive, probability, and outcome facts into reusable historical memory.
- The value of the round is not new modeling but durable sample assembly for later calibration and backtest work.
- The most important safety line is that PWB-05 must stay read-only and non-executing: it may assemble existing records, but it must not re-trigger strategy, simulation, execution, or promotion behavior.

## PWB-05 Implementation Baseline
- PWB-05 now has a first-class calibration-memory and backtest-memory layer with dedicated models, SQLite storage, repository methods, read-only builders, APIs, and dashboard shell visibility.
- Calibration samples are assembled from existing market/weather/probability/outcome records only; missing components stay in eligibility checks rather than triggering rebuilds or fetches.
- Hypothetical backtest memory is derived from calibration samples only and remains analytical memory, not a simulator or execution path.

## PWB-05A Backlog Baseline
- PWB-05A is positioned as the first real DEB shadow round that consumes accepted historical memory rather than placeholder-only logic.
- The value of the round is shadow computation and diagnostics from real sample memory, not active-engine control.
- The most important safety line is that PWB-05A must stay shadow-only and non-executing: it may compute and persist DEB shadow outputs, but it must not change the active engine, trigger strategy, simulation, execution, or promotion behavior.

## PWB-05A Verification Environment
- The local default interpreter available in this session is `/usr/bin/python3`, and it does not currently have `fastapi` installed.
- Because of that environment gap, backend pytest execution for the new PWB-05A acceptance file could not be completed in-session even though static syntax verification passed for the new files.

## PWB-05B Backlog Baseline
- PWB-05B is positioned as the first real EMOS shadow round that consumes accepted historical memory rather than placeholder-only logic.
- The value of the round is shadow computation and diagnostics from real sample memory, not active-engine control.
- The most important safety line is that PWB-05B must stay shadow-only and non-executing: it may compute and persist EMOS shadow outputs, but it must not change the active engine, trigger strategy, simulation, execution, or promotion behavior.

## PWB-05B Verification Environment
- The local default interpreter available in this session is still `/usr/bin/python3`, and it still does not currently have `fastapi` or `pytest` installed.
- Because of that environment gap, backend and dashboard pytest execution for the new PWB-05B acceptance files could not be completed in-session even though static syntax verification passed for the new files.

## PWB-05C Backlog Baseline
- PWB-05C is positioned as the first read-only comparison round that evaluates Gaussian, DEB shadow, and EMOS shadow on the same accepted historical memory.
- The value of the round is cross-engine evidence and ranking visibility, not active-engine control.
- The most important safety line is that PWB-05C must stay read-only and non-executing: it may compute and persist evaluation rows, but it must not change the active engine, trigger strategy, simulation, execution, or promotion behavior.

## PWB-05C Verification Environment
- The local default interpreter available in this session is still `/usr/bin/python3`, and it still does not currently have `fastapi` or `pytest` installed.
- Because of that environment gap, backend and dashboard pytest execution for the new PWB-05C acceptance files could not be completed in-session even though static syntax verification passed for the new files.

## PWB-06 Round Framing
- The architecture's Layer 6 describes a governed action console, so the safest next step after the shadow-evaluation chain is a read-only command review surface.
- The new round should remain advisory only: it may surface approval metadata and decision context, but it must not trigger execution, simulation, or promotion behavior.

## PWB-06 Verification Environment
- The local `python3` shell for this session does not currently have `pydantic` installed, so direct backend smoke execution could not be completed even though the new files passed `py_compile`.
- The bundled workspace Python runtime does allow backend smoke execution, but it does not include `streamlit`, so dashboard panel imports are verified here via `py_compile` rather than a live import smoke.

## PWB-07 Round Framing
- Layer 6 of the architecture is the governance and execution layer, so the next safe extension after command review is a read-only execution-decision review surface.
- The new round must stay advisory only: it may surface execution-mode, gate, and approval context, but it must not trigger execution, simulation, promotion, or trading behavior.

## PWB-07 Verification Environment
- The bundled workspace Python runtime can import the new execution-decision review model and repository paths, so PWB-07 Phase A/B smoke validation passed there.
- The bundled workspace Python runtime in this session does not include `fastapi`, so API smoke for the new execution-decision review router could not be completed here even though the service and repository smokes passed and the Python files compiled.
- The local `python3` runtime can import the new execution-decision review panel and the History shell after the UI wiring change, so the dashboard phase is verified at the import/smoke level even though bundled `pytest` is still unavailable.

## PWB-08 Round Framing
- The next conservative layer after execution-decision review is a read-only execution-queue review surface.
- The round should remain advisory only: it may surface queue state and approval context, but it must not trigger execution, simulation, promotion, or trading behavior.

## PWB-08 Verification Environment
- The local `python3` runtime can compile and smoke-test the new execution-queue review repository layer.
- The local `python3` runtime can compile the new execution-queue review panel and History shell wiring, but it still lacks Streamlit for a live import smoke.
- The bundled runtime remains useful for backend compile/smoke checks, but it does not include `pytest`, so full test execution is still deferred to the project environment with dependencies installed.

## PWB-09 Round Framing
- The next conservative layer after execution-queue review is a read-only approval-window review surface.
- The round should remain advisory only: it may surface approval state and audit context, but it must not trigger execution, simulation, promotion, or trading behavior.

## PWB-09 Verification Environment
- The local `python3` runtime can compile and smoke-test the new approval-window review repository layer.
- The local `python3` runtime can also compile and smoke-test the new approval-window review service layer.
- The local `python3` runtime can compile the new approval-window review panel and the History shell wiring, but live Streamlit rendering remains environment-bound in this session.
- API and dashboard live verification are still partially environment-bound because the bundled runtime does not include full `fastapi` / `pytest` / `streamlit` coverage for an end-to-end run.

## PWB-10 Round Framing
- The next conservative layer after approval-window review is a read-only activation-readiness review surface.
- The round should remain advisory only: it may surface activation-readiness state and governance context, but it must not trigger execution, simulation, promotion, or trading behavior.

## PWB-10 Verification Environment
- The local `python3` runtime can compile and smoke-test the new activation-readiness review repository layer.
- The local `python3` runtime can also compile and smoke-test the new activation-readiness review service layer.
- The local `python3` runtime can compile the new activation-readiness review panel and the History shell wiring, but live Streamlit rendering remains environment-bound in this session.
- API and dashboard live verification are still partially environment-bound because the bundled runtime does not include full `fastapi` / `pytest` / `streamlit` coverage for an end-to-end run.

## PWB-11 Round Framing
- The next conservative layer after activation-readiness review is a read-only activation-authorization review surface.
- The round should remain advisory only: it may surface activation-authorization state and governance context, but it must not trigger execution, simulation, promotion, or trading behavior.

## PWB-11 Verification Environment
- The local `python3` runtime can compile and smoke-test the new activation-authorization review repository layer.
- The local `python3` runtime can also compile and smoke-test the new activation-authorization review service layer.
- The local `python3` runtime can compile the new activation-authorization review panel and the History shell wiring, but live Streamlit rendering remains environment-bound in this session.
- API and dashboard live verification are still partially environment-bound because the bundled runtime does not include full `fastapi` / `pytest` / `streamlit` coverage for an end-to-end run.
## 2026-08-25 — MIL-3.17 kickoff
- The branch is clean at `c8476bf` and is six commits ahead of origin; remote publishing remains separate from implementation.
- MIL-3.16 already supplies immutable acknowledged proposals, same-window trial results, funding completeness checks, and read-only API/UI surfaces.
- The correct forward boundary is each asset's archived trial `evidence_end`, not the trial generation wall-clock time.
- Replay warmup can remain leak-free by loading exactly `warmup_bars - 1` context candles at or before the anchor, so the replay engine's first actionable bar is the first candle strictly after the anchor.
- Forward observation must remain advisory and append-only: no candidate application, no execution route, and no rewriting an earlier checkpoint.
- The existing simulation engine starts strategy actions at index `warmup_bars - 1`; using 59 historical context bars for a 60-bar warmup makes the first actionable bar exactly the first unseen forward candle.
- Existing MIL-3.16 tests already provide deterministic candles, funding, proposal acknowledgement, storage immutability, read-only API, explicit CLI, and static UI safety patterns that MIL-3.17 can extend consistently.
- `ReplayEngine.run_detailed` counts only bars from its warmup boundary onward, filters funding from that same boundary, and initializes a fresh portfolio there; no engine mutation is needed for forward-only measurement.
- A synchronized cross-asset checkpoint should use the minimum latest unseen candle time so every asset is assessed over an identical forward end and no faster feed gets extra evidence.
- The dashboard already validates envelope authority at runtime; the new forward view should add equivalent schema and authority rejection before rendering any status.
- MIL-3.17 domain/storage tests confirm 59 context bars plus 80 unseen bars produce exactly 80 measured bars; funding gaps fail closed and eligible-trial enforcement is explicit.
- Rebuilding the same endpoint must preserve the checkpoint's original lineage to remain idempotent; a later endpoint chains to the prior observation ID and input hash, while older unseen endpoints are rejected.
- Warmup candles must be included in the content hash because they affect the first forward decision, even though they are excluded from all measured performance; the implementation now preserves this reproducibility distinction.
- The storage boundary independently revalidates the archived trial configuration, target strategy and per-asset anchors, so callers cannot bypass the normal CLI by submitting altered parameters or a forward start at/before the trial endpoint.
## 2026-08-25 — MIL-3.18 kickoff
- MIL-3.17 is cleanly committed at `6964d87`; the branch is seven commits ahead of origin.
- MIL-3.18 will govern a sequence of existing immutable checkpoints rather than introduce another strategy or execution mechanism.
- Confirmation must require both a minimum forward horizon and consecutive qualifying checkpoints; a single favorable checkpoint is insufficient.
- The main view should keep current risk, evidence continuity, confirmation progress, decay warnings, and recovery instructions visible without action controls.
- The existing ingestion scheduler is intentionally public-market-data-only; continuous forward observation should be a separate local runner so replay failures cannot interfere with ingestion and the scheduler's declared scope remains truthful.
- Existing shadow stability derives transitions without persisting a second aggregate table. MIL-3.18 can follow that pattern: immutable forward checkpoints remain the source of truth, while stability/governance is rebuilt read-only from their ordered payloads.
- Long-term confirmation should require a minimum measured horizon plus a tail streak of qualifying checkpoints; hard stops override all confirmation progress, and broken lineage must force deferral.
- The stability model can remain read-only and deterministic: it derives score/return/risk transitions, verifies every predecessor ID and input hash, and turns continuity, decay, reversal, rising risk and hard-stop conditions into actionable evidence objects.
- Default confirmation is deliberately stricter than MIL-3.17's first checkpoint: 720 measured 1h bars (30 days) and three consecutive qualifying checkpoints inside a 30-checkpoint evaluation window.
- The monitor is isolated from ingestion, processes every eligible archived trial, reuses an unchanged endpoint idempotently, waits on insufficient history, degrades on integrity/coverage failures, and permanently skips a trial after its latest hard-stop checkpoint.

## MIL-3.18 errors encountered
| Error | Attempt | Resolution |
|---|---:|---|
| Direct `_api_payload()` test expected a returned 400 for a missing `trial_id`, but validation raises before HTTP dispatch wraps it | 1 | Updated the unit test to assert the domain `ValueError`; request dispatch remains responsible for the HTTP 400 envelope |
- The MIL-3.18 control surface passes its targeted syntax/tests and keeps confirmation progress, current risk, checkpoint trace, alarms, recommended response and closure condition in the primary forward-observation card.
- Final review added review-gate authority validation, genesis/non-monotonic lineage checks and a truthful empty-history stability response bound to the requested archived trial.
- No authenticated adapter, credential handling, order call or configuration-application route was added; the new monitor only reads market/trial evidence and archives PAPER_ONLY checkpoints.
## 2026-08-26 — MIL-3.19 kickoff
- MIL-3.18 is cleanly committed at `c2901de`; the branch is eight commits ahead of origin.
- Human review must be an immutable local write path distinct from the read-only HTTP API; the dashboard will display records and blocked actions but never create them.
- Candidate lifecycle will be explicit: observing, acknowledged, paused, restarted/observing, or terminated. Termination is irreversible; restart is allowed only from pause and never bypasses stop/defer evidence.
- Evidence export should be deterministic and self-verifying: trial, checkpoints, derived stability, reviews, per-component SHA-256 hashes and one combined manifest hash.
- Existing proposal review establishes the right authority pattern but is terminal and one-per-proposal; MIL-3.19 needs an append-only lineage-chained event stream because pause and restart are lifecycle transitions rather than a single terminal vote.
- The monitor already has a single per-trial gate before replay, so lifecycle enforcement can fail safely by adding one current-state lookup before the hard-stop and data checks.
- Review storage independently rebuilds current stability from archived checkpoints and verifies its hash, disposition, checkpoint count, warning set, latest observation identity and prior review lineage before accepting an event.
- Evidence bundle identity excludes only the derived stability generation timestamp; archived trial, checkpoints and human review payloads are hashed exactly, then covered by one combined manifest hash.
- The final archive transaction now rechecks both review lineage/time and latest observation identity, closing the window where a concurrent checkpoint could otherwise make an already-built review stale.
- Evidence verification treats authority locks as signed trust claims: changing export-only, parameter-application, automatic-change or live-execution authority invalidates the bundle even if evidence components are untouched.

## MIL-3.19 errors encountered
| Error | Attempt | Resolution |
|---|---:|---|
| One large patch used an outdated storage context and failed atomically | 1 | Split the change into focused review, storage-hardening, export and CLI patches using the current line context |
| Full suite retained MIL-3.18's exact UI version assertion after the console advanced to 03.19 | 1 | Updated the prior stability UI test to assert the current shared console version; all MIL-3.18 functional evidence assertions remain intact |
| First context-integrity check expected `trial_id` inside the archived trial payload, but its identity lives in the storage envelope | 1 | Bound the top-level trial identity to stability plus every observation/review payload, while target strategy remains independently bound to the trial payload |
- Seven MIL-3.19 backend acceptance tests now pass across lifecycle transitions, irreversible termination, stale/tampered evidence rejection, monitor gating, deterministic bundle verification, read-only APIs and explicit local CLIs.
- The read-only lifecycle console exposes current state, permitted local actions, immutable review history, export manifest and recovery guidance without adding a browser write control.

## 2026-08-26 — MIL-3.20 kickoff
- MIL-3.19 is cleanly committed at `5663715`; the branch is nine commits ahead of origin.
- Offline verification must operate from the exported JSON alone and must never require or mutate SQLite.
- Retention must be scoped to a dedicated evidence directory, preserve a verifiable inventory, avoid overwriting files and prune only explicitly recognized bundle/verification artifacts.
- Activation approval is authorization for an isolated PAPER_ONLY configuration sandbox only; it must not alter the active replay defaults, start a trial, place an order or authorize live execution.
- The console should expose actual approval state, prerequisite failures, evidence identity, expiry/revocation state and recovery guidance, but all writes remain explicit local CLI operations.
- Existing SQLite backup logic already demonstrates safe scoping: resolved destination, non-overwrite, temporary write plus atomic replace, integrity verification and filename-pattern-limited pruning. Evidence retention should reuse those principles without mixing database backups and evidence artifacts.
- `DashboardService` currently owns only a `MarketStore`, so durable approval status belongs in SQLite; filesystem retention should remain an explicit offline CLI/report rather than making ordinary API GETs scan or mutate an operator-selected directory.
- Approval should be bound to a verified bundle's combined manifest hash and raw file SHA-256. The trial configuration can be identified by a canonical hash while the approval explicitly leaves active configuration unchanged.
- Final retention hardening must verify both bundle integrity and filename identity before an old artifact becomes eligible for pruning; matching a filename pattern alone is insufficient authority to delete a file.

## MIL-3.20 errors encountered
| Error | Attempt | Resolution |
|---|---:|---|
| Targeted pytest was launched from the repository root with `PYTHONPATH=.` and could not import the nested `aars_market` package | 1 | Run MIL-3 tests from `03_Projects/Polymarket/mil3`, matching the established project test command |
| First expiry-path test referenced a nonexistent storage `_utc` helper | 1 | Reused the storage module's established `_iso` plus `_parse` normalization path |
| Initial Mac mini documentation patch used a slightly different line wrap than the current file | 1 | Read the exact local paragraph and applied the addition against its current wrapping |

## 2026-08-27 — MIL-3.21 kickoff
- MIL-3.20 is cleanly committed at `23be812`; the branch is ten commits ahead of origin.
- Registration should consume exactly one unexpired `APPROVED` review into one immutable configuration entry. The approval ID needs a database uniqueness constraint so concurrent consumers cannot duplicate it.
- Sandbox activation is a mutable pointer plus an append-only event trail. Pointer update, version increment and activation event must commit in one SQLite transaction.
- Read-only GET requests must not reconcile or write expiry events. Instead, effective configuration resolution must derive `EXPIRED_FAIL_SAFE` or `REVOKED_FAIL_SAFE` immediately and expose the stale stored pointer separately.
- A later explicit reconciliation cycle can persist the already-effective invalidation event; safety must never depend on that cycle running.
- Rollback should target the previous pointer recorded by the latest unrolled activation. If that target is missing, expired or revoked, rollback must clear to the baseline/empty state rather than revive unsafe configuration.
- MIL-3.21 will materialize and select configuration only inside a named local sandbox registry. It will not start ReplayEngine, change shared defaults, contact an exchange or add a live execution adapter.
- SQLite foreign keys make configuration deletion impossible while referenced by the sandbox pointer or event history; MIL-3.21 adds no deletion API, preserving rollback and audit evidence.
- A sandbox GET can remain strictly read-only while still enforcing expiry: it exposes both `stored_configuration_id` and a separately derived `effective_configuration_id`, which becomes null immediately when approval validity fails.
- Rollback safety is evaluated at rollback time, not activation time. An expired or revoked previous configuration is never restored; the rollback event atomically clears the pointer instead.
- Optimistic state version, previous pointer and previous event ID are all rechecked under `BEGIN IMMEDIATE`, so a stale activation payload cannot partially update the registry.

## 2026-08-27 — MIL-3.22 kickoff
- MIL-3.21 exposes a strict read-only `effective_configuration_id`; expiry, revocation and approval mismatch already suppress it immediately without waiting for reconciliation.
- The runtime must bind each session to sandbox ID, configuration ID, configuration hash and sandbox state version. A pointer change therefore fences the old worker even if its approval remains valid.
- Runtime authority will be represented by a short renewable lease plus an opaque fencing token. Heartbeats must revalidate the effective configuration and token inside one `BEGIN IMMEDIATE` transaction.
- Kill switch is sandbox-scoped persistent state, defaults fail-safe, and can only be armed or cleared by an explicit local CLI with operator and note. The read-only HTTP API will expose but never change it.
- A bounded runtime cycle will record governed configuration consumption and health only. It will not call ReplayEngine, an exchange adapter, an order function, or any live execution path.
- UI design must distinguish requested/leased state from effective runtime state, show heartbeat age and stop cause, and keep kill-switch/recovery guidance visible without browser write controls.
- Runtime event versions and kill-switch event versions have database uniqueness constraints, making each append-only state transition unambiguous.
- Kill-switch ARM rejects timestamps older than a running session's latest heartbeat so the atomic stop trail cannot move backward.
- Runtime effective-state diagnosis checks kill authority, pointer/configuration authority and then lease freshness, preserving the most useful root-cause evidence.

## MIL-3.22 errors encountered
| Error | Attempt | Resolution |
|---|---:|---|
| Initial combined planning patch referenced a nonexistent MIL-3.21 error heading and failed atomically | 1 | Applied the plan/progress update against exact current context and appended findings separately |
| First MIL-3.22 compile command used repository-relative source paths while already running from the nested MIL-3 root | 1 | Rerun compilation with `aars_market/...` paths from the MIL-3 root |
| Combined runtime UI patch assumed a standalone `.isolated-registry-deck` CSS selector that the current stylesheet does not contain | 1 | Split HTML and CSS edits, then append runtime styles against the actual stylesheet tail |

## 2026-08-27 — MIL-3.23 kickoff
- The approved runtime configuration already contains symbols, timeframe, warmup, proposed strategy parameters and deterministic paper cost/risk settings from the archived trial.
- MIL-3.23 will reuse `ReplayEngine` and the existing paper ledger instead of inventing a second accounting model. Each cycle calculates the proposed strategy cumulatively through one synchronized stored-candle boundary.
- Cycle identity is sandbox + configuration + synchronized snapshot boundary, not session ID. This makes a crash-recovery session resume the same cycle instead of double-applying it.
- A snapshot reservation stores content hashes and exact per-asset boundaries. Commit rebuilds the snapshot under a write lock and rejects source drift before atomically inserting the ledger result and marking the checkpoint committed.
- Checkpoint states are `RESERVED` and `COMMITTED`; append-only events record `RESERVE`, `RECOVER` and `COMMIT`. A committed cycle is immutable and duplicate calls return the existing result.
- Recovery may transfer a RESERVED cycle only after its previous owner is no longer effectively RUNNING. A live fenced owner cannot be stolen.
- Each committed result is a cumulative deterministic ledger view, chained to the previous committed cycle. This avoids mutable incremental portfolio state and makes restart verification reproducible.
- No raw market write, replay order, exchange adapter or live connector is introduced. Market candles/funding are read-only inputs and all fills remain the existing simulated paper accounting outputs.
- Non-finite internal leverage/risk values from pathological paper liquidation are normalized to strict JSON `null`; explicit liquidation event/risk evidence remains available instead of serializing `NaN` or `Infinity`.

## MIL-3.23 errors encountered
| Error | Attempt | Resolution |
|---|---:|---|
| A MIL-3.22 bounded-runtime test expected a committed ledger even though its synthetic clock predates the minimum snapshot history | 1 | Keep that case as an explicit WAITING assertion and verify a committed cycle in the current-time CLI fixture |
| The prior MIL-3.22 UI test retained the shorter no-button recovery sentence after MIL-3.23 added RECOVER to the explicit prohibition | 1 | Updated the shared console assertion to the stricter MIL-3.23 wording |

## 2026-08-28 — MIL-3.24 kickoff
- The current MIL-3.23 runtime already provides synchronized content-addressed market snapshots, fenced cycles, atomic checkpoints and cumulative ReplayEngine paper-ledger results.
- MIL-3.24 will add four isolated shadow bots—Buy & Hold, Spot Grid, Futures Long Grid and AARS Dynamic—using the same snapshot but independent virtual accounts and result identities.
- All bot actions remain simulated ledger intents/fills. Runtime risk response may freeze a bot or block a cycle, but cannot submit an order, change shared configuration, or authorize live execution.
- The first implementation should reuse the existing strategy and accounting engines rather than create divergent P&L calculations.
- `simulation.py` already implements the exact four strategies plus a common `ReplayEngine`; it accounts for realized/grid/unrealized P&L, fees, slippage, funding, exposure, leverage, margin buffer and liquidation approximation.
- The approved `ValidationCandidate` carries parameters for all four bot constructors even when one target strategy was selected, so a fleet can remain fully bound to the immutable approved configuration without inventing mutable runtime settings.
- The safest persistence seam is the existing atomic cycle result: add one content-addressed bot-fleet section to the ledger payload so checkpoint commit, crash recovery and duplicate-cycle reuse cover all four bots together without a second mutable transaction.
- Approved trial settings already carry `stop_max_drawdown` and `stop_max_liquidation_risk`; these can govern each bot without adding an unapproved runtime knob. Any liquidation approximation event is an unconditional stop.
- Existing `PaperPortfolio` returns deterministic simulated fill records but `ReplayResult` discards them. MIL-3.24 should retain fill evidence and final account state in the result while avoiding any external order object or connector.
- Fleet funding coverage must be COMPLETE even when the originally selected candidate did not use funding, because the fixed four-bot fleet always contains Futures Grid and AARS Dynamic.
- A risk breach must change future simulation behavior, not merely label a completed replay. The fleet ReplayEngine path will flatten the affected virtual account once, mark it FROZEN, and suppress later strategy actions; existing replay callers remain unchanged unless they explicitly provide a risk-stop policy.

## MIL-3.24 errors encountered
| Error | Attempt | Resolution |
|---|---:|---|
| System `pytest` did not add the nested MIL-3 root to `sys.path`, causing collection-time `ModuleNotFoundError: aars_market` | 1 | Rerun with `PYTHONPATH=.` from the MIL-3 directory; no test or implementation failure occurred |
| MIL-3.23 UI regression retained an exact `03.23` console version assertion after the shared shell advanced to `03.24` | 1 | Updated only the version assertion; all MIL-3.23 snapshot, commit, idempotency and no-control assertions remain unchanged |
| Six earlier shared-console UI tests also retained the exact `03.23` version after the full suite reached them | 1 | Updated only those version strings to `03.24`; their feature and safety assertions remain unchanged |

- The embedded fleet uses the snapshot boundary as its deterministic calculation timestamp; retrying a crashed RESERVED cycle later therefore rebuilds the same fleet/result identity instead of producing a time-dependent hash.
- Legacy MIL-3.23 ledger v1 verification remains accepted for already committed cycles, while new calculations emit ledger v2 with a separately verified bot-fleet hash bound to cycle, snapshot and configuration identities.
- Final audit hardened the risk-stop path for already insolvent paper approximations: the account becomes FROZEN and retains liquidation evidence without attempting or inventing a flatten fill that cannot be funded.
