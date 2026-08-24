const state = {
  payload: null,
  selectedStrategy: "AARS_DYNAMIC",
  chartMode: "equity",
  usingSample: false,
  viewingArchive: null,
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
    ? `${funding.events} EVENTS · ${funding.coverage?.status || "UNCHECKED"}`
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
  await Promise.all([loadArchiveOptions(), loadPortfolio().catch(renderPortfolioUnavailable)]);
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
      <span>${escapeHtml(asset.funding_coverage_status)} FUNDING · ${formatPercent(asset.max_liquidation_risk)} LIQ.</span>
    </div>`).join("");
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
  await Promise.all([loadArchiveOptions(), loadPortfolio().catch(renderPortfolioUnavailable)]);
}

$("#market-select").addEventListener("change", () => requestDashboard().catch(showSwitchFailure));
$("#window-select").addEventListener("change", () => requestDashboard().catch(showSwitchFailure));
$("#archive-select").addEventListener("change", (event) => loadArchivedView(event.target.value).catch(showSwitchFailure));
$("#diff-before").addEventListener("change", () => loadStableDiff().catch(showSwitchFailure));
$("#diff-after").addEventListener("change", () => loadStableDiff().catch(showSwitchFailure));

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
