from __future__ import annotations

import re
from html import escape, unescape
from typing import Iterable

import streamlit as st


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def fmt_value(value: object) -> str:
    if value is None:
        return "-"
    return sanitize_text(str(value))


def sanitize_text(text: object) -> str:
    if text is None:
        return "-"
    cleaned = unescape(str(text))
    cleaned = _HTML_TAG_RE.sub("", cleaned)
    return cleaned.strip() or "-"


def render_panel_title(title: str, subtitle: str | None = None) -> None:
    _render_compact_panel_styles()
    subtitle_html = (
        f"<div class='compact-panel-subtitle'>{escape(sanitize_text(subtitle))}</div>"
        if subtitle
        else ""
    )
    st.markdown(
        f"""
        <div class="compact-panel-heading">
          <div class="compact-panel-title">{escape(sanitize_text(title))}</div>
          {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kv_section(
    title: str,
    items: Iterable[tuple[str, object]],
    metric_label: str | None = None,
    metric_value: object | None = None,
) -> None:
    _render_compact_panel_styles()
    metric_html = ""
    if metric_label is not None:
        metric_html = f"""
          <div class="compact-metric">
            <span>{escape(sanitize_text(metric_label))}</span>
            <strong>{escape(fmt_value(metric_value))}</strong>
          </div>
        """

    rows = "\n".join(
        f"""
        <div class="compact-kv-row">
          <span>{escape(sanitize_text(label))}</span>
          <strong>{escape(fmt_value(value))}</strong>
        </div>
        """
        for label, value in items
    )

    st.markdown(
        f"""
        <section class="compact-info-card">
          <div class="compact-card-title">{escape(sanitize_text(title))}</div>
          {metric_html}
          <div class="compact-kv-grid">
            {rows}
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_compact_note(text: str, tone: str = "info") -> None:
    _render_compact_panel_styles()
    st.markdown(
        f"""
        <div class="compact-note compact-note--{escape(tone)}">
          {escape(sanitize_text(text))}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_compact_panel_styles() -> None:
    st.markdown(
        """
        <style>
        .compact-panel-heading {
            margin: 0.28rem 0 0.18rem;
        }
        .compact-panel-title {
            color: #11282f;
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 1.02rem;
            font-weight: 950;
            line-height: 1.1;
        }
        .compact-panel-subtitle {
            margin-top: 0.08rem;
            color: #667782;
            font-size: 0.72rem;
            line-height: 1.25;
        }
        .compact-info-card {
            border: 1px solid rgba(35, 72, 82, 0.15);
            border-radius: 14px;
            background: rgba(255,255,255,0.80);
            padding: 0.42rem 0.48rem;
            margin: 0.28rem 0;
            box-shadow: 0 10px 22px rgba(49, 77, 75, 0.06);
        }
        .compact-card-title {
            color: #667782;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.62rem;
            font-weight: 900;
            letter-spacing: 0.10em;
            text-transform: uppercase;
        }
        .compact-metric {
            margin-top: 0.24rem;
            border: 1px solid rgba(35, 72, 82, 0.10);
            border-radius: 12px;
            background: rgba(255,255,255,0.72);
            padding: 0.32rem 0.38rem;
        }
        .compact-metric span,
        .compact-kv-row span {
            color: #667782;
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.6rem;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .compact-metric strong {
            display: block;
            margin-top: 0.08rem;
            color: #11282f;
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 1.1rem;
            font-weight: 950;
            line-height: 1.05;
        }
        .compact-kv-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.24rem;
            margin-top: 0.30rem;
        }
        .compact-kv-row {
            display: grid;
            grid-template-columns: minmax(6.5rem, 0.75fr) minmax(0, 1fr);
            gap: 0.34rem;
            align-items: center;
            border: 1px solid rgba(35, 72, 82, 0.10);
            border-radius: 10px;
            background: rgba(255,255,255,0.62);
            padding: 0.24rem 0.32rem;
            min-height: 2.1rem;
        }
        .compact-kv-row strong {
            color: #17252b;
            font-size: 0.72rem;
            font-weight: 800;
            line-height: 1.14;
            overflow-wrap: anywhere;
            text-align: right;
        }
        .compact-note {
            border: 1px solid rgba(35, 72, 82, 0.12);
            border-radius: 12px;
            background: rgba(255,255,255,0.70);
            color: #667782;
            padding: 0.34rem 0.42rem;
            margin: 0.26rem 0;
            font-size: 0.72rem;
            line-height: 1.28;
        }
        .compact-note--warning {
            border-color: rgba(196, 122, 21, 0.28);
            background: rgba(255, 249, 233, 0.82);
        }
        .compact-note--critical {
            border-color: rgba(196, 77, 70, 0.28);
            background: rgba(255, 244, 241, 0.86);
        }
        @media (max-width: 1100px) {
            .compact-kv-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
