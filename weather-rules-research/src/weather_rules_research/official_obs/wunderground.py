from __future__ import annotations

from weather_rules_research.models import Station


class WundergroundHistoryHelper:
    BASE_URL = "https://www.wunderground.com/history/weekly/cn/shanghai"

    @classmethod
    def build_history_weekly_url(cls, station_code: str) -> str:
        code = station_code.strip().upper()
        if not code:
            raise ValueError("station_code is required")
        return f"{cls.BASE_URL}/{code}"

    @classmethod
    def station_code_from_source(cls, source: str | None) -> str | None:
        if not source:
            return None
        prefix = "wunderground:"
        lowered = source.lower()
        if not lowered.startswith(prefix):
            return None
        return source[len(prefix) :].strip().upper() or None

    @classmethod
    def station_code_from_station(cls, station: Station) -> str | None:
        return cls.station_code_from_source(station.source)

    @classmethod
    def build_history_url_for_station(cls, station: Station) -> str | None:
        station_code = cls.station_code_from_station(station)
        if station_code is None:
            return None
        return cls.build_history_weekly_url(station_code)
