const strategySeeds = [
  ["BUY_HOLD", 0.182, 0.248, 0.71, 0.93, 1.16, 1.03, 0.006, 0, 168.4],
  ["SPOT_GRID", 0.126, 0.112, 0.88, 1.27, 1.42, 1.01, 0.006, 0, 118.1],
  ["FUTURES_LONG_GRID_10X", 0.314, 0.392, 0.63, 0.81, 1.09, 10.64, 0.054, 0, 147.9],
  ["AARS_DYNAMIC", 0.154, 0.087, 1.11, 1.48, 1.67, 0.74, 0.004, 0, 154.2],
];

function traceFor(seed, index) {
  const points = [];
  for (let i = 0; i < 96; i += 1) {
    const trend = seed * (i / 95);
    const wave = Math.sin(i * (0.19 + index * 0.02)) * (0.016 + index * 0.004);
    const equity = 1000 * (1 + trend + wave);
    const drawdown = Math.max(0, (Math.sin(i * 0.13 + index) + 1) * 0.5 * (0.05 + index * 0.025));
    const leverage = index === 2 ? 5.2 + Math.sin(i * 0.17) * 3.8 : 0.38 + index * 0.13 + Math.sin(i * 0.15) * 0.12;
    points.push({
      index: 120 + i,
      as_of: new Date(Date.UTC(2026, 7, 20, i)).toISOString(),
      mark_price: 148 + Math.sin(i * 0.12) * 7 + i * 0.05,
      equity,
      drawdown,
      net_exposure: index === 3 ? Math.sin(i * 0.09) * 0.68 : Math.max(0, leverage),
      effective_leverage: Math.abs(leverage),
      margin_buffer_pct: leverage ? 1 / Math.abs(leverage) : 1,
      liquidation_risk: index === 2 ? 0.025 + Math.max(0, Math.sin(i * 0.17)) * 0.029 : 0.004,
    });
  }
  return points;
}

const strategies = strategySeeds.map((seed, index) => {
  const [id, totalReturn, maxDrawdown, sharpe, sortino, profitFactor, maxLev, liqRisk, liqEvents, finalPrice] = seed;
  return {
    id,
    summary: {
      strategy: id,
      execution_mode: "PAPER_ONLY",
      symbol: "SOLUSDT",
      timeframe: "1h",
      bars: 2160,
      initial_equity: 1000,
      final_equity: 1000 * (1 + totalReturn),
      total_return: totalReturn,
      max_drawdown: maxDrawdown,
      sharpe_approx: sharpe,
      sortino,
      profit_factor: profitFactor,
      profit_factor_label: profitFactor.toFixed(2),
      turnover_notional: [1000, 28420, 184920, 19360][index],
      fees: [0.5, 14.21, 92.46, 9.68][index],
      slippage: [0.2, 5.68, 36.98, 3.87][index],
      funding: [0, 0, 42.18, 1.26][index],
      realized_pnl: [0, 118.4, 402.7, 121.6][index],
      realized_grid_pnl: [0, 118.4, 402.7, 0][index],
      inventory_unrealized_pnl: [183.2, 27.4, 82.1, 47.2][index],
      final_net_exposure: [1.01, 0.38, 4.82, -0.21][index],
      max_abs_net_exposure: maxLev,
      final_effective_leverage: [1.01, 0.38, 4.82, 0.21][index],
      max_effective_leverage: maxLev,
      min_margin_buffer_pct: [0.97, 0.91, 0.094, 0.88][index],
      max_liquidation_risk: liqRisk,
      liquidation_events: liqEvents,
      final_mark_price: finalPrice,
    },
    trace: traceFor(totalReturn, index),
  };
});

export const SAMPLE_PAYLOAD = {
  schema_version: "mil3.dashboard.v1",
  generated_at: "2026-08-24T07:30:00+00:00",
  execution_mode: "PAPER_ONLY",
  market: {
    symbol: "SOLUSDT",
    timeframe: "1h",
    bars: 2280,
    source: "Embedded deterministic demonstration payload",
    latest_candle_at: "2026-08-24T07:00:00+00:00",
    freshness_status: "UNKNOWN",
    degraded: true,
    degraded_reason: "No generated dashboard_payload.json was found; demonstration data is displayed.",
  },
  highest_risk: {
    level: "ELEVATED",
    strategy: "FUTURES_LONG_GRID_10X",
    liquidation_risk: 0.054,
    liquidation_events: 0,
    min_margin_buffer_pct: 0.094,
  },
  latest_stable_view: {
    as_of: "2026-08-24T07:00:00+00:00",
    state: "DISTRIBUTION",
    confidence: 0.78,
    probabilities: { bull: 0.21, base: 0.49, bear: 0.3, horizon_bars: 24 },
    recommended_exposure: -0.21,
    decision_reason: "state=DISTRIBUTION; state_prior=-0.15; bull=0.210; bear=0.300; confidence=0.78",
    evidence: ["RSI and price structure show weakening momentum", "Close remains below the short-term EMA cluster"],
    counter_evidence: ["Long-term EMA structure has not confirmed a breakdown"],
    status: "DEGRADED",
  },
  parameters: {
    initial_equity: 1000,
    warmup_bars: 120,
    futures_leverage: 10,
    aars_max_abs_exposure: 1,
    grid_spacing_pct: 0.01,
    grid_levels: 5,
    tactical_hedge: true,
    fee_rate: 0.0005,
    slippage_rate: 0.0002,
    funding_rate_per_bar: 0.00001,
    maintenance_margin_rate: 0.005,
    intrabar_path_model: "green: prev-close/open/low/high/close; red: prev-close/open/high/low/close",
  },
  strategies,
  alerts: [
    {
      id: "DATA_FRESHNESS",
      severity: "ELEVATED",
      object: "SOLUSDT",
      trigger: "dashboard_payload.json is not loaded",
      impact: "The screen is showing deterministic demonstration data, not current market evidence.",
      recommended_action: "Generate the payload from SQLite and reload this console.",
      status: "OPEN",
      closure_condition: "A valid mil3.dashboard.v1 payload is loaded.",
    },
    {
      id: "LEVERAGE_WATCH",
      severity: "ELEVATED",
      object: "FUTURES_LONG_GRID_10X",
      trigger: "configured futures leverage is 10x",
      impact: "Small price changes can materially compress margin buffer.",
      recommended_action: "Review leverage and liquidation traces before shadow acceptance.",
      status: "MONITORING",
      closure_condition: "Leverage is reduced below 5x or an exception is recorded.",
    },
  ],
  review_gate: {
    disposition: "DEFER",
    reasons: ["DATA_FRESHNESS", "LEVERAGE_WATCH"],
    live_execution_allowed: false,
  },
};
