const state = {
  payload: null,
  selectedStrategy: "AARS_DYNAMIC",
  chartMode: "equity",
  usingSample: false,
  viewingArchive: null,
  shadowStability: null,
  selectedShadowSnapshot: null,
  promotionGovernance: null,
  paperProposal: null,
  paperTrial: null,
  forwardObservation: null,
  forwardStability: null,
  forwardLifecycle: null,
  isolatedActivation: null,
  isolatedSandbox: null,
  isolatedRuntime: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];

const strategyLabels = {
  BUY_HOLD: "BUY & HOLD",
  SPOT_GRID: "SPOT GRID",
  FUTURES_LONG_GRID_10X: "FUTURES GRID · 10X",
  AARS_DYNAMIC: "AARS DYNAMIC",
};

function escapeHtml(value) {
  return String(value ?? "—")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatPercent(value, digits = 1, signed = false) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  const number = Number(value) * 100;
  const sign = signed && number > 0 ? "+" : "";
  return `${sign}${number.toFixed(digits)}%`;
}

function formatNumber(value, digits = 2) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  return Number(value).toFixed(digits);
}

function formatMoney(value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return "—";
  const sign = Number(value) > 0 ? "+" : Number(value) < 0 ? "−" : "";
  return `${sign}$${Math.abs(Number(value)).toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short", timeZone: "UTC" }) + " UTC";
}

function currentStrategy() {
  return state.payload.strategies.find((item) => item.id === state.selectedStrategy) ?? state.payload.strategies[0];
}

function validatePayload(payload) {
  if (!["mil3.dashboard.v1", "mil3.dashboard.v2"].includes(payload.schema_version)) throw new Error("unsupported dashboard schema");
  if (payload.execution_mode !== "PAPER_ONLY") throw new Error("unsafe execution mode rejected");
  return payload;
}

function validateShadowPayload(payload, schema) {
  if (payload.schema_version !== schema) throw new Error(`unsupported ${schema} schema`);
  if (payload.execution_mode !== "PAPER_ONLY") throw new Error("unsafe shadow execution mode rejected");
  if (payload.review_gate?.live_execution_allowed !== false) throw new Error("shadow evidence did not deny live execution");
  return payload;
}

function validatePromotionGovernance(payload) {
  if (payload.schema_version !== "mil3.promotion-governance.v1") throw new Error("unsupported promotion governance schema");
  if (payload.execution_mode !== "PAPER_ONLY") throw new Error("unsafe governance execution mode rejected");
  if (payload.decision?.automatic_strategy_change_allowed !== false) throw new Error("automatic strategy change was not locked");
  if (payload.decision?.live_execution_allowed !== false || payload.review_gate?.live_execution_allowed !== false) {
    throw new Error("governance evidence did not deny live execution");
  }
  return payload;
}

function validatePaperProposalIndex(payload) {
  if (payload.schema_version !== "mil3.paper-configuration-proposal-index.v1") throw new Error("unsupported paper proposal index schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe paper proposal index rejected");
  if (payload.proposal_application_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("paper proposal index did not preserve authority locks");
  }
  return payload;
}

function validatePaperProposalEnvelope(payload) {
  if (payload.schema_version !== "mil3.paper-configuration-proposal-envelope.v1") throw new Error("unsupported paper proposal envelope schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe paper proposal envelope rejected");
  if (payload.proposal_application_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("paper proposal envelope did not preserve authority locks");
  }
  const authority = payload.proposal?.authority;
  if (authority?.proposal_application_allowed !== false || authority?.automatic_strategy_change_allowed !== false || authority?.live_execution_allowed !== false) {
    throw new Error("paper proposal did not preserve authority locks");
  }
  if (payload.review && (payload.review.acknowledgement_applies_parameters !== false || payload.review.live_execution_allowed !== false)) {
    throw new Error("paper proposal review exceeded advisory authority");
  }
  return payload;
}

function validatePaperTrialIndex(payload) {
  if (payload.schema_version !== "mil3.paper-trial-result-index.v1") throw new Error("unsupported paper trial index schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe paper trial index rejected");
  if (payload.trial_application_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("paper trial index did not preserve authority locks");
  }
  return payload;
}

function validatePaperTrialEnvelope(payload) {
  if (payload.schema_version !== "mil3.paper-trial-result-envelope.v1") throw new Error("unsupported paper trial envelope schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe paper trial envelope rejected");
  if (payload.trial_application_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("paper trial envelope did not preserve authority locks");
  }
  const authority = payload.trial?.authority;
  const gate = payload.trial?.review_gate;
  if (authority?.trial_application_allowed !== false || authority?.automatic_strategy_change_allowed !== false || authority?.live_execution_allowed !== false) {
    throw new Error("paper trial did not preserve authority locks");
  }
  if (gate?.trial_application_allowed !== false || gate?.automatic_strategy_change_allowed !== false || gate?.live_execution_allowed !== false) {
    throw new Error("paper trial review gate exceeded advisory authority");
  }
  return payload;
}

function validateForwardObservationIndex(payload) {
  if (payload.schema_version !== "mil3.forward-observation-index.v1") throw new Error("unsupported forward observation index schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe forward observation index rejected");
  if (payload.observation_application_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("forward observation index did not preserve authority locks");
  }
  return payload;
}

function validateForwardObservationEnvelope(payload) {
  if (payload.schema_version !== "mil3.forward-observation-envelope.v1") throw new Error("unsupported forward observation envelope schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe forward observation envelope rejected");
  if (payload.observation_application_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("forward observation envelope did not preserve authority locks");
  }
  const observation = payload.observation;
  if (observation?.boundary?.policy !== "STRICTLY_AFTER_TRIAL_EVIDENCE_END" || observation?.boundary?.historical_replay_included !== false || observation?.boundary?.warmup_context_affects_performance !== false) {
    throw new Error("forward observation did not preserve the out-of-sample boundary");
  }
  const authority = observation?.authority;
  const gate = observation?.review_gate;
  if (authority?.observation_application_allowed !== false || authority?.automatic_strategy_change_allowed !== false || authority?.live_execution_allowed !== false) {
    throw new Error("forward observation did not preserve authority locks");
  }
  if (gate?.observation_application_allowed !== false || gate?.automatic_strategy_change_allowed !== false || gate?.live_execution_allowed !== false) {
    throw new Error("forward observation review gate exceeded advisory authority");
  }
  return payload;
}

function validateForwardStability(payload) {
  if (payload.schema_version !== "mil3.forward-stability.v1") throw new Error("unsupported forward stability schema");
  if (payload.execution_mode !== "PAPER_ONLY") throw new Error("unsafe forward stability mode rejected");
  const authority = payload.authority;
  const gate = payload.review_gate;
  if (authority?.observation_application_allowed !== false || authority?.automatic_strategy_change_allowed !== false || authority?.live_execution_allowed !== false) {
    throw new Error("forward stability did not preserve authority locks");
  }
  if (gate?.observation_application_allowed !== false || gate?.automatic_strategy_change_allowed !== false || gate?.live_execution_allowed !== false) {
    throw new Error("forward stability review gate exceeded advisory authority");
  }
  return payload;
}

function validateForwardLifecycle(payload) {
  if (payload.schema_version !== "mil3.forward-candidate-lifecycle.v1") throw new Error("unsupported forward lifecycle schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe forward lifecycle rejected");
  if (payload.review_action_applies_parameters !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("forward lifecycle did not preserve authority locks");
  }
  return payload;
}

function validateForwardReviewEnvelope(payload) {
  if (payload.schema_version !== "mil3.forward-candidate-review-envelope.v1") throw new Error("unsupported forward review envelope schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe forward review envelope rejected");
  if (payload.review_action_applies_parameters !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("forward review envelope did not preserve authority locks");
  }
  const review = payload.review;
  if (review?.review_action_applies_parameters !== false || review?.automatic_strategy_change_allowed !== false || review?.live_execution_allowed !== false) {
    throw new Error("forward human review exceeded advisory authority");
  }
  return payload;
}

function validateForwardEvidenceManifest(payload) {
  if (payload.schema_version !== "mil3.forward-evidence-manifest.v1") throw new Error("unsupported forward evidence manifest schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true || payload.evidence_export_only !== true) throw new Error("unsafe forward evidence manifest rejected");
  if (payload.review_action_applies_parameters !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("forward evidence manifest did not preserve authority locks");
  }
  if (!/^[0-9a-f]{64}$/.test(payload.manifest?.combined_sha256 || "")) throw new Error("forward evidence manifest hash is invalid");
  return payload;
}

function validateEvidenceGovernancePolicy(payload) {
  if (payload.schema_version !== "mil3.evidence-governance-policy.v1") throw new Error("unsupported evidence governance policy schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true || payload.offline_verification_required !== true) throw new Error("unsafe evidence governance policy rejected");
  if (payload.approval_applies_configuration !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("evidence governance policy exceeded paper authority");
  }
  return payload;
}

function validateIsolatedActivationLifecycle(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-activation-lifecycle.v1") throw new Error("unsupported isolated activation lifecycle schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe isolated activation lifecycle rejected");
  if (payload.approval_applies_configuration !== false || payload.shared_configuration_change_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("isolated activation lifecycle exceeded sandbox authority");
  }
  if (payload.isolated_paper_activation_allowed !== (payload.current_state === "APPROVED")) throw new Error("isolated activation current authority differs from state");
  return payload;
}

function validateIsolatedActivationReviewEnvelope(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-activation-review-envelope.v1") throw new Error("unsupported isolated activation review envelope schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe isolated activation review rejected");
  if (payload.approval_applies_configuration !== false || payload.shared_configuration_change_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("isolated activation review envelope exceeded sandbox authority");
  }
  const authority = payload.review?.authority;
  if (authority?.approval_applies_configuration !== false || authority?.shared_configuration_change_allowed !== false || authority?.automatic_strategy_change_allowed !== false || authority?.live_execution_allowed !== false) {
    throw new Error("isolated activation human review exceeded sandbox authority");
  }
  if (authority?.isolated_paper_activation_allowed !== (payload.review?.resulting_state === "APPROVED")) throw new Error("isolated activation review authority differs from decision");
  return payload;
}

function validateIsolatedConfigurationIndex(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-configuration-index.v1") throw new Error("unsupported isolated configuration index schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true || payload.registry_entries_inert !== true) throw new Error("unsafe isolated configuration index rejected");
  if (payload.starts_strategy_process !== false || payload.shared_configuration_change_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("isolated configuration index exceeded registry authority");
  }
  return payload;
}

function validateIsolatedSandbox(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-sandbox-view.v1") throw new Error("unsupported isolated sandbox schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe isolated sandbox rejected");
  if (payload.starts_strategy_process !== false || payload.shared_configuration_change_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("isolated sandbox exceeded pointer authority");
  }
  const effective = payload.effective_state === "ACTIVE";
  if ((payload.effective_configuration_id !== null) !== effective || (payload.effective_configuration !== null) !== effective) {
    throw new Error("isolated sandbox effective configuration differs from fail-safe state");
  }
  return payload;
}

function validateIsolatedSandboxEventIndex(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-sandbox-event-index.v1") throw new Error("unsupported isolated sandbox event index schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true) throw new Error("unsafe isolated sandbox events rejected");
  if (payload.starts_strategy_process !== false || payload.shared_configuration_change_allowed !== false || payload.automatic_strategy_change_allowed !== false || payload.live_execution_allowed !== false) {
    throw new Error("isolated sandbox events exceeded pointer authority");
  }
  return payload;
}

function validateIsolatedRuntime(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-runtime-index.v1") throw new Error("unsupported isolated runtime schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true || payload.browser_control_allowed !== false) throw new Error("unsafe isolated runtime rejected");
  if (payload.configuration_consumption_only !== true || payload.replay_started !== false || payload.order_path_present !== false || payload.live_execution_allowed !== false) {
    throw new Error("isolated runtime exceeded consumption-only authority");
  }
  if (payload.kill_switch?.schema_version !== "mil3.isolated-paper-runtime-kill-switch.v1" || payload.kill_switch?.read_only !== true || payload.kill_switch?.browser_control_allowed !== false) {
    throw new Error("isolated runtime kill switch authority is invalid");
  }
  const latest = payload.latest_session;
  if (latest && (latest.schema_version !== "mil3.isolated-paper-runtime-session-view.v1" || latest.read_only !== true || latest.browser_control_allowed !== false || latest.live_execution_allowed !== false)) {
    throw new Error("isolated runtime session authority is invalid");
  }
  if (latest?.effective_status === "RUNNING" && (latest.stored_status !== "RUNNING" || payload.kill_switch.effective_state !== "CLEAR")) {
    throw new Error("isolated runtime effective state differs from stored authority");
  }
  return payload;
}

function validateIsolatedRuntimeEventIndex(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-runtime-event-index.v1") throw new Error("unsupported isolated runtime event schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true || payload.browser_control_allowed !== false || payload.replay_started !== false || payload.order_path_present !== false || payload.live_execution_allowed !== false) {
    throw new Error("isolated runtime events exceeded read-only authority");
  }
  return payload;
}

function validateIsolatedRuntimeKillEventIndex(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-runtime-kill-event-index.v1") throw new Error("unsupported runtime kill event schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true || payload.browser_control_allowed !== false || payload.starts_runtime !== false || payload.live_execution_allowed !== false) {
    throw new Error("runtime kill events exceeded stop-only authority");
  }
  return payload;
}

function validateIsolatedRuntimeCycleIndex(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-runtime-cycle-index.v1") throw new Error("unsupported runtime cycle index schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true || payload.market_source_read_only !== true || payload.paper_orders_created !== false || payload.order_path_present !== false || payload.live_execution_allowed !== false) {
    throw new Error("runtime cycle index exceeded calculation-only authority");
  }
  if (payload.latest_cycle && (payload.latest_cycle.schema_version !== "mil3.isolated-paper-runtime-cycle-view.v1" || payload.latest_cycle.read_only !== true || payload.latest_cycle.live_execution_allowed !== false)) {
    throw new Error("runtime checkpoint authority is invalid");
  }
  return payload;
}

function validateIsolatedRuntimeCycleEventIndex(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-runtime-cycle-event-index.v1") throw new Error("unsupported runtime cycle event schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true || payload.paper_orders_created !== false || payload.order_path_present !== false || payload.live_execution_allowed !== false) {
    throw new Error("runtime checkpoint events exceeded read-only authority");
  }
  return payload;
}

function validateIsolatedPaperLedgerEnvelope(payload) {
  if (payload.schema_version !== "mil3.isolated-paper-ledger-result-envelope.v1") throw new Error("unsupported paper ledger envelope schema");
  if (payload.execution_mode !== "PAPER_ONLY" || payload.read_only !== true || payload.market_source_read_only !== true || payload.paper_orders_created !== false || payload.order_path_present !== false || payload.live_execution_allowed !== false) {
    throw new Error("paper ledger envelope exceeded calculation-only authority");
  }
  const authority = payload.result?.authority;
  if (authority?.deterministic_paper_calculation !== true || authority?.market_source_read_only !== true || authority?.paper_orders_created !== false || authority?.order_path_present !== false || authority?.live_execution_allowed !== false) {
    throw new Error("paper ledger result authority is invalid");
  }
  if (payload.result?.schema_version === "mil3.isolated-paper-ledger-result.v2") {
    const fleet = payload.result.bot_fleet;
    const expectedBots = ["BUY_HOLD", "SPOT_GRID", "FUTURES_LONG_GRID", "AARS_DYNAMIC"];
    if (fleet?.schema_version !== "mil3.shadow-strategy-bot-fleet.v1" || fleet?.execution_mode !== "PAPER_ONLY" || fleet?.authority?.independent_virtual_accounts !== true || fleet?.authority?.simulated_order_intents_only !== true || fleet?.authority?.external_order_requests_created !== false || fleet?.authority?.order_path_present !== false || fleet?.authority?.live_execution_allowed !== false || JSON.stringify(fleet.bot_order) !== JSON.stringify(expectedBots)) {
      throw new Error("shadow strategy bot fleet authority is invalid");
    }
  }
  return payload;
}

function validateForwardBotOperations(payload) {
  if (payload.schema_version !== "mil3.forward-bot-operations.v1") throw new Error("unsupported forward bot operations schema");
  const authority = payload.authority;
  if (payload.execution_mode !== "PAPER_ONLY" || authority?.stored_public_market_data_only !== true || authority?.closed_candles_only !== true || authority?.read_only_view !== true || authority?.browser_control_allowed !== false || authority?.external_order_requests_created !== false || authority?.order_path_present !== false || authority?.live_execution_allowed !== false) {
    throw new Error("forward bot operations exceeded read-only PAPER_ONLY authority");
  }
  return payload;
}

function trendClass(value) {
  return Number(value) > 0 ? "positive" : Number(value) < 0 ? "negative" : "";
}

function renderSystemStatus() {
  const { payload } = state;
  const freshness = $("#freshness-status");
  freshness.textContent = payload.market.freshness_status;
  freshness.className = payload.market.freshness_status === "CURRENT" ? "positive" : "warning";
  $("#generated-at").textContent = formatDate(payload.generated_at);

  const riskStatus = $("#highest-risk-status");
  riskStatus.textContent = `${payload.highest_risk.level} · ${formatPercent(payload.highest_risk.liquidation_risk)}`;
  riskStatus.dataset.level = payload.highest_risk.level;

  const banner = $("#degraded-banner");
  banner.hidden = !payload.market.degraded;
  $("#degraded-reason").textContent = payload.market.degraded_reason || "Fresh replay data is not confirmed.";
  $("#source-line").textContent = `${payload.market.source} · ${payload.market.bars} bars · ${state.usingSample ? "DEMO FALLBACK" : "GENERATED PAYLOAD"}`;
  $("#market-context").textContent = `${payload.market.symbol} / ${payload.market.timeframe} · AS OF ${formatDate(payload.market.latest_candle_at)}`;
  $("#review-gate").textContent = payload.review_gate.disposition.replaceAll("_", " ");
}

function renderViewControls() {
  const selection = state.payload.selection || {
    symbol: state.payload.market.symbol,
    timeframe: state.payload.market.timeframe,
    replay_window: "90d",
  };
  const markets = state.payload.available_markets?.length
    ? [...new Set(state.payload.available_markets.map((item) => item.symbol))]
    : ["BTCUSDT", "ETHUSDT", "SOLUSDT"];
  const windows = state.payload.available_windows || ["30d", "90d", "180d", "365d", "all"];
  const marketSelect = $("#market-select");
  const windowSelect = $("#window-select");
  marketSelect.innerHTML = markets.map((symbol) => `<option value="${escapeHtml(symbol)}">${escapeHtml(symbol)}</option>`).join("");
  windowSelect.innerHTML = windows.map((window) => `<option value="${escapeHtml(window)}">${escapeHtml(window.toUpperCase())}</option>`).join("");
  marketSelect.value = selection.symbol;
  windowSelect.value = selection.replay_window;
  marketSelect.disabled = Boolean(state.viewingArchive);
  windowSelect.disabled = Boolean(state.viewingArchive);
  const funding = state.payload.funding;
  $("#funding-status").textContent = funding
    ? `${funding.events} EVENTS · ${funding.coverage?.status || "UNCHECKED"} · ${funding.coverage?.cadence_hours || 8}H ${funding.coverage?.cadence_source || "FALLBACK"}`
    : "FALLBACK / NOT ARCHIVED";
  const archive = state.payload.latest_stable_view_archive;
  $("#archive-provenance").textContent = state.viewingArchive
    ? `ARCHIVED EVIDENCE · ${state.viewingArchive.view_id} · created ${formatDate(state.viewingArchive.created_at)}`
    : archive
      ? `IMMUTABLE ARCHIVE · ${archive.view_id} · stored ${formatDate(archive.archived_at)}`
      : "Current generated replay; no archive identity is present in this payload.";
  $("#view-status").textContent = state.viewingArchive ? "Archived evidence view · controls locked" : "Current replay view · read-only controls";
}

function renderStrategyNav() {
  const nav = $("#strategy-nav");
  nav.replaceChildren();
  state.payload.strategies.forEach((item, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `strategy-button${item.id === state.selectedStrategy ? " active" : ""}`;
    button.dataset.strategy = item.id;
    button.setAttribute("aria-pressed", item.id === state.selectedStrategy ? "true" : "false");
    button.innerHTML = `
      <span class="strategy-number">0${index + 1}</span>
      <span>
        <span class="strategy-name">${escapeHtml(strategyLabels[item.id] || item.id)}</span>
        <span class="strategy-return ${trendClass(item.summary.total_return)}">${formatPercent(item.summary.total_return, 1, true)} RETURN</span>
      </span>`;
    button.addEventListener("click", () => selectStrategy(item.id));
    nav.append(button);
  });
}

function renderMetricStrip(summary) {
  const metrics = [
    ["TOTAL RETURN", formatPercent(summary.total_return, 1, true), trendClass(summary.total_return), "net of modeled costs"],
    ["MAX DRAWDOWN", formatPercent(summary.max_drawdown), summary.max_drawdown > 0.25 ? "warning" : "", "peak-to-trough"],
    ["SHARPE", formatNumber(summary.sharpe_approx), "", "annualized approximation"],
    ["SORTINO", formatNumber(summary.sortino), "", "downside deviation"],
    ["PROFIT FACTOR", summary.profit_factor_label ?? formatNumber(summary.profit_factor), "", "gross gain / gross loss"],
    ["MAX LEVERAGE", `${formatNumber(summary.max_effective_leverage)}×`, summary.max_effective_leverage >= 5 ? "warning" : "", "observed effective"],
  ];
  $("#metric-strip").innerHTML = metrics.map(([label, value, className, note]) => `
    <article class="metric-card">
      <span>${label}</span>
      <strong class="${className}">${value}</strong>
      <small>${note}</small>
    </article>`).join("");
}

function linePoints(values, width, height, padding, minValue, maxValue) {
  const span = Math.max(maxValue - minValue, 1e-9);
  return values.map((value, index) => {
    const x = padding + (index / Math.max(values.length - 1, 1)) * (width - padding * 2);
    const y = padding + (1 - (value - minValue) / span) * (height - padding * 2);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(" ");
}

function renderChart(strategy) {
  const trace = strategy.trace || [];
  if (!trace.length) {
    $("#trace-chart").textContent = "No replay trace is available.";
    return;
  }
  const width = 900;
  const height = 215;
  const padding = 24;
  const equityMode = state.chartMode === "equity";
  const primary = trace.map((point) => equityMode ? point.equity : point.liquidation_risk * 100);
  const secondary = trace.map((point) => equityMode ? point.drawdown * 100 : point.effective_leverage ?? 0);
  const pMin = Math.min(...primary);
  const pMax = Math.max(...primary);
  const sMin = 0;
  const sMax = Math.max(...secondary, 0.001);
  const primaryPoints = linePoints(primary, width, height, padding, pMin, pMax);
  const secondaryPoints = linePoints(secondary, width, height, padding, sMin, sMax);
  const areaPoints = `${padding},${height - padding} ${primaryPoints} ${width - padding},${height - padding}`;
  const primaryLabel = equityMode ? `$${pMax.toFixed(0)}` : `${pMax.toFixed(1)}%`;
  const primaryFloor = equityMode ? `$${pMin.toFixed(0)}` : `${pMin.toFixed(1)}%`;

  $("#trace-chart").innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
      <defs>
        <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#68e0d0" stop-opacity="0.19" />
          <stop offset="100%" stop-color="#68e0d0" stop-opacity="0" />
        </linearGradient>
      </defs>
      ${[0.2, 0.4, 0.6, 0.8].map((position) => `<line class="chart-grid" x1="${padding}" x2="${width - padding}" y1="${height * position}" y2="${height * position}" />`).join("")}
      <polygon class="chart-area" points="${areaPoints}" />
      <polyline class="chart-line-primary" points="${primaryPoints}" />
      <polyline class="chart-line-secondary" points="${secondaryPoints}" />
      <text class="chart-axis" x="${padding}" y="14">${primaryLabel}</text>
      <text class="chart-axis" x="${padding}" y="${height - 4}">${primaryFloor}</text>
      <text class="chart-axis" x="${width - padding}" y="${height - 4}" text-anchor="end">${escapeHtml(formatDate(trace.at(-1).as_of))}</text>
    </svg>`;
  $("#trace-chart").setAttribute("aria-label", equityMode
    ? `${strategyLabels[strategy.id]} equity and drawdown replay trace`
    : `${strategyLabels[strategy.id]} liquidation risk and leverage replay trace`);
  $("#chart-legend").innerHTML = equityMode
    ? '<span class="legend-key">EQUITY</span><span class="legend-key secondary">DRAWDOWN %</span>'
    : '<span class="legend-key">LIQUIDATION RISK %</span><span class="legend-key secondary">EFFECTIVE LEVERAGE ×</span>';
}

function renderComparison() {
  $("#comparison-body").innerHTML = state.payload.strategies.map((item) => {
    const summary = item.summary;
    return `<tr class="${item.id === state.selectedStrategy ? "selected" : ""}" data-strategy="${escapeHtml(item.id)}" tabindex="0">
      <td class="strategy-table-name">${escapeHtml(strategyLabels[item.id] || item.id)}</td>
      <td class="${trendClass(summary.total_return)}">${formatPercent(summary.total_return, 1, true)}</td>
      <td>${formatPercent(summary.max_drawdown)}</td>
      <td>${formatNumber(summary.sharpe_approx)}</td>
      <td>${formatNumber(summary.sortino)}</td>
      <td>${escapeHtml(summary.profit_factor_label ?? formatNumber(summary.profit_factor))}</td>
      <td class="${summary.max_effective_leverage >= 5 ? "warning" : ""}">${formatNumber(summary.max_effective_leverage)}×</td>
      <td class="${summary.max_liquidation_risk >= 0.1 ? "negative" : ""}">${formatPercent(summary.max_liquidation_risk)}</td>
    </tr>`;
  }).join("");
  $$("#comparison-body tr").forEach((row) => {
    const activate = () => selectStrategy(row.dataset.strategy);
    row.addEventListener("click", activate);
    row.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") activate();
    });
  });
}

function renderRisk() {
  const risk = state.payload.highest_risk;
  $("#risk-value").textContent = formatPercent(risk.liquidation_risk);
  $("#risk-strategy").textContent = strategyLabels[risk.strategy] || risk.strategy;
  $("#risk-margin").textContent = `Minimum margin buffer ${formatPercent(risk.min_margin_buffer_pct)} · ${risk.liquidation_events} approximation breach${risk.liquidation_events === 1 ? "" : "es"}`;
  $("#risk-dial").style.setProperty("--risk-angle", `${Math.min(300, risk.liquidation_risk * 300)}deg`);

  $("#alert-count").textContent = state.payload.alerts.length;
  $("#alert-list").innerHTML = state.payload.alerts.length
    ? state.payload.alerts.map((alert) => `
      <article class="alert-card">
        <div class="alert-head">
          <span class="severity" data-severity="${escapeHtml(alert.severity)}">${escapeHtml(alert.severity)} · ${escapeHtml(alert.id)}</span>
          <span class="alert-status">${escapeHtml(alert.status)}</span>
        </div>
        <strong>${escapeHtml(alert.object)} — ${escapeHtml(alert.trigger)}</strong>
        <p>${escapeHtml(alert.impact)}</p>
        <p class="alert-action">NEXT: ${escapeHtml(alert.recommended_action)}</p>
        <p>CLOSE WHEN: ${escapeHtml(alert.closure_condition)}</p>
      </article>`).join("")
    : '<article class="alert-card"><strong>No open risk objects.</strong><p>Continue monitoring data trust and margin buffer.</p></article>';
}

function renderLatestStableView() {
  const view = state.payload.latest_stable_view;
  const status = $("#stable-status");
  status.textContent = view.status;
  status.dataset.status = view.status;
  $("#market-state").textContent = view.state;
  $("#stable-as-of").textContent = `Confidence ${formatPercent(view.confidence)} · stable as of ${formatDate(view.as_of)}`;
  $("#recommended-exposure").textContent = `${view.recommended_exposure >= 0 ? "+" : ""}${formatNumber(view.recommended_exposure)}×`;
  $("#recommended-exposure").className = trendClass(view.recommended_exposure);
  $("#decision-reason").textContent = view.decision_reason;

  const probabilities = view.probabilities;
  $("#probability-block").innerHTML = ["bull", "base", "bear"].map((key) => `
    <div class="probability-row ${key}">
      <span>${key.toUpperCase()}</span>
      <div class="probability-track"><i style="width:${Math.max(0, Math.min(100, probabilities[key] * 100))}%"></i></div>
      <strong>${formatPercent(probabilities[key])}</strong>
    </div>`).join("");

  const list = (items) => (items?.length ? items : ["No evidence item recorded."])
    .map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  $("#evidence-list").innerHTML = list(view.evidence);
  $("#counter-evidence-list").innerHTML = list(view.counter_evidence);
}

function renderAccounting(summary) {
  const items = [
    ["REALIZED GRID P&L", formatMoney(summary.realized_grid_pnl), trendClass(summary.realized_grid_pnl)],
    ["INVENTORY UNREALIZED", formatMoney(summary.inventory_unrealized_pnl), trendClass(summary.inventory_unrealized_pnl)],
    ["FEES", formatMoney(-Math.abs(summary.fees)), "negative"],
    ["SLIPPAGE ATTRIBUTION", formatMoney(-Math.abs(summary.slippage)), "negative"],
    ["FUNDING", formatMoney(-summary.funding), trendClass(-summary.funding)],
    ["TURNOVER", `$${Number(summary.turnover_notional).toLocaleString(undefined, { maximumFractionDigits: 0 })}`, ""],
  ];
  $("#accounting-grid").innerHTML = items.map(([label, value, className]) => `
    <div class="accounting-item"><span>${label}</span><strong class="${className}">${value}</strong></div>`).join("");

  $("#parameter-list").innerHTML = Object.entries(state.payload.parameters).map(([key, value]) => `
    <dt>${escapeHtml(key.replaceAll("_", " ").toUpperCase())}</dt><dd>${escapeHtml(value)}</dd>`).join("");
}

function renderSelectedStrategy() {
  const strategy = currentStrategy();
  $("#strategy-title").textContent = strategyLabels[strategy.id] || strategy.id;
  renderMetricStrip(strategy.summary);
  renderChart(strategy);
  renderComparison();
  renderAccounting(strategy.summary);
}

function selectStrategy(id) {
  state.selectedStrategy = id;
  renderStrategyNav();
  renderSelectedStrategy();
  if (state.viewingArchive) {
    renderPortfolioUnavailable(new Error("Archived single-asset evidence selected; current portfolio aggregation is intentionally withheld."));
  } else {
    loadPortfolio().catch(renderPortfolioUnavailable);
  }
}

function render() {
  renderSystemStatus();
  renderViewControls();
  renderStrategyNav();
  renderSelectedStrategy();
  renderRisk();
  renderLatestStableView();
}

async function requestDashboard() {
  const symbol = $("#market-select").value || "SOLUSDT";
  const window = $("#window-select").value || "90d";
  const response = await fetch(`/api/v1/dashboard?symbol=${encodeURIComponent(symbol)}&interval=1h&window=${encodeURIComponent(window)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`dashboard request returned ${response.status}`);
  state.payload = validatePayload(await response.json());
  state.usingSample = false;
  state.viewingArchive = null;
  render();
  await Promise.all([
    loadArchiveOptions(),
    loadPortfolio().catch(renderPortfolioUnavailable),
    loadCurrentCadence(),
  ]);
}

async function loadArchiveOptions() {
  const select = $("#archive-select");
  const beforeSelect = $("#diff-before");
  const afterSelect = $("#diff-after");
  const symbol = state.payload.market.symbol;
  try {
    const response = await fetch(`/api/v1/stable-views?symbol=${encodeURIComponent(symbol)}&interval=${encodeURIComponent(state.payload.market.timeframe)}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`archive request returned ${response.status}`);
    const { stable_views } = await response.json();
    select.innerHTML = '<option value="">CURRENT REPLAY</option>' + stable_views.map((view) =>
      `<option value="${escapeHtml(view.view_id)}">${escapeHtml(view.replay_window.toUpperCase())} · ${escapeHtml(formatDate(view.as_of))}</option>`
    ).join("");
    select.value = state.viewingArchive?.view_id || "";
    const diffOptions = '<option value="">SELECT ARCHIVE</option>' + stable_views.map((view) =>
      `<option value="${escapeHtml(view.view_id)}">${escapeHtml(view.replay_window.toUpperCase())} · ${escapeHtml(formatDate(view.as_of))}</option>`
    ).join("");
    beforeSelect.innerHTML = diffOptions;
    afterSelect.innerHTML = diffOptions;
    if (stable_views.length >= 2) {
      beforeSelect.value = stable_views[1].view_id;
      afterSelect.value = stable_views[0].view_id;
      await loadStableDiff();
    }
  } catch (_error) {
    select.innerHTML = '<option value="">CURRENT REPLAY · ARCHIVE API UNAVAILABLE</option>';
    beforeSelect.innerHTML = '<option value="">ARCHIVE API UNAVAILABLE</option>';
    afterSelect.innerHTML = '<option value="">ARCHIVE API UNAVAILABLE</option>';
  }
}

async function loadPortfolio() {
  const window = state.payload.selection?.replay_window || "90d";
  const response = await fetch(`/api/v1/portfolio?symbols=BTCUSDT,ETHUSDT,SOLUSDT&interval=1h&window=${encodeURIComponent(window)}&strategy=${encodeURIComponent(state.selectedStrategy)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`portfolio request returned ${response.status}`);
  const payload = await response.json();
  if (payload.execution_mode !== "PAPER_ONLY") throw new Error("unsafe portfolio mode rejected");
  const summary = payload.summary;
  const status = $("#portfolio-status");
  status.textContent = summary.degraded ? "DEGRADED" : "MONITORING";
  status.dataset.status = summary.degraded ? "DEGRADED" : "STABLE";
  const metrics = [
    ["TOTAL RETURN", formatPercent(summary.total_return, 1, true)],
    ["MAX DRAWDOWN", formatPercent(summary.max_drawdown)],
    ["NET EXPOSURE", `${formatNumber(summary.final_net_exposure)}×`],
    ["GROSS EXPOSURE", `${formatNumber(summary.final_gross_exposure)}×`],
    ["EFFECTIVE LEVERAGE", `${formatNumber(summary.final_effective_leverage)}×`],
    ["MAX LIQ. RISK", formatPercent(summary.max_liquidation_risk)],
  ];
  $("#portfolio-metrics").innerHTML = metrics.map(([label, value]) =>
    `<div><span>${label}</span><strong>${value}</strong></div>`
  ).join("");
  $("#portfolio-assets").innerHTML = payload.assets.map((asset) => `
    <div class="portfolio-asset">
      <span>${escapeHtml(asset.symbol)} · ${formatPercent(asset.weight)}</span>
      <strong>${formatNumber(asset.final_net_exposure)}× NET</strong>
      <span>${escapeHtml(asset.funding_coverage_status)} · ${escapeHtml(asset.funding_cadence_hours)}H ${escapeHtml(asset.funding_cadence_source)} · ${formatPercent(asset.max_liquidation_risk)} LIQ.</span>
    </div>`).join("");
}

async function loadCurrentCadence() {
  if (state.viewingArchive) return;
  try {
    const symbol = state.payload.market.symbol;
    const response = await fetch(`/api/v1/funding-cadence?symbol=${encodeURIComponent(symbol)}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`cadence request returned ${response.status}`);
    const payload = await response.json();
    if (payload.execution_mode !== "PAPER_ONLY") throw new Error("unsafe cadence mode rejected");
    const current = payload.current;
    const replay = state.payload.funding?.coverage;
    $("#funding-status").textContent = `CURRENT ${current.interval_hours}H ${current.source_status} · REPLAY ${replay?.cadence_hours || 8}H ${replay?.cadence_source || "FALLBACK"}`;
  } catch (_error) {
    // The dashboard replay provenance remains visible when the current snapshot API is unavailable.
  }
}

function renderPortfolioUnavailable(error) {
  const status = $("#portfolio-status");
  status.textContent = "UNAVAILABLE";
  status.dataset.status = "DEGRADED";
  $("#portfolio-metrics").innerHTML = `<div><span>RECOVERY</span><strong class="warning">RUN LOCAL API</strong></div>`;
  $("#portfolio-assets").innerHTML = `<div class="portfolio-asset"><span>${escapeHtml(error.message)}</span></div>`;
}

async function loadStableDiff() {
  const before = $("#diff-before").value;
  const after = $("#diff-after").value;
  if (!before || !after) {
    $("#diff-summary").textContent = "Select two archived views from the same market.";
    $("#diff-list").replaceChildren();
    return;
  }
  const response = await fetch(`/api/v1/stable-view-diff?before=${encodeURIComponent(before)}&after=${encodeURIComponent(after)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`diff request returned ${response.status}`);
  const payload = await response.json();
  $("#diff-summary").textContent = `${payload.summary.status} · ${payload.summary.changed_fields} changed fields · ${payload.summary.material_changes} material`;
  $("#diff-list").innerHTML = payload.changes.length ? payload.changes.slice(0, 60).map((change) => `
    <div class="diff-change" data-severity="${escapeHtml(change.severity)}">
      <strong>${escapeHtml(change.severity)} · ${escapeHtml(change.path)}</strong>
      <span>${escapeHtml(change.before)} → ${escapeHtml(change.after)}</span>
    </div>`).join("") : '<div class="diff-summary">No semantic changes.</div>';
}

async function loadArchivedView(viewId) {
  if (!viewId) return requestDashboard();
  const response = await fetch(`/api/v1/stable-views/${encodeURIComponent(viewId)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`archive view returned ${response.status}`);
  const metadata = [...$("#archive-select").options].find((item) => item.value === viewId)?.textContent || "ARCHIVE";
  state.payload = validatePayload(await response.json());
  state.viewingArchive = { view_id: viewId, created_at: state.payload.generated_at, label: metadata };
  render();
  $("#archive-select").value = viewId;
  renderPortfolioUnavailable(new Error("Archived single-asset evidence selected; current portfolio aggregation is intentionally withheld."));
}

const shadowRecovery = {
  FUNDING_HISTORY_FALLBACK: "Ingest timestamped funding history before relying on futures cost evidence.",
  PARAMETER_INSTABILITY: "Keep observing; do not promote a parameter while selection continues to change.",
  TRAIN_TEST_SCORE_DECAY: "Review out-of-sample folds and reduce confidence in the training result.",
  BASELINE_UNDERPERFORMANCE: "Compare against Buy & Hold before accepting further shadow research.",
  LIQUIDATION_APPROXIMATION_BREACH: "Reduce leverage or grid inventory before the next review.",
  INSUFFICIENT_FOLDS: "Extend the stored history to create more chronological test folds.",
  NO_PARAMETER_SENSITIVITY: "Validate more than one bounded candidate before drawing a stability conclusion.",
  OVERLAPPING_TEST_WINDOWS: "Use non-overlapping test windows for independent fold evidence.",
};

function renderShadowMetrics(payload) {
  const latest = payload.points.at(-1);
  const metrics = [
    ["DAILY SNAPSHOTS", payload.snapshot_count, "immutable evidence rows"],
    ["CONSECUTIVE READY", payload.summary.consecutive_ready_snapshots, "latest uninterrupted run"],
    ["PARAMETER CHANGES", payload.summary.parameter_change_events, "daily transition events"],
    ["VALIDATION RETURN", latest ? formatPercent(latest.mean_validation_test_return, 1, true) : "—", "mean out-of-sample"],
    ["PORTFOLIO DRAWDOWN", latest ? formatPercent(latest.portfolio.max_drawdown) : "—", "latest archived replay"],
    ["LIQUIDATION RISK", latest ? formatPercent(latest.portfolio.max_liquidation_risk) : "—", "approximation only"],
  ];
  $("#shadow-metrics").innerHTML = metrics.map(([label, value, note]) => `
    <div><span>${label}</span><strong>${escapeHtml(value)}</strong><small>${note}</small></div>`).join("");
}

function renderShadowTrend(points) {
  const target = $("#shadow-trend");
  if (!points.length) {
    target.innerHTML = '<p class="shadow-empty">No archived daily evidence yet. Run the explicit PAPER_ONLY daily snapshot command.</p>';
    target.setAttribute("aria-label", "No continuous shadow evidence is archived");
    return;
  }
  const width = 900;
  const height = 220;
  const padding = 28;
  const returns = points.map((point) => Number(point.portfolio.total_return) * 100);
  const risks = points.map((point) => Number(point.portfolio.max_liquidation_risk) * 100);
  const returnMin = Math.min(...returns, 0);
  const returnMax = Math.max(...returns, 0.001);
  const riskMax = Math.max(...risks, 0.001);
  const returnPoints = linePoints(returns, width, height, padding, returnMin, returnMax);
  const riskPoints = linePoints(risks, width, height, padding, 0, riskMax);
  const circles = (values, min, max, className) => values.map((value, index) => {
    const [x, y] = linePoints(values, width, height, padding, min, max).split(" ")[index].split(",");
    return `<circle class="${className}" cx="${x}" cy="${y}" r="3" />`;
  }).join("");
  target.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" aria-hidden="true">
      ${[0.25, 0.5, 0.75].map((position) => `<line class="chart-grid" x1="${padding}" x2="${width - padding}" y1="${height * position}" y2="${height * position}" />`).join("")}
      <polyline class="chart-line-primary" points="${returnPoints}" />
      <polyline class="chart-line-secondary" points="${riskPoints}" />
      ${circles(returns, returnMin, returnMax, "shadow-point-primary")}
      ${circles(risks, 0, riskMax, "shadow-point-secondary")}
      <text class="chart-axis" x="${padding}" y="15">RETURN ${formatPercent(returnMax / 100, 1, true)}</text>
      <text class="chart-axis" x="${width - padding}" y="15" text-anchor="end">RISK ${formatPercent(riskMax / 100)}</text>
      <text class="chart-axis" x="${padding}" y="${height - 5}">${escapeHtml(formatDate(points[0].as_of))}</text>
      <text class="chart-axis" x="${width - padding}" y="${height - 5}" text-anchor="end">${escapeHtml(formatDate(points.at(-1).as_of))}</text>
    </svg>`;
  target.setAttribute("aria-label", `${points.length} archived daily snapshots; latest portfolio return ${formatPercent(points.at(-1).portfolio.total_return)} and liquidation risk ${formatPercent(points.at(-1).portfolio.max_liquidation_risk)}`);
}

function renderShadowWarnings(payload) {
  const entries = Object.entries(payload.summary.recurring_warning_counts)
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0]));
  $("#shadow-warning-count").textContent = entries.length;
  $("#shadow-warning-list").innerHTML = entries.length ? entries.map(([code, count]) => `
    <article class="shadow-warning-item">
      <div><strong>${escapeHtml(code.replaceAll("_", " "))}</strong><span>${count} / ${payload.snapshot_count} snapshots</span></div>
      <p>${escapeHtml(shadowRecovery[code] || "Review the affected fold evidence before changing the monitored strategy.")}</p>
    </article>`).join("") : '<p class="shadow-empty">No recurring validation warnings are recorded.</p>';
}

function renderShadowTimeline(payload) {
  const transitions = new Map(payload.transitions.map((item) => [item.to_snapshot_id, item]));
  const target = $("#shadow-timeline");
  if (!payload.points.length) {
    target.innerHTML = '<p class="shadow-empty">No immutable daily snapshots are available.</p>';
    return;
  }
  target.innerHTML = [...payload.points].reverse().map((point, index) => {
    const transition = transitions.get(point.snapshot_id);
    const changes = transition?.candidate_changes?.length || 0;
    const added = transition?.warnings_added?.length || 0;
    const reviewChanged = Boolean(transition?.review_transition);
    return `<button class="snapshot-row${index === 0 ? " active" : ""}" type="button" data-shadow-snapshot="${escapeHtml(point.snapshot_id)}">
      <span class="snapshot-marker" data-status="${point.review_disposition === "DEFER" ? "DEFER" : "READY"}"></span>
      <span>
        <strong>${escapeHtml(formatDate(point.as_of))}</strong>
        <small>${escapeHtml(point.review_disposition.replaceAll("_", " "))} · ${changes} parameter change${changes === 1 ? "" : "s"} · ${added} warning${added === 1 ? "" : "s"} added${reviewChanged ? " · GATE CHANGED" : ""}</small>
      </span>
      <span class="snapshot-return ${trendClass(point.portfolio.total_return)}">${formatPercent(point.portfolio.total_return, 1, true)}</span>
    </button>`;
  }).join("");
  $$('[data-shadow-snapshot]').forEach((button) => button.addEventListener("click", () => {
    $$('[data-shadow-snapshot]').forEach((item) => item.classList.toggle("active", item === button));
    loadShadowSnapshot(button.dataset.shadowSnapshot).catch(renderShadowDetailUnavailable);
  }));
}

function renderShadowStability(payload) {
  state.shadowStability = payload;
  const latest = payload.points.at(-1);
  const historyInsufficient = payload.summary.history_warnings.includes("INSUFFICIENT_DAILY_HISTORY");
  const gate = latest?.review_disposition || "DEFER";
  const gateElement = $("#shadow-review-gate");
  gateElement.textContent = gate.replaceAll("_", " ");
  gateElement.className = gate === "DEFER" ? "warning" : "positive";
  $("#shadow-as-of").textContent = latest ? formatDate(latest.as_of) : "NO SNAPSHOT";
  $("#shadow-history-trust").textContent = historyInsufficient ? `${payload.snapshot_count} / 7 · INSUFFICIENT` : `${payload.snapshot_count} SNAPSHOTS · OBSERVED`;
  $("#shadow-history-trust").className = historyInsufficient ? "warning" : "positive";
  $("#shadow-state-banner").dataset.status = gate === "DEFER" || historyInsufficient ? "DEGRADED" : "STABLE";
  $("#shadow-next-step").textContent = !latest
    ? "Run the explicit daily PAPER_ONLY archive command; this screen never creates snapshots."
    : gate === "DEFER"
      ? "Review recurring warnings and risk drift. Do not promote parameters while the gate is deferred."
      : historyInsufficient
        ? "Continue daily observation until at least seven immutable snapshots exist."
        : "Continue monitoring; READY_FOR_SHADOW_REVIEW is not live-trading authority.";
  renderShadowMetrics(payload);
  renderShadowTrend(payload.points);
  renderShadowWarnings(payload);
  renderShadowTimeline(payload);
}

const countGovernanceChecks = new Set([
  "MINIMUM_DAILY_HISTORY",
  "CONSECUTIVE_READY_REVIEWS",
  "LIQUIDATION_EVENTS",
]);

function formatGovernanceObserved(check) {
  if (check.observed === null || check.observed === undefined) return "NOT AVAILABLE";
  if (typeof check.observed === "object") {
    const entries = Object.entries(check.observed.by_code || {});
    return entries.length
      ? entries.map(([code, value]) => `${code.replaceAll("_", " ")} ${formatPercent(value)}`).join(" · ")
      : "NONE RECORDED";
  }
  if (countGovernanceChecks.has(check.id)) return String(check.observed);
  if (typeof check.observed === "number") return formatPercent(check.observed);
  return String(check.observed).replaceAll("_", " ");
}

function renderPromotionGovernance(payload) {
  state.promotionGovernance = payload;
  const disposition = payload.decision.disposition;
  const card = $(".promotion-card");
  card.dataset.status = disposition;
  $("#promotion-disposition").textContent = disposition.replaceAll("_", " ");
  $("#promotion-next-review").textContent = payload.decision.next_review_condition;
  const passes = payload.checks.filter((item) => item.status === "PASS").length;
  const blocks = payload.decision.blocking_checks.length;
  const rejects = payload.decision.rejection_checks.length;
  $("#promotion-summary").innerHTML = [
    ["EVIDENCE WINDOW", `${payload.evidence_window.evaluated_snapshots} / ${payload.evidence_window.available_snapshots}`, "evaluated / available"],
    ["PASSING CHECKS", `${passes} / ${payload.checks.length}`, "all required for candidacy"],
    ["BLOCKING CHECKS", blocks, "continue observation"],
    ["REJECTION CHECKS", rejects, "material adverse evidence"],
  ].map(([label, value, note]) => `<div><span>${label}</span><strong>${escapeHtml(value)}</strong><small>${note}</small></div>`).join("");

  const order = { REJECT: 0, BLOCK: 1, PASS: 2 };
  $("#promotion-checks").innerHTML = [...payload.checks]
    .sort((left, right) => order[left.status] - order[right.status])
    .map((check) => `<article class="promotion-check" data-status="${escapeHtml(check.status)}">
      <div class="promotion-check-head">
        <span>${escapeHtml(check.status)}</span>
        <strong>${escapeHtml(check.label)}</strong>
      </div>
      <p class="promotion-observed">OBSERVED ${escapeHtml(formatGovernanceObserved(check))} · REQUIRED ${escapeHtml(check.requirement)}</p>
      <p>${escapeHtml(check.impact)}</p>
      ${check.status === "PASS" ? "" : `<p class="promotion-recovery">CLEAR WHEN: ${escapeHtml(check.recovery_condition)}</p>`}
    </article>`).join("");

  $("#promotion-policy-list").innerHTML = Object.entries(payload.policy).map(([key, value]) => `
    <dt>${escapeHtml(key.replaceAll("_", " ").toUpperCase())}</dt><dd>${escapeHtml(value)}</dd>`).join("");
}

function renderPromotionUnavailable(error) {
  state.promotionGovernance = null;
  $(".promotion-card").dataset.status = "CONTINUE_OBSERVATION";
  $("#promotion-disposition").textContent = "GOVERNANCE UNAVAILABLE · CONTINUE OBSERVATION";
  $("#promotion-next-review").textContent = "Restore the read-only governance endpoint. No strategy change is permitted while evidence is unavailable.";
  $("#promotion-summary").innerHTML = '<div><span>RECOVERY</span><strong class="warning">READ-ONLY API REQUIRED</strong><small>existing shadow evidence is unchanged</small></div>';
  $("#promotion-checks").innerHTML = `<p class="shadow-empty">${escapeHtml(error.message)}</p>`;
  $("#promotion-policy-list").replaceChildren();
}

async function loadPromotionGovernance(strategy) {
  const response = await fetch(`/api/v1/promotion-governance?limit=90&strategy=${encodeURIComponent(strategy)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`promotion governance returned ${response.status}`);
  renderPromotionGovernance(validatePromotionGovernance(await response.json()));
}

function formatProposalParameter(name, value) {
  if (name === "tactical_hedge") return value ? "ON" : "OFF";
  if (name === "grid_spacing_pct") return formatPercent(value, 2);
  if (name === "aars_max_abs_exposure" || name === "futures_leverage") return `${formatNumber(value, 2)}×`;
  return String(value);
}

function renderPaperProposal(envelope) {
  state.paperProposal = envelope;
  const proposal = envelope.proposal;
  const review = envelope.review;
  const risk = proposal.expected_risk_impact;
  const status = envelope.status;
  const card = $(".paper-proposal-card");
  card.dataset.status = status;
  $("#paper-proposal-status").textContent = status.replaceAll("_", " ");
  $("#paper-proposal-id").textContent = envelope.proposal_id;
  $("#paper-proposal-summary").innerHTML = [
    ["TARGET", proposal.target_strategy.replaceAll("_", " "), "paper strategy only"],
    ["SELECTED CANDIDATE", proposal.selection.selected_candidate_id, `${proposal.selection.selection_count} / ${proposal.selection.asset_count} latest asset selections`],
    ["PARAMETER CHANGES", proposal.parameter_changes.length, "none have been applied"],
    ["EVIDENCE AS OF", formatDate(proposal.source_evidence.shadow_as_of), "immutable shadow snapshot"],
  ].map(([label, value, note]) => `<div><span>${label}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></div>`).join("");
  $("#paper-proposal-changes").innerHTML = proposal.parameter_changes.map((change) => `
    <article>
      <span>${escapeHtml(change.parameter.replaceAll("_", " ").toUpperCase())}</span>
      <div><strong>${escapeHtml(formatProposalParameter(change.parameter, change.before))}</strong><i aria-hidden="true">→</i><strong>${escapeHtml(formatProposalParameter(change.parameter, change.after))}</strong></div>
      <small>RELATIVE DELTA ${change.relative_delta === null ? "NOT APPLICABLE" : escapeHtml(formatPercent(change.relative_delta, 1, true))}</small>
    </article>`).join("");
  $("#paper-proposal-risk").innerHTML = `
    <div class="paper-risk-grid">
      <div><span>EXCESS RETURN VS BUY & HOLD</span><strong class="${trendClass(risk.observed_mean_excess_return_vs_buy_hold)}">${formatPercent(risk.observed_mean_excess_return_vs_buy_hold, 1, true)}</strong></div>
      <div><span>MAX OBSERVED DRAWDOWN</span><strong>${formatPercent(risk.observed_max_portfolio_drawdown)}</strong></div>
      <div><span>MAX LIQUIDATION RISK</span><strong>${formatPercent(risk.observed_max_liquidation_risk)}</strong></div>
      <div><span>LIQUIDATION BREACHES</span><strong>${escapeHtml(risk.observed_liquidation_events)}</strong></div>
    </div>
    <p><strong>${escapeHtml(risk.assessment.replaceAll("_", " "))}:</strong> ${escapeHtml(risk.statement)}</p>
    <p class="paper-stop-condition"><strong>STOP CONDITION:</strong> ${escapeHtml(proposal.review_instructions.rollback_condition)}</p>`;
  $("#paper-proposal-review").innerHTML = review
    ? `<strong>${escapeHtml(review.disposition.replaceAll("_", " "))}</strong>
       <dl><dt>REVIEWER</dt><dd>${escapeHtml(review.reviewer)}</dd><dt>RECORDED</dt><dd>${escapeHtml(formatDate(review.reviewed_at))}</dd></dl>
       <p>${escapeHtml(review.note)}</p>
       <small>THIS RECORD DID NOT APPLY PARAMETERS.</small>`
    : `<strong>PENDING HUMAN REVIEW</strong>
       <p>No terminal human record is archived. Review must be recorded through the explicit local PAPER_ONLY command.</p>
       <small>THIS SCREEN HAS NO APPROVE OR APPLY CONTROL.</small>`;
  $("#paper-proposal-source").textContent = `SOURCE SNAPSHOT ${proposal.source_evidence.shadow_snapshot_id} · GOVERNANCE ${formatDate(proposal.source_evidence.governance_generated_at)} · ${proposal.selection.policy}`;
}

function renderPaperProposalUnavailable(error, empty = false) {
  state.paperProposal = null;
  $(".paper-proposal-card").dataset.status = empty ? "NO_PROPOSAL" : "UNAVAILABLE";
  $("#paper-proposal-status").textContent = empty ? "NO ARCHIVED PROPOSAL" : "ARCHIVE UNAVAILABLE";
  $("#paper-proposal-id").textContent = "NO PROPOSAL SELECTED";
  $("#paper-proposal-summary").innerHTML = `<div><span>SAFE STATE</span><strong class="warning">NO CHANGE PERMITTED</strong><small>${empty ? "create only after promotion candidacy" : "restore read-only local API"}</small></div>`;
  $("#paper-proposal-changes").innerHTML = '<p class="shadow-empty">No before/after parameter packet is available.</p>';
  $("#paper-proposal-risk").innerHTML = '<p class="shadow-empty">Risk evidence remains unforecast and no paper parameter has been applied.</p>';
  $("#paper-proposal-review").innerHTML = '<strong>PENDING HUMAN REVIEW</strong><p>No review can be inferred without an immutable proposal.</p>';
  $("#paper-proposal-source").textContent = error.message;
}

async function loadPaperProposals(strategy) {
  const response = await fetch(`/api/v1/paper-proposals?limit=30&strategy=${encodeURIComponent(strategy)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`paper proposal index returned ${response.status}`);
  const index = validatePaperProposalIndex(await response.json());
  const latest = index.proposals[0];
  if (!latest) {
    renderPaperProposalUnavailable(new Error("Archive a proposal locally only after MIL-3.14 reports PROMOTION CANDIDATE."), true);
    return;
  }
  const detailResponse = await fetch(`/api/v1/paper-proposals/${encodeURIComponent(latest.proposal_id)}`, { cache: "no-store" });
  if (!detailResponse.ok) throw new Error(`paper proposal detail returned ${detailResponse.status}`);
  renderPaperProposal(validatePaperProposalEnvelope(await detailResponse.json()));
}

const trialPercentMetrics = new Set([
  "mean_total_return",
  "worst_max_drawdown",
  "max_liquidation_risk",
  "min_margin_buffer_pct",
]);

function formatTrialMetric(name, value, signed = false) {
  if (value === null || value === undefined) return "NOT FINITE";
  if (trialPercentMetrics.has(name)) return formatPercent(value, 1, signed);
  if (name === "liquidation_events") return String(value);
  return formatNumber(value, 2);
}

function renderPaperTrial(envelope) {
  state.paperTrial = envelope;
  const trial = envelope.trial;
  const baseline = trial.results.baseline;
  const proposed = trial.results.proposed;
  const delta = trial.results.delta_proposed_minus_baseline;
  const disposition = trial.review_gate.disposition;
  const card = $(".paper-trial-card");
  card.dataset.status = disposition;
  $("#paper-trial-status").textContent = disposition.replaceAll("_", " ");
  $("#paper-trial-id").textContent = envelope.trial_id;
  $("#paper-trial-summary").innerHTML = [
    ["TARGET", trial.target_strategy.replaceAll("_", " "), "isolated paper replay"],
    ["ASSETS", trial.configuration.symbols.length, trial.configuration.symbols.join(" · ")],
    ["WINDOW", trial.configuration.replay_window.toUpperCase(), `${trial.configuration.timeframe} · ${trial.configuration.warmup_bars} warmup bars`],
    ["COMPLETED", formatDate(trial.generated_at), "immutable result"],
  ].map(([label, value, note]) => `<div><span>${label}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></div>`).join("");

  const comparisonMetrics = [
    ["mean_total_return", "MEAN TOTAL RETURN"],
    ["worst_max_drawdown", "WORST MAX DRAWDOWN"],
    ["mean_sharpe_approx", "MEAN SHARPE"],
    ["mean_sortino", "MEAN SORTINO"],
    ["max_liquidation_risk", "MAX LIQUIDATION RISK"],
    ["max_effective_leverage", "MAX EFFECTIVE LEVERAGE"],
  ];
  $("#paper-trial-comparison").innerHTML = `<div class="trial-compare-head"><span>METRIC</span><span>BASELINE</span><span>PROPOSED</span><span>DELTA</span></div>${comparisonMetrics.map(([key, label]) => `
    <div class="trial-compare-row">
      <span>${label}</span>
      <strong>${formatTrialMetric(key, baseline[key])}</strong>
      <strong>${formatTrialMetric(key, proposed[key])}</strong>
      <strong class="${trendClass(key.includes("drawdown") || key.includes("liquidation") || key.includes("leverage") ? -delta[key] : delta[key])}">${formatTrialMetric(key, delta[key], true)}</strong>
    </div>`).join("")}`;

  const costs = [
    ["turnover_notional", "TURNOVER", formatMoney],
    ["fees", "FEES", formatMoney],
    ["slippage", "SLIPPAGE", formatMoney],
    ["funding", "FUNDING", formatMoney],
    ["realized_pnl", "REALIZED P&L", formatMoney],
    ["realized_grid_pnl", "GRID P&L", formatMoney],
    ["inventory_unrealized_pnl", "INVENTORY UNREALIZED", formatMoney],
  ];
  $("#paper-trial-costs").innerHTML = costs.map(([key, label, formatter]) => `
    <div><span>${label}</span><strong>${formatter(proposed[key])}</strong><small>Δ ${formatter(delta[key])}</small></div>`).join("");

  const stop = trial.stop_condition;
  $("#paper-trial-stop").innerHTML = `
    <strong>${stop.triggered ? "STOP TRIGGERED" : "NO STOP TRIGGERED"}</strong>
    <dl>
      <dt>MAX DRAWDOWN LIMIT</dt><dd>${formatPercent(stop.max_drawdown)}</dd>
      <dt>MAX LIQUIDATION RISK</dt><dd>${formatPercent(stop.max_liquidation_risk)}</dd>
      <dt>LIQUIDATION EVENTS ALLOWED</dt><dd>${escapeHtml(stop.liquidation_events_allowed)}</dd>
    </dl>
    <p>${stop.reasons.length ? escapeHtml(stop.reasons.join(" · ").replaceAll("_", " ")) : "All archived stop checks remained within the configured paper limits."}</p>
    <small>NO RESULT APPLIES A CONFIGURATION.</small>`;

  $("#paper-trial-assets").innerHTML = trial.results.per_asset.map((asset) => `
    <article>
      <span>${escapeHtml(asset.symbol)} · ${escapeHtml(asset.bars)} BARS · ${escapeHtml(asset.funding_events)} FUNDING EVENTS · ${escapeHtml(asset.funding_coverage.status)} @ ${escapeHtml(asset.funding_coverage.cadence_hours)}H ${escapeHtml(asset.funding_coverage.cadence_source)}</span>
      <strong>${formatPercent(asset.proposed.total_return, 1, true)} <small>PROPOSED RETURN</small></strong>
      <dl>
        <dt>BASELINE RETURN</dt><dd>${formatPercent(asset.baseline.total_return, 1, true)}</dd>
        <dt>PROPOSED DRAWDOWN</dt><dd>${formatPercent(asset.proposed.max_drawdown)}</dd>
        <dt>PROPOSED LIQUIDATION RISK</dt><dd>${formatPercent(asset.proposed.max_liquidation_risk)}</dd>
      </dl>
      <code>${escapeHtml(asset.input_sha256.slice(0, 16))}…</code>
    </article>`).join("");
  $("#paper-trial-source").textContent = `PROPOSAL ${trial.proposal_id} · SOURCE SNAPSHOT ${trial.source_snapshot_id} · INPUT SHA256 ${trial.input_evidence.combined_sha256} · ${trial.input_evidence.reproducibility_scope}`;
}

function renderPaperTrialUnavailable(error, empty = false) {
  state.paperTrial = null;
  $(".paper-trial-card").dataset.status = empty ? "NO_TRIAL" : "UNAVAILABLE";
  $("#paper-trial-status").textContent = empty ? "NO ARCHIVED TRIAL" : "TRIAL ARCHIVE UNAVAILABLE";
  $("#paper-trial-id").textContent = "NO TRIAL SELECTED";
  $("#paper-trial-summary").innerHTML = `<div><span>SAFE STATE</span><strong class="warning">NO CONFIGURATION APPLIED</strong><small>${empty ? "trial requires an acknowledged proposal" : "restore read-only local API"}</small></div>`;
  $("#paper-trial-comparison").innerHTML = '<p class="shadow-empty">No same-window baseline/proposed evidence is available.</p>';
  $("#paper-trial-costs").innerHTML = '<p class="shadow-empty">No common-ledger cost delta is available.</p>';
  $("#paper-trial-stop").innerHTML = '<strong>TRIAL NOT VERIFIED</strong><p>No stop result is inferred without immutable evidence.</p><small>NO RESULT APPLIES A CONFIGURATION.</small>';
  $("#paper-trial-assets").replaceChildren();
  $("#paper-trial-source").textContent = error.message;
}

async function loadPaperTrials(strategy) {
  const response = await fetch(`/api/v1/paper-trials?limit=30&strategy=${encodeURIComponent(strategy)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`paper trial index returned ${response.status}`);
  const index = validatePaperTrialIndex(await response.json());
  const latest = index.trials[0];
  if (!latest) {
    renderPaperTrialUnavailable(new Error("Run an isolated local trial only after the proposal is acknowledged for PAPER_ONLY evaluation."), true);
    return;
  }
  const detailResponse = await fetch(`/api/v1/paper-trials/${encodeURIComponent(latest.trial_id)}`, { cache: "no-store" });
  if (!detailResponse.ok) throw new Error(`paper trial detail returned ${detailResponse.status}`);
  renderPaperTrial(validatePaperTrialEnvelope(await detailResponse.json()));
}

function renderForwardObservation(envelope) {
  state.forwardObservation = envelope;
  const observation = envelope.observation;
  const baseline = observation.results.baseline;
  const proposed = observation.results.proposed;
  const delta = observation.results.delta_proposed_minus_baseline;
  const disposition = observation.review_gate.disposition;
  const card = $(".forward-observation-card");
  card.dataset.status = disposition;
  $("#forward-observation-status").textContent = disposition.replaceAll("_", " ");
  $("#forward-observation-id").textContent = envelope.observation_id;
  $("#forward-observation-summary").innerHTML = [
    ["FORWARD BARS", observation.results.forward_bars, `${observation.review_gate.confirmation_bars_required} required for confirmation`],
    ["OBSERVED THROUGH", formatDate(observation.boundary.synchronized_forward_end), "common multi-asset boundary"],
    ["PROPOSED RETURN", formatPercent(proposed.mean_total_return, 1, true), `Δ ${formatPercent(delta.mean_total_return, 1, true)}`],
    ["MAX LIQUIDATION RISK", formatPercent(proposed.max_liquidation_risk), observation.stop_condition.triggered ? "stop triggered" : "within paper stop"],
  ].map(([label, value, note]) => `<div><span>${label}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></div>`).join("");

  const metrics = [
    ["mean_total_return", "MEAN TOTAL RETURN"],
    ["worst_max_drawdown", "WORST MAX DRAWDOWN"],
    ["mean_sharpe_approx", "MEAN SHARPE"],
    ["mean_sortino", "MEAN SORTINO"],
    ["max_liquidation_risk", "MAX LIQUIDATION RISK"],
  ];
  $("#forward-observation-comparison").innerHTML = `<div class="trial-compare-head"><span>METRIC</span><span>BASELINE</span><span>PROPOSED</span><span>DELTA</span></div>${metrics.map(([key, label]) => `
    <div class="trial-compare-row"><span>${label}</span><strong>${formatTrialMetric(key, baseline[key])}</strong><strong>${formatTrialMetric(key, proposed[key])}</strong><strong class="${trendClass(key.includes("drawdown") || key.includes("liquidation") ? -delta[key] : delta[key])}">${formatTrialMetric(key, delta[key], true)}</strong></div>`).join("")}`;

  const anchors = Object.entries(observation.boundary.trial_evidence_end_per_asset);
  $("#forward-observation-boundary").innerHTML = `
    <strong>NO HISTORICAL PERFORMANCE REUSED</strong>
    <p>Warmup context supports indicators only. Returns, costs, funding and risk begin on the first candle strictly after each archived trial boundary.</p>
    <dl>${anchors.map(([symbol, end]) => `<dt>${escapeHtml(symbol)} TRIAL END</dt><dd>${escapeHtml(formatDate(end))}</dd>`).join("")}</dl>`;
  const lineage = observation.lineage;
  $("#forward-observation-lineage").innerHTML = `
    <strong>${lineage.previous_observation_id ? "CHAINED CHECKPOINT" : "GENESIS CHECKPOINT"}</strong>
    <dl><dt>PREVIOUS ID</dt><dd>${escapeHtml(lineage.previous_observation_id || "NONE")}</dd><dt>PREVIOUS INPUT</dt><dd>${escapeHtml(lineage.previous_input_sha256 ? `${lineage.previous_input_sha256.slice(0, 16)}…` : "NONE")}</dd></dl>
    <p>Archived checkpoints cannot move backward or overwrite different evidence at the same endpoint.</p>`;
  $("#forward-observation-assets").innerHTML = observation.results.per_asset.map((asset) => `
    <article><span>${escapeHtml(asset.symbol)} · ${escapeHtml(asset.forward_bars)} FORWARD BARS · ${escapeHtml(asset.funding_coverage.status)} FUNDING</span><strong>${formatPercent(asset.proposed.total_return, 1, true)} <small>PROPOSED RETURN</small></strong><dl><dt>FORWARD START</dt><dd>${escapeHtml(formatDate(asset.forward_start))}</dd><dt>BASELINE RETURN</dt><dd>${formatPercent(asset.baseline.total_return, 1, true)}</dd><dt>PROPOSED DRAWDOWN</dt><dd>${formatPercent(asset.proposed.max_drawdown)}</dd></dl><code>${escapeHtml(asset.input_sha256.slice(0, 16))}…</code></article>`).join("");
  $("#forward-observation-source").textContent = `TRIAL ${observation.trial_id} · INPUT SHA256 ${observation.input_evidence.combined_sha256} · FORWARD-ONLY · NO RESULT APPLIES A CONFIGURATION`;
}

function renderForwardStability(payload) {
  state.forwardStability = payload;
  const summary = payload.summary;
  const policy = payload.policy;
  const disposition = payload.review_gate.disposition;
  $("#forward-stability-status").textContent = disposition.replaceAll("_", " ");
  $("#forward-stability-status").dataset.status = disposition;
  $("#forward-stability-progress").innerHTML = [
    ["MEASURED HORIZON", `${summary.latest_forward_bars} / ${policy.minimum_forward_bars} BARS`, summary.latest_forward_bars >= policy.minimum_forward_bars ? "HORIZON MET" : "ACCUMULATING"],
    ["QUALIFYING STREAK", `${summary.consecutive_qualifying_checkpoints} / ${policy.minimum_consecutive_qualifying}`, summary.consecutive_qualifying_checkpoints >= policy.minimum_consecutive_qualifying ? "STREAK MET" : "NOT YET PERSISTENT"],
    ["CURRENT SCORE Δ", formatNumber(summary.current_score_delta, 3), `BEST ${formatNumber(summary.best_score_delta, 3)}`],
    ["CURRENT RETURN Δ", formatPercent(summary.current_return_delta, 1, true), `${summary.evaluated_checkpoints} / ${summary.available_checkpoints} CHECKPOINTS EVALUATED`],
    ["LIQUIDATION RISK", formatPercent(summary.current_liquidation_risk), summary.warning_codes.includes("LIQUIDATION_RISK_RISING") ? "RISING" : "NO RISING-RISK ALARM"],
  ].map(([label, value, note]) => `<div><span>${label}</span><strong>${escapeHtml(value)}</strong><small>${escapeHtml(note)}</small></div>`).join("");

  $("#forward-stability-trace").innerHTML = payload.points.length ? payload.points.map((point) => `
    <article data-qualified="${point.forward_bars >= policy.minimum_forward_bars && point.score_delta >= 0 && point.return_delta >= 0 && !point.stop_triggered}">
      <span>${escapeHtml(formatDate(point.observed_through))}</span>
      <strong>${formatNumber(point.score_delta, 3)} <small>SCORE Δ</small></strong>
      <em>${formatPercent(point.return_delta, 1, true)} RETURN Δ · ${formatPercent(point.proposed_max_liquidation_risk)} LIQ RISK</em>
    </article>`).join("") : '<p class="shadow-empty">No checkpoint trace is available.</p>';

  $("#forward-stability-alarms").innerHTML = payload.alarms.length ? payload.alarms.map((alarm) => `
    <article data-severity="${escapeHtml(alarm.severity)}">
      <div><strong>${escapeHtml(alarm.severity)} · ${escapeHtml(alarm.code.replaceAll("_", " "))}</strong><span>${escapeHtml(alarm.object)}</span></div>
      <dl><dt>TRIGGER</dt><dd>${escapeHtml(alarm.trigger)}</dd><dt>IMPACT</dt><dd>${escapeHtml(alarm.impact)}</dd><dt>RECOMMENDED</dt><dd>${escapeHtml(alarm.recommended_action)}</dd><dt>CLOSE WHEN</dt><dd>${escapeHtml(alarm.closure_condition)}</dd></dl>
    </article>`).join("") : '<p class="forward-clear">NO ACTIVE DECAY OR CONTINUITY ALARMS</p>';
  $("#forward-stability-next").textContent = `${payload.review_gate.next_review_condition} Automatic strategy change and live execution remain disallowed.`;
}

function renderForwardStabilityUnavailable(error) {
  state.forwardStability = null;
  $("#forward-stability-status").textContent = "STABILITY UNAVAILABLE";
  $("#forward-stability-status").dataset.status = "UNAVAILABLE";
  $("#forward-stability-progress").innerHTML = '<div><span>SAFE STATE</span><strong class="warning">NO PERSISTENCE CLAIM</strong><small>read-only evidence unavailable</small></div>';
  $("#forward-stability-trace").innerHTML = '<p class="shadow-empty">No checkpoint trend is inferred.</p>';
  $("#forward-stability-alarms").innerHTML = `<p class="shadow-empty">${escapeHtml(error.message)}</p>`;
  $("#forward-stability-next").textContent = "Restore the read-only stability endpoint; keep baseline and do not apply parameters.";
}

function renderForwardLifecycle(lifecycle, latestReviewEnvelope, manifest) {
  state.forwardLifecycle = lifecycle;
  const current = lifecycle.current_state;
  $("#forward-lifecycle-status").textContent = current.replaceAll("_", " ");
  $("#forward-lifecycle-status").dataset.status = current;
  const observationConfirmed = state.forwardStability?.review_gate?.disposition === "EXTENDED_OBSERVATION_CONFIRMED";
  const actionMap = {
    OBSERVING: [observationConfirmed ? "ACKNOWLEDGE, PAUSE OR TERMINATE" : "PAUSE OR TERMINATE", "Acknowledgement is additionally allowed only after extended observation is confirmed."],
    OBSERVING_ACKNOWLEDGED: ["PAUSE OR TERMINATE", "Acknowledgement remains paper-only and applies no parameters."],
    PAUSED: ["RESTART OR TERMINATE", "Restart requires current non-stopped, non-deferred stability evidence."],
    TERMINATED: ["NO FURTHER TRANSITION", "Termination is irreversible; begin a new governed proposal and trial lifecycle."],
  };
  const [available, condition] = actionMap[current] || ["NO ACTION INFERRED", "Restore valid lifecycle evidence."];
  const latestReview = latestReviewEnvelope?.review;
  $("#forward-lifecycle-current").innerHTML = `
    <strong>${escapeHtml(current.replaceAll("_", " "))}</strong>
    <dl><dt>AVAILABLE HUMAN ACTION</dt><dd>${escapeHtml(available)}</dd><dt>WRITE PATH</dt><dd>run_forward_review.py</dd><dt>LATEST REVIEWER</dt><dd>${escapeHtml(latestReview?.reviewer || "NONE")}</dd><dt>LATEST REVIEW TIME</dt><dd>${escapeHtml(latestReview ? formatDate(latestReview.reviewed_at) : "NONE")}</dd></dl>
    <p>${escapeHtml(condition)}</p>
    <small>THIS READ-ONLY SCREEN HAS NO REVIEW OR APPLY BUTTON.</small>`;
  $("#forward-review-history").innerHTML = lifecycle.reviews.length ? lifecycle.reviews.map((review) => `
    <article><span>${escapeHtml(formatDate(review.reviewed_at))} · ${escapeHtml(review.reviewer)}</span><strong>${escapeHtml(review.action.replaceAll("_", " "))}</strong><small>${escapeHtml(review.resulting_state.replaceAll("_", " "))} · ${escapeHtml(review.review_id)}</small></article>`).join("") : '<p class="shadow-empty">No human lifecycle review has been archived.</p>';
  $("#forward-evidence-manifest").innerHTML = `
    <strong>SHA-256 MANIFEST READY</strong>
    <dl><dt>OBSERVATIONS</dt><dd>${escapeHtml(manifest.manifest.observation_count)}</dd><dt>HUMAN REVIEWS</dt><dd>${escapeHtml(manifest.manifest.review_count)}</dd><dt>LIFECYCLE STATE</dt><dd>${escapeHtml(manifest.lifecycle_state)}</dd><dt>COMBINED HASH</dt><dd><code>${escapeHtml(manifest.manifest.combined_sha256.slice(0, 20))}…</code></dd></dl>
    <p>Full export is available only through run_forward_evidence_export.py. Existing files are never overwritten.</p>`;
  $("#forward-lifecycle-recovery").textContent = current === "TERMINATED"
    ? "Candidate terminated. Preserve the evidence bundle and start a new governed proposal/trial if research resumes."
    : "Human actions require the explicit local CLI, reviewer identity and note. No review applies parameters or authorizes live execution.";
}

function renderForwardLifecycleUnavailable(error) {
  state.forwardLifecycle = null;
  $("#forward-lifecycle-status").textContent = "LIFECYCLE UNAVAILABLE";
  $("#forward-lifecycle-status").dataset.status = "UNAVAILABLE";
  $("#forward-lifecycle-current").innerHTML = '<strong class="warning">NO HUMAN ACTION PERMITTED</strong><p>Current lifecycle state could not be verified.</p>';
  $("#forward-review-history").innerHTML = '<p class="shadow-empty">No review history is inferred.</p>';
  $("#forward-evidence-manifest").innerHTML = `<p class="shadow-empty">${escapeHtml(error.message)}</p>`;
  $("#forward-lifecycle-recovery").textContent = "Restore lifecycle and manifest evidence before any local human review command.";
}

function renderIsolatedActivation(lifecycle, policy, latestReviewEnvelope) {
  state.isolatedActivation = lifecycle;
  const current = lifecycle.current_state;
  const latest = latestReviewEnvelope?.review;
  $("#activation-approval-status").textContent = current.replaceAll("_", " ");
  $("#activation-approval-status").dataset.status = current;
  const stability = state.forwardStability;
  const forward = state.forwardLifecycle;
  const requirements = [
    ["OFFLINE BUNDLE VERIFICATION", latest ? "VERIFIED RECEIPT ARCHIVED" : "REQUIRED BEFORE REVIEW", Boolean(latest)],
    ["FORWARD STABILITY", stability?.review_gate?.disposition || "UNAVAILABLE", stability?.review_gate?.disposition === "EXTENDED_OBSERVATION_CONFIRMED"],
    ["HUMAN FORWARD STATE", forward?.current_state || "UNAVAILABLE", forward?.current_state === "OBSERVING_ACKNOWLEDGED"],
    ["ACTIVE WARNING CODES", stability?.summary?.warning_codes?.length ? stability.summary.warning_codes.join(", ") : "NONE", Boolean(stability) && stability.summary.warning_codes.length === 0],
  ];
  $("#activation-prerequisites").innerHTML = requirements.map(([label, value, passed]) => `
    <article data-status="${passed ? "PASS" : "BLOCK"}"><span>${escapeHtml(label)}</span><strong>${passed ? "PASS" : "BLOCK"}</strong><small>${escapeHtml(value)}</small></article>`).join("");
  $("#evidence-retention-policy").innerHTML = `
    <strong>${escapeHtml(policy.retention_days)} DAYS · ${escapeHtml(policy.minimum_verified_copies)} VERIFIED COPIES</strong>
    <dl><dt>VERIFY</dt><dd>run_forward_evidence_verify.py</dd><dt>BACK UP</dt><dd>run_forward_evidence_retain.py</dd><dt>PRUNE SCOPE</dt><dd>${escapeHtml(policy.prune_scope.replaceAll("_", " "))}</dd><dt>DATABASE ACCESS</dt><dd>NONE</dd></dl>
    <p>Unknown files and the minimum verified-copy floor are preserved.</p>`;
  $("#activation-review-history").innerHTML = lifecycle.events.length ? lifecycle.events.map((event) => `
    <article><span>${escapeHtml(formatDate(event.reviewed_at))} · ${escapeHtml(event.reviewer)}</span><strong>${escapeHtml(event.action.replaceAll("_", " "))}</strong><small>${escapeHtml(event.resulting_state)} · ${escapeHtml(event.sandbox_id)} · ${escapeHtml(event.review_id)}</small></article>`).join("") : '<p class="shadow-empty">No isolated activation decision has been archived.</p>';
  const expiry = latest?.valid_until ? ` Authorization expires ${formatDate(latest.valid_until)}.` : "";
  const recovery = {
    PENDING_HUMAN_APPROVAL: "Verify and retain the complete bundle offline, then use the explicit local review CLI. Approval remains blocked until every prerequisite passes.",
    APPROVED: `Limited sandbox authority exists; no configuration has been applied.${expiry}`,
    REJECTED: "Decision is terminal for this evidence bundle. Preserve evidence and start a new governed trial for reconsideration.",
    REVOKED: "Sandbox authority was withdrawn. No configuration change or execution is permitted.",
    EXPIRED: "Approval expired without applying configuration. A new evidence lifecycle is required.",
  };
  $("#activation-approval-recovery").textContent = `${recovery[current] || "Restore valid isolated approval evidence."} THIS SCREEN HAS NO APPROVE OR ACTIVATE BUTTON.`;
}

function renderIsolatedActivationUnavailable(error) {
  state.isolatedActivation = null;
  $("#activation-approval-status").textContent = "APPROVAL UNAVAILABLE";
  $("#activation-approval-status").dataset.status = "UNAVAILABLE";
  $("#activation-prerequisites").innerHTML = '<article data-status="BLOCK"><span>SAFE STATE</span><strong>BLOCK</strong><small>NO SANDBOX AUTHORITY INFERRED</small></article>';
  $("#evidence-retention-policy").innerHTML = `<p class="shadow-empty">${escapeHtml(error.message)}</p>`;
  $("#activation-review-history").innerHTML = '<p class="shadow-empty">No approval history is inferred.</p>';
  $("#activation-approval-recovery").textContent = "Restore policy, lifecycle and review evidence before any local approval command.";
}

function renderIsolatedRegistry(configurationIndex, sandbox, eventIndex) {
  state.isolatedSandbox = sandbox;
  const current = sandbox.effective_state;
  $("#sandbox-effective-status").textContent = current.replaceAll("_", " ");
  $("#sandbox-effective-status").dataset.status = current;
  $("#sandbox-pointer-summary").innerHTML = `
    <strong>${escapeHtml(current.replaceAll("_", " "))}</strong>
    <dl><dt>STORED POINTER</dt><dd>${escapeHtml(sandbox.stored_configuration_id || "EMPTY")}</dd><dt>EFFECTIVE CONFIG</dt><dd>${escapeHtml(sandbox.effective_configuration_id || "NONE")}</dd><dt>STATE VERSION</dt><dd>${escapeHtml(sandbox.state_version)}</dd><dt>EVALUATED</dt><dd>${escapeHtml(formatDate(sandbox.evaluated_at))}</dd></dl>
    <p>${escapeHtml(sandbox.blocking_reason)}</p>`;
  const config = sandbox.stored_configuration;
  $("#sandbox-configuration-detail").innerHTML = config ? `
    <strong>${escapeHtml(config.target_strategy)} · ${escapeHtml(config.configuration_id)}</strong>
    <dl><dt>SANDBOX</dt><dd>${escapeHtml(config.sandbox_id)}</dd><dt>APPROVAL</dt><dd>${escapeHtml(config.approval_review_id)}</dd><dt>VALID UNTIL</dt><dd>${escapeHtml(formatDate(config.valid_until))}</dd><dt>CONFIG SHA-256</dt><dd><code>${escapeHtml(config.configuration_sha256.slice(0, 20))}…</code></dd></dl>
    <p>Registry entry is immutable and inert. Selection changes only the isolated pointer.</p>` : `
    <strong>NO STORED CONFIGURATION</strong><p>${escapeHtml(configurationIndex.configurations.length)} immutable registry entries are available for this sandbox.</p>`;
  const rollback = sandbox.rollback_candidate;
  $("#sandbox-rollback-status").innerHTML = rollback ? `
    <strong>ROLLBACK AVAILABLE</strong>
    <dl><dt>ACTIVATION EVENT</dt><dd>${escapeHtml(rollback.event_id)}</dd><dt>RECORDED TARGET</dt><dd>${escapeHtml(rollback.previous_configuration_id || "EMPTY BASELINE")}</dd><dt>SAFE TARGET NOW</dt><dd>${escapeHtml(rollback.safe_rollback_configuration_id || "EMPTY BASELINE")}</dd></dl>
    <p>${rollback.target_fails_safe_to_empty ? "Recorded target is no longer valid; rollback will clear the pointer." : "Target remains within current isolated approval authority."}</p>` : '<strong>ROLLBACK BLOCKED</strong><p>No current unrolled activation exists.</p>';
  $("#sandbox-event-history").innerHTML = eventIndex.events.length ? eventIndex.events.map((event) => `
    <article><span>VERSION ${escapeHtml(event.state_version)} · ${escapeHtml(formatDate(event.event_at))} · ${escapeHtml(event.operator)}</span><strong>${escapeHtml(event.action.replaceAll("_", " "))}</strong><small>${escapeHtml(event.previous_configuration_id || "EMPTY")} → ${escapeHtml(event.next_configuration_id || "EMPTY")} · ${escapeHtml(event.event_id)}</small></article>`).join("") : '<p class="shadow-empty">No atomic sandbox pointer event has been archived.</p>';
  const recovery = {
    EMPTY: "Register and activate only through run_isolated_paper_config.py after current approval is verified.",
    ACTIVE: "The isolated pointer is effective, but no strategy process was started. Rollback remains an explicit local CLI action.",
    EXPIRED_FAIL_SAFE: "Stored pointer is already ineffective. Run RECONCILE to persist the fail-safe invalidation event.",
    REVOKED_FAIL_SAFE: "Revoked approval makes the stored pointer ineffective immediately. Run RECONCILE to persist invalidation.",
    APPROVAL_MISMATCH_FAIL_SAFE: "Approval lineage changed. Keep the pointer ineffective and reconcile before further work.",
    CONFIGURATION_MISSING_FAIL_SAFE: "Registry integrity is degraded. Preserve the database and investigate before any action.",
  };
  $("#sandbox-registry-recovery").textContent = `${recovery[current] || "Restore valid registry evidence."} THIS SCREEN HAS NO REGISTER, ACTIVATE OR ROLLBACK BUTTON.`;
}

function renderIsolatedRegistryUnavailable(error) {
  state.isolatedSandbox = null;
  $("#sandbox-effective-status").textContent = "REGISTRY UNAVAILABLE";
  $("#sandbox-effective-status").dataset.status = "UNAVAILABLE";
  $("#sandbox-pointer-summary").innerHTML = '<strong class="warning">NO EFFECTIVE CONFIGURATION INFERRED</strong><p>Stored and effective state could not be separated safely.</p>';
  $("#sandbox-configuration-detail").innerHTML = `<p class="shadow-empty">${escapeHtml(error.message)}</p>`;
  $("#sandbox-rollback-status").innerHTML = '<strong>ROLLBACK BLOCKED</strong><p>No rollback target is inferred.</p>';
  $("#sandbox-event-history").innerHTML = '<p class="shadow-empty">No pointer event history is inferred.</p>';
  $("#sandbox-registry-recovery").textContent = "Restore registry, sandbox and event evidence; shared configuration and live execution remain prohibited.";
}

function renderIsolatedRuntime(runtime, eventIndex, killEventIndex, cycleIndex, cycleEventIndex, ledgerEnvelope, forwardOps) {
  state.isolatedRuntime = runtime;
  const session = runtime.latest_session;
  const status = session?.effective_status || "NO_SESSION";
  const kill = runtime.kill_switch;
  $("#runtime-effective-status").textContent = status.replaceAll("_", " ");
  $("#runtime-effective-status").dataset.status = status;
  $("#runtime-kill-switch").innerHTML = `
    <strong data-status="${escapeHtml(kill.effective_state)}">${escapeHtml(kill.effective_state)}</strong>
    <dl><dt>INITIALIZED</dt><dd>${kill.initialized ? "YES" : "NO · FAIL SAFE"}</dd><dt>STATE VERSION</dt><dd>${escapeHtml(kill.state_version)}</dd><dt>CHANGED</dt><dd>${escapeHtml(kill.changed_at ? formatDate(kill.changed_at) : "—")}</dd></dl>
    <p>${escapeHtml(kill.blocking_reason)}</p>`;
  $("#runtime-session-summary").innerHTML = session ? `
    <strong>${escapeHtml(session.effective_status.replaceAll("_", " "))}</strong>
    <dl><dt>SESSION</dt><dd>${escapeHtml(session.session_id)}</dd><dt>WORKER</dt><dd>${escapeHtml(session.worker_id)}</dd><dt>STORED STATUS</dt><dd>${escapeHtml(session.stored_status)}</dd><dt>EFFECTIVE STATUS</dt><dd>${escapeHtml(session.effective_status)}</dd><dt>CONFIGURATION</dt><dd>${escapeHtml(session.configuration_id)}</dd><dt>SANDBOX VERSION</dt><dd>${escapeHtml(session.sandbox_state_version)}</dd></dl>
    <p>${escapeHtml(session.blocking_reason)}</p>` : '<strong>NO SESSION</strong><p>No isolated runtime lease has been acquired.</p>';
  $("#runtime-lease-health").innerHTML = session ? `
    <strong>${session.effective_status === "RUNNING" ? "LEASE CURRENT" : "LEASE NOT EFFECTIVE"}</strong>
    <dl><dt>LAST HEARTBEAT</dt><dd>${escapeHtml(formatDate(session.last_heartbeat_at))}</dd><dt>HEARTBEAT AGE</dt><dd>${escapeHtml(Math.round(session.heartbeat_age_seconds))} s</dd><dt>LEASE EXPIRES</dt><dd>${escapeHtml(formatDate(session.lease_expires_at))}</dd><dt>SESSION VERSION</dt><dd>${escapeHtml(session.session_version)}</dd></dl>
    <p>Every renewal revalidates the fencing token, pointer version, configuration hash, approval and kill switch.</p>` : '<strong>NO LEASE</strong><p>Runtime remains stopped until an explicit local bounded command acquires a lease.</p>';
  $("#runtime-event-history").innerHTML = eventIndex.events.length ? eventIndex.events.slice().reverse().map((event) => `
    <article><span>VERSION ${escapeHtml(event.session_version)} · ${escapeHtml(formatDate(event.event_at))} · ${escapeHtml(event.operator)}</span><strong>${escapeHtml(event.action)}</strong><small>${escapeHtml(event.reason)} · ${escapeHtml(event.event_id)}</small></article>`).join("") : '<p class="shadow-empty">No runtime session events are archived.</p>';
  $("#runtime-kill-history").innerHTML = killEventIndex.events.length ? killEventIndex.events.slice().reverse().map((event) => `
    <article><span>VERSION ${escapeHtml(event.state_version)} · ${escapeHtml(formatDate(event.event_at))} · ${escapeHtml(event.operator)}</span><strong>${escapeHtml(event.action)} → ${escapeHtml(event.resulting_state)}</strong><small>${escapeHtml(event.note)} · ${escapeHtml(event.event_id)}</small></article>`).join("") : '<p class="shadow-empty">Kill switch is uninitialized and therefore ARMED by default.</p>';
  const checkpoint = cycleIndex.latest_cycle;
  const snapshot = checkpoint?.snapshot;
  const ledger = ledgerEnvelope?.result;
  const fleet = ledger?.bot_fleet;
  $("#runtime-cycle-checkpoint").innerHTML = checkpoint ? `
    <strong>${escapeHtml(checkpoint.status)} · VERSION ${escapeHtml(checkpoint.checkpoint_version)}</strong>
    <dl><dt>CYCLE</dt><dd>${escapeHtml(checkpoint.cycle_id)}</dd><dt>OWNER SESSION</dt><dd>${escapeHtml(checkpoint.owner_session_id)}</dd><dt>ATTEMPTS</dt><dd>${escapeHtml(checkpoint.attempt_count)}</dd><dt>PREVIOUS COMMIT</dt><dd>${escapeHtml(checkpoint.previous_committed_cycle_id || "GENESIS")}</dd><dt>RESULT</dt><dd>${escapeHtml(checkpoint.result_id || "NOT COMMITTED")}</dd></dl>
    <p>${checkpoint.status === "COMMITTED" ? "Result and checkpoint were committed atomically." : "Reserved work may be recovered only after the previous lease is ineffective."}</p>` : '<strong>NO CHECKPOINT</strong><p>No deterministic paper cycle has been reserved.</p>';
  $("#runtime-snapshot-boundary").innerHTML = snapshot ? `
    <strong>CONTENT-ADDRESSED SNAPSHOT</strong>
    <dl><dt>BOUNDARY</dt><dd>${escapeHtml(formatDate(snapshot.snapshot_boundary))}</dd><dt>SNAPSHOT SHA-256</dt><dd><code>${escapeHtml(snapshot.snapshot_sha256.slice(0, 20))}…</code></dd><dt>INPUT SHA-256</dt><dd><code>${escapeHtml(snapshot.combined_input_sha256.slice(0, 20))}…</code></dd><dt>ASSETS</dt><dd>${escapeHtml(snapshot.assets.length)}</dd><dt>SOURCE</dt><dd>${escapeHtml(snapshot.source)}</dd></dl>
    <p>Commit rebuilds this exact boundary and blocks changed candles, funding or cadence evidence.</p>` : '<strong>NO SNAPSHOT</strong><p>No source boundary or input hash is inferred.</p>';
  $("#runtime-ledger-summary").innerHTML = ledger ? `
    <strong>COMMITTED · ${escapeHtml(ledger.result_id)}</strong>
    <dl><dt>FINAL EQUITY</dt><dd>${escapeHtml(formatMoney(ledger.aggregate.final_equity))}</dd><dt>MEAN RETURN</dt><dd>${escapeHtml(formatPercent(ledger.aggregate.mean_total_return, 2, true))}</dd><dt>REALIZED P&amp;L</dt><dd>${escapeHtml(formatMoney(ledger.aggregate.realized_pnl))}</dd><dt>GRID P&amp;L</dt><dd>${escapeHtml(formatMoney(ledger.aggregate.realized_grid_pnl))}</dd><dt>UNREALIZED</dt><dd>${escapeHtml(formatMoney(ledger.aggregate.inventory_unrealized_pnl))}</dd><dt>FEES / FUNDING</dt><dd>${escapeHtml(formatMoney(ledger.aggregate.fees))} / ${escapeHtml(formatMoney(ledger.aggregate.funding))}</dd><dt>MAX LEVERAGE</dt><dd>${escapeHtml(formatNumber(ledger.aggregate.max_effective_leverage, 2))}×</dd><dt>LIQUIDATION RISK</dt><dd>${escapeHtml(formatPercent(ledger.aggregate.max_liquidation_risk, 2))}</dd></dl>
    <p>Deterministic cumulative paper accounting; no external order request was created.</p>` : '<strong>NO COMMITTED LEDGER</strong><p>A RESERVED checkpoint has no effective result until atomic COMMIT succeeds.</p>';
  $("#runtime-bot-fleet").innerHTML = fleet ? fleet.bots.map((bot) => {
    const fills = bot.per_asset.reduce((total, asset) => total + Number(asset.account.fill_evidence.simulated_fill_count || 0), 0);
    return `<article data-status="${escapeHtml(bot.state)}">
      <span>${escapeHtml(bot.bot_id.replaceAll("_", " "))}</span>
      <strong>${escapeHtml(bot.state)}</strong>
      <dl><dt>ACCOUNT</dt><dd>${escapeHtml(bot.account_id)}</dd><dt>FINAL EQUITY</dt><dd>${escapeHtml(formatMoney(bot.aggregate.final_equity))}</dd><dt>MEAN RETURN</dt><dd>${escapeHtml(formatPercent(bot.aggregate.mean_total_return, 2, true))}</dd><dt>REALIZED / GRID</dt><dd>${escapeHtml(formatMoney(bot.aggregate.realized_pnl))} / ${escapeHtml(formatMoney(bot.aggregate.realized_grid_pnl))}</dd><dt>UNREALIZED</dt><dd>${escapeHtml(formatMoney(bot.aggregate.inventory_unrealized_pnl))}</dd><dt>FEES / FUNDING</dt><dd>${escapeHtml(formatMoney(bot.aggregate.fees))} / ${escapeHtml(formatMoney(bot.aggregate.funding))}</dd><dt>MAX LEVERAGE</dt><dd>${escapeHtml(formatNumber(bot.aggregate.max_effective_leverage, 2))}×</dd><dt>LIQUIDATION RISK</dt><dd>${escapeHtml(formatPercent(bot.aggregate.max_liquidation_risk, 2))}</dd><dt>SIMULATED FILLS</dt><dd>${escapeHtml(fills)}</dd></dl>
      <small>${escapeHtml(bot.stop_reasons.length ? bot.stop_reasons.join(" · ") : "Independent virtual account remains inside approved risk limits.")}</small>
    </article>`;
  }).join("") : '<p class="shadow-empty">No four-bot fleet is present in this committed ledger. Legacy MIL-3.23 results remain read-only.</p>';
  const trigger = forwardOps.trigger;
  $("#forward-bot-trigger").innerHTML = `
    <strong>${escapeHtml(forwardOps.status.replaceAll("_", " "))}</strong>
    <dl><dt>TIMEFRAME</dt><dd>${escapeHtml(trigger.timeframe)}</dd><dt>LATEST CLOSED</dt><dd>${escapeHtml(trigger.latest_synchronized_closed_boundary ? formatDate(trigger.latest_synchronized_closed_boundary) : "UNAVAILABLE")}</dd><dt>LATEST COMMITTED</dt><dd>${escapeHtml(trigger.latest_committed_boundary ? formatDate(trigger.latest_committed_boundary) : "NONE")}</dd><dt>NEW CLOSED BAR</dt><dd>${trigger.new_closed_bar ? "YES · WAKE DUE" : "NO"}</dd></dl>
    <p>Only synchronized fully closed candles may trigger one bounded PAPER_ONLY wake.</p>`;
  const delta = forwardOps.cycle_delta;
  $("#forward-bot-delta").innerHTML = delta.bots.length ? `
    <strong>${escapeHtml(delta.status)} · ${escapeHtml(delta.current_result_id)}</strong>
    <dl>${delta.bots.map((bot) => `<dt>${escapeHtml(bot.bot_id.replaceAll("_", " "))}</dt><dd>${bot.metrics.final_equity == null ? "—" : escapeHtml(formatMoney(bot.metrics.final_equity))} equity Δ · ${bot.metrics.realized_pnl == null ? "—" : escapeHtml(formatMoney(bot.metrics.realized_pnl))} realized Δ · ${escapeHtml(bot.per_asset.reduce((sum, asset) => sum + Number(asset.new_simulated_fills || 0), 0))} new fills</dd>`).join("")}</dl>
    <p>Each delta is derived from two verified cumulative account results; GENESIS has no prior cycle.</p>` : '<strong>NO VERIFIED DELTA</strong><p>Two committed ledger v2 results are required for cycle-to-cycle attribution.</p>';
  const burnIn = forwardOps.burn_in;
  $("#forward-bot-burn-in").innerHTML = `
    <strong>${escapeHtml(burnIn.status.replaceAll("_", " "))}</strong>
    <dl><dt>CONTINUOUS DAYS</dt><dd>${escapeHtml(formatNumber(burnIn.observed_days, 2))}</dd><dt>CONTINUOUS CYCLES</dt><dd>${escapeHtml(burnIn.continuous_cycles)}</dd><dt>7-DAY PROGRESS</dt><dd>${escapeHtml(formatPercent(burnIn.minimum_progress, 1))}</dd><dt>14-DAY PROGRESS</dt><dd>${escapeHtml(formatPercent(burnIn.target_progress, 1))}</dd><dt>MAX GAP</dt><dd>${burnIn.max_gap_seconds == null ? "—" : `${escapeHtml(formatNumber(burnIn.max_gap_seconds / 3600, 1))} h`}</dd></dl>
    <p>Readiness requires continuous closed-bar evidence; a gap over two intervals resets the suffix window.</p>`;
  $("#forward-bot-alerts").innerHTML = forwardOps.alerts.length ? forwardOps.alerts.map((alert) => `
    <article data-severity="${escapeHtml(alert.severity)}"><span>${escapeHtml(alert.severity)} · ${escapeHtml(alert.object)}</span><strong>${escapeHtml(alert.code.replaceAll("_", " "))}</strong><small>${escapeHtml(alert.trigger)} ${escapeHtml(alert.impact)} ${escapeHtml(alert.recommended_response)}</small></article>`).join("") : '<p class="shadow-empty">No forward-operations alert is active.</p>';
  $("#runtime-cycle-history").innerHTML = cycleEventIndex.events.length ? cycleEventIndex.events.slice().reverse().map((event) => `
    <article><span>VERSION ${escapeHtml(event.checkpoint_version)} · ${escapeHtml(formatDate(event.event_at))} · ${escapeHtml(event.session_id)}</span><strong>${escapeHtml(event.action)}</strong><small>${escapeHtml(event.cycle_id)} · ${escapeHtml(event.event_id)}</small></article>`).join("") : '<p class="shadow-empty">No reserve/recover/commit history is archived.</p>';
  const recovery = status === "RUNNING"
    ? "Monitor heartbeat age and configuration identity. ARM_KILL remains the immediate local stop path."
    : kill.effective_state === "ARMED"
      ? "Review the stop cause, then use CLEAR_KILL locally only when restart prerequisites are satisfied. Clearing never restarts a session."
      : status === "NO_SESSION" || status === "STOPPED"
        ? "Use the bounded local RUN command only while the registry configuration remains effective."
        : "The stored session is already ineffective. Run RECONCILE locally to persist the fail-safe stop before any new acquisition.";
  const checkpointRecovery = checkpoint?.status === "RESERVED"
    ? " CHECKPOINT IS RESERVED: wait for the owner lease to stop before a new RUN recovers it."
    : checkpoint?.status === "COMMITTED"
      ? " COMMIT IS STABLE: duplicate cycles reuse this result and cannot apply it twice."
      : "";
  $("#runtime-recovery").textContent = `${recovery}${checkpointRecovery} THIS SCREEN HAS NO RUN, STOP, RECOVER OR KILL-SWITCH BUTTON.`;
}

function renderIsolatedRuntimeUnavailable(error) {
  state.isolatedRuntime = null;
  $("#runtime-effective-status").textContent = "RUNTIME UNAVAILABLE";
  $("#runtime-effective-status").dataset.status = "UNAVAILABLE";
  $("#runtime-kill-switch").innerHTML = '<strong data-status="ARMED">INFERRED ARMED</strong><p>No runtime permission is inferred without kill-switch evidence.</p>';
  $("#runtime-session-summary").innerHTML = '<strong>NO EFFECTIVE SESSION</strong><p>Stored and effective runtime state cannot be verified.</p>';
  $("#runtime-lease-health").innerHTML = `<strong>LEASE UNTRUSTED</strong><p>${escapeHtml(error.message)}</p>`;
  $("#runtime-event-history").innerHTML = '<p class="shadow-empty">No runtime history is inferred.</p>';
  $("#runtime-kill-history").innerHTML = '<p class="shadow-empty">No kill-switch history is inferred.</p>';
  $("#runtime-cycle-checkpoint").innerHTML = '<strong>NO TRUSTED CHECKPOINT</strong><p>No commit or recovery state is inferred.</p>';
  $("#runtime-snapshot-boundary").innerHTML = '<strong>SNAPSHOT UNAVAILABLE</strong><p>No market boundary or content hash is trusted.</p>';
  $("#runtime-ledger-summary").innerHTML = '<strong>NO COMMITTED LEDGER</strong><p>No calculated result is inferred.</p>';
  $("#runtime-bot-fleet").innerHTML = '<p class="shadow-empty">No isolated bot account or simulated fill evidence is inferred.</p>';
  $("#forward-bot-trigger").innerHTML = '<strong>TRIGGER UNAVAILABLE</strong><p>No closed-bar wake is inferred.</p>';
  $("#forward-bot-delta").innerHTML = '<strong>DELTA UNAVAILABLE</strong><p>No cycle account change is inferred.</p>';
  $("#forward-bot-burn-in").innerHTML = '<strong>BURN-IN UNAVAILABLE</strong><p>No continuity or readiness claim is inferred.</p>';
  $("#forward-bot-alerts").innerHTML = '<p class="shadow-empty">Forward operation alerts are unavailable.</p>';
  $("#runtime-cycle-history").innerHTML = '<p class="shadow-empty">No checkpoint transition history is inferred.</p>';
  $("#runtime-recovery").textContent = "Restore read-only runtime evidence; runtime, replay and order activity remain blocked.";
}

function renderForwardObservationUnavailable(error, empty = false) {
  state.forwardObservation = null;
  $(".forward-observation-card").dataset.status = empty ? "NO_OBSERVATION" : "UNAVAILABLE";
  $("#forward-observation-status").textContent = empty ? "NO FORWARD CHECKPOINT" : "FORWARD ARCHIVE UNAVAILABLE";
  $("#forward-observation-id").textContent = "NO CHECKPOINT SELECTED";
  $("#forward-observation-summary").innerHTML = `<div><span>SAFE STATE</span><strong class="warning">NO CONFIGURATION APPLIED</strong><small>${empty ? "eligible trial and new market data required" : "restore read-only local API"}</small></div>`;
  $("#forward-observation-comparison").innerHTML = '<p class="shadow-empty">No true out-of-sample comparison is available.</p>';
  $("#forward-observation-boundary").innerHTML = '<strong>BOUNDARY NOT VERIFIED</strong><p>No historical result is treated as forward evidence.</p>';
  $("#forward-observation-lineage").innerHTML = '<strong>NO ARCHIVED LINEAGE</strong><p>No checkpoint continuity is inferred.</p>';
  $("#forward-observation-assets").replaceChildren();
  $("#forward-observation-source").textContent = error.message;
  renderForwardStabilityUnavailable(error);
  renderForwardLifecycleUnavailable(error);
  renderIsolatedActivationUnavailable(error);
  renderIsolatedRegistryUnavailable(error);
  renderIsolatedRuntimeUnavailable(error);
}

async function loadForwardObservations(strategy) {
  const response = await fetch(`/api/v1/forward-observations?limit=30&strategy=${encodeURIComponent(strategy)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`forward observation index returned ${response.status}`);
  const index = validateForwardObservationIndex(await response.json());
  const latest = index.observations[0];
  if (!latest) {
    renderForwardObservationUnavailable(new Error("Archive a checkpoint after an eligible trial accumulates new PAPER_ONLY evidence."), true);
    return;
  }
  const [detailResponse, stabilityResponse, lifecycleResponse, manifestResponse, policyResponse, activationResponse] = await Promise.all([
    fetch(`/api/v1/forward-observations/${encodeURIComponent(latest.observation_id)}`, { cache: "no-store" }),
    fetch(`/api/v1/forward-stability?trial_id=${encodeURIComponent(latest.trial_id)}&limit=90`, { cache: "no-store" }),
    fetch(`/api/v1/forward-lifecycle?trial_id=${encodeURIComponent(latest.trial_id)}`, { cache: "no-store" }),
    fetch(`/api/v1/forward-evidence-manifest?trial_id=${encodeURIComponent(latest.trial_id)}`, { cache: "no-store" }),
    fetch("/api/v1/evidence-governance-policy", { cache: "no-store" }),
    fetch(`/api/v1/isolated-activation?trial_id=${encodeURIComponent(latest.trial_id)}`, { cache: "no-store" }),
  ]);
  if (!detailResponse.ok) throw new Error(`forward observation detail returned ${detailResponse.status}`);
  renderForwardObservation(validateForwardObservationEnvelope(await detailResponse.json()));
  if (!stabilityResponse.ok) {
    renderForwardStabilityUnavailable(new Error(`forward stability returned ${stabilityResponse.status}`));
  } else {
    renderForwardStability(validateForwardStability(await stabilityResponse.json()));
  }
  if (!lifecycleResponse.ok || !manifestResponse.ok) {
    renderForwardLifecycleUnavailable(new Error(`forward lifecycle/manifest returned ${lifecycleResponse.status}/${manifestResponse.status}`));
  } else {
    const lifecycle = validateForwardLifecycle(await lifecycleResponse.json());
    const manifest = validateForwardEvidenceManifest(await manifestResponse.json());
    let latestReviewEnvelope = null;
    if (lifecycle.latest_review) {
      const reviewResponse = await fetch(`/api/v1/forward-reviews/${encodeURIComponent(lifecycle.latest_review.review_id)}`, { cache: "no-store" });
      if (!reviewResponse.ok) {
        renderForwardLifecycleUnavailable(new Error(`forward review returned ${reviewResponse.status}`));
        return;
      }
      latestReviewEnvelope = validateForwardReviewEnvelope(await reviewResponse.json());
    }
    renderForwardLifecycle(lifecycle, latestReviewEnvelope, manifest);
  }
  if (!policyResponse.ok || !activationResponse.ok) {
    renderIsolatedActivationUnavailable(new Error(`evidence policy/activation returned ${policyResponse.status}/${activationResponse.status}`));
    renderIsolatedRegistryUnavailable(new Error("isolated approval evidence is unavailable"));
    renderIsolatedRuntimeUnavailable(new Error("isolated runtime authority is unavailable"));
  } else {
    const policy = validateEvidenceGovernancePolicy(await policyResponse.json());
    const activation = validateIsolatedActivationLifecycle(await activationResponse.json());
    let latestActivationReview = null;
    if (activation.latest_event) {
      const reviewResponse = await fetch(`/api/v1/isolated-activation-reviews/${encodeURIComponent(activation.latest_event.review_id)}`, { cache: "no-store" });
      if (!reviewResponse.ok) {
        renderIsolatedActivationUnavailable(new Error(`isolated activation review returned ${reviewResponse.status}`));
        return;
      }
      latestActivationReview = validateIsolatedActivationReviewEnvelope(await reviewResponse.json());
    }
    renderIsolatedActivation(activation, policy, latestActivationReview);
    const sandboxId = latestActivationReview?.review?.sandbox_id || "aars-paper-sandbox";
    const [configurationResponse, sandboxResponse, eventResponse] = await Promise.all([
      fetch(`/api/v1/isolated-configurations?sandbox_id=${encodeURIComponent(sandboxId)}&limit=100`, { cache: "no-store" }),
      fetch(`/api/v1/isolated-sandbox?sandbox_id=${encodeURIComponent(sandboxId)}`, { cache: "no-store" }),
      fetch(`/api/v1/isolated-sandbox-events?sandbox_id=${encodeURIComponent(sandboxId)}&limit=100`, { cache: "no-store" }),
    ]);
    if (!configurationResponse.ok || !sandboxResponse.ok || !eventResponse.ok) {
      renderIsolatedRegistryUnavailable(new Error(`registry/sandbox/events returned ${configurationResponse.status}/${sandboxResponse.status}/${eventResponse.status}`));
      renderIsolatedRuntimeUnavailable(new Error("registry evidence is unavailable"));
    } else {
      renderIsolatedRegistry(
        validateIsolatedConfigurationIndex(await configurationResponse.json()),
        validateIsolatedSandbox(await sandboxResponse.json()),
        validateIsolatedSandboxEventIndex(await eventResponse.json()),
      );
      const [runtimeResponse, killEventResponse, cycleResponse, forwardOpsResponse] = await Promise.all([
        fetch(`/api/v1/isolated-runtime?sandbox_id=${encodeURIComponent(sandboxId)}&limit=100`, { cache: "no-store" }),
        fetch(`/api/v1/isolated-runtime-kill-events?sandbox_id=${encodeURIComponent(sandboxId)}&limit=100`, { cache: "no-store" }),
        fetch(`/api/v1/isolated-runtime-cycles?sandbox_id=${encodeURIComponent(sandboxId)}&limit=100`, { cache: "no-store" }),
        fetch(`/api/v1/forward-bot-operations?sandbox_id=${encodeURIComponent(sandboxId)}`, { cache: "no-store" }),
      ]);
      if (!runtimeResponse.ok || !killEventResponse.ok || !cycleResponse.ok || !forwardOpsResponse.ok) {
        renderIsolatedRuntimeUnavailable(new Error(`runtime/kill-events/cycles/forward-ops returned ${runtimeResponse.status}/${killEventResponse.status}/${cycleResponse.status}/${forwardOpsResponse.status}`));
      } else {
        const runtime = validateIsolatedRuntime(await runtimeResponse.json());
        const killEvents = validateIsolatedRuntimeKillEventIndex(await killEventResponse.json());
        const cycleIndex = validateIsolatedRuntimeCycleIndex(await cycleResponse.json());
        const forwardOps = validateForwardBotOperations(await forwardOpsResponse.json());
        let runtimeEvents = validateIsolatedRuntimeEventIndex({
          schema_version: "mil3.isolated-paper-runtime-event-index.v1",
          execution_mode: "PAPER_ONLY",
          session_id: null,
          events: [],
          read_only: true,
          browser_control_allowed: false,
          replay_started: false,
          order_path_present: false,
          live_execution_allowed: false,
        });
        if (runtime.latest_session) {
          const runtimeEventResponse = await fetch(`/api/v1/isolated-runtime-events?session_id=${encodeURIComponent(runtime.latest_session.session_id)}&limit=100`, { cache: "no-store" });
          if (!runtimeEventResponse.ok) {
            renderIsolatedRuntimeUnavailable(new Error(`runtime events returned ${runtimeEventResponse.status}`));
            return;
          }
          runtimeEvents = validateIsolatedRuntimeEventIndex(await runtimeEventResponse.json());
        }
        let cycleEvents = validateIsolatedRuntimeCycleEventIndex({
          schema_version: "mil3.isolated-paper-runtime-cycle-event-index.v1",
          execution_mode: "PAPER_ONLY", cycle_id: null, events: [], read_only: true,
          paper_orders_created: false, order_path_present: false, live_execution_allowed: false,
        });
        let ledgerEnvelope = null;
        if (cycleIndex.latest_cycle) {
          const requests = [
            fetch(`/api/v1/isolated-runtime-cycle-events?cycle_id=${encodeURIComponent(cycleIndex.latest_cycle.cycle_id)}&limit=100`, { cache: "no-store" }),
          ];
          if (cycleIndex.latest_cycle.result_id) requests.push(fetch(`/api/v1/isolated-paper-ledger-results/${encodeURIComponent(cycleIndex.latest_cycle.result_id)}`, { cache: "no-store" }));
          const responses = await Promise.all(requests);
          if (!responses.every((response) => response.ok)) {
            renderIsolatedRuntimeUnavailable(new Error(`checkpoint evidence returned ${responses.map((response) => response.status).join("/")}`));
            return;
          }
          cycleEvents = validateIsolatedRuntimeCycleEventIndex(await responses[0].json());
          if (responses[1]) ledgerEnvelope = validateIsolatedPaperLedgerEnvelope(await responses[1].json());
        }
        renderIsolatedRuntime(runtime, runtimeEvents, killEvents, cycleIndex, cycleEvents, ledgerEnvelope, forwardOps);
      }
    }
  }
}

function validationMarkets(snapshot) {
  return snapshot.validation.markets || [snapshot.validation];
}

function renderShadowSnapshot(snapshotId, snapshot) {
  state.selectedShadowSnapshot = snapshotId;
  $("#shadow-detail-id").textContent = snapshotId;
  const assets = validationMarkets(snapshot).map((market) => {
    const latestFold = market.folds?.at(-1);
    const warnings = market.warnings?.map((item) => item.code) || [];
    return `<article class="shadow-asset-card">
      <span>${escapeHtml(market.market.symbol)} · LATEST TRAIN-SELECTED CANDIDATE</span>
      <strong>${escapeHtml(latestFold?.selected_candidate?.candidate_id || "NO COMPLETE FOLD")}</strong>
      <dl>
        <dt>OUT-OF-SAMPLE RETURN</dt><dd>${formatPercent(market.aggregate.mean_test_return, 1, true)}</dd>
        <dt>SELECTION STABILITY</dt><dd>${formatPercent(market.aggregate.selection_stability)}</dd>
        <dt>WARNINGS</dt><dd>${warnings.length ? escapeHtml(warnings.join(", ")) : "NONE"}</dd>
      </dl>
    </article>`;
  }).join("");
  const portfolio = snapshot.portfolio.summary;
  const reasons = snapshot.review_gate.reasons?.length ? snapshot.review_gate.reasons.join(", ") : "No deferral reason recorded";
  $("#shadow-detail").innerHTML = `
    <div class="shadow-detail-provenance">
      <span>SYNC EVIDENCE ${escapeHtml(formatDate(snapshot.as_of))}</span>
      <span>VALIDATION ${escapeHtml(snapshot.configuration.validation_strategy)}</span>
      <span>MONITORED PORTFOLIO ${escapeHtml(snapshot.configuration.portfolio_strategy)} · FIXED DEFAULTS</span>
      <span>LIVE EXECUTION DISALLOWED</span>
    </div>
    <div class="shadow-asset-grid">${assets}</div>
    <div class="shadow-portfolio-evidence">
      <div><span>PORTFOLIO RETURN</span><strong class="${trendClass(portfolio.total_return)}">${formatPercent(portfolio.total_return, 1, true)}</strong></div>
      <div><span>MAX DRAWDOWN</span><strong>${formatPercent(portfolio.max_drawdown)}</strong></div>
      <div><span>NET / GROSS EXPOSURE</span><strong>${formatNumber(portfolio.final_net_exposure)}× / ${formatNumber(portfolio.final_gross_exposure)}×</strong></div>
      <div><span>MARGIN BUFFER</span><strong>${formatPercent(portfolio.min_margin_buffer_pct)}</strong></div>
      <div><span>LIQUIDATION RISK</span><strong>${formatPercent(portfolio.max_liquidation_risk)}</strong></div>
      <div><span>REVIEW REASON</span><strong>${escapeHtml(reasons)}</strong></div>
    </div>`;
}

function renderShadowDetailUnavailable(error) {
  $("#shadow-detail-id").textContent = "UNAVAILABLE";
  $("#shadow-detail").innerHTML = `<p class="shadow-empty">Snapshot detail unavailable. The last stability view remains visible. ${escapeHtml(error.message)}</p>`;
}

function renderShadowUnavailable(error) {
  state.shadowStability = null;
  $("#shadow-state-banner").dataset.status = "DEGRADED";
  $("#shadow-as-of").textContent = "NO LOCAL API EVIDENCE";
  $("#shadow-review-gate").textContent = "DEFER";
  $("#shadow-review-gate").className = "warning";
  $("#shadow-history-trust").textContent = "UNAVAILABLE";
  $("#shadow-history-trust").className = "warning";
  $("#shadow-next-step").textContent = "Start the read-only local API and run the explicit daily archive command. No sample daily evidence is fabricated.";
  $("#shadow-metrics").innerHTML = '<div><span>RECOVERY</span><strong class="warning">LOCAL API REQUIRED</strong><small>PAPER_ONLY evidence remains preserved</small></div>';
  $("#shadow-trend").innerHTML = '<p class="shadow-empty">Continuous shadow history is unavailable.</p>';
  $("#shadow-warning-count").textContent = "0";
  $("#shadow-warning-list").innerHTML = `<p class="shadow-empty">${escapeHtml(error.message)}</p>`;
  $("#shadow-timeline").innerHTML = '<p class="shadow-empty">No snapshot timeline loaded.</p>';
  renderShadowDetailUnavailable(error);
  renderPromotionUnavailable(error);
  renderPaperProposalUnavailable(error);
  renderPaperTrialUnavailable(error);
  renderForwardObservationUnavailable(error);
}

async function loadShadowSnapshot(snapshotId) {
  const response = await fetch(`/api/v1/shadow-snapshots/${encodeURIComponent(snapshotId)}`, { cache: "no-store" });
  if (!response.ok) throw new Error(`snapshot detail returned ${response.status}`);
  const snapshot = validateShadowPayload(await response.json(), "mil3.shadow-daily.v1");
  renderShadowSnapshot(snapshotId, snapshot);
}

async function loadShadowEvidence() {
  const strategy = $("#shadow-strategy").value;
  $("#shadow-refresh").disabled = true;
  $("#shadow-refresh").textContent = "READING EVIDENCE…";
  try {
    const [indexResponse, stabilityResponse] = await Promise.all([
      fetch(`/api/v1/shadow-snapshots?limit=90&strategy=${encodeURIComponent(strategy)}`, { cache: "no-store" }),
      fetch(`/api/v1/shadow-stability?limit=90&strategy=${encodeURIComponent(strategy)}`, { cache: "no-store" }),
    ]);
    if (!indexResponse.ok) throw new Error(`snapshot index returned ${indexResponse.status}`);
    if (!stabilityResponse.ok) throw new Error(`stability view returned ${stabilityResponse.status}`);
    const index = await indexResponse.json();
    if (index.execution_mode !== "PAPER_ONLY" || index.read_only !== true) throw new Error("unsafe snapshot index rejected");
    const stability = validateShadowPayload(await stabilityResponse.json(), "mil3.shadow-stability.v1");
    renderShadowStability(stability);
    const latestId = stability.points.at(-1)?.snapshot_id || index.shadow_snapshots[0]?.snapshot_id;
    await Promise.all([
      latestId
        ? loadShadowSnapshot(latestId).catch(renderShadowDetailUnavailable)
        : Promise.resolve(renderShadowDetailUnavailable(new Error("archive the first daily snapshot to populate evidence"))),
      loadPromotionGovernance(strategy).catch(renderPromotionUnavailable),
      loadPaperProposals(strategy).catch(renderPaperProposalUnavailable),
      loadPaperTrials(strategy).catch(renderPaperTrialUnavailable),
      loadForwardObservations(strategy).catch(renderForwardObservationUnavailable),
    ]);
  } finally {
    $("#shadow-refresh").disabled = false;
    $("#shadow-refresh").textContent = "REFRESH READ-ONLY VIEW";
  }
}

async function loadPayload() {
  try {
    const endpoint = location.protocol === "file:" ? "./dashboard_payload.json" : "/api/v1/dashboard?symbol=SOLUSDT&interval=1h&window=90d";
    const response = await fetch(endpoint, { cache: "no-store" });
    if (!response.ok) throw new Error(`payload request returned ${response.status}`);
    state.payload = validatePayload(await response.json());
  } catch (error) {
    state.payload = SAMPLE_PAYLOAD;
    state.usingSample = true;
    console.info("AARS console is using its deterministic demonstration payload:", error.message);
  }
  if (!state.payload.strategies.some((item) => item.id === state.selectedStrategy)) {
    state.selectedStrategy = state.payload.strategies[0].id;
  }
  render();
  await Promise.all([
    loadArchiveOptions(),
    loadPortfolio().catch(renderPortfolioUnavailable),
    loadCurrentCadence(),
    loadShadowEvidence().catch(renderShadowUnavailable),
  ]);
}

$("#market-select").addEventListener("change", () => requestDashboard().catch(showSwitchFailure));
$("#window-select").addEventListener("change", () => requestDashboard().catch(showSwitchFailure));
$("#archive-select").addEventListener("change", (event) => loadArchivedView(event.target.value).catch(showSwitchFailure));
$("#diff-before").addEventListener("change", () => loadStableDiff().catch(showSwitchFailure));
$("#diff-after").addEventListener("change", () => loadStableDiff().catch(showSwitchFailure));
$("#shadow-strategy").addEventListener("change", () => loadShadowEvidence().catch(renderShadowUnavailable));
$("#shadow-refresh").addEventListener("click", () => loadShadowEvidence().catch(renderShadowUnavailable));

function showSwitchFailure(error) {
  renderViewControls();
  $("#archive-select").value = state.viewingArchive?.view_id || "";
  $("#degraded-banner").hidden = false;
  $("#degraded-reason").textContent = `Requested view unavailable; preserving the last stable display. ${error.message}`;
  $("#view-status").textContent = "Switch failed · previous stable view preserved";
}

$$('[data-chart]').forEach((button) => {
  button.addEventListener("click", () => {
    state.chartMode = button.dataset.chart;
    $$('[data-chart]').forEach((item) => item.classList.toggle("active", item === button));
    renderChart(currentStrategy());
  });
});

loadPayload();
