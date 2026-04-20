from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from weather_rules_research.models.market_rule import MarketRule
from weather_rules_research.rules.market_taxonomy import MarketTaxonomy, classify_market_question
from weather_rules_research.rules.question_parser import parse_market_question


@dataclass(frozen=True)
class MarketResolution:
    rule: MarketRule | None
    reason: str
    taxonomy: MarketTaxonomy
    resolver_name: str
    snapshot: dict | None = None


class MarketResolver(Protocol):
    name: str

    def resolve(self, market_snapshot: dict, rules: list[MarketRule], taxonomy: MarketTaxonomy) -> MarketResolution:
        ...


class UnsupportedMarketResolver:
    def __init__(self, name: str = "unsupported_market_resolver") -> None:
        self.name = name

    def resolve(self, market_snapshot: dict, rules: list[MarketRule], taxonomy: MarketTaxonomy) -> MarketResolution:
        return MarketResolution(
            rule=None,
            reason=f"unsupported_market_family:{taxonomy.market_family}",
            taxonomy=taxonomy,
            resolver_name=self.name,
            snapshot={
                "market_family": taxonomy.market_family,
                "resolution_scope": taxonomy.resolution_scope,
                "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
                "required_data_source": taxonomy.required_data_source,
                "band_scheme": taxonomy.band_scheme,
            },
        )


class SeaIceExtentResolver:
    def __init__(self, name: str = "sea_ice_extent_resolver") -> None:
        self.name = name

    def resolve(self, market_snapshot: dict, rules: list[MarketRule], taxonomy: MarketTaxonomy) -> MarketResolution:
        question = str(market_snapshot.get("market_question") or "")
        parsed = _parse_sea_ice_expectation(question)
        return MarketResolution(
            rule=None,
            reason="sea_ice_extent_snapshot_expected",
            taxonomy=taxonomy,
            resolver_name=self.name,
            snapshot={
                "market_family": taxonomy.market_family,
                "resolution_scope": taxonomy.resolution_scope,
                "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
                "required_data_source": taxonomy.required_data_source,
                "band_scheme": taxonomy.band_scheme,
                "question_mode": parsed["question_mode"],
                "threshold_lower": parsed["threshold_lower"],
                "threshold_upper": parsed["threshold_upper"],
                "unit": parsed["unit"],
                "expected_band": parsed["expected_band"],
                "comparison_hint": parsed["comparison_hint"],
            },
        )


class GlobalTemperatureIndexResolver:
    def __init__(self, name: str = "global_temperature_index_resolver") -> None:
        self.name = name

    def resolve(self, market_snapshot: dict, rules: list[MarketRule], taxonomy: MarketTaxonomy) -> MarketResolution:
        question = str(market_snapshot.get("market_question") or "")
        parsed = _parse_global_temperature_index(question)
        return MarketResolution(
            rule=None,
            reason="global_temperature_index_snapshot_expected",
            taxonomy=taxonomy,
            resolver_name=self.name,
            snapshot={
                "market_family": taxonomy.market_family,
                "resolution_scope": taxonomy.resolution_scope,
                "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
                "required_data_source": taxonomy.required_data_source,
                "band_scheme": taxonomy.band_scheme,
                "question_mode": parsed["question_mode"],
                "ordinal_rank": parsed["ordinal_rank"],
                "expected_band": parsed["expected_band"],
                "comparison_hint": parsed["comparison_hint"],
            },
        )


class StationTemperatureResolver:
    def __init__(self, name: str = "station_temperature_resolver") -> None:
        self.name = name

    def resolve(self, market_snapshot: dict, rules: list[MarketRule], taxonomy: MarketTaxonomy) -> MarketResolution:
        market_id = str(market_snapshot.get("market_id") or "")
        market_question = str(market_snapshot.get("market_question") or "")
        location_name = str(market_snapshot.get("location_name") or "")
        snapshot = _build_weather_metric_snapshot(market_question, taxonomy, parse_market_question(market_question).variable_name)

        for rule in rules:
            if str(rule.market_id) == market_id:
                return MarketResolution(
                    rule=rule,
                    reason="matched_by_market_id",
                    taxonomy=taxonomy,
                    resolver_name=self.name,
                    snapshot=snapshot,
                )

        if not market_question:
            return MarketResolution(rule=None, reason="missing_market_question", taxonomy=taxonomy, resolver_name=self.name)

        parsed = parse_market_question(market_question)
        if parsed.needs_review or not parsed.location_name or not parsed.variable_name:
            return MarketResolution(
                rule=None,
                reason="question_not_supported_by_temperature_parser",
                taxonomy=taxonomy,
                resolver_name=self.name,
                snapshot={
                    "market_family": taxonomy.market_family,
                    "resolution_scope": taxonomy.resolution_scope,
                    "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
                    "required_data_source": taxonomy.required_data_source,
                    "band_scheme": taxonomy.band_scheme,
                    "parse_confidence": parsed.parse_confidence,
                },
            )

        normalized_location = _normalize_text(parsed.location_name)
        normalized_rule_location = _normalize_text(location_name)

        for rule in rules:
            if _normalize_text(rule.location_name) != normalized_location:
                continue
            if rule.variable_name != parsed.variable_name:
                continue
            return MarketResolution(
                rule=rule,
                reason="matched_by_question_and_location",
                taxonomy=taxonomy,
                resolver_name=self.name,
            )

        if normalized_location and normalized_rule_location and normalized_location == normalized_rule_location:
            return MarketResolution(
                rule=None,
                reason="no_rule_for_parsed_location_and_variable",
                taxonomy=taxonomy,
                resolver_name=self.name,
                snapshot={
                    "market_family": taxonomy.market_family,
                    "resolution_scope": taxonomy.resolution_scope,
                    "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
                    "required_data_source": taxonomy.required_data_source,
                    "band_scheme": taxonomy.band_scheme,
                    "parsed_location_name": parsed.location_name,
                    "parsed_variable_name": parsed.variable_name,
                },
            )

        return MarketResolution(rule=None, reason="no_rulebook_match", taxonomy=taxonomy, resolver_name=self.name)


class StationWeatherMetricResolver:
    def __init__(self, name: str = "station_weather_metric_resolver") -> None:
        self.name = name

    def resolve(self, market_snapshot: dict, rules: list[MarketRule], taxonomy: MarketTaxonomy) -> MarketResolution:
        market_id = str(market_snapshot.get("market_id") or "")
        market_question = str(market_snapshot.get("market_question") or "")
        location_name = str(market_snapshot.get("location_name") or "")
        parsed_for_snapshot = parse_market_question(market_question)
        snapshot = _build_weather_metric_snapshot(
            market_question,
            taxonomy,
            parsed_for_snapshot.variable_name,
        )

        for rule in rules:
            if str(rule.market_id) == market_id:
                return MarketResolution(
                    rule=rule,
                    reason="matched_by_market_id",
                    taxonomy=taxonomy,
                    resolver_name=self.name,
                    snapshot=snapshot,
                )

        if not market_question:
            return MarketResolution(rule=None, reason="missing_market_question", taxonomy=taxonomy, resolver_name=self.name)

        parsed = parse_market_question(market_question)
        if parsed.needs_review or not parsed.location_name or not parsed.variable_name:
            return MarketResolution(
                rule=None,
                reason="question_not_supported_by_weather_metric_parser",
                taxonomy=taxonomy,
                resolver_name=self.name,
                snapshot={
                    "market_family": taxonomy.market_family,
                    "resolution_scope": taxonomy.resolution_scope,
                    "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
                    "required_data_source": taxonomy.required_data_source,
                    "band_scheme": taxonomy.band_scheme,
                    "parse_confidence": parsed.parse_confidence,
                },
            )

        normalized_location = _normalize_text(parsed.location_name)
        normalized_rule_location = _normalize_text(location_name)
        for rule in rules:
            if _normalize_text(rule.location_name) != normalized_location:
                continue
            if rule.variable_name != parsed.variable_name:
                continue
            return MarketResolution(
                rule=rule,
                reason="matched_by_question_and_location",
                taxonomy=taxonomy,
                resolver_name=self.name,
                snapshot=snapshot,
            )

        if normalized_location and normalized_rule_location and normalized_location == normalized_rule_location:
            return MarketResolution(
                rule=None,
                reason="no_rule_for_parsed_location_and_variable",
                taxonomy=taxonomy,
                resolver_name=self.name,
                snapshot={
                    **snapshot,
                    "parsed_location_name": parsed.location_name,
                    "parsed_variable_name": parsed.variable_name,
                },
            )

        return MarketResolution(rule=None, reason="no_rulebook_match", taxonomy=taxonomy, resolver_name=self.name)


class MarketResolverRegistry:
    def __init__(self) -> None:
        self._resolvers: dict[str, MarketResolver] = {
            "station_temperature": StationTemperatureResolver(),
            "weather_metric": StationWeatherMetricResolver(),
            "sea_ice_extent": SeaIceExtentResolver(),
            "global_temperature_index": GlobalTemperatureIndexResolver(),
        }
        self._fallback = UnsupportedMarketResolver()

    def resolve(self, market_snapshot: dict, rules: list[MarketRule]) -> MarketResolution:
        question = str(market_snapshot.get("market_question") or "")
        taxonomy = classify_market_question(question)
        resolver = self._resolvers.get(taxonomy.market_family, self._fallback)
        return resolver.resolve(market_snapshot, rules, taxonomy)

    def register(self, market_family: str, resolver: MarketResolver) -> None:
        self._resolvers[market_family] = resolver


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().split())


def _parse_sea_ice_expectation(question: str) -> dict:
    lower = question.lower()
    between = _extract_between_thresholds(lower)
    if between is not None:
        lower_threshold, upper_threshold = between
        return {
            "question_mode": "between",
            "threshold_lower": lower_threshold,
            "threshold_upper": upper_threshold,
            "unit": "million_sq_km",
            "expected_band": "in_range",
            "comparison_hint": "Compare observed sea ice extent against the stated range.",
        }

    less_than = _extract_less_than_threshold(lower)
    if less_than is not None:
        return {
            "question_mode": "less_than",
            "threshold_lower": None,
            "threshold_upper": less_than,
            "unit": "million_sq_km",
            "expected_band": "below_range",
            "comparison_hint": "Compare observed sea ice extent against the upper threshold.",
        }

    above = _extract_above_threshold(lower)
    if above is not None:
        return {
            "question_mode": "above",
            "threshold_lower": above,
            "threshold_upper": None,
            "unit": "million_sq_km",
            "expected_band": "above_range",
            "comparison_hint": "Compare observed sea ice extent against the lower threshold.",
        }

    return {
        "question_mode": "unknown",
        "threshold_lower": None,
        "threshold_upper": None,
        "unit": "million_sq_km",
        "expected_band": "in_range",
        "comparison_hint": "Sea ice question parsed, but thresholds were not recognized.",
    }


def _build_weather_metric_snapshot(
    question: str,
    taxonomy: MarketTaxonomy,
    variable_name: str | None,
) -> dict:
    base = {
        "market_family": taxonomy.market_family,
        "resolution_scope": taxonomy.resolution_scope,
        "supported_by_current_pipeline": taxonomy.supported_by_current_pipeline,
        "required_data_source": taxonomy.required_data_source,
        "band_scheme": taxonomy.band_scheme,
    }

    if variable_name == "daily_precipitation_sum":
        return {
            **base,
            **_parse_precipitation_expectation(question),
        }

    if variable_name == "daily_snowfall_sum":
        return {
            **base,
            **_parse_snowfall_expectation(question),
        }

    if variable_name == "daily_max_wind_speed":
        return {
            **base,
            **_parse_wind_speed_expectation(question),
        }

    return base


def _parse_precipitation_expectation(question: str) -> dict:
    lower = question.lower()
    between = _extract_metric_between_thresholds(lower, unit_pattern=r"(?:mm|millimeters?)")
    if between is not None:
        lower_threshold, upper_threshold = between
        return {
            "question_mode": "between",
            "threshold_lower": lower_threshold,
            "threshold_upper": upper_threshold,
            "unit": "mm",
            "expected_band": "in_range",
            "comparison_hint": "Compare observed precipitation against the stated range.",
        }

    less_than = _extract_metric_less_than_threshold(lower, unit_pattern=r"(?:mm|millimeters?)")
    if less_than is not None:
        return {
            "question_mode": "less_than",
            "threshold_lower": None,
            "threshold_upper": less_than,
            "unit": "mm",
            "expected_band": "below_range",
            "comparison_hint": "Compare observed precipitation against the upper threshold.",
        }

    above = _extract_metric_above_threshold(
        lower,
        unit_pattern=r"(?:mm|millimeters?)",
    )
    if above is not None:
        return {
            "question_mode": "above",
            "threshold_lower": above,
            "threshold_upper": None,
            "unit": "mm",
            "expected_band": "above_range",
            "comparison_hint": "Compare observed precipitation against the lower threshold.",
        }

    return {
        "question_mode": "unknown",
        "threshold_lower": None,
        "threshold_upper": None,
        "unit": "mm",
        "expected_band": None,
        "comparison_hint": "Precipitation question parsed, but thresholds were not recognized.",
    }


def _parse_snowfall_expectation(question: str) -> dict:
    lower = question.lower()
    between = _extract_metric_between_thresholds(lower, unit_pattern=r"(?:cm|centimeters?)")
    if between is not None:
        lower_threshold, upper_threshold = between
        return {
            "question_mode": "between",
            "threshold_lower": lower_threshold,
            "threshold_upper": upper_threshold,
            "unit": "cm",
            "expected_band": "in_range",
            "comparison_hint": "Compare observed snowfall against the stated range.",
        }

    less_than = _extract_metric_less_than_threshold(lower, unit_pattern=r"(?:cm|centimeters?)")
    if less_than is not None:
        return {
            "question_mode": "less_than",
            "threshold_lower": None,
            "threshold_upper": less_than,
            "unit": "cm",
            "expected_band": "below_range",
            "comparison_hint": "Compare observed snowfall against the upper threshold.",
        }

    above = _extract_metric_above_threshold(
        lower,
        unit_pattern=r"(?:cm|centimeters?)",
    )
    if above is not None:
        return {
            "question_mode": "above",
            "threshold_lower": above,
            "threshold_upper": None,
            "unit": "cm",
            "expected_band": "above_range",
            "comparison_hint": "Compare observed snowfall against the lower threshold.",
        }

    return {
        "question_mode": "unknown",
        "threshold_lower": None,
        "threshold_upper": None,
        "unit": "cm",
        "expected_band": None,
        "comparison_hint": "Snowfall question parsed, but thresholds were not recognized.",
    }


def _parse_wind_speed_expectation(question: str) -> dict:
    lower = question.lower()
    between = _extract_metric_between_thresholds(lower, unit_pattern=r"(?:km/h|kph)")
    if between is not None:
        lower_threshold, upper_threshold = between
        return {
            "question_mode": "between",
            "threshold_lower": lower_threshold,
            "threshold_upper": upper_threshold,
            "unit": "km_h",
            "expected_band": "in_range",
            "comparison_hint": "Compare observed wind speed against the stated range.",
        }

    less_than = _extract_metric_less_than_threshold(lower, unit_pattern=r"(?:km/h|kph)")
    if less_than is not None:
        return {
            "question_mode": "less_than",
            "threshold_lower": None,
            "threshold_upper": less_than,
            "unit": "km_h",
            "expected_band": "below_range",
            "comparison_hint": "Compare observed wind speed against the upper threshold.",
        }

    above = _extract_metric_above_threshold(
        lower,
        unit_pattern=r"(?:km/h|kph)",
    )
    if above is not None:
        return {
            "question_mode": "above",
            "threshold_lower": above,
            "threshold_upper": None,
            "unit": "km_h",
            "expected_band": "above_range",
            "comparison_hint": "Compare observed wind speed against the lower threshold.",
        }

    return {
        "question_mode": "unknown",
        "threshold_lower": None,
        "threshold_upper": None,
        "unit": "km_h",
        "expected_band": None,
        "comparison_hint": "Wind-speed question parsed, but thresholds were not recognized.",
    }


def _extract_between_thresholds(question: str) -> tuple[float, float] | None:
    import re

    match = re.search(
        r"between\s+(?P<lower>\d+(?:\.\d+)?)m?\s*&\s*(?P<upper>\d+(?:\.\d+)?)m?",
        question,
        re.IGNORECASE,
    )
    if not match:
        return None
    return float(match.group("lower")), float(match.group("upper"))


def _extract_less_than_threshold(question: str) -> float | None:
    import re

    match = re.search(r"less than\s+(?P<upper>\d+(?:\.\d+)?)m?", question, re.IGNORECASE)
    if not match:
        return None
    return float(match.group("upper"))


def _extract_above_threshold(question: str) -> float | None:
    import re

    match = re.search(r"above\s+(?P<lower>\d+(?:\.\d+)?)m?", question, re.IGNORECASE)
    if not match:
        return None
    return float(match.group("lower"))


def _extract_metric_between_thresholds(question: str, unit_pattern: str) -> tuple[float, float] | None:
    import re

    match = re.search(
        rf"between\s+(?P<lower>\d+(?:\.\d+)?)\s*(?:{unit_pattern})?\s*(?:and|&|to)\s*"
        rf"(?P<upper>\d+(?:\.\d+)?)\s*(?:{unit_pattern})?",
        question,
        re.IGNORECASE,
    )
    if not match:
        return None
    return float(match.group("lower")), float(match.group("upper"))


def _extract_metric_less_than_threshold(question: str, unit_pattern: str) -> float | None:
    import re

    match = re.search(
        rf"less than\s+(?P<upper>\d+(?:\.\d+)?)\s*(?:{unit_pattern})?",
        question,
        re.IGNORECASE,
    )
    if not match:
        return None
    return float(match.group("upper"))


def _extract_metric_above_threshold(question: str, unit_pattern: str) -> float | None:
    import re

    match = re.search(
        rf"(?:above|more than|greater than)\s+(?P<lower>\d+(?:\.\d+)?)\s*(?:{unit_pattern})?",
        question,
        re.IGNORECASE,
    )
    if not match:
        return None
    return float(match.group("lower"))


def _parse_global_temperature_index(question: str) -> dict:
    lower = question.lower()
    if "hottest year" in lower and "third" not in lower and "fourth" not in lower and "fifth" not in lower:
        year = _extract_year(lower)
        return {
            "question_mode": "ordinal_hottest_year",
            "ordinal_rank": 1,
            "year": year,
            "expected_band": "top_1",
            "comparison_hint": "Compare the climate index outcome against hottest-year rank 1.",
        }

    match = _extract_ordinal_hottest_year(lower)
    if match is not None:
        ordinal_rank, year = match
        return {
            "question_mode": "ordinal_hottest_year",
            "ordinal_rank": ordinal_rank,
            "year": year,
            "expected_band": f"top_{ordinal_rank}",
            "comparison_hint": "Compare the climate index outcome against the ordinal rank in the question.",
        }

    return {
        "question_mode": "unknown",
        "ordinal_rank": None,
        "year": None,
        "expected_band": "top_3",
        "comparison_hint": "Global temperature index question parsed, but ordinal rank was not recognized.",
    }


def _extract_year(question: str) -> str | None:
    import re

    match = re.search(r"\b(?P<year>\d{4})\b", question)
    if not match:
        return None
    return match.group("year")


def _extract_ordinal_hottest_year(question: str) -> tuple[int, str | None] | None:
    import re

    ordinal_map = {
        "first": 1,
        "second": 2,
        "third": 3,
        "fourth": 4,
        "fifth": 5,
        "sixth": 6,
        "seventh": 7,
        "eighth": 8,
        "ninth": 9,
        "tenth": 10,
    }

    match = re.search(
        r"(?:(?P<year>\d{4})\s+be the\s+)?(?P<ordinal>first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)"
        r"[-\s]*hottest year(?: on record)?",
        question,
        re.IGNORECASE,
    )
    if not match:
        return None

    ordinal_word = match.group("ordinal").lower()
    ordinal_rank = ordinal_map.get(ordinal_word)
    if ordinal_rank is None:
        return None
    return ordinal_rank, match.group("year")
