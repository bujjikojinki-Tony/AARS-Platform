from __future__ import annotations

import re
from datetime import datetime

from backend.models.core import MarketSnapshot
from backend.models.weather import ParseConfidence
from backend.models.weather import WeatherDirection
from backend.models.weather import WeatherMarketDescriptor
from backend.models.weather import WeatherMetric
from backend.models.weather import WeatherUnit


DATE_PATTERN = re.compile(r"\b(?:on|before)\s+(\d{4}-\d{2}-\d{2})\b", re.IGNORECASE)
MONTH_DAY_YEAR_PATTERN = re.compile(
    r"\b(?:on|before)\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2}),\s*(\d{4})\b",
    re.IGNORECASE,
)
MONTH_DAY_PATTERN = re.compile(
    r"\b(?:on|before)\s+"
    r"(January|February|March|April|May|June|July|August|September|October|November|December)"
    r"\s+(\d{1,2})\b",
    re.IGNORECASE,
)
CITY_PATTERNS = (
    re.compile(r"^Will\s+([A-Z][A-Za-z]+(?:[\s-][A-Z][A-Za-z]+)*)\s+high temperature\b"),
    re.compile(r"\b(?:in|near)\s+([A-Z][A-Za-z]+(?:[\s-][A-Z][A-Za-z]+)*)\b"),
)
THRESHOLD_PATTERN = re.compile(
    r"\b(?:exceed|above|over|reach at least|at least|below|under|less than)\s+(-?\d+(?:\.\d+)?)\s*([A-Za-z%]+)?",
    re.IGNORECASE,
)
MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}
CITY_ALIASES = {
    "nyc": ("New York", "NY"),
    "new york city": ("New York", "NY"),
    "new york": ("New York", "NY"),
    "los angeles": ("Los Angeles", "CA"),
    "chicago": ("Chicago", "IL"),
    "tokyo": ("Tokyo", None),
    "osaka": ("Osaka", None),
    "kyoto": ("Kyoto", None),
    "london": ("London", None),
    "paris": ("Paris", None),
    "seoul": ("Seoul", None),
    "hong kong": ("Hong Kong", None),
    "taipei": ("Taipei", None),
    "singapore": ("Singapore", None),
}


def _parse_direction(question: str) -> WeatherDirection:
    lowered = question.lower()
    if any(token in lowered for token in ("below", "under", "less than")):
        return WeatherDirection.BELOW
    return WeatherDirection.ABOVE


def _parse_metric(question: str) -> WeatherMetric:
    lowered = question.lower()
    if "rainfall" in lowered or "precipitation" in lowered:
        return WeatherMetric.PRECIPITATION
    if (
        "low temperature" in lowered
        or "minimum temperature" in lowered
        or "daily low" in lowered
    ):
        return WeatherMetric.DAILY_LOW
    if (
        "high temperature" in lowered
        or "max temperature" in lowered
        or "maximum temperature" in lowered
        or "daily high" in lowered
        or "high of" in lowered
    ):
        return WeatherMetric.DAILY_HIGH
    return WeatherMetric.UNKNOWN


def _parse_unit(unit_text: str | None) -> WeatherUnit:
    token = (unit_text or "").strip().upper()
    if token in {"C", "°C"}:
        return WeatherUnit.C
    if token in {"F", "°F"}:
        return WeatherUnit.F
    if token == "MM":
        return WeatherUnit.MM
    if token == "IN":
        return WeatherUnit.IN
    return WeatherUnit.UNKNOWN


def _parse_city(question: str) -> tuple[str, str | None] | None:
    lowered = question.lower()
    for alias, value in CITY_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", lowered):
            return value
    for pattern in CITY_PATTERNS:
        match = pattern.search(question)
        if match is not None:
            city = match.group(1).strip()
            return city, CITY_ALIASES.get(city.lower(), (city, None))[1]
    return None


def _parse_target_date(question: str, *, default_year: int = 2026) -> str:
    date_match = DATE_PATTERN.search(question)
    if date_match is not None:
        return date_match.group(1)
    month_day_year_match = MONTH_DAY_YEAR_PATTERN.search(question)
    if month_day_year_match is not None:
        month_name = month_day_year_match.group(1).lower()
        day = int(month_day_year_match.group(2))
        year = int(month_day_year_match.group(3))
        month = MONTHS[month_name]
        return datetime(year, month, day).strftime("%Y-%m-%d")
    month_day_match = MONTH_DAY_PATTERN.search(question)
    if month_day_match is not None:
        month_name = month_day_match.group(1).lower()
        day = int(month_day_match.group(2))
        month = MONTHS[month_name]
        return datetime(default_year, month, day).strftime("%Y-%m-%d")
    raise ValueError(f"unable to parse target date from question: {question}")


def parse_market_question(market: MarketSnapshot, *, default_year: int = 2026) -> WeatherMarketDescriptor:
    question = market.question.strip()
    warnings: list[str] = []

    city = _parse_city(question)
    if city is None:
        raise ValueError(f"unable to parse city from question: {question}")
    city_name, region = city

    target_date = _parse_target_date(question, default_year=default_year)

    threshold_match = THRESHOLD_PATTERN.search(question)
    if threshold_match is None:
        raise ValueError(f"unable to parse threshold from question: {question}")
    threshold = float(threshold_match.group(1))
    metric = _parse_metric(question)
    if metric == WeatherMetric.UNKNOWN:
        warnings.append("metric_unknown")
    unit = _parse_unit(threshold_match.group(2))
    if unit == WeatherUnit.UNKNOWN:
        warnings.append("unit_unknown")
    direction = _parse_direction(question)
    return WeatherMarketDescriptor(
        market_id=market.market_id,
        question=question,
        city=city_name,
        region=region,
        target_date=target_date,
        metric=metric,
        threshold=threshold,
        unit=unit,
        direction=direction,
        confidence=ParseConfidence.MEDIUM if not warnings else ParseConfidence.LOW,
        parse_warnings=warnings,
    )
