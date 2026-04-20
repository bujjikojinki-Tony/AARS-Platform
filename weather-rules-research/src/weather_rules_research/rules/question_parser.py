from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class QuestionParseResult:
    market_type: str | None
    location_name: str | None
    target_date_raw: str | None
    variable_name: str | None
    parse_confidence: float
    needs_review: bool


class QuestionParser:
    """
    MVP parser for market question titles.

    Supported examples:
    - Highest temperature in Central Park on Apr 12?
    - Lowest temperature in Singapore on March 15?
    """

    HIGH_TEMP_PATTERNS = [
        re.compile(
            r"highest temperature in (?P<location>.+?) on (?P<date>.+?)\??$",
            re.IGNORECASE,
        ),
    ]

    LOW_TEMP_PATTERNS = [
        re.compile(
            r"lowest temperature in (?P<location>.+?) on (?P<date>.+?)\??$",
            re.IGNORECASE,
        ),
    ]

    PRECIPITATION_PATTERNS = [
        re.compile(
            r"(?:will\s+)?(?:total\s+)?(?:precipitation|rainfall) in "
            r"(?P<location>.+?) on (?P<date>.+?)(?:\s+be\s+.+?)?\??$",
            re.IGNORECASE,
        ),
        re.compile(
            r"how much (?:rain|precipitation) (?:will fall|is forecast) in "
            r"(?P<location>.+?) on (?P<date>.+?)(?:\s+.+?)?\??$",
            re.IGNORECASE,
        ),
    ]

    SNOWFALL_PATTERNS = [
        re.compile(
            r"(?:will\s+)?(?:total\s+)?snow(?:fall)? in "
            r"(?P<location>.+?) on (?P<date>.+?)(?:\s+be\s+.+?)?\??$",
            re.IGNORECASE,
        ),
    ]

    WIND_PATTERNS = [
        re.compile(
            r"(?:will\s+)?(?:the\s+)?(?:max(?:imum)?\s+)?wind speed in "
            r"(?P<location>.+?) on (?P<date>.+?)(?:\s+be\s+.+?)?\??$",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:will\s+)?wind gusts? in "
            r"(?P<location>.+?) on (?P<date>.+?)(?:\s+be\s+.+?)?\??$",
            re.IGNORECASE,
        ),
    ]

    GLOBAL_TEMP_INDEX_PATTERNS = [
        re.compile(
            r"(?P<ordinal>first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)"
            r"[-\s]*hottest year(?: on record)?\??$",
            re.IGNORECASE,
        ),
        re.compile(
            r"will (?P<year>\d{4}) be the (?P<ordinal>first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)"
            r"[-\s]*hottest year(?: on record)?\??$",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?P<ordinal>first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)"
            r"[-\s]*hottest year on record\??$",
            re.IGNORECASE,
        ),
    ]

    def parse(self, question: str) -> QuestionParseResult:
        question = question.strip()

        for pattern in self.HIGH_TEMP_PATTERNS:
            match = pattern.match(question)
            if match:
                return QuestionParseResult(
                    market_type="daily_high_temperature",
                    location_name=match.group("location").strip(),
                    target_date_raw=match.group("date").strip(),
                    variable_name="daily_max_temperature",
                    parse_confidence=0.92,
                    needs_review=False,
                )

        for pattern in self.LOW_TEMP_PATTERNS:
            match = pattern.match(question)
            if match:
                return QuestionParseResult(
                    market_type="daily_low_temperature",
                    location_name=match.group("location").strip(),
                    target_date_raw=match.group("date").strip(),
                    variable_name="daily_min_temperature",
                    parse_confidence=0.92,
                    needs_review=False,
                )

        for pattern in self.PRECIPITATION_PATTERNS:
            match = pattern.match(question)
            if match:
                return QuestionParseResult(
                    market_type="daily_precipitation",
                    location_name=match.group("location").strip(),
                    target_date_raw=match.group("date").strip(),
                    variable_name="daily_precipitation_sum",
                    parse_confidence=0.88,
                    needs_review=False,
                )

        for pattern in self.SNOWFALL_PATTERNS:
            match = pattern.match(question)
            if match:
                return QuestionParseResult(
                    market_type="daily_snowfall",
                    location_name=match.group("location").strip(),
                    target_date_raw=match.group("date").strip(),
                    variable_name="daily_snowfall_sum",
                    parse_confidence=0.88,
                    needs_review=False,
                )

        for pattern in self.WIND_PATTERNS:
            match = pattern.match(question)
            if match:
                return QuestionParseResult(
                    market_type="daily_max_wind_speed",
                    location_name=match.group("location").strip(),
                    target_date_raw=match.group("date").strip(),
                    variable_name="daily_max_wind_speed",
                    parse_confidence=0.87,
                    needs_review=False,
                )

        for pattern in self.GLOBAL_TEMP_INDEX_PATTERNS:
            match = pattern.match(question)
            if match:
                return QuestionParseResult(
                    market_type="global_temperature_index_ordinal",
                    location_name=None,
                    target_date_raw=match.groupdict().get("year"),
                    variable_name="global_temperature_index",
                    parse_confidence=0.88,
                    needs_review=False,
                )

        return QuestionParseResult(
            market_type=None,
            location_name=None,
            target_date_raw=None,
            variable_name=None,
            parse_confidence=0.0,
            needs_review=True,
        )


def parse_market_question(question: str) -> QuestionParseResult:
    return QuestionParser().parse(question)
