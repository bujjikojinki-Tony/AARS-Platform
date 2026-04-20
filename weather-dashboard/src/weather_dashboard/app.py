from __future__ import annotations

from difflib import SequenceMatcher
import html
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

from weather_dashboard.loaders.bias_report_loader import BiasReportLoader
from weather_dashboard.loaders.comparison_history_loader import ComparisonHistoryLoader
from weather_dashboard.loaders.dashboard_rows_loader import DashboardRowsLoader
from weather_dashboard.loaders.gamma_search_loader import GammaSearchLoader
from weather_dashboard.loaders.jsonl_loader import JsonlLoader
from weather_dashboard.loaders.market_bundle_loader import MarketBundleLoader
from weather_dashboard.loaders.realtime_forecast_loader import RealtimeForecastLoader
from weather_dashboard.loaders.realtime_market_loader import RealtimeMarketLoader
from weather_dashboard.loaders.rulebook_loader import RulebookLoader
from weather_dashboard.loaders.signal_loader import SignalLoader
from weather_dashboard.loaders.timeseries_loader import TimeSeriesLoader
from weather_dashboard.loaders.wunderground_loader import WundergroundShanghaiLoader
from weather_dashboard.settings import (
    BIAS_REPORT_CSV,
    BACKTEST_REPORT_JSON,
    CALIBRATION_REPORT_JSON,
    COMPARISON_HISTORY_JSON,
    DASHBOARD_ROWS_JSON,
    EXECUTION_APPROVAL_DB_PATH,
    EXECUTION_DASHBOARD_INTENT_JSON,
    EXECUTION_GATEWAY_DIR,
    EXECUTION_PENDING_INTENTS_DIR,
    EXECUTION_PRODUCTION_READINESS_JSON,
    EXECUTION_WHITELIST_YAML,
    GATE_STACK_OPS_ALERTS_JSONL,
    HUMAN_FILL_RECONCILIATION_REPORT_JSON,
    LABEL_COVERAGE_REPORT_JSON,
    MANUAL_ADVISORY_AUDIT_JSONL,
    TELEGRAM_APPROVAL_SIGNAL_JSON,
    TELEGRAM_OPS_DELIVERY_LOG_JSONL,
    TELEGRAM_OPS_NOTIFICATIONS_JSONL,
    GAMMA_API_BASE_URL,
    GAMMA_SEARCH_LIMIT,
    GATE_STACK_API_JSON,
    MARKET_BUNDLES_JSON,
    MONITORING_STATUS_JSON,
    OPERATOR_MARKET_CONTEXT_JSON,
    PINNED_MARKET_ID,
    POSITION_SNAPSHOT_JSON,
    PINNED_MARKET_OVERRIDE_JSON,
    PROBABILITY_SHADOW_REPORT_JSON,
    PROBABILITY_STATES_DIR,
    RECENT_MARKETS_JSON,
    REALTIME_FORECAST_JSON,
    REALTIME_FORECAST_SNAPSHOTS_GLOB,
    REALTIME_MARKET_JSON,
    REALTIME_MARKET_SNAPSHOTS_GLOB,
    RESOLVER_REPORT_JSON,
    RULEBOOK_JSON,
    SIGNAL_JSON,
    MODEL_VALIDATION_REPORT_JSON,
    TRAINING_SAMPLES_JSONL,
    VALIDATION_FRESHNESS_STATUS_JSON,
    SHANGHAI_JOINED_HISTORY_JSON,
    WATCHLIST_OVERRIDES_JSON,
    WATCHLIST_REMOVED_JSON,
    WORKSPACE_DIR,
    WUNDERGROUND_SHANGHAI_CACHE_JSON,
    TIMESERIES_JSON,
    UNIFIED_STATUS_JSON,
)
from weather_dashboard.ui.architecture_console import (
    find_resolver_rule,
    render_architecture_brief,
    render_architecture_styles,
    render_layer_ribbon,
    render_pipeline_flow,
    render_pipeline_summary,
)
from weather_dashboard.ui.bias_summary_panel import render_bias_summary_panel
from weather_dashboard.ui.comparison_focus_panel import render_comparison_focus_panel
from weather_dashboard.ui.comparison_table import render_comparison_table
from weather_dashboard.ui.command_center import (
    render_app_header,
    render_command_center,
    render_deerflow_signature,
)
from weather_dashboard.ui.command_metric_cards import render_command_metric_cards
from weather_dashboard.ui.compact_gate_stack_panel import (
    build_compact_gate_stack_summary,
    render_compact_gate_stack_panel,
)
from weather_dashboard.ui.data_alignment_panel import render_data_alignment_panel
from weather_dashboard.ui.history_relationship_panel import render_history_relationship_panel
from weather_dashboard.ui.history_forecast_panel import render_history_forecast_panel
from weather_dashboard.ui.detail_panel import render_detail_panel
from weather_dashboard.ui.divergence_chart import render_divergence_chart
from weather_dashboard.ui.divergence_trend_chart import render_divergence_trend_chart
from weather_dashboard.ui.execution_gate_panel import render_execution_gate_panel
from weather_dashboard.ui.field_dictionary_panel import render_field_dictionary_panel
from weather_dashboard.ui.filters import render_filters
from weather_dashboard.ui.live_status_panel import render_live_status_panel
from weather_dashboard.ui.market_panel import render_market_panel
from weather_dashboard.ui.market_evidence_chart import render_market_evidence_chart
from weather_dashboard.ui.market_snapshots_panel import render_market_snapshots_panel
from weather_dashboard.ui.manual_advisory_reconciliation_panel import (
    render_manual_advisory_reconciliation_panel,
)
from weather_dashboard.ui.model_validation_panel import render_model_validation_panel
from weather_dashboard.ui.ops_alert_panel import render_ops_alert_panel
from weather_dashboard.ui.operator_messages import NO_COMPARISON_HISTORY, NO_TIMESERIES
from weather_dashboard.ui.operator_context_badge import (
    build_operator_context_badge_context,
    render_operator_context_badge,
)
from weather_dashboard.ui.operator_focus_panel import (
    build_operator_focus_summary,
    render_operator_focus_banner,
)
from weather_dashboard.ui.overview import render_overview
from weather_dashboard.ui.operator_closure_panel import render_operator_closure_panel
from weather_dashboard.ui.probability_shadow_panel import (
    render_probability_shadow_panel,
    render_probability_shadow_report_panel,
)
from weather_dashboard.ui.pipeline_sync_context import (
    build_pipeline_sync_context,
    render_pipeline_sync_context,
)
from weather_dashboard.ui.raw_json_panel import render_raw_json_panel
from weather_dashboard.ui.read_only_account_panel import (
    build_read_only_account_summary,
    render_read_only_account_panel,
)
from weather_dashboard.ui.recent_markets_panel import render_recent_markets_panel
from weather_dashboard.ui.resolver_status_panel import render_resolver_status_panel
from weather_dashboard.ui.rule_station_panel import render_rule_station_panel
from weather_dashboard.ui.signal_panel import render_signal_panel
from weather_dashboard.ui.theme import render_theme
from weather_dashboard.ui.top_parameter_ribbon import (
    build_top_parameter_ribbon_summary,
    render_top_parameter_ribbon,
)
from weather_dashboard.ui.timeline_panel import render_timeline_panel
from weather_dashboard.ui.trade_decision_panel import render_trade_decision_panel
from weather_dashboard.ui.timeseries_panel import render_timeseries_panel
from weather_dashboard.ui.unified_status_strip import render_unified_status_strip
from weather_dashboard.ui.worker_health_strip import render_worker_health_strip
from weather_dashboard.utils.dataframe_utils import available_sort_columns, safe_sort_dashboard_rows


st.set_page_config(
    page_title="Weather vs Polymarket Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
)

SAFE_MODE = os.getenv("WEATHER_DASHBOARD_SAFE_MODE", "").lower() in {"1", "true", "yes"}
ENABLE_LIVE_WUNDERGROUND = os.getenv("WEATHER_DASHBOARD_ENABLE_LIVE_WUNDERGROUND", "").lower() in {
    "1",
    "true",
    "yes",
}

if SAFE_MODE:
    st.warning("Weather Dashboard Safe Mode: custom theme is disabled for display debugging.")
else:
    render_theme()
render_architecture_styles()
render_app_header()

rows_loader = DashboardRowsLoader()
signal_loader = SignalLoader()
market_loader = MarketBundleLoader()
realtime_market_loader = RealtimeMarketLoader()
realtime_forecast_loader = RealtimeForecastLoader()
timeseries_loader = TimeSeriesLoader()
bias_loader = BiasReportLoader()
rulebook_loader = RulebookLoader()
history_loader = ComparisonHistoryLoader()
jsonl_loader = JsonlLoader()

try:
    df = rows_loader.load_df(DASHBOARD_ROWS_JSON)
except Exception as e:
    st.error(f"Failed to load dashboard rows: {e}")
    df = None

try:
    signal_payload = signal_loader.load(SIGNAL_JSON)
except Exception as e:
    st.error(f"Failed to load signal payload: {e}")
    signal_payload = {}

try:
    market_bundles = market_loader.load(MARKET_BUNDLES_JSON)
except Exception as e:
    st.error(f"Failed to load market bundles: {e}")
    market_bundles = []

try:
    realtime_market = realtime_market_loader.load(REALTIME_MARKET_JSON)
except Exception as e:
    st.error(f"Failed to load realtime market: {e}")
    realtime_market = None

try:
    market_snapshots = realtime_market_loader.load_many(REALTIME_MARKET_SNAPSHOTS_GLOB)
except Exception as e:
    st.error(f"Failed to load market snapshots: {e}")
    market_snapshots = []

watchlist_snapshots = list(market_snapshots)
if realtime_market and all(
    str(snapshot.get("market_id")) != str(realtime_market.get("market_id"))
    for snapshot in watchlist_snapshots
):
    watchlist_snapshots.insert(0, realtime_market)

try:
    realtime_forecast = realtime_forecast_loader.load(REALTIME_FORECAST_JSON)
except Exception as e:
    st.error(f"Failed to load realtime forecast: {e}")
    realtime_forecast = None

try:
    realtime_forecast_snapshots = realtime_forecast_loader.load_many(REALTIME_FORECAST_SNAPSHOTS_GLOB)
except Exception:
    realtime_forecast_snapshots = []

try:
    ts_df = timeseries_loader.load_df(TIMESERIES_JSON)
except Exception:
    ts_df = None

try:
    bias_df = bias_loader.load_df(BIAS_REPORT_CSV)
except Exception:
    bias_df = None

try:
    rulebook_payload = rulebook_loader.load(RULEBOOK_JSON)
except Exception:
    rulebook_payload = None

try:
    history_df = history_loader.load_df(COMPARISON_HISTORY_JSON)
except Exception:
    history_df = None

try:
    training_samples_df = jsonl_loader.load_df(TRAINING_SAMPLES_JSONL)
except Exception:
    training_samples_df = None

try:
    manual_advisory_audit_events = jsonl_loader.load_records(MANUAL_ADVISORY_AUDIT_JSONL)
except Exception:
    manual_advisory_audit_events = []

try:
    gate_stack_ops_alert_events = jsonl_loader.load_records(GATE_STACK_OPS_ALERTS_JSONL)
except Exception:
    gate_stack_ops_alert_events = []

try:
    telegram_ops_notifications = jsonl_loader.load_records(TELEGRAM_OPS_NOTIFICATIONS_JSONL)
except Exception:
    telegram_ops_notifications = []

try:
    telegram_ops_delivery_events = jsonl_loader.load_records(TELEGRAM_OPS_DELIVERY_LOG_JSONL)
except Exception:
    telegram_ops_delivery_events = []

try:
    shanghai_history_reference = realtime_forecast_loader.load(SHANGHAI_JOINED_HISTORY_JSON)
except Exception:
    shanghai_history_reference = None

try:
    resolver_report = realtime_forecast_loader.load(RESOLVER_REPORT_JSON)
except Exception:
    resolver_report = None

try:
    probability_shadow_report = realtime_forecast_loader.load(PROBABILITY_SHADOW_REPORT_JSON)
except Exception:
    probability_shadow_report = None

try:
    calibration_report = realtime_forecast_loader.load(CALIBRATION_REPORT_JSON)
except Exception:
    calibration_report = None

try:
    backtest_report = realtime_forecast_loader.load(BACKTEST_REPORT_JSON)
except Exception:
    backtest_report = None

try:
    model_validation_report = realtime_forecast_loader.load(MODEL_VALIDATION_REPORT_JSON)
except Exception:
    model_validation_report = None

try:
    validation_freshness_status = realtime_forecast_loader.load(VALIDATION_FRESHNESS_STATUS_JSON)
except Exception:
    validation_freshness_status = None

try:
    label_coverage_report = realtime_forecast_loader.load(LABEL_COVERAGE_REPORT_JSON)
except Exception:
    label_coverage_report = None

try:
    production_readiness_report = realtime_forecast_loader.load(EXECUTION_PRODUCTION_READINESS_JSON)
except Exception:
    production_readiness_report = None

try:
    human_fill_reconciliation_report = realtime_forecast_loader.load(
        HUMAN_FILL_RECONCILIATION_REPORT_JSON
    )
except Exception:
    human_fill_reconciliation_report = None

try:
    position_snapshot = realtime_forecast_loader.load(POSITION_SNAPSHOT_JSON)
except Exception:
    position_snapshot = None

try:
    monitoring_status_report = realtime_forecast_loader.load(MONITORING_STATUS_JSON)
except Exception:
    monitoring_status_report = None

try:
    unified_status_report = realtime_forecast_loader.load(UNIFIED_STATUS_JSON)
except Exception:
    unified_status_report = None
try:
    gate_stack_api_report = realtime_forecast_loader.load(GATE_STACK_API_JSON)
except Exception:
    gate_stack_api_report = None

operator_mode = str(
    ((unified_status_report or {}).get("operator") or {}).get("operator_mode") or "dry_run_guarded"
)


def _load_watchlist_overrides(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _load_json_dict(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_json_list(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    return []


def _freshness_bucket_for_snapshot(snapshot: dict | None) -> str:
    if not snapshot:
        return "unknown"
    updated_at = snapshot.get("updated_at")
    if not updated_at:
        return "unknown"
    try:
        dt = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
    except ValueError:
        return "unknown"
    age_minutes = max((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds() / 60.0, 0.0)
    if age_minutes <= 5:
        return "fresh"
    if age_minutes <= 30:
        return "warm"
    return "stale"


def _edge_bucket(probability_state: dict | None) -> str:
    value = probability_state.get("confidence_adjusted_edge") if probability_state else None
    try:
        edge = float(value)
    except (TypeError, ValueError):
        return "blocked"
    if edge >= 0.05:
        return "positive"
    if edge <= -0.05:
        return "negative"
    return "flat"


def _build_watchlist_enriched_snapshots(
    market_snapshots: list[dict],
    *,
    resolver_report: dict | None,
    probability_shadow_report: dict | None,
) -> list[dict]:
    probability_by_market = {}
    if probability_shadow_report:
        for state in probability_shadow_report.get("states", []):
            if isinstance(state, dict) and state.get("market_id") is not None:
                probability_by_market[str(state.get("market_id"))] = state

    enriched: list[dict] = []
    for snapshot in market_snapshots:
        market_id = str(snapshot.get("market_id") or "")
        resolver_rule = find_resolver_rule(resolver_report, market_id)
        probability_state = probability_by_market.get(market_id)
        enriched.append(
            {
                **snapshot,
                "resolver_status": (resolver_rule or {}).get("resolver_status") or "unknown",
                "confidence_adjusted_edge": (probability_state or {}).get("confidence_adjusted_edge"),
                "edge_bucket": _edge_bucket(probability_state),
                "freshness_bucket": _freshness_bucket_for_snapshot(snapshot),
            }
        )
    return enriched


watchlist_snapshots = _build_watchlist_enriched_snapshots(
    watchlist_snapshots,
    resolver_report=resolver_report,
    probability_shadow_report=probability_shadow_report,
)


def _save_watchlist_overrides(path: Path, overrides: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(overrides, indent=2, ensure_ascii=False), encoding="utf-8")


def _save_json_dict(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _save_json_list(path: Path, payload: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _save_json_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _activate_market_snapshot_for_pipeline(snapshot: dict) -> Path:
    market_id = str(snapshot.get("market_id") or "")
    if not market_id:
        raise ValueError("Cannot activate a market snapshot without market_id.")

    payload = {
        **snapshot,
        "market_id": market_id,
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "activation_source": "weather_dashboard",
    }
    _save_json_payload(REALTIME_MARKET_JSON, payload)
    return REALTIME_MARKET_JSON


def _run_pipeline_command(name: str, cwd: Path, args: list[str]) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    started_at = datetime.now(timezone.utc)
    try:
        completed = subprocess.run(
            [sys.executable, *args],
            cwd=str(cwd),
            env=env,
            text=True,
            capture_output=True,
            timeout=45,
            check=False,
        )
    except Exception as exc:
        return {
            "name": name,
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "started_at": started_at.isoformat(),
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }

    return {
        "name": name,
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-3000:],
        "stderr": completed.stderr[-3000:],
        "started_at": started_at.isoformat(),
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }


def _run_selected_market_pipeline(snapshot: dict) -> dict:
    activated_path = _activate_market_snapshot_for_pipeline(snapshot)
    steps = [
        {
            "name": "resolver_once",
            "cwd": WORKSPACE_DIR / "weather-rules-research",
            "args": ["scripts/run_resolver_once.py"],
        },
        {
            "name": "forecast_once",
            "cwd": WORKSPACE_DIR / "weather-rules-research",
            "args": ["scripts/run_weather_once.py"],
        },
        {
            "name": "probability_shadow",
            "cwd": WORKSPACE_DIR / "weather-comparison-engine",
            "args": ["scripts/run_probability_shadow.py"],
        },
        {
            "name": "comparison_once",
            "cwd": WORKSPACE_DIR / "weather-comparison-engine",
            "args": ["scripts/run_comparison_once.py"],
        },
    ]

    results = [
        _run_pipeline_command(step["name"], step["cwd"], step["args"])
        for step in steps
    ]
    return {
        "market_id": str(snapshot.get("market_id") or ""),
        "activated_market_path": str(activated_path),
        "ran_at": datetime.now(timezone.utc).isoformat(),
        "ok": all(result["ok"] for result in results),
        "steps": results,
    }


def _render_pipeline_sync_panel(
    selected_snapshot: dict | None,
    key_prefix: str,
) -> None:
    st.markdown("<div class='compact-panel-title'>Pipeline Sync</div>", unsafe_allow_html=True)

    if selected_snapshot is None:
        st.info("Select or focus a market before running pipeline sync.")
        return

    market_id = str(selected_snapshot.get("market_id") or "")
    sync_context = build_pipeline_sync_context(
        selected_market_id=market_id,
        operator_context=st.session_state.get("operator_market_context"),
        last_sync_result=st.session_state.get("last_pipeline_sync_result"),
    )
    st.caption(
        "Activate writes the selected market into the live input file, then runs resolver, "
        "probability shadow, and one comparison pass."
    )
    render_pipeline_sync_context(sync_context)
    c1, c2 = st.columns([0.46, 0.54], vertical_alignment="center")
    with c1:
        run_sync = st.button(
            "Activate & Run Pipeline",
            key=f"{key_prefix}_pipeline_sync_{market_id}",
            use_container_width=True,
            help="Use the selected market as current realtime input and refresh resolver/probability/comparison outputs.",
        )
    with c2:
        st.markdown(f"Current selected market: `{market_id or '-'}`")

    if run_sync:
        with st.spinner("Running selected-market pipeline..."):
            result = _run_selected_market_pipeline(selected_snapshot)
        st.session_state["last_pipeline_sync_result"] = result
        if result["ok"]:
            _cached_gamma_search.clear()
            st.toast(f"Pipeline synced for {market_id}", icon="✅")
        else:
            st.warning("Pipeline sync finished with one or more failed steps.")
        st.rerun()

    result = st.session_state.get("last_pipeline_sync_result")
    if not result:
        return

    status = "OK" if result.get("ok") else "Needs attention"
    st.markdown(f"**Last sync:** `{status}` · market `{result.get('market_id', '-')}` · `{result.get('ran_at', '-')}`")
    for step in result.get("steps", []):
        step_ok, status_note = _normalize_pipeline_step_status(step)
        label = "passed" if step_ok else "failed"
        step_name = _format_pipeline_step_name(str(step.get("name") or "-"))
        with st.expander(f"{step_name} · {label}", expanded=not step_ok):
            st.caption(f"returncode={step.get('returncode')} finished_at={step.get('finished_at')}")
            if status_note:
                st.warning(status_note)
            failure_summary = _summarize_pipeline_step_failure(step)
            if failure_summary:
                st.warning(failure_summary)
            if step.get("stdout"):
                st.code(step.get("stdout"), language="json")
            if step.get("stderr"):
                st.code(step.get("stderr"), language="text")


def _format_pipeline_step_name(name: str) -> str:
    return {
        "resolver_once": "Resolver refresh",
        "forecast_once": "Forecast refresh",
        "probability_shadow": "Probability refresh",
        "comparison_once": "Comparison refresh",
    }.get(name, name.replace("_", " "))


def _normalize_pipeline_step_status(step: dict) -> tuple[bool, str | None]:
    raw_ok = step.get("ok")
    returncode = step.get("returncode")
    normalized_ok = bool(raw_ok)
    try:
        normalized_returncode = int(returncode) if returncode is not None else None
    except (TypeError, ValueError):
        normalized_returncode = None

    if normalized_returncode is not None:
        normalized_ok = normalized_returncode == 0

    if raw_ok is not None and bool(raw_ok) != normalized_ok:
        return normalized_ok, "Step status was inconsistent; UI normalized it using returncode."
    return normalized_ok, None


def _summarize_pipeline_step_failure(step: dict) -> str | None:
    step_ok, _ = _normalize_pipeline_step_status(step)
    if step_ok:
        return None
    text = "\n".join(
        part for part in [str(step.get("stderr") or ""), str(step.get("stdout") or "")] if part
    )
    if not text.strip():
        return "This step failed, but no error details were captured."
    if "SSL:" in text or "CERTIFICATE_VERIFY_FAILED" in text or "EOF occurred in violation of protocol" in text:
        return "Remote weather fetch failed because the local Python SSL handshake failed."
    if "ReadTimeout" in text or "timed out" in text or "TimeoutError" in text:
        return "Remote weather fetch timed out."
    if "No such file or directory" in text:
        return "A required runtime file or artifact is missing."
    if "ModuleNotFoundError" in text:
        return "A required Python module is missing in this environment."
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    return first_line[:220] if first_line else "This step failed."


persisted_watchlist_overrides = _load_watchlist_overrides(WATCHLIST_OVERRIDES_JSON)
if persisted_watchlist_overrides:
    st.session_state.setdefault("market_watchlist_overrides", persisted_watchlist_overrides)

persisted_recent_markets = _load_json_list(RECENT_MARKETS_JSON)
if persisted_recent_markets:
    st.session_state.setdefault("recent_markets", persisted_recent_markets)

persisted_removed_markets = _load_json_list(WATCHLIST_REMOVED_JSON)
if persisted_removed_markets:
    st.session_state.setdefault("market_watchlist_removed", persisted_removed_markets)

persisted_pinned_override = _load_json_dict(PINNED_MARKET_OVERRIDE_JSON)
if persisted_pinned_override:
    st.session_state.setdefault(
        "pinned_market_override",
        str(persisted_pinned_override.get("market_id") or ""),
    )
    st.session_state.setdefault(
        "pinned_market_override_label",
        str(persisted_pinned_override.get("label") or persisted_pinned_override.get("market_id") or ""),
    )
    st.session_state.setdefault(
        "pinned_market_override_source",
        str(persisted_pinned_override.get("source") or "pinned"),
    )
    st.session_state.setdefault(
        "pinned_market_override_snapshot",
        persisted_pinned_override.get("snapshot") or None,
    )


def _select_snapshot(
    snapshots: list[dict],
    market_id: str | None,
    fallback: dict | None,
) -> dict | None:
    if market_id:
        for snapshot in snapshots:
            if str(snapshot.get("market_id")) == market_id:
                return snapshot
    return fallback or (snapshots[0] if snapshots else None)


def _find_snapshot_by_market_id(snapshots: list[dict], market_id: str | None) -> dict | None:
    if not market_id:
        return None
    for snapshot in snapshots:
        if str(snapshot.get("market_id") or "") == str(market_id):
            return snapshot
    return None


def _snapshot_search_text(snapshot: dict) -> str:
    parts = [
        str(snapshot.get("market_id") or ""),
        str(snapshot.get("market_question") or ""),
        str(snapshot.get("market_family") or ""),
        str(snapshot.get("location_name") or ""),
        str(snapshot.get("market_band") or ""),
        str(snapshot.get("market_band_label") or ""),
    ]
    return " ".join(part.lower() for part in parts if part)


def _score_snapshot(query: str, snapshot: dict) -> float:
    haystack = _snapshot_search_text(snapshot)
    needle = query.lower().strip()
    if not needle:
        return 0.0
    if needle in haystack:
        return 1.0
    tokens = [token for token in needle.split() if token]
    token_hits = sum(1 for token in tokens if token in haystack)
    token_score = token_hits / max(len(tokens), 1)
    ratio = SequenceMatcher(None, needle, haystack).ratio()
    return max(ratio, token_score)


def _search_snapshots(
    snapshots: list[dict],
    query: str,
    limit: int = 20,
) -> list[dict]:
    needle = query.strip()
    if not needle:
        return []

    ranked = []
    for snapshot in snapshots:
        score = _score_snapshot(needle, snapshot)
        if score > 0.0:
            ranked.append((score, snapshot))

    ranked.sort(
        key=lambda item: (
            item[0],
            str(item[1].get("updated_at") or ""),
            str(item[1].get("market_id") or ""),
        ),
        reverse=True,
    )
    return [snapshot for _, snapshot in ranked[:limit]]


def _snapshot_label(snapshot: dict) -> str:
    return (
        f"{snapshot.get('market_id', '-')} | "
        f"{snapshot.get('market_family', '-')} | "
        f"{snapshot.get('market_question') or snapshot.get('location_name') or '-'}"
    )


def _remember_recent_market(
    market_id: str | None,
    label: str | None,
    source: str,
    market_family: str | None = None,
    max_items: int = 8,
) -> None:
    if not market_id:
        return
    current = (market_id, source)
    if st.session_state.get("last_recent_selection") == current:
        return

    recent = st.session_state.setdefault("recent_markets", [])
    now = datetime.now(timezone.utc)
    recent[:] = [item for item in recent if item.get("market_id") != market_id]
    recent.insert(
        0,
        {
            "market_id": market_id,
            "label": label or market_id,
            "source": source,
            "market_family": market_family,
            "chosen_at": now.isoformat(),
            "chosen_at_ts": int(now.timestamp()),
        },
    )
    del recent[max_items:]
    st.session_state["last_recent_selection"] = current
    _save_json_list(RECENT_MARKETS_JSON, recent)


def _set_pinned_market(snapshot: dict, source: str, label: str | None = None) -> None:
    market_id = str(snapshot.get("market_id") or "")
    if not market_id:
        return
    snapshot_label = label or _snapshot_label(snapshot)
    st.session_state["pinned_market_override"] = market_id
    st.session_state["pinned_market_override_label"] = snapshot_label
    st.session_state["pinned_market_override_source"] = source
    st.session_state["pinned_market_override_snapshot"] = snapshot
    _save_json_dict(
        PINNED_MARKET_OVERRIDE_JSON,
        {
            "market_id": market_id,
            "label": snapshot_label,
            "source": source,
            "snapshot": snapshot,
        },
    )


def _clear_pinned_market() -> None:
    for key in (
        "pinned_market_override",
        "pinned_market_override_label",
        "pinned_market_override_source",
        "pinned_market_override_snapshot",
    ):
        st.session_state.pop(key, None)
    if PINNED_MARKET_OVERRIDE_JSON.exists():
        PINNED_MARKET_OVERRIDE_JSON.unlink()


def _promote_market_to_recent(snapshot: dict, source: str = "search") -> None:
    market_id = str(snapshot.get("market_id") or "")
    if not market_id:
        return
    label = _snapshot_label(snapshot)
    _remember_recent_market(
        market_id,
        label,
        source,
        market_family=str(snapshot.get("market_family") or "-"),
    )
    _set_pinned_market(snapshot, source=source, label=label)


def _add_market_to_watchlist(snapshot: dict) -> None:
    market_id = str(snapshot.get("market_id") or "")
    if not market_id:
        return

    removed = st.session_state.setdefault("market_watchlist_removed", [])
    removed[:] = [
        item for item in removed if str(item.get("market_id") or "") != market_id
    ]
    _save_json_list(WATCHLIST_REMOVED_JSON, removed)

    overrides = st.session_state.setdefault("market_watchlist_overrides", [])
    normalized = {**snapshot}
    normalized["market_id"] = market_id
    normalized["search_source"] = snapshot.get("search_source") or "gamma"
    normalized["updated_at"] = snapshot.get("updated_at") or datetime.now(timezone.utc).isoformat()

    overrides[:] = [
        item for item in overrides if str(item.get("market_id") or "") != market_id
    ]
    overrides.insert(0, normalized)
    _save_watchlist_overrides(WATCHLIST_OVERRIDES_JSON, overrides)


def _remove_market_from_watchlist(market_id: str | None) -> None:
    if not market_id:
        return

    overrides = st.session_state.setdefault("market_watchlist_overrides", [])
    overrides[:] = [
        item for item in overrides if str(item.get("market_id") or "") != str(market_id)
    ]
    _save_watchlist_overrides(WATCHLIST_OVERRIDES_JSON, overrides)

    recent = st.session_state.setdefault("recent_markets", [])
    recent[:] = [
        item for item in recent if str(item.get("market_id") or "") != str(market_id)
    ]
    _save_json_list(RECENT_MARKETS_JSON, recent)

    if str(st.session_state.get("pinned_market_override") or "") == str(market_id):
        _clear_pinned_market()

    removed = st.session_state.setdefault("market_watchlist_removed", [])
    if all(str(item.get("market_id") or "") != str(market_id) for item in removed):
        removed.insert(
            0,
            {
                "market_id": str(market_id),
                "removed_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    _save_json_list(WATCHLIST_REMOVED_JSON, removed)


def _merge_watchlist_snapshots(*groups: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()
    removed_ids = {
        str(item.get("market_id") or "")
        for item in st.session_state.get("market_watchlist_removed", [])
        if item.get("market_id") is not None
    }

    for group in groups:
        for snapshot in group:
            market_id = str(snapshot.get("market_id") or "")
            if not market_id or market_id in seen or market_id in removed_ids:
                continue
            seen.add(market_id)
            merged.append(snapshot)

    merged.sort(
        key=lambda snapshot: (
            str(snapshot.get("updated_at") or ""),
            str(snapshot.get("market_id") or ""),
        ),
        reverse=True,
    )
    return merged


def _merge_search_results(*groups: list[dict]) -> list[dict]:
    merged: list[dict] = []
    seen: set[str] = set()

    for group in groups:
        for snapshot in group:
            market_id = str(snapshot.get("market_id") or "")
            if not market_id or market_id in seen:
                continue
            seen.add(market_id)
            merged.append(snapshot)

    return merged


@st.cache_data(ttl=45, show_spinner=False)
def _cached_gamma_search(query: str, base_url: str, limit: int) -> list[dict]:
    loader = GammaSearchLoader(base_url)
    return loader.search(query, limit=limit)


@st.cache_data(ttl=600, show_spinner=False)
def _cached_wunderground_shanghai(target_date: str | None) -> dict:
    return WundergroundShanghaiLoader().load_summary(target_date=target_date)


def _load_wunderground_cache() -> dict | None:
    try:
        payload = realtime_forecast_loader.load(WUNDERGROUND_SHANGHAI_CACHE_JSON)
    except Exception:
        return None
    return payload if isinstance(payload, dict) else None


def _refresh_wunderground_cache(target_date: str | None) -> dict:
    payload = _cached_wunderground_shanghai(target_date)
    payload["fetched_at"] = datetime.now(timezone.utc).isoformat()
    payload["source_mode"] = "manual_refresh"
    _save_json_payload(WUNDERGROUND_SHANGHAI_CACHE_JSON, payload)
    return payload


def _is_shanghai_market_snapshot(snapshot: dict | None) -> bool:
    if not snapshot:
        return False
    return (
        str(snapshot.get("market_id") or "") == "sample_market_shanghai_001"
        or str(snapshot.get("location_name") or "").lower() == "shanghai"
        or "shanghai" in str(snapshot.get("market_question") or "").lower()
    )


def _highlight_text(text: str, query: str) -> str:
    if not query.strip():
        return html.escape(text)

    escaped = html.escape(text)
    tokens = [token for token in re.split(r"\s+", query.strip()) if token]
    if not tokens:
        return escaped

    def repl(match: re.Match[str]) -> str:
        return f"<mark>{match.group(0)}</mark>"

    highlighted = escaped
    for token in sorted(set(tokens), key=len, reverse=True):
        pattern = re.compile(re.escape(html.escape(token)), re.IGNORECASE)
        highlighted = pattern.sub(repl, highlighted)
    return highlighted


def _format_gamma_search_error(message: str) -> str:
    ssl_tokens = [
        "CERTIFICATE_VERIFY_FAILED",
        "UNEXPECTED_EOF_WHILE_READING",
        "EOF occurred in violation of protocol",
        "SSL:",
    ]
    if not any(token in message for token in ssl_tokens):
        return message
    return (
        "Gamma remote search is temporarily unavailable because the local Python SSL handshake failed. "
        "Local watchlist search is still available."
    )


def _format_wunderground_error(message: str) -> str:
    if "CERTIFICATE_VERIFY_FAILED" not in message:
        return message
    return (
        "Wunderground SSL certificate verification failed on this local Python environment. "
        "To enable temporary dev fallback, restart with WUNDERGROUND_ALLOW_INSECURE_SSL=1, "
        "or repair the local certificate store."
    )


def _render_search_preview(snapshots: list[dict], query: str, key_prefix: str = "search") -> None:
    if not query.strip():
        return

    st.caption(f"Live matches for: `{query}`")
    if not snapshots:
        st.info("No live market matched your search yet.")
        return

    for idx, snapshot in enumerate(snapshots[:8]):
        market_id = str(snapshot.get("market_id") or "-")
        family = str(snapshot.get("market_family") or "-")
        question = str(snapshot.get("market_question") or snapshot.get("location_name") or "-")
        updated_at = str(snapshot.get("updated_at") or "-")
        pinned = bool(snapshot.get("pinned"))
        badge = "PINNED" if pinned else str(snapshot.get("search_source") or "LIVE").upper()

        left, right = st.columns([4, 1], vertical_alignment="top")
        with left:
            st.markdown(
                (
                    f"<div style='padding:0.55rem 0.7rem;border-radius:0.7rem;"
                    f"border:1px solid rgba(35,72,82,0.14);margin-bottom:0.2rem;"
                    f"background:linear-gradient(180deg, rgba(255,255,255,0.94), rgba(248,246,239,0.82));'>"
                    f"<div style='display:flex;justify-content:space-between;gap:0.75rem;'>"
                    f"<div><strong style='color:#145248'>{badge}</strong> "
                    f"<span style='color:#667782'>{html.escape(family)} · {html.escape(market_id)}</span></div>"
                    f"<div style='color:#667782;font-size:0.72rem;'>{html.escape(updated_at)}</div>"
                    f"</div>"
                    f"<div style='margin-top:0.35rem;line-height:1.35;color:#17252b;font-weight:750;'>"
                    f"{_highlight_text(question, query)}"
                    f"</div>"
                    f"</div>"
                ),
                unsafe_allow_html=True,
            )
        with right:
            if st.button(
                "Add to list",
                key=f"{key_prefix}_add_{idx}_{market_id}",
                use_container_width=True,
            ):
                _add_market_to_watchlist(snapshot)
                _promote_market_to_recent(
                    snapshot,
                    source=str(snapshot.get("search_source") or "search"),
                )
                st.toast(f"Added {market_id} to the desk", icon="✅")
                st.rerun()


def _load_live_watchlist_snapshots() -> tuple[dict | None, list[dict]]:
    live_realtime_market = None
    live_market_snapshots: list[dict] = []

    try:
        live_realtime_market = realtime_market_loader.load(REALTIME_MARKET_JSON)
    except Exception:
        live_realtime_market = None

    try:
        live_market_snapshots = realtime_market_loader.load_many(REALTIME_MARKET_SNAPSHOTS_GLOB)
    except Exception:
        live_market_snapshots = []

    watchlist = list(live_market_snapshots)
    if live_realtime_market and all(
        str(snapshot.get("market_id")) != str(live_realtime_market.get("market_id"))
        for snapshot in watchlist
    ):
        watchlist.insert(0, live_realtime_market)

    return live_realtime_market, _merge_watchlist_snapshots(
        watchlist,
        st.session_state.get("market_watchlist_overrides", []),
    )


def _load_live_forecast_snapshot() -> dict | None:
    try:
        return realtime_forecast_loader.load(REALTIME_FORECAST_JSON)
    except Exception:
        return None


def _load_live_forecast_snapshots() -> list[dict]:
    snapshots: list[dict] = []

    try:
        snapshots = realtime_forecast_loader.load_many(REALTIME_FORECAST_SNAPSHOTS_GLOB)
    except Exception:
        snapshots = []

    try:
        fallback = realtime_forecast_loader.load(REALTIME_FORECAST_JSON)
    except Exception:
        fallback = None

    if fallback and all(
        str(snapshot.get("market_id") or "") != str(fallback.get("market_id") or "")
        for snapshot in snapshots
    ):
        snapshots.insert(0, fallback)

    return snapshots


def _load_live_dashboard_rows():
    try:
        return rows_loader.load_df(DASHBOARD_ROWS_JSON)
    except Exception:
        return None


def _load_probability_state(market_id: str | None) -> dict | None:
    if not market_id:
        return None
    try:
        return realtime_forecast_loader.load(
            PROBABILITY_STATES_DIR / f"probability_state_{market_id}.json"
        )
    except Exception:
        return None


def _write_operator_market_context(
    *,
    market_id: str | None,
    label: str | None,
    source: str | None,
    market_family: str | None,
    market_snapshot: dict | None,
    comparison_row: dict | None,
    probability_state: dict | None,
    resolver_rule: dict | None,
) -> None:
    payload = {
        "schema_version": "operator_market_context.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "weather-dashboard",
        "selection_source": source or "unknown",
        "market_id": str(market_id or "") or None,
        "label": label,
        "market_family": market_family,
        "market_question": (market_snapshot or {}).get("market_question"),
        "comparison_status": (comparison_row or {}).get("comparison_status"),
        "action_hint": (comparison_row or {}).get("action_hint"),
        "probability_mode": (probability_state or {}).get("probability_mode"),
        "execution_constraint": (probability_state or {}).get("execution_constraint"),
        "resolver_status": (resolver_rule or {}).get("resolver_status")
        or (resolver_rule or {}).get("rule_status"),
    }
    try:
        OPERATOR_MARKET_CONTEXT_JSON.parent.mkdir(parents=True, exist_ok=True)
        OPERATOR_MARKET_CONTEXT_JSON.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        return
    st.session_state["operator_market_context"] = payload


def _forecast_matches_market(
    forecast_snapshot: dict | None,
    market_snapshot: dict | None,
) -> bool:
    if not forecast_snapshot or not market_snapshot:
        return False
    forecast_market_id = str(forecast_snapshot.get("market_id") or "")
    market_id = str(market_snapshot.get("market_id") or "")
    return bool(forecast_market_id and market_id and forecast_market_id == market_id)


def _select_forecast_snapshot(
    forecast_snapshots: list[dict],
    market_snapshot: dict | None,
    fallback_snapshot: dict | None = None,
) -> dict | None:
    if market_snapshot is None:
        return fallback_snapshot

    market_id = str(market_snapshot.get("market_id") or "")
    if not market_id:
        return fallback_snapshot

    for snapshot in forecast_snapshots:
        if str(snapshot.get("market_id") or "") == market_id:
            return snapshot

    if _forecast_matches_market(fallback_snapshot, market_snapshot):
        return fallback_snapshot

    return None


watchlist_snapshots = _merge_watchlist_snapshots(
    watchlist_snapshots,
    st.session_state.get("market_watchlist_overrides", []),
)

if df is not None:
    sort_cols = available_sort_columns(df)
    pinned_market_id = st.session_state.get("pinned_market_override") or PINNED_MARKET_ID
    auto_market_id = (realtime_market or {}).get("market_id")
    market_snapshot_map = {
        str(snapshot.get("market_id")): snapshot
        for snapshot in watchlist_snapshots
        if snapshot.get("market_id") is not None
    }
    market_label_by_id = {
        market_id: _snapshot_label(snapshot) for market_id, snapshot in market_snapshot_map.items()
    }
    recent_markets = [
        item
        for item in st.session_state.get("recent_markets", [])
        if item.get("market_id") in market_snapshot_map
    ]
    recent_market_ids = [item.get("market_id") for item in recent_markets]
    recent_choices = [
        f"Recent: {market_label_by_id[market_id]}" for market_id in recent_market_ids if market_id in market_label_by_id
    ]
    other_market_ids = [market_id for market_id in sorted(market_snapshot_map.keys()) if market_id not in recent_market_ids]
    other_choices = [market_label_by_id[market_id] for market_id in other_market_ids]
    pinned_market_choices = ["Auto"] + recent_choices + other_choices
    default_choice = (
        f"Recent: {market_label_by_id[pinned_market_id]}"
        if pinned_market_id in recent_market_ids
        else (market_label_by_id[pinned_market_id] if pinned_market_id in market_snapshot_map else "Auto")
    )
    default_index = pinned_market_choices.index(default_choice) if default_choice in pinned_market_choices else 0
    selected_market_snapshot_candidate = None
    pin_current_market = False

    with st.sidebar:
        st.header("Control")

        refresh_data = st.button(
            "Refresh Data",
            use_container_width=True,
            help="Reload local realtime files and clear cached Gamma/Wunderground lookups without auto-refreshing the whole page.",
        )
        if refresh_data:
            _cached_gamma_search.clear()
            _cached_wunderground_shanghai.clear()
            st.toast("Data cache cleared. Reloading latest snapshots.", icon="🔄")
            st.rerun()

        selected_sort = None
        ascending = False
        market_search_query = ""
        gamma_search_results: list[dict] = []
        gamma_search_error = None
        search_choice_label = None

        with st.expander("Market Focus", expanded=True):
            selected_market_choice = st.selectbox(
                "Pinned Market",
                pinned_market_choices,
                index=default_index,
            )
            pin_current_market = st.button(
                "Pin Current Market",
                use_container_width=True,
            )
            clear_pinned_market = st.button(
                "Clear Pin",
                use_container_width=True,
                disabled=not bool(st.session_state.get("pinned_market_override") or PINNED_MARKET_ID),
            )

        with st.expander("Search Market", expanded=False):
            market_search_query = st.text_input(
                "Market Search",
                value="",
                placeholder="Type a market name, family, location, or id",
                help="Search live Polymarket markets first; fall back to tracked watchlist matches.",
            )

            if market_search_query.strip():
                try:
                    gamma_search_results = _cached_gamma_search(
                        market_search_query,
                        GAMMA_API_BASE_URL,
                        GAMMA_SEARCH_LIMIT,
                    )
                except Exception as exc:
                    gamma_search_error = str(exc)

            local_search_results = [
                {**snapshot, "search_source": "local"}
                for snapshot in _search_snapshots(watchlist_snapshots, market_search_query)
            ]
            search_results = _merge_search_results(gamma_search_results, local_search_results)
            search_labels = [_snapshot_label(snapshot) for snapshot in search_results]
            if market_search_query.strip():
                if gamma_search_error:
                    st.caption(f"Gamma search unavailable: {_format_gamma_search_error(gamma_search_error)}")
                elif gamma_search_results:
                    st.caption("Gamma API results are live and take priority.")
                elif local_search_results:
                    st.caption("Showing current watchlist matches.")
                search_choice_label = st.selectbox(
                    "Search Results",
                    search_labels if search_labels else ["No matches yet"],
                    disabled=not bool(search_labels),
                )
                st.markdown("**Preview / Add**")
                if search_labels:
                    _render_search_preview(search_results, market_search_query, key_prefix="sidebar_search")
                else:
                    st.caption("No search preview available.")
        if not market_search_query.strip():
            local_search_results = []
            search_results = []
            search_labels = []

        with st.expander("Sort Rows", expanded=False):
            if sort_cols:
                selected_sort = st.selectbox("Sort By", sort_cols)
            else:
                st.caption("No sortable columns available.")
            ascending = st.checkbox("Ascending", value=False)

        if selected_market_choice == "Auto":
            selected_market_id = None
        elif selected_market_choice.startswith("Recent: "):
            label = selected_market_choice.replace("Recent: ", "", 1)
            selected_market_id = next(
                (
                    market_id
                    for market_id, snapshot in market_snapshot_map.items()
                    if _snapshot_label(snapshot) == label
                ),
                None,
            )
        else:
            selected_market_id = next(
                (
                    market_id
                    for market_id, snapshot in market_snapshot_map.items()
                    if _snapshot_label(snapshot) == selected_market_choice
                ),
                None,
            )

        if (
            market_search_query.strip()
            and search_results
            and search_choice_label in search_labels
        ):
            selected_search_snapshot = search_results[search_labels.index(search_choice_label)]
            selected_market_id = selected_search_snapshot.get("market_id")
            selected_market_snapshot_candidate = selected_search_snapshot
            selected_market_source = "search"
        elif selected_market_choice == "Auto":
            selected_market_source = "pinned" if pinned_market_id else "auto"
        elif selected_market_choice.startswith("Recent: "):
            selected_market_source = "recent"
        else:
            selected_market_source = "pinned"

        if clear_pinned_market:
            _clear_pinned_market()
            st.rerun()

        with st.expander("Files", expanded=False):
            st.caption(f"Dashboard rows: {DASHBOARD_ROWS_JSON.name}")
            st.caption(f"History: {COMPARISON_HISTORY_JSON.name}")
            st.caption(f"Snapshots: {REALTIME_MARKET_SNAPSHOTS_GLOB}")

    if selected_sort:
        df = safe_sort_dashboard_rows(
            df,
            sort_by=selected_sort,
            ascending=ascending,
        )

    pinned_market_override = st.session_state.get("pinned_market_override")
    pinned_override_snapshot = st.session_state.get("pinned_market_override_snapshot")
    if pinned_market_override and not pinned_override_snapshot:
        pinned_override_snapshot = market_snapshot_map.get(str(pinned_market_override))
    if pinned_market_override and pinned_override_snapshot and selected_market_choice == "Auto":
        selected_market_id = str(pinned_market_override)
        selected_market_source = st.session_state.get("pinned_market_override_source", "recent")
        selected_market_snapshot = pinned_override_snapshot
    elif selected_market_snapshot_candidate is not None:
        selected_market_snapshot = selected_market_snapshot_candidate
    else:
        selected_market_snapshot = _select_snapshot(
            watchlist_snapshots,
            selected_market_id,
            realtime_market if selected_market_choice == "Auto" else None,
        )

    if not selected_market_id and selected_market_snapshot is not None:
        selected_market_id = str(selected_market_snapshot.get("market_id") or "")

    selected_market_label = (
        market_label_by_id.get(selected_market_id)
        or (_snapshot_label(selected_market_snapshot) if selected_market_snapshot else None)
        or selected_market_choice
        or selected_market_id
    )
    selected_market_family = (
        selected_market_snapshot.get("market_family") if selected_market_snapshot else None
    )
    selected_realtime_forecast = _select_forecast_snapshot(
        realtime_forecast_snapshots,
        selected_market_snapshot,
        realtime_forecast,
    )
    shanghai_live_weather = _load_wunderground_cache() if _is_shanghai_market_snapshot(selected_market_snapshot) else None
    if ENABLE_LIVE_WUNDERGROUND and _is_shanghai_market_snapshot(selected_market_snapshot):
        try:
            shanghai_target_date = selected_market_snapshot.get("target_date")
            if not shanghai_target_date and selected_realtime_forecast is not None:
                shanghai_target_date = selected_realtime_forecast.get("target_date")
            shanghai_live_weather = _refresh_wunderground_cache(
                str(shanghai_target_date) if shanghai_target_date else None
            )
        except Exception as exc:
            st.caption(f"Wunderground Shanghai live pull unavailable: {_format_wunderground_error(str(exc))}")
    _remember_recent_market(
        selected_market_id,
        selected_market_label,
        selected_market_source,
        market_family=selected_market_family,
    )
    if pin_current_market and selected_market_snapshot is not None:
        _set_pinned_market(
            selected_market_snapshot,
            source="pinned",
            label=_snapshot_label(selected_market_snapshot),
        )
        _remember_recent_market(
            str(selected_market_snapshot.get("market_id") or ""),
            _snapshot_label(selected_market_snapshot),
            "pinned",
            market_family=str(selected_market_snapshot.get("market_family") or "-"),
        )
        st.rerun()
    active_market_id = (
        selected_market_id
        or (selected_market_snapshot.get("market_id") if selected_market_snapshot else None)
        or auto_market_id
    )

    market_comparison_df = df
    if active_market_id and "market_id" in df.columns:
        market_comparison_df = df[df["market_id"] == active_market_id]

    comparison_row = market_comparison_df.iloc[0].to_dict() if not market_comparison_df.empty else None
    probability_state = _load_probability_state(str(active_market_id) if active_market_id else None)
    resolver_rule = find_resolver_rule(
        resolver_report,
        str(active_market_id) if active_market_id else None,
    )
    _write_operator_market_context(
        market_id=str(active_market_id) if active_market_id else None,
        label=str(selected_market_label) if selected_market_label else None,
        source=str(selected_market_source) if selected_market_source else None,
        market_family=str(selected_market_family) if selected_market_family else None,
        market_snapshot=selected_market_snapshot,
        comparison_row=comparison_row,
        probability_state=probability_state,
        resolver_rule=resolver_rule,
    )

    @st.fragment(run_every=10)
    def _render_live_desk() -> None:
        live_df = _load_live_dashboard_rows()
        live_realtime_market, live_watchlist_snapshots = _load_live_watchlist_snapshots()
        live_realtime_forecast = _load_live_forecast_snapshot()
        live_realtime_forecast_snapshots = _load_live_forecast_snapshots()

        live_market_snapshot_map = {
            str(snapshot.get("market_id")): snapshot
            for snapshot in live_watchlist_snapshots
            if snapshot.get("market_id") is not None
        }
        live_pinned_market_override = st.session_state.get("pinned_market_override")
        live_pinned_override_snapshot = st.session_state.get("pinned_market_override_snapshot")
        if live_pinned_market_override and not live_pinned_override_snapshot:
            live_pinned_override_snapshot = live_market_snapshot_map.get(str(live_pinned_market_override))

        live_selected_market_snapshot = selected_market_snapshot
        if live_pinned_market_override and live_pinned_override_snapshot and selected_market_choice == "Auto":
            live_selected_market_snapshot = live_pinned_override_snapshot
        elif selected_market_snapshot is not None:
            live_selected_market_snapshot = live_market_snapshot_map.get(
                str(selected_market_snapshot.get("market_id") or "")
            ) or selected_market_snapshot
        else:
            live_selected_market_snapshot = _select_snapshot(
                live_watchlist_snapshots,
                active_market_id,
                live_realtime_market if selected_market_choice == "Auto" else None,
            )

        live_active_market_id = (
            str(live_selected_market_snapshot.get("market_id") or "")
            if live_selected_market_snapshot is not None
            else active_market_id
        )
        live_forecast_for_selected = (
            _select_forecast_snapshot(
                live_realtime_forecast_snapshots,
                live_selected_market_snapshot,
                live_realtime_forecast,
            )
        )
        live_recent_markets = [
            item
            for item in st.session_state.get("recent_markets", [])
            if item.get("market_id") in live_market_snapshot_map
        ]

        live_market_comparison_df = live_df
        if (
            live_df is not None
            and live_active_market_id
            and "market_id" in live_df.columns
        ):
            live_market_comparison_df = live_df[live_df["market_id"] == live_active_market_id]

        live_comparison_row = (
            live_market_comparison_df.iloc[0].to_dict()
            if live_market_comparison_df is not None and not live_market_comparison_df.empty
            else None
        )

        render_command_center(
            live_market_comparison_df if live_market_comparison_df is not None else market_comparison_df,
            live_selected_market_snapshot,
            live_forecast_for_selected,
        )
        render_operator_closure_panel(
            live_market_comparison_df if live_market_comparison_df is not None else market_comparison_df,
            live_selected_market_snapshot,
            live_forecast_for_selected,
            bot_authorized=bool(st.session_state.get("weather_console_authorized", False)),
        )

    render_architecture_brief(
        market_snapshot=selected_market_snapshot,
        resolver_rule=resolver_rule,
        probability_state=probability_state,
        comparison_row=comparison_row,
        bot_authorized=bool(st.session_state.get("weather_console_authorized", False)),
    )
    render_layer_ribbon(
        market_snapshot=selected_market_snapshot,
        resolver_rule=resolver_rule,
        probability_state=probability_state,
        comparison_row=comparison_row,
        bot_authorized=bool(st.session_state.get("weather_console_authorized", False)),
    )

    compact_gate_summary = build_compact_gate_stack_summary(
        market_snapshot=selected_market_snapshot,
        activated_market_snapshot=realtime_market,
        forecast_snapshot=selected_realtime_forecast,
        resolver_rule=resolver_rule,
        probability_state=probability_state,
        comparison_row=comparison_row,
        validation_freshness_status=validation_freshness_status,
        label_coverage_report=label_coverage_report,
        unified_status_report=unified_status_report,
        gate_stack_api_report=gate_stack_api_report,
        bot_authorized=bool(st.session_state.get("weather_console_authorized", False)),
        whitelist_path=EXECUTION_WHITELIST_YAML,
    )
    operator_focus_summary = build_operator_focus_summary(
        market_snapshot=selected_market_snapshot,
        forecast_snapshot=selected_realtime_forecast,
        probability_state=probability_state,
        comparison_row=comparison_row,
        compact_gate_summary=compact_gate_summary,
        unified_status_report=unified_status_report,
        position_snapshot=position_snapshot,
        production_readiness_report=production_readiness_report,
    )
    account_summary = build_read_only_account_summary(
        position_snapshot,
        str(active_market_id) if active_market_id else None,
        production_readiness_report,
    )
    operator_context_summary = build_operator_context_badge_context(
        st.session_state.get("operator_market_context")
    )
    top_parameter_ribbon_summary = build_top_parameter_ribbon_summary(
        market_snapshot=selected_market_snapshot,
        forecast_snapshot=selected_realtime_forecast,
        resolver_rule=resolver_rule,
        probability_state=probability_state,
        comparison_row=comparison_row,
        compact_gate_summary=compact_gate_summary,
        shanghai_live_weather=shanghai_live_weather,
    )

    st.markdown('<div class="desk-tabs-anchor"></div>', unsafe_allow_html=True)
    render_top_parameter_ribbon(top_parameter_ribbon_summary)
    tab_command, tab_pipeline, tab_markets, tab_charts, tab_history, tab_validation, tab_evidence = st.tabs(
        [
            "Command",
            "Pipeline",
            "Markets",
            "Charts",
            "History",
            "Validation",
            "Evidence / Raw",
        ]
    )

    with tab_command:
        render_operator_focus_banner(
            operator_focus_summary,
            title="Execution Brief",
            subtitle="Default view shows only the fields that can change an operator decision.",
            fields=[
                ("Probability", "probability_mode"),
                ("Constraint", "execution_constraint"),
                ("Compare", "comparison_status"),
                ("Edge", "edge"),
                ("Auth Gate", "authorization_gate"),
                ("Exec Gate", "execution_gate"),
            ],
        )
        render_command_metric_cards(
            focus_summary=operator_focus_summary,
            account_summary=account_summary,
            operator_context_summary=operator_context_summary,
        )
        current_col1, current_col2 = st.columns([0.92, 1.08])
        with current_col1:
            render_trade_decision_panel(
                selected_market_snapshot,
                selected_realtime_forecast,
                probability_state,
                comparison_row,
            )
        with current_col2:
            render_compact_gate_stack_panel(compact_gate_summary)
            render_live_status_panel(
                selected_market_snapshot,
                selected_realtime_forecast,
                key_prefix="command_live_status",
            )

        show_command_diagnostics = st.checkbox(
            "Show command diagnostics: detailed gate, resolver, probability and weather evidence",
            value=False,
            key="command_show_diagnostics",
        )
        if show_command_diagnostics:
            diag_col1, diag_col2 = st.columns([1, 1])
            with diag_col1:
                st.markdown("#### Detailed Gate Controls")
                render_execution_gate_panel(
                    market_snapshot=selected_market_snapshot,
                    forecast_snapshot=selected_realtime_forecast,
                    resolver_rule=resolver_rule,
                    probability_state=probability_state,
                    comparison_row=comparison_row,
                    validation_freshness_status=validation_freshness_status,
                    label_coverage_report=label_coverage_report,
                    bot_authorized=bool(st.session_state.get("weather_console_authorized", False)),
                    pending_intents_dir=EXECUTION_PENDING_INTENTS_DIR,
                    latest_intent_path=EXECUTION_DASHBOARD_INTENT_JSON,
                    telegram_signal_path=TELEGRAM_APPROVAL_SIGNAL_JSON,
                    whitelist_path=EXECUTION_WHITELIST_YAML,
                    gateway_dir=EXECUTION_GATEWAY_DIR,
                    approval_db_path=EXECUTION_APPROVAL_DB_PATH,
                    production_readiness_path=EXECUTION_PRODUCTION_READINESS_JSON,
                    manual_advisory_audit_path=MANUAL_ADVISORY_AUDIT_JSONL,
                    key_prefix="command_tab",
                    operator_mode=operator_mode,
                )
                render_probability_shadow_panel(probability_state)
            with diag_col2:
                render_operator_context_badge(st.session_state.get("operator_market_context"))
                render_read_only_account_panel(
                    position_snapshot,
                    str(active_market_id) if active_market_id else None,
                    production_readiness_report,
                )
                render_manual_advisory_reconciliation_panel(human_fill_reconciliation_report)
                render_comparison_focus_panel(
                    market_comparison_df,
                    selected_market_snapshot,
                    selected_realtime_forecast,
                )
                render_resolver_status_panel(
                    resolver_report,
                    str(selected_market_snapshot.get("market_id") or "")
                    if selected_market_snapshot
                    else active_market_id,
                )
                render_history_forecast_panel(
                    selected_market_snapshot,
                    selected_realtime_forecast,
                    shanghai_history_reference,
                    shanghai_live_weather,
                )

        show_operator_tools = st.checkbox(
            "Show operator tools: BOT controls and XAI closure",
            value=False,
            key="command_show_operator_tools",
        )
        if show_operator_tools:
            st.markdown("#### BOT Controls / XAI Closure")
            _render_live_desk()

        if _is_shanghai_market_snapshot(selected_market_snapshot):
            refresh_col, cache_col = st.columns([0.54, 0.46])
            with refresh_col:
                if st.button(
                    "Refresh ZSPD Weather",
                    use_container_width=True,
                    help="Manual Wunderground refresh. It may take a few seconds and will not run during normal page load.",
                ):
                    shanghai_target_date = selected_market_snapshot.get("target_date") if selected_market_snapshot else None
                    forecast_for_market = selected_realtime_forecast
                    if not shanghai_target_date and forecast_for_market is not None:
                        shanghai_target_date = forecast_for_market.get("target_date")
                    try:
                        with st.spinner("Refreshing Wunderground ZSPD..."):
                            shanghai_live_weather = _refresh_wunderground_cache(
                                str(shanghai_target_date) if shanghai_target_date else None
                            )
                        st.toast("ZSPD weather snapshot refreshed.", icon="✅")
                        st.rerun()
                    except Exception as exc:
                        st.warning(
                            f"Wunderground Shanghai live pull unavailable: {_format_wunderground_error(str(exc))}"
                        )
            with cache_col:
                if shanghai_live_weather:
                    st.caption(
                        f"ZSPD cache: {shanghai_live_weather.get('fetched_at') or 'existing snapshot'}"
                    )
                else:
                    st.caption("ZSPD cache: empty")

    with tab_pipeline:
        render_operator_focus_banner(
            operator_focus_summary,
            title="Pipeline Contract Health",
            subtitle="Shows whether market, resolver, forecast, probability and gate contracts agree.",
            fields=[
                ("Resolver", "resolver_gate"),
                ("Freshness", "freshness_gate"),
                ("Gate Source", "gate_source"),
                ("Target Date", "target_date"),
                ("Family", "family"),
                ("Updated", "updated_at"),
            ],
        )
        render_pipeline_flow(
            market_snapshot=selected_market_snapshot,
            resolver_rule=resolver_rule,
            probability_state=probability_state,
            comparison_row=comparison_row,
        )
        _render_pipeline_sync_panel(selected_market_snapshot, key_prefix="pipeline_tab")
        render_data_alignment_panel(
            selected_market_snapshot=selected_market_snapshot,
            activated_market_snapshot=realtime_market,
            forecast_snapshot=selected_realtime_forecast,
            resolver_rule=resolver_rule,
            probability_state=probability_state,
            comparison_row=comparison_row,
            validation_freshness_status=validation_freshness_status,
            label_coverage_report=label_coverage_report,
            bot_authorized=bool(st.session_state.get("weather_console_authorized", False)),
        )
        render_pipeline_summary(
            market_snapshot=selected_market_snapshot,
            resolver_rule=resolver_rule,
            probability_state=probability_state,
            comparison_row=comparison_row,
        )
        show_pipeline_diagnostics = st.checkbox(
            "Show pipeline diagnostics: detailed execution gate, resolver and probability reports",
            value=False,
            key="pipeline_show_diagnostics",
        )
        if show_pipeline_diagnostics:
            render_execution_gate_panel(
                market_snapshot=selected_market_snapshot,
                forecast_snapshot=selected_realtime_forecast,
                resolver_rule=resolver_rule,
                probability_state=probability_state,
                comparison_row=comparison_row,
                validation_freshness_status=validation_freshness_status,
                label_coverage_report=label_coverage_report,
                bot_authorized=bool(st.session_state.get("weather_console_authorized", False)),
                pending_intents_dir=EXECUTION_PENDING_INTENTS_DIR,
                latest_intent_path=EXECUTION_DASHBOARD_INTENT_JSON,
                telegram_signal_path=TELEGRAM_APPROVAL_SIGNAL_JSON,
                whitelist_path=EXECUTION_WHITELIST_YAML,
                gateway_dir=EXECUTION_GATEWAY_DIR,
                approval_db_path=EXECUTION_APPROVAL_DB_PATH,
                production_readiness_path=EXECUTION_PRODUCTION_READINESS_JSON,
                manual_advisory_audit_path=MANUAL_ADVISORY_AUDIT_JSONL,
                key_prefix="pipeline_tab",
                operator_mode=operator_mode,
            )
            pipeline_col1, pipeline_col2 = st.columns([1, 1])
            with pipeline_col1:
                render_resolver_status_panel(
                    resolver_report,
                    str(selected_market_snapshot.get("market_id") or "")
                    if selected_market_snapshot
                    else active_market_id,
                )
                render_probability_shadow_panel(probability_state)
                render_probability_shadow_report_panel(probability_shadow_report)
            with pipeline_col2:
                render_live_status_panel(
                    selected_market_snapshot,
                    selected_realtime_forecast,
                    key_prefix="pipeline_live_status",
                )

    with tab_markets:
        render_operator_focus_banner(
            operator_focus_summary,
            title="Market Selection Desk",
            subtitle="Use this page to choose the market; execution-sensitive status stays pinned above the watchlist.",
            fields=[
                ("Family", "family"),
                ("Market Prob", "market_probability"),
                ("Compare", "comparison_status"),
                ("Resolver", "resolver_gate"),
                ("Freshness", "freshness_gate"),
                ("Constraint", "execution_constraint"),
            ],
        )
        st.markdown("<div class='compact-panel-title'>Market Search & Watchlist</div>", unsafe_allow_html=True)
        pinned_count = 1 if selected_market_snapshot else 0
        manual_count = len(st.session_state.get("market_watchlist_overrides", []))
        removed_count = len(st.session_state.get("market_watchlist_removed", []))
        market_metric_cols = st.columns(4)
        market_metric_cols[0].metric("Tracked Markets", len(watchlist_snapshots))
        market_metric_cols[1].metric("Manual Adds", manual_count)
        market_metric_cols[2].metric("Focused", pinned_count)
        market_metric_cols[3].metric("Hidden", removed_count)
        show_market_sync = st.checkbox(
            "Show selected market pipeline sync",
            value=False,
            key="markets_show_pipeline_sync",
        )
        if show_market_sync:
            _render_pipeline_sync_panel(selected_market_snapshot, key_prefix="markets_tab")

        market_tab_search = st.text_input(
            "Search Polymarket and local watchlist",
            value="",
            placeholder="Type market name, id, Shanghai temperature, hottest year...",
            key="markets_tab_search",
        )
        market_tab_search_results: list[dict] = []
        market_tab_gamma_error = None
        if market_tab_search.strip():
            try:
                market_tab_gamma_results = _cached_gamma_search(
                    market_tab_search,
                    GAMMA_API_BASE_URL,
                    GAMMA_SEARCH_LIMIT,
                )
            except Exception as exc:
                market_tab_gamma_results = []
                market_tab_gamma_error = str(exc)
            market_tab_local_results = [
                {**snapshot, "search_source": "local"}
                for snapshot in _search_snapshots(watchlist_snapshots, market_tab_search)
            ]
            market_tab_search_results = _merge_search_results(
                market_tab_gamma_results,
                market_tab_local_results,
            )
            if market_tab_gamma_error:
                st.caption(f"Gamma search unavailable: {_format_gamma_search_error(market_tab_gamma_error)}")
            _render_search_preview(
                market_tab_search_results,
                market_tab_search,
                key_prefix="markets_tab_search",
            )

        market_tab_col1, market_tab_col2 = st.columns([0.42, 0.58])
        with market_tab_col1:
            render_recent_markets_panel(recent_markets)
        with market_tab_col2:
            watchlist_action = render_market_snapshots_panel(
                watchlist_snapshots,
                selected_market_snapshot.get("market_id") if selected_market_snapshot else None,
                removable_market_ids={
                    str(item.get("market_id") or "")
                    for item in st.session_state.get("market_watchlist_overrides", [])
                    if item.get("market_id") is not None
                },
            )
            if watchlist_action:
                action = str(watchlist_action.get("action") or "")
                market_id = str(watchlist_action.get("market_id") or "")
                action_snapshot = _find_snapshot_by_market_id(watchlist_snapshots, market_id)

                if action in {"focus", "pin"} and action_snapshot is not None:
                    _set_pinned_market(
                        action_snapshot,
                        source="watchlist",
                        label=_snapshot_label(action_snapshot),
                    )
                    _remember_recent_market(
                        market_id,
                        _snapshot_label(action_snapshot),
                        "pinned" if action == "pin" else "watchlist",
                        market_family=str(action_snapshot.get("market_family") or "-"),
                    )
                    st.toast(f"{'Pinned' if action == 'pin' else 'Focused'} {market_id}", icon="📌")
                    st.rerun()

                if action == "unpin":
                    if str(st.session_state.get("pinned_market_override") or "") == market_id:
                        _clear_pinned_market()
                    st.toast(f"Unpinned {market_id}", icon="📍")
                    st.rerun()

                if action == "remove":
                    _remove_market_from_watchlist(market_id)
                    st.toast(f"Removed {market_id} from watchlist", icon="🗑️")
                    st.rerun()

    with tab_charts:
        render_operator_focus_banner(
            operator_focus_summary,
            title="Signal Charts",
            subtitle="Charts and selected-market deltas first; full comparison rows are available on demand.",
            fields=[
                ("Compare", "comparison_status"),
                ("Gap", "confidence_adjusted_gap"),
                ("Edge", "edge"),
                ("Market Prob", "market_probability"),
                ("Target Date", "target_date"),
                ("Updated", "updated_at"),
            ],
        )
        filtered_df = render_filters(df)

        if active_market_id and "market_id" in filtered_df.columns:
            filtered_df = filtered_df[filtered_df["market_id"] == active_market_id]

        if selected_market_id and selected_market_snapshot is None:
            st.warning(
                f"Manual market id `{selected_market_id}` was not found in the current watchlist."
            )

        render_overview(filtered_df)

        chart_col1, chart_col2 = st.columns([1, 1])
        with chart_col1:
            render_divergence_chart(filtered_df)
        with chart_col2:
            render_detail_panel(filtered_df, active_market_id)

        if selected_market_snapshot is not None:
            st.caption(
                f"Tracking market: `{selected_market_snapshot.get('market_id', '-')}` "
                f"({selected_market_snapshot.get('market_family', '-')})"
            )

        if ts_df is not None:
            render_timeseries_panel(ts_df, active_market_id)
        else:
            st.info(NO_TIMESERIES)

        show_chart_rows = st.checkbox(
            "Show comparison rows and raw signal payload",
            value=False,
            key="charts_show_rows",
        )
        if show_chart_rows:
            render_comparison_table(filtered_df)
            render_signal_panel(signal_payload)

    with tab_history:
        render_operator_focus_banner(
            operator_focus_summary,
            title="Evidence Timeline",
            subtitle="Historical evidence should explain the current gate state, not bury it under rows.",
            fields=[
                ("Compare", "comparison_status"),
                ("Gap", "confidence_adjusted_gap"),
                ("Probability", "probability_mode"),
                ("Constraint", "execution_constraint"),
                ("Gate Source", "gate_source"),
                ("Updated", "updated_at"),
            ],
        )
        if history_df is not None:
            render_market_evidence_chart(
                training_samples_df=training_samples_df,
                selected_market_id=active_market_id,
                audit_events=manual_advisory_audit_events,
            )
            render_divergence_trend_chart(history_df, active_market_id)
            hist_col1, hist_col2 = st.columns([1, 1])
            with hist_col1:
                render_timeline_panel(history_df, active_market_id)
            with hist_col2:
                render_history_relationship_panel(history_df, active_market_id)
        else:
            st.info(NO_COMPARISON_HISTORY)

    with tab_validation:
        render_operator_focus_banner(
            operator_focus_summary,
            title="Validation And Promotion",
            subtitle="Use this page to decide whether probability can be promoted, held, or demoted.",
            fields=[
                ("Probability", "probability_mode"),
                ("Constraint", "execution_constraint"),
                ("Freshness", "freshness_gate"),
                ("Production", "production_ready"),
                ("BOT Can Move", "can_bot_trade"),
                ("Mode", "operator_mode"),
            ],
        )
        render_model_validation_panel(
            model_validation_report=model_validation_report,
            calibration_report=calibration_report,
            backtest_report=backtest_report,
            validation_freshness_status=validation_freshness_status,
            label_coverage_report=label_coverage_report,
        )

    with tab_evidence:
        render_operator_focus_banner(
            operator_focus_summary,
            title="Evidence And Raw Payloads",
            subtitle="Raw contracts, resolver rules and source payloads live here so operating pages stay quiet.",
            fields=[
                ("Market", "market_id"),
                ("Family", "family"),
                ("Resolver", "resolver_gate"),
                ("Gate Source", "gate_source"),
                ("Position", "position_status"),
                ("Updated", "updated_at"),
            ],
        )
        show_system_diagnostics = st.checkbox(
            "Show system diagnostics: worker health and unified status",
            value=False,
            key="evidence_show_system_diagnostics",
        )
        if show_system_diagnostics:
            render_worker_health_strip(monitoring_status_report)
            render_unified_status_strip(unified_status_report)
        else:
            st.caption(
                "System diagnostics are hidden by default to keep the operating surface focused."
            )
        render_ops_alert_panel(
            alert_events=gate_stack_ops_alert_events,
            notification_events=telegram_ops_notifications,
            delivery_events=telegram_ops_delivery_events,
        )
        show_field_dictionary = st.checkbox(
            "Show field dictionary",
            value=False,
            key="evidence_show_field_dictionary",
        )
        if show_field_dictionary:
            render_field_dictionary_panel()

        evidence_col1, evidence_col2 = st.columns([1, 1])
        with evidence_col1:
            if bias_df is not None:
                render_bias_summary_panel(bias_df)
            else:
                st.info("No bias report found.")
        with evidence_col2:
            render_rule_station_panel(rulebook_payload, active_market_id)

        render_raw_json_panel(
            signal_payload=signal_payload,
            market_bundles=market_bundles,
            market_snapshots=watchlist_snapshots,
            rulebook_payload=rulebook_payload,
        )
        render_market_panel(market_bundles)

    render_deerflow_signature()
else:
    st.warning("Dashboard rows unavailable.")
