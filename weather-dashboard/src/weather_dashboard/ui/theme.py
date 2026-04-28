from __future__ import annotations

import os

import streamlit as st


def render_theme() -> None:
    if os.getenv("WEATHER_DASHBOARD_LEGACY_THEME", "").lower() not in {"1", "true", "yes"}:
        st.markdown(
            """
            <style>
            :root {
                --desk-bg: #020305;
                --desk-bg-2: #070a0f;
                --desk-panel: rgba(12, 15, 20, 0.98);
                --desk-panel-strong: rgba(15, 18, 24, 0.99);
                --desk-line: rgba(255, 255, 255, 0.12);
                --desk-ink: #f7fbff;
                --desk-muted: #a3adb7;
                --desk-green: #69d39a;
                --desk-amber: #d7ab57;
                --desk-red: #d96d67;
                --desk-blue: #4f8fe6;
                --desk-alarm: #d96d67;
                --desk-anomaly: #d7ab57;
                --desk-quality-bad: #ff73e1;
                --desk-surface-soft: rgba(12, 15, 20, 0.94);
                --desk-surface-strong: rgba(15, 18, 24, 0.99);
                --desk-text-primary: #f7fbff;
                --desk-text-secondary: #a3adb7;
                --desk-text-tertiary: #72808e;
                --desk-border-soft: rgba(255, 255, 255, 0.08);
                --desk-border-strong: rgba(91, 148, 225, 0.28);
                --font-display: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
                --font-body: "Avenir Next", "SF Pro Text", "Segoe UI", "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", sans-serif;
                --font-serif: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
                --font-mono: "SF Mono", "Menlo", monospace;
                --type-xs: 0.62rem;
                --type-sm: 0.74rem;
                --type-base: 0.84rem;
                --type-md: 0.96rem;
                --type-lg: 1.08rem;
                --type-xl: 1.24rem;
                --type-hero: clamp(1.06rem, 1.38vw, 1.30rem);
                --leading-tight: 1.12;
                --leading-normal: 1.32;
                --tracking-label: 0.14em;
            }

            .stApp {
                background:
                    radial-gradient(circle at 8% 0%, rgba(79, 143, 230, 0.10), transparent 28%),
                    radial-gradient(circle at 92% 12%, rgba(105, 211, 154, 0.08), transparent 30%),
                    linear-gradient(180deg, #020305 0%, #070a0f 42%, #090c10 100%);
                color: var(--desk-ink);
                font-family: var(--font-body);
            }

            :root {
                --ops-bg: var(--desk-bg);
                --ops-bg-2: var(--desk-bg-2);
                --ops-surface: var(--desk-panel);
                --ops-surface-2: var(--desk-panel-strong);
                --ops-surface-3: rgba(25, 31, 41, 0.98);
                --ops-text: var(--desk-text-primary);
                --ops-text-muted: var(--desk-text-secondary);
                --ops-text-dim: var(--desk-text-tertiary);
                --ops-border: var(--desk-border-soft);
                --ops-border-strong: var(--desk-border-strong);
                --ops-accent: var(--desk-blue);
                --ops-accent-2: #3f6fa8;
                --ops-good: var(--desk-green);
                --ops-warn: var(--desk-amber);
                --ops-bad: var(--desk-alarm);
                --ops-quality-bad: var(--desk-quality-bad);
                --ops-alarm: var(--desk-alarm);
                --ops-anomaly: var(--desk-anomaly);
                --ops-font-display: var(--font-display);
                --ops-font-body: var(--font-body);
                --ops-font-mono: var(--font-mono);
            }

            .stApp,
            .stApp [data-testid="stAppViewContainer"],
            .stApp [data-testid="stAppViewContainer"] * {
                color: var(--desk-ink);
            }

            .stApp [data-testid="stHeader"],
            .stApp [data-testid="stToolbar"],
            .stApp [data-testid="stDecoration"],
            .stApp [data-testid="stStatusWidget"] {
                display: none !important;
                visibility: hidden !important;
            }

            .block-container {
                max-width: none;
                width: 100%;
                padding: 0.55rem 0.75rem 0.45rem;
            }

            section[data-testid="stSidebar"] {
                background: rgba(10, 13, 18, 0.98);
                border-right: 1px solid var(--desk-line);
            }

            .desk-shell,
            .market-overview-banner,
            .console-interaction-strip,
            .operator-closure-panel,
            .compact-info-card,
            .console-card,
            .monitor-card,
            .soft-control-card,
            .recent-market-card,
            .history-summary-card {
                border: 1px solid var(--desk-line);
                border-radius: 10px;
                background: var(--desk-panel);
                box-shadow: none;
            }

            .desk-title,
            .page-title,
            h1, h2, h3, h4 {
                color: var(--desk-ink);
                font-family: var(--font-display);
                letter-spacing: -0.01em;
                line-height: var(--leading-tight);
            }

            .desk-kicker,
            .eyebrow,
            .mini-label,
            .metric-label,
            .console-strip-title,
            .operator-closure-title,
            .compact-metric span,
            .compact-kv-row span,
            .compact-panel-subtitle,
            .section-label {
                color: var(--desk-muted);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 800;
                letter-spacing: var(--tracking-label);
                line-height: var(--leading-tight);
                text-transform: uppercase;
            }

            .desk-kicker {
                color: #e6c67c;
            }

            .desk-subtitle,
            .page-subtitle,
            .console-subtitle,
            .compact-panel-subtitle,
            .thin-evidence-line,
            .closure-detail,
            .compact-note {
                color: var(--desk-muted);
                font-size: var(--type-sm);
                line-height: var(--leading-normal);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        return

    if os.getenv("WEATHER_DASHBOARD_LEGACY_THEME", "").lower() not in {"1", "true", "yes"}:
        st.markdown(
            """
            <style>
            :root {
                --desk-bg: #f7f3e8;
                --desk-panel: rgba(255, 255, 255, 0.76);
                --desk-panel-strong: rgba(255, 255, 255, 0.92);
                --desk-line: rgba(35, 72, 82, 0.16);
                --desk-ink: #17252b;
                --desk-muted: #667782;
                --desk-green: #0f9f71;
                --desk-amber: #c47a15;
                --desk-red: #c44d46;
                --font-display: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
                --font-body: "Avenir Next", "Trebuchet MS", sans-serif;
                --font-serif: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
                --font-mono: "SF Mono", "Menlo", monospace;
                --type-xs: 0.62rem;
                --type-sm: 0.70rem;
                --type-base: 0.80rem;
                --type-md: 0.92rem;
                --type-lg: 1.06rem;
                --type-xl: 1.24rem;
                --type-hero: clamp(0.98rem, 1.34vw, 1.30rem);
                --leading-tight: 1.12;
                --leading-normal: 1.32;
                --tracking-label: 0.11em;
            }

            .stApp {
                background:
                    radial-gradient(circle at 8% 0%, rgba(214, 143, 52, 0.12), transparent 28%),
                    radial-gradient(circle at 92% 12%, rgba(15, 159, 113, 0.10), transparent 30%),
                    linear-gradient(135deg, #fbf7ec 0%, #eef5f1 48%, #f9f1dd 100%);
                color: var(--desk-ink);
                font-family: var(--font-body);
            }

            .block-container {
                max-width: none;
                width: 100%;
                padding: 0.55rem 0.75rem 0.4rem;
            }

            h1, h2, h3, h4 {
                color: var(--desk-ink);
                font-family: var(--font-display);
                letter-spacing: -0.01em;
                line-height: var(--leading-tight);
            }

            p, label, [data-testid="stMarkdownContainer"] {
                font-size: var(--type-base);
                line-height: var(--leading-normal);
            }

            section[data-testid="stSidebar"] {
                background: rgba(248, 245, 235, 0.96);
                border-right: 1px solid var(--desk-line);
            }

            .desk-shell,
            .market-overview-banner,
            .console-interaction-strip,
            .operator-closure-panel,
            .compact-info-card,
            .console-card,
            .monitor-card,
            .soft-control-card,
            .recent-market-card,
            .history-summary-card {
                border: 1px solid var(--desk-line);
                border-radius: 12px;
                background: var(--desk-panel);
                box-shadow: 0 10px 24px rgba(49, 77, 75, 0.07);
            }

            .desk-shell {
                padding: 0.44rem 0.64rem;
                margin-bottom: 0.28rem;
            }

            .desk-kicker,
            .eyebrow,
            .mini-label,
            .metric-label,
            .console-strip-title,
            .operator-closure-title,
            .compact-metric span,
            .compact-kv-row span,
            .compact-panel-subtitle,
            .section-label {
                color: var(--desk-muted);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 800;
                letter-spacing: var(--tracking-label);
                line-height: var(--leading-tight);
                text-transform: uppercase;
            }

            .desk-kicker {
                color: var(--desk-amber);
            }

            .desk-title,
            .page-title {
                margin: 0.04rem 0;
                color: #11282f;
                font-family: var(--font-display);
                font-size: var(--type-hero);
                font-weight: 900;
                line-height: 1.16;
            }

            .desk-subtitle,
            .page-subtitle,
            .console-subtitle,
            .compact-panel-subtitle,
            .thin-evidence-line,
            .closure-detail,
            .compact-note {
                color: var(--desk-muted);
                font-size: var(--type-sm);
                line-height: var(--leading-normal);
            }

            .console-interaction-strip,
            .market-overview-banner,
            .worker-health-strip,
            .unified-status-strip,
            .operator-context-badge,
            .compact-gate-stack,
            .operator-closure-panel {
                margin-bottom: 0.28rem;
                padding: 0.36rem 0.48rem;
            }

            .unified-status-strip,
            .operator-context-badge {
                border: 1px solid var(--desk-line);
                border-radius: 12px;
                background: linear-gradient(135deg, rgba(255,255,255,0.84), rgba(246,248,243,0.9));
                box-shadow: 0 10px 24px rgba(49, 77, 75, 0.06);
            }

            .unified-status-strip__title {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 0.4rem;
            }

            .unified-status-strip__title strong {
                color: var(--desk-ink);
                font-family: var(--font-display);
                font-size: var(--type-lg);
                line-height: var(--leading-tight);
            }

            .unified-status-strip__metrics {
                display: grid;
                grid-template-columns: repeat(8, minmax(0, 1fr));
                gap: 0.28rem;
                margin-top: 0.34rem;
            }

            .unified-status-strip__metrics div,
            .unified-status-strip__blockers {
                border: 1px solid var(--desk-line);
                border-radius: 10px;
                background: rgba(255,255,255,0.72);
                padding: 0.28rem 0.34rem;
            }

            .unified-status-strip__metrics span,
            .unified-status-strip__blockers span {
                color: var(--desk-muted);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 800;
                letter-spacing: var(--tracking-label);
                text-transform: uppercase;
            }

            .unified-status-strip__metrics strong,
            .unified-status-strip__blockers strong {
                display: block;
                margin-top: 0.12rem;
                color: var(--desk-ink);
                font-size: var(--type-sm);
                line-height: var(--leading-tight);
            }

            .unified-status-strip__blockers {
                margin-top: 0.32rem;
            }

            .operator-context-badge {
                background:
                    radial-gradient(circle at 8% 20%, rgba(205, 231, 129, 0.24), transparent 34%),
                    linear-gradient(135deg, rgba(255,255,255,0.9), rgba(241,247,238,0.86));
            }

            .operator-context-badge__title {
                display: flex;
                justify-content: space-between;
                gap: 0.4rem;
                align-items: center;
            }

            .operator-context-badge__title span,
            .operator-context-badge__grid span {
                color: var(--desk-muted);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 800;
                letter-spacing: var(--tracking-label);
                text-transform: uppercase;
            }

            .operator-context-badge__title strong {
                color: var(--desk-ink);
                font-family: var(--font-display);
                font-size: var(--type-md);
            }

            .operator-context-badge__grid {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.28rem;
                margin-top: 0.34rem;
            }

            .operator-context-badge__grid div {
                border: 1px solid var(--desk-line);
                border-radius: 10px;
                background: rgba(255,255,255,0.72);
                padding: 0.28rem 0.34rem;
            }

            .operator-context-badge__grid strong {
                display: block;
                margin-top: 0.12rem;
                color: var(--desk-ink);
                font-size: var(--type-sm);
                line-height: var(--leading-tight);
            }

            .operator-context-badge__footer {
                color: var(--desk-muted);
                font-size: var(--type-xs);
                margin-top: 0.3rem;
            }

            .pipeline-sync-context {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0.28rem;
                margin: 0.36rem 0;
            }

            .pipeline-sync-context div {
                border: 1px solid var(--desk-line);
                border-radius: 10px;
                background: rgba(255,255,255,0.72);
                padding: 0.28rem 0.34rem;
            }

            .pipeline-sync-context span {
                color: var(--desk-muted);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 800;
                letter-spacing: var(--tracking-label);
                text-transform: uppercase;
            }

            .pipeline-sync-context strong {
                display: block;
                margin-top: 0.12rem;
                color: var(--desk-ink);
                font-size: var(--type-sm);
                line-height: var(--leading-tight);
            }

            .compact-gate-stack__top {
                display: grid;
                grid-template-columns: minmax(0, 1fr) auto;
                gap: 0.4rem;
                align-items: center;
            }

            .compact-gate-stack__eyebrow,
            .compact-gate-stack__blockers,
            .compact-gate-stack__metrics span {
                color: var(--desk-muted);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 800;
                letter-spacing: var(--tracking-label);
                text-transform: uppercase;
            }

            .compact-gate-stack__title {
                color: var(--desk-ink);
                font-family: var(--font-display);
                font-size: var(--type-lg);
                font-weight: 950;
                line-height: var(--leading-tight);
            }

            .compact-gate-stack__status {
                padding: 0.18rem 0.46rem;
                border-radius: 999px;
                border: 1px solid var(--desk-line);
                background: rgba(255,255,255,0.76);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 900;
            }

            .compact-gate-stack__status--ready,
            .compact-gate-stack__status--dry_run_intent_ready {
                border-color: rgba(15, 159, 113, 0.28);
                background: rgba(15, 159, 113, 0.09);
            }

            .compact-gate-stack__status--blocked {
                border-color: rgba(196, 77, 70, 0.28);
                background: rgba(196, 77, 70, 0.09);
            }

            .compact-gate-stack__metrics {
                display: grid;
                grid-template-columns: repeat(7, minmax(0, 1fr));
                gap: 0.3rem;
                margin-top: 0.36rem;
            }

            .compact-gate-stack__metrics div {
                border: 1px solid var(--desk-line);
                border-radius: 10px;
                background: rgba(255,255,255,0.7);
                padding: 0.3rem 0.34rem;
            }

            .compact-gate-stack__metrics strong {
                display: block;
                margin-top: 0.12rem;
                color: var(--desk-ink);
                font-size: var(--type-sm);
                line-height: var(--leading-tight);
            }

            .compact-gate-stack__chips {
                display: flex;
                flex-wrap: wrap;
                gap: 0.22rem;
                margin-top: 0.34rem;
            }

            .compact-gate-chip {
                display: inline-flex;
                align-items: center;
                gap: 0.22rem;
                padding: 0.14rem 0.38rem;
                border-radius: 999px;
                border: 1px solid var(--desk-line);
                background: rgba(255,255,255,0.76);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                line-height: var(--leading-tight);
            }

            .compact-gate-chip--ok {
                border-color: rgba(15, 159, 113, 0.28);
                background: rgba(15, 159, 113, 0.09);
            }

            .compact-gate-chip--warn {
                border-color: rgba(196, 122, 21, 0.28);
                background: rgba(196, 122, 21, 0.10);
            }

            .compact-gate-chip--block {
                border-color: rgba(196, 77, 70, 0.28);
                background: rgba(196, 77, 70, 0.09);
            }

            .compact-gate-stack__blockers {
                margin-top: 0.34rem;
            }

            .worker-health-strip {
                display: grid;
                grid-template-columns: auto auto minmax(0, 1fr);
                gap: 0.38rem;
                align-items: center;
            }

            .worker-health-strip__title,
            .worker-health-strip__overall {
                color: var(--desk-muted);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 800;
                letter-spacing: var(--tracking-label);
                text-transform: uppercase;
            }

            .worker-health-strip__chips {
                display: flex;
                flex-wrap: wrap;
                gap: 0.24rem;
                justify-content: flex-end;
            }

            .worker-health-pill {
                display: inline-flex;
                align-items: center;
                gap: 0.3rem;
                padding: 0.18rem 0.42rem;
                border-radius: 999px;
                border: 1px solid var(--desk-line);
                background: rgba(255, 255, 255, 0.76);
                color: var(--desk-ink);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                line-height: var(--leading-tight);
            }

            .worker-health-pill em {
                color: var(--desk-muted);
                font-style: normal;
            }

            .worker-health-pill--healthy {
                border-color: rgba(15, 159, 113, 0.28);
                background: rgba(15, 159, 113, 0.09);
            }

            .worker-health-pill--warning {
                border-color: rgba(196, 122, 21, 0.28);
                background: rgba(196, 122, 21, 0.10);
            }

            .worker-health-pill--blocked {
                border-color: rgba(196, 77, 70, 0.34);
                background: rgba(196, 77, 70, 0.13);
            }

            .worker-health-pill--stale,
            .worker-health-pill--missing {
                border-color: rgba(196, 77, 70, 0.28);
                background: rgba(196, 77, 70, 0.09);
            }

            .flat-overview-row,
            .banner-meta {
                display: grid;
                grid-template-columns: minmax(0, 1fr) auto;
                gap: 0.55rem;
                align-items: center;
            }

            .flat-market-title strong {
                display: block;
                overflow: hidden;
                color: var(--desk-ink);
                font-family: var(--font-serif);
                font-size: var(--type-md);
                line-height: var(--leading-tight);
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .control-console-topline,
            .thin-status-strip,
            .console-strip-actions {
                display: flex;
                flex-wrap: wrap;
                gap: 0.25rem;
                align-items: center;
                justify-content: flex-end;
            }

            .control-chip,
            .console-pill,
            .status-pill,
            .thin-status-strip span,
            .step-badge {
                display: inline-flex;
                align-items: center;
                gap: 0.22rem;
                padding: 0.16rem 0.42rem;
                border: 1px solid var(--desk-line);
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.72);
                color: var(--desk-ink);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                line-height: var(--leading-tight);
            }

            .control-chip--ok,
            .state-authorized,
            .state-logged,
            .closure-card--ok,
            .status-pill--ok {
                border-color: rgba(15, 159, 113, 0.28);
                background: rgba(15, 159, 113, 0.09);
            }

            .control-chip--warning,
            .state-step,
            .state-xai,
            .closure-card--warning,
            .status-pill--warning {
                border-color: rgba(196, 122, 21, 0.28);
                background: rgba(196, 122, 21, 0.10);
            }

            .state-locked,
            .closure-card--critical,
            .status-pill--critical {
                border-color: rgba(196, 77, 70, 0.28);
                background: rgba(196, 77, 70, 0.09);
            }

            .operator-closure-grid {
                display: grid;
                grid-template-columns: repeat(5, minmax(0, 1fr));
                gap: 0.32rem;
            }

            .closure-card {
                display: grid;
                grid-template-columns: auto minmax(0, 1fr);
                gap: 0.32rem;
                min-width: 0;
                padding: 0.38rem 0.42rem;
                border: 1px solid var(--desk-line);
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.70);
            }

            .closure-card-index {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 1.28rem;
                height: 1.28rem;
                border-radius: 999px;
                background: rgba(17, 57, 92, 0.10);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 900;
            }

            .closure-question {
                overflow: hidden;
                color: var(--desk-muted);
                font-size: var(--type-xs);
                font-weight: 760;
                line-height: var(--leading-tight);
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .closure-answer {
                overflow: hidden;
                color: var(--desk-ink);
                font-family: var(--font-display);
                font-size: var(--type-md);
                font-weight: 900;
                line-height: var(--leading-tight);
                text-overflow: ellipsis;
                white-space: nowrap;
            }

            .compact-panel-heading {
                margin: 0.18rem 0 0.24rem;
            }

            .compact-panel-title {
                color: var(--desk-ink);
                font-family: var(--font-display);
                font-size: var(--type-lg);
                font-weight: 900;
                line-height: var(--leading-tight);
            }

            .compact-info-card {
                min-height: 100%;
                padding: 0.45rem 0.52rem;
            }

            .compact-metric {
                margin-bottom: 0.22rem;
            }

            .compact-metric strong {
                display: block;
                color: var(--desk-ink);
                font-family: var(--font-display);
                font-size: var(--type-xl);
                font-weight: 900;
                line-height: var(--leading-tight);
            }

            .compact-kv-section {
                display: grid;
                gap: 0.16rem;
                margin-top: 0.22rem;
            }

            .compact-kv-row {
                display: grid;
                grid-template-columns: minmax(7rem, 0.8fr) minmax(0, 1.2fr);
                gap: 0.42rem;
                align-items: baseline;
                padding: 0.11rem 0;
                border-bottom: 1px solid rgba(35, 72, 82, 0.08);
            }

            .compact-kv-row strong {
                min-width: 0;
                overflow-wrap: anywhere;
                color: var(--desk-ink);
                font-size: var(--type-sm);
                font-weight: 760;
            }

            .console-grid,
            .control-console-grid,
            .live-workbench-grid {
                display: grid;
                grid-template-columns: minmax(15rem, 0.9fr) minmax(0, 1.5fr);
                gap: 0.5rem;
                align-items: stretch;
            }

            .console-card,
            .monitor-card,
            .soft-control-card {
                padding: 0.46rem 0.52rem;
            }

            .step-list {
                display: grid;
                gap: 0.28rem;
            }

            .step-item {
                padding: 0.36rem 0.42rem;
                border: 1px solid var(--desk-line);
                border-radius: 10px;
                background: rgba(255,255,255,0.62);
            }

            .step-title {
                color: var(--desk-ink);
                font-size: var(--type-sm);
                font-weight: 840;
            }

            .step-meta,
            .step-body,
            .monitor-body,
            .soft-control-body {
                color: var(--desk-muted);
                font-size: var(--type-xs);
                line-height: var(--leading-normal);
            }

            div[data-testid="stTabs"] button {
                min-height: 2rem;
                color: var(--desk-muted);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 800;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }

            div[data-testid="stTabs"] [aria-selected="true"] {
                color: var(--desk-ink);
                border-bottom-color: var(--desk-green);
            }

            .stButton > button,
            div[data-testid="stDownloadButton"] button {
                min-height: 2rem;
                border: 1px solid var(--desk-line);
                border-radius: 999px;
                background: var(--desk-panel-strong);
                color: var(--desk-ink);
                font-family: var(--font-mono);
                font-size: var(--type-xs);
                font-weight: 800;
            }

            .stTextInput input,
            .stSelectbox div[data-baseweb="select"] > div,
            .stNumberInput input {
                border-color: var(--desk-line);
                border-radius: 10px;
                background: rgba(255, 255, 255, 0.90);
                color: var(--desk-ink);
                font-size: var(--type-sm);
            }

            [data-testid="stDataFrame"] {
                border: 1px solid var(--desk-line);
                border-radius: 12px;
                overflow: hidden;
            }

            .element-container {
                margin-bottom: 0.22rem;
            }

            hr {
                margin: 0.35rem 0;
                border-color: rgba(35, 72, 82, 0.14);
            }

            @media (max-width: 1100px) {
                .operator-closure-grid {
                    grid-template-columns: repeat(2, minmax(0, 1fr));
                }

                .console-grid,
                .control-console-grid,
                .live-workbench-grid {
                    grid-template-columns: minmax(0, 1fr);
                }
            }

            @media (max-width: 720px) {
                .block-container {
                    padding: 0.45rem 0.45rem 0.35rem;
                }

                .operator-closure-grid {
                    grid-template-columns: minmax(0, 1fr);
                }

                .flat-overview-row,
                .banner-meta {
                    grid-template-columns: minmax(0, 1fr);
                }

                .control-console-topline,
                .thin-status-strip,
                .console-strip-actions {
                    justify-content: flex-start;
                }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        """
        <style>
        :root {
            --desk-bg: #f7f3e8;
            --desk-line: rgba(35, 72, 82, 0.16);
            --desk-ink: #17252b;
            --desk-muted: #667782;
            --desk-green: #0f9f71;
            --desk-amber: #c47a15;
            --desk-red: #c44d46;
            --font-display: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            --font-body: "Avenir Next", "Trebuchet MS", sans-serif;
            --font-serif: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
            --font-mono: "SF Mono", "Menlo", monospace;
            --type-xs: 0.64rem;
            --type-sm: 0.72rem;
            --type-base: 0.82rem;
            --type-md: 0.95rem;
            --type-lg: 1.12rem;
            --type-xl: 1.32rem;
            --type-hero: clamp(0.98rem, 1.5vw, 1.36rem);
            --leading-tight: 1.1;
            --leading-normal: 1.3;
            --tracking-label: 0.12em;
        }

        .stApp {
            background: linear-gradient(135deg, #fbf7ec 0%, #eef5f1 48%, #f9f1dd 100%);
            color: var(--desk-ink);
        }

        .block-container {
            max-width: none;
            width: 100%;
            padding: 0.6rem 0.75rem 0.35rem;
        }

        h1, h2, h3, h4 {
            font-family: var(--font-display);
            color: var(--desk-ink);
        }

        p, label {
            font-family: var(--font-body);
            font-size: var(--type-base);
            line-height: var(--leading-normal);
        }

        .desk-shell,
        .market-overview-banner,
        .console-interaction-strip,
        .operator-closure-panel,
        .compact-info-card,
        div[data-testid="stTabs"] {
            border: 1px solid var(--desk-line);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.68);
            box-shadow: 0 10px 24px rgba(49, 77, 75, 0.07);
        }

        .desk-shell {
            padding: 0.45rem 0.65rem;
            margin-bottom: 0.25rem;
        }

        .desk-kicker,
        .eyebrow,
        .mini-label,
        .metric-label,
        .console-strip-title,
        .operator-closure-title,
        .compact-metric span,
        .compact-kv-row span {
            color: var(--desk-muted);
            font-family: var(--font-mono);
            font-size: var(--type-xs);
            font-weight: 800;
            letter-spacing: var(--tracking-label);
            line-height: var(--leading-tight);
            text-transform: uppercase;
        }

        .desk-kicker {
            color: var(--desk-amber);
        }

        .desk-title {
            margin: 0.05rem 0;
            color: #11282f;
            font-family: var(--font-display);
            font-size: var(--type-hero);
            font-weight: 900;
            line-height: 1.18;
        }

        .desk-subtitle,
        .page-subtitle,
        .console-subtitle,
        .compact-panel-subtitle,
        .thin-evidence-line,
        .closure-detail {
            color: var(--desk-muted);
            font-size: var(--type-sm);
            line-height: var(--leading-normal);
        }

        .console-interaction-strip,
        .market-overview-banner,
        .operator-closure-panel {
            margin-bottom: 0.25rem;
            padding: 0.35rem 0.45rem;
        }

        .flat-overview-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 0.5rem;
            align-items: center;
        }

        .flat-market-title strong {
            display: block;
            overflow: hidden;
            color: var(--desk-ink);
            font-family: var(--font-serif);
            font-size: var(--type-md);
            line-height: var(--leading-tight);
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .control-console-topline,
        .thin-status-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            justify-content: flex-end;
        }

        .control-chip,
        .console-pill,
        .thin-status-strip span {
            display: inline-flex;
            align-items: center;
            gap: 0.22rem;
            padding: 0.16rem 0.42rem;
            border: 1px solid var(--desk-line);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.72);
            color: var(--desk-ink);
            font-family: var(--font-mono);
            font-size: var(--type-xs);
            line-height: var(--leading-tight);
        }

        .control-chip--ok,
        .state-authorized,
        .state-logged,
        .closure-card--ok {
            border-color: rgba(15, 159, 113, 0.28);
            background: rgba(15, 159, 113, 0.09);
        }

        .control-chip--warning,
        .state-step,
        .state-xai,
        .closure-card--warning {
            border-color: rgba(196, 122, 21, 0.28);
            background: rgba(196, 122, 21, 0.10);
        }

        .state-locked,
        .closure-card--critical {
            border-color: rgba(196, 77, 70, 0.28);
            background: rgba(196, 77, 70, 0.09);
        }

        .operator-closure-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.32rem;
        }

        .closure-card {
            display: grid;
            grid-template-columns: auto minmax(0, 1fr);
            gap: 0.32rem;
            min-width: 0;
            padding: 0.38rem 0.42rem;
            border: 1px solid var(--desk-line);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.70);
        }

        .closure-card-index {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.3rem;
            height: 1.3rem;
            border-radius: 999px;
            background: rgba(17, 57, 92, 0.10);
            font-family: var(--font-mono);
            font-size: var(--type-xs);
            font-weight: 900;
        }

        .closure-question {
            overflow: hidden;
            color: var(--desk-muted);
            font-size: var(--type-xs);
            font-weight: 760;
            line-height: var(--leading-tight);
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .closure-answer {
            overflow: hidden;
            color: var(--desk-ink);
            font-family: var(--font-display);
            font-size: var(--type-md);
            font-weight: 900;
            line-height: var(--leading-tight);
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .compact-panel-heading {
            margin-bottom: 0.3rem;
        }

        .compact-panel-title {
            color: var(--desk-ink);
            font-family: var(--font-display);
            font-size: var(--type-lg);
            font-weight: 900;
            line-height: var(--leading-tight);
        }

        .compact-info-card {
            display: grid;
            gap: 0.28rem;
            margin-bottom: 0.38rem;
            padding: 0.48rem 0.55rem;
        }

        .compact-card-title {
            color: #33464e;
            font-family: var(--font-display);
            font-size: var(--type-md);
            font-weight: 850;
        }

        .compact-metric strong {
            color: var(--desk-green);
            font-family: var(--font-display);
            font-size: var(--type-xl);
            font-weight: 900;
            line-height: var(--leading-tight);
        }

        .compact-kv-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.22rem 0.48rem;
        }

        .compact-kv-row strong {
            overflow: hidden;
            color: var(--desk-ink);
            font-size: var(--type-sm);
            font-weight: 760;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .compact-note {
            margin: 0.22rem 0 0.38rem;
            padding: 0.35rem 0.48rem;
            border: 1px solid var(--desk-line);
            border-radius: 10px;
            color: var(--desk-muted);
            font-size: var(--type-sm);
            background: rgba(17, 57, 92, 0.06);
        }

        .stButton > button {
            min-height: 1.9rem;
            border-radius: 999px;
            font-size: var(--type-sm);
            font-weight: 750;
        }

        div[data-testid="stMetric"] {
            border: 1px solid var(--desk-line);
            border-radius: 12px;
            padding: 0.42rem 0.55rem;
            background: rgba(255, 255, 255, 0.72);
        }

        div[data-testid="stMetricValue"] {
            color: var(--desk-green);
            font-family: var(--font-display);
            font-size: var(--type-xl);
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--desk-line);
            border-radius: 12px;
            overflow: hidden;
        }

        div[data-testid="stTabs"] {
            padding: 0.18rem 0.28rem 0.3rem;
        }

        div[data-testid="stTabs"] [data-baseweb="tab"] {
            font-size: var(--type-sm);
        }

        @media (max-width: 980px) {
            .operator-closure-grid,
            .compact-kv-grid,
            .flat-overview-row {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    return

    st.markdown(
        """
        <style>
        :root {
            --desk-bg: #f7f3e8;
            --desk-panel: rgba(255, 252, 244, 0.86);
            --desk-panel-strong: rgba(255, 255, 255, 0.96);
            --desk-line: rgba(35, 72, 82, 0.15);
            --desk-line-hot: rgba(205, 132, 28, 0.34);
            --desk-ink: #17252b;
            --desk-muted: #667782;
            --desk-green: #0f9f71;
            --desk-teal: #0e8fa3;
            --desk-amber: #c47a15;
            --desk-red: #c44d46;
            --font-display: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            --font-body: "Avenir Next", "Trebuchet MS", sans-serif;
            --font-serif: "Iowan Old Style", "Palatino Linotype", "Book Antiqua", serif;
            --font-mono: "SF Mono", "Menlo", monospace;
            --type-xs: 0.64rem;
            --type-sm: 0.72rem;
            --type-base: 0.82rem;
            --type-md: 0.95rem;
            --type-lg: 1.12rem;
            --type-xl: 1.32rem;
            --type-hero: clamp(0.95rem, 1.45vw, 1.32rem);
            --leading-tight: 1.08;
            --leading-normal: 1.28;
            --tracking-label: 0.12em;
        }

        .stApp {
            background:
                radial-gradient(circle at 15% 4%, rgba(14, 143, 163, 0.14), transparent 30rem),
                radial-gradient(circle at 86% 2%, rgba(196, 122, 21, 0.13), transparent 24rem),
                linear-gradient(135deg, #fbf7ec 0%, #eef5f1 44%, #f9f1dd 100%);
            color: var(--desk-ink);
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            pointer-events: none;
            background-image:
                linear-gradient(rgba(35,72,82,0.055) 1px, transparent 1px),
                linear-gradient(90deg, rgba(35,72,82,0.045) 1px, transparent 1px);
            background-size: 44px 44px;
            mask-image: linear-gradient(to bottom, rgba(0,0,0,0.55), transparent 78%);
            z-index: 0;
        }

        .block-container {
            max-width: none;
            width: 100%;
            padding: 0.55rem 0.65rem 0.28rem;
            position: relative;
            z-index: 1;
        }

        .stMarkdown,
        .stCaption,
        div[data-testid="stMarkdownContainer"] {
            margin-bottom: 0.18rem;
        }

        h1, h2, h3, h4 {
            font-family: var(--font-display);
            letter-spacing: 0.015em;
        }

        h2, h3 {
            color: #15292f;
        }

        p, div, label, span {
            font-family: var(--font-body);
        }

        code, pre, .stCode {
            font-family: var(--font-mono);
        }

        [data-testid="stSidebar"] {
            background:
                linear-gradient(180deg, rgba(255, 252, 244, 0.98), rgba(239, 247, 244, 0.98));
            border-right: 1px solid var(--desk-line);
        }

        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label {
            color: #263d44;
            font-size: inherit;
            line-height: var(--leading-normal);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            margin: 0.15rem 0 0.25rem;
            font-size: var(--type-md);
        }

        [data-testid="stSidebar"] div[data-testid="stExpander"] {
            margin-bottom: 0.28rem;
            border-radius: 12px;
        }

        [data-testid="stSidebar"] details summary {
            min-height: 2rem;
            padding: 0.28rem 0.48rem;
            font-size: var(--type-base);
            font-weight: 800;
        }

        [data-testid="stSidebar"] div[data-testid="stSelectbox"],
        [data-testid="stSidebar"] div[data-testid="stTextInput"] {
            margin-bottom: 0.28rem;
        }

        [data-testid="stSidebar"] input,
        [data-testid="stSidebar"] [data-baseweb="select"] {
            font-size: inherit;
        }

        div[data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(248, 242, 229, 0.94));
            border: 1px solid var(--desk-line);
            border-radius: 12px;
            padding: 0.42rem 0.55rem;
            box-shadow: 0 10px 24px rgba(64, 81, 76, 0.08);
        }

        div[data-testid="stMetric"] label {
            color: var(--desk-muted) !important;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-size: var(--type-xs);
        }

        div[data-testid="stMetricValue"] {
            color: var(--desk-green);
            font-family: var(--font-display);
            letter-spacing: 0.02em;
            font-size: var(--type-xl);
        }

        div[data-testid="stExpander"] {
            border: 1px solid var(--desk-line);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.74);
            overflow: hidden;
        }

        .stDataFrame,
        div[data-testid="stDataFrame"] {
            border: 1px solid var(--desk-line);
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 12px 28px rgba(45, 68, 69, 0.08);
        }

        div[data-testid="stDataFrame"] {
            max-height: 44vh;
        }

        .stButton > button {
            border-radius: 999px;
            border: 1px solid rgba(14, 143, 163, 0.26);
            background: linear-gradient(135deg, rgba(14, 143, 163, 0.12), rgba(255, 255, 255, 0.74));
            color: #16343b;
            min-height: 1.82rem;
            padding: 0.18rem 0.55rem;
            font-size: var(--type-sm);
            font-weight: 700;
            letter-spacing: 0.02em;
            transition: transform 160ms ease, border-color 160ms ease, background 160ms ease;
        }

        .stButton > button:hover {
            transform: translateY(-1px);
            border-color: rgba(196, 122, 21, 0.55);
            background: linear-gradient(135deg, rgba(196, 122, 21, 0.14), rgba(14, 143, 163, 0.08));
        }

        mark {
            color: #25180a;
            background: rgba(255, 206, 126, 0.86);
            border-radius: 0.22rem;
            padding: 0 0.16rem;
        }

        .desk-shell {
            border: 1px solid var(--desk-line);
            border-radius: 14px;
            padding: 0.42rem 0.62rem;
            margin: 0.08rem 0 0.18rem;
            background:
                linear-gradient(135deg, rgba(255, 255, 255, 0.93), rgba(248, 241, 224, 0.9)),
                radial-gradient(circle at top right, rgba(14, 143, 163, 0.13), transparent 18rem);
            box-shadow: 0 14px 36px rgba(49, 77, 75, 0.12);
        }

        .desk-kicker {
            color: var(--desk-amber);
            font-size: var(--type-xs);
            text-transform: uppercase;
            letter-spacing: 0.22em;
            font-weight: 800;
        }

        .desk-title {
            margin: 0.04rem 0 0.08rem;
            color: #11282f;
            font-family: var(--font-display);
            font-size: var(--type-hero);
            font-weight: 900;
            line-height: 1.18;
            letter-spacing: -0.035em;
        }

        .desk-subtitle {
            color: var(--desk-muted);
            font-size: var(--type-sm);
            max-width: 70rem;
            line-height: var(--leading-normal);
        }

        .command-grid {
            display: grid;
            grid-template-columns: 1.45fr 0.9fr 0.9fr;
            gap: 0.9rem;
            margin-top: 1rem;
        }

        .command-card {
            border: 1px solid var(--desk-line);
            border-radius: 22px;
            padding: 1rem;
            background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(245, 238, 222, 0.82));
            min-height: 150px;
        }

        .command-label {
            color: var(--desk-muted);
            font-size: var(--type-xs);
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 800;
        }

        .command-value {
            color: var(--desk-ink);
            font-size: var(--type-md);
            line-height: var(--leading-normal);
            margin-top: 0.4rem;
            font-weight: 750;
        }

        .command-number {
            color: var(--desk-green);
            font-family: var(--font-display);
            font-size: var(--type-xl);
            line-height: var(--leading-tight);
            margin-top: 0.4rem;
            font-weight: 900;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.38rem;
            padding: 0.28rem 0.62rem;
            border-radius: 999px;
            border: 1px solid rgba(15, 159, 113, 0.22);
            background: rgba(15, 159, 113, 0.10);
            color: #0c6248;
            font-size: var(--type-xs);
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }

        .status-dot {
            width: 0.52rem;
            height: 0.52rem;
            border-radius: 50%;
            background: var(--desk-green);
            box-shadow: 0 0 18px rgba(15, 159, 113, 0.42);
        }

        .desk-footer-mark {
            display: flex;
            justify-content: flex-end;
            margin: 1.5rem 0 0.2rem;
        }

        .desk-footer-mark a {
            color: rgba(23, 37, 43, 0.44);
            text-decoration: none;
            font-size: var(--type-xs);
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .desk-footer-mark a:hover {
            color: var(--desk-amber);
        }

        .weather-argument-console {
            animation: rise 700ms ease-out both;
        }

        .console-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 18px;
            padding: 6px 9px;
            border-bottom: 1px solid var(--desk-line);
            background: rgba(255, 255, 255, 0.62);
        }

        .console-title-group {
            display: grid;
            gap: 3px;
        }

        .eyebrow,
        .mini-label,
        .metric-label {
            font-family: var(--font-mono);
            font-size: var(--type-xs);
            letter-spacing: var(--tracking-label);
            text-transform: uppercase;
            color: var(--desk-muted);
        }

        .console-section-title {
            margin: 0;
            font-family: var(--font-serif);
            font-size: var(--type-md);
            letter-spacing: -0.03em;
            color: var(--desk-ink);
        }

        .control-console-topline {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
            justify-content: flex-end;
        }

        .control-chip,
        .console-pill {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            padding: 3px 6px;
            border-radius: 999px;
            border: 1px solid var(--desk-line);
            background: rgba(255, 255, 255, 0.66);
            color: var(--desk-ink);
            font-family: var(--font-mono);
            font-size: var(--type-xs);
        }

        .control-chip--accent {
            background: rgba(17, 57, 92, 0.09);
            border-color: rgba(17, 57, 92, 0.22);
        }

        .control-chip--warning {
            background: rgba(196, 122, 21, 0.12);
            border-color: rgba(196, 122, 21, 0.24);
        }

        .control-chip--ok {
            background: rgba(15, 159, 113, 0.10);
            border-color: rgba(15, 159, 113, 0.22);
        }

        .console-pane {
            display: grid;
            gap: 6px;
            padding: 7px;
            min-height: 0;
            overflow: hidden;
        }

        .console-hero {
            padding: 11px 13px;
            border-radius: 14px;
            border-left: 4px solid #11395c;
            background: linear-gradient(135deg, rgba(17, 57, 92, 0.10), rgba(255, 255, 255, 0.45));
        }

        .console-hero p {
            margin: 0;
            color: var(--desk-ink);
            line-height: var(--leading-normal);
            font-size: var(--type-base);
        }

        .step-list {
            display: grid;
            gap: 4px;
        }

        .step-card {
            display: grid;
            gap: 2px;
            padding: 5px 8px;
            border-radius: 10px;
            border: 1px solid var(--desk-line);
            background: rgba(255, 255, 255, 0.58);
        }

        .step-card--active {
            border-color: rgba(17, 57, 92, 0.42);
            box-shadow: 0 0 0 1px rgba(17, 57, 92, 0.14);
            background: rgba(17, 57, 92, 0.08);
        }

        .step-card--completed {
            opacity: 0.82;
        }

        .step-card--pending {
            opacity: 0.74;
        }

        .step-card-topline {
            display: flex;
            justify-content: space-between;
            gap: 8px;
            align-items: center;
        }

        .step-card-title {
            margin: 0;
            font-size: var(--type-sm);
            font-weight: 800;
            color: var(--desk-ink);
        }

        .step-card-desc {
            margin: 0;
            color: var(--desk-muted);
            line-height: var(--leading-tight);
            font-size: var(--type-xs);
        }

        .step-badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 18px;
            height: 18px;
            border-radius: 999px;
            background: rgba(35, 72, 82, 0.10);
            color: var(--desk-ink);
            font-family: var(--font-mono);
            font-size: var(--type-xs);
            flex-shrink: 0;
        }

        .step-badge--done {
            background: rgba(15, 159, 113, 0.88);
            color: white;
        }

        .top-banner {
            display: grid;
            gap: 12px;
            padding: 14px;
            border-radius: 18px;
            border: 1px solid var(--desk-line);
            background: rgba(255, 255, 255, 0.68);
            box-shadow: 0 18px 45px rgba(49, 77, 75, 0.08);
        }

        .banner-meta,
        .banner-title-row {
            display: grid;
            gap: 12px;
        }

        .banner-meta {
            grid-template-columns: 1fr auto;
            align-items: center;
        }

        .banner-title-row {
            grid-template-columns: minmax(0, 1.25fr) minmax(220px, 0.75fr);
            align-items: start;
        }

        .section-block {
            display: grid;
            gap: 12px;
        }

        .page-title {
            margin: 0;
            font-family: var(--font-serif);
            font-size: var(--type-xl);
            line-height: var(--leading-tight);
            letter-spacing: -0.04em;
            color: var(--desk-ink);
        }

        .page-title--compact {
            font-size: var(--type-lg);
        }

        .page-subtitle,
        .console-subtitle {
            color: var(--desk-muted);
            line-height: var(--leading-normal);
            margin: 0;
            font-size: var(--type-base);
        }

        .hero-callout {
            padding: 18px;
            border-left: 4px solid #11395c;
            border-radius: 18px;
            background: linear-gradient(135deg, rgba(17, 57, 92, 0.1), rgba(255, 255, 255, 0.45));
        }

        .hero-callout p {
            margin: 0;
            color: var(--desk-ink);
            line-height: var(--leading-normal);
        }

        .console-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 7px;
        }

        .console-card {
            padding: 8px;
            border-radius: 13px;
            border: 1px solid var(--desk-line);
            background: rgba(255, 255, 255, 0.58);
            min-width: 0;
            overflow: hidden;
        }

        .console-card--full {
            grid-column: 1 / -1;
        }

        .console-panel-title {
            display: flex;
            align-items: center;
            gap: 10px;
            margin: 0 0 6px;
            font-size: var(--type-base);
            font-weight: 800;
            color: #33464e;
        }

        .compact-panel-heading {
            display: grid;
            gap: 0.08rem;
            margin: 0 0 0.28rem;
        }

        .compact-panel-title {
            color: var(--desk-ink);
            font-family: var(--font-display);
            font-size: var(--type-lg);
            font-weight: 900;
            letter-spacing: 0.01em;
            line-height: var(--leading-tight);
        }

        .compact-panel-subtitle {
            overflow: hidden;
            color: var(--desk-muted);
            font-size: var(--type-sm);
            line-height: var(--leading-normal);
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .compact-info-card {
            display: grid;
            gap: 0.28rem;
            min-width: 0;
            margin-bottom: 0.38rem;
            padding: 0.48rem 0.55rem;
            border: 1px solid var(--desk-line);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.62);
            box-shadow: 0 10px 24px rgba(45, 68, 69, 0.07);
        }

        .compact-card-title {
            color: #33464e;
            font-family: var(--font-display);
            font-size: var(--type-md);
            font-weight: 850;
            line-height: var(--leading-tight);
        }

        .compact-metric {
            display: grid;
            gap: 0.08rem;
        }

        .compact-metric span,
        .compact-kv-row span {
            color: var(--desk-muted);
            font-family: var(--font-mono);
            font-size: var(--type-xs);
            letter-spacing: var(--tracking-label);
            line-height: var(--leading-tight);
            text-transform: uppercase;
        }

        .compact-metric strong {
            color: var(--desk-green);
            font-family: var(--font-display);
            font-size: var(--type-xl);
            font-weight: 900;
            line-height: var(--leading-tight);
        }

        .compact-kv-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.22rem 0.48rem;
        }

        .compact-kv-row {
            display: grid;
            gap: 0.04rem;
            min-width: 0;
        }

        .compact-kv-row strong {
            overflow: hidden;
            color: var(--desk-ink);
            font-size: var(--type-sm);
            font-weight: 760;
            line-height: var(--leading-tight);
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .compact-note {
            margin: 0.22rem 0 0.38rem;
            padding: 0.35rem 0.48rem;
            border: 1px solid var(--desk-line);
            border-radius: 10px;
            color: var(--desk-muted);
            font-size: var(--type-sm);
            line-height: var(--leading-normal);
            background: rgba(17, 57, 92, 0.06);
        }

        .compact-note--warning {
            color: #8a5512;
            border-color: rgba(196, 122, 21, 0.24);
            background: rgba(196, 122, 21, 0.10);
        }

        .compact-note--critical {
            color: #9c2f2d;
            border-color: rgba(196, 77, 70, 0.24);
            background: rgba(196, 77, 70, 0.09);
        }

        .readiness-status-strip {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.34rem;
            margin: 0.24rem 0 0.42rem;
        }

        .readiness-count-card {
            display: grid;
            gap: 0.04rem;
            padding: 0.38rem 0.46rem;
            border: 1px solid var(--desk-line);
            border-radius: 11px;
            background: rgba(255, 255, 255, 0.58);
        }

        .readiness-count-card span {
            color: var(--desk-muted);
            font-family: var(--font-mono);
            font-size: var(--type-xs);
            letter-spacing: var(--tracking-label);
            line-height: var(--leading-tight);
            text-transform: uppercase;
        }

        .readiness-count-card strong {
            color: var(--desk-ink);
            font-family: var(--font-display);
            font-size: var(--type-lg);
            font-weight: 900;
            line-height: var(--leading-tight);
        }

        .readiness-count-card--blocked {
            border-color: rgba(196, 77, 70, 0.30);
            background: rgba(196, 77, 70, 0.08);
        }

        .readiness-count-card--blocked strong {
            color: #9c2f2d;
        }

        .readiness-count-card--warning {
            border-color: rgba(196, 122, 21, 0.30);
            background: rgba(196, 122, 21, 0.10);
        }

        .readiness-count-card--warning strong {
            color: #8a5512;
        }

        .readiness-count-card--passed {
            border-color: rgba(61, 136, 94, 0.28);
            background: rgba(61, 136, 94, 0.10);
        }

        .readiness-count-card--passed strong {
            color: var(--desk-green);
        }

        .operator-closure-panel {
            display: grid;
            gap: 0.25rem;
            margin: 0 0 0.22rem;
            padding: 0.35rem;
            border: 1px solid var(--desk-line);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.50);
            box-shadow: 0 8px 20px rgba(49, 77, 75, 0.06);
        }

        .operator-closure-title {
            color: var(--desk-muted);
            font-family: var(--font-mono);
            font-size: var(--type-xs);
            font-weight: 850;
            letter-spacing: var(--tracking-label);
            line-height: var(--leading-tight);
            text-transform: uppercase;
        }

        .operator-closure-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.3rem;
        }

        .closure-card {
            display: grid;
            grid-template-columns: auto minmax(0, 1fr);
            gap: 0.32rem;
            min-width: 0;
            padding: 0.38rem 0.42rem;
            border: 1px solid var(--desk-line);
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.66);
        }

        .closure-card--ok {
            border-color: rgba(15, 159, 113, 0.24);
            background: rgba(15, 159, 113, 0.08);
        }

        .closure-card--warning {
            border-color: rgba(196, 122, 21, 0.24);
            background: rgba(196, 122, 21, 0.09);
        }

        .closure-card--critical {
            border-color: rgba(196, 77, 70, 0.24);
            background: rgba(196, 77, 70, 0.08);
        }

        .closure-card-index {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.3rem;
            height: 1.3rem;
            border-radius: 999px;
            background: rgba(17, 57, 92, 0.10);
            color: var(--desk-ink);
            font-family: var(--font-mono);
            font-size: var(--type-xs);
            font-weight: 900;
        }

        .closure-card-body {
            display: grid;
            gap: 0.08rem;
            min-width: 0;
        }

        .closure-question {
            overflow: hidden;
            color: var(--desk-muted);
            font-size: var(--type-xs);
            font-weight: 760;
            line-height: var(--leading-tight);
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .closure-answer {
            overflow: hidden;
            color: var(--desk-ink);
            font-family: var(--font-display);
            font-size: var(--type-md);
            font-weight: 900;
            line-height: var(--leading-tight);
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .closure-detail {
            overflow: hidden;
            color: var(--desk-muted);
            font-size: var(--type-xs);
            line-height: var(--leading-tight);
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .monitor-list {
            display: grid;
            gap: 5px;
        }

        .monitor-item {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 6px 8px;
            border-radius: 10px;
            font-size: var(--type-sm);
            border: 1px solid var(--desk-line);
        }

        .monitor-item span {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .monitor-item--critical {
            color: #9c2f2d;
            background: rgba(196, 77, 70, 0.10);
        }

        .monitor-item--warning {
            color: #8a5512;
            background: rgba(196, 122, 21, 0.12);
        }

        .monitor-item--info {
            color: #415860;
            background: rgba(17, 57, 92, 0.06);
        }

        .weather-console-frame {
            display: grid;
            gap: 3px;
            margin: 0.05rem 0 0.16rem;
        }

        .console-interaction-strip {
            margin: 0.05rem 0 0.15rem;
            padding: 0.2rem 0.42rem 0.28rem;
            border: 1px solid var(--desk-line);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.55);
            box-shadow: 0 8px 20px rgba(49, 77, 75, 0.06);
        }

        .console-strip-title {
            margin-bottom: 0.12rem;
            color: var(--desk-muted);
            font-family: var(--font-mono);
            font-size: var(--type-xs);
            font-weight: 800;
            letter-spacing: var(--tracking-label);
            text-transform: uppercase;
        }

        .state-chip {
            font-weight: 900;
        }

        .state-overview {
            background: rgba(17, 57, 92, 0.08);
            border-color: rgba(17, 57, 92, 0.22);
        }

        .state-step,
        .state-xai {
            background: rgba(196, 122, 21, 0.12);
            border-color: rgba(196, 122, 21, 0.24);
        }

        .state-authorized,
        .state-logged {
            background: rgba(15, 159, 113, 0.11);
            border-color: rgba(15, 159, 113, 0.25);
        }

        .state-locked {
            background: rgba(196, 77, 70, 0.10);
            border-color: rgba(196, 77, 70, 0.25);
        }

        .market-overview-banner {
            display: grid;
            gap: 3px;
            padding: 4px 7px;
            border-radius: 12px;
            border: 1px solid var(--desk-line);
            background:
                linear-gradient(135deg, rgba(255,255,255,0.86), rgba(247,241,228,0.78)),
                radial-gradient(circle at top right, rgba(17,57,92,0.08), transparent 16rem);
            box-shadow: 0 10px 24px rgba(49, 77, 75, 0.08);
        }

        .flat-overview-row {
            display: grid;
            grid-template-columns: minmax(0, 1fr) auto;
            gap: 8px;
            align-items: center;
        }

        .flat-market-title {
            min-width: 0;
        }

        .flat-market-title strong {
            display: block;
            max-width: 100%;
            overflow: hidden;
            color: var(--desk-ink);
            font-family: var(--font-serif);
            font-size: var(--type-md);
            line-height: var(--leading-tight);
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .thin-status-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 4px;
        }

        .thin-status-strip span {
            display: inline-flex;
            gap: 0.22rem;
            align-items: center;
            padding: 2px 5px;
            border: 1px solid var(--desk-line);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.58);
            color: var(--desk-muted);
            font-size: var(--type-xs);
            line-height: var(--leading-tight);
        }

        .thin-status-strip strong {
            color: var(--desk-ink);
            font-size: var(--type-xs);
        }

        .thin-evidence-line {
            overflow: hidden;
            color: var(--desk-muted);
            font-size: var(--type-sm);
            line-height: var(--leading-tight);
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .micro-metric-row {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 8px;
        }

        .micro-metric-row div {
            padding: 9px 11px;
            border-radius: 14px;
            border: 1px solid var(--desk-line);
            background: rgba(255, 255, 255, 0.62);
        }

        .micro-metric-row span,
        .yes-no-side span,
        .soft-control span {
            display: block;
            color: var(--desk-muted);
            font-size: var(--type-xs);
            text-transform: uppercase;
            letter-spacing: 0.12em;
        }

        .micro-metric-row strong {
            display: block;
            margin-top: 0.35rem;
            color: var(--desk-ink);
            font-family: var(--font-serif);
            font-size: var(--type-lg);
            line-height: var(--leading-tight);
        }

        .left-control-zone {
            display: grid;
            gap: 4px;
            margin-top: 2px;
            padding-top: 5px;
            border-top: 1px solid var(--desk-line);
        }

        .emergency-actions {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 5px;
        }

        .soft-control {
            min-height: 38px;
            padding: 6px 7px;
            border-radius: 10px;
            border: 1px solid var(--desk-line);
            background: rgba(255, 255, 255, 0.64);
        }

        .soft-control strong {
            display: block;
            margin-bottom: 0.12rem;
            color: var(--desk-ink);
            font-size: var(--type-sm);
        }

        .soft-control--danger {
            border-color: rgba(196, 77, 70, 0.24);
            background: rgba(196, 77, 70, 0.08);
        }

        .soft-control--neutral {
            border-color: rgba(17, 57, 92, 0.20);
            background: rgba(17, 57, 92, 0.06);
        }

        .yes-no-switch {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 6px;
            margin-bottom: 6px;
        }

        .yes-no-side {
            padding: 7px;
            border-radius: 11px;
            border: 1px solid var(--desk-line);
            background: rgba(255, 255, 255, 0.65);
        }

        .yes-no-side strong {
            display: block;
            margin-top: 0.3rem;
            font-size: var(--type-lg);
            line-height: var(--leading-tight);
            font-family: var(--font-serif);
        }

        .yes-no-side--yes {
            border-color: rgba(15, 159, 113, 0.24);
            background: rgba(15, 159, 113, 0.08);
        }

        .yes-no-side--no {
            border-color: rgba(196, 122, 21, 0.24);
            background: rgba(196, 122, 21, 0.08);
        }

        div[data-testid="stTabs"] {
            border: 1px solid var(--desk-line);
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.54);
            padding: 0.12rem 0.25rem 0.25rem;
            box-shadow: 0 10px 24px rgba(49, 77, 75, 0.06);
        }

        div[data-testid="stTabs"] [data-baseweb="tab-list"] {
            gap: 0.15rem;
            margin-bottom: 0.08rem;
        }

        div[data-testid="stTabs"] [data-baseweb="tab"] {
            height: 1.55rem;
            padding: 0.12rem 0.55rem;
            border-radius: 999px;
            font-size: var(--type-sm);
        }

        div[data-testid="stTabs"] [data-baseweb="tab-panel"] {
            max-height: calc(100vh - 250px);
            min-height: 300px;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 0.08rem 0.08rem 0.18rem;
        }

        .desk-tabs-anchor {
            height: 0;
            margin: 0;
        }

        @keyframes rise {
            from {
                opacity: 0;
                transform: translateY(14px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 980px) {
            .command-grid {
                grid-template-columns: 1fr;
            }

            .console-grid,
            .operator-closure-grid,
            .micro-metric-row,
            .emergency-actions,
            .yes-no-switch,
            .banner-meta,
            .banner-title-row {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
