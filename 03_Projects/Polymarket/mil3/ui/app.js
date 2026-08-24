import { SAMPLE_PAYLOAD } from "./sample-data.js";

const state = {
  payload: null,
  selectedStrategy: "AARS_DYNAMIC",
  chartMode: "equity",
  usingSample: false,
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
}

function render() {
  renderSystemStatus();
  renderStrategyNav();
  renderSelectedStrategy();
  renderRisk();
  renderLatestStableView();
}

async function loadPayload() {
  try {
    const response = await fetch("./dashboard_payload.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`payload request returned ${response.status}`);
    const payload = await response.json();
    if (payload.schema_version !== "mil3.dashboard.v1") throw new Error("unsupported dashboard schema");
    if (payload.execution_mode !== "PAPER_ONLY") throw new Error("unsafe execution mode rejected");
    state.payload = payload;
  } catch (error) {
    state.payload = SAMPLE_PAYLOAD;
    state.usingSample = true;
    console.info("AARS console is using its deterministic demonstration payload:", error.message);
  }
  if (!state.payload.strategies.some((item) => item.id === state.selectedStrategy)) {
    state.selectedStrategy = state.payload.strategies[0].id;
  }
  render();
}

$$('[data-chart]').forEach((button) => {
  button.addEventListener("click", () => {
    state.chartMode = button.dataset.chart;
    $$('[data-chart]').forEach((item) => item.classList.toggle("active", item === button));
    renderChart(currentStrategy());
  });
});

loadPayload();
