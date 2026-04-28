from __future__ import annotations

import json
from pathlib import Path

import weather_dashboard.ui.r5_pages as r5_pages


def test_markets_inventory_rows_merge_focus_and_hidden_state(monkeypatch) -> None:
    monkeypatch.setitem(
        r5_pages.st.session_state,
        "r5_focus_market_ids",
        ["shanghai"],
    )
    monkeypatch.setitem(
        r5_pages.st.session_state,
        "market_watchlist_removed",
        [
            {
                "market_id": "berlin",
                "market": "Berlin, DE",
                "region": "Europe",
            }
        ],
    )
    monkeypatch.setitem(
        r5_pages.st.session_state,
        "market_watchlist_overrides",
        [
            {
                "market_id": "shanghai",
                "market": "Shanghai, CN",
                "region": "Asia",
                "signal": "Rainfall > 50mm",
                "watchlist": "WATCHED",
                "focus": "PINNED",
            }
        ],
    )

    inventory = r5_pages._market_inventory_rows(
        [
            {
                "market_id": "shanghai",
                "market": "Shanghai, CN",
                "region": "Asia",
                "signal": "Rainfall > 50mm",
                "group": "WATCH",
                "watchlist": "WATCHED",
                "focus": "NO",
                "scan_priority": "P2",
                "resolver": "OK",
                "source": "LIVE",
                "action_hint": "View",
            }
        ]
    )

    shanghai = next(row for row in inventory if row["market_id"] == "shanghai")
    berlin = next(row for row in inventory if row["market_id"] == "berlin")

    assert shanghai["group"] == "FOCUS"
    assert shanghai["focus"] == "PINNED"
    assert berlin["group"] == "HIDDEN"
    assert berlin["watchlist"] == "REMOVED"
    assert berlin["action_hint"] == "Restore"


def test_markets_page_context_and_results_are_persisted(tmp_path, monkeypatch) -> None:
    context_path = tmp_path / "page_context.json"
    monkeypatch.setattr(r5_pages, "PAGE_CONTEXT_JSON", context_path)
    monkeypatch.setitem(r5_pages.st.session_state, "markets_page_results", {})

    payload = r5_pages._write_markets_page_context(
        source_page="markets",
        target_page="markets",
        selected_market_id="shanghai",
        selected_row_id="shanghai",
        entry_reason="inventory_review",
        entry_context={"active_group": "FOCUS", "selected_market": "Shanghai, CN"},
    )
    r5_pages._set_markets_result("Focus added", "Shanghai added to focus markets.", "good")

    context = json.loads(context_path.read_text(encoding="utf-8"))
    result = r5_pages.st.session_state["markets_page_results"]["markets"]

    assert payload["schema_version"] == "page_context.v1"
    assert context["source_page"] == "markets"
    assert context["target_page"] == "markets"
    assert context["selected_market_id"] == "shanghai"
    assert context["entry_context"]["selected_market"] == "Shanghai, CN"
    assert result["title"] == "Focus added"
    assert result["message"] == "Shanghai added to focus markets."
    assert result["tone"] == "good"


def test_markets_page_source_contains_paging_and_realtime_explanation() -> None:
    source = Path("weather-dashboard/src/weather_dashboard/ui/r5_pages.py").read_text(encoding="utf-8")

    assert "Rows / page" in source
    assert "Showing {page_start + 1 if page_rows else 0} to {page_end} of {total_rows} filtered inventory rows" in source
    assert "LIVE = current snapshot" in source
    assert "market fields refresh when dashboard autorefresh ticks" in source
