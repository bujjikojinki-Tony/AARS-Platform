from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from math import floor
from typing import Sequence

from .models import FundingRate


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class FundingGap:
    start: str
    end: str
    hours: float
    estimated_missing_events: int
    location: str


@dataclass(frozen=True)
class FundingCoverage:
    status: str
    required: bool
    cadence_hours: float
    observed_events: int
    estimated_missing_events: int
    coverage_ratio: float
    largest_gap_hours: float
    gaps: tuple[FundingGap, ...]

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["gaps"] = [asdict(gap) for gap in self.gaps]
        return payload


def analyze_funding_coverage(
    rates: Sequence[FundingRate],
    start: datetime,
    end: datetime,
    *,
    cadence: timedelta = timedelta(hours=8),
    required: bool = True,
    tolerance: float = 1.5,
) -> FundingCoverage:
    start_utc = _utc(start)
    end_utc = _utc(end)
    if end_utc < start_utc:
        raise ValueError("end must be at or after start")
    if cadence <= timedelta(0):
        raise ValueError("cadence must be positive")
    if tolerance < 1:
        raise ValueError("tolerance must be at least 1")

    events = sorted(
        {
            _utc(item.funding_time)
            for item in rates
            if start_utc <= _utc(item.funding_time) <= end_utc
        }
    )
    boundaries = [start_utc, *events, end_utc]
    threshold = cadence * tolerance
    gaps: list[FundingGap] = []
    for index in range(len(boundaries) - 1):
        left = boundaries[index]
        right = boundaries[index + 1]
        duration = right - left
        if duration <= threshold:
            continue
        location = "internal"
        if index == 0:
            location = "leading"
        elif index == len(boundaries) - 2:
            location = "trailing"
        missing = max(1, floor(duration / cadence) - (0 if location != "internal" else 1))
        gaps.append(
            FundingGap(
                start=left.isoformat(),
                end=right.isoformat(),
                hours=duration.total_seconds() / 3600.0,
                estimated_missing_events=missing,
                location=location,
            )
        )

    estimated_missing = sum(gap.estimated_missing_events for gap in gaps)
    denominator = len(events) + estimated_missing
    ratio = 1.0 if not required else len(events) / denominator if denominator else 0.0
    if not required:
        status = "NOT_REQUIRED"
    elif not events:
        status = "MISSING"
    elif gaps:
        status = "GAPPED"
    else:
        status = "COMPLETE"
    return FundingCoverage(
        status=status,
        required=required,
        cadence_hours=cadence.total_seconds() / 3600.0,
        observed_events=len(events),
        estimated_missing_events=estimated_missing,
        coverage_ratio=ratio,
        largest_gap_hours=max((gap.hours for gap in gaps), default=0.0),
        gaps=tuple(gaps),
    )
