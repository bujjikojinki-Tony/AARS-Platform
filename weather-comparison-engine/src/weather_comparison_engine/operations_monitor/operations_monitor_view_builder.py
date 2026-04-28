from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from weather_comparison_engine.operations_monitor.models import (
    FocusMarketItem,
    MarketMonitorCard,
    OperationsMonitorView,
)
from weather_comparison_engine.governance.page_context import normalize_page_context
from weather_comparison_engine.settings import (
    ALERTS_OUTPUT_DIR,
    FAMILY_ANOMALY_SUMMARY_JSON,
    GATE_STACK_API_JSON,
    MARKET_ALERT_EVENTS_DIR,
    MARKET_ANOMALY_EVENTS_DIR,
    MARKET_UNIVERSE_SNAPSHOT_JSON,
    MARKET_WORKSTATION_OUTPUT_DIR,
    OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
    SCAN_QUEUE_STATUS_JSON,
    SCANNER_OPS_ALERTS_JSON,
    SCANNER_STATUS_JSON,
    SOURCE_POLICY_STATUS_JSON,
    EVIDENCE_SCAN_SNAPSHOT_JSON,
    UNIFIED_STATUS_JSON,
)


def build_operations_monitor_view_from_files(
    *,
    page_context: dict[str, Any] | None = None,
    scanner_status_path: Path = SCANNER_STATUS_JSON,
    scan_queue_status_path: Path = SCAN_QUEUE_STATUS_JSON,
    market_universe_snapshot_path: Path = MARKET_UNIVERSE_SNAPSHOT_JSON,
    evidence_scan_snapshot_path: Path = EVIDENCE_SCAN_SNAPSHOT_JSON,
    opportunity_board_path: Path = OPPORTUNITY_BOARD_CANONICAL_VIEW_JSON,
    source_policy_status_path: Path = SOURCE_POLICY_STATUS_JSON,
    gate_stack_api_path: Path = GATE_STACK_API_JSON,
    unified_status_path: Path = UNIFIED_STATUS_JSON,
    family_anomaly_summary_path: Path = FAMILY_ANOMALY_SUMMARY_JSON,
    market_alert_events_dir: Path = MARKET_ALERT_EVENTS_DIR,
    market_anomaly_events_dir: Path = MARKET_ANOMALY_EVENTS_DIR,
    market_workstation_dir: Path = MARKET_WORKSTATION_OUTPUT_DIR,
    scanner_ops_alerts_path: Path = SCANNER_OPS_ALERTS_JSON,
    now: datetime | None = None,
) -> OperationsMonitorView:
    return build_operations_monitor_view(
        page_context=page_context,
        scanner_status=_load_json_file(scanner_status_path),
        scan_queue_status=_load_json_file(scan_queue_status_path),
        market_universe_snapshot=_load_json_file(market_universe_snapshot_path),
        evidence_scan_snapshot=_load_json_file(evidence_scan_snapshot_path),
        opportunity_board=_load_json_file(opportunity_board_path),
        source_policy_status=_load_json_file(source_policy_status_path),
        gate_stack_api=_load_json_file(gate_stack_api_path),
        unified_status=_load_json_file(unified_status_path),
        family_anomaly_summary=_load_json_file(family_anomaly_summary_path),
        market_alert_events_dir=market_alert_events_dir,
        market_anomaly_events_dir=market_anomaly_events_dir,
        market_workstation_dir=market_workstation_dir,
        scanner_ops_alerts=_load_json_records(scanner_ops_alerts_path),
        now=now,
    )


def build_operations_monitor_view(
    *,
    page_context: dict[str, Any] | None = None,
    scanner_status: dict[str, Any] | None = None,
    scan_queue_status: dict[str, Any] | None = None,
    market_universe_snapshot: dict[str, Any] | None = None,
    evidence_scan_snapshot: dict[str, Any] | None = None,
    opportunity_board: dict[str, Any] | None = None,
    source_policy_status: dict[str, Any] | None = None,
    gate_stack_api: dict[str, Any] | None = None,
    unified_status: dict[str, Any] | None = None,
    family_anomaly_summary: dict[str, Any] | None = None,
    market_alert_events_dir: Path | None = None,
    market_anomaly_events_dir: Path | None = None,
    market_workstation_dir: Path | None = None,
    scanner_ops_alerts: list[dict[str, Any]] | None = None,
    now: datetime | None = None,
) -> OperationsMonitorView:
    now = now or datetime.now(timezone.utc)
    scanner_status = scanner_status if isinstance(scanner_status, dict) else {}
    scan_queue_status = scan_queue_status if isinstance(scan_queue_status, dict) else {}
    market_universe_snapshot = market_universe_snapshot if isinstance(market_universe_snapshot, dict) else {}
    evidence_scan_snapshot = evidence_scan_snapshot if isinstance(evidence_scan_snapshot, dict) else {}
    opportunity_board = opportunity_board if isinstance(opportunity_board, dict) else {}
    source_policy_status = source_policy_status if isinstance(source_policy_status, dict) else {}
    gate_stack_api = gate_stack_api if isinstance(gate_stack_api, dict) else {}
    unified_status = unified_status if isinstance(unified_status, dict) else {}
    family_anomaly_summary = family_anomaly_summary if isinstance(family_anomaly_summary, dict) else {}
    scanner_ops_alerts = [item for item in (scanner_ops_alerts or []) if isinstance(item, dict)]
    page_context = normalize_page_context(
        page_context,
        source_page="operations_monitor",
        target_page=str((page_context or {}).get("target_page") or "operations_monitor"),
        selected_market_id=str((page_context or {}).get("selected_market_id") or ""),
        selected_row_id=str((page_context or {}).get("selected_row_id") or ""),
        entry_reason=str((page_context or {}).get("entry_reason") or "runtime_home"),
        entry_context=(page_context or {}).get("entry_context") if isinstance(page_context, dict) else {},
        upstream_refs={
            "scanner_status_ref": str(scanner_status.get("generated_at") or "-"),
            "scan_queue_ref": str(scan_queue_status.get("generated_at") or "-"),
        },
        now=now,
    )

    universe_markets = [item for item in (market_universe_snapshot.get("markets") or []) if isinstance(item, dict)]
    evidence_rows = [item for item in (evidence_scan_snapshot.get("rows") or []) if isinstance(item, dict)]
    opportunity_rows = [item for item in (opportunity_board.get("rows") or []) if isinstance(item, dict)]
    opportunity_by_key = _build_opportunity_index(opportunity_rows)
    evidence_by_key = _build_evidence_index(evidence_rows)

    cards = _build_market_monitor_cards(
        universe_markets,
        opportunity_by_key=opportunity_by_key,
        evidence_by_key=evidence_by_key,
        market_alert_events_dir=market_alert_events_dir,
        market_anomaly_events_dir=market_anomaly_events_dir,
        market_workstation_dir=market_workstation_dir,
        unified_status=unified_status,
    )
    selected_market_id = _selected_market_id(unified_status, cards)
    page_selected_market_id = str(page_context.get("selected_market_id") or "").strip()
    if page_selected_market_id:
        selected_market_id = page_selected_market_id
    focus_markets = _build_focus_markets(cards, selected_market_id=selected_market_id)
    selected_quick_detail = _build_selected_market_quick_detail(
        selected_market_id=selected_market_id,
        cards=cards,
        market_workstation_dir=market_workstation_dir,
        opportunity_by_key=opportunity_by_key,
        evidence_by_key=evidence_by_key,
    )
    derived_ops_alerts = _build_ops_alerts(
        scanner_status=scanner_status,
        scan_queue_status=scan_queue_status,
        source_policy_status=source_policy_status,
        scanner_ops_alerts=scanner_ops_alerts,
    )
    system_health = _build_system_health(
        scanner_status=scanner_status,
        scan_queue_status=scan_queue_status,
        source_policy_status=source_policy_status,
        ops_alerts=derived_ops_alerts,
        family_anomaly_summary=family_anomaly_summary,
    )
    global_summary = _build_global_summary(
        scanner_status=scanner_status,
        cards=cards,
        focus_markets=focus_markets,
        scan_queue_status=scan_queue_status,
        source_policy_status=source_policy_status,
        ops_alerts=derived_ops_alerts,
    )

    view: OperationsMonitorView = {
        "schema_version": "operations_monitor_view.v1",
        "generated_at": now.isoformat(),
        "page_context": page_context,
        "global_summary": global_summary,
        "focus_markets": focus_markets,
        "market_monitor_cards": cards,
        "system_health": system_health,
        "ops_alerts": derived_ops_alerts,
        "selected_market_quick_detail": selected_quick_detail,
        "view_context": {
            "selected_market_id": selected_market_id,
            "focus_market_count": len(focus_markets),
            "market_count": len(cards),
            "family_count": len({str(item.get("market_family") or "-") for item in cards}),
            "source_version": market_universe_snapshot.get("schema_version") or "-",
            "scanner_version": scanner_status.get("schema_version") or "-",
            "page_context": page_context,
        },
        "upstream_refs": {
            "scanner_status_ref": str(scanner_status.get("generated_at") or "-"),
            "scan_queue_ref": str(scan_queue_status.get("generated_at") or "-"),
            "market_universe_ref": str(market_universe_snapshot.get("generated_at") or "-"),
            "evidence_scan_ref": str(evidence_scan_snapshot.get("generated_at") or "-"),
            "opportunity_board_ref": str(opportunity_board.get("generated_at") or "-"),
            "source_policy_ref": str(source_policy_status.get("generated_at") or "-"),
            "gate_stack_ref": str(gate_stack_api.get("generated_at") or "-"),
            "unified_status_ref": str(unified_status.get("generated_at") or "-"),
            "family_anomaly_ref": str(family_anomaly_summary.get("generated_at") or "-"),
        },
    }
    return view


def write_operations_monitor_view(path: str | Path, payload: OperationsMonitorView) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def write_operations_monitor_artifacts(
    *,
    view_path: str | Path,
    summary_path: str | Path,
    payload: OperationsMonitorView,
) -> dict[str, Path]:
    view_out = write_operations_monitor_view(view_path, payload)
    summary_out = Path(summary_path)
    summary_out.parent.mkdir(parents=True, exist_ok=True)
    summary_out.write_text(
        json.dumps(_build_summary_artifact(payload), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {
        "view": view_out,
        "summary": summary_out,
    }


def _build_market_monitor_cards(
    universe_markets: list[dict[str, Any]],
    *,
    opportunity_by_key: dict[str, dict[str, Any]],
    evidence_by_key: dict[str, dict[str, Any]],
    market_alert_events_dir: Path | None,
    market_anomaly_events_dir: Path | None,
    market_workstation_dir: Path | None,
    unified_status: dict[str, Any],
) -> list[MarketMonitorCard]:
    cards: list[MarketMonitorCard] = []
    for market in universe_markets:
        market_id = str(market.get("market_id") or "").strip()
        city = str(market.get("city") or market.get("location_name") or "-").strip() or "-"
        family = str(market.get("market_family") or "-").strip() or "-"
        key = _market_key(market_id=market_id, city=city, market_family=family)
        opportunity_row = opportunity_by_key.get(key) or {}
        evidence_row = evidence_by_key.get(key) or {}
        market_alert = _load_latest_matching_json(
            market_alert_events_dir,
            tokens=[market_id, city, family, str(opportunity_row.get("row_id") or "")],
        )
        market_anomaly = _load_latest_matching_jsonl(
            market_anomaly_events_dir,
            tokens=[market_id, city, family, str(opportunity_row.get("row_id") or "")],
        )
        workstation_view = _load_latest_market_workstation_view(
            market_workstation_dir,
            tokens=[market_id, city, family, str(opportunity_row.get("row_id") or "")],
        )
        latest_gate = workstation_view.get("latest_gate") if isinstance(workstation_view, dict) else {}
        gate_advisory_panel = workstation_view.get("gate_advisory_panel") if isinstance(workstation_view, dict) else {}
        gate_summary = gate_advisory_panel.get("gate_summary") if isinstance(gate_advisory_panel, dict) else {}
        best_model = (
            str(opportunity_row.get("best_model") or evidence_row.get("best_model") or market.get("best_model") or "-")
        )
        freshness_status = str(
            evidence_row.get("freshness_status")
            or market.get("freshness_status")
            or opportunity_row.get("freshness_status")
            or "unknown"
        )
        latest_alert_severity = str(
            market_alert.get("severity")
            or opportunity_row.get("latest_alert_severity")
            or evidence_row.get("latest_alert_severity")
            or "-"
        )
        latest_anomaly_score = _coerce_float(
            market_anomaly.get("anomaly_score")
            or market_anomaly.get("intervention_like_score")
            or evidence_row.get("latest_anomaly_score")
            or opportunity_row.get("latest_anomaly_score")
        )
        latest_gate_can_execute = latest_gate.get("can_execute") if isinstance(latest_gate, dict) else None
        gate_summary_can_execute = gate_summary.get("can_execute") if isinstance(gate_summary, dict) else None
        can_execute = _coerce_bool(
            latest_gate_can_execute if latest_gate_can_execute is not None else gate_summary_can_execute
        )
        primary_block_reason = str(
            latest_gate.get("primary_block_reason") if isinstance(latest_gate, dict) else None
            or gate_summary.get("primary_block_reason") if isinstance(gate_summary, dict) else None
            or market.get("primary_block_reason")
            or opportunity_row.get("gate_risk_summary")
            or "-"
        )
        recommended_action = str(
            opportunity_row.get("recommended_action")
            or workstation_view.get("recommended_operator_action")
            or _derive_recommended_action(latest_alert_severity, latest_anomaly_score, freshness_status, can_execute)
        )
        opportunity_score = _coerce_float(
            opportunity_row.get("opportunity_score")
            or market.get("opportunity_score")
            or _derive_opportunity_score(
                market,
                latest_alert_severity=latest_alert_severity,
                latest_anomaly_score=latest_anomaly_score,
                freshness_status=freshness_status,
            )
        )
        difficulty_label = str(
            opportunity_row.get("difficulty_label")
            or market.get("difficulty_label")
            or _derive_difficulty_label(
                market.get("source_match_grade"),
                freshness_status,
                can_execute,
            )
        )
        source_precision_score = _coerce_float(
            opportunity_row.get("source_precision_score")
            or evidence_row.get("source_precision_score")
            or market.get("source_precision_score")
            or _derive_source_precision_score(market.get("source_match_grade"))
        )
        primary_state, secondary_states, primary_state_reason = _derive_primary_state(
            latest_alert_severity=latest_alert_severity,
            latest_anomaly_score=latest_anomaly_score,
            freshness_status=freshness_status,
            can_execute=can_execute,
            primary_block_reason=primary_block_reason,
            selected_market=bool(
                str(unified_status.get("current_market", {}).get("market_id") or "").strip() == market_id
            ),
        )
        display_priority = _derive_display_priority(
            opportunity_score=opportunity_score,
            latest_alert_severity=latest_alert_severity,
            latest_anomaly_score=latest_anomaly_score,
            freshness_status=freshness_status,
            can_execute=can_execute,
            selected_market=bool(
                str(unified_status.get("current_market", {}).get("market_id") or "").strip() == market_id
            ),
        )
        cards.append(
            {
                "schema_version": "market_monitor_card.v1",
                "market_id": market_id,
                "city": city,
                "market_family": family,
                "market_question_short": _shorten_text(
                    market.get("question")
                    or market.get("market_question")
                    or opportunity_row.get("market_question")
                    or "-",
                    72,
                ),
                "opportunity_score": round(float(opportunity_score), 3),
                "difficulty_label": difficulty_label,
                "best_model": best_model,
                "freshness_status": freshness_status,
                "source_precision_score": round(float(source_precision_score), 3),
                "latest_alert_severity": latest_alert_severity,
                "latest_anomaly_score": latest_anomaly_score,
                "primary_state": primary_state,
                "secondary_states": secondary_states,
                "primary_state_reason": primary_state_reason,
                "display_priority": display_priority,
                "can_execute": can_execute,
                "primary_block_reason": primary_block_reason,
                "recommended_action": recommended_action,
                "is_focus_market": False,
                "scan_priority": str(market.get("scan_priority") or evidence_row.get("scan_priority") or "-"),
                "upstream_refs": {
                    "market_id": market_id,
                    "opportunity_row_id": str(opportunity_row.get("row_id") or "-"),
                    "evidence_ref": str(evidence_row.get("generated_at") or "-"),
                    "alert_ref": str(market_alert.get("event_id") or market_alert.get("generated_at") or "-"),
                    "anomaly_ref": str(market_anomaly.get("event_id") or market_anomaly.get("generated_at") or "-"),
                    "workstation_ref": str(workstation_view.get("generated_at") or "-"),
                },
                "latest_context": {
                    "market_id": market_id,
                    "market_question": market.get("question") or market.get("market_question") or "-",
                    "comparison_status": str(opportunity_row.get("comparison_status") or evidence_row.get("scan_status") or "-"),
                    "freshness_reason": str(market.get("freshness_reason") or evidence_row.get("freshness_reason") or "-"),
                    "alert_reason": str(market_alert.get("primary_reason") or "-"),
                    "anomaly_reason": str(market_anomaly.get("primary_reason") or "-"),
                    "can_execute": can_execute,
                },
                "selected_market": bool(
                    str(unified_status.get("current_market", {}).get("market_id") or "").strip() == market_id
                ),
            }
        )

    cards.sort(
        key=lambda item: (
            not bool(item.get("selected_market")),
            _focus_rank(item),
            -float(item.get("opportunity_score") or 0.0),
            _alert_rank(str(item.get("latest_alert_severity") or "")),
            _freshness_rank(str(item.get("freshness_status") or "")),
            str(item.get("city") or ""),
            str(item.get("market_family") or ""),
        )
    )
    return cards


def _build_focus_markets(cards: list[MarketMonitorCard], *, selected_market_id: str | None) -> list[FocusMarketItem]:
    focus_candidates: list[FocusMarketItem] = []
    selected_market_norm = _normalize_token(selected_market_id)
    for card in cards:
        market_id = str(card.get("market_id") or "")
        market_family = str(card.get("market_family") or "")
        reasons: list[str] = []
        alert_severity = str(card.get("latest_alert_severity") or "-").lower()
        anomaly_score = _coerce_float(card.get("latest_anomaly_score"))
        freshness_status = str(card.get("freshness_status") or "unknown").lower()
        can_execute = bool(card.get("can_execute"))
        block_reason = str(card.get("primary_block_reason") or "-")
        if _normalize_token(market_id) == selected_market_norm and selected_market_norm:
            reasons.append("selected")
        if alert_severity in {"amber", "red", "critical"}:
            reasons.append(f"alert={alert_severity}")
        if anomaly_score >= 0.5:
            reasons.append(f"anomaly={anomaly_score:.2f}")
        if freshness_status in {"stale", "unavailable"}:
            reasons.append(f"freshness={freshness_status}")
        if block_reason not in {"", "-"} and not can_execute:
            reasons.append(f"block={block_reason}")
        if float(card.get("opportunity_score") or 0.0) >= 0.65:
            reasons.append(f"opp={float(card.get('opportunity_score') or 0.0):.2f}")
        if not reasons:
            continue
        focus_candidates.append(
            {
                "market_id": market_id,
                "market_family": market_family,
                "city": str(card.get("city") or "-"),
                "market_question_short": str(card.get("market_question_short") or "-"),
                "focus_reason": ", ".join(dict.fromkeys(reasons)),
                "next_action": _derive_recommended_action(
                    str(card.get("latest_alert_severity") or ""),
                    _coerce_float(card.get("latest_anomaly_score")),
                    str(card.get("freshness_status") or ""),
                    bool(card.get("can_execute")),
                ),
                "latest_priority_score": round(
                    max(
                        float(card.get("opportunity_score") or 0.0),
                        anomaly_score,
                        _alert_weight(alert_severity),
                        1.0 if block_reason not in {"", "-"} and not can_execute else 0.0,
                    ),
                    3,
                ),
                "primary_state": str(card.get("primary_state") or "LIVE"),
                "secondary_states": list(card.get("secondary_states") or []),
                "display_priority": float(card.get("display_priority") or 0.0),
                "is_selected_market": _normalize_token(market_id) == selected_market_norm and bool(selected_market_norm),
                "pinned_by_user": False,
            }
        )

    if not focus_candidates and cards:
        top_card = cards[0]
        focus_candidates.append(
            {
                "market_id": str(top_card.get("market_id") or ""),
                "market_family": str(top_card.get("market_family") or "-"),
                "city": str(top_card.get("city") or "-"),
                "market_question_short": str(top_card.get("market_question_short") or "-"),
                "focus_reason": "top_opportunity",
                "next_action": _derive_recommended_action(
                    str(top_card.get("latest_alert_severity") or ""),
                    _coerce_float(top_card.get("latest_anomaly_score")),
                    str(top_card.get("freshness_status") or ""),
                    bool(top_card.get("can_execute")),
                ),
                "latest_priority_score": round(float(top_card.get("opportunity_score") or 0.0), 3),
                "primary_state": str(top_card.get("primary_state") or "LIVE"),
                "secondary_states": list(top_card.get("secondary_states") or []),
                "display_priority": float(top_card.get("display_priority") or 0.0),
                "is_selected_market": bool(top_card.get("selected_market")),
                "pinned_by_user": False,
            }
        )
    focus_candidates.sort(
        key=lambda item: (
            not bool(item.get("is_selected_market")),
            -float(item.get("latest_priority_score") or 0.0),
            str(item.get("city") or ""),
            str(item.get("market_family") or ""),
        )
    )
    return focus_candidates[:6]


def _build_selected_market_quick_detail(
    *,
    selected_market_id: str,
    cards: list[MarketMonitorCard],
    market_workstation_dir: Path | None,
    opportunity_by_key: dict[str, dict[str, Any]],
    evidence_by_key: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    selected_card = next((item for item in cards if str(item.get("market_id") or "") == selected_market_id), {})
    city = str(selected_card.get("city") or "-")
    family = str(selected_card.get("market_family") or "-")
    card_key = _market_key(market_id=selected_market_id, city=city, market_family=family)
    opportunity_row = opportunity_by_key.get(card_key) or {}
    evidence_row = evidence_by_key.get(card_key) or {}
    workstation_view = _load_latest_market_workstation_view(
        market_workstation_dir,
        tokens=[selected_market_id, city, family, str(opportunity_row.get("row_id") or "")],
    )

    if workstation_view:
        return {
            "schema_version": "selected_market_quick_detail.v1",
            "market_id": selected_market_id,
            "market_question": _pick_text(
                workstation_view.get("top_parameter_view", {}).get("market_question"),
                selected_card.get("market_question_short"),
                opportunity_row.get("market_question"),
            ),
            "city": _pick_text(selected_card.get("city"), opportunity_row.get("city")),
            "market_family": _pick_text(selected_card.get("market_family"), opportunity_row.get("market_family")),
            "opportunity_context": workstation_view.get("entry_context") or {},
            "top_parameter_summary": _summarize_top_parameter_view(
                workstation_view.get("top_parameter_view") or {},
            ),
            "rule_source_model_panel": workstation_view.get("rule_source_model_panel") or {},
            "validation_compare_panel": workstation_view.get("validation_compare_panel") or {},
            "gate_advisory_panel": workstation_view.get("gate_advisory_panel") or {},
            "latest_alert": workstation_view.get("latest_alert") or {},
            "latest_anomaly": workstation_view.get("latest_anomaly") or {},
            "latest_gate": workstation_view.get("latest_gate") or {},
            "latest_ops": workstation_view.get("latest_ops") or {},
            "recommended_operator_action": (
                (workstation_view.get("gate_advisory_panel") or {}).get("advisory_summary", {}).get("recommended_operator_action")
                or selected_card.get("recommended_action")
                or "-"
            ),
            "next_action": (
                (workstation_view.get("gate_advisory_panel") or {}).get("advisory_summary", {}).get("recommended_operator_action")
                or selected_card.get("recommended_action")
                or "-"
            ),
            "execution_boundary": (
                (workstation_view.get("gate_advisory_panel") or {}).get("dry_run_area", {}).get("execution_boundary")
                or "-"
            ),
            "source_refs": {
                "workstation_ref": str(workstation_view.get("generated_at") or "-"),
                "opportunity_row_id": str(opportunity_row.get("row_id") or "-"),
            },
        }

    return {
        "schema_version": "selected_market_quick_detail.v1",
        "market_id": selected_market_id,
        "market_question": _pick_text(selected_card.get("market_question_short"), opportunity_row.get("market_question")),
        "city": _pick_text(selected_card.get("city"), opportunity_row.get("city")),
        "market_family": _pick_text(selected_card.get("market_family"), opportunity_row.get("market_family")),
        "opportunity_context": opportunity_row or {},
        "top_parameter_summary": {
            "display_value": evidence_row.get("display_value") or "-",
            "display_unit": evidence_row.get("display_unit") or "-",
            "model_band": evidence_row.get("model_band") or "-",
            "observation_band": evidence_row.get("observation_band") or "-",
            "source_match_grade": evidence_row.get("source_match_grade") or opportunity_row.get("source_match_grade") or "-",
            "freshness_status": evidence_row.get("freshness_status") or selected_card.get("freshness_status") or "-",
            "primary_state": selected_card.get("primary_state") or "LIVE",
        },
        "rule_source_model_panel": {
            "best_model": selected_card.get("best_model") or opportunity_row.get("best_model") or "-",
            "best_source_stack": selected_card.get("best_source_stack") or opportunity_row.get("best_source_stack") or [],
            "difficulty_label": selected_card.get("difficulty_label") or opportunity_row.get("difficulty_label") or "-",
        },
        "validation_compare_panel": {
            "validation_status": evidence_row.get("validation_status") or "-",
            "promotion_readiness": evidence_row.get("promotion_readiness") or "-",
            "label_coverage": evidence_row.get("label_coverage") or "-",
            "source_coverage": evidence_row.get("source_coverage") or "-",
        },
        "gate_advisory_panel": {
            "gate_status": "unknown",
            "primary_block_reason": selected_card.get("primary_block_reason") or "-",
            "can_execute": selected_card.get("can_execute"),
        },
        "latest_alert": {},
        "latest_anomaly": {},
        "latest_gate": {},
        "latest_ops": {},
        "recommended_operator_action": selected_card.get("recommended_action") or "-",
        "next_action": selected_card.get("recommended_action") or "-",
        "execution_boundary": selected_card.get("primary_block_reason") or "-",
        "source_refs": {
            "workstation_ref": "-",
            "opportunity_row_id": str(opportunity_row.get("row_id") or "-"),
        },
    }


def _build_global_summary(
    *,
    scanner_status: dict[str, Any],
    cards: list[MarketMonitorCard],
    focus_markets: list[FocusMarketItem],
    scan_queue_status: dict[str, Any],
    source_policy_status: dict[str, Any],
    ops_alerts: list[dict[str, Any]],
) -> dict[str, Any]:
    fresh_ratio = _safe_ratio(
        _coerce_int(scanner_status.get("fresh_markets")),
        _coerce_int(scanner_status.get("scanned_markets")),
    )
    families = {str(item.get("market_family") or "-") for item in cards}
    high_alert_markets = sum(1 for item in cards if _alert_weight(str(item.get("latest_alert_severity") or "")) >= 0.5)
    high_anomaly_markets = sum(1 for item in cards if _coerce_float(item.get("latest_anomaly_score")) >= 0.5)
    gate_blocked_markets = sum(
        1
        for item in cards
        if not _coerce_bool(item.get("can_execute")) and str(item.get("primary_block_reason") or "-") not in {"", "-"}
    )
    active_markets = sum(1 for item in cards if str(item.get("scan_priority") or "").lower() not in {"paused", "inactive"})
    source_counts = source_policy_status.get("counts") or {}
    return {
        "markets_scanned": _coerce_int(scanner_status.get("scanned_markets")),
        "focus_markets_count": len(focus_markets),
        "active_weather_markets": active_markets,
        "families_monitored": len(families),
        "high_alert_markets": high_alert_markets,
        "high_anomaly_markets": high_anomaly_markets,
        "gate_blocked_markets": gate_blocked_markets,
        "stale_source_count": _coerce_int(scanner_status.get("stale_markets")),
        "fallback_source_count": _coerce_int(source_counts.get("stale")) + _coerce_int(source_counts.get("unavailable")),
        "unavailable_source_count": _coerce_int(scanner_status.get("unavailable_markets")),
        "ops_alert_count": len(ops_alerts),
        "scan_backlog": _coerce_int(scanner_status.get("backlog_count")),
        "queue_pending": _coerce_int(scan_queue_status.get("accepted_count")),
        "last_refresh_time": str(scanner_status.get("generated_at") or source_policy_status.get("generated_at") or "-"),
        "fresh_ratio": fresh_ratio,
        "priority_mix": scanner_status.get("priority_counts") or {},
        "freshness_mix": scanner_status.get("freshness_counts") or {},
    }


def _build_system_health(
    *,
    scanner_status: dict[str, Any],
    scan_queue_status: dict[str, Any],
    source_policy_status: dict[str, Any],
    ops_alerts: list[dict[str, Any]],
    family_anomaly_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "scanner_health": {
            "status": _scanner_health_label(scanner_status),
            "scanned_markets": _coerce_int(scanner_status.get("scanned_markets")),
            "fresh_markets": _coerce_int(scanner_status.get("fresh_markets")),
            "stale_markets": _coerce_int(scanner_status.get("stale_markets")),
            "unavailable_markets": _coerce_int(scanner_status.get("unavailable_markets")),
            "alert_markets": _coerce_int(scanner_status.get("alert_markets")),
            "backlog_count": _coerce_int(scanner_status.get("backlog_count")),
            "next_scan_eta": str(scanner_status.get("next_scan_eta") or "-"),
            "priority_counts": scanner_status.get("priority_counts") or {},
            "freshness_counts": scanner_status.get("freshness_counts") or {},
        },
        "source_health": {
            "overall_status": str(source_policy_status.get("overall_status") or "-"),
            "counts": source_policy_status.get("counts") or {},
            "priority_counts": source_policy_status.get("priority_counts") or {},
            "fallback_count": _coerce_int((source_policy_status.get("counts") or {}).get("fallback")),
            "precision_degrade_count": _coerce_int((source_policy_status.get("counts") or {}).get("precision_degrade")),
            "problem_sources": [
                {
                    "source_name": item.get("source_name"),
                    "freshness_status": item.get("freshness_status"),
                    "status_reason": item.get("status_reason"),
                    "priority_level": item.get("priority_level"),
                }
                for item in (source_policy_status.get("problem_sources") or [])[:4]
                if isinstance(item, dict)
            ],
        },
        "queue_health": {
            "schema_version": str(scan_queue_status.get("schema_version") or "alert_queue_status.v1"),
            "accepted_count": _coerce_int(scan_queue_status.get("accepted_count")),
            "pending_count": _coerce_int(scan_queue_status.get("pending_count")),
            "sent_count": _coerce_int(scan_queue_status.get("sent_count")),
            "acked_count": _coerce_int(scan_queue_status.get("acked_count")),
            "suppressed_count": _coerce_int(scan_queue_status.get("suppressed_count")),
            "output_path": str(scan_queue_status.get("output_path") or "-"),
            "alerts_output_dir": str(scan_queue_status.get("alerts_output_dir") or "-"),
        },
        "family_scan_health": {
            "schema_version": str(family_anomaly_summary.get("schema_version") or "-"),
            "market_family": str(family_anomaly_summary.get("market_family") or "-"),
            "scanned_market_count": _coerce_int(family_anomaly_summary.get("scanned_market_count")),
            "high_anomaly_count": _coerce_int(family_anomaly_summary.get("high_anomaly_count")),
            "high_intervention_like_count": _coerce_int(family_anomaly_summary.get("high_intervention_like_count")),
            "family_risk_summary": str(family_anomaly_summary.get("family_risk_summary") or "-"),
        },
        "latest_ops_alerts": ops_alerts[:5],
    }


def _build_ops_alerts(
    *,
    scanner_status: dict[str, Any],
    scan_queue_status: dict[str, Any],
    source_policy_status: dict[str, Any],
    scanner_ops_alerts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    alerts = [item for item in scanner_ops_alerts if isinstance(item, dict)]
    if alerts:
        alerts.sort(key=lambda item: (_alert_rank(str(item.get("severity") or "")), str(item.get("generated_at") or "")))
        return alerts

    derived: list[dict[str, Any]] = []
    for source in (source_policy_status.get("problem_sources") or [])[:5]:
        if not isinstance(source, dict):
            continue
        severity = "red" if str(source.get("freshness_status") or "").lower() == "unavailable" else "amber"
        derived.append(
            {
                "alert_id": _slugify(str(source.get("source_name") or "ops")),
                "alert_type": "source_unavailable" if severity == "red" else "source_degraded",
                "severity": severity,
                "component": str(source.get("source_name") or "-"),
                "primary_reason": str(source.get("status_reason") or source.get("fallback_policy") or "-"),
                "affected_scope": str(source.get("source_type") or "-"),
                "cooldown_until": "-",
                "generated_at": str(source.get("observed_at") or source_policy_status.get("generated_at") or "-"),
            }
        )
    if _coerce_int(scanner_status.get("backlog_count")) > 0:
        derived.append(
            {
                "alert_id": "scan_backlog",
                "alert_type": "scan_backlog",
                "severity": "amber",
                "component": "scanner",
                "primary_reason": f"backlog_count={scanner_status.get('backlog_count')}",
                "affected_scope": "scan_pipeline",
                "cooldown_until": "-",
                "generated_at": str(scanner_status.get("generated_at") or "-"),
            }
        )
    if _coerce_int(scan_queue_status.get("accepted_count")) == 0 and not derived:
        derived.append(
            {
                "alert_id": "no_ops_alerts",
                "alert_type": "heartbeat",
                "severity": "info",
                "component": "operations_monitor",
                "primary_reason": "no active ops alerts",
                "affected_scope": "monitoring",
                "cooldown_until": "-",
                "generated_at": str(scanner_status.get("generated_at") or scan_queue_status.get("generated_at") or "-"),
            }
        )
    return derived


def _build_summary_artifact(payload: OperationsMonitorView) -> dict[str, Any]:
    global_summary = payload.get("global_summary") or {}
    selected_detail = payload.get("selected_market_quick_detail") or {}
    system_health = payload.get("system_health") or {}
    scanner_health = system_health.get("scanner_health") or {}
    source_health = system_health.get("source_health") or {}
    queue_health = system_health.get("queue_health") or {}
    return {
        "schema_version": "operations_monitor_summary.v1",
        "generated_at": payload.get("generated_at"),
        "selected_market_id": (payload.get("view_context") or {}).get("selected_market_id") or "-",
        "markets_scanned": global_summary.get("markets_scanned"),
        "focus_markets_count": global_summary.get("focus_markets_count"),
        "fresh_ratio": global_summary.get("fresh_ratio"),
        "high_alert_markets": global_summary.get("high_alert_markets"),
        "high_anomaly_markets": global_summary.get("high_anomaly_markets"),
        "gate_blocked_markets": global_summary.get("gate_blocked_markets"),
        "ops_alert_count": global_summary.get("ops_alert_count"),
        "scanner_status": scanner_health.get("status"),
        "scanner_next_scan_eta": scanner_health.get("next_scan_eta"),
        "source_status": source_health.get("overall_status"),
        "queue_accepted_count": queue_health.get("accepted_count"),
        "queue_suppressed_count": queue_health.get("suppressed_count"),
        "recommended_operator_action": _pick_text(
            selected_detail.get("recommended_operator_action"),
            _derive_monitor_action(global_summary, system_health),
        ),
        "primary_warning": _pick_text(
            _first_problem_reason(source_health.get("problem_sources") or []),
            _first_ops_alert_reason(payload.get("ops_alerts") or []),
            "all clear",
        ),
        "focus_markets": [
            {
                "market_id": item.get("market_id"),
                "market_family": item.get("market_family"),
                "focus_reason": item.get("focus_reason"),
            }
            for item in (payload.get("focus_markets") or [])[:5]
            if isinstance(item, dict)
        ],
        "selected_market_summary": {
            "market_question": selected_detail.get("market_question"),
            "execution_boundary": selected_detail.get("execution_boundary"),
            "market_family": selected_detail.get("market_family"),
        },
    }


def _build_opportunity_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for key in {
            _market_key(
                market_id=str(row.get("market_id") or ""),
                city=str(row.get("city") or ""),
                market_family=str(row.get("market_family") or ""),
            ),
            _market_key(
                market_id=_first_item((row.get("upstream_refs") or {}).get("market_ids")),
                city=str(row.get("city") or ""),
                market_family=str(row.get("market_family") or ""),
            ),
            _market_key(city=str(row.get("city") or ""), market_family=str(row.get("market_family") or "")),
        }:
            if key:
                index.setdefault(key, row)
    return index


def _build_evidence_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = _market_key(
            market_id=str(row.get("market_id") or ""),
            city=str(row.get("city") or ""),
            market_family=str(row.get("market_family") or ""),
        )
        if key:
            index.setdefault(key, row)
    return index


def _selected_market_id(unified_status: dict[str, Any], cards: list[MarketMonitorCard]) -> str:
    current_market = unified_status.get("current_market") if isinstance(unified_status.get("current_market"), dict) else {}
    current_market_id = str(current_market.get("market_id") or "").strip()
    if current_market_id:
        return current_market_id
    if cards:
        return str(cards[0].get("market_id") or "")
    return ""


def _load_latest_market_workstation_view(directory: Path | None, *, tokens: list[str]) -> dict[str, Any]:
    if not directory or not directory.exists():
        return {}
    candidates = sorted(directory.glob("market_workstation_*.json"), key=_sort_key, reverse=True)
    if not candidates:
        return {}
    normalized_tokens = [_normalize_token(token) for token in tokens if token]
    for path in candidates:
        payload = _load_json_file(path)
        if not payload:
            continue
        if _payload_matches_tokens(payload, normalized_tokens) or _payload_matches_tokens(path.name, normalized_tokens):
            return payload
    return {}


def _load_latest_matching_json(directory: Path | None, *, tokens: list[str]) -> dict[str, Any]:
    if not directory or not directory.exists():
        return {}
    candidates = sorted(directory.glob("*.json"), key=_sort_key, reverse=True)
    normalized_tokens = [_normalize_token(token) for token in tokens if token]
    for path in candidates:
        payload = _load_json_file(path)
        if not payload:
            continue
        if _payload_matches_tokens(payload, normalized_tokens) or _payload_matches_tokens(path.name, normalized_tokens):
            return payload
    return {}


def _load_latest_matching_jsonl(directory: Path | None, *, tokens: list[str]) -> dict[str, Any]:
    if not directory or not directory.exists():
        return {}
    candidates = sorted(directory.glob("*.jsonl"), key=_sort_key, reverse=True)
    normalized_tokens = [_normalize_token(token) for token in tokens if token]
    for path in candidates:
        try:
            lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        except Exception:
            continue
        for line in reversed(lines):
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            if _payload_matches_tokens(payload, normalized_tokens):
                return payload
    return {}


def _payload_matches_tokens(value: Any, normalized_tokens: list[str]) -> bool:
    if not normalized_tokens:
        return False
    if isinstance(value, dict):
        return any(_payload_matches_tokens(item, normalized_tokens) for item in value.values())
    if isinstance(value, list):
        return any(_payload_matches_tokens(item, normalized_tokens) for item in value)
    if value is None:
        return False
    token = _normalize_token(str(value))
    if not token:
        return False
    return any(tok in token or token in tok for tok in normalized_tokens)


def _load_json_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _load_json_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        return [payload]
    return []


def _sort_key(path: Path) -> datetime:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _normalize_token(value: object) -> str:
    token = re.sub(r"[^a-z0-9]+", "", str(value or "").lower())
    return token


def _market_key(*, market_id: str = "", city: str = "", market_family: str = "") -> str:
    tokens = [
        _normalize_token(market_id),
        _normalize_token(city),
        _normalize_token(market_family),
    ]
    tokens = [token for token in tokens if token]
    return "::".join(tokens)


def _coerce_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: object, default: int = 0) -> int:
    try:
        return int(value if value is not None else default)
    except (TypeError, ValueError):
        return default


def _coerce_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off"}:
            return False
    return default


def _pick_text(*values: object) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
    return "-"


def _first_item(value: object) -> str:
    if isinstance(value, list) and value:
        return str(value[0] or "")
    if isinstance(value, tuple) and value:
        return str(value[0] or "")
    if isinstance(value, str):
        return value
    return ""


def _shorten_text(value: object, limit: int) -> str:
    text = _pick_text(value)
    if len(text) <= limit:
        return text
    if limit <= 3:
        return text[:limit]
    return f"{text[: limit - 1].rstrip()}…"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "ops-alert"


def _safe_ratio(numerator: int, denominator: int) -> str:
    if denominator <= 0:
        return "0.00"
    return f"{numerator / denominator:.2f}"


def _alert_weight(severity: str) -> float:
    severity = severity.lower()
    if severity in {"red", "critical"}:
        return 1.0
    if severity in {"amber", "high"}:
        return 0.7
    if severity in {"watch", "warning"}:
        return 0.35
    return 0.0


def _alert_rank(severity: str) -> int:
    severity = severity.lower()
    if severity in {"red", "critical"}:
        return 0
    if severity in {"amber", "high"}:
        return 1
    if severity in {"watch", "warning"}:
        return 2
    return 3


def _focus_rank(card: MarketMonitorCard) -> float:
    anomaly_score = _coerce_float(card.get("latest_anomaly_score"))
    alert_weight = _alert_weight(str(card.get("latest_alert_severity") or ""))
    block_weight = 1.0 if not _coerce_bool(card.get("can_execute")) and str(card.get("primary_block_reason") or "-") not in {"", "-"} else 0.0
    state_weight = _state_weight(str(card.get("primary_state") or ""))
    priority = float(card.get("display_priority") or 0.0) / 100.0
    return max(float(card.get("opportunity_score") or 0.0), anomaly_score, alert_weight, block_weight, state_weight, priority)


def _freshness_rank(freshness: str) -> int:
    freshness = freshness.lower()
    if freshness == "fresh":
        return 0
    if freshness == "seed_prior":
        return 1
    if freshness == "stale":
        return 2
    if freshness == "unavailable":
        return 3
    return 4


def _scanner_health_label(scanner_status: dict[str, Any]) -> str:
    scanned = _coerce_int(scanner_status.get("scanned_markets"))
    fresh = _coerce_int(scanner_status.get("fresh_markets"))
    stale = _coerce_int(scanner_status.get("stale_markets"))
    unavailable = _coerce_int(scanner_status.get("unavailable_markets"))
    backlog = _coerce_int(scanner_status.get("backlog_count"))
    if unavailable > 0 or backlog > 0:
        return "degraded"
    if scanned > 0 and fresh >= stale:
        return "healthy"
    return "warning"


def _derive_opportunity_score(
    market: dict[str, Any],
    *,
    latest_alert_severity: str,
    latest_anomaly_score: float | None,
    freshness_status: str,
) -> float:
    priority = str(market.get("scan_priority") or "").lower()
    priority_score = {
        "critical": 1.0,
        "high": 0.8,
        "medium": 0.55,
        "low": 0.35,
    }.get(priority, 0.45)
    freshness_score = {
        "fresh": 1.0,
        "seed_prior": 0.55,
        "stale": 0.45,
        "unavailable": 0.15,
    }.get(freshness_status.lower(), 0.5)
    alert_penalty = _alert_weight(latest_alert_severity)
    anomaly_bonus = min(_coerce_float(latest_anomaly_score), 1.0)
    return round(max(0.0, min(1.0, 0.45 * priority_score + 0.25 * freshness_score + 0.2 * anomaly_bonus + 0.1 * (1.0 - alert_penalty))), 3)


def _derive_difficulty_label(source_match_grade: object, freshness_status: str, can_execute: bool) -> str:
    grade = str(source_match_grade or "").lower()
    if freshness_status.lower() in {"unavailable", "stale"} and not can_execute:
        return "hard"
    if grade in {"exact_station", "official"}:
        return "easy"
    if grade in {"family_exact", "official_proxy"}:
        return "medium"
    return "hard"


def _derive_source_precision_score(source_match_grade: object) -> float:
    grade = str(source_match_grade or "").lower()
    return {
        "exact_station": 1.0,
        "family_exact": 0.75,
        "family_only": 0.5,
        "unmatched": 0.0,
    }.get(grade, 0.5)


def _derive_recommended_action(
    latest_alert_severity: str,
    latest_anomaly_score: float | None,
    freshness_status: str,
    can_execute: bool,
) -> str:
    if not can_execute or freshness_status.lower() in {"stale", "unavailable"}:
        return "review_monitoring"
    if latest_alert_severity.lower() in {"red", "critical"}:
        return "open_workstation"
    if _coerce_float(latest_anomaly_score) >= 0.5:
        return "watch"
    return "prioritize_review"


def _derive_primary_state(
    *,
    latest_alert_severity: str,
    latest_anomaly_score: float | None,
    freshness_status: str,
    can_execute: bool,
    primary_block_reason: str,
    selected_market: bool,
) -> tuple[str, list[str], str]:
    secondary_states: list[str] = []
    reason_parts: list[str] = []
    alert_severity = str(latest_alert_severity or "").lower()
    freshness = str(freshness_status or "").lower()
    anomaly_value = _coerce_float(latest_anomaly_score)
    primary_state = "LIVE"

    if freshness in {"stale", "unavailable"}:
        secondary_states.append("STALE")
        reason_parts.append(f"freshness={freshness}")
    if alert_severity in {"red", "critical"}:
        secondary_states.append("ALERT")
    elif alert_severity in {"amber", "high"}:
        secondary_states.append("ALERT")
    if anomaly_value >= 0.5:
        secondary_states.append("ANOM")
    if not can_execute and str(primary_block_reason or "-") not in {"", "-"}:
        secondary_states.append("BLOCKED")
        reason_parts.append(f"block={primary_block_reason}")
    if selected_market:
        reason_parts.append("selected")

    if not can_execute and str(primary_block_reason or "-") not in {"", "-"}:
        primary_state = "BLOCKED"
    elif alert_severity in {"red", "critical"}:
        primary_state = "ALERT"
        reason_parts.append(f"alert={alert_severity}")
    elif anomaly_value >= 0.5:
        primary_state = "ANOM"
        reason_parts.append(f"anomaly={anomaly_value:.2f}")
    elif freshness in {"stale", "unavailable"}:
        primary_state = "STALE"
    else:
        primary_state = "LIVE"

    if selected_market and primary_state == "LIVE" and secondary_states:
        reason_parts.append("focus")
    return primary_state, list(dict.fromkeys(secondary_states)), ", ".join(dict.fromkeys(reason_parts)) or "-"


def _state_weight(state: str) -> float:
    state = str(state or "").upper()
    return {
        "BLOCKED": 1.0,
        "ALERT": 0.92,
        "ANOM": 0.78,
        "STALE": 0.55,
        "LIVE": 0.2,
    }.get(state, 0.0)


def _derive_display_priority(
    *,
    opportunity_score: float | object,
    latest_alert_severity: str,
    latest_anomaly_score: float | None,
    freshness_status: str,
    can_execute: bool,
    selected_market: bool,
) -> float:
    score = max(0.0, min(1.0, _coerce_float(opportunity_score)))
    alert_weight = _alert_weight(latest_alert_severity)
    anomaly_value = min(1.0, _coerce_float(latest_anomaly_score))
    freshness_bonus = {
        "fresh": 0.15,
        "seed_prior": 0.08,
        "stale": -0.05,
        "unavailable": -0.12,
    }.get(str(freshness_status or "").lower(), 0.0)
    gate_bonus = 0.06 if not can_execute else 0.0
    selected_bonus = 0.12 if selected_market else 0.0
    return round(100.0 * max(0.0, min(1.0, score * 0.55 + alert_weight * 0.2 + anomaly_value * 0.12 + freshness_bonus + gate_bonus + selected_bonus)), 1)


def _summarize_top_parameter_view(top_parameter_view: dict[str, Any]) -> dict[str, Any]:
    weather = top_parameter_view.get("weather") if isinstance(top_parameter_view.get("weather"), dict) else {}
    forecast = top_parameter_view.get("forecast") if isinstance(top_parameter_view.get("forecast"), dict) else {}
    gate = top_parameter_view.get("decision") if isinstance(top_parameter_view.get("decision"), dict) else {}
    source_contract = top_parameter_view.get("source_contract") if isinstance(top_parameter_view.get("source_contract"), dict) else {}
    return {
        "market_question": top_parameter_view.get("market_question") or "-",
        "market_family": top_parameter_view.get("market_family") or "-",
        "location_name": top_parameter_view.get("location_name") or "-",
        "target_date": top_parameter_view.get("target_date") or "-",
        "display_value": weather.get("display_value") or "-",
        "display_unit": weather.get("display_unit") or "-",
        "model_band": forecast.get("model_band") or "-",
        "observation_band": weather.get("observation_band") or "-",
        "source_match_grade": source_contract.get("source_match_grade") or "-",
        "freshness_status": source_contract.get("freshness_status") or "-",
        "can_execute": gate.get("can_execute"),
        "primary_block_reason": gate.get("primary_block_reason") or "-",
        "primary_state": _primary_state_from_top_parameter(gate, source_contract, weather, forecast),
    }


def _primary_state_from_top_parameter(
    gate: dict[str, Any],
    source_contract: dict[str, Any],
    weather: dict[str, Any],
    forecast: dict[str, Any],
) -> str:
    freshness = str(source_contract.get("freshness_status") or "").lower()
    can_execute = _coerce_bool(gate.get("can_execute"))
    block_reason = str(gate.get("primary_block_reason") or "-")
    alert_like = str(weather.get("alert_severity") or forecast.get("alert_severity") or "").lower()
    anomaly_like = _coerce_float(weather.get("anomaly_score") or forecast.get("anomaly_score"))
    if not can_execute and block_reason not in {"", "-"}:
        return "BLOCKED"
    if alert_like in {"red", "critical"}:
        return "ALERT"
    if anomaly_like >= 0.5:
        return "ANOM"
    if freshness in {"stale", "unavailable"}:
        return "STALE"
    return "LIVE"


def _first_problem_reason(problem_sources: list[dict[str, Any]]) -> str:
    for source in problem_sources:
        reason = source.get("status_reason") if isinstance(source, dict) else None
        if isinstance(reason, str) and reason.strip():
            return reason.strip()
    return "-"


def _first_ops_alert_reason(ops_alerts: list[dict[str, Any]]) -> str:
    for alert in ops_alerts:
        reason = alert.get("primary_reason") if isinstance(alert, dict) else None
        if isinstance(reason, str) and reason.strip():
            return reason.strip()
    return "-"


def _derive_monitor_action(global_summary: dict[str, Any], system_health: dict[str, Any]) -> str:
    scanner = system_health.get("scanner_health") or {}
    source = system_health.get("source_health") or {}
    if _coerce_int(scanner.get("unavailable_markets")) > 0 or str(source.get("overall_status") or "").lower() == "blocked":
        return "review_source_health"
    if _coerce_int(global_summary.get("high_alert_markets")) > 0:
        return "review_alert_markets"
    if _coerce_int(global_summary.get("high_anomaly_markets")) > 0:
        return "review_anomaly_markets"
    return "monitor_and_wait"
