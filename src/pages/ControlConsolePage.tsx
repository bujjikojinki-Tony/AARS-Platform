import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Cpu,
  Layers,
  Lock,
  Radar,
  Shield,
  Sparkles,
  TrendingUp,
  Unlock,
  Zap,
} from "lucide-react";

type ProcedureStepStatus = "completed" | "active" | "pending";

type ProcedureStep = {
  id: number;
  title: string;
  status: ProcedureStepStatus;
  logic: string;
};

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
  ] satisfies ProcedureStep[],
};

const XAI_LEVELS = [
  {
    id: 1,
    label: "结论",
    description: "直接可执行的建议",
  },
  {
    id: 2,
    label: "证据",
    description: "传感器与逻辑链路",
  },
  {
    id: 3,
    label: "推演",
    description: "未来态势与风险拐点",
  },
] as const;

const ALERTS = [
  {
    level: "critical",
    label: "RWST 液位低限触发",
    time: "02:14:05",
  },
  {
    level: "warning",
    label: "辅助供水流量异常",
    time: "02:15:21",
  },
  {
    level: "info",
    label: "柴油发电机 1A 已加载",
    time: "02:13:58",
  },
] as const;

const TREND_POINTS = [40, 45, 52, 60, 58, 55, 48, 42, 38, 35, 32, 30];

const SKETCH_LANES = [
  {
    title: "过程层",
    note: "步骤、状态、分支都被固定在规程脊柱上。",
  },
  {
    title: "证据层",
    note: "把 XAI 解释和物理信号挂在同一视图上。",
  },
  {
    title: "控制层",
    note: "只暴露当前被允许的最小动作集合。",
  },
  {
    title: "记录层",
    note: "围绕主界面的上下文以卡片方式展开。",
  },
] as const;

function clamp(value: number, min: number, max: number) {
  return Math.max(min, Math.min(max, value));
}

function ProcedureSpineIcon() {
  return (
    <svg
      aria-hidden="true"
      className="sketch-radar"
      viewBox="0 0 100 100"
      role="img"
    >
      <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(125, 211, 252, 0.35)" strokeWidth="0.8" />
      <circle cx="50" cy="50" r="30" fill="none" stroke="rgba(148, 163, 184, 0.4)" strokeWidth="0.8" strokeDasharray="2 2" />
      {[0, 72, 144, 216, 288].map((deg) => (
        <line
          key={deg}
          x1="50"
          y1="50"
          x2={50 + 45 * Math.cos((deg * Math.PI) / 180)}
          y2={50 + 45 * Math.sin((deg * Math.PI) / 180)}
          stroke="rgba(148, 163, 184, 0.35)"
          strokeWidth="0.8"
        />
      ))}
      <polygon
        points="50,15 80,40 75,70 50,85 25,70 20,40"
        fill="rgba(34, 197, 94, 0.16)"
        stroke="rgba(34, 197, 94, 0.8)"
        strokeWidth="1.2"
      />
    </svg>
  );
}

export function ControlConsolePage() {
  const [activeStepId, setActiveStepId] = useState(3);
  const [showXaiLevel, setShowXaiLevel] = useState(1);
  const [isAuthorized, setIsAuthorized] = useState(false);
  const [pressure, setPressure] = useState(15.2);
  const [temp, setTemp] = useState(312.4);
  const [aiConfidence, setAiConfidence] = useState(96);

  const activeStep =
    PROCEDURE_DATA.steps.find((step) => step.id === activeStepId) ??
    PROCEDURE_DATA.steps[2];

  useEffect(() => {
    let nextPressure = pressure;
    let nextTemp = temp;
    let nextConfidence = aiConfidence;

    const interval = window.setInterval(() => {
      nextPressure = clamp(
        Number((nextPressure + (Math.random() - 0.5) * 0.08).toFixed(2)),
        14.6,
        16.1,
      );
      nextTemp = clamp(
        Number((nextTemp + (Math.random() - 0.5) * 0.2).toFixed(1)),
        309.5,
        314.5,
      );
      nextConfidence = clamp(
        Number((nextConfidence + (Math.random() - 0.5) * 0.6).toFixed(0)),
        92,
        99,
      );

      setPressure(nextPressure);
      setTemp(nextTemp);
      setAiConfidence(nextConfidence);
    }, 2000);

    return () => window.clearInterval(interval);
  }, []);

  return (
    <div className="procedure-sketch-shell">
      <style>{`
        :root {
          color-scheme: dark;
        }

        .procedure-sketch-shell {
          position: relative;
          min-height: 100vh;
          overflow: hidden;
          padding: 24px;
          background:
            radial-gradient(circle at top left, rgba(56, 189, 248, 0.18), transparent 28%),
            radial-gradient(circle at 86% 18%, rgba(99, 102, 241, 0.16), transparent 24%),
            linear-gradient(180deg, #0b1020 0%, #0f172a 45%, #070b16 100%);
          color: #e2e8f0;
          font-family: "Inter", "Segoe UI", system-ui, sans-serif;
        }

        .procedure-sketch-shell::before {
          content: "";
          position: absolute;
          inset: 0;
          background-image:
            linear-gradient(rgba(148, 163, 184, 0.08) 1px, transparent 1px),
            linear-gradient(90deg, rgba(148, 163, 184, 0.08) 1px, transparent 1px);
          background-size: 120px 120px;
          mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.72), transparent 90%);
          pointer-events: none;
        }

        .sketch-shell {
          position: relative;
          z-index: 1;
          display: grid;
          gap: 18px;
          max-width: 1480px;
          margin: 0 auto;
        }

        .top-banner,
        .sketch-card,
        .footer-bar,
        .sketch-canvas,
        .sketch-chip,
        .sketch-prompt {
          border: 1px solid rgba(148, 163, 184, 0.18);
          background: rgba(15, 23, 42, 0.74);
          backdrop-filter: blur(18px);
          box-shadow: 0 20px 60px rgba(2, 6, 23, 0.3);
        }

        .top-banner {
          position: sticky;
          top: 16px;
          z-index: 4;
          display: grid;
          gap: 18px;
          padding: 20px 22px;
          border-radius: 28px;
        }

        .banner-meta,
        .banner-title-row,
        .footer-bar,
        .tool-row,
        .stat-row,
        .chip-row,
        .sketch-tabs {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          align-items: center;
          justify-content: space-between;
        }

        .eyebrow,
        .mini-label,
        .section-label,
        .metric-label,
        .sketch-caption,
        .sketch-subtitle {
          font-size: 0.74rem;
          letter-spacing: 0.18em;
          text-transform: uppercase;
          color: #94a3b8;
          font-family: "SF Mono", "Menlo", monospace;
        }

        .page-title {
          margin: 0;
          font-size: clamp(2rem, 4vw, 4.4rem);
          line-height: 0.98;
          letter-spacing: -0.05em;
        }

        .page-subtitle,
        .card-copy,
        .sketch-body,
        .panel-text,
        .list-text {
          margin: 0;
          color: #cbd5e1;
          line-height: 1.6;
        }

        .chip-row,
        .status-row {
          justify-content: flex-start;
        }

        .sketch-chip {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          padding: 8px 12px;
          border-radius: 999px;
          font-size: 0.78rem;
          color: #e2e8f0;
        }

        .sketch-chip--accent {
          background: rgba(59, 130, 246, 0.12);
          border-color: rgba(59, 130, 246, 0.24);
        }

        .sketch-chip--warning {
          background: rgba(245, 158, 11, 0.12);
          border-color: rgba(245, 158, 11, 0.24);
        }

        .sketch-chip--ok {
          background: rgba(34, 197, 94, 0.1);
          border-color: rgba(34, 197, 94, 0.24);
        }

        .sketch-layout {
          display: grid;
          grid-template-columns: minmax(290px, 0.82fr) minmax(0, 1.45fr) minmax(300px, 0.95fr);
          gap: 18px;
          align-items: start;
        }

        .stack {
          display: grid;
          gap: 18px;
        }

        .sketch-card {
          position: relative;
          overflow: hidden;
          border-radius: 24px;
        }

        .sketch-card::after {
          content: "";
          position: absolute;
          inset: auto -40px -80px auto;
          width: 180px;
          height: 180px;
          border-radius: 50%;
          background: radial-gradient(circle, rgba(125, 211, 252, 0.08), transparent 68%);
          pointer-events: none;
        }

        .card-header {
          display: grid;
          gap: 8px;
          margin-bottom: 16px;
        }

        .card-title {
          margin: 0;
          font-size: clamp(1.15rem, 2vw, 1.8rem);
          line-height: 1.05;
          letter-spacing: -0.04em;
        }

        .identity-meta,
        .panel-block,
        .callout-panel,
        .signal-panel {
          padding: 16px;
          border-radius: 18px;
          border: 1px solid rgba(148, 163, 184, 0.16);
          background: rgba(15, 23, 42, 0.52);
        }

        .metric-row,
        .bullet-list,
        .tool-list {
          display: grid;
          gap: 12px;
        }

        .metric-row {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .bullet-item {
          padding: 14px 0;
          border-top: 1px solid rgba(148, 163, 184, 0.12);
        }

        .bullet-item:first-child {
          border-top: 0;
          padding-top: 0;
        }

        .bullet-title {
          font-weight: 600;
          color: #f8fafc;
        }

        .bullet-note {
          margin-top: 4px;
          color: #94a3b8;
          font-size: 0.92rem;
          line-height: 1.55;
        }

        .step-card {
          display: grid;
          gap: 10px;
          width: 100%;
          padding: 16px;
          border: 1px solid rgba(148, 163, 184, 0.16);
          border-radius: 18px;
          background: rgba(2, 6, 23, 0.42);
          color: inherit;
          text-align: left;
          cursor: pointer;
          transition:
            transform 180ms ease,
            border-color 180ms ease,
            background 180ms ease;
        }

        .step-card:hover,
        .step-card:focus-visible {
          transform: translateY(-1px);
          border-color: rgba(125, 211, 252, 0.28);
          background: rgba(15, 23, 42, 0.74);
          outline: 0;
        }

        .step-card--completed {
          opacity: 0.88;
        }

        .step-card--active {
          border-color: rgba(59, 130, 246, 0.42);
          background: linear-gradient(180deg, rgba(37, 99, 235, 0.14), rgba(15, 23, 42, 0.64));
          box-shadow: inset 0 0 0 1px rgba(59, 130, 246, 0.12);
        }

        .step-head {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 12px;
        }

        .step-index {
          display: inline-flex;
          width: 30px;
          height: 30px;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          background: rgba(59, 130, 246, 0.16);
          color: #bfdbfe;
          font-size: 0.8rem;
          font-family: "SF Mono", "Menlo", monospace;
        }

        .step-index--done {
          background: rgba(34, 197, 94, 0.16);
          color: #bbf7d0;
        }

        .sketch-tag {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 4px 10px;
          border-radius: 999px;
          background: rgba(148, 163, 184, 0.12);
          color: #cbd5e1;
          font-size: 0.7rem;
          letter-spacing: 0.12em;
          text-transform: uppercase;
        }

        .sketch-canvas {
          position: relative;
          min-height: 920px;
          padding: 18px;
          border-radius: 30px;
        }

        .canvas-grid {
          position: relative;
          min-height: 884px;
          display: grid;
          grid-template-columns: repeat(12, minmax(0, 1fr));
          grid-template-rows: repeat(12, minmax(0, 1fr));
          gap: 14px;
        }

        .canvas-annotation {
          display: grid;
          gap: 6px;
          padding: 14px;
          border-radius: 18px;
          border: 1px dashed rgba(148, 163, 184, 0.28);
          background: rgba(15, 23, 42, 0.52);
        }

        .canvas-annotation--top-left {
          grid-column: 1 / span 3;
          grid-row: 1 / span 3;
        }

        .canvas-annotation--top-right {
          grid-column: 10 / span 3;
          grid-row: 1 / span 3;
        }

        .canvas-annotation--bottom-left {
          grid-column: 1 / span 3;
          grid-row: 10 / span 3;
        }

        .canvas-annotation--bottom-right {
          grid-column: 10 / span 3;
          grid-row: 10 / span 3;
        }

        .screen-shell {
          grid-column: 4 / span 6;
          grid-row: 2 / span 10;
          display: grid;
          gap: 14px;
          align-content: start;
          padding: 22px;
          border-radius: 28px;
          border: 1px solid rgba(59, 130, 246, 0.22);
          background:
            linear-gradient(180deg, rgba(15, 23, 42, 0.96), rgba(2, 6, 23, 0.82)),
            radial-gradient(circle at top, rgba(59, 130, 246, 0.14), transparent 44%);
          box-shadow:
            0 0 0 1px rgba(148, 163, 184, 0.06),
            0 24px 70px rgba(2, 6, 23, 0.38);
        }

        .screen-topline {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          justify-content: space-between;
          align-items: center;
        }

        .screen-title {
          margin: 0;
          font-size: clamp(1.8rem, 2.8vw, 3rem);
          line-height: 1;
          letter-spacing: -0.05em;
        }

        .screen-grid {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
          gap: 12px;
        }

        .screen-panel {
          padding: 14px;
          border-radius: 18px;
          border: 1px solid rgba(148, 163, 184, 0.14);
          background: rgba(15, 23, 42, 0.44);
        }

        .screen-panel--wide {
          grid-column: span 2;
        }

        .screen-flow {
          display: grid;
          gap: 10px;
          padding: 16px;
          border-radius: 20px;
          border: 1px solid rgba(148, 163, 184, 0.12);
          background: rgba(2, 6, 23, 0.36);
        }

        .flow-track {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
          align-items: center;
        }

        .flow-node {
          display: grid;
          gap: 8px;
          padding: 12px;
          border-radius: 16px;
          border: 1px solid rgba(148, 163, 184, 0.14);
          background: rgba(15, 23, 42, 0.54);
          text-align: center;
        }

        .flow-node--active {
          border-color: rgba(59, 130, 246, 0.34);
          background: rgba(37, 99, 235, 0.14);
        }

        .flow-arrow {
          color: #60a5fa;
          display: flex;
          justify-content: center;
        }

        .xai-tabs {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }

        .xai-tab {
          appearance: none;
          border: 1px solid rgba(148, 163, 184, 0.18);
          background: rgba(15, 23, 42, 0.56);
          color: #cbd5e1;
          border-radius: 999px;
          padding: 8px 12px;
          font: inherit;
          cursor: pointer;
        }

        .xai-tab--active {
          color: #eff6ff;
          border-color: rgba(59, 130, 246, 0.34);
          background: rgba(37, 99, 235, 0.16);
        }

        .evidence-box {
          display: grid;
          gap: 10px;
          padding: 14px;
          border-radius: 18px;
          border: 1px solid rgba(148, 163, 184, 0.14);
          background: rgba(2, 6, 23, 0.34);
        }

        .action-button-grid {
          display: grid;
          gap: 10px;
        }

        .action-button {
          appearance: none;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          gap: 8px;
          min-height: 54px;
          padding: 14px 16px;
          border-radius: 16px;
          border: 1px solid rgba(148, 163, 184, 0.18);
          background: rgba(15, 23, 42, 0.58);
          color: #e2e8f0;
          font: inherit;
          font-weight: 600;
          cursor: pointer;
          transition:
            transform 180ms ease,
            border-color 180ms ease,
            background 180ms ease;
        }

        .action-button:hover,
        .action-button:focus-visible {
          transform: translateY(-1px);
          border-color: rgba(125, 211, 252, 0.28);
          background: rgba(30, 41, 59, 0.9);
          outline: 0;
        }

        .action-button--primary {
          border-color: rgba(59, 130, 246, 0.32);
          background: rgba(37, 99, 235, 0.16);
        }

        .footer-bar {
          position: sticky;
          bottom: 16px;
          z-index: 3;
          padding: 16px 18px;
          border-radius: 22px;
        }

        .footer-group {
          display: flex;
          flex-wrap: wrap;
          gap: 12px;
          align-items: center;
        }

        .pulse {
          width: 10px;
          height: 10px;
          border-radius: 999px;
          background: #22c55e;
          box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.6);
          animation: pulse 1.8s infinite;
        }

        .sketch-radar {
          width: 140px;
          height: 140px;
          filter: drop-shadow(0 0 20px rgba(59, 130, 246, 0.18));
        }

        .center-note {
          display: grid;
          gap: 6px;
          padding: 14px;
          border-radius: 18px;
          border-left: 4px solid rgba(59, 130, 246, 0.8);
          background: linear-gradient(135deg, rgba(37, 99, 235, 0.14), rgba(15, 23, 42, 0.52));
        }

        .center-note p {
          margin: 0;
          color: #dbeafe;
          line-height: 1.55;
        }

        @keyframes pulse {
          0% {
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.45);
          }

          70% {
            box-shadow: 0 0 0 14px rgba(34, 197, 94, 0);
          }

          100% {
            box-shadow: 0 0 0 0 rgba(34, 197, 94, 0);
          }
        }

        @media (max-width: 1200px) {
          .sketch-layout {
            grid-template-columns: 1fr;
          }

          .sketch-canvas {
            min-height: auto;
          }

          .canvas-grid {
            min-height: auto;
            grid-template-columns: 1fr;
            grid-template-rows: auto;
          }

          .canvas-annotation,
          .screen-shell {
            grid-column: auto;
            grid-row: auto;
          }

          .screen-shell {
            order: 0;
          }
        }

        @media (max-width: 720px) {
          .procedure-sketch-shell {
            padding: 12px;
          }

          .top-banner,
          .sketch-card,
          .sketch-canvas,
          .footer-bar {
            border-radius: 20px;
          }

          .screen-grid,
          .metric-row,
          .flow-track {
            grid-template-columns: 1fr;
          }

          .screen-panel--wide {
            grid-column: span 1;
          }
        }
      `}</style>

      <div className="sketch-shell">
        <section className="top-banner" aria-label="Procedure sketch header">
          <div className="banner-meta">
            <div className="eyebrow">AARS Runtime MVP / Control Console Sketch</div>
            <div className="chip-row">
              <span className="sketch-chip sketch-chip--accent">
                <Shield className="h-4 w-4" />
                规程集 {PROCEDURE_DATA.id}
              </span>
              <span className="sketch-chip sketch-chip--warning">
                <Sparkles className="h-4 w-4" />
                草图模式
              </span>
              <span className="sketch-chip sketch-chip--ok">
                <Cpu className="h-4 w-4" />
                AI-CPS Online
              </span>
            </div>
          </div>

          <div className="banner-title-row">
            <div className="stack" style={{ maxWidth: "980px" }}>
              <h1 className="page-title">计算机化规程系统界面草图</h1>
              <p className="page-subtitle">
                这是一个围绕核心规程屏幕展开的草图式控制台：左侧是规程脊柱，中间是主界面，
                右侧是证据、控制和报警。布局刻意保持“环绕式”关系，便于快速理解操作边界。
              </p>
              <div className="status-row">
                <span className="sketch-chip sketch-chip--accent">流程态：{activeStep.title}</span>
                <span className="sketch-chip sketch-chip--warning">授权态：{isAuthorized ? "已开放" : "待授权"}</span>
                <span className="sketch-chip sketch-chip--ok">AI 置信度：{aiConfidence}%</span>
              </div>
            </div>

            <div className="sketch-card" style={{ padding: "16px", minWidth: "280px" }}>
              <div className="mini-label">当前聚焦</div>
              <p className="card-copy" style={{ marginTop: "8px" }}>
                {activeStep.logic}
              </p>
            </div>
          </div>
        </section>

        <div className="sketch-layout">
          <aside className="stack" aria-label="Procedure spine">
            <section className="sketch-card" style={{ padding: "18px" }}>
              <div className="card-header">
                <div className="section-label">规程脊柱</div>
                <h2 className="card-title">步骤驱动的执行线</h2>
              </div>
              <ProcedureSpineIcon />
              <div className="bullet-list" style={{ marginTop: "16px" }}>
                {PROCEDURE_DATA.steps.map((step) => {
                  const isActive = step.id === activeStepId;
                  const isCompleted = step.status === "completed";

                  return (
                    <button
                      key={step.id}
                      type="button"
                      className={`step-card ${isActive ? "step-card--active" : ""}`}
                      onClick={() => {
                        setActiveStepId(step.id);
                      }}
                    >
                      <div className="step-head">
                        <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                          <span className={`step-index ${isCompleted ? "step-index--done" : ""}`}>
                            {isCompleted ? <CheckCircle2 className="h-4 w-4" /> : step.id}
                          </span>
                          <div>
                            <div className="bullet-title">{step.title}</div>
                            <div className="bullet-note">{step.logic}</div>
                          </div>
                        </div>
                        <span className="sketch-tag">{isActive ? "执行中" : step.status}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </section>

            <section className="sketch-card" style={{ padding: "18px" }}>
              <div className="card-header">
                <div className="section-label">过程状态</div>
                <h2 className="card-title">边界、压力和温度</h2>
              </div>

              <div className="metric-row">
                <div className="identity-meta">
                  <div className="mini-label">一回路压力</div>
                  <p className="card-copy">{pressure.toFixed(2)} MPa</p>
                </div>
                <div className="identity-meta">
                  <div className="mini-label">堆芯温度</div>
                  <p className="card-copy">{temp.toFixed(1)} °C</p>
                </div>
              </div>

              <div className="panel-block" style={{ marginTop: "14px" }}>
                <div className="mini-label">规程摘要</div>
                <p className="card-copy">
                  当前页面不是完整流程引擎，而是一个围绕核心规程界面的操作草图，优先展示什么在中间、
                  什么在周围、什么不应该越界。
                </p>
              </div>
            </section>
          </aside>

          <main className="sketch-canvas" aria-label="Central procedure sketch canvas">
            <div className="canvas-grid">
              <article className="canvas-annotation canvas-annotation--top-left">
                <div className="mini-label">流程层</div>
                <div className="bullet-title">{SKETCH_LANES[0].title}</div>
                <div className="panel-text">{SKETCH_LANES[0].note}</div>
              </article>

              <article className="canvas-annotation canvas-annotation--top-right">
                <div className="mini-label">证据层</div>
                <div className="bullet-title">{SKETCH_LANES[1].title}</div>
                <div className="panel-text">{SKETCH_LANES[1].note}</div>
              </article>

              <article className="canvas-annotation canvas-annotation--bottom-left">
                <div className="mini-label">控制层</div>
                <div className="bullet-title">{SKETCH_LANES[2].title}</div>
                <div className="panel-text">{SKETCH_LANES[2].note}</div>
              </article>

              <article className="canvas-annotation canvas-annotation--bottom-right">
                <div className="mini-label">记录层</div>
                <div className="bullet-title">{SKETCH_LANES[3].title}</div>
                <div className="panel-text">{SKETCH_LANES[3].note}</div>
              </article>

              <section className="screen-shell" aria-labelledby="screen-title">
                <div className="screen-topline">
                  <div className="stack" style={{ gap: "8px" }}>
                    <div className="section-label">核心界面</div>
                    <h2 className="screen-title" id="screen-title">
                      {PROCEDURE_DATA.title}
                    </h2>
                  </div>
                  <div className="chip-row">
                    <span className="sketch-chip sketch-chip--accent">
                      <Radar className="h-4 w-4" />
                      主视图
                    </span>
                    <span className="sketch-chip sketch-chip--warning">
                      <Lock className="h-4 w-4" />
                      {isAuthorized ? "授权打开" : "锁定"}
                    </span>
                  </div>
                </div>

                <div className="center-note">
                  <div className="mini-label">当前步骤</div>
                  <p>
                    {activeStep.id}. {activeStep.title}
                  </p>
                  <p className="card-copy">{activeStep.logic}</p>
                </div>

                <div className="screen-grid">
                  <div className="screen-panel">
                    <div className="mini-label">执行形态</div>
                    <p className="card-copy" style={{ marginTop: "8px" }}>
                      由规程步骤、状态、和授权状态共同决定当前可见操作。
                    </p>
                  </div>
                  <div className="screen-panel">
                    <div className="mini-label">AI 建议</div>
                    <p className="card-copy" style={{ marginTop: "8px" }}>
                      聚焦 {activeStep.title}，确认边界信号后再前进。
                    </p>
                  </div>
                  <div className="screen-panel screen-panel--wide">
                    <div className="mini-label">流转路径</div>
                    <div className="screen-flow" style={{ marginTop: "10px" }}>
                      <div className="flow-track">
                        <div className={`flow-node ${activeStepId >= 1 ? "flow-node--active" : ""}`}>
                          <span className="metric-label">01</span>
                          <strong>验证</strong>
                        </div>
                        <div className="flow-arrow">
                          <ArrowRight className="h-5 w-5" />
                        </div>
                        <div className={`flow-node ${activeStepId >= 3 ? "flow-node--active" : ""}`}>
                          <span className="metric-label">02</span>
                          <strong>核实</strong>
                        </div>
                        <div className="flow-arrow">
                          <ArrowRight className="h-5 w-5" />
                        </div>
                        <div className={`flow-node ${activeStepId >= 4 ? "flow-node--active" : ""}`}>
                          <span className="metric-label">03</span>
                          <strong>处置</strong>
                        </div>
                        <div className="flow-arrow">
                          <ArrowRight className="h-5 w-5" />
                        </div>
                        <div className={`flow-node ${activeStepId >= 5 ? "flow-node--active" : ""}`}>
                          <span className="metric-label">04</span>
                          <strong>记录</strong>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="evidence-box">
                  <div className="screen-topline">
                    <div>
                      <div className="mini-label">XAI 证据点</div>
                      <p className="card-copy" style={{ marginTop: "8px" }}>
                        选择一个解释层，把建议、证据和趋势分开看。
                      </p>
                    </div>
                    <div className="xai-tabs">
                      {XAI_LEVELS.map((level) => (
                        <button
                          key={level.id}
                          type="button"
                          className={`xai-tab ${showXaiLevel === level.id ? "xai-tab--active" : ""}`}
                          title={level.description}
                          onClick={() => {
                            setShowXaiLevel(level.id);
                          }}
                        >
                          {level.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {showXaiLevel === 1 ? (
                    <div className="stack">
                      <div className="bullet-title">结论</div>
                      <p className="card-copy">
                        检测到安注系统启动后的次生异常，建议优先核实阀门隔离状态并保持当前注水流量。
                      </p>
                      <div className="chip-row" style={{ justifyContent: "flex-start" }}>
                        <span className="sketch-chip sketch-chip--ok">预期收益 +15.4%</span>
                        <span className="sketch-chip sketch-chip--accent">规程约束已对齐</span>
                      </div>
                    </div>
                  ) : null}

                  {showXaiLevel === 2 ? (
                    <div className="stack">
                      <div className="bullet-item">
                        <div className="bullet-title">FI-203 反向压差信号</div>
                        <div className="bullet-note">传感器提示系统正在偏离预期流向。</div>
                      </div>
                      <div className="bullet-item">
                        <div className="bullet-title">V-101 阀门全开位</div>
                        <div className="bullet-note">P&amp;ID 逻辑验证显示存在非计划开位。</div>
                      </div>
                    </div>
                  ) : null}

                  {showXaiLevel === 3 ? (
                    <div className="stack">
                      <div className="bullet-title">未来 15 分钟趋势</div>
                      <div className="screen-flow">
                        <div className="flow-track" style={{ alignItems: "end", gridTemplateColumns: "repeat(12, minmax(0, 1fr))" }}>
                          {TREND_POINTS.map((height, index) => (
                            <div key={`${height}-${index}`} style={{ position: "relative", height: "110px" }}>
                              <div
                                style={{
                                  position: "absolute",
                                  inset: "auto 0 0 0",
                                  height: `${height}%`,
                                  borderRadius: "8px 8px 0 0",
                                  background:
                                    index < 3
                                      ? "rgba(148, 163, 184, 0.24)"
                                      : "rgba(59, 130, 246, 0.44)",
                                }}
                              />
                              {index === 3 ? (
                                <div
                                  style={{
                                    position: "absolute",
                                    inset: "0",
                                    borderTop: "2px solid rgba(239, 68, 68, 0.95)",
                                    animation: "pulse 1.8s infinite",
                                  }}
                                />
                              ) : null}
                            </div>
                          ))}
                        </div>
                        <div className="chip-row" style={{ justifyContent: "space-between" }}>
                          <span className="mini-label">当前</span>
                          <span className="mini-label">建议执行点</span>
                          <span className="mini-label">未来 15min</span>
                        </div>
                      </div>
                    </div>
                  ) : null}
                </div>
              </section>
            </div>
          </main>

          <aside className="stack" aria-label="Evidence and control rail">
            <section className="sketch-card" style={{ padding: "18px" }}>
              <div className="card-header">
                <div className="section-label">报警与上下文</div>
                <h2 className="card-title">围绕主界面的信号窗口</h2>
              </div>

              <div className="tool-list">
                {ALERTS.map((alert) => (
                  <div
                    key={`${alert.label}-${alert.time}`}
                    className="identity-meta"
                    style={{
                      borderColor:
                        alert.level === "critical"
                          ? "rgba(239, 68, 68, 0.2)"
                          : alert.level === "warning"
                            ? "rgba(245, 158, 11, 0.2)"
                            : "rgba(148, 163, 184, 0.14)",
                    }}
                  >
                    <div className="screen-topline" style={{ alignItems: "flex-start" }}>
                      <div>
                        <div className="bullet-title">
                          {alert.level === "critical" ? <AlertTriangle className="inline-block h-4 w-4 text-red-400" /> : null}
                          {alert.level === "warning" ? <AlertTriangle className="inline-block h-4 w-4 text-amber-400" /> : null}
                          {alert.level === "info" ? <Activity className="inline-block h-4 w-4 text-slate-400" /> : null}
                          <span style={{ marginLeft: "8px" }}>{alert.label}</span>
                        </div>
                        <div className="bullet-note">{alert.time}</div>
                      </div>
                      <span className="sketch-tag">{alert.level}</span>
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="sketch-card" style={{ padding: "18px" }}>
              <div className="card-header">
                <div className="section-label">操作区</div>
                <h2 className="card-title">仅暴露当前可允许动作</h2>
              </div>

              <div className="stack">
                <div className="identity-meta">
                  <div className="mini-label">授权状态</div>
                  <p className="card-copy" style={{ marginTop: "8px" }}>
                    {isAuthorized
                      ? "授权成功，软控制按钮可用。"
                      : "尚未授权，需先展开证据层。"}
                  </p>
                </div>

                <button
                  type="button"
                  className={`action-button ${isAuthorized ? "action-button--primary" : ""}`}
                  onClick={() => {
                    setIsAuthorized(!isAuthorized);
                  }}
                >
                  {isAuthorized ? <Unlock className="h-4 w-4" /> : <Lock className="h-4 w-4" />}
                  {isAuthorized ? "撤销授权" : "解锁规程"}
                </button>

                <button
                  type="button"
                  className="action-button"
                  onClick={() => {
                    if (!isAuthorized) {
                      setIsAuthorized(true);
                      return;
                    }

                    console.log("[Control Console] isolate procedure branch");
                  }}
                >
                  <CheckCircle2 className="h-4 w-4" />
                  生成当前工况摘要
                </button>

                <button
                  type="button"
                  className="action-button"
                  onClick={() => {
                    console.log("[Control Console] fallback to paper procedure");
                  }}
                >
                  <Layers className="h-4 w-4" />
                  降级到纸质模式
                </button>
              </div>
            </section>

            <section className="sketch-card" style={{ padding: "18px" }}>
              <div className="card-header">
                <div className="section-label">草图说明</div>
                <h2 className="card-title">这个布局在说什么</h2>
              </div>
              <p className="card-copy">
                我把中心屏幕保留为唯一主焦点，四周只放上下文卡片，避免像常规仪表盘那样把信息铺满。
                这更接近规程系统的操作方式：先确认步骤，再核对证据，最后才允许动作。
              </p>
              <div className="panel-block" style={{ marginTop: "14px" }}>
                <div className="mini-label">设计语义</div>
                <div className="bullet-note" style={{ marginTop: "8px" }}>
                  <Zap className="inline-block h-4 w-4 text-sky-300" /> 中心是一条规程屏幕，而不是一个统计面板。
                </div>
                <div className="bullet-note">
                  <TrendingUp className="inline-block h-4 w-4 text-sky-300" /> 周围卡片是上下文环，不是独立页面。
                </div>
              </div>
            </section>
          </aside>
        </div>

        <footer className="footer-bar" aria-label="Procedure sketch footer">
          <div className="footer-group">
            <span className="pulse" aria-hidden="true" />
            <span className="metric-label">AI AGENT: ONLINE</span>
            <span className="sketch-chip sketch-chip--accent">规程屏幕聚焦</span>
            <span className="sketch-chip sketch-chip--ok">草图完成</span>
          </div>

          <div className="chip-row" style={{ justifyContent: "flex-end" }}>
            <button
              type="button"
              className="action-button"
              onClick={() => {
                console.log("[Control Console] export sketch note");
              }}
            >
              导出草图说明
            </button>
            <button
              type="button"
              className="action-button action-button--primary"
              onClick={() => {
                console.log("[Control Console] sync sketch to review");
              }}
            >
              同步到评审
            </button>
          </div>
        </footer>
      </div>
    </div>
  );
}
