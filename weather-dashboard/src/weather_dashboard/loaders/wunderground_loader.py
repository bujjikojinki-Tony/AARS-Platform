from __future__ import annotations

import json
import os
import re
import ssl
from datetime import datetime, timezone
from urllib.error import URLError
from urllib.request import Request, urlopen


class WundergroundShanghaiLoader:
    HISTORY_URL = "https://www.wunderground.com/history/weekly/cn/shanghai/ZSPD"
    USER_AGENT = "weather-dashboard/1.0"

    @staticmethod
    def _fetch_text(url: str) -> str:
        request = Request(url, headers={"User-Agent": WundergroundShanghaiLoader.USER_AGENT})
        try:
            with urlopen(request, timeout=20) as response:  # nosec: B310
                return response.read().decode("utf-8")
        except URLError as exc:
            if (
                WundergroundShanghaiLoader._is_certificate_error(exc)
                and WundergroundShanghaiLoader._allow_insecure_ssl()
            ):
                context = ssl._create_unverified_context()  # noqa: SLF001, nosec: B323 - opt-in dev fallback only
                with urlopen(request, timeout=20, context=context) as response:  # nosec: B310 - opt-in dev fallback
                    return response.read().decode("utf-8")
            raise

    @staticmethod
    def _allow_insecure_ssl() -> bool:
        return os.getenv("WUNDERGROUND_ALLOW_INSECURE_SSL", "").lower() in {
            "1",
            "true",
            "yes",
        }

    @staticmethod
    def _is_certificate_error(exc: URLError) -> bool:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, ssl.SSLCertVerificationError):
            return True
        return "CERTIFICATE_VERIFY_FAILED" in str(exc)

    @classmethod
    def extract_forecast_url(cls, html: str) -> str | None:
        match = re.search(r'https://api\.weather\.com/v3/wx/forecast/daily/5day[^"]+', html)
        return match.group(0) if match else None

    @classmethod
    def extract_current_url(cls, html: str) -> str | None:
        match = re.search(r'https://api\.weather\.com/v3/wx/observations/current[^"]+(?:icaoCode=ZSPD|geocode=31\.15%2C121\.803)[^"]*', html)
        return match.group(0) if match else None

    @staticmethod
    def _fahrenheit_to_celsius(value: float | int | None) -> float | None:
        if value is None:
            return None
        return round((float(value) - 32.0) * 5.0 / 9.0, 1)

    @staticmethod
    def _normalize_target_date(target_date: str | None, default_year: int | None = None) -> str | None:
        if not target_date:
            return None
        value = target_date.strip()
        if not value:
            return None
        if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
            return value
        year = default_year or datetime.now(timezone.utc).year
        try:
            parsed = datetime.strptime(f"{value} {year}", "%b %d %Y")
            return parsed.replace(year=year).date().isoformat()
        except ValueError:
            return None

    @classmethod
    def _select_forecast_index(cls, forecast_payload: dict, target_date: str | None) -> int | None:
        valid_times = forecast_payload.get("validTimeLocal") or []
        normalized_target = cls._normalize_target_date(target_date)
        if normalized_target:
            for idx, value in enumerate(valid_times):
                if str(value).startswith(normalized_target):
                    return idx
        for idx, value in enumerate(forecast_payload.get("temperatureMax") or []):
            if value is not None:
                return idx
        return None

    @classmethod
    def load_summary(cls, target_date: str | None = None) -> dict:
        html = cls._fetch_text(cls.HISTORY_URL)

        forecast_url = cls.extract_forecast_url(html)
        current_url = cls.extract_current_url(html)

        if not forecast_url:
            raise RuntimeError("Could not find embedded daily forecast URL in Wunderground page")
        if not current_url:
            raise RuntimeError("Could not find embedded current observation URL in Wunderground page")

        forecast_payload = json.loads(cls._fetch_text(forecast_url))
        current_payload = json.loads(cls._fetch_text(current_url))

        forecast_index = cls._select_forecast_index(forecast_payload, target_date)
        if forecast_index is None:
            raise RuntimeError("Could not select a forecast row for the requested target date")

        forecast_temp_max_f = (forecast_payload.get("temperatureMax") or [None])[forecast_index]
        forecast_temp_min_f = (forecast_payload.get("temperatureMin") or [None])[forecast_index]
        narrative = (forecast_payload.get("narrative") or [None])[forecast_index]
        valid_time_local = (forecast_payload.get("validTimeLocal") or [None])[forecast_index]

        return {
            "history_url": cls.HISTORY_URL,
            "forecast_api_url": forecast_url,
            "current_api_url": current_url,
            "target_date": target_date,
            "forecast_target_date": valid_time_local,
            "forecast_temp_max_c": cls._fahrenheit_to_celsius(forecast_temp_max_f),
            "forecast_temp_min_c": cls._fahrenheit_to_celsius(forecast_temp_min_f),
            "forecast_narrative": narrative,
            "observed_temp_c": cls._fahrenheit_to_celsius(current_payload.get("temperature")),
            "observed_temp_max_24h_c": cls._fahrenheit_to_celsius(current_payload.get("temperatureMax24Hour")),
            "observed_temp_min_24h_c": cls._fahrenheit_to_celsius(current_payload.get("temperatureMin24Hour")),
            "observed_valid_time": current_payload.get("validTimeLocal"),
            "station_name": "Shanghai Pudong Intl Airport Station",
            "station_code": "ZSPD",
        }
