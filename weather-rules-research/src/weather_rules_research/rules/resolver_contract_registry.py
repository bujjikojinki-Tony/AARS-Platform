from __future__ import annotations

from dataclasses import dataclass

from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.official_obs import WundergroundHistoryHelper
from weather_rules_research.registries.source_registry import (
    get_source_contract_profile,
    required_data_source_for_family,
)
from weather_rules_research.rules.market_taxonomy import MarketTaxonomy


@dataclass(frozen=True)
class ResolverSourceContract:
    contract_version: str = "resolver_contract.v1"
    required_data_source: str | None = None
    required_sources: tuple[str, ...] = ()
    settlement_source_type: str | None = None
    official_vs_proxy_source: str | None = None
    source_match_grade: str | None = None
    official_source_url: str | None = None
    source_note: str | None = None
    station_id: str | None = None
    unit: str | None = None


class ResolverContractRegistry:
    def build_contract(
        self,
        *,
        taxonomy: MarketTaxonomy,
        market_snapshot: dict,
        rule: MarketRule | None,
        resolution_snapshot: dict | None = None,
    ) -> ResolverSourceContract:
        resolution_snapshot = resolution_snapshot or {}
        family = taxonomy.market_family

        if family in {"station_temperature", "weather_metric"}:
            return self._build_station_contract(
                taxonomy=taxonomy,
                market_snapshot=market_snapshot,
                rule=rule,
                resolution_snapshot=resolution_snapshot,
            )
        if family == "sea_ice_extent":
            profile = get_source_contract_profile("sea_ice_family_exact")
            return ResolverSourceContract(
                required_data_source=profile.get("required_data_source")
                or taxonomy.required_data_source
                or required_data_source_for_family(family),
                required_sources=tuple(profile.get("required_sources") or ()),
                settlement_source_type=profile.get("settlement_source_type"),
                official_vs_proxy_source=profile.get("official_vs_proxy_source"),
                source_match_grade=profile.get("source_match_grade"),
                official_source_url=profile.get("official_source_url"),
                source_note=profile.get("source_note"),
                unit=resolution_snapshot.get("unit") or "million_sq_km",
            )
        if family == "global_temperature_index":
            profile = get_source_contract_profile("global_temperature_family_exact")
            return ResolverSourceContract(
                required_data_source=profile.get("required_data_source")
                or taxonomy.required_data_source
                or required_data_source_for_family(family),
                required_sources=tuple(profile.get("required_sources") or ()),
                settlement_source_type=profile.get("settlement_source_type"),
                official_vs_proxy_source=profile.get("official_vs_proxy_source"),
                source_match_grade=profile.get("source_match_grade"),
                official_source_url=profile.get("official_source_url"),
                source_note=profile.get("source_note"),
            )
        profile = get_source_contract_profile("unknown_unmatched")
        return ResolverSourceContract(
            required_data_source=taxonomy.required_data_source or required_data_source_for_family(family),
            required_sources=tuple(profile.get("required_sources") or ()),
            settlement_source_type=profile.get("settlement_source_type"),
            official_vs_proxy_source=profile.get("official_vs_proxy_source"),
            source_match_grade=profile.get("source_match_grade"),
            official_source_url=profile.get("official_source_url"),
            source_note=profile.get("source_note"),
            unit=resolution_snapshot.get("unit"),
        )

    def _build_station_contract(
        self,
        *,
        taxonomy: MarketTaxonomy,
        market_snapshot: dict,
        rule: MarketRule | None,
        resolution_snapshot: dict,
    ) -> ResolverSourceContract:
        location_name = (
            (rule.location_name if rule is not None else None)
            or market_snapshot.get("location_name")
            or resolution_snapshot.get("parsed_location_name")
        )
        station_name = rule.station_name if rule is not None else None
        station_id = self._station_id(rule=rule, location_name=location_name, station_name=station_name)
        unit = resolution_snapshot.get("unit") or _unit_for_variable(
            rule.variable_name if rule is not None else taxonomy.primary_variable_name
        )

        if self._is_shanghai_station(location_name=location_name, station_name=station_name, station_id=station_id):
            profile = get_source_contract_profile("station_shanghai_exact")
            return ResolverSourceContract(
                required_data_source=profile.get("required_data_source"),
                required_sources=tuple(profile.get("required_sources") or ()),
                settlement_source_type=profile.get("settlement_source_type"),
                official_vs_proxy_source=profile.get("official_vs_proxy_source"),
                source_match_grade=profile.get("source_match_grade"),
                official_source_url=WundergroundHistoryHelper.build_history_weekly_url("ZSPD"),
                source_note=profile.get("source_note"),
                station_id="ZSPD",
                unit=unit,
            )

        if rule is None:
            profile = get_source_contract_profile("station_fallback")
            return ResolverSourceContract(
                required_data_source=profile.get("required_data_source")
                or taxonomy.required_data_source
                or required_data_source_for_family(taxonomy.market_family),
                required_sources=tuple(profile.get("required_sources") or ()),
                settlement_source_type=profile.get("settlement_source_type"),
                official_vs_proxy_source=profile.get("official_vs_proxy_source"),
                source_match_grade=profile.get("source_match_grade"),
                official_source_url=profile.get("official_source_url"),
                source_note=profile.get("source_note"),
                station_id=station_id,
                unit=unit,
            )

        profile = get_source_contract_profile("station_exact")
        return ResolverSourceContract(
            required_data_source=profile.get("required_data_source")
            or taxonomy.required_data_source
            or required_data_source_for_family(taxonomy.market_family),
            required_sources=tuple(profile.get("required_sources") or ()),
            settlement_source_type=profile.get("settlement_source_type"),
            official_vs_proxy_source="official" if self._rule_looks_official(rule) else "proxy",
            source_match_grade=profile.get("source_match_grade"),
            official_source_url=self._station_source_url(rule, station_id),
            source_note=profile.get("source_note"),
            station_id=station_id,
            unit=unit,
        )

    @staticmethod
    def _rule_looks_official(rule: MarketRule) -> bool:
        text = f"{rule.source_name} {rule.raw_rules_text}".lower()
        return any(keyword in text for keyword in ("official", "noaa", "nws", "weather.gov", "wunderground"))

    @staticmethod
    def _station_id(
        *,
        rule: MarketRule | None,
        location_name: str | None,
        station_name: str | None,
    ) -> str | None:
        if ResolverContractRegistry._is_shanghai_station(
            location_name=location_name,
            station_name=station_name,
            station_id=rule.nws_station_id if rule is not None else None,
        ):
            return "ZSPD"
        if rule is None:
            return None
        return rule.nws_station_id or rule.cdo_station_id

    @staticmethod
    def _station_source_url(rule: MarketRule, station_id: str | None) -> str | None:
        if station_id and station_id.upper() == "ZSPD":
            return WundergroundHistoryHelper.build_history_weekly_url("ZSPD")
        if rule.nws_station_id:
            return f"https://api.weather.gov/stations/{rule.nws_station_id}"
        if rule.cdo_station_id:
            return "https://www.ncei.noaa.gov/cdo-web/api/v2"
        return None

    @staticmethod
    def _is_shanghai_station(
        *,
        location_name: str | None,
        station_name: str | None,
        station_id: str | None,
    ) -> bool:
        parts = [
            str(location_name or "").lower(),
            str(station_name or "").lower(),
            str(station_id or "").lower(),
        ]
        joined = " ".join(parts)
        return "shanghai" in joined or "pudong" in joined or "zspd" in joined


def _unit_for_variable(variable_name: str | None) -> str | None:
    if variable_name in {"daily_max_temperature", "daily_min_temperature"}:
        return "celsius"
    if variable_name == "daily_precipitation_sum":
        return "mm"
    if variable_name == "daily_snowfall_sum":
        return "cm"
    if variable_name == "daily_max_wind_speed":
        return "km_h"
    return None
