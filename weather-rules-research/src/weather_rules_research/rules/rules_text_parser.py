from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class RulesTextParseResult:
    station_name: str | None
    station_id: str | None
    source_name: str | None
    timezone: str | None
    variable_name: str | None
    parse_confidence: float
    needs_review: bool
    extracted_flags: list[str]


class RulesTextParser:
    """
    Lightweight rule text parser for settlement rules.

    It tries to extract:
    - official source wording
    - station references
    - timezone
    - variable semantics
    """

    STATION_PATTERNS = [
        re.compile(r"central park", re.IGNORECASE),
        re.compile(r"changi airport", re.IGNORECASE),
        re.compile(r"hong kong observatory", re.IGNORECASE),
        re.compile(r"shanghai pudong international airport", re.IGNORECASE),
        re.compile(r"pudong airport", re.IGNORECASE),
        re.compile(r"\bshanghai\b", re.IGNORECASE),
    ]

    TIMEZONE_PATTERNS = {
        "America/New_York": re.compile(r"new york time|eastern time|\bedt\b|\best\b", re.IGNORECASE),
        "Asia/Singapore": re.compile(r"singapore time|\bsgt\b", re.IGNORECASE),
        "Asia/Hong_Kong": re.compile(r"hong kong time|\bhkt\b", re.IGNORECASE),
        "Asia/Shanghai": re.compile(r"shanghai time|china standard time|\bcst\b", re.IGNORECASE),
    }

    def parse(self, rules_text: str) -> RulesTextParseResult:
        text = rules_text.strip()
        extracted_flags: list[str] = []

        station_name = None
        station_id = None
        source_name = None
        timezone = None
        variable_name = None
        confidence = 0.2

        if re.search(r"official source|official data|official station", text, re.IGNORECASE):
            source_name = "official_source"
            extracted_flags.append("official_source")
            confidence += 0.15

        if re.search(r"noaa|nws|weather\.gov|observatory|wunderground", text, re.IGNORECASE):
            extracted_flags.append("named_source")
            confidence += 0.15

        lowered = text.lower()
        if "central park" in lowered:
            station_name = "New York City Central Park"
            station_id = "KNYC"
            extracted_flags.append("station_central_park")
            confidence += 0.2
        elif "changi airport" in lowered:
            station_name = "Singapore Changi Airport"
            station_id = "WSSS"
            extracted_flags.append("station_changi")
            confidence += 0.2
        elif "hong kong observatory" in lowered:
            station_name = "Hong Kong Observatory"
            station_id = "HKO"
            extracted_flags.append("station_hko")
            confidence += 0.2
        elif "shanghai pudong international airport" in lowered or "pudong airport" in lowered or re.search(r"\bshanghai\b", lowered):
            station_name = "Shanghai Pudong International Airport"
            station_id = None
            extracted_flags.append("station_shanghai_pudong")
            confidence += 0.2

        for tz_name, pattern in self.TIMEZONE_PATTERNS.items():
            if pattern.search(text):
                timezone = tz_name
                extracted_flags.append(f"timezone_{tz_name}")
                confidence += 0.1
                break

        if re.search(r"highest temperature|max temperature|daily high", text, re.IGNORECASE):
            variable_name = "daily_max_temperature"
            extracted_flags.append("variable_daily_max_temperature")
            confidence += 0.1
        elif re.search(r"lowest temperature|min temperature|daily low", text, re.IGNORECASE):
            variable_name = "daily_min_temperature"
            extracted_flags.append("variable_daily_min_temperature")
            confidence += 0.1
        elif re.search(r"precipitation|rainfall|daily rain|daily precipitation", text, re.IGNORECASE):
            variable_name = "daily_precipitation_sum"
            extracted_flags.append("variable_daily_precipitation_sum")
            confidence += 0.1
        elif re.search(r"snowfall|snow total|daily snow", text, re.IGNORECASE):
            variable_name = "daily_snowfall_sum"
            extracted_flags.append("variable_daily_snowfall_sum")
            confidence += 0.1
        elif re.search(r"wind speed|max wind|maximum wind|wind gust", text, re.IGNORECASE):
            variable_name = "daily_max_wind_speed"
            extracted_flags.append("variable_daily_max_wind_speed")
            confidence += 0.1

        needs_review = confidence < 0.8

        return RulesTextParseResult(
            station_name=station_name,
            station_id=station_id,
            source_name=source_name,
            timezone=timezone,
            variable_name=variable_name,
            parse_confidence=min(confidence, 0.99),
            needs_review=needs_review,
            extracted_flags=extracted_flags,
        )


def parse_rules_text(rules_text: str | None) -> RulesTextParseResult:
    return RulesTextParser().parse(rules_text or "")
