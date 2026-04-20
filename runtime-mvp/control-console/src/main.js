const PROCEDURE_DATA = {
  id: "E-0",
  title: "反应堆跳闸或安全注入",
  steps: [
    {
      id: 1,
      title: "验证反应堆已跳闸",
      status: "completed",
      logic: "确认所有控制棒底灯亮且中子通量下降。",
    },
    {
      id: 2,
      title: "验证汽轮机已跳闸",
      status: "completed",
      logic: "确认主汽门已关闭且发电机输出功率为零。",
    },
    {
      id: 3,
      title: "核实交流应急母线带电",
      status: "active",
      logic: "检查母线电压 > 370V 且柴油发电机运行正常。",
    },
    {
      id: 4,
      title: "检查安注水箱 (RWST) 液位",
      status: "pending",
      logic: "若液位低于低限，需手动切换吸入口。",
    },
    {
      id: 5,
      title: "控制主汽隔离阀 (MSIV)",
      status: "pending",
      logic: "基于二回路降压速率判断是否隔离。",
    },
  ],
};

const ALERTS = [
  { level: "critical", label: "RWST 液位低限触发", time: "02:14:05" },
  { level: "warning", label: "辅助供水流量异常", time: "02:15:21" },
  { level: "info", label: "柴油发电机 1A 已加载", time: "02:13:58" },
];

const XAI_LEVELS = [
  { id: 1, label: "结论" },
  { id: 2, label: "物理证据" },
  { id: 3, label: "孪生推演" },
];

const TREND_POINTS = [40, 45, 52, 60, 58, 55, 48, 42, 38, 35, 32, 30];

const state = {
  activeStepId: 3,
  showXaiLevel: 1,
  isAuthorized: false,
  pressure: 15.2,
  temp: 312.4,
  aiConfidence: 96,
};

function stepStatusLabel(status) {
  if (status === "completed") return "已完成";
  if (status === "active") return "执行中";
  return "待处理";
}

function stepStatusClass(status) {
  if (status === "completed") return "step-card--completed";
  if (status === "active") return "step-card--active";
  return "";
}

function renderRadar() {
  return `
    <div class="console-radar">
      <svg viewBox="0 0 100 100" class="w-full h-full drop-shadow-lg" role="img" aria-label="CSF radar illustration">
        <circle cx="50" cy="50" r="45" fill="none" stroke="#334155" stroke-width="0.5" stroke-dasharray="2" />
        <circle cx="50" cy="50" r="30" fill="none" stroke="#334155" stroke-width="0.5" stroke-dasharray="2" />
        ${[0, 60, 120, 180, 240, 300]
          .map(
            (deg) => `
              <line
                x1="50"
                y1="50"
                x2="${50 + 45 * Math.cos((deg * Math.PI) / 180)}"
                y2="${50 + 45 * Math.sin((deg * Math.PI) / 180)}"
                stroke="#475569"
                stroke-width="0.5"
              />
            `,
          )
          .join("")}
        <polygon
          points="50,15 80,40 75,70 50,85 25,70 20,40"
          fill="rgba(34, 197, 94, 0.2)"
          stroke="#22c55e"
          stroke-width="1"
        />
        <text x="50" y="10" font-size="4" text-anchor="middle" fill="#94a3b8">次临界</text>
        <text x="90" y="40" font-size="4" text-anchor="start" fill="#fbbf24">核心冷却</text>
        <text x="90" y="70" font-size="4" text-anchor="start" fill="#94a3b8">热阱</text>
        <text x="50" y="95" font-size="4" text-anchor="middle" fill="#94a3b8">完整性</text>
        <text x="10" y="70" font-size="4" text-anchor="end" fill="#94a3b8">容器</text>
        <text x="10" y="40" font-size="4" text-anchor="end" fill="#94a3b8">水容量</text>
      </svg>
    </div>
  `;
}

function renderStepList() {
  return PROCEDURE_DATA.steps
    .map((step) => {
      const active = step.id === state.activeStepId;
      return `
        <button
          type="button"
          class="step-card ${stepStatusClass(step.status)}"
          data-step-id="${step.id}"
        >
          <div class="step-card-topline">
            <div class="step-badge ${step.status === "completed" ? "step-badge--done" : ""}">
              ${step.status === "completed" ? "✓" : step.id}
            </div>
            <span class="console-pill">${stepStatusLabel(step.status)}</span>
          </div>
          <h3 class="step-card-title ${active ? "text-blue-300" : ""}">${step.title}</h3>
          <p class="step-card-desc">${step.logic}</p>
          ${active ? '<span class="metric-label">EXECUTING</span>' : ""}
        </button>
      `;
    })
    .join("");
}

function renderXaiContent() {
  if (state.showXaiLevel === 1) {
    return `
      <div class="console-panel">
        <div class="console-hero">
          <p>检测到安注系统启动后的次生异常，建议立即核实阀门隔离状态并保持当前注水流量。</p>
        </div>
        <div class="console-pill">预期安全收益: +15.4% 堆芯冷却裕量</div>
        <div class="console-pill">法规对标状态: 符合 IEEE 1786 规程导则</div>
        <div class="console-pill">RAG 证据: 已匹配历史运行反馈</div>
      </div>
    `;
  }

  if (state.showXaiLevel === 2) {
    return `
      <div class="console-panel">
        <div class="console-pill">传感器流量计 FI-203 出现反向压差信号</div>
        <div class="console-pill">P&amp;ID 逻辑验证：阀门 V-101 处于非计划全开位</div>
        <div class="console-hero">
          <p>
            主蒸汽管线破裂 → 二回路降压 → FI-203 反转 → V-101 未自动隔离(潜在卡涩)
          </p>
        </div>
      </div>
    `;
  }

  return `
    <div class="console-panel">
      <p class="console-subtitle">基于数字孪生的 "What-If" 未来 15 分钟态势预测：</p>
      <div style="display:flex; align-items:end; gap:4px; height:96px; padding: 0 8px; border-bottom: 1px solid rgba(148,163,184,0.14); border-left: 1px solid rgba(148,163,184,0.14);">
        ${TREND_POINTS.map(
          (height, idx) => `
            <div style="position:relative; flex:1; height:100%;">
              <div style="height:${height}%; border-radius:6px 6px 0 0; background: rgba(59,130,246,0.36);"></div>
              ${idx === 3 ? '<div style="position:absolute; inset:0; border-top:2px solid #ef4444; animation:pulse 1.6s infinite;"></div>' : ""}
            </div>
          `,
        ).join("")}
      </div>
      <div style="display:flex; justify-content:space-between; font-size:9px; color:#64748b; padding:0 2px;">
        <span>当前</span>
        <span>建议执行点</span>
        <span>未来 15min (预测安全)</span>
      </div>
    </div>
  `;
}

function renderAlerts() {
  return ALERTS.map((alert) => {
    const icon = alert.level === "critical" ? "🚨" : alert.level === "warning" ? "⚠" : "ℹ";
    return `
      <div class="monitor-item monitor-item--${alert.level}">
        <span>${icon} ${alert.label}</span>
        <span>${alert.time}</span>
      </div>
    `;
  }).join("");
}

function render() {
  const root = document.querySelector("#app");
  if (!root) {
    throw new Error("Unable to find #app root for Control Console page");
  }

  const activeStep = PROCEDURE_DATA.steps.find((step) => step.id === state.activeStepId) ?? PROCEDURE_DATA.steps[2];
  const authLabel = state.isAuthorized ? "授权成功：操作员已通过 POE 验证" : "解锁提示：展开 POE 证据点以激活软控制按钮";

  root.innerHTML = `
    <div class="control-console-shell">
      <section class="top-banner" aria-label="Control console page header">
        <div class="banner-meta">
          <div class="eyebrow">AARS Runtime MVP / Control Console</div>
          <div class="control-console-topline">
            <span class="control-chip control-chip--accent"><strong>规程集:</strong> ${PROCEDURE_DATA.id}</span>
            <span class="control-chip control-chip--warning"><strong>当前步骤:</strong> ${activeStep.title}</span>
            <span class="control-chip control-chip--ok"><strong>AI 置信度:</strong> ${state.aiConfidence}%</span>
          </div>
        </div>
        <div class="banner-title-row">
          <div class="section-block">
            <h1 class="page-title">AI-CPS 智能规程执行控制台</h1>
            <p class="page-subtitle">
              这是一个独立可打开的控制台页面。它展示规程、态势、XAI 证据点和软控制区，并保留受限执行边界。
            </p>
            <div class="status-row">
              <span class="status-pill status-pill--accent">Type-3 协同执行</span>
              <span class="status-pill status-pill--warning">Control Surface</span>
              <span class="status-pill status-pill--accent">AI-CPS Online</span>
            </div>
          </div>
          <div class="hero-callout">
            <div class="mini-label">当前聚焦</div>
            <p>${activeStep.logic}</p>
          </div>
        </div>
      </section>

      <section class="control-console-main">
        <div class="console-column console-column--left">
          <div class="console-header">
            <div class="console-title-group">
              <div class="eyebrow">规程逻辑序列</div>
              <h2 class="console-section-title">反应堆跳闸或安全注入</h2>
            </div>
            ${renderRadar()}
          </div>
          <div class="console-pane console-scroll">
            <div class="console-hero">
              <p>SSOT 事实源验证已通过。点击任一步骤即可切换当前聚焦节点。</p>
            </div>
            <div class="step-list">
              ${renderStepList()}
            </div>
            <div class="console-actions">
              <button class="console-button console-button--danger" data-console-action="terminate">终止当前规程</button>
              <button class="console-button" data-console-action="fallback">降级至纸质模式 (PBP)</button>
            </div>
          </div>
        </div>

        <div class="console-column console-column--right">
          <div class="console-pane console-scroll">
            <div class="top-banner" style="position: static; top: auto;">
              <div class="banner-meta">
                <div class="eyebrow">AI 顶层建议区</div>
                <div class="control-console-topline">
                  <span class="control-chip control-chip--accent"><strong>Confidence:</strong> ${state.aiConfidence}%</span>
                  <span class="control-chip control-chip--ok"><strong>授权:</strong> ${state.isAuthorized ? "已解锁" : "未解锁"}</span>
                </div>
              </div>
              <div class="banner-title-row">
                <div class="section-block">
                  <h2 class="page-title" style="font-size: clamp(1.5rem, 2.6vw, 2.8rem);">AI 智能优化建议</h2>
                  <p class="page-subtitle">
                    检测到安注系统启动后的次生异常，建议优先隔离 V-101 阀门以保护蒸汽发生器。
                  </p>
                </div>
                <div class="hero-callout">
                  <div class="mini-label">执行状态</div>
                  <p>${state.isAuthorized ? "可执行" : "待授权"}</p>
                </div>
              </div>

              <div class="section-block">
                <div class="eyebrow">XAI 证据点 (Points of Evidence)</div>
                <div class="xai-tabs">
                  ${XAI_LEVELS.map(
                    (level) => `
                      <button
                        class="xai-tab ${state.showXaiLevel === level.id ? "xai-tab--active" : ""}"
                        data-xai-level="${level.id}"
                        type="button"
                      >
                        ${level.label}
                      </button>
                    `,
                  ).join("")}
                </div>
                <div class="xai-content">
                  ${renderXaiContent()}
                </div>
              </div>
            </div>

            <div class="console-grid">
              <section class="console-card">
                <div class="console-panel">
                  <div class="console-panel-title">
                    <span>📡</span>
                    <span>关联报警窗口 (12)</span>
                  </div>
                  <div class="monitor-list">
                    ${renderAlerts()}
                  </div>
                </div>
              </section>

              <section class="console-card">
                <div class="console-panel">
                  <div class="console-panel-title">
                    <span>🔧</span>
                    <span>软控制 / 交互区</span>
                  </div>
                  <div class="console-card">
                    <div class="step-card-topline">
                      <div>
                        <div class="console-pill">V-101 阀门控制</div>
                        <p class="console-subtitle" style="margin-top:10px;">当前状态: 全开 (100%)</p>
                      </div>
                      <button class="console-button ${state.isAuthorized ? "console-button--primary" : ""}" data-console-action="isolate-valve" type="button">隔离阀门</button>
                    </div>
                  </div>
                  <div class="console-card">
                    <div class="console-panel" style="justify-items:center; text-align:center;">
                      <button class="console-button" data-console-action="toggle-auth" type="button">
                        ${state.isAuthorized ? "🔓" : "🔒"} ${authLabel}
                      </button>
                    </div>
                  </div>
                </div>
              </section>
            </div>

            <section class="console-card console-card--full">
              <div class="console-panel-title">
                <span>ℹ</span>
                <span>运行提示</span>
              </div>
              <p class="console-subtitle" style="margin:0;">
                实时安全提示：AI-CPS 已识别到堆芯出口热电偶温度趋势平稳，建议维持当前注水流量。
              </p>
            </section>
          </div>
        </div>
      </section>

      <footer class="console-footer">
        <div class="footer-group">
          <span class="footer-pulse" aria-hidden="true"></span>
          <span class="metric-label" style="margin:0;">AI AGENT: ONLINE</span>
          <span class="console-pill">Safety Class C</span>
        </div>
        <div class="console-actions">
          <button class="console-button" data-console-action="report" type="button">生成当前工况报告</button>
          <button class="console-button console-button--primary" data-console-action="sync" type="button">同步至全厂监视大屏</button>
        </div>
      </footer>
    </div>
  `;

  root.querySelectorAll("[data-step-id]").forEach((button) => {
    button.addEventListener("click", () => {
      const id = Number(button.getAttribute("data-step-id"));
      state.activeStepId = id;
      render();
    });
  });

  root.querySelectorAll("[data-xai-level]").forEach((button) => {
    button.addEventListener("click", () => {
      state.showXaiLevel = Number(button.getAttribute("data-xai-level"));
      render();
    });
  });

  root.querySelectorAll("[data-console-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.getAttribute("data-console-action");

      if (action === "toggle-auth") {
        state.isAuthorized = !state.isAuthorized;
        render();
        return;
      }

      if (action === "isolate-valve") {
        if (state.isAuthorized) {
          console.log("[Control Console] isolating V-101");
        } else {
          state.isAuthorized = true;
          render();
        }
        return;
      }

      console.log(`[Control Console] ${action}`);
    });
  });
}

function tick() {
  state.pressure = Number((state.pressure + (Math.random() - 0.5) * 0.1).toFixed(2));
  state.temp = Number((state.temp + (Math.random() - 0.5) * 0.2).toFixed(1));
  state.aiConfidence = Math.max(
    92,
    Math.min(99, Number((state.aiConfidence + (Math.random() - 0.5) * 0.6).toFixed(0))),
  );
  render();
}

render();
setInterval(tick, 2000);
