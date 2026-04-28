from __future__ import annotations

import re
from html import escape, unescape
from typing import Iterable


_HTML_TAG_RE = re.compile(r"<[^>]+>")


def fmt_value(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, dict) and "value" in value:
        return sanitize_text(value.get("value"))
    return sanitize_text(str(value))


def sanitize_text(text: object) -> str:
    if text is None:
        return "-"
    if isinstance(text, dict) and "value" in text:
        text = text.get("value")
    cleaned = unescape(str(text))
    cleaned = _HTML_TAG_RE.sub("", cleaned)
    return cleaned.strip() or "-"


def semantic_tone(label: object, value: object | None = None) -> str:
    label_text = sanitize_text(label).lower()
    value_text = sanitize_text(value).lower()
    if isinstance(value, dict):
        value_text = sanitize_text(value.get("value")).lower()
    if value_text in {"-", "none", ""}:
        return "muted"

    numeric_value = _coerce_float(value)

    ok_values = {
        "ready",
        "pass",
        "healthy",
        "fresh",
        "exact_station",
        "aligned",
        "live_approved",
        "live_execution_allowed",
        "yes",
        "true",
        "within_limit",
        "allow_live_execution",
    }
    warning_values = {
        "warning",
        "warm",
        "stale",
        "shadow_calibrated_candidate",
        "heuristic_not_calibrated",
        "dry_run_only",
        "manual_advisory_only",
        "family_only",
        "proxy",
        "partial",
        "mild_divergence",
        "hold_execution_and_review",
        "refresh_pipeline_inputs",
        "review_resolver_contract",
        "review",
    }
    critical_values = {
        "blocked",
        "block",
        "no",
        "false",
        "missing",
        "unavailable",
        "unhealthy",
        "stale_worker",
        "strong_divergence",
        "unmatched_rule",
        "market_mismatch",
        "resolver_not_matched",
        "resolver_source_not_exact",
        "validation_freshness_blocked",
        "label_coverage_blocked",
        "danger",
        "critical",
        "over_limit",
        "red",
    }
    warning_values = warning_values | {"amber", "yellow", "anomaly", "anomalous", "watch"}

    if value_text in ok_values:
        return "ok"
    if value_text in critical_values:
        return "critical"
    if value_text in warning_values:
        return "warning"

    if any(token in label_text for token in ("can execute", "gate status", "execution gate")):
        if value_text in {"yes", "ready", "pass", "live_execution_allowed"}:
            return "ok"
        if value_text in {"no", "blocked", "false"}:
            return "critical"
        return "warning"
    if "freshness" in label_text:
        if value_text in {"fresh", "healthy", "pass"}:
            return "ok"
        if value_text in {"warning", "warm", "stale"}:
            return "warning"
        return "critical"
    if "comparison status" in label_text:
        if value_text in {"aligned"}:
            return "ok"
        if value_text in {"mild_divergence", "partial"}:
            return "warning"
        return "critical"
    if "alert" in label_text:
        if value_text in {"0", "none", ""} or numeric_value == 0:
            return "ok"
        if value_text in {"red", "critical", "blocked", "danger"} or (numeric_value is not None and numeric_value >= 1):
            return "critical"
        return "warning"
    if "anomaly" in label_text:
        if value_text in {"0", "none", ""} or numeric_value == 0:
            return "ok"
        if value_text in {"red", "critical", "blocked", "danger"}:
            return "critical"
        return "warning"
    if "source match grade" in label_text:
        if value_text in {"exact_station"}:
            return "ok"
        if value_text in {"family_only"}:
            return "warning"
        return "critical"
    if "probability mode" in label_text:
        if value_text in {"live_approved"}:
            return "ok"
        return "warning"
    if "execution constraint" in label_text:
        if value_text in {"live_execution_allowed"}:
            return "ok"
        return "warning"
    if "promotion state" in label_text:
        if value_text in {"live_approved"}:
            return "ok"
        return "warning"
    if "fresh ratio" in label_text and numeric_value is not None:
        if numeric_value >= 0.8:
            return "ok"
        if numeric_value >= 0.55:
            return "warning"
        return "critical"
    if "scanner status" in label_text or "source health" in label_text:
        if value_text in {"healthy", "ready", "ok", "fresh"}:
            return "ok"
        if value_text in {"warm", "stale", "degraded"}:
            return "warning"
        return "critical"
    return "neutral"


def semantic_value_html(label: object, value: object, *, metric: bool = False) -> str:
    tone = semantic_tone(label, value)
    class_name = "semantic-value semantic-value--metric" if metric else "semantic-value"
    return (
        f"<span class='{class_name} semantic-value--{tone}'>"
        f"{escape(fmt_value(value))}"
        "</span>"
    )


def semantic_row_html(label: object, value: object) -> str:
    tone = semantic_tone(label, value)
    quality = quality_from_value(value)
    return (
        f"<div class='compact-kv-row compact-kv-row--{tone}'>"
        f"<span class='compact-kv-row__label'>"
        f"<span class='compact-kv-row__label-text'>{escape(sanitize_text(label))}</span>"
        f"{_state_badge_html(tone, label)}"
        f"{_quality_badge_html(quality)}"
        f"</span>"
        f"<strong>{semantic_value_html(label, value)}</strong>"
        "</div>"
    )


def render_panel_title(title: str, subtitle: str | None = None) -> None:
    import streamlit as st

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


def render_live_banner(
    title: str,
    subtitle: str,
    *,
    live_label: str = "LIVE",
    live_hint: str = "Auto-refresh enabled",
    live_meta: str | None = None,
) -> None:
    import streamlit as st

    _render_compact_panel_styles()
    meta_html = (
        f"<span class='compact-live-meta'>{escape(sanitize_text(live_meta))}</span>" if live_meta else ""
    )
    st.markdown(
        f"""
        <style>
        .compact-live-banner {{
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 0.72rem 0.82rem;
            margin: 0.1rem 0 0.44rem;
            border-radius: 0.72rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: linear-gradient(180deg, rgba(15, 18, 24, 0.99), rgba(9, 12, 16, 0.99));
            box-shadow: none;
        }}
        .compact-live-banner__title {{
            color: #f8fbff;
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 0.98rem;
            font-weight: 950;
            line-height: 1.04;
            letter-spacing: 0.02em;
        }}
        .compact-live-banner__subtitle {{
            margin-top: 0.12rem;
            color: #93a0aa;
            font-size: 0.68rem;
            line-height: 1.18;
        }}
        .compact-live-banner__right {{
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 0.32rem;
            align-items: center;
        }}
        .compact-live-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.26rem 0.52rem;
            border-radius: 0.46rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(12, 15, 20, 0.98);
            color: #f8fbff;
            font-size: 0.54rem;
            font-weight: 850;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}
        .compact-state-pill {{
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.22rem 0.44rem;
            border-radius: 0.42rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(12, 15, 20, 0.98);
            color: #f8fbff;
            font-size: 0.48rem;
            font-weight: 900;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}
        .compact-state-pill--live {{
            border-color: rgba(105, 211, 154, 0.3);
            color: #98ebb9;
        }}
        .compact-state-pill--stale {{
            border-color: rgba(215, 171, 87, 0.3);
            color: #e6c67c;
        }}
        .compact-state-pill--blocked {{
            border-color: rgba(217, 109, 103, 0.3);
            color: #e5a09d;
        }}
        .compact-live-pill__dot {{
            width: 0.38rem;
            height: 0.38rem;
            border-radius: 999px;
            background: #69d39a;
            box-shadow: 0 0 0 0.12rem rgba(105, 211, 154, 0.14);
            animation: compactPulse 1.8s ease-in-out infinite;
        }}
        .compact-live-meta {{
            color: #a1abb4;
            font-size: 0.52rem;
        }}
        @keyframes compactPulse {{
            0% {{ transform: scale(0.92); opacity: 0.72; }}
            50% {{ transform: scale(1.08); opacity: 1; }}
            100% {{ transform: scale(0.92); opacity: 0.72; }}
        }}
        @media (max-width: 920px) {{
            .compact-live-banner {{
                flex-direction: column;
            }}
            .compact-live-banner__right {{
                justify-content: flex-start;
            }}
        }}
        </style>
        <div class="compact-live-banner">
          <div>
            <div class="compact-live-banner__title">{escape(sanitize_text(title))}</div>
            <div class="compact-live-banner__subtitle">{escape(sanitize_text(subtitle))}</div>
          </div>
          <div class="compact-live-banner__right">
            <span class="compact-live-pill"><span class="compact-live-pill__dot"></span>{escape(sanitize_text(live_label))}</span>
            <span class="compact-live-meta">{escape(sanitize_text(live_hint))}</span>
            <span class="compact-state-pill compact-state-pill--live">LIVE</span>
            <span class="compact-state-pill compact-state-pill--stale">STALE</span>
            <span class="compact-state-pill compact-state-pill--blocked">BLOCKED</span>
            {meta_html}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_legend_card(
    title: str = "Legend",
    *,
    subtitle: str | None = None,
    items: Iterable[dict[str, object]] | None = None,
) -> None:
    import streamlit as st

    _render_compact_panel_styles()
    legend_items = list(items) if items is not None else default_state_legend_items()
    subtitle_html = (
        f"<div class='compact-card-subtitle'>{escape(sanitize_text(subtitle))}</div>" if subtitle else ""
    )
    body = "".join(_render_legend_item(item) for item in legend_items)
    st.markdown(
        f"""
        <div class="compact-info-card">
          <div class="compact-card-title">{escape(sanitize_text(title))}</div>
          {subtitle_html}
          <div class="compact-legend-grid">
            {body}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chart_legend_card(
    title: str = "Curve Legend",
    *,
    subtitle: str | None = None,
    items: Iterable[dict[str, object]] | None = None,
) -> None:
    import streamlit as st

    _render_compact_panel_styles()
    legend_items = list(items) if items is not None else default_market_evidence_curve_legend_items()
    subtitle_html = (
        f"<div class='compact-card-subtitle'>{escape(sanitize_text(subtitle))}</div>" if subtitle else ""
    )
    body = "".join(_render_chart_legend_item(item) for item in legend_items)
    st.markdown(
        f"""
        <div class="compact-info-card">
          <div class="compact-card-title">{escape(sanitize_text(title))}</div>
          {subtitle_html}
          <div class="compact-legend-grid compact-legend-grid--chart">
            {body}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def default_state_legend_items() -> list[dict[str, object]]:
    return [
        {"kind": "state", "label": "LIVE", "meaning": "Realtime update", "tone": "live"},
        {"kind": "state", "label": "STALE", "meaning": "Needs refresh", "tone": "stale"},
        {"kind": "state", "label": "ALERT", "meaning": "Market alarm", "tone": "alert"},
        {"kind": "state", "label": "ANOM", "meaning": "Safety yellow anomaly", "tone": "anom"},
        {"kind": "state", "label": "BLOCKED", "meaning": "Gate / validation stop", "tone": "blocked"},
        {"kind": "quality", "label": "B", "meaning": "Bad data quality", "tone": "bad"},
    ]


def default_market_evidence_curve_legend_items() -> list[dict[str, object]]:
    return [
        {"kind": "line", "label": "Market probability", "meaning": "Market-implied odds trend", "color": "#2f9bff"},
        {"kind": "line", "label": "Forecast", "meaning": "Model forecast series", "color": "#ffad28"},
        {"kind": "line", "label": "Observation", "meaning": "Canonical observation series", "color": "#35d46f"},
        {"kind": "line", "label": "Official threshold", "meaning": "Policy baseline / comparator", "color": "#d8e2ed", "style": "dashed"},
        {"kind": "marker", "label": "Alert", "meaning": "Alert or gate marker", "color": "#ff493f"},
    ]


def default_signal_trend_legend_items() -> list[dict[str, object]]:
    return [
        {"kind": "line", "label": "Alerts", "meaning": "Alert event count over time", "color": "#ff5b57"},
        {"kind": "line", "label": "Anomalies", "meaning": "Anomaly event count over time", "color": "#ffd34d"},
        {"kind": "line", "label": "Ops Issues", "meaning": "Scanner and pipeline issues", "color": "#2f9bff"},
        {"kind": "marker", "label": "Red", "meaning": "Critical severity bucket", "color": "#ff5b57"},
        {"kind": "marker", "label": "Amber", "meaning": "Warning severity bucket", "color": "#ffb23f"},
        {"kind": "marker", "label": "Blue", "meaning": "Info or runtime bucket", "color": "#2f9bff"},
    ]


def _render_legend_item(item: dict[str, object]) -> str:
    kind = str(item.get("kind") or "state")
    label = sanitize_text(item.get("label") or item.get("key") or "-")
    meaning = sanitize_text(item.get("meaning") or "-")
    tone = sanitize_text(item.get("tone") or "muted").lower()
    if kind == "quality":
        mark = "<span class='compact-quality-pill compact-quality-pill--bad'>B</span>"
    elif kind == "state":
        mark = f"<span class='compact-state-pill compact-state-pill--{tone}'>{escape(label)}</span>"
    else:
        mark = f"<span class='compact-state-pill compact-state-pill--{tone}'>{escape(label)}</span>"
    return (
        "<span class='compact-legend-item'>"
        f"{mark}"
        f"<span class='compact-legend-text'>{escape(meaning)}</span>"
        "</span>"
    )


def _render_chart_legend_item(item: dict[str, object]) -> str:
    kind = str(item.get("kind") or "line")
    label = sanitize_text(item.get("label") or "-")
    meaning = sanitize_text(item.get("meaning") or "-")
    color = str(item.get("color") or "#2f9bff")
    style = str(item.get("style") or "solid").lower()
    if kind == "marker":
        mark = f"<span class='compact-legend-mark compact-legend-mark--dot' style='background:{escape(color)}'></span>"
    elif style == "dashed":
        mark = f"<span class='compact-legend-mark compact-legend-mark--line-dashed' style='border-top-color:{escape(color)}'></span>"
    else:
        mark = f"<span class='compact-legend-mark compact-legend-mark--line' style='background:{escape(color)}'></span>"
    return (
        "<span class='compact-legend-item'>"
        f"{mark}"
        f"<span class='compact-legend-text'><strong>{escape(label)}</strong> {escape(meaning)}</span>"
        "</span>"
    )


def render_stat_strip(items: Iterable[tuple[str, object]], *, title: str | None = None) -> None:
    import streamlit as st

    _render_compact_panel_styles()
    items = list(items)
    if not items:
        return
    title_html = (
        f"<div class='compact-card-title' style='margin-bottom:0.3rem;'>{escape(sanitize_text(title))}</div>"
        if title
        else ""
    )
    cols = st.columns(len(items), gap="small")
    for col, (label, value) in zip(cols, items):
        tone = semantic_tone(label, value)
        quality = quality_from_value(value)
        with col:
            with st.container(border=True):
                st.markdown(
                    f"""
                    <div class="compact-stat-tile compact-stat-tile--{tone}">
                      <div class="compact-stat-tile__label-row">
                        <div class="compact-stat-tile__label">{escape(sanitize_text(label))}</div>
                        {_state_badge_html(tone)}
                        {_quality_badge_html(quality)}
                      </div>
                      <div class="compact-stat-tile__value">{escape(fmt_value(value))}</div>
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
    import streamlit as st

    _render_compact_panel_styles()
    with st.container(border=True):
        st.caption(sanitize_text(title))
        if metric_label is not None:
            metric_tone = semantic_tone(metric_label, metric_value)
            st.markdown(
                f"""
                <div class="compact-metric compact-metric--{metric_tone}">
                  <span>{escape(sanitize_text(metric_label))}</span>
                  <strong>{escape(fmt_value(metric_value))}</strong>
                </div>
                """,
                unsafe_allow_html=True,
            )

        row_items = [(label, value) for label, value in items if not _is_empty_value(value)]
        if not row_items:
            st.caption("-")
            return

        for label, value in row_items:
            tone = semantic_tone(label, value)
            value_color = _tone_color(tone)
            quality = quality_from_value(value)
            st.markdown(
                f"""
                <div style="border-top:1px solid var(--compact-divider-color, rgba(35,72,82,0.08));padding:0.14rem 0 0.12rem;margin-top:0.14rem;">
                  <div style="display:flex;align-items:center;gap:0.4rem;justify-content:space-between;margin-bottom:0.04rem;">
                    <div style="display:flex;align-items:center;gap:0.32rem;min-width:0;">
                      <div style="color:var(--compact-label-color, #52656f);font-size:0.58rem;font-weight:850;letter-spacing:0.08em;text-transform:uppercase;line-height:1.14;">{escape(sanitize_text(label))}</div>
                      {_state_badge_html(tone, label)}
                      {_quality_badge_html(quality)}
                    </div>
                  </div>
                  <div style="color:var(--compact-value-color, {value_color});font-size:0.74rem;font-weight:850;line-height:1.20;font-variant-numeric:tabular-nums;word-break:break-word;overflow-wrap:anywhere;white-space:normal;">{escape(fmt_value(value))}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_compact_note(text: str, tone: str = "info") -> None:
    import streamlit as st

    _render_compact_panel_styles()
    st.markdown(
        f"""
        <div class="compact-note compact-note--{escape(tone)}">
          {escape(sanitize_text(text))}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _is_empty_value(value: object) -> bool:
    return value in (None, "", "-", [], {})


def _coerce_float(value: object | None) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, dict):
        return _coerce_float(value.get("value"))
    text = sanitize_text(value).replace(",", "").strip()
    try:
        return float(text)
    except Exception:
        return None


def _tone_color(tone: str) -> str:
    return {
        "ok": "#0f9f71",
        "warning": "#c47a15",
        "critical": "#c44d46",
        "neutral": "#0f3f4a",
        "muted": "#667782",
    }.get(tone, "#0f3f4a")


def quality_from_value(value: object) -> str:
    if isinstance(value, dict):
        quality = str(value.get("data_quality") or value.get("quality") or value.get("quality_level") or "").strip().lower()
        if quality in {"bad", "poor", "low"}:
            return "bad"
        if quality in {"mixed", "warning", "fair"}:
            return "fair"
        if quality in {"good", "high", "excellent"}:
            return "good"
    return "good"


def with_data_quality(value: object, quality: str = "bad", reason: str | None = None) -> dict:
    payload: dict[str, object] = {"value": value, "data_quality": quality}
    if reason:
        payload["data_quality_reason"] = reason
    return payload


def _state_badge_html(tone: str, label: object | None = None) -> str:
    label_text = sanitize_text(label).lower()
    if tone == "critical":
        if any(token in label_text for token in ("gate", "execution", "authorization", "blocked", "block", "constraint")):
            state = ("BLOCKED", "compact-kv-state--blocked")
        else:
            state = ("ALERT", "compact-kv-state--alert")
    elif tone == "warning":
        if any(token in label_text for token in ("anom", "anomaly", "anomal", "deviation", "exception")):
            state = ("ANOM", "compact-kv-state--anom")
        else:
            state = ("STALE", "compact-kv-state--stale")
    else:
        state = {
            "ok": ("LIVE", "compact-kv-state--live"),
            "neutral": ("LIVE", "compact-kv-state--live"),
            "muted": ("N/A", "compact-kv-state--muted"),
        }.get(tone, ("LIVE", "compact-kv-state--live"))
    label, class_name = state
    return f"<span class='compact-kv-state {class_name}'>{escape(label)}</span>"


def _quality_badge_html(quality: str) -> str:
    quality = str(quality or "").strip().lower()
    if quality in {"", "good", "high", "excellent"}:
        return ""
    return "<span class='compact-quality-pill compact-quality-pill--bad'>B</span>"


def _render_compact_panel_styles() -> None:
    import streamlit as st

    st.markdown(
        """
        <style>
        .compact-panel-heading {
            margin: 0.28rem 0 0.18rem;
        }
        .compact-panel-title {
            color: var(--compact-panel-title-color, #f8fbff);
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 1.16rem;
            font-weight: 950;
            line-height: 1.04;
            letter-spacing: 0.02em;
        }
        .compact-panel-subtitle {
            margin-top: 0.08rem;
            color: var(--compact-panel-subtitle-color, #87919b);
            font-size: 0.78rem;
            line-height: 1.2;
        }
        .compact-info-card {
            border: 1px solid var(--compact-panel-border-color, rgba(255, 255, 255, 0.11));
            border-radius: 10px;
            background: var(--compact-panel-bg, rgba(12, 15, 20, 0.98));
            padding: 0.38rem 0.42rem;
            margin: 0.22rem 0;
            box-shadow: none;
        }
        .compact-card-title {
            color: var(--compact-card-title-color, #aeb8c1);
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.61rem;
            font-weight: 900;
            letter-spacing: 0.10em;
            text-transform: uppercase;
        }
        .compact-metric {
            margin-top: 0.24rem;
            border: 1px solid var(--compact-metric-border-color, rgba(255, 255, 255, 0.12));
            border-radius: 8px;
            background: var(--compact-metric-bg, rgba(14, 18, 24, 0.98));
            padding: 0.28rem 0.34rem;
        }
        .compact-metric span,
        .compact-kv-row span {
            color: var(--compact-label-color, #8f9aa5);
            font-family: "SF Mono", "Menlo", monospace;
            font-size: 0.65rem;
            font-weight: 900;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }
        .compact-metric strong {
            display: block;
            margin-top: 0.08rem;
            color: var(--compact-value-color, #f8fbff);
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 1.18rem;
            font-weight: 950;
            line-height: 1.05;
        }
        .compact-metric--ok strong,
        .semantic-value--ok {
            color: var(--compact-ok-color, #0f9f71);
        }
        .compact-metric--warning strong,
        .semantic-value--warning {
            color: var(--compact-warning-color, #c47a15);
        }
        .compact-metric--critical strong,
        .semantic-value--critical {
            color: var(--compact-critical-color, #c44d46);
        }
        .compact-metric--neutral strong,
        .semantic-value--neutral {
            color: var(--compact-neutral-color, #edf2f6);
        }
        .semantic-value--muted {
            color: var(--compact-muted-color, #8f9aa5);
        }
        .compact-kv-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 0.18rem;
            margin-top: 0.30rem;
        }
        .compact-kv-row {
            display: grid;
            grid-template-columns: minmax(6.5rem, 0.75fr) minmax(0, 1fr);
            gap: 0.34rem;
            align-items: center;
            border: 1px solid var(--compact-row-border-color, rgba(255, 255, 255, 0.12));
            border-radius: 8px;
            background: var(--compact-row-bg, rgba(12, 15, 20, 0.98));
            padding: 0.2rem 0.28rem;
            min-height: 1.9rem;
        }
        .compact-kv-row__label {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.28rem;
            min-width: 0;
        }
        .compact-kv-row__label-text {
            min-width: 0;
        }
        .compact-legend-grid {
            display: flex;
            flex-wrap: wrap;
            gap: 0.24rem 0.42rem;
            align-items: center;
            margin-top: 0.3rem;
        }
        .compact-legend-grid--chart {
            gap: 0.28rem 0.5rem;
        }
        .compact-legend-item {
            display: inline-flex;
            align-items: center;
            gap: 0.28rem;
            min-width: 0;
        }
        .compact-legend-mark {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            flex: 0 0 auto;
        }
        .compact-legend-mark--line {
            width: 1rem;
            height: 0.2rem;
            border-radius: 999px;
        }
        .compact-legend-mark--line-dashed {
            width: 1rem;
            height: 0;
            border-top: 0.12rem dashed;
        }
        .compact-legend-mark--dot {
            width: 0.52rem;
            height: 0.52rem;
            border-radius: 999px;
        }
        .compact-legend-text {
            color: #a2acb6;
            font-size: 0.64rem;
            line-height: 1.15;
        }
        .compact-stat-strip {
            display: flex;
            flex-wrap: nowrap;
            gap: 0.32rem;
            overflow-x: auto;
            padding-bottom: 0.04rem;
        }
        .compact-stat-tile {
            flex: 1 1 0;
            min-width: 7.5rem;
            padding: 0.38rem 0.46rem;
            border-radius: 0.6rem;
            border: 1px solid rgba(255, 255, 255, 0.12);
            background: rgba(12, 15, 20, 0.98);
        }
        .compact-stat-tile--ok {
            border-color: rgba(15, 159, 113, 0.24);
            background: rgba(11, 22, 16, 0.98);
        }
        .compact-stat-tile--warning {
            border-color: rgba(215, 171, 87, 0.26);
            background: rgba(28, 23, 13, 0.98);
        }
        .compact-stat-tile--critical {
            border-color: rgba(217, 109, 103, 0.28);
            background: rgba(29, 16, 16, 0.98);
        }
        .compact-stat-tile--neutral {
            border-color: rgba(91, 148, 225, 0.18);
            background: rgba(12, 15, 20, 0.98);
        }
        .compact-stat-tile__label-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.22rem;
            min-width: 0;
        }
        .compact-stat-tile__label {
            color: #dfe6ee;
            font-size: 0.54rem;
            font-weight: 900;
            letter-spacing: 0.10em;
            text-transform: uppercase;
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .compact-stat-tile__value {
            margin-top: 0.1rem;
            color: #f8fbff;
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 1.18rem;
            font-weight: 950;
            line-height: 1.04;
            font-variant-numeric: tabular-nums;
            word-break: break-word;
        }
        .compact-kv-state {
            display: inline-flex;
            align-items: center;
            padding: 0.12rem 0.3rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            font-size: 0.48rem;
            font-weight: 900;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .compact-kv-state--live {
            border-color: rgba(105, 211, 154, 0.22);
            color: #8fe2b0;
            background: rgba(16, 25, 20, 0.9);
        }
        .compact-kv-state--stale {
            border-color: rgba(215, 171, 87, 0.22);
            color: #d9b96d;
            background: rgba(29, 24, 16, 0.9);
        }
        .compact-kv-state--alert {
            border-color: rgba(217, 109, 103, 0.22);
            color: #e79a95;
            background: rgba(31, 19, 19, 0.9);
        }
        .compact-kv-state--anom {
            border-color: rgba(215, 171, 87, 0.22);
            color: #e6c67c;
            background: rgba(34, 29, 16, 0.9);
        }
        .compact-kv-state--blocked {
            border-color: rgba(217, 109, 103, 0.22);
            color: #de8f8a;
            background: rgba(31, 19, 19, 0.9);
        }
        .compact-kv-state--muted {
            border-color: rgba(255, 255, 255, 0.08);
            color: #8f9aa5;
            background: rgba(16, 20, 27, 0.9);
        }
        .compact-quality-pill {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 1rem;
            height: 1rem;
            padding: 0 0.16rem;
            border-radius: 999px;
            border: 1px solid rgba(255, 255, 255, 0.12);
            font-size: 0.54rem;
            font-weight: 950;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            white-space: nowrap;
        }
        .compact-quality-pill--bad {
            border-color: rgba(232, 92, 215, 0.58);
            color: #ff8cf0;
            background: rgba(52, 10, 48, 0.98);
        }
        .compact-card-subtitle {
            color: #9ba9b4;
            font-size: 0.62rem;
            line-height: 1.18;
            margin-top: 0.04rem;
        }
        .compact-kv-row--ok {
            border-color: var(--compact-ok-border-color, rgba(15, 159, 113, 0.22));
            background: var(--compact-ok-bg, rgba(15, 159, 113, 0.06));
        }
        .compact-kv-row--warning {
            border-color: var(--compact-warning-border-color, rgba(196, 122, 21, 0.24));
            background: var(--compact-warning-bg, rgba(196, 122, 21, 0.07));
        }
        .compact-kv-row--critical {
            border-color: var(--compact-critical-border-color, rgba(196, 77, 70, 0.26));
            background: var(--compact-critical-bg, rgba(196, 77, 70, 0.07));
        }
        .compact-kv-row strong {
            color: var(--compact-value-color, #eef3f7);
            font-family: "Avenir Next Condensed", "DIN Condensed", "Trebuchet MS", sans-serif;
            font-size: 0.9rem;
            font-weight: 900;
            line-height: 1.08;
            overflow-wrap: anywhere;
            text-align: right;
        }
        .compact-note {
            border: 1px solid var(--compact-note-border-color, rgba(255, 255, 255, 0.12));
            border-radius: 8px;
            background: var(--compact-note-bg, rgba(12, 15, 20, 0.98));
            color: var(--compact-note-color, #a2acb6);
            padding: 0.3rem 0.38rem;
            margin: 0.22rem 0;
            font-size: 0.74rem;
            line-height: 1.22;
        }
        .compact-note--warning {
            border-color: var(--compact-note-warning-border-color, rgba(215, 171, 87, 0.24));
            background: var(--compact-note-warning-bg, rgba(29, 24, 16, 0.96));
            color: var(--compact-note-warning-color, #d9b96d);
        }
        .compact-note--critical {
            border-color: var(--compact-note-critical-border-color, rgba(217, 109, 103, 0.24));
            background: var(--compact-note-critical-bg, rgba(31, 19, 19, 0.96));
            color: var(--compact-note-critical-color, #de8f8a);
        }
        .compact-note--ok {
            border-color: var(--compact-note-ok-border-color, rgba(105, 211, 154, 0.22));
            background: var(--compact-note-ok-bg, rgba(16, 25, 20, 0.96));
            color: var(--compact-note-ok-color, #8fe2b0);
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
