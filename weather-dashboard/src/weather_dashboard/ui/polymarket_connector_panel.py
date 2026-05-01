from __future__ import annotations

from typing import Any, cast

import streamlit as st

from weather_dashboard.lib.api import apiGet, apiPost
from weather_dashboard.types.weather import (
    PolymarketConnectorConfig,
    PolymarketConnectorHealth,
    PolymarketMarketCacheItem,
    PolymarketPreviewSnapshot,
)
from weather_dashboard.ui.status_badge import render_status_badge

MODE_OPTIONS = ("MOCK_ONLY", "POLYMARKET_ONLY", "HYBRID")
STATE_KEY = "pwb04d_polymarket_connector_state"
MODE_WIDGET_KEY = "pwb04d_polymarket_mode"
NETWORK_WIDGET_KEY = "pwb04d_polymarket_network"


def build_polymarket_connector_panel_state() -> dict[str, object]:
    return {
        "status": "ok",
        "mode": "MOCK_ONLY",
        "allow_polymarket_network": False,
        "health": None,
        "config": None,
        "cached_markets": [],
        "preview_snapshots": [],
        "message": None,
        "warnings": [
            "Polymarket network access disabled by config.",
        ],
        "read_only": True,
    }


def _get_panel_state() -> dict[str, object]:
    state = st.session_state.get(STATE_KEY)
    if not isinstance(state, dict):
        state = build_polymarket_connector_panel_state()
        st.session_state[STATE_KEY] = state
    return state


def _set_message(state: dict[str, object], message: str | None) -> None:
    state["message"] = message


def _sync_widget_state(state: dict[str, object]) -> None:
    st.session_state[MODE_WIDGET_KEY] = state["mode"]
    st.session_state[NETWORK_WIDGET_KEY] = "Enabled" if state["allow_polymarket_network"] else "Disabled"


def _apply_source_mode_payload(state: dict[str, object], payload: dict[str, Any]) -> None:
    state["mode"] = str(payload.get("market_source_mode") or state["mode"])
    state["allow_polymarket_network"] = bool(
        payload.get("allow_polymarket_network", state["allow_polymarket_network"])
    )
    config = payload.get("config")
    if isinstance(config, dict):
        state["config"] = config
    _sync_widget_state(state)


def load_source_mode(state: dict[str, object]) -> None:
    try:
        payload = cast(dict[str, Any], apiGet("/api/polymarket/source-mode"))
        if payload.get("status") != "ok":
            _set_message(state, str(payload.get("message") or "Failed to load source mode."))
            return
        _apply_source_mode_payload(state, payload)
        _set_message(state, "Source mode loaded.")
    except Exception as exc:  # pragma: no cover - surfaced in UI
        _set_message(state, f"Failed to load source mode: {exc}")


def save_source_mode(state: dict[str, object]) -> None:
    try:
        payload = cast(
            dict[str, Any],
            apiPost(
                "/api/polymarket/source-mode",
                {
                    "market_source_mode": str(st.session_state.get(MODE_WIDGET_KEY, state["mode"])),
                    "allow_polymarket_network": str(
                        st.session_state.get(NETWORK_WIDGET_KEY, "Disabled")
                    ).lower()
                    == "enabled",
                },
            ),
        )
        if payload.get("status") != "ok":
            _set_message(state, str(payload.get("message") or "Failed to update source mode."))
            return
        _apply_source_mode_payload(state, payload)
        _set_message(state, str(payload.get("message") or "Source mode updated."))
    except Exception as exc:  # pragma: no cover - surfaced in UI
        _set_message(state, f"Failed to update source mode: {exc}")


def check_health(state: dict[str, object]) -> None:
    try:
        payload = cast(dict[str, Any], apiGet("/api/polymarket/health"))
        if payload.get("status") != "ok":
            _set_message(state, "Health check failed.")
            return
        state["health"] = payload.get("health")
        state["config"] = payload.get("config")
        health = payload.get("health")
        state["warnings"] = list((health or {}).get("warnings") or [])
        config = payload.get("config") or {}
        state["mode"] = str(config.get("market_source_mode") or state["mode"])
        state["allow_polymarket_network"] = bool(
            config.get("allow_polymarket_network", state["allow_polymarket_network"])
        )
        _sync_widget_state(state)
        _set_message(state, "Connector health checked.")
    except Exception as exc:  # pragma: no cover - surfaced in UI
        _set_message(state, f"Health check failed: {exc}")


def load_cached_markets(state: dict[str, object]) -> None:
    try:
        payload = cast(dict[str, Any], apiGet("/api/polymarket/markets?limit=50"))
        if payload.get("status") != "ok":
            _set_message(state, "Failed to load cached markets.")
            return
        items = list(payload.get("items") or [])
        state["cached_markets"] = items
        _set_message(state, f"Loaded {len(items)} cached market records.")
    except Exception as exc:  # pragma: no cover - surfaced in UI
        _set_message(state, f"Failed to load cached markets: {exc}")


def load_weather_markets(state: dict[str, object]) -> None:
    try:
        payload = cast(dict[str, Any], apiGet("/api/polymarket/weather-markets?limit=50"))
        if payload.get("status") != "ok":
            _set_message(state, "Failed to load weather markets.")
            return
        cached = list(payload.get("cached_items") or [])
        preview = list(payload.get("preview_snapshots") or [])
        warnings = list(payload.get("warnings") or [])
        state["cached_markets"] = cached
        state["preview_snapshots"] = preview
        state["warnings"] = warnings
        _set_message(
            state,
            f"Loaded {len(cached)} cached weather records and {len(preview)} preview snapshots.",
        )
    except Exception as exc:  # pragma: no cover - surfaced in UI
        _set_message(state, f"Failed to load weather markets: {exc}")


def sync_weather_markets(state: dict[str, object]) -> None:
    try:
        payload = cast(
            dict[str, Any],
            apiPost("/api/polymarket/sync-weather-markets", {"limit": 50}),
        )
        if payload.get("status") != "ok":
            _set_message(state, "Sync failed.")
            return
        state["cached_markets"] = list(payload.get("records") or [])
        state["warnings"] = list(payload.get("warnings") or [])
        _set_message(
            state,
            f"Read-only sync completed. Saved {int(payload.get('saved_count') or 0)} records.",
        )
    except Exception as exc:  # pragma: no cover - surfaced in UI
        _set_message(state, f"Sync failed: {exc}")


def _render_warning_box(warnings: list[str]) -> None:
    st.markdown("#### Connector Warnings")
    if not warnings:
        st.caption("No warnings loaded.")
        return
    for warning in warnings:
        st.warning(warning, icon="!")
    st.caption(
        "This panel is read-only. It does not expose wallet, private key, order placement, order cancellation, or live trading controls."
    )


def _render_health_card(
    health: PolymarketConnectorHealth | None,
    config: PolymarketConnectorConfig | None,
) -> None:
    st.markdown("#### Connector Health")
    if not health:
        st.caption("No health check loaded.")
    else:
        cols = st.columns(2)
        with cols[0]:
            st.caption("Gamma")
            render_status_badge("REACHABLE" if health["gamma_reachable"] else "NOT REACHABLE")
        with cols[1]:
            st.caption("CLOB")
            render_status_badge("REACHABLE" if health["clob_reachable"] else "NOT REACHABLE")
        st.write(f"Mode: `{health['mode']}`")
        st.write(f"Checked: `{health['last_checked_at']}`")
    if config:
        st.markdown("#### Config")
        st.write(f"Network: `{'enabled' if config['allow_polymarket_network'] else 'disabled'}`")
        st.write(f"Timeout: `{config['request_timeout_seconds']}s`")
        st.write(f"Max markets: `{config['max_markets']}`")


def _cached_markets_rows(items: list[PolymarketMarketCacheItem]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for item in items:
        rows.append(
            {
                "question": item["question"],
                "market_id": item["polymarket_market_id"],
                "prices": ", ".join(
                    f"{outcome}: {item['outcome_prices'][idx] if idx < len(item['outcome_prices']) else '—'}"
                    for idx, outcome in enumerate(item["outcomes"])
                ),
                "status": ",".join(
                    flag
                    for flag, enabled in (
                        ("ACTIVE", item["active"]),
                        ("CLOSED", bool(item.get("closed"))),
                        ("ARCHIVED", bool(item.get("archived"))),
                    )
                    if enabled
                )
                or "INACTIVE",
                "liquidity": item.get("liquidity"),
            }
        )
    return rows


def _preview_snapshot_rows(items: list[PolymarketPreviewSnapshot]) -> list[dict[str, object]]:
    return [
        {
            "question": item["question"],
            "market_id": item["market_id"],
            "yes": f"{item['yes_price'] * 100:.1f}%",
            "no": f"{item['no_price'] * 100:.1f}%",
            "source": item["source"],
        }
        for item in items
    ]


def render_polymarket_connector_panel() -> None:
    state = _get_panel_state()
    if MODE_WIDGET_KEY not in st.session_state or NETWORK_WIDGET_KEY not in st.session_state:
        _sync_widget_state(state)

    st.markdown("### Polymarket Read-Only Connector")
    st.caption(
        "Public market discovery and weather-market preview. No wallet, signing, order, cancel, or live execution controls are exposed."
    )
    badge_cols = st.columns([1, 1, 1], gap="small")
    with badge_cols[0]:
        render_status_badge(str(state["mode"]))
    with badge_cols[1]:
        render_status_badge(
            "NETWORK ON" if bool(state["allow_polymarket_network"]) else "NETWORK OFF"
        )
    with badge_cols[2]:
        render_status_badge("READ ONLY")

    with st.container(border=True):
        cols = st.columns([1, 1, 1], gap="small")
        with cols[0]:
            st.selectbox("Source Mode", MODE_OPTIONS, key=MODE_WIDGET_KEY)
        with cols[1]:
            st.selectbox("Polymarket Network", ("Disabled", "Enabled"), key=NETWORK_WIDGET_KEY)
        with cols[2]:
            st.write("")
            st.write("")
            if st.button("Save Source Mode", use_container_width=True):
                save_source_mode(state)

        action_cols = st.columns(5, gap="small")
        actions = [
            ("Load Mode", load_source_mode),
            ("Check Health", check_health),
            ("Load Cached Markets", load_cached_markets),
            ("Load Weather Markets", load_weather_markets),
            ("Sync Weather Markets", sync_weather_markets),
        ]
        for col, (label, action) in zip(action_cols, actions):
            with col:
                if st.button(label, use_container_width=True):
                    action(state)

    if state.get("message"):
        st.info(str(state["message"]))

    left, right = st.columns(2, gap="medium")
    with left:
        _render_health_card(
            cast(PolymarketConnectorHealth | None, state.get("health")),
            cast(PolymarketConnectorConfig | None, state.get("config")),
        )
    with right:
        _render_warning_box(list(cast(list[str], state.get("warnings") or [])))

    table_left, table_right = st.columns(2, gap="medium")
    with table_left:
        st.markdown("#### Cached Polymarket Markets")
        cached_rows = _cached_markets_rows(
            list(cast(list[PolymarketMarketCacheItem], state.get("cached_markets") or []))
        )
        if cached_rows:
            st.dataframe(cached_rows, use_container_width=True, hide_index=True)
        else:
            st.caption("No cached market records.")
    with table_right:
        st.markdown("#### Market Snapshot Preview")
        preview_rows = _preview_snapshot_rows(
            list(cast(list[PolymarketPreviewSnapshot], state.get("preview_snapshots") or []))
        )
        if preview_rows:
            st.dataframe(preview_rows, use_container_width=True, hide_index=True)
        else:
            st.caption("No preview snapshots.")

    with st.expander("Raw Connector State", expanded=False):
        st.json(
            {
                "mode": state["mode"],
                "allow_polymarket_network": state["allow_polymarket_network"],
                "health": state.get("health"),
                "config": state.get("config"),
                "warnings": state.get("warnings"),
                "cached_markets": state.get("cached_markets"),
                "preview_snapshots": state.get("preview_snapshots"),
            }
        )
