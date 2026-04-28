from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from weather_telegram_console.settings import (
    get_advanced_anomaly_output_dir,
    get_comparison_history_path,
    get_family_scan_reports_dir,
    get_gate_stack_api_path,
    get_label_coverage_report_path,
    get_latest_dashboard_rows_path,
    get_manual_advisory_audit_path,
    get_market_alert_events_dir,
    get_market_anomaly_events_dir,
    get_model_validation_report_path,
    get_operator_market_context_path,
    get_opportunity_board_view_path,
    get_unified_status_path,
    get_validation_freshness_status_path,
    get_validation_output_dir,
)
from weather_telegram_console.integrations.gate_stack_consumer import consume_gate_stack_payload
from weather_telegram_console.integrations.top_parameter_view import build_top_parameter_view
from weather_telegram_console.operator_messages import (
    NO_COMPARISON_HISTORY,
    NO_COMPARISON_HISTORY_FOR_SELECTED_MARKET,
    NO_CURRENT_MARKET,
    NO_LATEST_MARKET_SUMMARY,
    SELECTED_MARKET_NOT_IN_SUMMARY,
)


class MarketAPI:
    def load_market_summary(self, market_id: str | None = None) -> dict:
        rows = self._load_json(get_latest_dashboard_rows_path())
        if not isinstance(rows, list) or not rows:
            raise FileNotFoundError(NO_LATEST_MARKET_SUMMARY)

        target_market_id = (market_id or self._get_current_market_id() or "").strip()
        if target_market_id:
            for row in rows:
                if isinstance(row, dict) and str(row.get("market_id") or "") == target_market_id:
                    return self._build_market_summary(row)
            raise FileNotFoundError(f"{SELECTED_MARKET_NOT_IN_SUMMARY} market_id=`{target_market_id}`")

        for row in rows:
            if isinstance(row, dict):
                return self._build_market_summary(row)

        raise FileNotFoundError(NO_LATEST_MARKET_SUMMARY)

    def load_market_timeline(self, market_id: str | None = None, limit: int = 8) -> list[dict]:
        history = self._load_json(get_comparison_history_path())
        if not isinstance(history, list) or not history:
            raise FileNotFoundError(NO_COMPARISON_HISTORY)

        target_market_id = (market_id or self._get_current_market_id() or "").strip()
        if not target_market_id:
            raise FileNotFoundError(NO_CURRENT_MARKET)

        filtered = [
            row
            for row in history
            if isinstance(row, dict) and str(row.get("market_id") or "") == target_market_id
        ]
        if not filtered:
            raise FileNotFoundError(
                f"{NO_COMPARISON_HISTORY_FOR_SELECTED_MARKET} market_id=`{target_market_id}`"
            )

        filtered.sort(key=lambda row: str(row.get("timestamp") or ""), reverse=True)
        return filtered[:limit]

    def _build_market_summary(self, row: dict) -> dict:
        market_id = str(row.get("market_id") or "").strip()
        advisory_events = self._load_manual_advisory_events(market_id)
        gate_stack_api = self._load_json(get_gate_stack_api_path())
        unified_status = self._load_json(get_unified_status_path())
        compact_gate_stack = self._build_compact_gate_stack(
            row,
            gate_stack_api=gate_stack_api,
            unified_status=unified_status,
        )
        data_availability = {
            "market_snapshot_ref_present": bool(row.get("market_snapshot_ref")),
            "forecast_snapshot_ref_present": bool(row.get("forecast_snapshot_ref")),
            "manual_advisory_events_present": bool(advisory_events),
            "manual_advisory_audit_available": get_manual_advisory_audit_path().exists(),
        }
        workstation_context = self._build_workstation_context(
            market_id=market_id,
            row=row,
            compact_gate_stack=compact_gate_stack,
        )
        latest_family_scan_report = self._load_latest_family_scan_report()
        phase30_artifacts = self._load_phase30_artifacts()
        phase30_family_summary = phase30_artifacts.get("family_anomaly_summary") or {}
        family_anomaly_summary = (
            _family_scan_summary(phase30_family_summary)
            if phase30_family_summary
            else (_family_scan_summary(latest_family_scan_report) if latest_family_scan_report else {})
        )
        if latest_family_scan_report or phase30_artifacts.get("family_anomaly_summary"):
            workstation_context["family_anomaly_summary"] = family_anomaly_summary
        if phase30_artifacts.get("validation_summary_v1"):
            workstation_context["validation_summary_v1"] = phase30_artifacts.get("validation_summary_v1") or {}
        return {
            **row,
            "compact_gate_stack": compact_gate_stack,
            "promotion_state": compact_gate_stack.get("promotion_state") or _extract_promotion_state(
                gate_stack_api,
                unified_status,
                row,
            ),
            "top_parameter_view": build_top_parameter_view(
                current_market=row,
                probability=row,
                gate_stack=compact_gate_stack,
                resolver=row,
                weather=row,
            ),
            "advisory_summary": self._build_advisory_summary(advisory_events),
            "data_availability": data_availability,
            "workstation_context": workstation_context,
            "family_anomaly_summary": family_anomaly_summary,
            "validation_summary_v1": phase30_artifacts.get("validation_summary_v1") or {},
        }

    def _build_workstation_context(
        self,
        *,
        market_id: str,
        row: dict,
        compact_gate_stack: dict,
    ) -> dict:
        validation = self._build_validation_summary()
        phase30 = self._load_phase30_artifacts()
        opportunity = self._find_opportunity_row(market_id, row)
        return {
            "schema_version": "telegram_market_workstation_context.v1",
            "market_alert": self._load_latest_market_alert(market_id),
            "family_anomaly": self._load_latest_market_anomaly(market_id),
            "gate_summary": {
                "resolver_gate": compact_gate_stack.get("resolver_gate"),
                "probability_gate": compact_gate_stack.get("probability_gate"),
                "freshness_gate": compact_gate_stack.get("freshness_gate"),
                "authorization_gate": compact_gate_stack.get("authorization_gate"),
                "execution_gate": compact_gate_stack.get("execution_gate"),
                "primary_block_reason": _first_item(compact_gate_stack.get("block_reasons"))
                or _first_item(compact_gate_stack.get("resolver_gate_reasons")),
                "recommended_operator_action": compact_gate_stack.get("recommended_operator_action"),
                "source": compact_gate_stack.get("source"),
                "execution_boundary": "gate_stack_api.v1_only",
            },
            "validation_summary": {
                **validation,
                "validation_summary_v1": phase30.get("validation_summary_v1") or {},
                "coverage_summary_v1": phase30.get("coverage_summary_v1") or {},
                "promotion_support_v1": phase30.get("promotion_support_v1") or {},
                "model_validation_compare_v1": phase30.get("model_validation_compare_v1") or {},
            },
            "opportunity_entry": _summarize_opportunity_row(opportunity),
        }

    def _build_compact_gate_stack(
        self,
        row: dict,
        *,
        gate_stack_api: dict | None = None,
        unified_status: dict | None = None,
    ) -> dict:
        market_id = str(row.get("market_id") or "").strip()
        if isinstance(gate_stack_api, dict) and str(gate_stack_api.get("schema_version") or "") == "gate_stack_api.v1":
            consumer = consume_gate_stack_payload(gate_stack_api, market_id=market_id)
            source_payload = consumer.market_view if isinstance(getattr(consumer, "market_view", None), dict) else consumer.payload
            gate_stack = source_payload.get("gate_stack") if isinstance(source_payload.get("gate_stack"), dict) else source_payload
            if isinstance(gate_stack, dict):
                promotion_state = _extract_promotion_state(source_payload, gate_stack_api, unified_status, row)
                return {
                    "resolver_gate": str(gate_stack.get("resolver_gate") or "pass"),
                    "resolver_gate_reasons": [
                        str(item) for item in gate_stack.get("resolver_gate_reasons") or []
                    ],
                    "probability_gate": str(gate_stack.get("probability_gate") or "-"),
                    "freshness_gate": str(gate_stack.get("freshness_gate") or "-"),
                    "authorization_gate": str(gate_stack.get("authorization_gate") or "-"),
                    "execution_gate": str(gate_stack.get("execution_gate") or "-"),
                    "block_reasons": [str(item) for item in gate_stack.get("block_reasons") or []],
                    "severity": str(source_payload.get("severity") or gate_stack_api.get("severity") or "medium"),
                    "recommended_operator_action": str(
                        source_payload.get("recommended_operator_action")
                        or gate_stack_api.get("recommended_operator_action")
                        or "hold_execution_and_review"
                    ),
                    "source": consumer.gate_source,
                    "promotion_state": promotion_state,
                    "promotion_reason": promotion_state.get("promotion_reason"),
                    "demotion_reason": promotion_state.get("demotion_reason"),
                }

        if isinstance(unified_status, dict):
            current_market = unified_status.get("current_market") or {}
            current_market_id = str(current_market.get("market_id") or "").strip()
            gate_stack = unified_status.get("gate_stack")
            if market_id and market_id == current_market_id and isinstance(gate_stack, dict):
                promotion_state = _extract_promotion_state(unified_status, row)
                return {
                    "resolver_gate": str(gate_stack.get("resolver_gate") or "pass"),
                    "resolver_gate_reasons": [
                        str(item) for item in gate_stack.get("resolver_gate_reasons") or []
                    ],
                    "probability_gate": str(gate_stack.get("probability_gate") or "-"),
                    "freshness_gate": str(gate_stack.get("freshness_gate") or "-"),
                    "authorization_gate": str(gate_stack.get("authorization_gate") or "-"),
                    "execution_gate": str(gate_stack.get("execution_gate") or "-"),
                    "block_reasons": [str(item) for item in gate_stack.get("block_reasons") or []],
                    "source": "unified_fallback",
                    "promotion_state": promotion_state,
                    "promotion_reason": promotion_state.get("promotion_reason"),
                    "demotion_reason": promotion_state.get("demotion_reason"),
                }

        resolver_status = str(row.get("resolver_status") or row.get("rule_status") or "")
        resolver_confidence = float(row.get("resolver_confidence") or 0.0)
        source_match_grade = str(row.get("source_match_grade") or "")
        reasons: list[str] = []
        if resolver_status.strip().lower() != "matched":
            reasons.append("resolver_not_matched")
        if resolver_confidence < 0.7:
            reasons.append("resolver_confidence_low")
        if source_match_grade.strip().lower() in {"", "unmatched", "family_only"}:
            reasons.append("resolver_source_not_exact")
        return {
            "resolver_gate": "blocked" if reasons else "pass",
            "authorization_gate": "blocked" if reasons else "pass",
            "resolver_gate_reasons": reasons,
            "source": "local_fallback",
            "promotion_state": _extract_promotion_state(row),
            "promotion_reason": _extract_promotion_state(row).get("promotion_reason"),
            "demotion_reason": _extract_promotion_state(row).get("demotion_reason"),
        }

    def _get_current_market_id(self) -> str | None:
        operator_context = self._load_json(get_operator_market_context_path())
        if isinstance(operator_context, dict):
            market_id = str(operator_context.get("market_id") or "").strip()
            if market_id:
                return market_id

        report = self._load_json(get_unified_status_path())
        if not isinstance(report, dict):
            return None
        current_market = report.get("current_market") or {}
        return str(current_market.get("market_id") or "").strip() or None

    def _load_manual_advisory_events(self, market_id: str) -> list[dict]:
        path = get_manual_advisory_audit_path()
        if not market_id or not path.exists():
            return []

        events: list[dict] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            if str(payload.get("market_id") or "") != market_id:
                continue
            events.append(payload)
        events.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        return events

    def _build_advisory_summary(self, events: list[dict]) -> dict:
        latest = events[0] if events else {}
        payload = latest.get("payload") or {}
        manual_trade_ticket = payload.get("manual_trade_ticket") or {}
        return {
            "event_count": len(events),
            "latest_event_type": latest.get("event_type"),
            "latest_created_at": latest.get("created_at"),
            "latest_decision": payload.get("decision") or payload.get("approval_status"),
            "latest_gate_status": payload.get("gate_status"),
            "latest_price": manual_trade_ticket.get("price"),
            "latest_size": manual_trade_ticket.get("size"),
        }

    def _build_validation_summary(self) -> dict:
        validation = self._load_json(get_model_validation_report_path())
        freshness = self._load_json(get_validation_freshness_status_path())
        coverage = self._load_json(get_label_coverage_report_path())
        phase30 = self._load_phase30_artifacts()
        metrics = validation.get("validation_metrics") if isinstance(validation, dict) else {}
        metrics = metrics if isinstance(metrics, dict) else {}
        promotion = validation.get("promotion_state") if isinstance(validation, dict) else {}
        promotion = promotion if isinstance(promotion, dict) else {}
        return {
            "schema_version": "telegram_validation_summary.v1",
            "promotion_state": promotion.get("probability_mode")
            or validation.get("probability_mode")
            or "-",
            "promotion_reason": promotion.get("promotion_reason")
            or validation.get("promotion_reason")
            or "-",
            "demotion_reason": promotion.get("demotion_reason")
            or validation.get("demotion_reason")
            or "-",
            "freshness_status": freshness.get("status") if isinstance(freshness, dict) else "-",
            "freshness_reason": freshness.get("reason") if isinstance(freshness, dict) else "-",
            "coverage_status": coverage.get("status") if isinstance(coverage, dict) else "-",
            "labeled_ratio": coverage.get("labeled_ratio") if isinstance(coverage, dict) else "-",
            "sample_count": validation.get("sample_count") if isinstance(validation, dict) else "-",
            "labeled_sample_count": validation.get("labeled_sample_count") if isinstance(validation, dict) else "-",
            "calibration_status": validation.get("calibration_status") if isinstance(validation, dict) else "-",
            "brier_score": metrics.get("brier_score"),
            "calibration_error": metrics.get("calibration_error"),
            "validation_summary_v1": phase30.get("validation_summary_v1") or {},
            "coverage_summary_v1": phase30.get("coverage_summary_v1") or {},
            "promotion_support_v1": phase30.get("promotion_support_v1") or {},
            "model_validation_compare_v1": phase30.get("model_validation_compare_v1") or {},
        }

    def _find_opportunity_row(self, market_id: str, row: dict) -> dict:
        board = self._load_json(get_opportunity_board_view_path())
        rows = board.get("rows") if isinstance(board, dict) else []
        if not isinstance(rows, list):
            return {}
        market_id_text = str(market_id or "").strip()
        for item in rows:
            if not isinstance(item, dict):
                continue
            market_ids = (item.get("upstream_refs") or {}).get("market_ids") or []
            if market_id_text and market_id_text in {str(value) for value in market_ids}:
                return item
        city = str(row.get("city") or row.get("location_name") or "").strip().lower()
        family = str(row.get("market_family") or "").strip().lower()
        if not city or not family:
            return {}
        for item in rows:
            if not isinstance(item, dict):
                continue
            if (
                str(item.get("city") or "").strip().lower() == city
                and str(item.get("market_family") or "").strip().lower() == family
            ):
                return item
        return {}

    def _load_latest_market_alert(self, market_id: str) -> dict:
        return _load_latest_json_for_market(get_market_alert_events_dir(), market_id)

    def _load_latest_market_anomaly(self, market_id: str) -> dict:
        return _load_latest_jsonl_for_market(get_market_anomaly_events_dir(), market_id)

    def _load_latest_family_scan_report(self) -> dict:
        directory = get_family_scan_reports_dir()
        if not directory.exists():
            return {}
        candidates = sorted(directory.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
        if not candidates:
            return {}
        try:
            payload = json.loads(candidates[0].read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _load_phase30_artifacts(self) -> dict:
        validation_dir = get_validation_output_dir()
        anomaly_dir = get_advanced_anomaly_output_dir()
        validation_summary = self._load_latest_json_matching(validation_dir, "validation_summary_*.json")
        coverage_summary = self._load_latest_json_matching(validation_dir, "coverage_summary_*.json")
        promotion_support = self._load_latest_json_matching(validation_dir, "promotion_support_*.json")
        model_compare = self._load_latest_json_matching(validation_dir, "model_validation_compare_*.json")
        family_anomaly_summary = self._load_latest_json_matching(anomaly_dir, "family_anomaly_summary_*.json")
        return {
            "validation_summary_v1": validation_summary,
            "coverage_summary_v1": coverage_summary,
            "promotion_support_v1": promotion_support,
            "model_validation_compare_v1": model_compare,
            "family_anomaly_summary": family_anomaly_summary or {},
        }

    def _load_latest_json_matching(self, directory: Path, pattern: str) -> dict:
        if not directory.exists():
            return {}
        candidates = sorted(directory.glob(pattern), key=lambda item: item.stat().st_mtime, reverse=True)
        if not candidates:
            return {}
        try:
            payload = json.loads(candidates[0].read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _load_json(self, path: Path) -> Any:
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None


def _extract_promotion_state(*payloads: dict | None) -> dict:
    for payload in payloads:
        if not isinstance(payload, dict):
            continue
        candidate = payload.get("promotion_state")
        if isinstance(candidate, dict):
            return candidate
        probability = payload.get("probability")
        if isinstance(probability, dict):
            candidate = probability.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
        validation = payload.get("validation")
        if isinstance(validation, dict):
            candidate = validation.get("promotion_state")
            if isinstance(candidate, dict):
                return candidate
    return {}


def _summarize_opportunity_row(row: dict) -> dict:
    row = row if isinstance(row, dict) else {}
    refs = row.get("upstream_refs") if isinstance(row.get("upstream_refs"), dict) else {}
    return {
        "schema_version": "telegram_opportunity_entry.v1",
        "row_id": row.get("row_id") or "-",
        "opportunity_score": row.get("opportunity_score"),
        "difficulty_score": row.get("difficulty_score"),
        "difficulty_label": row.get("difficulty_label") or "-",
        "recommended_action": row.get("recommended_action") or "-",
        "best_model": row.get("best_model") or "-",
        "best_source_stack": row.get("best_source_stack") or [],
        "opportunity_reason": row.get("opportunity_reason") or "-",
        "market_refs": refs.get("market_ids") or [],
        "alert_refs": refs.get("alert_refs") or [],
        "anomaly_refs": refs.get("anomaly_refs") or [],
    }


def _family_scan_summary(report: dict) -> dict:
    if str(report.get("schema_version") or "").strip() == "family_anomaly_summary.v1":
        return {
            "schema_version": "family_anomaly_summary.v1",
            "family_scan_status": str(report.get("schema_version") or "-"),
            "top_family": str(report.get("market_family") or "-"),
            "top_score": report.get("high_intervention_like_count") or "-",
            "top_bucket": _bucket_for_score(report.get("high_intervention_like_count")),
            "signal_summary": str(report.get("family_risk_summary") or report.get("primary_reason") or "-"),
            "bucket_counts": report.get("anomaly_bucket_counts") or {},
            "generated_at": report.get("generated_at") or "-",
        }
    family_summaries = [item for item in (report.get("family_summaries") or []) if isinstance(item, dict)]
    ranked = sorted(
        family_summaries,
        key=lambda item: float(item.get("max_intervention_like_score") or 0.0),
        reverse=True,
    )
    top_family = ranked[0] if ranked else {}
    signal_summary = report.get("signal_summary") or {}
    return {
        "schema_version": "family_anomaly_summary.v1",
        "family_scan_status": str(report.get("input_mode") or report.get("schema_version") or "-"),
        "top_family": str(top_family.get("market_family") or "-"),
        "top_score": top_family.get("max_intervention_like_score") or "-",
        "top_bucket": _bucket_for_score(top_family.get("max_intervention_like_score")),
        "signal_summary": (
            f"pv={signal_summary.get('price_velocity_high_count', 0)} "
            f"edge={signal_summary.get('edge_dislocation_high_count', 0)} "
            f"mismatch={signal_summary.get('evidence_mismatch_count', 0)} "
            f"stress={signal_summary.get('microstructure_stress_high_count', 0)} "
            f"peer={signal_summary.get('peer_outlier_count', 0)} "
            f"high={signal_summary.get('intervention_like_high_count', 0)}"
        ),
        "bucket_counts": report.get("anomaly_bucket_counts") or {},
        "generated_at": report.get("generated_at") or "-",
    }


def _bucket_for_score(score: object) -> str:
    try:
        value = float(score or 0.0)
    except (TypeError, ValueError):
        value = 0.0
    if value >= 0.8:
        return "high"
    if value >= 0.5:
        return "medium"
    return "low"


def _load_latest_json_for_market(directory: Path, market_id: str) -> dict:
    if not directory.exists():
        return {}
    market_id_text = str(market_id or "").strip()
    for path in sorted(directory.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        if not market_id_text or str(payload.get("market_id") or "") == market_id_text:
            return payload
    return {}


def _load_latest_jsonl_for_market(directory: Path, market_id: str) -> dict:
    if not directory.exists():
        return {}
    market_id_text = str(market_id or "").strip()
    for path in sorted(directory.glob("*.jsonl"), key=lambda item: item.stat().st_mtime, reverse=True):
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
            if not market_id_text or str(payload.get("market_id") or "") == market_id_text:
                return payload
    return {}


def _first_item(value: object) -> object:
    if isinstance(value, list) and value:
        return value[0]
    return None
