from datetime import datetime
from datetime import timezone

from backend.models.weather import FreshnessStatus
from backend.models.weather import WeatherSourceRecord


class SourceHealthChecker:
    def __init__(self, stale_after_hours: int = 6):
        self.stale_after_hours = stale_after_hours

    def check(self, record: WeatherSourceRecord) -> WeatherSourceRecord:
        if record.normalized_value is None:
            record.freshness_status = FreshnessStatus.MISSING
            return record
        try:
            fetched = datetime.fromisoformat(record.fetched_at.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            age_hours = (now - fetched).total_seconds() / 3600
        except Exception:
            record.freshness_status = FreshnessStatus.STALE
            return record
        if age_hours > self.stale_after_hours:
            record.freshness_status = FreshnessStatus.STALE
        else:
            record.freshness_status = FreshnessStatus.FRESH
        return record
