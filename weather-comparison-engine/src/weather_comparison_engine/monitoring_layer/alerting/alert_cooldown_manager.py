from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(slots=True)
class AlertCooldownManager:
    cooldown_minutes: dict[str, int]

    def is_cooling_down(self, *, key: str, severity: str, last_emitted_at: datetime | None, now: datetime | None = None) -> bool:
        if last_emitted_at is None:
            return False
        timestamp = now or datetime.now(timezone.utc)
        minutes = self.cooldown_minutes.get(str(severity or "watch").lower(), 15)
        return timestamp - last_emitted_at < timedelta(minutes=minutes)
