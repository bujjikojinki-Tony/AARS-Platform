from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MarketBandSpec:
    scheme: str
    band: str | None
    label: str | None = None
    lower_threshold: float | None = None
    upper_threshold: float | None = None
    unit: str | None = None


_SEA_ICE_BETWEEN_PATTERN = re.compile(
    r"between\s+(?P<lower>\d+(?:\.\d+)?)m?\s*&\s*(?P<upper>\d+(?:\.\d+)?)m?",
    re.IGNORECASE,
)
_SEA_ICE_LESS_THAN_PATTERN = re.compile(
    r"less than\s+(?P<upper>\d+(?:\.\d+)?)m?",
    re.IGNORECASE,
)
_SEA_ICE_ABOVE_PATTERN = re.compile(
    r"above\s+(?P<lower>\d+(?:\.\d+)?)m?",
    re.IGNORECASE,
)
_PRECIP_BETWEEN_PATTERN = re.compile(
    r"between\s+(?P<lower>\d+(?:\.\d+)?)\s*(?:mm|millimeters?)?\s*(?:and|&|to)\s*"
    r"(?P<upper>\d+(?:\.\d+)?)\s*(?:mm|millimeters?)?",
    re.IGNORECASE,
)
_PRECIP_LESS_THAN_PATTERN = re.compile(
    r"less than\s+(?P<upper>\d+(?:\.\d+)?)\s*(?:mm|millimeters?)?",
    re.IGNORECASE,
)
_PRECIP_ABOVE_PATTERN = re.compile(
    r"(?:above|more than|greater than)\s+(?P<lower>\d+(?:\.\d+)?)\s*(?:mm|millimeters?)?",
    re.IGNORECASE,
)
_SNOW_BETWEEN_PATTERN = re.compile(
    r"between\s+(?P<lower>\d+(?:\.\d+)?)\s*(?:cm|centimeters?)?\s*(?:and|&|to)\s*"
    r"(?P<upper>\d+(?:\.\d+)?)\s*(?:cm|centimeters?)?",
    re.IGNORECASE,
)
_SNOW_LESS_THAN_PATTERN = re.compile(
    r"less than\s+(?P<upper>\d+(?:\.\d+)?)\s*(?:cm|centimeters?)?",
    re.IGNORECASE,
)
_SNOW_ABOVE_PATTERN = re.compile(
    r"(?:above|more than|greater than)\s+(?P<lower>\d+(?:\.\d+)?)\s*(?:cm|centimeters?)?",
    re.IGNORECASE,
)
_WIND_BETWEEN_PATTERN = re.compile(
    r"between\s+(?P<lower>\d+(?:\.\d+)?)\s*(?:km/h|kph)?\s*(?:and|&|to)\s*"
    r"(?P<upper>\d+(?:\.\d+)?)\s*(?:km/h|kph)?",
    re.IGNORECASE,
)
_WIND_LESS_THAN_PATTERN = re.compile(
    r"less than\s+(?P<upper>\d+(?:\.\d+)?)\s*(?:km/h|kph)?",
    re.IGNORECASE,
)
_WIND_ABOVE_PATTERN = re.compile(
    r"(?:above|more than|greater than)\s+(?P<lower>\d+(?:\.\d+)?)\s*(?:km/h|kph)?",
    re.IGNORECASE,
)


def derive_market_band_spec(
    market_question: str | None,
    favored_probability: float | None,
) -> MarketBandSpec:
    question = (market_question or "").lower()

    if "hottest year" in question or "rank among the hottest years" in question:
        ordinal_rank = _extract_global_temperature_ordinal_rank(market_question or "")
        band = f"top_{ordinal_rank}" if ordinal_rank is not None else "top_3"
        label = f"ordinal_rank_{ordinal_rank}" if ordinal_rank is not None else "ordinal_rank"
        return MarketBandSpec(
            scheme="global_temperature_index_ordinal",
            band=band,
            label=label,
            unit="ordinal_rank",
        )

    if "sea ice" in question and "extent" in question:
        lower, upper = _extract_sea_ice_thresholds(market_question or "")
        if lower is not None and upper is not None:
            label = f"{_format_threshold(lower)}_to_{_format_threshold(upper)}"
            return MarketBandSpec(
                scheme="sea_ice_range_3way",
                band="in_range",
                label=label,
                lower_threshold=lower,
                upper_threshold=upper,
                unit="million_sq_km",
            )

        return MarketBandSpec(
            scheme="sea_ice_range_3way",
            band="in_range",
            label="sea_ice_range",
            unit="million_sq_km",
        )

    if any(keyword in question for keyword in ("precipitation", "rainfall", "rain")):
        lower, upper = _extract_precipitation_thresholds(market_question or "")
        if lower is not None and upper is not None:
            label = f"{_format_threshold(lower)}_to_{_format_threshold(upper)}"
            return MarketBandSpec(
                scheme="precipitation_range_3way",
                band="in_range",
                label=label,
                lower_threshold=lower,
                upper_threshold=upper,
                unit="mm",
            )
        if upper is not None:
            return MarketBandSpec(
                scheme="precipitation_range_3way",
                band="below_range",
                label=f"lt_{_format_threshold(upper)}",
                upper_threshold=upper,
                unit="mm",
            )
        if lower is not None:
            return MarketBandSpec(
                scheme="precipitation_range_3way",
                band="above_range",
                label=f"gt_{_format_threshold(lower)}",
                lower_threshold=lower,
                unit="mm",
            )
        return MarketBandSpec(
            scheme="precipitation_range_3way",
            band=None,
            label="precipitation_range",
            unit="mm",
        )

    if any(keyword in question for keyword in ("snowfall", "snow total", "snow ")):
        lower, upper = _extract_snowfall_thresholds(market_question or "")
        if lower is not None and upper is not None:
            label = f"{_format_threshold(lower)}_to_{_format_threshold(upper)}"
            return MarketBandSpec(
                scheme="snowfall_range_3way",
                band="in_range",
                label=label,
                lower_threshold=lower,
                upper_threshold=upper,
                unit="cm",
            )
        if upper is not None:
            return MarketBandSpec(
                scheme="snowfall_range_3way",
                band="below_range",
                label=f"lt_{_format_threshold(upper)}",
                upper_threshold=upper,
                unit="cm",
            )
        if lower is not None:
            return MarketBandSpec(
                scheme="snowfall_range_3way",
                band="above_range",
                label=f"gt_{_format_threshold(lower)}",
                lower_threshold=lower,
                unit="cm",
            )
        return MarketBandSpec(
            scheme="snowfall_range_3way",
            band=None,
            label="snowfall_range",
            unit="cm",
        )

    if "wind" in question:
        lower, upper = _extract_wind_thresholds(market_question or "")
        if lower is not None and upper is not None:
            label = f"{_format_threshold(lower)}_to_{_format_threshold(upper)}"
            return MarketBandSpec(
                scheme="wind_speed_range_3way",
                band="in_range",
                label=label,
                lower_threshold=lower,
                upper_threshold=upper,
                unit="km_h",
            )
        if upper is not None:
            return MarketBandSpec(
                scheme="wind_speed_range_3way",
                band="below_range",
                label=f"lt_{_format_threshold(upper)}",
                upper_threshold=upper,
                unit="km_h",
            )
        if lower is not None:
            return MarketBandSpec(
                scheme="wind_speed_range_3way",
                band="above_range",
                label=f"gt_{_format_threshold(lower)}",
                lower_threshold=lower,
                unit="km_h",
            )
        return MarketBandSpec(
            scheme="wind_speed_range_3way",
            band=None,
            label="wind_speed_range",
            unit="km_h",
        )

    return MarketBandSpec(
        scheme="temperature_4_bucket",
        band=_classify_probability_bucket(favored_probability),
        label="probability_bucket",
    )


def _classify_probability_bucket(probability: float | None) -> str | None:
    if probability is None:
        return None
    if probability < 0.25:
        return "26_or_below"
    if probability < 0.50:
        return "27"
    if probability < 0.75:
        return "28"
    return "29_plus"


def _extract_sea_ice_thresholds(question: str) -> tuple[float | None, float | None]:
    between = _SEA_ICE_BETWEEN_PATTERN.search(question)
    if between:
        return float(between.group("lower")), float(between.group("upper"))

    less_than = _SEA_ICE_LESS_THAN_PATTERN.search(question)
    if less_than:
        return None, float(less_than.group("upper"))

    above = _SEA_ICE_ABOVE_PATTERN.search(question)
    if above:
        return float(above.group("lower")), None

    return None, None


def _extract_precipitation_thresholds(question: str) -> tuple[float | None, float | None]:
    between = _PRECIP_BETWEEN_PATTERN.search(question)
    if between:
        return float(between.group("lower")), float(between.group("upper"))

    less_than = _PRECIP_LESS_THAN_PATTERN.search(question)
    if less_than:
        return None, float(less_than.group("upper"))

    above = _PRECIP_ABOVE_PATTERN.search(question)
    if above:
        return float(above.group("lower")), None

    return None, None


def _extract_snowfall_thresholds(question: str) -> tuple[float | None, float | None]:
    between = _SNOW_BETWEEN_PATTERN.search(question)
    if between:
        return float(between.group("lower")), float(between.group("upper"))

    less_than = _SNOW_LESS_THAN_PATTERN.search(question)
    if less_than:
        return None, float(less_than.group("upper"))

    above = _SNOW_ABOVE_PATTERN.search(question)
    if above:
        return float(above.group("lower")), None

    return None, None


def _extract_wind_thresholds(question: str) -> tuple[float | None, float | None]:
    between = _WIND_BETWEEN_PATTERN.search(question)
    if between:
        return float(between.group("lower")), float(between.group("upper"))

    less_than = _WIND_LESS_THAN_PATTERN.search(question)
    if less_than:
        return None, float(less_than.group("upper"))

    above = _WIND_ABOVE_PATTERN.search(question)
    if above:
        return float(above.group("lower")), None

    return None, None


def _format_threshold(value: float) -> str:
    if float(value).is_integer():
        return f"{int(value)}_0"
    return str(value).replace(".", "_")


def _extract_global_temperature_ordinal_rank(question: str) -> int | None:
    match = re.search(
        r"(first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)[-\s]*hottest year",
        question,
        re.IGNORECASE,
    )
    if not match:
        return None

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
    return ordinal_map.get(match.group(1).lower())
