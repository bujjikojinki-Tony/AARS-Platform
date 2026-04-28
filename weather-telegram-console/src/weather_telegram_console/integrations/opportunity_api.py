from __future__ import annotations

import json
from pathlib import Path

from weather_telegram_console.settings import get_advanced_anomaly_output_dir
from weather_telegram_console.settings import get_family_scan_reports_dir
from weather_telegram_console.settings import get_opportunity_board_city_dir_path
from weather_telegram_console.settings import get_opportunity_board_view_path
from weather_telegram_console.settings import get_validation_output_dir


class OpportunityAPI:
    def load_opportunity_board(self, city: str | None = None) -> dict:
        payload = self._load_json(get_opportunity_board_view_path())
        if not isinstance(payload, dict):
            raise FileNotFoundError("No opportunity board found yet.")

        latest_family_scan_report = self._load_latest_family_scan_report()
        phase30_artifacts = self._load_phase30_artifacts()
        phase30_family_summary = phase30_artifacts.get("family_anomaly_summary") or {}
        if latest_family_scan_report or phase30_family_summary:
            payload["latest_family_scan_report"] = latest_family_scan_report
            payload["family_anomaly_summary"] = (
                _family_scan_summary(phase30_family_summary)
                if phase30_family_summary
                else _family_scan_summary(latest_family_scan_report)
            )
            payload["validation_summary_v1"] = phase30_artifacts.get("validation_summary_v1") or {}

        rows = payload.get("rows") or []
        if not isinstance(rows, list):
            rows = []

        normalized_city = str(city or "").strip().lower()
        if normalized_city:
            city_payload = self._load_city_payload(city)
            if city_payload:
                city_payload.setdefault("selected_city", city)
                if latest_family_scan_report or phase30_family_summary:
                    city_payload.setdefault("latest_family_scan_report", latest_family_scan_report)
                    city_payload.setdefault(
                        "family_anomaly_summary",
                        _family_scan_summary(phase30_family_summary)
                        if phase30_family_summary
                        else _family_scan_summary(latest_family_scan_report),
                    )
                    city_payload.setdefault(
                        "validation_summary_v1",
                        phase30_artifacts.get("validation_summary_v1") or {},
                    )
                return city_payload
            filtered = [
                row
                for row in rows
                if isinstance(row, dict) and str(row.get("city") or "").strip().lower() == normalized_city
            ]
            if not filtered:
                raise FileNotFoundError(f"No opportunity rows found for city `{city}`.")
            payload = {
                **payload,
                "selected_city": city,
                "rows": filtered,
                "row_count": len(filtered),
            }
            if latest_family_scan_report or phase30_family_summary:
                payload["latest_family_scan_report"] = latest_family_scan_report
                payload["family_anomaly_summary"] = (
                    _family_scan_summary(phase30_family_summary)
                    if phase30_family_summary
                    else _family_scan_summary(latest_family_scan_report)
                )
                payload["validation_summary_v1"] = phase30_artifacts.get("validation_summary_v1") or {}

        return payload

    def _load_city_payload(self, city: str | None) -> dict:
        city_text = str(city or "").strip()
        if not city_text:
            return {}
        city_dir = get_opportunity_board_city_dir_path()
        candidate = city_dir / f"city_opportunity_{self._slugify(city_text)}.json"
        return self._load_json(candidate)

    def _load_json(self, path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return payload if isinstance(payload, dict) else {}

    def _load_latest_family_scan_report(self) -> dict:
        directory = get_family_scan_reports_dir()
        if not directory.exists():
            return {}
        candidates = sorted(directory.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
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
        return {
            "validation_summary_v1": self._load_latest_json_matching(validation_dir, "validation_summary_*.json"),
            "family_anomaly_summary": self._load_latest_json_matching(anomaly_dir, "family_anomaly_summary_*.json"),
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

    def _slugify(self, value: str) -> str:
        slug = value.strip().lower().replace(" ", "_").replace("/", "_")
        slug = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in slug)
        while "__" in slug:
            slug = slug.replace("__", "_")
        return slug or "unknown"


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
