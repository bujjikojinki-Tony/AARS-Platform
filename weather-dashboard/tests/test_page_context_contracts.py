from __future__ import annotations

from weather_dashboard.ui.market_workstation_page import build_market_workstation_view
from weather_dashboard.ui.r5_pages import build_command_context_view


def _workstation_view() -> dict:
    return build_market_workstation_view(
        selected_market_id="m_focus",
        top_parameter_view={
            "schema_version": "top_parameter_view.v2",
            "market_id": "m_focus",
            "market_family": "temperature_daily_max",
            "location_name": "Shanghai",
            "target_date": "2026-04-22",
            "variable_name": "daily_max_temperature",
            "canonical_unit": "celsius",
            "source_contract": {
                "source_match_grade": "exact_station",
                "official_vs_proxy_source": "official",
                "freshness_status": "fresh",
            },
            "polymarket": {
                "market_implied_probability": 0.52,
                "yes_price": 0.52,
                "no_price": 0.48,
            },
            "decision": {
                "fair_value": 0.61,
                "edge": 0.09,
                "probability_mode": "shadow_calibrated_candidate",
            },
        },
        resolver_rule={
            "market_id": "m_focus",
            "band_scheme": "temperature_celsius_integer",
            "resolver_confidence": 0.92,
        },
        comparison_row={"market_id": "m_focus"},
        gate_summary={
            "gate_status": "BLOCKED",
            "can_execute": False,
            "primary_block_reason": "Validation coverage < 80%",
        },
        opportunity_context={
            "row_id": "shanghai.temperature_daily_max",
            "city": "Shanghai",
            "market_family": "temperature_daily_max",
            "best_model": "ECMWF",
            "best_source_stack": ["ecmwf", "metar"],
            "source_precision_score": 0.88,
            "difficulty_label": "easy",
            "recommended_action": "open_workstation",
        },
        validation_summary={
            "label_coverage": 0.723,
            "promotion_state": "shadow_calibrated_candidate",
        },
    )


def test_page_context_contracts_remain_stable_across_core_flows() -> None:
    workstation_view = _workstation_view()

    flow_cases = [
        (
            "operations_monitor",
            "workstation",
            build_market_workstation_view,
            {
                "source_page": "operations_monitor",
                "target_page": "workstation",
                "selected_market_id": "m_focus",
                "entry_reason": "open_workstation",
                "entry_context": {"recommended_action": "open_workstation"},
            },
        ),
        (
            "opportunity_board",
            "workstation",
            build_market_workstation_view,
            {
                "source_page": "opportunity_board",
                "target_page": "workstation",
                "selected_market_id": "m_focus",
                "entry_reason": "open_workstation",
                "entry_context": {"recommended_action": "open_workstation", "row_id": "shanghai.temperature_daily_max"},
            },
        ),
        (
            "workstation",
            "command",
            build_command_context_view,
            {
                "source_page": "workstation",
                "target_page": "command",
                "selected_market_id": "m_focus",
                "entry_reason": "send_to_command",
                "entry_context": {"recommended_action": "review_evidence", "best_model": "ECMWF"},
            },
        ),
        (
            "operations_monitor",
            "command",
            build_command_context_view,
            {
                "source_page": "operations_monitor",
                "target_page": "command",
                "selected_market_id": "m_focus",
                "entry_reason": "send_to_command",
                "entry_context": {"recommended_action": "review_evidence", "best_model": "ECMWF"},
            },
        ),
    ]

    for source_page, target_page, builder, page_context in flow_cases:
        if builder is build_market_workstation_view:
            view = builder(
                selected_market_id="m_focus",
                top_parameter_view=workstation_view["top_parameter_view"],
                resolver_rule={"market_id": "m_focus"},
                comparison_row={"market_id": "m_focus"},
                gate_summary=workstation_view["latest_gate"],
                opportunity_context=workstation_view["opportunity_context"],
                validation_summary=workstation_view["validation_compare_panel"],
                page_context=page_context,
            )
        else:
            view = builder(
                workstation_view=workstation_view,
                page_context=page_context,
                bot_authorized=True,
            )

        assert view["page_context"]["source_page"] == source_page
        assert view["page_context"]["target_page"] == target_page
        assert view["page_context"]["selected_market_id"] == "m_focus"
        assert view["page_context"]["entry_context"]["recommended_action"] == page_context["entry_context"]["recommended_action"]
        assert view["page_context"]["entry_reason"] == page_context["entry_reason"]
        if builder is build_command_context_view:
            assert view["command_context"]["research_direction"] == "review_evidence"
            assert view["command_context"]["edge"] == 0.09
