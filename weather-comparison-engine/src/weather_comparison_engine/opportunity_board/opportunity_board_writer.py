from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from weather_comparison_engine.opportunity_board.feature_loader import load_opportunity_feature_context
from weather_comparison_engine.opportunity_board.opportunity_explanation_builder import build_opportunity_explanation
from weather_comparison_engine.opportunity_board.opportunity_row_builder import build_opportunity_row
from weather_comparison_engine.governance.page_context import normalize_page_context


def build_opportunity_board_view(
    *,
    latest_dashboard_rows: list[dict],
    context: dict | None = None,
    page_context: dict | None = None,
    now: datetime | None = None,
) -> dict:
    context = context or {}
    now = now or datetime.now(timezone.utc)
    page_context = normalize_page_context(
        page_context,
        source_page=str((page_context or {}).get("source_page") or "opportunity_board"),
        target_page=str((page_context or {}).get("target_page") or "opportunity_board"),
        selected_market_id=str((page_context or {}).get("selected_market_id") or ""),
        selected_row_id=str((page_context or {}).get("selected_row_id") or ""),
        entry_reason=str((page_context or {}).get("entry_reason") or "research_entry"),
        entry_context=(page_context or {}).get("entry_context") if isinstance(page_context, dict) else {},
        upstream_refs={
            "board_ref": str(
                ((page_context or {}).get("upstream_refs") or {}).get("board_ref") or "-"
            ),
        },
        now=now,
    )
    opportunity_rows = _with_seed_rows(latest_dashboard_rows, context.get("opportunity_seed_list") or {})
    grouped = _group_rows(opportunity_rows)
    board_rows: list[dict] = []

    for (city, market_family), rows in grouped.items():
        board_rows.append(
            build_opportunity_row(
                city=city,
                market_family=market_family,
                rows=rows,
                context={
                    **context,
                    "market_question": rows[0].get("market_question") if rows else None,
                },
            )
        )

    board_rows.sort(
        key=lambda item: (
            -float(item.get("opportunity_score") or 0.0),
            float(item.get("difficulty_score") or 0.0),
            _freshness_sort_key(str(item.get("freshness_status") or "")),
            -float(item.get("source_precision_score") or 0.0),
            str(item.get("city") or ""),
            str(item.get("market_family") or ""),
        )
    )

    for index, row in enumerate(board_rows, start=1):
        row["opportunity_rank"] = index

    summary = _build_board_summary(board_rows)
    explanations = {row["row_id"]: build_opportunity_explanation(row) for row in board_rows}
    return {
        "schema_version": "opportunity_board_view.v1",
        "generated_at": now.isoformat(),
        "page_context": page_context,
        "row_count": len(board_rows),
        "summary": summary,
        "rows": board_rows,
        "explanations": explanations,
        "seed_summary": _build_seed_summary(board_rows),
        "feature_rows": [_feature_row(row) for row in board_rows],
    }


def write_opportunity_board_view(path: str | Path, payload: dict) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def write_opportunity_board_artifacts(
    *,
    board_path: str | Path,
    explanation_path: str | Path,
    feature_rows_path: str | Path,
    city_dir: str | Path,
    payload: dict,
    summary_path: str | Path | None = None,
    canonical_board_path: str | Path | None = None,
    canonical_explanation_path: str | Path | None = None,
    canonical_feature_rows_path: str | Path | None = None,
) -> dict[str, Path]:
    board_out = write_opportunity_board_view(board_path, payload)
    explanation_out = Path(explanation_path)
    explanation_out.parent.mkdir(parents=True, exist_ok=True)
    explanation_out.write_text(
        json.dumps(payload.get("explanations") or {}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    feature_rows_out = Path(feature_rows_path)
    feature_rows_out.parent.mkdir(parents=True, exist_ok=True)
    feature_rows_out.write_text(
        json.dumps(payload.get("feature_rows") or [], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    summary_out: Path | None = None
    if summary_path is not None:
        summary_out = Path(summary_path)
        summary_out.parent.mkdir(parents=True, exist_ok=True)
        summary_out.write_text(
            json.dumps(_summary_artifact(payload), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    canonical_board_out = _write_optional_artifact(canonical_board_path, payload)
    canonical_explanation_out = _write_optional_artifact(
        canonical_explanation_path,
        payload.get("explanations") or {},
    )
    canonical_feature_rows_out = _write_optional_artifact(
        canonical_feature_rows_path,
        payload.get("feature_rows") or [],
    )

    city_dir = Path(city_dir)
    city_dir.mkdir(parents=True, exist_ok=True)
    city_files: dict[str, Path] = {}
    city_groups: dict[str, list[dict]] = {}
    for row in payload.get("rows") or []:
        city = str(row.get("city") or "unknown").strip() or "unknown"
        city_groups.setdefault(city, []).append(row)
    for city, rows in city_groups.items():
        city_path = city_dir / f"city_opportunity_{_slugify(city)}.json"
        city_payload = {
            "schema_version": "city_opportunity.v1",
            "generated_at": payload.get("generated_at"),
            "city": city,
            "row_count": len(rows),
            "rows": rows,
        }
        city_path.write_text(json.dumps(city_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        city_files[city] = city_path
    outputs = {
        "board": board_out,
        "explanations": explanation_out,
        "feature_rows": feature_rows_out,
        "city_dir": city_dir,
        "city_files": city_files,
    }
    if summary_out is not None:
        outputs["summary"] = summary_out
    if canonical_board_out is not None:
        outputs["canonical_board"] = canonical_board_out
    if canonical_explanation_out is not None:
        outputs["canonical_explanations"] = canonical_explanation_out
    if canonical_feature_rows_out is not None:
        outputs["canonical_feature_rows"] = canonical_feature_rows_out
    return outputs


def build_opportunity_board_from_files(
    *,
    latest_dashboard_rows_path: Path,
    gate_stack_api_path: Path,
    unified_status_path: Path,
    model_validation_report_path: Path | None = None,
    source_policy_status_path: Path | None = None,
    opportunity_seed_list_path: Path | None = None,
    market_alert_events_dir: Path | None = None,
    market_anomaly_events_dir: Path | None = None,
    family_scan_reports_dir: Path | None = None,
    comparison_history_path: Path | None = None,
    page_context: dict | None = None,
    now: datetime | None = None,
) -> dict:
    context = load_opportunity_feature_context(
        latest_dashboard_rows_path=latest_dashboard_rows_path,
        gate_stack_api_path=gate_stack_api_path,
        unified_status_path=unified_status_path,
        model_validation_report_path=model_validation_report_path,
        source_policy_status_path=source_policy_status_path,
        opportunity_seed_list_path=opportunity_seed_list_path,
        market_alert_events_dir=market_alert_events_dir,
        market_anomaly_events_dir=market_anomaly_events_dir,
        family_scan_reports_dir=family_scan_reports_dir,
        comparison_history_path=comparison_history_path,
    )
    return build_opportunity_board_view(
        latest_dashboard_rows=context.get("latest_dashboard_rows") or [],
        context=context,
        page_context=page_context,
        now=now,
    )


def _group_rows(rows: list[dict]) -> dict[tuple[str, str], list[dict]]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        if not isinstance(row, dict):
            continue
        city = _derive_city(row)
        market_family = str(row.get("market_family") or "unknown").strip() or "unknown"
        grouped[(city, market_family)].append(row)
    return grouped


def _with_seed_rows(rows: list[dict], seed_list: dict) -> list[dict]:
    merged = [row for row in rows if isinstance(row, dict)]
    existing_keys = {
        (_derive_city(row).lower(), str(row.get("market_family") or "unknown").strip().lower())
        for row in merged
    }
    for seed in seed_list.get("rows") or []:
        if not isinstance(seed, dict):
            continue
        if str(seed.get("seed_status") or "").lower() != "active":
            continue
        city = str(seed.get("city") or "").strip()
        family = str(seed.get("market_family") or "").strip()
        if not city or not family:
            continue
        key = (city.lower(), family.lower())
        if key in existing_keys:
            continue
        merged.append(_seed_to_dashboard_row(seed))
        existing_keys.add(key)
    return merged


def _seed_to_dashboard_row(seed: dict) -> dict:
    difficulty_label = str(seed.get("initial_difficulty_label") or "medium").lower()
    source_match_grade = {
        "easy": "exact_station",
        "medium": "family_exact",
        "hard": "family_only",
    }.get(difficulty_label, "family_exact")
    resolver_confidence = {
        "easy": 0.78,
        "medium": 0.62,
        "hard": 0.45,
    }.get(difficulty_label, 0.55)
    return {
        "market_id": "",
        "market_question": f"Seeded opportunity for {seed.get('city')} {seed.get('market_family')}",
        "city": seed.get("city"),
        "location_name": seed.get("city"),
        "country": seed.get("country") or "-",
        "market_family": seed.get("market_family"),
        "initial_edge_label": seed.get("initial_edge_label"),
        "initial_difficulty_label": difficulty_label,
        "best_model": seed.get("initial_best_model"),
        "best_source_stack": seed.get("initial_best_source_stack") or [],
        "source_match_grade": source_match_grade,
        "official_vs_proxy_source": "official",
        "resolver_confidence": resolver_confidence,
        "comparison_status": "seed_prior",
        "freshness_status": "seed_prior",
        "seed_id": seed.get("seed_id"),
        "seeded_from_manual_research": True,
        "seed_status": seed.get("seed_status"),
        "source_origin": seed.get("source_origin"),
        "manual_confidence": seed.get("manual_confidence"),
        "seed_notes": seed.get("notes"),
        "superseded_by_system_score": bool(seed.get("superseded_by_system_score")),
    }


def _derive_city(row: dict) -> str:
    location = str(row.get("location_name") or row.get("city") or "").strip()
    if location:
        return location
    question = str(row.get("market_question") or "").strip()
    if not question:
        return "Unknown"
    for marker in (" in ", " for ", " at "):
        if marker not in question.lower():
            continue
        fragment = question.split(marker, 1)[1]
        fragment = fragment.split(" on ", 1)[0]
        fragment = fragment.split(" by ", 1)[0]
        fragment = fragment.split("?", 1)[0]
        fragment = fragment.strip(" .,:;")
        if fragment:
            return fragment[:48]
    return "Unknown"


def _freshness_sort_key(status: str) -> int:
    order = {"fresh": 0, "healthy": 0, "warm": 1, "warning": 1, "seed_prior": 2, "stale": 2, "blocked": 3, "unavailable": 3, "unknown": 2}
    return order.get(status.lower(), 2)


def _build_board_summary(rows: list[dict]) -> dict:
    cities = {str(row.get("city") or "-") for row in rows}
    families = {str(row.get("market_family") or "-") for row in rows}
    freshness_counts: dict[str, int] = {}
    for row in rows:
        freshness = str(row.get("freshness_status") or "unknown").lower()
        freshness_counts[freshness] = freshness_counts.get(freshness, 0) + 1
    top_row = rows[0] if rows else {}
    return {
        "city_count": len(cities),
        "family_count": len(families),
        "freshness_counts": freshness_counts,
        "high_opportunity_count": sum(1 for row in rows if float(row.get("opportunity_score") or 0.0) >= 0.7),
        "easy_count": sum(1 for row in rows if str(row.get("difficulty_label") or "") == "easy"),
        "medium_count": sum(1 for row in rows if str(row.get("difficulty_label") or "") == "medium"),
        "hard_count": sum(1 for row in rows if str(row.get("difficulty_label") or "") == "hard"),
        "top_city": top_row.get("city") or "-",
        "top_family": top_row.get("market_family") or "-",
        "top_model": top_row.get("best_model") or "-",
        "top_action": top_row.get("recommended_action") or "-",
    }


def _build_seed_summary(rows: list[dict]) -> dict:
    seeded_rows = [row for row in rows if row.get("seeded_from_manual_research")]
    return {
        "seeded_row_count": len(seeded_rows),
        "seeded_city_count": len({str(row.get("city") or "-") for row in seeded_rows}),
        "seed_source_type": "manual_seed_from_research_image" if seeded_rows else "-",
        "seed_usage": "cold_start_prior_only",
    }


def _feature_row(row: dict) -> dict:
    return {
        "row_id": row.get("row_id"),
        "city": row.get("city"),
        "market_family": row.get("market_family"),
        "edge_component": (row.get("opportunity_components") or {}).get("edge_component"),
        "market_lag_component": (row.get("opportunity_components") or {}).get("market_lag_component"),
        "source_precision_component": (row.get("opportunity_components") or {}).get("source_precision_component"),
        "freshness_component": (row.get("opportunity_components") or {}).get("freshness_component"),
        "liquidity_component": (row.get("opportunity_components") or {}).get("liquidity_component"),
        "anomaly_penalty_component": (row.get("opportunity_components") or {}).get("anomaly_penalty_component"),
        "difficulty_score": row.get("difficulty_score"),
        "best_model": row.get("best_model"),
        "best_source_stack": row.get("best_source_stack"),
        "seed_id": row.get("seed_id"),
        "seeded_from_manual_research": row.get("seeded_from_manual_research"),
        "opportunity_policy_ref": row.get("opportunity_policy_ref"),
        "scoring_policy_ref": row.get("scoring_policy_ref"),
        "difficulty_policy_ref": row.get("difficulty_policy_ref"),
        "model_recommendation_policy_ref": row.get("model_recommendation_policy_ref"),
        "action_mapping_policy_ref": row.get("action_mapping_policy_ref"),
        "freshness_mapping_policy_ref": row.get("freshness_mapping_policy_ref"),
        "source_precision_policy_ref": row.get("source_precision_policy_ref"),
    }


def _summary_artifact(payload: dict) -> dict:
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else []
    return {
        "schema_version": "opportunity_board_summary.v1",
        "generated_at": payload.get("generated_at"),
        "total_rows": payload.get("row_count", len(rows)),
        "fresh_rows": sum(1 for row in rows if str(row.get("freshness_status") or "").lower() == "fresh"),
        "high_opportunity_rows": summary.get("high_opportunity_count", 0),
        "easy_rows": summary.get("easy_count", 0),
        "rows_with_alerts": sum(1 for row in rows if int(row.get("alert_count") or 0) > 0),
        "rows_with_anomalies": sum(1 for row in rows if int(row.get("anomaly_count") or 0) > 0),
        "city_count": summary.get("city_count", 0),
        "family_count": summary.get("family_count", 0),
        "top_city": summary.get("top_city", "-"),
        "top_family": summary.get("top_family", "-"),
        "top_model": summary.get("top_model", "-"),
        "seed_summary": payload.get("seed_summary") or {},
    }


def _write_optional_artifact(path: str | Path | None, payload: object) -> Path | None:
    if path is None:
        return None
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def _slugify(value: str) -> str:
    slug = value.strip().lower().replace(" ", "_").replace("/", "_")
    slug = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in slug)
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "unknown"
