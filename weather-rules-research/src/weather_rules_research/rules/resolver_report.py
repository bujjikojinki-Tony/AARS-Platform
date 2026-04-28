from __future__ import annotations

from collections import Counter
import json
from datetime import datetime, timezone
from pathlib import Path

from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.models.resolved_market_rule import ResolvedMarketRule
from weather_rules_research.rules.resolver_contract_registry import ResolverContractRegistry
from weather_rules_research.rules.live_market_resolver import resolve_market_resolution


def build_resolved_market_rule(
    market_snapshot: dict,
    rules: list[MarketRule],
) -> ResolvedMarketRule:
    resolution = resolve_market_resolution(market_snapshot, rules)
    taxonomy = resolution.taxonomy
    base_snapshot = resolution.snapshot or {}
    rule = resolution.rule
    contract = ResolverContractRegistry().build_contract(
        taxonomy=taxonomy,
        market_snapshot=market_snapshot,
        rule=rule,
        resolution_snapshot=base_snapshot,
    )
    market_id = str(market_snapshot.get("market_id") or (rule.market_id if rule else ""))
    market_question = market_snapshot.get("market_question") or (rule.market_question if rule else None)

    if rule is not None:
        policy_refs = {
            "source_policy_ref": contract.source_policy_ref,
            "unit_policy_ref": contract.unit_policy_ref,
            "precision_policy_ref": contract.precision_policy_ref,
            "rounding_policy_ref": contract.rounding_policy_ref,
            "band_mapping_policy_ref": contract.band_mapping_policy_ref,
        }
        return ResolvedMarketRule(
            market_id=market_id,
            market_question=market_question,
            resolver_status="matched",
            resolver_reason=resolution.reason,
            resolver_name=resolution.resolver_name,
            resolver_confidence=rule.parse_confidence,
            market_family=taxonomy.market_family,
            resolution_scope=taxonomy.resolution_scope,
            supported_by_current_pipeline=taxonomy.supported_by_current_pipeline,
            resolver_contract_version=contract.contract_version,
            required_data_source=contract.required_data_source,
            required_sources=list(contract.required_sources),
            band_scheme=taxonomy.band_scheme,
            settlement_source_type=contract.settlement_source_type,
            official_vs_proxy_source=contract.official_vs_proxy_source,
            source_match_grade=contract.source_match_grade,
            official_source_url=contract.official_source_url,
            source_note=contract.source_note,
            **policy_refs,
            location_name=rule.location_name,
            station_name=rule.station_name,
            station_id=contract.station_id,
            nws_station_id=rule.nws_station_id,
            cdo_station_id=rule.cdo_station_id,
            target_date=rule.target_date,
            variable_name=rule.variable_name,
            timezone=rule.timezone,
            unit=contract.unit,
            source_rule_market_id=rule.market_id,
            **{
                key: value
                for key, value in base_snapshot.items()
                if key
                not in {
                    "market_family",
                    "resolution_scope",
                    "supported_by_current_pipeline",
                    "required_data_source",
                    "band_scheme",
                    "unit",
                }
            },
        )

    resolver_status = _status_for_snapshot_rule(taxonomy)
    policy_refs = {
        "source_policy_ref": contract.source_policy_ref,
        "unit_policy_ref": contract.unit_policy_ref,
        "precision_policy_ref": contract.precision_policy_ref,
        "rounding_policy_ref": contract.rounding_policy_ref,
        "band_mapping_policy_ref": contract.band_mapping_policy_ref,
    }
    return ResolvedMarketRule(
        market_id=market_id,
        market_question=market_question,
        resolver_status=resolver_status,
        resolver_reason=resolution.reason,
        resolver_name=resolution.resolver_name,
        resolver_confidence=0.85 if resolver_status == "matched" else 0.0,
        market_family=taxonomy.market_family,
        resolution_scope=taxonomy.resolution_scope,
        supported_by_current_pipeline=taxonomy.supported_by_current_pipeline,
        resolver_contract_version=contract.contract_version,
        required_data_source=contract.required_data_source,
        required_sources=list(contract.required_sources),
        band_scheme=base_snapshot.get("band_scheme") or taxonomy.band_scheme,
        settlement_source_type=contract.settlement_source_type,
        official_vs_proxy_source=contract.official_vs_proxy_source,
        source_match_grade=contract.source_match_grade,
        official_source_url=contract.official_source_url,
        source_note=contract.source_note,
        **policy_refs,
        location_name=market_snapshot.get("location_name") or base_snapshot.get("parsed_location_name"),
        station_id=contract.station_id,
        target_date=base_snapshot.get("target_date"),
        variable_name=base_snapshot.get("parsed_variable_name") or taxonomy.primary_variable_name,
        unit=contract.unit,
        failure_reason=resolution.reason if resolver_status != "matched" else None,
        **{
            key: value
            for key, value in base_snapshot.items()
            if key
            not in {
                "market_family",
                "resolution_scope",
                "supported_by_current_pipeline",
                "required_data_source",
                "band_scheme",
                "parsed_location_name",
                "parsed_variable_name",
                "target_date",
                "unit",
            }
        },
    )


def build_resolver_report(resolved_rules: list[ResolvedMarketRule]) -> dict:
    matched = [rule for rule in resolved_rules if rule.resolver_status == "matched"]
    unmatched = [rule for rule in resolved_rules if rule.resolver_status != "matched"]
    family_counts = Counter(rule.market_family or "unknown" for rule in resolved_rules)
    matched_family_counts = Counter(rule.market_family or "unknown" for rule in matched)
    unmatched_family_counts = Counter(rule.market_family or "unknown" for rule in unmatched)
    source_match_grade_counts = Counter(rule.source_match_grade or "unknown" for rule in resolved_rules)
    source_policy_counts = Counter(rule.official_vs_proxy_source or "unknown" for rule in resolved_rules)
    return {
        "schema_version": "resolver_report.v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tracked_markets": len(resolved_rules),
        "matched": len(matched),
        "unmatched": len(unmatched),
        "family_counts": dict(family_counts),
        "matched_family_counts": dict(matched_family_counts),
        "unmatched_family_counts": dict(unmatched_family_counts),
        "source_match_grade_counts": dict(source_match_grade_counts),
        "source_policy_counts": dict(source_policy_counts),
        "rules": [rule.model_dump(mode="json", exclude_none=True) for rule in resolved_rules],
    }


def write_resolver_outputs(
    *,
    resolved_rules: list[ResolvedMarketRule],
    output_dir: str | Path,
    report_path: str | Path,
) -> None:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for rule in resolved_rules:
        path = out_dir / f"market_rule_{rule.market_id}.json"
        path.write_text(
            json.dumps(rule.model_dump(mode="json", exclude_none=True), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    report = build_resolver_report(resolved_rules)
    report_out = Path(report_path)
    report_out.parent.mkdir(parents=True, exist_ok=True)
    report_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")


def _status_for_snapshot_rule(taxonomy) -> str:
    if (
        taxonomy.supported_by_current_pipeline
        and not taxonomy.station_required
        and taxonomy.required_data_source
    ):
        return "matched"
    return "unmatched"
