from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


@dataclass(slots=True)
class AlertDeduper:
    cooldown_seconds: dict[str, int] = field(default_factory=lambda: {"info": 600, "watch": 900, "amber": 1200, "red": 1800})
    _seen: dict[str, datetime] = field(default_factory=dict)

    def should_emit(self, *, dedupe_key: str, severity: str, now: datetime | None = None) -> bool:
        timestamp = now or datetime.now(timezone.utc)
        severity_key = str(severity or "watch").lower()
        cooldown = timedelta(seconds=self.cooldown_seconds.get(severity_key, 900))
        last_seen = self._seen.get(dedupe_key)
        if last_seen and timestamp - last_seen < cooldown:
            return False
        self._seen[dedupe_key] = timestamp
        return True
